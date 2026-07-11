from safeplc_assist_box.evidence.model_identity import classify_model_match
from safeplc_assist_box.schemas import AgentEvidence


def test_same_family_general_is_not_exact_model_support():
    evidence = AgentEvidence(
        "ev-general",
        "manual",
        "manual",
        "text",
        "General S7-1500 PROFINET guidance.",
        module_model="S7-1500 general",
        device_family="S7-1500",
    )
    assert classify_model_match("CPU 1517-3 PN interface", evidence) == "same_family_general"


def test_normal_cpu_and_redundant_cpu_are_not_compatible():
    evidence = AgentEvidence(
        "ev-rh",
        "R/H manual",
        "manual",
        "text",
        "CPU 1517H redundant interface",
        module_model="CPU 1517H",
    )
    assert classify_model_match("CPU 1517-3 PN interface", evidence) == "cross_family"
