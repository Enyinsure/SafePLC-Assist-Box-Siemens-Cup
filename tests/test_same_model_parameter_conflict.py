from safeplc_assist_box.evidence.evidence_pool import SharedEvidencePool
from safeplc_assist_box.schemas import AgentEvidence


def test_same_model_parameter_conflict():
    pool = SharedEvidencePool()
    pool.add(AgentEvidence("a", "m1", "m", "table", "Input 24 V", module_model="CPU 1517", parameter="input"), "Parameter Agent")
    pool.add(AgentEvidence("b", "m2", "m", "table", "Input 48 V", module_model="CPU 1517", parameter="input"), "Parameter Agent")
    assert any(item["reason"] == "same_model_parameter_value_conflict" for item in pool.conflicts)
