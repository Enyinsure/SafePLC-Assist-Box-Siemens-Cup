from safeplc_assist_box.agents.judge_agent import JudgeAgent
from safeplc_assist_box.schemas import AgentClaim, AgentEvidence, AgentResult, EvidencePool, QueryContext


def test_judge_rejects_cross_model():
    ev = AgentEvidence("ev1", "R/H manual", "manual", "figure", "CPU 1517H X1", model_match_level="cross_family")
    claim = AgentClaim("c1", "R/H X1 applies", "location", ["ev1"], direct_support=True)
    decision = JudgeAgent().decide(QueryContext("CPU 1517-3 PN X1"), [AgentResult("Figure Agent", "t", "ANSWERED", evidence_ids=["ev1"], claims=[claim])], EvidencePool([ev]))
    assert decision.verdict == "NEED_MORE_EVIDENCE"
    assert decision.unsupported_claims
