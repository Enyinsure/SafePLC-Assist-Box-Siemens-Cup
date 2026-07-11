from safeplc_assist_box.agents.judge_agent import JudgeAgent
from safeplc_assist_box.schemas import AgentEvidence, AgentResult, EvidencePool, QueryContext


def test_judge_detects_conflict_group():
    ev = AgentEvidence("ev1", "src", "sample", "text", "24 V", page=1)
    pool = EvidencePool(evidences=[ev], conflicts=[{"evidence_ids": ["ev1", "ev2"], "reason": "different values"}])
    result = AgentResult("Parameter Agent", "t1", "ANSWERED", "24 V", evidence_ids=["ev1"])
    decision = JudgeAgent().decide(QueryContext("q"), [result], pool)
    assert decision.confidence == "CONFLICT"
    assert decision.conflict_groups

