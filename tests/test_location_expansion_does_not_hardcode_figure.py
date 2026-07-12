from safeplc_assist_box.retrieval.query_expander import QueryExpander


def test_location_expansion_does_not_hardcode_figure():
    expanded = " ".join(QueryExpander().expand("CPU 1517-3 PN 的 X1 位置在哪里？").expanded_queries)
    assert "2-237" not in expanded
    assert "⑦" not in expanded
