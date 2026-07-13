import json
from pathlib import Path

from benchmark.generation.common import PROJECT_ROOT, forbidden_project_terms
from full_360_test_support import build_fixture_dataset


def test_full_360_dataset_contains_only_industrial_assistant_content():
    serialized = json.dumps(build_fixture_dataset()["full"], ensure_ascii=False).lower()
    assert all(term.lower() not in serialized for term in forbidden_project_terms())


def test_full_360_source_and_documentation_contain_no_unrelated_project_content():
    paths = [
        *sorted((PROJECT_ROOT / "benchmark" / "generation").glob("*.py")),
        *sorted((PROJECT_ROOT / "benchmark" / "full_360").glob("*.py")),
        PROJECT_ROOT / "benchmark" / "schemas" / "full_360_case.schema.json",
        PROJECT_ROOT / "scripts" / "run_full_360.py",
        PROJECT_ROOT / "scripts" / "summarize_full_360.py",
        PROJECT_ROOT / "docs" / "FULL_360_BENCHMARK.md",
    ]
    content = "\n".join(Path(path).read_text(encoding="utf-8").lower() for path in paths)
    assert all(term.lower() not in content for term in forbidden_project_terms())
