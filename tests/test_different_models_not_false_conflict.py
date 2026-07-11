from safeplc_assist_box.evidence.evidence_pool import SharedEvidencePool
from safeplc_assist_box.schemas import AgentEvidence


def test_different_models_not_false_conflict():
    pool = SharedEvidencePool()
    pool.add(AgentEvidence("a", "m", "m", "table", "Input 24 V", module_model="CPU 1515", parameter="input"), "Parameter Agent")
    pool.add(AgentEvidence("b", "m", "m", "table", "Input 48 V", module_model="CPU 1517", parameter="input"), "Parameter Agent")
    assert pool.conflicts == []
