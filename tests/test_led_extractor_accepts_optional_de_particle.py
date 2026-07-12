from safeplc_assist_box.evidence.fact_extractors import extract_led_checks


def test_led_extractor_accepts_optional_de_particle():
    text = "X1 P1 LINK RX/TX LED；X1 P2 的 LINK RX/TX LED"
    assert extract_led_checks(text) == ["X1 P1 LINK RX/TX LED", "X1 P2 LINK RX/TX LED"]
