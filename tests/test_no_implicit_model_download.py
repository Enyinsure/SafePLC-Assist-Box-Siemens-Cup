import pytest

from safeplc_assist_box.tools.embedding_adapter import EmbeddingAdapter, EmbeddingConfigurationError


class FakeCollection:
    def peek(self, limit):
        return {"embeddings": [[0.0, 0.0]]}


def test_auto_backend_does_not_download_or_use_chroma_default():
    adapter = EmbeddingAdapter(backend="auto", allow_chroma_default=False, allow_remote_download=False)
    with pytest.raises(EmbeddingConfigurationError, match="No query embedding is configured"):
        adapter.query_arguments(FakeCollection(), "query")


def test_chroma_default_requires_explicit_permission():
    adapter = EmbeddingAdapter(backend="chroma_default", allow_chroma_default=False)
    with pytest.raises(EmbeddingConfigurationError, match="disabled"):
        adapter.query_arguments(FakeCollection(), "query")
