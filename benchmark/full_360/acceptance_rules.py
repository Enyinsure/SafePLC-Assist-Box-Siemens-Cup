from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Sequence

from benchmark.full_core_30.acceptance_rules import evaluate_case as evaluate_core_case


def _nested(value: Dict[str, Any], *keys: str) -> Any:
    current: Any = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _evidences(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    pool = response.get("evidence_pool") if isinstance(response.get("evidence_pool"), dict) else {}
    values = pool.get("evidences") or response.get("evidence_items") or []
    return [item for item in values if isinstance(item, dict)]


def _final_evidences(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    judge = response.get("judge_decision") if isinstance(response.get("judge_decision"), dict) else {}
    final_ids = {str(value) for value in judge.get("final_evidence_ids") or []}
    return [item for item in _evidences(response) if str(item.get("evidence_id") or "") in final_ids]


def _structured_payloads(response: Dict[str, Any], final_evidences: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    payloads: List[Dict[str, Any]] = []
    for result in response.get("agent_results") or []:
        if not isinstance(result, dict):
            continue
        for claim in result.get("claims") or []:
            if isinstance(claim, dict):
                metadata = claim.get("metadata") if isinstance(claim.get("metadata"), dict) else {}
                payloads.append({**metadata, "claim_text": claim.get("claim_text", "")})
    for evidence in final_evidences:
        metadata = evidence.get("metadata") if isinstance(evidence.get("metadata"), dict) else {}
        payloads.append({**metadata, **{key: value for key, value in evidence.items() if key != "metadata"}})
    return payloads


def _contains_scalar(value: Any, expected: Any) -> bool:
    if isinstance(value, dict):
        return any(_contains_scalar(item, expected) for item in value.values())
    if isinstance(value, list):
        return any(_contains_scalar(item, expected) for item in value)
    if isinstance(expected, float) and isinstance(value, (int, float)):
        return abs(float(value) - expected) < 1e-9
    return value == expected


def _fact_supported(name: str, specification: Any, payloads: Sequence[Dict[str, Any]], response: Dict[str, Any]) -> bool:
    if name == "work_order" and isinstance(specification, dict):
        work_order = response.get("work_order") if isinstance(response.get("work_order"), dict) else {}
        return all(key in work_order for key in specification.get("required_keys") or [])
    if name == "parsed_target" and isinstance(specification, dict):
        slots = _nested(response, "query_context", "slots") or {}
        slot_names = {"interface": "interface_name", "order_number": "order_number"}
        for key, expected in specification.items():
            slot = slots.get(slot_names.get(key, key), {}) if isinstance(slots, dict) else {}
            actual = slot.get("value") if isinstance(slot, dict) else slot
            if str(actual or "") != str(expected):
                return False
        return True
    if isinstance(specification, dict) and "min_count" in specification:
        marker = name.rstrip("s")
        aliases = {
            "led_checks": {"led_checklist"},
            "emc_measures": {"emc_installation_measure"},
            "wiring_requirements": {"wiring_requirement"},
        }.get(name, set())
        matching = [
            payload for payload in payloads
            if str(payload.get("fact_type") or "").replace("_fact", "") in {name, marker, *aliases}
            or name in payload
            or marker in payload
        ]
        return len(matching) >= int(specification["min_count"])
    if not payloads:
        return False
    expected_scalars: List[Any] = []

    def collect(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key not in {"complete", "parameter_name"}:
                    collect(item)
        elif isinstance(value, list):
            for item in value:
                collect(item)
        elif value not in (None, ""):
            expected_scalars.append(value)

    collect(specification)
    return bool(expected_scalars) and all(any(_contains_scalar(payload, scalar) for payload in payloads) for scalar in expected_scalars)


def evaluate_case(case: Dict[str, Any], response: Dict[str, Any]) -> Dict[str, Any]:
    if str(case.get("benchmark_layer") or "core") == "core":
        return evaluate_core_case(case, response)

    checks: List[Dict[str, Any]] = []

    def check(name: str, passed: bool, actual: Any = None, expected: Any = None) -> None:
        checks.append({"name": name, "passed": bool(passed), "actual": actual, "expected": expected})

    judge = response.get("judge_decision") if isinstance(response.get("judge_decision"), dict) else {}
    action = str(response.get("action") or "")
    verdict = str(response.get("verdict") or judge.get("verdict") or "")
    answer = str(response.get("final_answer") or judge.get("final_answer") or "")
    selected_agents = list(response.get("selected_agents") or _nested(response, "agent_plan", "selected_agents") or [])
    final_ids = [str(value) for value in judge.get("final_evidence_ids") or []]
    final_evidences = _final_evidences(response)
    payloads = _structured_payloads(response, final_evidences)

    check("action", action in case["expected_action"], action, case["expected_action"])
    check("verdict", verdict in case["expected_verdict"], verdict, case["expected_verdict"])
    check(
        "agent_routing",
        set(case.get("expected_agents") or []).issubset(set(selected_agents)),
        selected_agents,
        case.get("expected_agents") or [],
    )
    if case.get("must_have_final_evidence"):
        check("final_evidence_required", bool(final_ids), final_ids, "non-empty")
    if case.get("must_have_empty_evidence"):
        check("final_evidence_empty", not final_ids, final_ids, [])

    actual_pages = {int(item["page"]) for item in final_evidences if str(item.get("page") or "").isdigit()}
    required_pages = set(case.get("required_evidence_pages") or [])
    if required_pages:
        check("evidence_pages", required_pages.issubset(actual_pages), sorted(actual_pages), sorted(required_pages))
    actual_modalities = {str(item.get("modality") or "") for item in final_evidences}
    required_modalities = set(case.get("required_evidence_modalities") or [])
    if required_modalities:
        check(
            "evidence_modalities",
            required_modalities.issubset(actual_modalities),
            sorted(actual_modalities),
            sorted(required_modalities),
        )
    actual_figures = {
        str(item.get("manual_figure_number") or item.get("figure_number") or item.get("figure_id") or "")
        for item in final_evidences
    }
    required_figures = set(case.get("required_figure_ids") or [])
    if required_figures:
        check("figure_grounding", required_figures.issubset(actual_figures), sorted(actual_figures), sorted(required_figures))

    required_terms = case.get("required_terms") or []
    forbidden_terms = case.get("forbidden_terms") or []
    if required_terms:
        check("required_terms", all(term in answer for term in required_terms), answer, required_terms)
    if forbidden_terms:
        check("forbidden_terms", all(term not in answer for term in forbidden_terms), answer, forbidden_terms)

    support_payload = json.dumps(
        {"final_evidences": final_evidences, "supported_claims": judge.get("supported_claims") or []},
        ensure_ascii=False,
    )
    forbidden_models = case.get("forbidden_models") or []
    if forbidden_models:
        check(
            "cross_model_scope",
            all(model not in support_payload for model in forbidden_models),
            support_payload[:1000],
            forbidden_models,
        )

    for fact_name, specification in (case.get("required_structured_facts") or {}).items():
        if fact_name == "must_not_be_supported":
            continue
        check(
            f"structured_fact:{fact_name}",
            _fact_supported(fact_name, specification, payloads, response),
            payloads[:5],
            specification,
        )
    if (case.get("required_structured_facts") or {}).get("must_not_be_supported"):
        parsed = (case.get("required_structured_facts") or {}).get("parsed_target") or {}
        check(
            "unsupported_target_not_claimed",
            all(str(value) not in support_payload for value in parsed.values()),
            support_payload[:1000],
            parsed,
        )

    scope = case.get("scope_conditions") or {}
    missing_slots = set(response.get("missing_slots") or _nested(response, "query_context", "missing_slots") or [])
    if action == "CLARIFY" and scope.get("required_missing_slots"):
        wanted = set(scope["required_missing_slots"])
        check("clarification_missing_slots", wanted.issubset(missing_slots), sorted(missing_slots), sorted(wanted))
    if action == "CLARIFY" and scope.get("required_missing_slots_any"):
        wanted = set(scope["required_missing_slots_any"])
        check("clarification_missing_slots_any", bool(wanted & missing_slots), sorted(missing_slots), sorted(wanted))

    failures = [item for item in checks if not item["passed"]]
    return {
        "case_id": case["case_id"],
        "passed": not failures,
        "status": "PASS" if not failures else "FAIL",
        "checks": checks,
        "failures": failures,
    }
