from safeplc_assist_box.evidence.model_identity import reject_cross_family
from retrieval_test_support import evidence


def test_parameter_rejects_other_cpu_voltage_ranges():
    wrong = evidence("cpu", "CPU input 20 V to 30 V", model="CPU 1518-4 PN/DP")
    right = evidence("ps", "PS static 19.2 V to 72 V", model="PS 60W 24/48/60VDC HF")
    assert reject_cross_family([wrong, right], "PS 60W 24/48/60VDC HF voltage") == [right]
