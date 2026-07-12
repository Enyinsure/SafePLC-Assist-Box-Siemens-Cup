from safeplc_assist_box.evidence.model_identity import classify_model_match
from retrieval_test_support import evidence


def test_ps_spacing_variants_are_aliases():
    item = evidence("ps", "PS 60 W 24 / 48 / 60 V DC HF", model="PS 60 W 24 / 48 / 60 V DC HF")
    assert classify_model_match("PS 60W 24/48/60VDC HF", item) == "exact_model"
