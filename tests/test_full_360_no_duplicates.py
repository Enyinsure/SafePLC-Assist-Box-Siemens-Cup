from benchmark.generation.common import near_duplicate_candidates, normalize_query
from full_360_test_support import build_fixture_dataset


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
