from fallback_test_support import evidence, registry


def test_jsonl_used_on_low_quality_chroma(monkeypatch):
    tools = registry(
        monkeypatch,
        [evidence("chroma_text", 0.1)],
        [evidence("jsonl_chunks", 0.8)],
        min_score="0.20",
    )
    results = tools.search_text("CPU 1517-3 PN X1")
    assert {item.retrieval_backend for item in results} == {"chroma_text", "jsonl_chunks"}
    assert "below_threshold" in tools.backend_audit["jsonl_fallback_reason"]
