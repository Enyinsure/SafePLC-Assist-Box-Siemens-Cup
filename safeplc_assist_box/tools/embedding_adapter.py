#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Dict, List, Optional


class EmbeddingConfigurationError(RuntimeError):
    pass


class EmbeddingDimensionMismatch(RuntimeError):
    pass


_ENCODER_CACHE: Dict[tuple, Any] = {}
_ENCODER_CACHE_LOCK = Lock()


class EmbeddingAdapter:
    """Lazy, explicit query embedding adapter for persistent Chroma collections."""

    VALID_BACKENDS = {"auto", "sentence_transformers", "chroma_default"}

    def __init__(
        self,
        backend: str = "auto",
        model_path: str = "",
        device: str = "cpu",
        normalize: bool = True,
        query_prefix: str = "",
        allow_chroma_default: bool = False,
        allow_remote_download: bool = False,
        encoder_factory: Optional[Callable[..., Any]] = None,
    ) -> None:
        backend = (backend or "auto").strip().lower()
        if backend not in self.VALID_BACKENDS:
            raise EmbeddingConfigurationError(
                f"Unsupported SAFEPLC_EMBEDDING_BACKEND={backend!r}; expected one of {sorted(self.VALID_BACKENDS)}"
            )
        self.backend = backend
        self.model_path = str(model_path or "")
        self.device = str(device or "cpu")
        self.normalize = bool(normalize)
        self.query_prefix = str(query_prefix or "")
        self.allow_chroma_default = bool(allow_chroma_default)
        self.allow_remote_download = bool(allow_remote_download)
        self.encoder_factory = encoder_factory
        self._encoder = None
        self.last_audit: Dict[str, Any] = self.audit()

    @classmethod
    def from_env(cls) -> "EmbeddingAdapter":
        return cls(
            backend=os.environ.get("SAFEPLC_EMBEDDING_BACKEND", "auto"),
            model_path=os.environ.get("SAFEPLC_EMBEDDING_MODEL_PATH", ""),
            device=os.environ.get("SAFEPLC_EMBEDDING_DEVICE", "cpu"),
            normalize=_bool_value(os.environ.get("SAFEPLC_EMBEDDING_NORMALIZE"), True),
            query_prefix=os.environ.get("SAFEPLC_EMBEDDING_QUERY_PREFIX", ""),
            allow_chroma_default=_bool_value(os.environ.get("SAFEPLC_ALLOW_CHROMA_DEFAULT_EMBEDDING"), False),
            allow_remote_download=_bool_value(os.environ.get("SAFEPLC_ALLOW_REMOTE_MODEL_DOWNLOAD"), False),
        )

    @classmethod
    def from_config(cls, config: Any) -> "EmbeddingAdapter":
        return cls(
            backend=config.embedding_backend,
            model_path=config.embedding_model_path,
            device=config.embedding_device,
            normalize=config.embedding_normalize,
            query_prefix=config.embedding_query_prefix,
            allow_chroma_default=config.allow_chroma_default_embedding,
            allow_remote_download=config.allow_remote_model_download,
        )

    def query_arguments(self, collection: Any, query: str) -> Dict[str, Any]:
        collection_dimension = collection_embedding_dimension(collection)
        use_local_encoder = bool(self.model_path) or self.backend == "sentence_transformers"
        if use_local_encoder:
            encoder = self._load_encoder()
            query_text = f"{self.query_prefix}{query}"
            encoded = encoder.encode(
                [query_text],
                normalize_embeddings=self.normalize,
                convert_to_numpy=True,
            )
            vector = _first_vector(encoded)
            embedding_dimension = len(vector)
            if collection_dimension is not None and embedding_dimension != collection_dimension:
                raise EmbeddingDimensionMismatch(
                    "Query embedding dimension "
                    f"{embedding_dimension} does not match collection dimension {collection_dimension}. "
                    "Set SAFEPLC_EMBEDDING_MODEL_PATH to the model used to build this collection."
                )
            self.last_audit = self.audit(
                embedding_dimension=embedding_dimension,
                collection_dimension=collection_dimension,
                resolved_backend="sentence_transformers",
            )
            return {"query_embeddings": [vector]}

        if self.backend == "chroma_default" or (self.backend == "auto" and self.allow_chroma_default):
            if not self.allow_chroma_default:
                raise EmbeddingConfigurationError(
                    "Chroma default embedding is disabled. Set SAFEPLC_ALLOW_CHROMA_DEFAULT_EMBEDDING=1 explicitly."
                )
            self.last_audit = self.audit(
                collection_dimension=collection_dimension,
                resolved_backend="chroma_default",
            )
            return {"query_texts": [query]}

        raise EmbeddingConfigurationError(
            "No query embedding is configured. Set SAFEPLC_EMBEDDING_MODEL_PATH to the local model used by the "
            "collection, or explicitly set SAFEPLC_ALLOW_CHROMA_DEFAULT_EMBEDDING=1. Remote model download is disabled."
        )

    def audit(
        self,
        embedding_dimension: Optional[int] = None,
        collection_dimension: Optional[int] = None,
        resolved_backend: str = "",
    ) -> Dict[str, Any]:
        return {
            "embedding_backend": resolved_backend or self.backend,
            "embedding_model_path": self.model_path,
            "embedding_device": self.device,
            "embedding_dimension": embedding_dimension,
            "collection_embedding_dimension": collection_dimension,
            "embedding_normalized": self.normalize,
            "query_prefix_used": self.query_prefix,
            "remote_download_allowed": self.allow_remote_download,
            "chroma_default_allowed": self.allow_chroma_default,
        }

    def _load_encoder(self) -> Any:
        if self._encoder is not None:
            return self._encoder
        if not self.model_path:
            raise EmbeddingConfigurationError(
                "SAFEPLC_EMBEDDING_BACKEND=sentence_transformers requires SAFEPLC_EMBEDDING_MODEL_PATH."
            )
        model_path = Path(self.model_path)
        if not model_path.exists() and not self.allow_remote_download:
            raise EmbeddingConfigurationError(
                f"Local embedding model does not exist: {model_path}. Remote download is disabled."
            )
        cache_key = (str(model_path), self.device, self.allow_remote_download)
        with _ENCODER_CACHE_LOCK:
            encoder = _ENCODER_CACHE.get(cache_key)
            if encoder is None:
                factory = self.encoder_factory or _sentence_transformer_factory
                encoder = factory(
                    str(model_path),
                    device=self.device,
                    local_files_only=not self.allow_remote_download,
                )
                _ENCODER_CACHE[cache_key] = encoder
        self._encoder = encoder
        return encoder


def collection_embedding_dimension(collection: Any) -> Optional[int]:
    payload = None
    errors: List[str] = []
    for method_name in ("peek", "get"):
        method = getattr(collection, method_name, None)
        if not callable(method):
            continue
        try:
            if method_name == "peek":
                payload = method(1)
            else:
                payload = method(limit=1, include=["embeddings"])
            dimension = _dimension_from_payload(payload)
            if dimension is not None:
                return dimension
        except Exception as exc:
            errors.append(f"{method_name}: {exc}")
    if errors:
        raise EmbeddingConfigurationError(
            "Unable to inspect collection embedding dimension without querying: " + "; ".join(errors)
        )
    return None


def _dimension_from_payload(payload: Any) -> Optional[int]:
    if not isinstance(payload, dict):
        return None
    embeddings = payload.get("embeddings")
    if embeddings is None:
        return None
    try:
        first = embeddings[0]
    except (IndexError, KeyError, TypeError):
        return None
    if first is None:
        return None
    try:
        return len(first)
    except TypeError:
        return None


def _first_vector(encoded: Any) -> List[float]:
    if hasattr(encoded, "tolist"):
        encoded = encoded.tolist()
    if not encoded:
        raise EmbeddingConfigurationError("The configured embedding model returned no query vector.")
    vector = encoded[0]
    if hasattr(vector, "tolist"):
        vector = vector.tolist()
    return [float(value) for value in vector]


def _sentence_transformer_factory(model_path: str, **kwargs: Any) -> Any:
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
    except Exception as exc:
        raise EmbeddingConfigurationError(
            "sentence-transformers is not installed; install requirements-full.txt in the FULL environment."
        ) from exc
    return SentenceTransformer(model_path, **kwargs)


def _bool_value(value: Optional[str], default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}
