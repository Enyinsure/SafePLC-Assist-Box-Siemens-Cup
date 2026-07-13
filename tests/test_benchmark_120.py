from __future__ import annotations

import json
from collections import Counter

from benchmark.generation.build_benchmark_120 import (
    CORE_SHA256,
    LAYER_120_COUNTS,
    NATURAL_120_COUNTS,
    STRESS_120_COUNTS,
    build_benchmark_120,
)
from benchmark.generation.build_full_360 import _has_figure_location
from benchmark.generation.common import CORE_CASES_PATH, load_jsonl, normalize_query, sha256_file
from benchmark.generation.validate_benchmark_120 import (
    CORE_ACCEPTANCE_SHA256,
    validate_benchmark_120_dataset,
)
from full_360_test_support import make_seed


def _dataset() -> dict:
    seeds = [make_seed(index) for index in range(1, 101)]
    core = load_jsonl(CORE_CASES_PATH)
    built = build_benchmark_120(seeds, core, core_sha256=sha256_file(CORE_CASES_PATH))
    return {**built, "seeds": seeds, "core": core}


def test_benchmark_120_exact_counts_and_categories():
    dataset = _dataset()
    full = dataset["full"]
    assert len(full) == 120
    assert Counter(case.get("benchmark_layer", "core") for case in full) == Counter(LAYER_120_COUNTS)
    assert Counter(case["category"] for case in dataset["natural"]) == Counter(NATURAL_120_COUNTS)
    assert Counter(case["category"] for case in dataset["stress"]) == Counter(STRESS_120_COUNTS)


def test_benchmark_120_build_is_deterministic_and_unique():
    seeds = [make_seed(index) for index in range(1, 101)]
    core = load_jsonl(CORE_CASES_PATH)
    first = build_benchmark_120(seeds, core, core_sha256=sha256_file(CORE_CASES_PATH))
    second = build_benchmark_120(seeds, core, core_sha256=sha256_file(CORE_CASES_PATH))
    assert json.dumps(first["full"], ensure_ascii=False, sort_keys=True) == json.dumps(
        second["full"], ensure_ascii=False, sort_keys=True
    )
    normalized = [normalize_query(case["query"]) for case in first["full"]]
    assert len(normalized) == len(set(normalized)) == 120
    assert first["query_uniqueness"]["exact_duplicate_count"] == 0


def test_benchmark_120_query_quality_and_figure_grounding():
    dataset = _dataset()
    seed_by_id = {seed["seed_id"]: seed for seed in dataset["seeds"]}
    generated = dataset["natural"] + dataset["stress"]
    assert all("该模块" not in case["query"] for case in generated)

    figure_cases = [case for case in dataset["natural"] if case["category"] == "figure_location"]
    assert len(figure_cases) == 8
    for case in figure_cases:
        assert case["required_figure_ids"]
        assert all(_has_figure_location(seed_by_id[seed_id]) for seed_id in case["source_seed_ids"])

    non_figure = {"parameter", "wiring", "troubleshooting", "emc", "compound_multi_agent"}
    for case in dataset["natural"]:
        if case["category"] in non_figure:
            assert case["required_figure_ids"] == []
            assert case["required_evidence_pages"] == []
            assert case["required_evidence_modalities"] == []


def test_benchmark_120_parameter_constraints_are_hard_nonempty_facts_only():
    dataset = _dataset()
    cases = [
        case
        for case in dataset["natural"]
        if "parameter" in (case.get("required_structured_facts") or {})
    ]
    assert cases
    for case in cases:
        expected = case["required_structured_facts"]["parameter"]
        assert not {"complete", "condition", "parameter_name"} & set(expected)
        assert all(value not in (None, "", []) for value in expected.values())


def test_benchmark_120_keeps_clarification_safety_and_cross_model_semantics():
    dataset = _dataset()
    natural = dataset["natural"]
    stress = dataset["stress"]

    clarification = [
        case
        for case in natural
        if case["category"] in {"missing_slot_clarification", "topology_clarification"}
    ]
    assert clarification
    assert all(case["expected_action"] == ["CLARIFY"] for case in clarification)
    assert all(case["expected_verdict"] == ["NEED_CLARIFICATION"] for case in clarification)

    safety = [case for case in stress if case["category"] == "industrial_safety_refusal"]
    assert safety
    for case in safety:
        assert case["expected_action"] == ["REFUSE"]
        assert case["expected_verdict"] == ["REFUSE"]
        assert set(case["scope_conditions"]["allowed_agents_any"]) == {
            "Wiring Agent",
            "Safety Boundary Agent",
        }
        assert case["must_have_empty_evidence"] is False

    cross_model = [case for case in stress if case["category"] == "cross_model_contamination"]
    assert cross_model
    for case in cross_model:
        assert set(case["expected_action"]) == {"ANSWER", "ABSTAIN"}
        assert case["scope_conditions"]["cross_model_comparison"]["target_model"]
        assert case["scope_conditions"]["cross_model_comparison"]["distractor_model"]


def test_benchmark_120_validator_and_frozen_core_contracts():
    dataset = _dataset()
    report = validate_benchmark_120_dataset(dataset["full"], dataset["seeds"], dataset["core"])
    assert report["valid"] is True, report["errors"]
    assert sha256_file(CORE_CASES_PATH) == CORE_SHA256
    assert sha256_file(CORE_CASES_PATH.with_name("acceptance_rules.py")) == CORE_ACCEPTANCE_SHA256
