from safeplc_assist_box.evidence.answer_evidence_verifier import verify_answer_evidence
from safeplc_assist_box.schemas import AgentEvidence
from verifier_test_support import claim, decision_for


def test_parameter_range_verification():
    item = AgentEvidence("ev1", "manual", "manual", "table", "static range is 19.2 V to 72 V")
    accepted = claim("static range is 19.2 V to 72 V")
    result = verify_answer_evidence("static range is 19.2 V to 72 V", decision_for(accepted), [item])
    assert result["numeric_consistency_pass"] is True
    assert result["unit_consistency_pass"] is True
