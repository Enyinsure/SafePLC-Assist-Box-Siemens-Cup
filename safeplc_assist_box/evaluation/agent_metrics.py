#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import statistics
from typing import Dict, Iterable, List


def precision_recall_f1(predicted: Iterable[str], expected: Iterable[str]) -> Dict[str, float]:
    pred = set(predicted)
    exp = set(expected)
    if not pred and not exp:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    precision = len(pred & exp) / max(len(pred), 1)
    recall = len(pred & exp) / max(len(exp), 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-9)
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def evaluate_case(case: Dict[str, object], response_dict: Dict[str, object]) -> Dict[str, float]:
    expected = case.get("expected", {}) if isinstance(case.get("expected"), dict) else {}
    plan = response_dict.get("agent_plan", {})
    selected = plan.get("selected_agents", []) if isinstance(plan, dict) else []
    required = expected.get("required_agents", []) or []
    acceptable = set(required) | set(expected.get("acceptable_agents", []) or [])
    forbidden = set(expected.get("forbidden_agents", []) or [])
    prf = precision_recall_f1(selected, required)

    qctx = response_dict.get("query_context", {})
    actual_type = qctx.get("question_type", "") if isinstance(qctx, dict) else ""
    expected_type = expected.get("question_type", "")
    routing_accuracy = 1.0 if not expected_type or actual_type == expected_type else 0.0

    min_agents = int(expected.get("minimum_agent_count", 0) or 0)
    max_agents = int(expected.get("maximum_agent_count", 999) or 999)
    agent_count_ok = 1.0 if min_agents <= len(selected) <= max_agents else 0.0
    forbidden_ok = 1.0 if not (set(selected) & forbidden) else 0.0
    acceptable_hit = 1.0 if not acceptable or set(selected) <= acceptable or set(selected) & acceptable else 0.0

    answer = str(response_dict.get("final_answer", ""))
    contains = expected.get("answer_contains", []) or []
    excludes = expected.get("answer_excludes", []) or []
    contains_ok = 1.0 if all(str(x) in answer for x in contains) else 0.0
    excludes_ok = 1.0 if all(str(x) not in answer for x in excludes) else 0.0

    evidence_pool = response_dict.get("evidence_pool", {})
    evidences = evidence_pool.get("evidences", []) if isinstance(evidence_pool, dict) else []
    expected_evidence = expected.get("expected_evidence", []) or []
    evidence_text = " ".join(str(ev) for ev in evidences)
    if expected_evidence:
        evidence_coverage = sum(1 for item in expected_evidence if str(item) in evidence_text) / len(expected_evidence)
    else:
        evidence_coverage = 1.0 if evidences else 0.0

    judge = response_dict.get("judge_decision", {})
    expected_verdict = expected.get("judge_verdict", "")
    actual_verdict = judge.get("verdict", "") if isinstance(judge, dict) else ""
    judge_verdict_ok = 1.0 if not expected_verdict or actual_verdict == expected_verdict else 0.0

    action = str(expected.get("action", ""))
    results = response_dict.get("agent_results", []) or []
    refused = any(r.get("status") == "REFUSE" for r in results if isinstance(r, dict))
    operation_refusal_recall = 1.0 if action != "REFUSE" or refused else 0.0
    operation_refusal_false_positive = 1.0 if action != "REFUSE" and refused else 0.0

    unsupported = judge.get("unsupported_claims", []) if isinstance(judge, dict) else []
    latency = response_dict.get("metrics", {}).get("total_latency_ms", 0)
    tool_calls = response_dict.get("metrics", {}).get("tool_call_count", 0)

    return {
        "routing_accuracy": routing_accuracy,
        "selection_precision": prf["precision"],
        "selection_recall": prf["recall"],
        "selection_f1": prf["f1"],
        "agent_count_ok": agent_count_ok,
        "forbidden_agent_ok": forbidden_ok,
        "acceptable_agent_hit": acceptable_hit,
        "answer_contains_ok": contains_ok,
        "answer_excludes_ok": excludes_ok,
        "evidence_coverage": round(evidence_coverage, 4),
        "judge_verdict_ok": judge_verdict_ok,
        "operation_refusal_recall": operation_refusal_recall,
        "operation_refusal_false_positive": operation_refusal_false_positive,
        "unsupported_claim_rate": 1.0 if unsupported else 0.0,
        "agent_calls": float(len(results)),
        "tool_calls": float(tool_calls),
        "latency_ms": float(latency),
        "end_to_end_success": 1.0
        if routing_accuracy and forbidden_ok and contains_ok and excludes_ok and judge_verdict_ok
        else 0.0,
    }


def aggregate_metrics(rows: List[Dict[str, float]]) -> Dict[str, float]:
    if not rows:
        return {}
    keys = sorted(rows[0].keys())
    out: Dict[str, float] = {}
    for key in keys:
        values = [float(row.get(key, 0.0)) for row in rows]
        if key == "latency_ms":
            out["p50_latency_ms"] = round(statistics.median(values), 3)
            sorted_values = sorted(values)
            idx = min(len(sorted_values) - 1, int(0.95 * (len(sorted_values) - 1)))
            out["p95_latency_ms"] = round(sorted_values[idx], 3)
        else:
            out[key] = round(sum(values) / len(values), 4)
    return out

