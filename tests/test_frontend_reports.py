from __future__ import annotations

from safeplc_assist_box.frontend.report_loader import (
    load_report_bundle,
    load_showcase_cases,
    load_supported_device_catalog,
)


def test_frontend_reports_only_use_repository_data() -> None:
    reports = load_report_bundle()
    cases = load_showcase_cases()
    catalog = load_supported_device_catalog()

    assert reports["benchmark"]["mode"] == "SAMPLE"
    assert reports["benchmark"]["case_count"] == 10
    assert 3 <= len(cases) <= 6
    assert all(case["source"] == "manual_curated_sample" for case in cases)
    assert catalog == {"S7-1500": ["CPU 1517-3 PN/DP", "PS 60W 24/48/60VDC HF"]}
