#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Dict, List, Optional

from ..schemas import AgentEvidence
from .chroma_collection_selector import (
    CollectionSelectionError,
    discover_collections,
    select_collection,
)
from .embedding_adapter import EmbeddingAdapter, EmbeddingConfigurationError, EmbeddingDimensionMismatch
from .metadata_normalizer import normalize_metadata


class ChromaUnavailable(RuntimeError):
    pass


class ChromaTextRetriever:
    def __init__(
        self,
        chroma_dir: str,
        collection_name: str = "",
        embedding_adapter: Optional[EmbeddingAdapter] = None,
    ) -> None:
        self.chroma_dir = Path(chroma_dir) if chroma_dir else Path()
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.last_latency_ms = 0
        self._collections: Optional[List[Dict[str, object]]] = None
        self.embedding_adapter = embedding_adapter or EmbeddingAdapter.from_env()
        self.backend_audit: Dict[str, object] = {}

    def available(self) -> bool:
        return bool(self.chroma_dir and self.chroma_dir.exists())

    def discover(self) -> List[Dict[str, object]]:
        if self._collections is not None:
            return self._collections
        self._collections = discover_collections(self._client(), str(self.chroma_dir))
        return self._collections

    def search(self, query: str, top_k: int = 20) -> List[AgentEvidence]:
        return self.search_many([query], top_k_per_query=top_k)

    def search_many(
        self,
        queries: List[str],
        top_k_per_query: int = 20,
        expansion_reasons: Optional[List[str]] = None,
    ) -> List[AgentEvidence]:
        started = time.perf_counter()
        collection = self._collection()
        clean_queries = [str(item).strip() for item in queries if str(item).strip()]
        if not clean_queries:
            return []

        # Exact MLFB/order-number lookup is deterministic and should happen
        # before loading the embedding model. This avoids losing an exact PLC
        # identifier in semantic nearest-neighbour retrieval.
        exact_rows = self._lexical_rescue(
            collection,
            clean_queries,
            top_k_per_query=top_k_per_query,
            exact_only=True,
        )
        if exact_rows:
            exact_rows.extend(self._same_page_aggregates(collection, exact_rows))
            rows = self._deduplicate(exact_rows)
            self.backend_audit = {
                "collection_name": self.collection_name,
                "distance_metric": "lexical_exact",
                "query_count": len(clean_queries),
                "lexical_exact_short_circuit": True,
                "lexical_result_count": len(rows),
            }
            self.last_latency_ms = int((time.perf_counter() - started) * 1000)
            return rows

        try:
            query_arguments = self.embedding_adapter.query_arguments_many(collection, clean_queries)
            raw = collection.query(
                **query_arguments,
                n_results=max(1, top_k_per_query),
                include=["documents", "metadatas", "distances"],
            )
            metric = self._distance_metric(collection)
            self.backend_audit = {
                **self.embedding_adapter.last_audit,
                "collection_name": self.collection_name,
                "distance_metric": metric,
                "query_count": len(clean_queries),
                "lexical_exact_short_circuit": False,
            }
        except (EmbeddingConfigurationError, EmbeddingDimensionMismatch):
            raise
        except Exception as exc:
            raise ChromaUnavailable(f"Text Chroma query failed: {exc}") from exc

        out: List[AgentEvidence] = []
        docs_by_query = raw.get("documents") or [[] for _ in clean_queries]
        metas_by_query = raw.get("metadatas") or [[] for _ in clean_queries]
        distances_by_query = raw.get("distances") or [[] for _ in clean_queries]
        reasons = expansion_reasons or []
        for query_index, retrieval_query in enumerate(clean_queries):
            docs = docs_by_query[query_index] if query_index < len(docs_by_query) else []
            metas = metas_by_query[query_index] if query_index < len(metas_by_query) else []
            distances = distances_by_query[query_index] if query_index < len(distances_by_query) else []
            for rank_index, doc in enumerate(docs, start=1):
                idx = rank_index - 1
                meta = metas[idx] if idx < len(metas) and isinstance(metas[idx], dict) else {}
                distance = distances[idx] if idx < len(distances) else None
                modality = str(meta.get("modality") or meta.get("source_type") or "").lower()
                backend = "chroma_table" if "table" in modality or "table" in self.collection_name.lower() else "chroma_text"
                evidence = normalize_metadata(
                    text=str(doc or ""), metadata=meta, backend=backend, query_text=retrieval_query,
                    collection_name=self.collection_name, source_path=str(self.chroma_dir),
                    raw_distance=distance, modality_hint="table" if backend == "chroma_table" else "text",
                    distance_metric=metric,
                )
                evidence.metadata.update(
                    {
                        "retrieval_query": retrieval_query,
                        "retrieval_query_index": query_index,
                        "query_expansion_reason": "original_query" if query_index == 0 else (
                            reasons[query_index - 1] if query_index - 1 < len(reasons) else "controlled_expansion"
                        ),
                        "rank_within_query": rank_index,
                    }
                )
                evidence.retrieval_query = retrieval_query
                evidence.retrieval_query_index = query_index
                evidence.query_expansion_reason = str(evidence.metadata["query_expansion_reason"])
                evidence.rank_within_query = rank_index
                out.append(evidence)

        lexical_rows = self._lexical_rescue(
            collection,
            clean_queries,
            top_k_per_query=min(max(4, top_k_per_query // 2), 12),
            exact_only=False,
        )
        out.extend(lexical_rows)
        out.extend(self._same_page_aggregates(collection, out))
        out = self._deduplicate(out)
        self.backend_audit["lexical_result_count"] = len(lexical_rows)
        self.last_latency_ms = int((time.perf_counter() - started) * 1000)
        return out

    def _lexical_rescue(
        self,
        collection: object,
        queries: List[str],
        *,
        top_k_per_query: int,
        exact_only: bool,
    ) -> List[AgentEvidence]:
        getter = getattr(collection, "get", None)
        if not callable(getter):
            return []

        rows: List[AgentEvidence] = []
        seen_terms = set()
        for query_index, query in enumerate(queries):
            terms = self._lexical_terms(query, exact_only=exact_only)
            for term in terms:
                normalized_term = term.strip()
                key = (query_index, normalized_term.upper())
                if not normalized_term or key in seen_terms:
                    continue
                seen_terms.add(key)
                try:
                    payload = getter(
                        where_document={"$contains": normalized_term},
                        include=["documents", "metadatas"],
                        limit=max(1, top_k_per_query),
                    )
                except Exception:
                    continue
                docs = payload.get("documents") or []
                metas = payload.get("metadatas") or []
                exact_identifier = bool(re.fullmatch(r"6ES7[A-Z0-9\-]{5,}", normalized_term, re.I))
                for rank_index, doc in enumerate(docs, start=1):
                    text = str(doc or "")
                    if normalized_term.lower() not in text.lower() and not self._metadata_contains(
                        metas[rank_index - 1] if rank_index - 1 < len(metas) else {},
                        normalized_term,
                    ):
                        continue
                    meta = metas[rank_index - 1] if rank_index - 1 < len(metas) and isinstance(metas[rank_index - 1], dict) else {}
                    modality = str(meta.get("modality") or meta.get("source_type") or "").lower()
                    backend = "chroma_table" if "table" in modality or "table" in self.collection_name.lower() else "chroma_text"
                    evidence = normalize_metadata(
                        text=text,
                        metadata=meta,
                        backend=backend,
                        query_text=query,
                        collection_name=self.collection_name,
                        source_path=str(self.chroma_dir),
                        fallback_score=0.99 if exact_identifier else 0.82,
                        modality_hint="table" if backend == "chroma_table" else "text",
                        distance_metric="lexical",
                    )
                    evidence.metadata.update(
                        {
                            "retrieval_query": query,
                            "retrieval_query_index": query_index,
                            "query_expansion_reason": "exact_identifier_lookup" if exact_identifier else "lexical_engineering_rescue",
                            "rank_within_query": rank_index,
                            "lexical_rescue": True,
                            "lexical_term": normalized_term,
                            "exact_identifier_match": exact_identifier,
                        }
                    )
                    evidence.retrieval_query = query
                    evidence.retrieval_query_index = query_index
                    evidence.query_expansion_reason = str(evidence.metadata["query_expansion_reason"])
                    evidence.rank_within_query = rank_index
                    rows.append(evidence)
        return self._deduplicate(rows)

    def _lexical_terms(self, query: str, *, exact_only: bool) -> List[str]:
        value = str(query or "")
        exact = list(dict.fromkeys(re.findall(r"\b6ES7[A-Z0-9\-]{5,}\b", value.upper())))
        if exact or exact_only:
            return exact

        low = value.lower()
        groups = []
        if any(token in low for token in ["emc", "电磁兼容", "屏蔽", "接地", "并行敷设", "动力电缆", "干扰"]):
            groups.extend(["电磁兼容", "屏蔽", "接地", "EMC", "动力电缆", "噪声滤波"])
        if any(token in low for token in ["profinet", "hmi", "交换机", "拓扑", "网络连接"]):
            groups.extend(["PROFINET", "HMI", "交换机", "网络拓扑"])
        if any(token in low for token in ["通信中断", "通信不上", "指示灯", "led", "诊断", "报警"]):
            groups.extend(["ERROR LED", "RUN/STOP LED", "诊断缓冲区", "通信中断", "事件跟踪"])
        if any(token in low for token in ["接线", "端子", "线径", "极性", "保护导线", "selv", "pelv"]):
            groups.extend(["接线", "端子", "保护导线", "SELV", "PELV", "极性"])
        return list(dict.fromkeys(groups))[:8]

    def _metadata_contains(self, metadata: object, term: str) -> bool:
        if not isinstance(metadata, dict):
            return False
        needle = term.lower()
        return any(needle in str(value).lower() for value in metadata.values())

    def _deduplicate(self, rows: List[AgentEvidence]) -> List[AgentEvidence]:
        best: Dict[str, AgentEvidence] = {}
        order: List[str] = []
        for row in rows:
            key = row.evidence_id or row.signature()
            if key not in best:
                best[key] = row
                order.append(key)
                continue
            current = best[key]
            if max(row.normalized_score, row.retrieval_score, row.quality_score) > max(
                current.normalized_score,
                current.retrieval_score,
                current.quality_score,
            ):
                best[key] = row
        return [best[key] for key in order]

    def _same_page_aggregates(self, collection: object, seeds: List[AgentEvidence]) -> List[AgentEvidence]:
        aggregates: List[AgentEvidence] = []
        seen = set()
        for seed in seeds:
            key = (seed.source, seed.page, seed.retrieval_query)
            if not seed.source or seed.page is None or key in seen:
                continue
            seen.add(key)
            siblings = self._fetch_page_siblings(collection, seed.source, seed.page)
            if len(siblings) < 2:
                continue
            siblings.sort(key=lambda item: int(item[1].get("chunk_index") or item[1].get("chunk_id") or 0))
            siblings = siblings[:3]
            text = "\n".join(item[0] for item in siblings if item[0])
            metadata = dict(siblings[0][1])
            aggregate = normalize_metadata(
                text=text,
                metadata=metadata,
                backend="chroma_text",
                query_text=seed.retrieval_query or seed.query_text,
                collection_name=self.collection_name,
                source_path=str(self.chroma_dir),
                raw_distance=seed.raw_distance,
                fallback_score=max(seed.normalized_score, seed.retrieval_score),
                modality_hint="text",
                distance_metric=seed.distance_metric,
            )
            chunk_ids = [str(item[1].get("chunk_id") or item[1].get("chunk_index") or index) for index, item in enumerate(siblings)]
            aggregate.metadata.update(
                {
                    "aggregated_chunk_ids": chunk_ids,
                    "aggregated_chunk_count": len(siblings),
                    "page_aggregate": True,
                    "retrieval_query": seed.retrieval_query,
                    "retrieval_query_index": seed.retrieval_query_index,
                    "query_expansion_reason": seed.query_expansion_reason,
                    "rank_within_query": seed.rank_within_query,
                }
            )
            aggregate.retrieval_query = seed.retrieval_query
            aggregate.retrieval_query_index = seed.retrieval_query_index
            aggregate.query_expansion_reason = seed.query_expansion_reason
            aggregate.rank_within_query = seed.rank_within_query
            aggregates.append(aggregate)
        return aggregates

    def _fetch_page_siblings(self, collection: object, source: str, page: int) -> List[tuple[str, Dict[str, object]]]:
        getter = getattr(collection, "get", None)
        if not callable(getter):
            return []
        for page_key in ("page_no", "page_index", "page"):
            for page_value in (page, str(page)):
                try:
                    payload = getter(
                        where={"$and": [{"source": source}, {page_key: page_value}]},
                        include=["documents", "metadatas"],
                        limit=3,
                    )
                    docs = payload.get("documents") or []
                    metas = payload.get("metadatas") or []
                    rows = [
                        (str(doc or ""), dict(metas[index]) if index < len(metas) and isinstance(metas[index], dict) else {})
                        for index, doc in enumerate(docs)
                    ]
                    if rows:
                        return [row for row in rows if str(row[1].get("source") or "") == source and int(row[1].get(page_key) or -1) == page]
                except Exception:
                    continue
        return []

    def _distance_metric(self, collection: object) -> str:
        metadata = getattr(collection, "metadata", None)
        if not isinstance(metadata, dict):
            return "unknown"
        metric = str(metadata.get("hnsw:space") or "unknown").lower()
        return metric if metric in {"cosine", "l2", "ip"} else "unknown"

    def _client(self):
        if self.client is not None:
            return self.client
        if not self.available():
            raise ChromaUnavailable(f"Text Chroma directory does not exist: {self.chroma_dir}")
        try:
            import chromadb  # type: ignore
        except Exception as exc:
            raise ChromaUnavailable("chromadb is not installed in this environment") from exc
        self.client = chromadb.PersistentClient(path=str(self.chroma_dir))
        return self.client

    def _collection(self):
        if self.collection is not None:
            return self.collection
        client = self._client()
        try:
            self.collection_name, self.collection, selected = select_collection(
                client,
                self.discover(),
                explicit_name=self.collection_name,
                kind="text",
            )
            self.backend_audit = {
                **self.embedding_adapter.audit(collection_dimension=selected.get("embedding_dimension")),
                "collection_name": self.collection_name,
                "collection_count": selected.get("count"),
            }
        except CollectionSelectionError as exc:
            raise ChromaUnavailable(str(exc)) from exc
        return self.collection
