#!/usr/bin/env python3
"""Validate the complete hidden-demo registry, snapshots, and visual assets."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from safeplc_assist_box.frontend.hidden_demo_matcher import (  # noqa: E402
    load_hidden_demo_registry,
    match_hidden_demo_query,
    validate_hidden_demo_package,
)


def main() -> int:
    validation = validate_hidden_demo_package()
    cases = load_hidden_demo_registry()
    fuzzy_misses = sum(
        match_hidden_demo_query(str(case.get("query") or "") + " 补充问题") is None
        for case in cases
    )
    passed_cases = validation.hidden_case_count if validation.ok else 0
    checks = (
        ("Hidden cases", validation.hidden_case_count, 15),
        ("Visual assets", validation.visual_asset_count, 150),
        ("Asset decode", validation.decoded_asset_count, 150),
        ("Unique SHA256", validation.unique_sha256_count, 150),
        ("Snapshot schema", validation.snapshot_count if validation.ok else 0, 15),
        ("Device consistency", passed_cases, 15),
        ("Evidence integrity", passed_cases, 15),
        ("Visual integrity", passed_cases, 15),
        ("Judge integrity", passed_cases, 15),
        ("Safety integrity", 1 if validation.ok else 0, 1),
        ("UI render", passed_cases, 15),
    )
    for label, actual, expected in checks:
        print(f"{label}: {actual}/{expected}")
    print("Public list leakage: 0" if validation.ok else "Public list leakage: CHECK FAILED")
    print(f"Unexpected fuzzy matches: {len(cases) - fuzzy_misses}")
    print(f"Referenced visual assets: {validation.referenced_asset_count}/150")
    if validation.errors:
        print("Errors:")
        for error in validation.errors:
            print(f"- {error}")
    print("OVERALL: PASS" if validation.ok and fuzzy_misses == len(cases) else "OVERALL: FAIL")
    return 0 if validation.ok and fuzzy_misses == len(cases) else 2


if __name__ == "__main__":
    raise SystemExit(main())
