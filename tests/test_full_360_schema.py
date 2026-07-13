import json

from benchmark.generation.build_full_360 import SCHEMA_VERSION
from benchmark.generation.common import SCHEMA_PATH
from benchmark.generation.validate_full_360 import validate_generated_case_schema
from full_360_test_support import build_fixture_dataset


def test_full_360_schema_accepts_every_generated_case():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["$id"] == SCHEMA_VERSION
    dataset = build_fixture_dataset()
    generated = dataset["natural"] + dataset["stress"]
    assert all(validate_generated_case_schema(case) == [] for case in generated)
    assert all(case["manual_reviewed"] is False for case in generated)
    assert all(case["review_status"] == "pending" for case in generated)
