from safeplc_assist_box.retrieval.query_expander import QueryExpander


def test_location_expansion_does_not_hardcode_page():
    expanded = " ".join(QueryExpander().expand("CPU 1517-3 PN 的 X1 在哪？").expanded_queries)
    assert "2476" not in expanded
    assert "page" not in expanded.lower()
