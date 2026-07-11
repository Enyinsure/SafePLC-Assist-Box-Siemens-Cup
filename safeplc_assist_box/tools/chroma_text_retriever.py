#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, List, Optional

from ..schemas import AgentEvidence
from .metadata_normalizer import normalize_metadata


class ChromaUnavailable(RuntimeError):
    pass


class ChromaTextRetriever:
    def __init__(self, chroma_dir: str, collection_name: str = "") -> None:
        self.chroma_dir = Path(chroma_dir) if chroma_dir else Path()
        self.collection_name = collection_name
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
            raise ChromaUnavailable(f"Text Chroma query failed: {exc}") from exc

        docs = (raw.get("documents") or [[]])[0]
        metas = (raw.get("metadatas") or [[]])[0]
        distances = (raw.get("distances") or [[]])[0]
        out: List[AgentEvidence] = []
        for idx, doc in enumerate(docs):
            meta = metas[idx] if idx < len(metas) and isinstance(metas[idx], dict) else {}
            distance = distances[idx] if idx < len(distances) else None
            modality = str(meta.get("modality") or meta.get("source_type") or "").lower()
            backend = "chroma_table" if "table" in modality or "table" in self.collection_name.lower() else "chroma_text"
            out.append(
                normalize_metadata(
                    text=str(doc or ""),
                    metadata=meta,
                    backend=backend,
                    query_text=query,
                    collection_name=self.collection_name,
                    source_path=str(self.chroma_dir),
                    raw_distance=distance,
                    modality_hint="table" if backend == "chroma_table" else "text",
                )
            )
        self.last_latency_ms = int((time.perf_counter() - started) * 1000)
        return out

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
        collections = self.discover()
        if not collections:
            raise ChromaUnavailable(f"No Chroma collections found under {self.chroma_dir}")
        if self.collection_name:
            names = {row["name"] for row in collections}
            if self.collection_name not in names:
                raise ChromaUnavailable(
                    f"Configured text collection '{self.collection_name}' not found; available={sorted(names)}"
                )
        else:
            non_empty = [row for row in collections if int(row.get("count", 0) or 0) > 0]
            chosen = non_empty[0] if non_empty else collections[0]
            self.collection_name = str(chosen["name"])
        self.collection = client.get_collection(self.collection_name)
        return self.collection
