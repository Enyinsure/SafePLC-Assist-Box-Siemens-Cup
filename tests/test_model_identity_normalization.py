from safeplc_assist_box.evidence.model_identity import extract_model_identity, normalize_model
from safeplc_assist_box.evidence.model_identity import classify_model_match
from retrieval_test_support import evidence
import pytest


def test_model_identity_normalization_aliases():
    assert normalize_model("1517-3 PN") == "CPU 1517-3 PN/DP"
    identity = extract_model_identity("CPU 1517-3 PN 6ES7517-3AP00-0AB0")
    assert "CPU 1517-3 PN/DP" in identity.normalized_models
    assert "6ES7517-3AP00-0AB0" in identity.order_numbers


def test_explicit_standard_cpu_is_not_changed_by_negated_rh_reference():
    identity = extract_model_identity("CPU 1517-3 PN 的 X1 在哪里？不要使用 R/H 冗余资料。")
    assert identity.normalized_model == "CPU 1517-3 PN/DP"
    assert identity.device_family == "S7-1500"


@pytest.mark.parametrize(
    "other_model",
    ["CPU 1517H-3 PN", "CPU 1517T-3 PN/DP", "CPU 1518-4 PN/DP", "CPU 1518HF-4 PN", "CPU 1513R-1 PN", "CPU 1511T-1 PN"],
)
def test_other_exact_cpu_variants_are_not_compatible_aliases(other_model):
    item = evidence("other", f"{other_model} X1", model=other_model)
    assert classify_model_match("CPU 1517-3 PN/DP X1", item) == "cross_family"
