from safeplc_assist_box.evidence.answer_evidence_verifier import verify_answer_evidence
from safeplc_assist_box.schemas import AgentClaim, AgentEvidence, JudgeDecision


def test_verifier_figure_requirement():
    ev = AgentEvidence("ev1", "manual", "manual", "text", "X1 text only")
    claim = AgentClaim("c1", "X1 location", "location", ["ev1"], direct_support=True)
    decision = JudgeDecision(["A"], [], [], [claim.claim_text], [], [], ["ev1"], False, False, "answer", "PASS", "HIGH", "ok", metadata={"accepted_claims": [claim]})
    result = verify_answer_evidence("answer", decision, [ev])
    assert "c1" in result["missing_figure_claim_ids"]
