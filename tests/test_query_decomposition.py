from safeplc_assist_box.agents.context_analyzer import ContextAnalyzer
from safeplc_assist_box.agents.query_decomposer import QueryDecomposer


def test_query_decomposition_multitask_x1_hmi():
    ctx = ContextAnalyzer().analyze("CPU 1517-3 PN 的 X1 接口在哪里，并说明 PROFINET 与 HMI 连接时的注意事项。")
    subquestions = QueryDecomposer().decompose(ctx)
    ids = {sq.subquestion_id for sq in subquestions}
    assert "sq_x1_location" in ids
    assert "sq_profinet_hmi" in ids
