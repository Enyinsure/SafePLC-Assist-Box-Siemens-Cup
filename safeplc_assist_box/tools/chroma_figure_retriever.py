#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Dict, List, Optional

from ..schemas import AgentEvidence
from .chroma_text_retriever import ChromaUnavailable
from .metadata_normalizer import first_value, load_jsonl_records, normalize_metadata


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
            image = str(card.get("image_path") or "")
            if image and Path(image).exists():
                count += 1
        return count

    def enrich(self, ev: AgentEvidence) -> AgentEvidence:
        cards = self._load()
        keys = [ev.figure_id, ev.figure_number, f"{ev.page}:{ev.figure_number}", f"{ev.page}:{ev.figure_id}"]
        card = next((cards[k] for k in keys if k and k in cards), None)
        if card:
            ev.figure_id = ev.figure_id or first_value(card, ("figure_id", "fig_id", "id"))
            ev.figure_number = ev.figure_number or first_value(card, ("figure_number", "fig_no", "figure"))
            ev.page = ev.page or _parse_page(first_value(card, ("page", "page_no", "page_number")))
            ev.image_path = ev.image_path or self._resolve_image(str(card.get("image_path") or card.get("image") or ""))
            ev.metadata.update({"figure_card_matched": True})
        if not ev.figure_number:
            m = re.search(r"(?:Figure|Fig\.|图)\s*[\d\-\.]+", ev.text, flags=re.IGNORECASE)
            if m:
                ev.figure_number = m.group(0)
        ev.metadata["has_visual_evidence"] = bool(ev.image_path and Path(ev.image_path).exists())
        ev.metadata["visual_evidence_status"] = (
            "image_available" if ev.metadata["has_visual_evidence"] else "page_text_only"
        )
        return ev

    def _resolve_image(self, image: str) -> str:
        if not image:
            return ""
        path = Path(image)
        if path.exists():
            return str(path)
        if self.visual_dir:
            candidate = self.visual_dir / image
            if candidate.exists():
                return str(candidate)
        return image

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
                for key in [figure_id, figure_number, f"{page}:{figure_number}", f"{page}:{figure_id}"]:
                    if key:
                        by_key[key] = record
        self._by_key = by_key
        return by_key


class ChromaFigureRetriever:
    def __init__(
        self,
        chroma_dir: str,
        collection_name: str = "",
        cards_jsonl: str = "",
        visual_dir: str = "",
    ) -> None:
        self.chroma_dir = Path(chroma_dir) if chroma_dir else Path()
        self.collection_name = collection_name
        self.cards = FigureMetadataMapper(cards_jsonl, visual_dir)
        self.client = None
        self.collection = None
        self.last_latency_ms = 0
        self._collections: Optional[List[Dict[str, object]]] = None

    def available(self) -> bool:
        return bool(self.chroma_dir and self.chroma_dir.exists())

    def discover(self) -> List[Dict[str, object]]:
        if self._collections is not None:
            return self._collections
        client = self._client()
        rows: List[Dict[str, object]] = []
        for collection in client.list_collections():
            name = getattr(collection, "name", str(collection))
            count = 0
            metadata_fields: List[str] = []
            try:
                count = int(collection.count())
                peek = collection.peek(5)
                for meta in peek.get("metadatas", []) or []:
                    if isinstance(meta, dict):
                        metadata_fields.extend(str(k) for k in meta.keys())
            except Exception:
                pass
            rows.append(
                {
                    "name": name,
                    "count": count,
                    "metadata_fields": sorted(set(metadata_fields)),
                    "path": str(self.chroma_dir),
                }
            )
        self._collections = rows
        return rows

    def search(self, query: str, top_k: int = 20) -> List[AgentEvidence]:
        started = time.perf_counter()
        collection = self._collection()
        try:
            raw = collection.query(
                query_texts=[query],
                n_results=max(1, top_k),
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            raise ChromaUnavailable(f"Figure Chroma query failed: {exc}") from exc
        docs = (raw.get("documents") or [[]])[0]
        metas = (raw.get("metadatas") or [[]])[0]
        distances = (raw.get("distances") or [[]])[0]
        out: List[AgentEvidence] = []
        for idx, doc in enumerate(docs):
            meta = metas[idx] if idx < len(metas) and isinstance(metas[idx], dict) else {}
            distance = distances[idx] if idx < len(distances) else None
            ev = normalize_metadata(
                text=str(doc or ""),
                metadata=meta,
                backend="chroma_figure",
                query_text=query,
                collection_name=self.collection_name,
                source_path=str(self.chroma_dir),
                raw_distance=distance,
                modality_hint="figure",
            )
            out.append(self.cards.enrich(ev))
        self.last_latency_ms = int((time.perf_counter() - started) * 1000)
        return out

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
        collections = self.discover()
        if not collections:
            raise ChromaUnavailable(f"No figure Chroma collections found under {self.chroma_dir}")
        if self.collection_name:
            names = {row["name"] for row in collections}
            if self.collection_name not in names:
                raise ChromaUnavailable(
                    f"Configured figure collection '{self.collection_name}' not found; available={sorted(names)}"
                )
        else:
            non_empty = [row for row in collections if int(row.get("count", 0) or 0) > 0]
            chosen = non_empty[0] if non_empty else collections[0]
            self.collection_name = str(chosen["name"])
        self.collection = client.get_collection(self.collection_name)
        return self.collection


def _parse_page(value: str) -> Optional[int]:
    match = re.search(r"\d+", str(value or ""))
    return int(match.group(0)) if match else None
