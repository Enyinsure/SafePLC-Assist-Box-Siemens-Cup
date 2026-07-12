from safeplc_assist_box.evidence.fact_extractors import extract_led_checks


def test_led_extractor_handles_line_break():
    assert extract_led_checks("X1\nP2 的 LINK RX/TX LED") == ["X1 P2 LINK RX/TX LED"]
    assert extract_led_checks("X1 P1R；X1 P2R") == ["X1 P1 LINK RX/TX LED", "X1 P2 LINK RX/TX LED"]
