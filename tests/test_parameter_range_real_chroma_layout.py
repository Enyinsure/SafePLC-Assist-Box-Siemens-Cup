from safeplc_assist_box.evidence.fact_extractors import extract_parameter_facts


TEXT = """电源电压
额定值 (DC)
24 V / 48 V / 60 V
允许范围，下限 (DC)
静态 19.2 V，动态 18.5 V
允许范围，上限 (DC)
静态 72 V，动态 75.5 V"""


def test_parameter_range_real_chroma_layout():
    facts = extract_parameter_facts(TEXT, "电源电压允许范围")

    assert facts.complete is True
    assert facts.rated_values == [24.0, 48.0, 60.0]
    assert facts.static_lower == 19.2
    assert facts.dynamic_lower == 18.5
    assert facts.static_upper == 72.0
    assert facts.dynamic_upper == 75.5
