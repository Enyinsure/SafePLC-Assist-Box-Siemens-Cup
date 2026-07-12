from safeplc_assist_box.evidence.fact_extractors import extract_led_checks


def test_led_extractor_page_2482_real_layout():
    text = """RUN/STOP LED 指示灯
ERROR LED 指示灯
MAINT LED 指示灯
端口 X1 P1 的 LINK RX/TX LED 指示灯
端口 X1 P2 的 LINK RX/TX LED 指示灯
端口 X2 P1 的 LINK RX/TX LED 指示灯"""
    assert extract_led_checks(text) == [
        "RUN/STOP LED", "ERROR LED", "MAINT LED",
        "X1 P1 LINK RX/TX LED", "X1 P2 LINK RX/TX LED",
    ]
