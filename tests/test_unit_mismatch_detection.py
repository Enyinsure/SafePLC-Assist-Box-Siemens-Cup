from safeplc_assist_box.evidence.answer_evidence_verifier import verify_answer_evidence
from safeplc_assist_box.schemas import AgentEvidence
from verifier_test_support import claim, decision_for


def test_unit_mismatch_detection():
    item = AgentEvidence("ev1", "manual", "manual", "table", "rated value is 24 V")
    accepted = claim("rated value is 24 A")
    result = verify_answer_evidence("rated value is 24 A", decision_for(accepted), [item])
    assert result["numeric_consistency_pass"] is True
    assert result["unit_consistency_pass"] is False
    assert result["unit_mismatch_claim_ids"] == ["c1", "__final_answer__"]
