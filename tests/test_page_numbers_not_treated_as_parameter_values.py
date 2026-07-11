from safeplc_assist_box.evidence.claim_value_parser import parse_claim_values


def test_page_and_figure_numbers_are_not_parameter_values():
    parsed = parse_claim_values("见资料页 2476、Figure 2-237，端口 X1 P1。")
    assert parsed.parameter_values == []
    assert parsed.page_numbers == [2476]
    assert parsed.figure_numbers == ["Figure 2-237"]
    assert parsed.port_labels == ["X1 P1"]
