from benchmark.generation.build_dev_120 import build_dev_120
from benchmark.generation.build_evidence_seed_bank import build_seed_bank_from_records
from benchmark.generation.build_full_360 import FROZEN_HASH_PATH, generate_files
from benchmark.generation.common import load_jsonl, write_jsonl
from benchmark.generation.validate_full_360 import validate_dataset, validate_files
from full_360_test_support import build_fixture_dataset


def test_full_360_answer_cases_and_mutations_are_traceable():
    dataset = build_fixture_dataset()
    report = validate_dataset(dataset["full"], dataset["seeds"], dataset["core"])
    assert report["valid"] is True, report["errors"]
    generated = dataset["natural"] + dataset["stress"]
    assert all(case["source_seed_ids"] for case in generated if "ANSWER" in case["expected_action"])
    assert all(case["parent_seed_id"] for case in dataset["stress"])
    assert all(case["mutation_type"] for case in dataset["stress"])
    assert all(case["manual_reviewed"] is False for case in generated)


def test_seed_builder_filters_garbage_and_extracts_supported_facts(tmp_path):
    valid = {
        "text": (
            "CPU 1517-3 PN/DP 6ES7517-3AP00-0AB0 电源电压 额定值 (DC) 24 V。"
            "静态范围 19.2 V 至 72 V，动态范围 18.5 V 至 75.5 V。"
            "① PROFINET IO 接口 X1，带 2 个端口。图 2-237 模块前视图。"
        ),
        "metadata": {"page_no": 2476, "section": "CPU 1517-3 PN/DP"},
    }
    garbled = {"text": "鈶 妯 鐨 锛", "metadata": {"page_no": 1}}
    records = [
        (valid, "text_chroma", str(tmp_path), "manual", "record-1"),
        (garbled, "text_chroma", str(tmp_path), "manual", "record-2"),
    ]
    seeds, report = build_seed_bank_from_records(records)
    assert len(seeds) == 1
    assert seeds[0]["source_verified"] is True
    assert seeds[0]["page"] == 2476
    assert seeds[0]["structured_facts"]["parameter"]["complete"] is True
    assert seeds[0]["structured_facts"]["location_markers"]["X1"] == "①"
    assert report["rejected_counts"]["empty_or_too_short"] == 1


def test_full_360_file_generation_dev_sampling_and_validation_pipeline(tmp_path):
    dataset = build_fixture_dataset()
    seed_path = tmp_path / "evidence_seed_bank.jsonl"
    write_jsonl(seed_path, dataset["seeds"])
    generation = generate_files(seed_path, tmp_path)
    assert generation["full_count"] == 360
    assert generation["query_uniqueness"]["full_normalized_unique_count"] == 360
    assert generation["query_uniqueness"]["exact_duplicate_count"] == 0
    assert set(generation["duplicate_retry_by_category"]) == set(
        generation["natural_category_counts"]
    ) | set(generation["stress_category_counts"])
    full_cases = load_jsonl(tmp_path / "full_360.jsonl")
    dev_cases = build_dev_120(full_cases)
    write_jsonl(tmp_path / "dev_120.jsonl", dev_cases)
    report = validate_files(
        tmp_path / "full_360.jsonl",
        seed_path,
        FROZEN_HASH_PATH,
        tmp_path / "manual_review_queue.jsonl",
    )
    assert report["valid"] is True, report["errors"]
    assert len(load_jsonl(tmp_path / "dev_120.jsonl")) == 120
