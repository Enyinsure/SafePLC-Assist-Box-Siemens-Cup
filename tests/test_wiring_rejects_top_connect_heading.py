from safeplc_assist_box.evidence.fact_extractors import extract_wiring_facts, has_wiring_normative_predicate


def test_wiring_rejects_top_connect_heading():
    heading = "Wiring SIMATIC TOP connect to the I/O modules"
    assert extract_wiring_facts(heading) == []
    assert has_wiring_normative_predicate(heading) is False
    assert has_wiring_normative_predicate("Use of terminal assignment diagrams") is False


def test_wiring_accepts_explicit_english_requirements():
    text = "Connect the protective conductor before commissioning.\nThe power supply must meet SELV/PELV requirements."
    facts = extract_wiring_facts(text)
    assert len(facts) == 2
    assert facts[0].startswith("Connect the protective conductor")
    assert "must meet SELV/PELV requirements" in facts[1]
