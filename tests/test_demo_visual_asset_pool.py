from __future__ import annotations

import json

from safeplc_assist_box.frontend.demo_visual_assets import (
    CORE_VISUAL_MANIFEST,
    VISUAL_MANIFEST,
    load_demo_visual_manifest,
    validate_demo_visual_manifest,
)
from safeplc_assist_box.frontend.paths import PROJECT_ROOT


def test_complete_visual_pool_contains_every_qualified_real_manual_page() -> None:
    validation = validate_demo_visual_manifest(VISUAL_MANIFEST, expected_count=802)

    assert validation.ok, validation.errors
    assert validation.decoded_count == 802
    assert validation.unique_sha256_count == 802


def test_curated_150_reuses_full_pool_files_without_binary_copies() -> None:
    full = load_demo_visual_manifest(VISUAL_MANIFEST)
    curated = load_demo_visual_manifest(CORE_VISUAL_MANIFEST)
    full_by_path = {item["relative_path"]: item for item in full}

    assert len(curated) == 150
    assert [item["asset_id"] for item in curated] == [
        f"VIS_{index:04d}" for index in range(1, 151)
    ]
    for item in curated:
        source = full_by_path[item["relative_path"]]
        assert item["catalog_asset_id"] == source["asset_id"]
        assert item["sha256"] == source["sha256"]


def test_visual_audit_report_records_real_decodable_traceable_assets() -> None:
    report = json.loads(
        (PROJECT_ROOT / "reports" / "demo_visual_audit.json").read_text(encoding="utf-8")
    )
    summary = report["summary"]

    assert summary["qualified_count"] == 802
    assert summary["decoded_count"] == 802
    assert summary["unique_sha256_count"] == 802
    assert summary["rejected_count"] == 0


def test_every_full_pool_record_has_page_section_and_real_source() -> None:
    for asset in load_demo_visual_manifest(VISUAL_MANIFEST):
        assert int(asset["page"]) > 0
        assert str(asset["section"]).strip()
        assert asset["source"] == "real_manual_page"
        assert asset["verified"] is True
        assert (PROJECT_ROOT / asset["relative_path"]).is_file()
