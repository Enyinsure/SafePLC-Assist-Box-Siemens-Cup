from safeplc_assist_box.agents.context_analyzer import ContextAnalyzer
from safeplc_assist_box.agents.judge_agent import JudgeAgent
from safeplc_assist_box.agents.query_decomposer import QueryDecomposer
from safeplc_assist_box.schemas import AgentResult, EvidencePool


def test_judge_abstains_after_active_backend_returns_no_reliable_evidence():
    context = ContextAnalyzer().analyze("CPU 1517-3 PN 不存在的参数是多少？")
    context.missing_slots = []
    context.subquestions = QueryDecomposer().decompose(context)
    result = AgentResult("Parameter Agent", "task", "ABSTAIN", abstain_reason="no reliable evidence")
    pool = EvidencePool([], metadata={"retrieval_backend_audit": {"text_backend_active": True}})
    decision = JudgeAgent().decide(context, [result], pool)
    assert decision.verdict == "ABSTAIN"
    assert decision.confidence == "NOT_AVAILABLE"
