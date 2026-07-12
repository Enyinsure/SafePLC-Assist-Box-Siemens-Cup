from safeplc_assist_box.agents.judge_agent import JudgeAgent
from safeplc_assist_box.schemas import AgentClaim, AgentEvidence, AgentResult, EvidencePool, QueryContext


def test_judge_rejects_low_information_wiring_claim():
    evidence = AgentEvidence("ev", "manual", "manual", "text", "接线 端子分配和接口说明")
    claim = AgentClaim("claim", "接线；端子分配；接口说明。", "connection", ["ev"], direct_support=True)
    result = AgentResult("Wiring Agent", "task", "ANSWERED", evidence_ids=["ev"], claims=[claim])
    decision = JudgeAgent().decide(QueryContext("S7-1500 端子接线注意事项是什么？"), [result], EvidencePool([evidence]))
    assert decision.verdict != "PASS"
    assert any("low_information_heading_fragment" in item for item in decision.unsupported_claims)
