from safeplc_assist_box.evidence.model_identity import extract_model_identities, extract_model_identity


def test_power_module_identity_normalization():
    assert extract_model_identity("PS 60 W 24 / 48 / 60 V DC HF").normalized_model == "PS 60W 24/48/60VDC HF"
    assert extract_model_identity("PM 70 W 120/230 V AC/DC").normalized_model == "PM 70W 120/230VAC/DC"
    assert [item.product_type for item in extract_model_identities("PS 25 W 24 VDC and ET 200SP")] == ["PS", "ET"]
