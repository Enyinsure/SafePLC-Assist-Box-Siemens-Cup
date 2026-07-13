from __future__ import annotations

import inspect
from collections import Counter

import pytest

import benchmark.generation.build_full_360 as full_360_module
from benchmark.generation.build_full_360 import (
    MAX_CASES_PER_SEED,
    GenerationError,
    SeedAllocator,
    _allocate_single_case,
    build_full_360,
)
from benchmark.generation.common import CORE_CASES_PATH, load_jsonl, normalize_query, sha256_file
from full_360_test_support import build_fixture_dataset, make_seed


def _verified_fixture_seeds() -> list[dict]:
    return [make_seed(index) for index in range(1, 101)]


def test_candidates_are_read_only_stable_and_filter_committed_cap():
    allocator = SeedAllocator([make_seed(index) for index in range(1, 5)])
    candidates = allocator.candidates(lambda _seed: True)
    expected = sorted(
        candidates,
        key=lambda seed: (
            allocator.usage[seed["seed_id"]],
            allocator.tie_rank[seed["seed_id"]],
            seed["seed_id"],
        ),
    )
    assert candidates == expected
    assert allocator.usage == Counter()

    selected = candidates[0]
    for _ in range(MAX_CASES_PER_SEED):
        allocator.commit(selected)
    assert selected not in allocator.candidates(lambda _seed: True)
    with pytest.raises(GenerationError, match="five-case"):
        allocator.commit(selected)
    assert allocator.usage[selected["seed_id"]] == MAX_CASES_PER_SEED


def test_commit_rejects_the_same_seed_twice_without_mutating_usage():
    seed = make_seed(1)
    allocator = SeedAllocator([seed])
    with pytest.raises(GenerationError, match="same source seed"):
        allocator.commit(seed, seed)
    assert allocator.usage == Counter()


def test_core_reserved_collision_does_not_charge_failed_candidate():
    allocator = SeedAllocator([make_seed(1), make_seed(2)])
    ordered = allocator.candidates(lambda _seed: True)
    blocked_seed_id = ordered[0]["seed_id"]
    accepted_seed_id = ordered[1]["seed_id"]
    used_queries = {normalize_query("Core occupied query")}
    retries: Counter[str] = Counter()

    def build_case(_index: int, seed: dict) -> dict:
        query = "Core occupied query" if seed["seed_id"] == blocked_seed_id else "Unique evidence query"
        return {
            "category": "parameter",
            "query": query,
            "source_seed_ids": [seed["seed_id"]],
        }

    case = _allocate_single_case(
        allocator,
        lambda _seed: True,
        build_case,
        1,
        used_queries,
        retries,
        "parameter",
    )

    assert case["source_seed_ids"] == [accepted_seed_id]
    assert allocator.usage[blocked_seed_id] == 0
    assert allocator.usage[accepted_seed_id] == 1
    assert retries == Counter({"parameter": 1})


def test_build_reserves_core_queries_and_shares_one_set_across_layers(monkeypatch):
    core = load_jsonl(CORE_CASES_PATH)
    expected = {normalize_query(case["query"]) for case in core}
    observed: dict[str, object] = {}

    def fake_natural(_allocator, used_queries, _retries):
        observed["natural_set_id"] = id(used_queries)
        observed["initial"] = set(used_queries)
        used_queries.add("natural-layer-probe")
        return []

    def fake_stress(_allocator, used_queries, _retries):
        observed["stress_set_id"] = id(used_queries)
        observed["stress_saw_probe"] = "natural-layer-probe" in used_queries
        return []

    monkeypatch.setattr(full_360_module, "build_natural_cases", fake_natural)
    monkeypatch.setattr(full_360_module, "build_stress_cases", fake_stress)
    build_full_360(_verified_fixture_seeds(), core, core_sha256=sha256_file(CORE_CASES_PATH))

    assert observed["initial"] == expected
    assert observed["natural_set_id"] == observed["stress_set_id"]
    assert observed["stress_saw_probe"] is True


def test_pair_categories_use_distinct_seeds_and_keep_stress_models_distinct():
    dataset = build_fixture_dataset()
    seeds_by_id = {seed["seed_id"]: seed for seed in dataset["seeds"]}
    pair_categories = {
        "compound_multi_agent",
        "cross_model_contamination",
        "conflicting_or_distractor_evidence",
    }
    pair_cases = [
        case
        for case in dataset["natural"] + dataset["stress"]
        if case["category"] in pair_categories
    ]

    assert pair_cases
    assert all(len(case["source_seed_ids"]) == 2 for case in pair_cases)
    assert all(len(set(case["source_seed_ids"])) == 2 for case in pair_cases)
    for case in pair_cases:
        if case["category"] == "compound_multi_agent":
            continue
        left, right = (seeds_by_id[seed_id] for seed_id in case["source_seed_ids"])
        assert left["module_model"] != right["module_model"]


def test_two_builds_have_identical_case_query_and_seed_signatures():
    seeds = _verified_fixture_seeds()
    core = load_jsonl(CORE_CASES_PATH)
    core_hash = sha256_file(CORE_CASES_PATH)
    first = build_full_360(seeds, core, core_sha256=core_hash)
    second = build_full_360(seeds, core, core_sha256=core_hash)

    def signatures(built: dict) -> list[tuple[str, str, tuple[str, ...]]]:
        return [
            (case["case_id"], case["query"], tuple(case["source_seed_ids"]))
            for case in built["natural"] + built["stress"]
        ]

    assert signatures(first) == signatures(second)
    assert first["seed_usage"] == second["seed_usage"]
    assert first["duplicate_retry_by_category"] == second["duplicate_retry_by_category"]


def test_generated_queries_do_not_embed_internal_identifiers():
    dataset = build_fixture_dataset()
    seeds_by_id = {seed["seed_id"]: seed for seed in dataset["seeds"]}
    for case in dataset["natural"] + dataset["stress"]:
        query = case["query"]
        assert case["case_id"] not in query
        for seed_id in case["source_seed_ids"]:
            assert seed_id not in query
            assert seeds_by_id[seed_id]["source_record_id"] not in query


def test_formal_layer_builders_do_not_use_eager_take():
    source = inspect.getsource(full_360_module.build_natural_cases)
    source += inspect.getsource(full_360_module.build_stress_cases)
    assert ".take(" not in source


def test_final_exact_duplicate_validation_is_fatal(monkeypatch):
    core = load_jsonl(CORE_CASES_PATH)

    def duplicate_natural(_allocator, _used_queries, _retries):
        return [{"query": core[0]["query"]}]

    monkeypatch.setattr(full_360_module, "build_natural_cases", duplicate_natural)
    monkeypatch.setattr(full_360_module, "build_stress_cases", lambda *_args: [])
    with pytest.raises(GenerationError, match="exact normalized duplicates"):
        build_full_360(
            _verified_fixture_seeds(),
            core,
            core_sha256=sha256_file(CORE_CASES_PATH),
        )
