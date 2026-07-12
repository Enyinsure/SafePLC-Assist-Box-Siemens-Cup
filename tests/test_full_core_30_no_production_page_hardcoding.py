from pathlib import Path

from benchmark.full_core_30.acceptance_rules import VERIFIED_PAGES, load_cases


ROOT = Path(__file__).resolve().parents[1]


def test_full_core_30_pages_are_verified_fixture_data_only():
    cases = load_cases()
    pages = {
        page
        for case in cases
        for page in case["expected"].get("required_evidence_pages", [])
    }
    assert pages <= VERIFIED_PAGES


def test_production_does_not_import_full_core_30_or_case_ids():
    case_ids = [case["case_id"] for case in load_cases()]
    for path in (ROOT / "safeplc_assist_box").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "full_core_30" not in text, path
        assert not any(case_id in text for case_id in case_ids), path
