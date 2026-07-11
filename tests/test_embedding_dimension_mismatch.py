import pytest

from safeplc_assist_box.tools.embedding_adapter import EmbeddingAdapter, EmbeddingDimensionMismatch


class FakeCollection:
    def peek(self, limit):
        return {"embeddings": [[0.0, 0.0]]}


class FakeEncoder:
    def encode(self, texts, **kwargs):
        return [[0.1, 0.2, 0.3]]


def test_embedding_dimension_mismatch_is_explicit(tmp_path):
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    adapter = EmbeddingAdapter(
        model_path=str(model_dir),
        encoder_factory=lambda *args, **kwargs: FakeEncoder(),
    )
    with pytest.raises(EmbeddingDimensionMismatch, match="does not match"):
        adapter.query_arguments(FakeCollection(), "query")
