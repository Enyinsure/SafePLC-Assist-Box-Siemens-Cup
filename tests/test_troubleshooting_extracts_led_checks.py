from safeplc_assist_box.evidence.fact_extractors import extract_led_checks


def test_troubleshooting_extracts_led_checks():
    text = "RUN/STOP LED ERROR LED MAINT LED X1 P1 LINK RX/TX LED X1 P2 LINK RX/TX LED"
    assert len(extract_led_checks(text)) == 5
