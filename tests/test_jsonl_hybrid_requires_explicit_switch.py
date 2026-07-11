from fallback_test_support import evidence, registry


def test_jsonl_hybrid_requires_explicit_switch(monkeypatch):
    strict = registry(monkeypatch, [evidence("chroma_text", 0.8)], [evidence("jsonl_chunks", 0.9)])
    assert {item.retrieval_backend for item in strict.search_text("CPU 1517-3 PN X1")} == {"chroma_text"}

    hybrid = registry(
        monkeypatch,
        [evidence("chroma_text", 0.8)],
        [evidence("jsonl_chunks", 0.9)],
        hybrid=True,
    )
    assert {item.retrieval_backend for item in hybrid.search_text("CPU 1517-3 PN X1")} == {
        "chroma_text",
        "jsonl_chunks",
    }
    assert hybrid.backend_audit["hybrid_mode"] is True
