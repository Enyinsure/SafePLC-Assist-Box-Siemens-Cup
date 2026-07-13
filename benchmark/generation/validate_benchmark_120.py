#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from benchmark.generation.build_benchmark_120 import (
    BENCHMARK_120_DIR,
    CASES_PATH,
    CORE_HASH_PATH,
    CORE_SHA256,
    LAYER_120_COUNTS,
    NATURAL_120_COUNTS,
    REVIEW_QUEUE_PATH,
    STRESS_120_COUNTS,
)
from benchmark.generation.build_full_360 import DEFAULT_SEED_BANK
from benchmark.generation.common import CORE_CASES_PATH, load_jsonl, sha256_file, write_json, write_jsonl
from benchmark.generation.validate_full_360 import validate_dataset

REPORT_PATH = BENCHMARK_120_DIR / "validation_report.json"
CORE_ACCEPTANCE_SHA256 = "44057f27781ef0aadd5d1eab21bf7ddb1c89dcbc4af0dd41e6ae563ad334ae95"


def _append_error(report: Dict[str, Any], code: str, detail: Any = None) -> None:
    error: Dict[str, Any] = {"code": code}
    if detail not in (None, ""):
        error["detail"] = detail
    report.setdefault("errors", []).append(error)
    report["valid"] = False


def validate_benchmark_120_dataset(
    cases: Sequence[Dict[str, Any]],
    seeds: Sequence[Dict[str, Any]],
    core_cases: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    report = validate_dataset(cases, seeds, core_cases, require_exact_counts=False)
    report["schema"] = "safeplc.benchmark_120.validation.v1"

    layers = Counter(str(case.get("benchmark_layer") or "core") for case in cases)
    natural = Counter(
        str(case.get("category") or "")
        for case in cases
        if case.get("benchmark_layer") == "natural"
    )
    stress = Counter(
        str(case.get("category") or "")
        for case in cases
        if case.get("benchmark_layer") == "stress"
    )

    if len(cases) != 120:
        _append_error(report, "invalid_total_count", {"actual": len(cases), "expected": 120})
    if dict(layers) != LAYER_120_COUNTS:
        _append_error(report, "invalid_layer_counts", {"actual": dict(layers), "expected": LAYER_120_COUNTS})
    if dict(natural) != NATURAL_120_COUNTS:
        _append_error(
            report,
            "invalid_natural_category_counts",
            {"actual": dict(natural), "expected": NATURAL_120_COUNTS},
        )
    if dict(stress) != STRESS_120_COUNTS:
        _append_error(
            report,
            "invalid_stress_category_counts",
            {"actual": dict(stress), "expected": STRESS_120_COUNTS},
        )

    dataset_core = [case for case in cases if str(case.get("benchmark_layer") or "core") == "core"]
    if dataset_core != list(core_cases):
        _append_error(report, "core_order_or_content_changed")

    report["case_count"] = len(cases)
    report["layer_counts"] = dict(sorted(layers.items()))
    report["natural_category_counts"] = dict(sorted(natural.items()))
    report["stress_category_counts"] = dict(sorted(stress.items()))
    return report


def validate_files(
    cases_path: Path = CASES_PATH,
    seeds_path: Path = DEFAULT_SEED_BANK,
    core_hash_path: Path = CORE_HASH_PATH,
    review_queue_path: Optional[Path] = REVIEW_QUEUE_PATH,
) -> Dict[str, Any]:
    cases = load_jsonl(cases_path)
    seeds = load_jsonl(seeds_path)
    core_cases = load_jsonl(CORE_CASES_PATH)
    report = validate_benchmark_120_dataset(cases, seeds, core_cases)

    current_core_hash = sha256_file(CORE_CASES_PATH)
    acceptance_path = CORE_CASES_PATH.with_name("acceptance_rules.py")
    current_acceptance_hash = sha256_file(acceptance_path)
    manifest_hash = core_hash_path.read_text(encoding="utf-8").strip().split()[0]

    report.update({
        "core_sha256_expected": CORE_SHA256,
        "core_sha256_manifest": manifest_hash,
        "core_sha256_actual": current_core_hash,
        "core_acceptance_sha256_expected": CORE_ACCEPTANCE_SHA256,
        "core_acceptance_sha256_actual": current_acceptance_hash,
    })

    if manifest_hash != CORE_SHA256 or current_core_hash != CORE_SHA256:
        _append_error(report, "core_sha256_changed")
    if current_acceptance_hash != CORE_ACCEPTANCE_SHA256:
        _append_error(report, "core_acceptance_sha256_changed")

    if review_queue_path is not None:
        write_jsonl(review_queue_path, report.get("near_duplicate_candidates") or [])
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the SafePLC Benchmark-120 dataset.")
    parser.add_argument("--cases", default=str(CASES_PATH))
    parser.add_argument("--seeds", default=str(DEFAULT_SEED_BANK))
    parser.add_argument("--core-hash", default=str(CORE_HASH_PATH))
    parser.add_argument("--review-queue", default=str(REVIEW_QUEUE_PATH))
    parser.add_argument("--report", default=str(REPORT_PATH))
    args = parser.parse_args(argv)

    try:
        report = validate_files(
            Path(args.cases),
            Path(args.seeds),
            Path(args.core_hash),
            Path(args.review_queue) if args.review_queue else None,
        )
    except (FileNotFoundError, IndexError, ValueError) as exc:
        print(f"Benchmark-120 validation blocked: {exc}", file=sys.stderr)
        return 2

    if args.report:
        write_json(Path(args.report), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
