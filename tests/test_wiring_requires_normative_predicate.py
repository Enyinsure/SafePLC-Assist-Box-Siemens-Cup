from safeplc_assist_box.evidence.fact_extractors import extract_wiring_facts


def test_wiring_requires_normative_predicate():
    assert extract_wiring_facts("前连接器、端子、电源和保护导线说明") == []
    assert extract_wiring_facts("应连接保护导线") == ["应连接保护导线"]
