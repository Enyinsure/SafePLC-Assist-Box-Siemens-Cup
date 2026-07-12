from test_judge_accepts_structured_led_checklist import structured_led_decision


def test_full_led_checklist_is_not_partial():
    result, decision = structured_led_decision()
    assert result.claims[0].metadata["partial_coverage"] is False
    assert decision.verdict == "PASS"
