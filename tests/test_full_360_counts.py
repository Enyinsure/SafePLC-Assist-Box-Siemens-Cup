from collections import Counter

from benchmark.generation.build_dev_120 import build_dev_120
from benchmark.generation.common import LAYER_COUNTS, NATURAL_COUNTS, STRESS_COUNTS
from full_360_test_support import build_fixture_dataset


def test_full_360_exact_layer_and_category_counts():
    dataset = build_fixture_dataset()
    cases = dataset["full"]
    assert len(cases) == 360
    assert Counter(case.get("benchmark_layer", "core") for case in cases) == LAYER_COUNTS
    assert Counter(case["category"] for case in dataset["natural"]) == NATURAL_COUNTS
    assert Counter(case["category"] for case in dataset["stress"]) == STRESS_COUNTS
    assert max(dataset["seed_usage"].values()) <= 5


def test_dev_120_is_stable_stratified_and_contains_all_core_cases():
    dataset = build_fixture_dataset()
    first = build_dev_120(dataset["full"])
    second = build_dev_120(dataset["full"])
    assert first == second
    assert len(first) == 120
    assert first[:30] == dataset["core"]
    assert {case.get("difficulty") for case in first[30:]} == {"easy", "medium", "hard"}
    actions = {action for case in first[30:] for action in case["expected_action"]}
    assert {"ANSWER", "CLARIFY", "ABSTAIN", "REFUSE"}.issubset(actions)
