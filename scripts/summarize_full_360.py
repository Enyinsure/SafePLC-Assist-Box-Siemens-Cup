#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from benchmark.generation.common import write_json, write_jsonl


def _rate(passed: int, total: int) -> float:
    return round(passed / total, 6) if total else 0.0


def _percentile(values: Sequence[int], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    return float(ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower))


def _check(payload: Dict[str, Any], name: str) -> Optional[bool]:
    acceptance = payload.get("acceptance") if isinstance(payload.get("acceptance"), dict) else {}
    for item in acceptance.get("checks") or []:
        if isinstance(item, dict) and str(item.get("name") or "") == name:
            return bool(item.get("passed"))
    return None


def _checks_with_prefix(payload: Dict[str, Any], prefix: str) -> List[bool]:
    acceptance = payload.get("acceptance") if isinstance(payload.get("acceptance"), dict) else {}
    return [
        bool(item.get("passed"))
        for item in acceptance.get("checks") or []
        if isinstance(item, dict) and str(item.get("name") or "").startswith(prefix)
    ]


def _accuracy(values: Iterable[Optional[bool]]) -> float:
    concrete = [value for value in values if value is not None]
    return _rate(sum(value is True for value in concrete), len(concrete))


def load_case_payloads(run_dir: Path) -> List[Dict[str, Any]]:
    ignored = {
        "environment.json", "checkpoint.json", "summary.json", "latency_metrics.json",
        "manual_review_metrics.json", "failure_analysis.json",
    }
    payloads = []
    for path in sorted(run_dir.glob("*.json")):
        if path.name in ignored:
            continue
        value = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(value, dict) and isinstance(value.get("case"), dict):
            payloads.append(value)
    return payloads


def summarize(payloads: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    rows = []
    category_status: Dict[str, Counter[str]] = defaultdict(Counter)
    layer_status: Dict[str, Counter[str]] = defaultdict(Counter)
    supported_claim_count = 0
    unsupported_claim_count = 0
    latencies: List[int] = []
    agent_calls: List[int] = []
    failures: List[Dict[str, Any]] = []
    for payload in payloads:
        case = payload.get("case") or {}
        response = payload.get("response") or {}
        acceptance = payload.get("acceptance") or {}
        status = str(acceptance.get("status") or payload.get("status") or "ERROR")
        category = str(case.get("category") or "")
        layer = str(case.get("benchmark_layer") or "core")
        category_status[category][status] += 1
        layer_status[layer][status] += 1
        latency = int(response.get("total_latency_ms") or 0)
        calls = int(response.get("total_agent_calls") or 0)
        latencies.append(latency)
        agent_calls.append(calls)
        judge = response.get("judge_decision") if isinstance(response.get("judge_decision"), dict) else {}
        supported_claim_count += len(judge.get("supported_claims") or response.get("supported_claims") or [])
        unsupported_claim_count += len(judge.get("unsupported_claims") or response.get("unsupported_claims") or [])
        row = {
            "case_id": case.get("case_id", ""),
            "layer": layer,
            "category": category,
            "status": status,
            "action": response.get("action", ""),
            "verdict": response.get("verdict", ""),
            "latency_ms": latency,
            "agent_calls": calls,
        }
        rows.append(row)
        if status != "PASS":
            failures.append({
                **row,
                "failures": acceptance.get("failures") or [],
                "error": payload.get("error") or {},
            })

    total_claims = supported_claim_count + unsupported_claim_count
    action_values = [_check(payload, "action") for payload in payloads]
    verdict_values = [_check(payload, "verdict") for payload in payloads]
    routing_values = [
        _check(payload, "agent_routing")
        if str((payload.get("case") or {}).get("benchmark_layer") or "core") != "core"
        else _check(payload, "required_agents")
        for payload in payloads
    ]
    clarification_values = [
        all(values) for payload in payloads
        if (values := _checks_with_prefix(payload, "clarification_"))
    ]
    abstention_values = [
        _check(payload, "action")
        for payload in payloads if "ABSTAIN" in ((payload.get("case") or {}).get("expected_action") or [])
    ]
    refusal_values = [
        _check(payload, "action")
        for payload in payloads if "REFUSE" in ((payload.get("case") or {}).get("expected_action") or [])
    ]
    parameter_values = [
        value for payload in payloads
        if (payload.get("case") or {}).get("category") == "parameter"
        for value in _checks_with_prefix(payload, "structured_fact:parameter")
    ]
    figure_values = [
        value for payload in payloads
        if (payload.get("case") or {}).get("category") == "figure_location"
        for value in (
            _checks_with_prefix(payload, "figure_grounding")
            + _checks_with_prefix(payload, "structured_fact:figure_location")
        )
    ]
    evidence_page_values = [
        value for payload in payloads for value in _checks_with_prefix(payload, "evidence_pages")
    ]
    cross_model_values = [
        value for payload in payloads for value in _checks_with_prefix(payload, "cross_model_scope")
    ]
    no_evidence_values = [
        value for payload in payloads for value in _checks_with_prefix(payload, "final_evidence_empty")
    ]
    pass_count = sum(row["status"] == "PASS" for row in rows)
    error_count = sum(row["status"] == "ERROR" for row in rows)
    metrics = {
        "overall_pass_rate": _rate(pass_count, len(rows)),
        "core_30_pass_rate": _rate(layer_status["core"]["PASS"], sum(layer_status["core"].values())),
        "natural_240_pass_rate": _rate(layer_status["natural"]["PASS"], sum(layer_status["natural"].values())),
        "stress_90_pass_rate": _rate(layer_status["stress"]["PASS"], sum(layer_status["stress"].values())),
        "action_accuracy": _accuracy(action_values),
        "verdict_accuracy": _accuracy(verdict_values),
        "agent_routing_accuracy": _accuracy(routing_values),
        "clarification_accuracy": _accuracy(clarification_values),
        "abstention_accuracy": _accuracy(abstention_values),
        "safety_refusal_accuracy": _accuracy(refusal_values),
        "parameter_structured_fact_accuracy": _accuracy(parameter_values),
        "figure_grounding_accuracy": _accuracy(figure_values),
        "evidence_page_accuracy": _accuracy(evidence_page_values),
        "claim_level_supported_rate": _rate(supported_claim_count, total_claims),
        "unsupported_claim_rate": _rate(unsupported_claim_count, total_claims),
        "cross_model_contamination_rate": round(1.0 - _accuracy(cross_model_values), 6) if cross_model_values else 0.0,
        "no_evidence_fabrication_rate": round(1.0 - _accuracy(no_evidence_values), 6) if no_evidence_values else 0.0,
        "average_agent_calls": round(statistics.fmean(agent_calls), 6) if agent_calls else 0.0,
        "p50_latency_ms": round(_percentile(latencies, 0.50), 3),
        "p95_latency_ms": round(_percentile(latencies, 0.95), 3),
        "error_count": error_count,
    }
    category_metrics = [
        {
            "category": category,
            "case_count": sum(counts.values()),
            "pass_count": counts["PASS"],
            "pass_rate": _rate(counts["PASS"], sum(counts.values())),
            "fail_count": counts["FAIL"],
            "error_count": counts["ERROR"],
        }
        for category, counts in sorted(category_status.items())
    ]
    manual_review = Counter(
        str((payload.get("case") or {}).get("review_status") or "core") for payload in payloads
    )
    return {
        "summary": {
            "schema": "safeplc.full_360.metrics.v1",
            "case_count": len(rows),
            "status_counts": dict(Counter(row["status"] for row in rows)),
            **metrics,
        },
        "category_metrics": category_metrics,
        "failures": failures,
        "latency_metrics": {
            "count": len(latencies),
            "average_ms": round(statistics.fmean(latencies), 3) if latencies else 0.0,
            "p50_ms": metrics["p50_latency_ms"],
            "p95_ms": metrics["p95_latency_ms"],
            "maximum_ms": max(latencies, default=0),
        },
        "manual_review_metrics": {
            "case_count": len(rows),
            "review_status_counts": dict(manual_review),
            "manual_reviewed_true": sum((payload.get("case") or {}).get("manual_reviewed") is True for payload in payloads),
            "manual_reviewed_false": sum((payload.get("case") or {}).get("manual_reviewed") is False for payload in payloads),
        },
    }


def write_outputs(output_dir: Path, result: Dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", result["summary"])
    with (output_dir / "summary.tsv").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("metric\tvalue\n")
        for key, value in result["summary"].items():
            if not isinstance(value, (dict, list)):
                handle.write(f"{key}\t{value}\n")
    with (output_dir / "category_metrics.tsv").open("w", encoding="utf-8", newline="\n") as handle:
        columns = ("category", "case_count", "pass_count", "pass_rate", "fail_count", "error_count")
        handle.write("\t".join(columns) + "\n")
        for row in result["category_metrics"]:
            handle.write("\t".join(str(row[key]) for key in columns) + "\n")
    write_jsonl(output_dir / "failure_analysis.jsonl", result["failures"])
    write_json(output_dir / "latency_metrics.json", result["latency_metrics"])
    write_json(output_dir / "manual_review_metrics.json", result["manual_review_metrics"])


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize a FULL-360 runtime directory.")
    parser.add_argument("run_dir")
    parser.add_argument("--output-dir", default="")
    args = parser.parse_args(argv)
    run_dir = Path(args.run_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else run_dir
    try:
        payloads = load_case_payloads(run_dir)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FULL-360 summary failed: {exc}", file=sys.stderr)
        return 2
    if not payloads:
        print(f"No per-case JSON files found in {run_dir}", file=sys.stderr)
        return 2
    result = summarize(payloads)
    write_outputs(output_dir, result)
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
