from safeplc_assist_box.evidence.claim_value_parser import parse_claim_values


def test_model_numbers_not_treated_as_parameter_values():
    parsed = parse_claim_values("CPU 1517-3 PN/DP, order 6ES7517-3AP00-0AB0")
    assert parsed.parameter_values == []
    assert parsed.models == ["CPU 1517-3 PN/DP"]
    assert parsed.order_numbers == ["6ES7517-3AP00-0AB0"]
