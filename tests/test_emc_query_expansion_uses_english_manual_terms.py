from safeplc_assist_box.retrieval.query_expander import QueryExpander


def test_emc_query_expansion_uses_english_manual_terms():
    result = QueryExpander().expand("EMC 安装时接地和屏蔽需要注意什么？")
    assert result.intent == "emc"
    assert result.expanded_queries == [
        "electromagnetic compatibility industrial applications residential areas EN 55011 Class B",
        "S7-1500 system cabling grounded control cabinets control boxes noise filters supply lines EMC",
    ]
    assert all("page" not in item.lower() and "chunk" not in item.lower() for item in result.expanded_queries)
