from safeplc_assist_box.evidence.fact_extractors import extract_wiring_facts


def test_wiring_rejects_rh_topology_figure():
    assert extract_wiring_facts("S7-1500R/H topology IO device assignment network view PROFINET connection partner") == []
