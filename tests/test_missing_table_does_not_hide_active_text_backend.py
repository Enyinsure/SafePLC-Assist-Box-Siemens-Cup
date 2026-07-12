from fallback_test_support import evidence, registry


def test_missing_table_does_not_hide_active_text_backend(monkeypatch):
    tools = registry(monkeypatch, [evidence("chroma_text", 0.8)], [])
    tools.errors.clear()
    results = tools.search_table("CPU 1517-3 PN voltage")
    assert results
    assert "chroma_text" in tools.backend_audit["backend_attempted"]
    assert "chroma_text" in tools.backend_audit["backend_used"]
    assert all("no active backend" not in item for item in tools.errors)
