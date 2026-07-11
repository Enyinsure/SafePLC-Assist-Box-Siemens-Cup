import pytest

from safeplc_assist_box.evidence.model_identity import extract_model_identity, normalize_model


@pytest.mark.parametrize(
    "raw,expected,product,family",
    [
        ("CPU 1517-3 PN", "CPU 1517-3 PN/DP", "CPU", "S7-1500"),
        ("CPU 1517-3 PN/DP", "CPU 1517-3 PN/DP", "CPU", "S7-1500"),
        ("PS 60W 24/48/60VDC HF", "PS 60W 24/48/60VDC HF", "PS", "S7-1500 POWER"),
        ("SM 521 DI", "SM 521 DI", "SM", "S7-1500 MODULE"),
        ("ET 200MP", "ET 200MP", "ET", "ET 200MP"),
        ("CPU 1517H", "CPU 1517 H", "CPU", "S7-1500R/H"),
        ("CPU 1518HF", "CPU 1518 HF", "CPU", "S7-1500R/H"),
    ],
)
def test_generic_model_identity(raw, expected, product, family):
    identity = extract_model_identity(raw)
    assert identity.normalized_model == expected
    assert identity.product_type == product
    assert identity.device_family == family
    assert normalize_model(raw) == expected


def test_order_number_is_extracted_separately():
    identity = extract_model_identity("CPU 1517-3 PN 6ES7517-3AP00-0AB0")
    assert identity.order_numbers == ["6ES7517-3AP00-0AB0"]
    assert identity.normalized_model == "CPU 1517-3 PN/DP"


def test_unicode_hyphen_and_ocr_spacing_are_normalized():
    identity = extract_model_identity("CPU 1517‑3\nPN / DP")
    assert identity.normalized_model == "CPU 1517-3 PN/DP"
