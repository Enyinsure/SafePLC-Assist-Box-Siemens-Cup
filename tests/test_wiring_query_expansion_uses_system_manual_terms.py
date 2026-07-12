from safeplc_assist_box.retrieval.query_expander import QueryExpander


def test_wiring_query_expansion_uses_system_manual_terms():
    result = QueryExpander().expand("S7-1500 端子接线注意事项是什么？")
    assert result.intent == "wiring"
    assert result.all_queries[0] == "S7-1500 端子接线注意事项是什么？"
    assert "系统手册" in result.expanded_queries[0]
    assert "protective conductor" in result.expanded_queries[1]
