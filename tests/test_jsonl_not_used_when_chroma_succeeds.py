from fallback_test_support import evidence, registry


def test_jsonl_not_used_when_chroma_succeeds(monkeypatch):
    tools = registry(monkeypatch, [evidence("chroma_text", 0.8)], [evidence("jsonl_chunks", 0.9)])
    results = tools.search_text("CPU 1517-3 PN X1")
    assert [item.retrieval_backend for item in results] == ["chroma_text"]
    assert tools._jsonl_chunks.calls == 0
    assert tools.backend_audit["jsonl_fallback_triggered"] is False
