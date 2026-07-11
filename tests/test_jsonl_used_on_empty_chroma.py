from fallback_test_support import evidence, registry


def test_jsonl_used_on_empty_chroma(monkeypatch):
    tools = registry(monkeypatch, [], [evidence("jsonl_chunks", 0.7)])
    results = tools.search_text("CPU 1517-3 PN X1")
    assert results[0].retrieval_backend == "jsonl_chunks"
    assert tools._jsonl_chunks.calls == 1
    assert "chroma_returned_zero" in tools.backend_audit["jsonl_fallback_reason"]
