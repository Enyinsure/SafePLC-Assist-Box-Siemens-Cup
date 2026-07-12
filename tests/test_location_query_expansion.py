from safeplc_assist_box.retrieval.query_expander import QueryExpander


def test_location_query_expands_to_front_view_terms():
    result = QueryExpander().expand("CPU 1517-3 PN 的 X1 接口在哪里？")
    assert result.intent == "location"
    assert result.normalized_model == "CPU 1517-3 PN/DP"
    assert result.interface_names == ["X1"]
    assert result.expanded_queries == ["CPU 1517-3 PN/DP 不带前面板的模块前视图 PROFINET IO 接口 X1"]


def test_non_location_intents_do_not_expand_to_front_view():
    for query in ("CPU 1517-3 PN 的 X1 有几个端口？", "电源电压是多少？", "通信故障怎么排查？"):
        assert QueryExpander().expand(query).expanded_queries == []
