from fallback_test_support import evidence, registry


def test_warning_distinguishes_missing_backend_from_filtered_results(monkeypatch):
    wrong = evidence("chroma_text", 0.9)
    wrong.module_model = "CPU 1518-4 PN/DP"
    tools = registry(monkeypatch, [wrong], [])
    tools.errors.clear()
    assert tools.search_text("CPU 1517-3 PN X1") == []
    assert "all_candidates_rejected_by_model_filter" in tools.backend_audit["jsonl_fallback_reason"]
    assert all("no active backend" not in item for item in tools.errors)
    assert tools.backend_audit["raw_result_count"] == 1
    assert tools.backend_audit["post_model_filter_count"] == 0
