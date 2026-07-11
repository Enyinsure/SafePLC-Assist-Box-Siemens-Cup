from safeplc_assist_box.evidence.answer_evidence_verifier import verify_answer_evidence
from safeplc_assist_box.schemas import AgentEvidence
from verifier_test_support import claim, decision_for


def test_interface_mismatch_detection():
    item = AgentEvidence("ev1", "manual", "manual", "text", "Use X1 P1 for this connection")
    accepted = claim("Use X2 P1 for this connection", claim_type="connection")
    result = verify_answer_evidence("Use X2 P1 for this connection", decision_for(accepted), [item])
    assert result["interface_consistency_pass"] is False
    assert result["interface_mismatch_claim_ids"] == ["c1"]
