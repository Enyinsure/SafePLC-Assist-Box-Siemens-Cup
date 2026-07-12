from pathlib import Path
from types import SimpleNamespace

import scripts.run_full_core_30 as runner


def config(tmp_path: Path, **updates):
    text_dir = tmp_path / "text"
    figure_dir = tmp_path / "figure"
    model_dir = tmp_path / "model"
    for path in (text_dir, figure_dir, model_dir):
        path.mkdir(exist_ok=True)
    values = {
        "mode": "FULL",
        "allow_jsonl_fallback": False,
        "enable_jsonl_hybrid": False,
        "chroma_dir": str(text_dir),
        "figure_chroma_dir": str(figure_dir),
        "enable_query_expansion": True,
        "max_expanded_queries": 2,
        "embedding_backend": "auto",
        "embedding_model_path": str(model_dir),
        "allow_remote_model_download": False,
        "allow_chroma_default_embedding": False,
    }
    values.update(updates)
    return SimpleNamespace(**values)


def test_full_environment_requires_both_chroma_expansion_and_embedding(tmp_path):
    assert runner.validate_full_environment(config(tmp_path)) == []
    invalid = config(
        tmp_path,
        figure_chroma_dir=str(tmp_path / "missing-figure"),
        enable_query_expansion=False,
        max_expanded_queries=1,
        embedding_model_path="",
    )
    errors = runner.validate_full_environment(invalid)
    assert "real_figure_Chroma_directory_is_required" in errors
    assert "query_expansion_must_be_enabled" in errors
    assert "max_expanded_queries_must_be_at_least_2" in errors
    assert "embedding_model_path_or_backend_is_not_available" in errors


def test_chroma_default_embedding_must_be_explicitly_available(tmp_path):
    enabled = config(
        tmp_path,
        embedding_backend="chroma_default",
        embedding_model_path="",
        allow_chroma_default_embedding=True,
    )
    assert runner.validate_full_environment(enabled) == []
    enabled.allow_chroma_default_embedding = False
    assert "embedding_model_path_or_backend_is_not_available" in runner.validate_full_environment(enabled)


def test_selected_collection_names_are_resolved_from_chroma(monkeypatch, tmp_path):
    class Adapter:
        def __init__(self):
            self.last_audit = {}

        def query_arguments(self, collection, query):
            self.last_audit = {"resolved": True, "query": query}
            return {"query_embeddings": [[0.1, 0.2]]}

    class Retriever:
        def __init__(self, path, collection_name, *args, **kwargs):
            self.collection_name = collection_name or ("figure_actual" if "figure" in path else "text_actual")

        def _collection(self):
            return object()

    monkeypatch.setattr(runner, "ChromaTextRetriever", Retriever)
    monkeypatch.setattr(runner, "ChromaFigureRetriever", Retriever)
    monkeypatch.setattr(runner.EmbeddingAdapter, "from_config", lambda value: Adapter())
    value = config(tmp_path)
    value.text_collection = ""
    value.figure_collection = ""
    value.figure_cards_jsonl = ""
    value.visual_dir = ""
    selected = runner.resolve_selected_collections(value)
    assert selected["selected_text_collection"] == "text_actual"
    assert selected["selected_figure_collection"] == "figure_actual"
    assert selected["text_embedding_audit"]["resolved"] is True
    assert selected["figure_embedding_audit"]["resolved"] is True
