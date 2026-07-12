#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

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
        self.last_latency_ms = int((time.perf_counter() - started) * 1000)
        return out

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
