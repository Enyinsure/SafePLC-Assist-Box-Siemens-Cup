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
        started = time.perf_counter()
        collection = self._collection()
        try:
            query_arguments = self.embedding_adapter.query_arguments(collection, query)
            raw = collection.query(
                **query_arguments,
                n_results=max(1, top_k),
                include=["documents", "metadatas", "distances"],
            )
            self.backend_audit = {
                **self.embedding_adapter.last_audit,
                "collection_name": self.collection_name,
            }
        except (EmbeddingConfigurationError, EmbeddingDimensionMismatch):
            raise
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
