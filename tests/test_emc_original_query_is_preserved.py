from safeplc_assist_box.retrieval.query_expander import QueryExpander


def test_emc_original_query_is_preserved():
    query = "EMC 安装时接地和屏蔽需要注意什么？"
    result = QueryExpander().expand(query)
    assert result.original_query == query
    assert result.all_queries[0] == query
    assert len(result.all_queries) == 3
