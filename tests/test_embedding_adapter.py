from safeplc_assist_box.tools.embedding_adapter import EmbeddingAdapter


class FakeEncoder:
    def __init__(self):
        self.calls = []

    def encode(self, texts, **kwargs):
        self.calls.append((texts, kwargs))
        return [[0.1, 0.2, 0.3]]


class FakeCollection:
    def peek(self, limit):
        return {"embeddings": [[0.0, 0.0, 0.0]]}


def test_local_embedding_uses_query_embeddings_and_prefix(tmp_path):
    encoder = FakeEncoder()
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    adapter = EmbeddingAdapter(
        model_path=str(model_dir),
        query_prefix="query: ",
        normalize=True,
        encoder_factory=lambda *args, **kwargs: encoder,
    )
    arguments = adapter.query_arguments(FakeCollection(), "X1 location")
    assert arguments == {"query_embeddings": [[0.1, 0.2, 0.3]]}
    assert encoder.calls[0][0] == ["query: X1 location"]
    assert encoder.calls[0][1]["normalize_embeddings"] is True
    assert adapter.last_audit["embedding_dimension"] == 3
    assert adapter.last_audit["collection_embedding_dimension"] == 3
