from safeplc_assist_box.evidence.model_identity import classify_model_match
from safeplc_assist_box.schemas import AgentEvidence


def test_cross_family_rejection_for_redundant_cpu():
    ev = AgentEvidence("", "S7-1500R/H manual", "manual", "figure", "CPU 1517H R/H X1", module_model="CPU 1517H")
    assert classify_model_match("CPU 1517-3 PN 的 X1 接口在哪里？", ev) == "cross_family"
