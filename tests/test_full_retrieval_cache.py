from fallback_test_support import evidence, registry


def test_full_fetch_page_and_figure_use_search_cache(monkeypatch):
    item = evidence("chroma_text", 0.8)
    item.page = 2476
    item.figure_id = "fig-x1"
    item.figure_number = "Figure 2-237"
    tools = registry(monkeypatch, [item], [])
    tools.search_text("CPU 1517-3 PN X1")
    assert tools.fetch_page("2476").evidence_id == item.evidence_id
    assert tools.fetch_figure("fig-x1").evidence_id == item.evidence_id
    assert tools.fetch_figure("Figure 2-237").evidence_id == item.evidence_id
    assert tools.backend_audit["tool_calls"][-1]["backend_used"] == ["retrieval_cache"]
