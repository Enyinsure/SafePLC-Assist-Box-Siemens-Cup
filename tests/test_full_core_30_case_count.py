from benchmark.full_core_30.acceptance_rules import category_counts, load_cases


EXPECTED_COUNTS = {
    "parameter": 4,
    "wiring": 4,
    "troubleshooting": 4,
    "figure_location": 4,
    "topology_clarification": 3,
    "emc": 3,
    "industrial_safety_refusal": 2,
    "unsupported_insufficient_evidence": 2,
    "cross_model_control": 2,
    "compound_multi_agent": 2,
}


def test_full_core_30_has_required_case_count_and_categories():
    cases = load_cases()
    assert len(cases) == 30
    assert category_counts(cases) == EXPECTED_COUNTS
