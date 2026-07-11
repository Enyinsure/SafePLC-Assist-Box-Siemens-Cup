from pathlib import Path


def test_business_code_does_not_route_by_case_id():
    root = Path("safeplc_assist_box")
    business_files = list((root / "agents").glob("*.py")) + list((root / "tools").glob("*.py"))
    combined = "\n".join(path.read_text(encoding="utf-8") for path in business_files)
    assert "case_id" not in combined
