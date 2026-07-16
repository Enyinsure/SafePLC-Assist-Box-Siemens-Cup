#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Dict, List, Optional

from ..schemas import AgentEvidence
from .chroma_collection_selector import CollectionSelectionError, discover_collections, select_collection
from .chroma_text_retriever import ChromaUnavailable
from .embedding_adapter import EmbeddingAdapter, EmbeddingConfigurationError, EmbeddingDimensionMismatch
from .metadata_normalizer import extract_location_marker, extract_manual_figure, first_value, load_jsonl_records, normalize_metadata
from .verified_figure_catalog import enrich_verified_figure_evidence


class FigureMetadataMapper:
    def __init__(self, cards_jsonl: str = "", visual_dir: str = "") -> None:
        self.cards_jsonl = Path(cards_jsonl) if cards_jsonl else Path()
        self.visual_dir = Path(visual_dir) if visual_dir else Path()
        self._by_key: Optional[Dict[str, Dict[str, object]]] = None
        self._card_count = 0

    def available(self) -> bool:
        return bool(self.cards_jsonl and self.cards_jsonl.exists() and self.cards_jsonl.is_file())

    def card_count(self) -> int:
        self._load()
        return self._card_count

    def image_resolvable_count(self) -> int:
        count = 0
        seen = set()
        for card in self._load().values():
            marker = id(card)
            if marker in seen:
                continue
            seen.add(marker)
            image = str(card.get("image_path") or card.get("image") or "")
            _, resolved, exists = self._resolve_image(image)
            if exists and resolved:
                count += 1
        return count

    def find_by_page(self, page: int) -> List[Dict[str, object]]:
        """Return figure cards whose page matches exactly."""
        if not self.available():
            return []

        target_page = int(page)
        matches: List[Dict[str, object]] = []

        for record in load_jsonl_records(self.cards_jsonl):
            record_page = _parse_page(
                first_value(
                    record,
                    ("page", "page_no", "page_number", "page_index"),
                )
            )
            if record_page == target_page:
                matches.append(record)

        return matches

    def enrich(self, ev: AgentEvidence) -> AgentEvidence:
        cards = self._load()
        keys = self._keys(
            ev.figure_id,
            ev.figure_number,
            str(ev.page or ""),
            ev.document_id,
            ev.manual_title,
        )
        card = next((cards[k] for k in keys if k and k in cards), None)
        if card:
            ev.figure_id = ev.figure_id or first_value(card, ("figure_id", "fig_id", "id"))
            ev.figure_number = ev.figure_number or first_value(card, ("figure_number", "fig_no", "figure"))
            ev.page = ev.page or _parse_page(first_value(card, ("page", "page_no", "page_number")))
            raw = ev.raw_image_path or str(card.get("image_path") or card.get("image") or "")
            raw, resolved, exists = self._resolve_image(raw)
            ev.raw_image_path = raw
            ev.resolved_image_path = resolved
            ev.image_exists = exists
            ev.image_path = resolved if exists else ""
            ev.metadata.update({"figure_card_matched": True})
        if not ev.figure_number:
            ev.figure_number, ev.manual_figure_caption = extract_manual_figure(ev.text)
        ev.manual_figure_number = ev.manual_figure_number or ev.figure_number
        ev.manual_figure_caption = ev.manual_figure_caption or str((card or {}).get("manual_figure_caption") or "")
        figure_id_type = str(ev.metadata.get("figure_id_type") or "unknown")
        ev.visual_record_id = ev.visual_record_id or (ev.figure_id if figure_id_type == "synthetic_visual_id" else "")
        if ev.raw_image_path and not ev.resolved_image_path:
            raw, resolved, exists = self._resolve_image(ev.raw_image_path)
            ev.raw_image_path, ev.resolved_image_path, ev.image_exists = raw, resolved, exists
            ev.image_path = resolved if exists else ""
        has_page_text = bool(
            ev.page
            or ev.figure_id
            or ev.figure_number
            or re.search(r"(?:Figure|Fig\.|图)\s*[\d\-.]+|front\s+view|前视图", ev.text or "", re.I)
        )
        ev.visual_evidence_status = (
            "image_available" if ev.image_exists else "page_text_only" if has_page_text else "missing"
        )
        ev.metadata.update(
            {
                "has_visual_evidence": ev.image_exists,
                "raw_image_path": ev.raw_image_path,
                "resolved_image_path": ev.resolved_image_path,
                "image_exists": ev.image_exists,
                "visual_evidence_status": ev.visual_evidence_status,
                "manual_figure_number": ev.manual_figure_number,
                "manual_figure_caption": ev.manual_figure_caption,
                "visual_record_id": ev.visual_record_id,
                "location_marker": ev.metadata.get("location_marker") or extract_location_marker(ev.text, ev.query_text),
            }
        )
        return enrich_verified_figure_evidence(ev)

    def _resolve_image(self, image: str):
        if not image:
            return "", "", False
        path = Path(image)
        if path.is_absolute() and path.is_file():
            return image, str(path), True
        if str(self.visual_dir) not in {"", "."}:
            candidate = self.visual_dir / image
            if candidate.is_file():
                return image, str(candidate), True
        if self.cards_jsonl.is_file():
            candidate = self.cards_jsonl.parent / image
            if candidate.is_file():
                return image, str(candidate), True
        return image, "", False

    def _load(self) -> Dict[str, Dict[str, object]]:
        if self._by_key is not None:
            return self._by_key
        by_key: Dict[str, Dict[str, object]] = {}
        if self.cards_jsonl.exists() and self.cards_jsonl.is_file():
            for record in load_jsonl_records(self.cards_jsonl):
                self._card_count += 1
                figure_id = first_value(record, ("figure_id", "fig_id", "id"))
                figure_number = first_value(record, ("figure_number", "fig_no", "figure"))
                page = first_value(record, ("page", "page_no", "page_number"))
                document_id = first_value(record, ("document_id", "doc_id", "manual_id"))
                manual_title = first_value(record, ("manual_title", "title", "doc_title"))
                for key in self._keys(figure_id, figure_number, page, document_id, manual_title):
                    if key:
                        by_key[key] = record
        self._by_key = by_key
        return by_key

    def _keys(self, figure_id: str, figure_number: str, page: str, document_id: str, manual_title: str) -> List[str]:
        return [
            figure_id,
            figure_number,
            f"{page}:{figure_id}" if page and figure_id else "",
            f"{page}:{figure_number}" if page and figure_number else "",
            f"{document_id}:{figure_id}" if document_id and figure_id else "",
            f"{manual_title}:{page}:{figure_number}" if manual_title and page and figure_number else "",
        ]


class ChromaFigureRetriever:
    def __init__(
        self,
        chroma_dir: str,
        collection_name: str = "",
        cards_jsonl: str = "",
        visual_dir: str = "",
        embedding_adapter: Optional[EmbeddingAdapter] = None,
    ) -> None:
        self.chroma_dir = Path(chroma_dir) if chroma_dir else Path()
        self.collection_name = collection_name
        self.cards = FigureMetadataMapper(cards_jsonl, visual_dir)
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
        started = time.perf_counter()
        query_text = str(query or "")

        # 中文：资料页 8078、页码：8078、页8078
        page_match = re.search(
            r"(?:资料)?页(?:码)?\s*[:：]?\s*0*(\d+)",
            query_text,
            re.I,
        )

        # 英文：page 8078、page: 8078
        if page_match is None:
            page_match = re.search(
                r"\bpage\s*[:：]?\s*0*(\d+)\b",
                query_text,
                re.I,
            )

        if page_match:
            page = int(page_match.group(1))
            direct = self._search_exact_page(query_text, page)

            if direct:
                self.last_latency_ms = int(
                    (time.perf_counter() - started) * 1000
                )
                self.backend_audit = {
                    "collection_name": self.collection_name,
                    "exact_page_lookup": True,
                    "exact_page": page,
                    "result_count": len(direct),
                }
                return direct[: max(1, top_k)]

        # 没有精确页码命中时，才进入向量检索
        collection = self._collection()

        try:
            query_arguments = self.embedding_adapter.query_arguments(
                collection,
                query_text,
            )
            raw = collection.query(
                **query_arguments,
                n_results=max(1, top_k),
                include=["documents", "metadatas", "distances"],
            )
            self.backend_audit = {
                **self.embedding_adapter.last_audit,
                "collection_name": self.collection_name,
                "distance_metric": self._distance_metric(collection),
                "exact_page_lookup": False,
            }
        except (EmbeddingConfigurationError, EmbeddingDimensionMismatch):
            raise
        except Exception as exc:
            raise ChromaUnavailable(
                f"Figure Chroma query failed: {exc}"
            ) from exc

        docs = (raw.get("documents") or [[]])[0]
        metas = (raw.get("metadatas") or [[]])[0]
        distances = (raw.get("distances") or [[]])[0]

        out: List[AgentEvidence] = []

        for idx, doc in enumerate(docs):
            meta = (
                metas[idx]
                if idx < len(metas) and isinstance(metas[idx], dict)
                else {}
            )
            distance = distances[idx] if idx < len(distances) else None

            ev = normalize_metadata(
                text=str(doc or ""),
                metadata=meta,
                backend="chroma_figure",
                query_text=query_text,
                collection_name=self.collection_name,
                source_path=str(self.chroma_dir),
                raw_distance=distance,
                modality_hint="figure",
                distance_metric=self._distance_metric(collection),
            )
            out.append(self.cards.enrich(ev))

        self.last_latency_ms = int(
            (time.perf_counter() - started) * 1000
        )
        return out

    def _search_exact_page(
        self,
        query: str,
        page: int,
    ) -> List[AgentEvidence]:
        """Resolve an explicitly requested page directly from figure cards."""
        results: List[AgentEvidence] = []

        for card in self.cards.find_by_page(page):
            caption = first_value(
                card,
                (
                    "manual_figure_caption",
                    "caption",
                    "text",
                    "content",
                    "description",
                ),
            ).strip()

            if not caption:
                caption = f"page {page:05d}"

            ev = normalize_metadata(
                text=caption,
                metadata=card,
                backend="chroma_figure",
                query_text=query,
                collection_name=self.collection_name,
                source_path=str(self.chroma_dir),
                fallback_score=1.0,
                modality_hint="figure",
                distance_metric="exact",
            )

            raw_image = (
                ev.raw_image_path
                or str(card.get("image_path") or card.get("image") or "")
            )

            raw_image, resolved_image, image_exists = (
                self.cards._resolve_image(raw_image)
            )

            ev.page = page
            ev.raw_image_path = raw_image
            ev.resolved_image_path = resolved_image
            ev.image_exists = image_exists
            ev.image_path = resolved_image if image_exists else ""
            ev.visual_evidence_status = (
                "image_available" if image_exists else "page_text_only"
            )
            ev.retrieval_score = 1.0
            ev.normalized_score = 1.0
            ev.vector_similarity = 1.0
            ev.manual_figure_caption = (
                ev.manual_figure_caption or caption
            )

            ev.metadata.update(
                {
                    "exact_page_match": True,
                    "requested_page": page,
                    "raw_image_path": raw_image,
                    "resolved_image_path": resolved_image,
                    "image_exists": image_exists,
                    "visual_evidence_status": ev.visual_evidence_status,
                }
            )

            results.append(ev)

        results.sort(
            key=lambda item: (
                not item.image_exists,
                item.figure_number or "",
                item.figure_id or "",
            )
        )
        return results

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
            raise ChromaUnavailable(f"Figure Chroma directory does not exist: {self.chroma_dir}")
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
                kind="figure",
            )
            self.backend_audit = {
                **self.embedding_adapter.audit(collection_dimension=selected.get("embedding_dimension")),
                "collection_name": self.collection_name,
                "collection_count": selected.get("count"),
            }
        except CollectionSelectionError as exc:
            raise ChromaUnavailable(str(exc)) from exc
        return self.collection


def _parse_page(value: str) -> Optional[int]:
    match = re.search(r"\d+", str(value or ""))
    return int(match.group(0)) if match else None
