from safeplc_assist_box.evidence.fact_extractors import extract_led_checks


def test_led_extractor_accepts_chinese_port_prefix():
    checks = extract_led_checks("端口 X1 P1 的 LINK RX/TX LED 指示灯")
    assert checks == ["X1 P1 LINK RX/TX LED"]
