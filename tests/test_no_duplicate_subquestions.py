from safeplc_assist_box.agents.context_analyzer import ContextAnalyzer
from safeplc_assist_box.agents.query_decomposer import QueryDecomposer


def test_no_duplicate_subquestions():
    context = ContextAnalyzer().analyze("HMI 通过 PROFINET 连接时有哪些网络注意事项和注意事项？")
    items = QueryDecomposer().decompose(context)
    assert len({item.subquestion_id for item in items}) == len(items)
    assert len(items) <= 4
