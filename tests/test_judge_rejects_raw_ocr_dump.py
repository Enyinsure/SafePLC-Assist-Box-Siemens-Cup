from safeplc_assist_box.agents.judge_agent import JudgeAgent
from safeplc_assist_box.schemas import AgentClaim, AgentEvidence, AgentResult, EvidencePool, QueryContext


def test_judge_rejects_raw_ocr_dump():
    ev = AgentEvidence("ev1", "manual", "manual", "text", "support")
    claim = AgentClaim("c1", "line\n" * 20, "grounded_qa", ["ev1"], direct_support=True)
    decision = JudgeAgent().decide(QueryContext("q"), [AgentResult("Parameter Agent", "t", "ANSWERED", evidence_ids=["ev1"], claims=[claim])], EvidencePool([ev]))
    assert decision.verdict == "NEED_MORE_EVIDENCE"
