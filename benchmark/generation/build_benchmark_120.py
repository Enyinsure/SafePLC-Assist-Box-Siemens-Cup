#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from benchmark.generation.build_full_360 import (
    DEFAULT_SEED_BANK,
    MAX_CASES_PER_SEED,
    GenerationError,
    SeedAllocator,
    _allocate_pair_case,
    _allocate_single_case,
    _different_identity,
    _has_emc,
    _has_figure,
    _has_figure_location,
    _has_identity,
    _has_led,
    _has_maintenance_fact,
    _has_parameter,
    _has_topology,
    _has_wiring,
    _natural_compound,
    _natural_emc,
    _natural_figure,
    _natural_missing_slot,
    _natural_parameter,
    _natural_topology_clarification,
    _natural_troubleshooting,
    _natural_wiring,
    _natural_work_order,
    _stress_conflict,
    _stress_cross_model,
    _stress_multimodal,
    _stress_safety,
    _stress_unsupported,
    _verified,
    generated_case_quality_issues,
    maintenance_contract_available,
)
from benchmark.generation.common import (
    CORE_CASES_PATH,
    GENERATOR_SEED,
    load_jsonl,
    near_duplicate_candidates,
    normalize_query,
    sha256_file,
    write_json,
    write_jsonl,
)

BENCHMARK_120_DIR = PROJECT_ROOT / "benchmark" / "cases" / "benchmark_120"
CASES_PATH = BENCHMARK_120_DIR / "cases.jsonl"
NATURAL_PATH = BENCHMARK_120_DIR / "natural_60.jsonl"
STRESS_PATH = BENCHMARK_120_DIR / "stress_30.jsonl"
REVIEW_QUEUE_PATH = BENCHMARK_120_DIR / "manual_review_queue.jsonl"
REPORT_PATH = BENCHMARK_120_DIR / "generation_report.json"
CORE_HASH_PATH = BENCHMARK_120_DIR / "core_30.sha256"

CORE_SHA256 = "960b49fa349bfe4d165d0cc341252b7180e2d9849ab38ea8aa69d35980337335"

NATURAL_120_COUNTS = {
    "parameter": 10,
    "wiring": 8,
    "troubleshooting": 8,
    "figure_location": 8,
    "emc": 6,
    "topology_clarification": 6,
    "compound_multi_agent": 6,
    "missing_slot_clarification": 4,
    "maintenance_work_order": 4,
}

STRESS_120_COUNTS = {
    "cross_model_contamination": 8,
    "unsupported_entity": 6,
    "industrial_safety_refusal": 6,
    "conflicting_or_distractor_evidence": 5,
    "multimodal_missing_or_mismatch": 5,
}

LAYER_120_COUNTS = {"core": 30, "natural": 60, "stress": 30}
NATURAL_ORDER = tuple(NATURAL_120_COUNTS)
STRESS_ORDER = tuple(STRESS_120_COUNTS)


def _append_single(
    buckets: Dict[str, List[Dict[str, Any]]],
    allocator: SeedAllocator,
    used_queries: set[str],
    duplicate_retries: Counter[str],
    category: str,
    count: int,
    predicate: Callable[[Dict[str, Any]], bool],
    builder: Callable[[int, Dict[str, Any]], Dict[str, Any]],
) -> None:
    for index in range(1, count + 1):
        buckets[category].append(
            _allocate_single_case(
                allocator,
                predicate,
                builder,
                index,
                used_queries,
                duplicate_retries,
                category,
            )
        )


def _append_pair(
    buckets: Dict[str, List[Dict[str, Any]]],
    allocator: SeedAllocator,
    used_queries: set[str],
    duplicate_retries: Counter[str],
    category: str,
    count: int,
    left_predicate: Callable[[Dict[str, Any]], bool],
    right_predicate: Callable[[Dict[str, Any], Dict[str, Any]], bool],
    builder: Callable[[int, Dict[str, Any], Dict[str, Any]], Dict[str, Any]],
) -> None:
    for index in range(1, count + 1):
        buckets[category].append(
            _allocate_pair_case(
                allocator,
                left_predicate,
                right_predicate,
                builder,
                index,
                used_queries,
                duplicate_retries,
                category,
            )
        )


def build_benchmark_120(
    seeds: Sequence[Dict[str, Any]],
    core_cases: Sequence[Dict[str, Any]],
    *,
    core_sha256: str,
) -> Dict[str, Any]:
    if len(core_cases) != 30:
        raise GenerationError(f"Core-30 must contain exactly 30 cases, found {len(core_cases)}")
    if core_sha256 != CORE_SHA256:
        raise GenerationError("Core-30 SHA256 differs from the frozen Benchmark-120 contract")
    if not maintenance_contract_available():
        raise GenerationError("Stable maintenance work-order output contract is unavailable")

    verified = [seed for seed in seeds if _verified(seed)]
    if len(verified) < 30:
        raise GenerationError(f"At least 30 verified seeds are required, found {len(verified)}")

    allocator = SeedAllocator(verified, random_seed=GENERATOR_SEED)
    used_queries = {normalize_query(str(case.get("query") or "")) for case in core_cases}
    duplicate_retries: Counter[str] = Counter()
    natural_buckets: Dict[str, List[Dict[str, Any]]] = {name: [] for name in NATURAL_ORDER}
    stress_buckets: Dict[str, List[Dict[str, Any]]] = {name: [] for name in STRESS_ORDER}

    # Scarce visual evidence is reserved before broad categories consume seed capacity.
    _append_single(
        natural_buckets,
        allocator,
        used_queries,
        duplicate_retries,
        "figure_location",
        NATURAL_120_COUNTS["figure_location"],
        _has_figure_location,
        _natural_figure,
    )
    _append_single(
        stress_buckets,
        allocator,
        used_queries,
        duplicate_retries,
        "multimodal_missing_or_mismatch",
        STRESS_120_COUNTS["multimodal_missing_or_mismatch"],
        _has_figure,
        _stress_multimodal,
    )

    # Figure cases are already reserved above. The allocator's usage-first ordering
    # naturally prefers untouched non-figure seeds when broad maintenance seeds exist,
    # while still allowing deterministic fallback for fixture or sparse datasets.
    _append_single(
        natural_buckets,
        allocator,
        used_queries,
        duplicate_retries,
        "maintenance_work_order",
        NATURAL_120_COUNTS["maintenance_work_order"],
        _has_maintenance_fact,
        _natural_work_order,
    )
    _append_single(
        natural_buckets,
        allocator,
        used_queries,
        duplicate_retries,
        "emc",
        NATURAL_120_COUNTS["emc"],
        _has_emc,
        _natural_emc,
    )
    _append_single(
        natural_buckets,
        allocator,
        used_queries,
        duplicate_retries,
        "parameter",
        NATURAL_120_COUNTS["parameter"],
        _has_parameter,
        _natural_parameter,
    )
    _append_single(
        natural_buckets,
        allocator,
        used_queries,
        duplicate_retries,
        "troubleshooting",
        NATURAL_120_COUNTS["troubleshooting"],
        _has_led,
        _natural_troubleshooting,
    )
    _append_single(
        natural_buckets,
        allocator,
        used_queries,
        duplicate_retries,
        "wiring",
        NATURAL_120_COUNTS["wiring"],
        _has_wiring,
        _natural_wiring,
    )
    _append_pair(
        natural_buckets,
        allocator,
        used_queries,
        duplicate_retries,
        "compound_multi_agent",
        NATURAL_120_COUNTS["compound_multi_agent"],
        _has_parameter,
        lambda _left, right: _has_wiring(right),
        _natural_compound,
    )
    _append_single(
        natural_buckets,
        allocator,
        used_queries,
        duplicate_retries,
        "topology_clarification",
        NATURAL_120_COUNTS["topology_clarification"],
        _has_topology,
        _natural_topology_clarification,
    )
    _append_single(
        natural_buckets,
        allocator,
        used_queries,
        duplicate_retries,
        "missing_slot_clarification",
        NATURAL_120_COUNTS["missing_slot_clarification"],
        _has_identity,
        _natural_missing_slot,
    )

    _append_pair(
        stress_buckets,
        allocator,
        used_queries,
        duplicate_retries,
        "cross_model_contamination",
        STRESS_120_COUNTS["cross_model_contamination"],
        _has_identity,
        _different_identity,
        _stress_cross_model,
    )
    _append_single(
        stress_buckets,
        allocator,
        used_queries,
        duplicate_retries,
        "unsupported_entity",
        STRESS_120_COUNTS["unsupported_entity"],
        _has_identity,
        _stress_unsupported,
    )
    _append_single(
        stress_buckets,
        allocator,
        used_queries,
        duplicate_retries,
        "industrial_safety_refusal",
        STRESS_120_COUNTS["industrial_safety_refusal"],
        _has_identity,
        _stress_safety,
    )
    _append_pair(
        stress_buckets,
        allocator,
        used_queries,
        duplicate_retries,
        "conflicting_or_distractor_evidence",
        STRESS_120_COUNTS["conflicting_or_distractor_evidence"],
        _has_identity,
        _different_identity,
        _stress_conflict,
    )

    natural = [case for category in NATURAL_ORDER for case in natural_buckets[category]]
    stress = [case for category in STRESS_ORDER for case in stress_buckets[category]]
    full = list(core_cases) + natural + stress

    seed_by_id = {str(seed["seed_id"]): seed for seed in verified}
    quality_failures = {
        str(case.get("case_id") or ""): generated_case_quality_issues(
            case,
            [seed_by_id[seed_id] for seed_id in case.get("source_seed_ids") or [] if seed_id in seed_by_id],
        )
        for case in natural + stress
    }
    quality_failures = {case_id: issues for case_id, issues in quality_failures.items() if issues}
    if quality_failures:
        raise GenerationError(f"Benchmark-120 query quality validation failed: {quality_failures}")

    normalized = [normalize_query(str(case.get("query") or "")) for case in full]
    duplicate_count = len(normalized) - len(set(normalized))
    if duplicate_count:
        raise GenerationError(f"Benchmark-120 contains {duplicate_count} exact normalized duplicates")
    if any(count > MAX_CASES_PER_SEED for count in allocator.usage.values()):
        raise GenerationError("A source seed exceeded the five-case generation cap")

    review_queue = near_duplicate_candidates(full)
    all_categories = list(NATURAL_ORDER) + list(STRESS_ORDER)
    return {
        "natural": natural,
        "stress": stress,
        "full": full,
        "manual_review_queue": review_queue,
        "seed_usage": dict(sorted(allocator.usage.items())),
        "query_uniqueness": {
            "full_query_count": len(full),
            "full_normalized_unique_count": len(set(normalized)),
            "exact_duplicate_count": duplicate_count,
        },
        "duplicate_retry_by_category": {
            category: duplicate_retries[category] for category in all_categories
        },
    }


def generate_files(
    seed_bank_path: Path = DEFAULT_SEED_BANK,
    output_dir: Path = BENCHMARK_120_DIR,
) -> Dict[str, Any]:
    seeds = load_jsonl(seed_bank_path)
    core_cases = load_jsonl(CORE_CASES_PATH)
    core_hash = sha256_file(CORE_CASES_PATH)
    built = build_benchmark_120(seeds, core_cases, core_sha256=core_hash)

    output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_dir / CASES_PATH.name, built["full"])
    write_jsonl(output_dir / NATURAL_PATH.name, built["natural"])
    write_jsonl(output_dir / STRESS_PATH.name, built["stress"])
    write_jsonl(output_dir / REVIEW_QUEUE_PATH.name, built["manual_review_queue"])
    (output_dir / CORE_HASH_PATH.name).write_text(core_hash + "\n", encoding="utf-8")

    report = {
        "schema": "safeplc.benchmark_120.generation_report.v1",
        "status": "COMPLETE",
        "random_seed": GENERATOR_SEED,
        "core_sha256": core_hash,
        "case_count": len(built["full"]),
        "layer_counts": LAYER_120_COUNTS,
        "natural_category_counts": dict(Counter(case["category"] for case in built["natural"])),
        "stress_category_counts": dict(Counter(case["category"] for case in built["stress"])),
        "manual_reviewed_true": sum(case.get("manual_reviewed") is True for case in built["full"]),
        "manual_reviewed_false": sum(case.get("manual_reviewed") is False for case in built["full"]),
        "near_duplicate_candidate_count": len(built["manual_review_queue"]),
        "seed_count": len(seeds),
        "max_cases_per_seed": max(built["seed_usage"].values(), default=0),
        "query_uniqueness": built["query_uniqueness"],
        "duplicate_retry_by_category": built["duplicate_retry_by_category"],
        "manual_review_status": "pending",
    }
    write_json(output_dir / REPORT_PATH.name, report)
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build deterministic SafePLC Benchmark-120 cases.")
    parser.add_argument("--seed-bank", default=str(DEFAULT_SEED_BANK))
    parser.add_argument("--output-dir", default=str(BENCHMARK_120_DIR))
    args = parser.parse_args(argv)
    try:
        report = generate_files(Path(args.seed_bank), Path(args.output_dir))
    except (FileNotFoundError, GenerationError, ValueError) as exc:
        print(f"Benchmark-120 generation blocked: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
