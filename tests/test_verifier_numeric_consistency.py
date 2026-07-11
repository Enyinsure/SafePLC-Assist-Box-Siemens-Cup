from safeplc_assist_box.evidence.answer_evidence_verifier import verify_answer_evidence
from safeplc_assist_box.schemas import AgentClaim, AgentEvidence, JudgeDecision


def test_verifier_numeric_consistency():
    ev = AgentEvidence("ev1", "manual", "manual", "table", "range is 24 V to 48 V")
    claim = AgentClaim("c1", "range is 24 V to 60 V", "parameter", ["ev1"], direct_support=True)
    decision = JudgeDecision(["A"], [], [], [claim.claim_text], [], [], ["ev1"], False, False, "answer", "PASS", "HIGH", "ok", metadata={"accepted_claims": [claim]})
    result = verify_answer_evidence("answer", decision, [ev])
    assert "c1" in result["numeric_mismatch_claim_ids"]
