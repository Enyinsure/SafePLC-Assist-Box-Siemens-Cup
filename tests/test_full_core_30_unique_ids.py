from benchmark.full_core_30.acceptance_rules import load_cases


def test_full_core_30_ids_and_ordinals_are_unique():
    cases = load_cases()
    ids = [case["case_id"] for case in cases]
    ordinals = [case["ordinal"] for case in cases]
    assert len(ids) == len(set(ids))
    assert ordinals == list(range(1, 31))
