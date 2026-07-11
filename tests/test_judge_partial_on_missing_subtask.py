from safeplc_assist_box.agents.context_analyzer import ContextAnalyzer
from safeplc_assist_box.agents.judge_agent import JudgeAgent
from safeplc_assist_box.agents.query_decomposer import QueryDecomposer
from safeplc_assist_box.schemas import AgentClaim, AgentEvidence, AgentResult, EvidencePool


def test_judge_partial_on_missing_subtask():
    ctx = ContextAnalyzer().analyze("CPU 1517-3 PN 的 X1 接口在哪里，并说明 PROFINET 与 HMI 连接时的注意事项。")
    ctx.subquestions = QueryDecomposer().decompose(ctx)
    ev = AgentEvidence("ev1", "manual", "sample", "figure", "X1 figure", page=2476, figure_number="Figure 2-237")
    claim = AgentClaim("c1", "X1 location", "location", ["ev1"], direct_support=True, subquestion_ids=["sq_x1_location"])
    decision = JudgeAgent().decide(ctx, [AgentResult("Figure Agent", "t", "ANSWERED", evidence_ids=["ev1"], claims=[claim])], EvidencePool([ev]))
    assert decision.verdict == "PARTIAL"
