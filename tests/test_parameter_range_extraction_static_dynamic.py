from safeplc_assist_box.evidence.fact_extractors import extract_parameter_facts


TEXT = "额定输入 24 V DC、48 V DC、60 V DC。静态范围 19.2 V 至 72 V，动态范围 18.5 V 至 75.5 V。"


def test_parameter_range_extraction_static_dynamic():
    facts = extract_parameter_facts(TEXT, "电源电压允许范围")
    assert facts.complete
    assert facts.rated_values == [24.0, 48.0, 60.0]
    assert (facts.static_lower, facts.static_upper) == (19.2, 72.0)
    assert (facts.dynamic_lower, facts.dynamic_upper) == (18.5, 75.5)
