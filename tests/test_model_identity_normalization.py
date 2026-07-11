from safeplc_assist_box.evidence.model_identity import extract_model_identity, normalize_model


def test_model_identity_normalization_aliases():
    assert normalize_model("1517-3 PN") == "CPU 1517-3 PN/DP"
    identity = extract_model_identity("CPU 1517-3 PN 6ES7517-3AP00-0AB0")
    assert "CPU 1517-3 PN/DP" in identity.normalized_models
    assert "6ES7517-3AP00-0AB0" in identity.order_numbers
