#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from benchmark.full_core_30.acceptance_rules import validate_case_definition
from benchmark.generation.build_full_360 import generated_case_quality_issues, _has_figure_location
from benchmark.generation.common import (
    CORE_CASES_PATH,
    FULL_360_DIR,
    LAYER_COUNTS,
    NATURAL_COUNTS,
    SCHEMA_VERSION,
    STRESS_COUNTS,
    forbidden_project_terms,
    load_jsonl,
    near_duplicate_candidates,
    normalize_query,
    sha256_file,
    write_json,
    write_jsonl,
)


DEFAULT_CASES_PATH = FULL_360_DIR / "full_360.jsonl"
DEFAULT_SEEDS_PATH = FULL_360_DIR / "evidence_seed_bank.jsonl"
DEFAULT_FROZEN_HASH_PATH = FULL_360_DIR / "frozen_core_30.sha256"
DEFAULT_REVIEW_QUEUE_PATH = FULL_360_DIR / "manual_review_queue.jsonl"
GENERATED_REQUIRED_FIELDS = {
    "schema_version", "case_id", "benchmark_layer", "category", "difficulty", "query", "origin",
    "parent_seed_id", "mutation_type", "mutation_fields", "expected_safe_behavior", "target_model",
    "target_order_number", "expected_action", "expected_verdict", "expected_agents",
    "required_evidence_modalities", "required_evidence_pages", "required_figure_ids", "required_terms",
    "forbidden_terms", "required_structured_facts", "forbidden_models", "scope_conditions",
    "must_have_final_evidence", "must_have_empty_evidence", "source_seed_ids", "source_verified",
    "manual_reviewed", "review_status", "trigger_condition",
}
ALLOWED_ACTIONS = {"ANSWER", "CLARIFY", "ABSTAIN", "REFUSE"}
ALLOWED_VERDICTS = {
    "PASS", "PARTIAL", "NEED_CLARIFICATION", "NEED_MORE_EVIDENCE", "ABSTAIN", "REFUSE", "CONFLICT",
}


def _error(errors: List[Dict[str, Any]], code: str, case_id: str = "", detail: Any = None) -> None:
    value: Dict[str, Any] = {"code": code}
    if case_id:
        value["case_id"] = case_id
    if detail not in (None, ""):
        value["detail"] = detail
    errors.append(value)


def validate_generated_case_schema(case: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    missing = sorted(GENERATED_REQUIRED_FIELDS - set(case))
    errors.extend(f"missing:{field}" for field in missing)
    case_id = str(case.get("case_id") or "")
    if not re.fullmatch(r"(?:natural|stress)_[a-z0-9_]+_[0-9]{4}", case_id):
        errors.append("invalid:case_id")
    if case.get("schema_version") != SCHEMA_VERSION:
        errors.append("invalid:schema_version")
    if case.get("benchmark_layer") not in {"natural", "stress"}:
        errors.append("invalid:benchmark_layer")
    if case.get("difficulty") not in {"easy", "medium", "hard"}:
        errors.append("invalid:difficulty")
    for key in (
        "expected_action", "expected_verdict", "expected_agents", "required_evidence_modalities",
        "required_evidence_pages", "required_figure_ids", "required_terms", "forbidden_terms",
        "forbidden_models", "source_seed_ids",
    ):
        if not isinstance(case.get(key), list):
            errors.append(f"invalid:{key}")
    if isinstance(case.get("expected_action"), list):
        if not case["expected_action"] or not set(case["expected_action"]).issubset(ALLOWED_ACTIONS):
            errors.append("invalid:expected_action")
    if isinstance(case.get("expected_verdict"), list):
        if not case["expected_verdict"] or not set(case["expected_verdict"]).issubset(ALLOWED_VERDICTS):
            errors.append("invalid:expected_verdict")
    if any(not isinstance(page, int) or page < 1 for page in case.get("required_evidence_pages") or []):
        errors.append("invalid:required_evidence_pages")
    if not isinstance(case.get("required_structured_facts"), dict):
        errors.append("invalid:required_structured_facts")
    if not isinstance(case.get("mutation_fields"), dict):
        errors.append("invalid:mutation_fields")
    if not isinstance(case.get("scope_conditions"), dict):
        errors.append("invalid:scope_conditions")
    for key in ("must_have_final_evidence", "must_have_empty_evidence", "source_verified", "manual_reviewed"):
        if not isinstance(case.get(key), bool):
            errors.append(f"invalid:{key}")
    if case.get("review_status") not in {"pending", "approved", "rejected", "needs_revision"}:
        errors.append("invalid:review_status")
    return list(dict.fromkeys(errors))


def validate_dataset(
    cases: Sequence[Dict[str, Any]],
    seeds: Sequence[Dict[str, Any]],
    core_cases: Sequence[Dict[str, Any]],
    *,
    require_exact_counts: bool = True,
) -> Dict[str, Any]:
    errors: List[Dict[str, Any]] = []
    layers = Counter(str(case.get("benchmark_layer") or "core") for case in cases)
    natural_categories = Counter(
        str(case.get("category") or "") for case in cases if case.get("benchmark_layer") == "natural"
    )
    stress_categories = Counter(
        str(case.get("category") or "") for case in cases if case.get("benchmark_layer") == "stress"
    )
    if require_exact_counts:
        if len(cases) != 360:
            _error(errors, "invalid_total_count", detail={"actual": len(cases), "expected": 360})
        for layer, expected in LAYER_COUNTS.items():
            if layers[layer] != expected:
                _error(errors, "invalid_layer_count", detail={"layer": layer, "actual": layers[layer], "expected": expected})
        if dict(natural_categories) != NATURAL_COUNTS:
            _error(errors, "invalid_natural_category_counts", detail=dict(natural_categories))
        if dict(stress_categories) != STRESS_COUNTS:
            _error(errors, "invalid_stress_category_counts", detail=dict(stress_categories))

    case_ids = [str(case.get("case_id") or "") for case in cases]
    duplicate_ids = sorted(item for item, count in Counter(case_ids).items() if not item or count > 1)
    if duplicate_ids:
        _error(errors, "duplicate_case_ids", detail=duplicate_ids)
    normalized_queries = [normalize_query(str(case.get("query") or "")) for case in cases]
    duplicate_queries = sorted(item for item, count in Counter(normalized_queries).items() if not item or count > 1)
    if duplicate_queries:
        _error(errors, "duplicate_normalized_queries", detail=duplicate_queries[:20])

    core_by_id = {str(case.get("case_id") or ""): case for case in core_cases}
    dataset_core = [case for case in cases if str(case.get("benchmark_layer") or "core") == "core"]
    if len(dataset_core) == len(core_cases):
        for case in dataset_core:
            case_id = str(case.get("case_id") or "")
            if case_id not in core_by_id or case != core_by_id[case_id]:
                _error(errors, "core_case_modified", case_id)
    else:
        _error(errors, "core_case_count_or_membership_changed")

    seed_by_id = {str(seed.get("seed_id") or ""): seed for seed in seeds}
    seed_usage: Counter[str] = Counter()
    for case in cases:
        case_id = str(case.get("case_id") or "")
        layer = str(case.get("benchmark_layer") or "core")
        if layer == "core":
            for issue in validate_case_definition(case):
                _error(errors, "invalid_core_schema", case_id, issue)
            continue
        for issue in validate_generated_case_schema(case):
            _error(errors, "invalid_generated_schema", case_id, issue)
        source_ids = [str(value) for value in case.get("source_seed_ids") or []]
        for seed_id in source_ids:
            seed_usage[seed_id] += 1
        if "ANSWER" in (case.get("expected_action") or []) and not source_ids:
            _error(errors, "answer_without_seed", case_id)
        if case.get("source_verified") is True:
            missing = [seed_id for seed_id in source_ids if seed_id not in seed_by_id]
            if missing:
                _error(errors, "verified_case_missing_seed", case_id, missing)
            unverified = [seed_id for seed_id in source_ids if seed_id in seed_by_id and seed_by_id[seed_id].get("source_verified") is not True]
            if unverified:
                _error(errors, "verified_case_uses_unverified_seed", case_id, unverified)
        source_seeds = [seed_by_id[seed_id] for seed_id in source_ids if seed_id in seed_by_id]
        quality_issues = generated_case_quality_issues(case, source_seeds)
        if quality_issues:
            _error(errors, "generated_query_quality_failed", case_id, quality_issues)
        verified_pages = {
            int(seed_by_id[seed_id].get("page") or 0)
            for seed_id in source_ids if seed_id in seed_by_id and seed_by_id[seed_id].get("source_verified") is True
        }
        invalid_pages = [page for page in case.get("required_evidence_pages") or [] if page not in verified_pages]
        if invalid_pages:
            _error(errors, "unverified_required_page", case_id, invalid_pages)
        if case.get("manual_reviewed") is True and case.get("review_status") == "pending":
            _error(errors, "automatic_manual_review_claim", case_id)
        if case.get("origin") == "controlled_mutation":
            if not case.get("parent_seed_id") or not case.get("mutation_type") or not case.get("expected_safe_behavior"):
                _error(errors, "mutation_audit_fields_missing", case_id)
        if layer == "stress" and not case.get("parent_seed_id"):
            _error(errors, "stress_parent_seed_missing", case_id)
        if case.get("category") == "industrial_safety_refusal":
            scope = case.get("scope_conditions") or {}
            allowed_agents = set(scope.get("allowed_agents_any") or [])
            if (
                "REFUSE" not in (case.get("expected_action") or [])
                or "REFUSE" not in (case.get("expected_verdict") or [])
                or not {"Wiring Agent", "Safety Boundary Agent"}.issubset(allowed_agents)
                or case.get("must_have_empty_evidence") is True
            ):
                _error(errors, "invalid_safety_expectation", case_id)
        if case.get("category") in {"missing_slot_clarification", "topology_clarification"}:
            if "CLARIFY" not in (case.get("expected_action") or []):
                _error(errors, "missing_slot_must_clarify", case_id)
        if case.get("category") == "unsupported_entity":
            if "ABSTAIN" not in (case.get("expected_action") or []) or not case.get("trigger_condition"):
                _error(errors, "unsupported_entity_must_abstain", case_id)
        category = str(case.get("category") or "")
        if category == "cross_model_contamination":
            actions = set(case.get("expected_action") or [])
            comparison = (case.get("scope_conditions") or {}).get("cross_model_comparison")
            if (
                not {"ANSWER", "ABSTAIN"}.issubset(actions)
                or not isinstance(comparison, dict)
                or not comparison.get("target_model")
                or not comparison.get("distractor_model")
                or case.get("forbidden_models")
                or case.get("must_have_empty_evidence") is True
            ):
                _error(errors, "invalid_cross_model_comparison_expectation", case_id)

        non_figure_categories = {"parameter", "wiring", "emc", "compound_multi_agent"}
        if category in non_figure_categories and case.get("required_figure_ids"):
            _error(errors, "non_figure_case_inherits_figure_requirement", case_id)
        if (
            category == "troubleshooting"
            and case.get("required_figure_ids")
            and not re.search(r"图|figure", str(case.get("query") or ""), re.I)
        ):
            _error(errors, "troubleshooting_inherits_unrequested_figure", case_id)
        if category == "figure_location" and not case.get("required_figure_ids"):
            _error(errors, "figure_location_missing_figure_requirement", case_id)
        if category == "maintenance_work_order" and "Figure Agent" in (case.get("expected_agents") or []):
            if not source_seeds or not all(_has_figure_location(seed) for seed in source_seeds):
                _error(errors, "invalid_figure_maintenance_seed", case_id)
            if not case.get("required_figure_ids"):
                _error(errors, "figure_maintenance_missing_figure_requirement", case_id)

        parameter = (case.get("required_structured_facts") or {}).get("parameter")
        if isinstance(parameter, dict):
            forbidden_parameter_keys = {"complete", "condition", "parameter_name"} & set(parameter)
            null_parameter_keys = [key for key, value in parameter.items() if value in (None, "", [])]
            if forbidden_parameter_keys or null_parameter_keys:
                _error(errors, "invalid_parameter_constraints", case_id, {
                    "forbidden_keys": sorted(forbidden_parameter_keys),
                    "empty_keys": sorted(null_parameter_keys),
                })

    overused = {seed_id: count for seed_id, count in seed_usage.items() if count > 5}
    if overused:
        _error(errors, "seed_generation_cap_exceeded", detail=overused)

    serialized = json.dumps(cases, ensure_ascii=False).lower()
    contaminated = [term for term in forbidden_project_terms() if term.lower() in serialized]
    if contaminated:
        _error(errors, "unrelated_project_term_detected", detail=contaminated)

    review_queue = near_duplicate_candidates(cases)
    return {
        "schema": "safeplc.full_360.validation.v1",
        "valid": not errors,
        "case_count": len(cases),
        "layer_counts": dict(sorted(layers.items())),
        "natural_category_counts": dict(sorted(natural_categories.items())),
        "stress_category_counts": dict(sorted(stress_categories.items())),
        "manual_reviewed_true": sum(case.get("manual_reviewed") is True for case in cases),
        "manual_reviewed_false": sum(case.get("manual_reviewed") is False for case in cases),
        "near_duplicate_candidate_count": len(review_queue),
        "near_duplicate_candidates": review_queue,
        "errors": errors,
    }


def _frozen_hash(path: Path) -> str:
    values = path.read_text(encoding="utf-8").strip().split()
    if not values or not re.fullmatch(r"[0-9a-fA-F]{64}", values[0]):
        raise ValueError(f"Invalid hash manifest: {path}")
    return values[0].lower()


def validate_files(
    cases_path: Path = DEFAULT_CASES_PATH,
    seeds_path: Path = DEFAULT_SEEDS_PATH,
    frozen_hash_path: Path = DEFAULT_FROZEN_HASH_PATH,
    review_queue_path: Optional[Path] = DEFAULT_REVIEW_QUEUE_PATH,
) -> Dict[str, Any]:
    expected_hash = _frozen_hash(frozen_hash_path)
    current_hash = sha256_file(CORE_CASES_PATH)
    cases = load_jsonl(cases_path)
    seeds = load_jsonl(seeds_path)
    core_cases = load_jsonl(CORE_CASES_PATH)
    report = validate_dataset(cases, seeds, core_cases)
    report["core_sha256_expected"] = expected_hash
    report["core_sha256_actual"] = current_hash
    if expected_hash != current_hash:
        report["valid"] = False
        report["errors"].append({"code": "core_sha256_changed"})
    if review_queue_path is not None:
        write_jsonl(review_queue_path, report["near_duplicate_candidates"])
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the complete FULL-360 benchmark dataset.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES_PATH))
    parser.add_argument("--seeds", default=str(DEFAULT_SEEDS_PATH))
    parser.add_argument("--frozen-hash", default=str(DEFAULT_FROZEN_HASH_PATH))
    parser.add_argument("--review-queue", default=str(DEFAULT_REVIEW_QUEUE_PATH))
    parser.add_argument("--report", default="")
    args = parser.parse_args(argv)
    try:
        report = validate_files(
            Path(args.cases), Path(args.seeds), Path(args.frozen_hash), Path(args.review_queue),
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"FULL-360 validation blocked: {exc}", file=sys.stderr)
        return 2
    if args.report:
        write_json(Path(args.report), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
