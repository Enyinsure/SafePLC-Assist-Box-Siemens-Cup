import json
from pathlib import Path

from benchmark.full_core_30.acceptance_rules import load_cases, validate_case_definition


ROOT = Path(__file__).resolve().parents[1]


def test_full_core_30_schema_and_cases_are_valid():
    schema = json.loads((ROOT / "benchmark/full_core_30/schema.json").read_text(encoding="utf-8"))
    assert schema["$id"] == "safeplc.full_core_30.case.v1"
    assert set(schema["required"]) == {"ordinal", "case_id", "category", "query", "origin", "server_verified", "expected"}
    for case in load_cases():
        assert validate_case_definition(case) == [], case["case_id"]
