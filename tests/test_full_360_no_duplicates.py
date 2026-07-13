from benchmark.generation.build_full_360 import build_full_360
from benchmark.generation.common import (
    CORE_CASES_PATH,
    load_jsonl,
    near_duplicate_candidates,
    normalize_query,
    sha256_file,
)
from full_360_test_support import build_fixture_dataset, make_seed


def test_full_360_has_unique_ids_and_exact_queries():
    cases = build_fixture_dataset()["full"]
    assert len({case["case_id"] for case in cases}) == 360
    assert len({normalize_query(case["query"]) for case in cases}) == 360


def test_near_duplicate_detector_marks_but_does_not_delete_candidates():
    cases = [
        {"case_id": "a", "query": "CPU 1517 的 X1 接口在哪里？"},
        {"case_id": "b", "query": "CPU 1517 的 X1 接口位置在哪里？"},
        {"case_id": "c", "query": "电源模块允许电压范围是多少？"},
    ]
    candidates = near_duplicate_candidates(cases, token_threshold=0.70, trigram_threshold=0.70)
    assert any({item["left_case_id"], item["right_case_id"]} == {"a", "b"} for item in candidates)
    assert len(cases) == 3


def test_repeated_real_world_seed_identity_does_not_duplicate_queries():
    models = (
        "CPU 1517-3 PN/DP",
        "CPU 1518-4 PN/DP",
        "PS 60W 24/48/60VDC HF",
        "ET 200MP",
    )
    seeds = []
    for index in range(1, 101):
        seed = make_seed(index)
        seed["module_model"] = models[(index - 1) % len(models)]
        seed["order_number"] = ""
        seed["section"] = "General module data"
        seeds.append(seed)
    core = load_jsonl(CORE_CASES_PATH)
    generated = build_full_360(seeds, core, core_sha256=sha256_file(CORE_CASES_PATH))["full"]
    normalized = [normalize_query(case["query"]) for case in generated]
    assert len(normalized) == len(set(normalized)) == 360
