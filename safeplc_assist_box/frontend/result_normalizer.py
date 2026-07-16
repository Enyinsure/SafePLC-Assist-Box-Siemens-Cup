"""Normalize production responses into one frontend-facing audit schema."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any, Dict, List, Mapping


FAILURE_STATUSES = {"ERROR", "FAILED", "TIMEOUT", "EXCEPTION"}
COMPLETED_STATUSES = {"ANSWERED", "PARTIAL", "REFUSE"}
WAITING_STATUSES = {"WAITING", "NEED_CLARIFICATION"}
SKIPPED_STATUSES = {"ABSTAIN", "NEED_MORE_EVIDENCE"}


def normalize_response(
    response: Any,
    device_context: Mapping[str, str] | None = None,
    source: str = "online_pipeline",
    frontend_mode: str = "auto",
    declared_demo_context: Mapping[str, str] | None = None,
) -> Dict[str, Any]:
    """Convert dataclass or JSON responses while retaining the untouched payload."""
    try:
        raw = _plain(response)
        if not isinstance(raw, dict):
            raise TypeError("The pipeline response is not an object.")
        return _normalize(
            raw,
            dict(device_context or {}),
            source,
            frontend_mode,
            dict(declared_demo_context or {}),
        )
    except Exception as exc:
        raw_fallback = _plain_or_repr(response)
        return {
            "request_id": "normalization_failed",
            "query": "",
            "device_context": dict(device_context or {}),
            "task_type": [],
            "task_plan": [],
            "selected_agents": [],
            "evidence_pool": [],
            "rejected_evidence": [],
            "evidence_stats": _empty_evidence_stats(),
            "answer": {
                "summary": "响应已返回，但当前前端无法完整解析。",
                "claims": [],
                "parameters": [],
                "safety_notes": [],
                "limitations": ["请在开发调试信息中检查原始响应。"],
                "raw_text": "",
                "evidence_ids": [],
                "status": "响应兼容性异常",
            },
            "judge_result": _empty_judge_result(),
            "work_order": {},
            "runtime": {
                "source": source,
                "frontend_mode": frontend_mode,
                "warnings": [f"结果归一化失败：{type(exc).__name__}"],
                "backend_audit": {},
            },
            "normalization": {
                "ok": False,
                "status": "failed",
                "error": repr(exc),
            },
            "compatibility_warnings": [repr(exc)],
            "raw_response": raw_fallback,
        }


def _normalize(
    raw: Dict[str, Any],
    selected_device: Dict[str, str],
    source: str,
    frontend_mode: str,
    declared_demo_context: Dict[str, str],
) -> Dict[str, Any]:
    query_context = _mapping(raw.get("query_context"))
    plan = _mapping(raw.get("agent_plan"))
    decision = _mapping(raw.get("judge_decision"))
    verifier = _mapping(raw.get("verifier"))
    metrics = _mapping(raw.get("metrics"))
    pool = _mapping(raw.get("evidence_pool"))
    work_order = _mapping(raw.get("work_order"))
    agent_results = [_mapping(item) for item in _items(raw.get("agent_results"))]
    evidences = [_mapping(item) for item in _items(pool.get("evidences") or raw.get("evidence_items"))]

    evidence_id_map = {
        str(evidence.get("evidence_id") or f"missing_{index}"): f"E{index}"
        for index, evidence in enumerate(evidences, start=1)
    }
    final_ids = [str(item) for item in _items(decision.get("final_evidence_ids"))]
    final_id_set = set(final_ids)
    accepted_claims = _accepted_claims(decision, agent_results)
    claim_links = _claim_links(accepted_claims)

    normalized_evidence = [
        _normalize_evidence(evidence, evidence_id_map, final_id_set, claim_links)
        for evidence in evidences
    ]
    rejected = _normalize_rejected(pool, decision, evidence_id_map)
    evidence_stats = _evidence_stats(normalized_evidence, rejected, pool)
    agents = _normalize_agents(plan, agent_results)
    task_plan = _normalize_tasks(query_context, plan, agent_results, decision)
    device = _device_context(
        selected_device,
        query_context,
        normalized_evidence,
        source,
        declared_demo_context,
    )
    answer = _normalize_answer(
        raw,
        query_context,
        decision,
        accepted_claims,
        evidence_id_map,
        final_ids,
        normalized_evidence,
        work_order,
    )
    judge = _normalize_judge(raw, query_context, decision, verifier, accepted_claims)

    generated_at = str(raw.get("generated_at") or work_order.get("generated_at") or "")
    request_seed = "|".join(
        [str(raw.get("query") or ""), generated_at, str(raw.get("mode") or "")]
    )
    request_id = "REQ-" + hashlib.sha256(request_seed.encode("utf-8")).hexdigest()[:10].upper()
    warnings = [str(item) for item in _items(raw.get("warnings")) if str(item).strip()]
    backend_audit = _mapping(
        metrics.get("retrieval_backend_audit")
        or pool.get("metadata", {}).get("retrieval_backend_audit")
    )

    return {
        "request_id": request_id,
        "query": str(raw.get("query") or query_context.get("original_query") or ""),
        "context": str(raw.get("context") or query_context.get("context") or ""),
        "device_context": device,
        "task_type": [str(raw.get("question_type") or query_context.get("question_type") or "UNKNOWN")],
        "task_plan": task_plan,
        "selected_agents": agents,
        "agent_execution": _normalize_agent_execution(plan),
        "evidence_pool": normalized_evidence,
        "rejected_evidence": rejected,
        "evidence_stats": evidence_stats,
        "answer": answer,
        "judge_result": judge,
        "work_order": work_order,
        "runtime": {
            "source": source,
            "frontend_mode": frontend_mode,
            "pipeline_mode": str(raw.get("mode") or ""),
            "backend_available": source == "online_pipeline",
            "total_elapsed_ms": _number(raw.get("total_latency_ms") or metrics.get("total_latency_ms")),
            "agent_calls": int(_number(raw.get("total_agent_calls") or metrics.get("total_agent_calls"))),
            "tool_calls": int(_number(raw.get("total_tool_calls") or metrics.get("tool_call_count"))),
            "action": str(raw.get("action") or ""),
            "generated_at": generated_at,
            "version": str(raw.get("version") or ""),
            "warnings": warnings,
            "backend_audit": backend_audit,
            "feature_switches": _mapping(metrics.get("feature_switches")),
            "routing_strategy": str(raw.get("routing_strategy") or metrics.get("routing_strategy") or ""),
        },
        "normalization": {"ok": True, "status": "success", "error": ""},
        "compatibility_warnings": [],
        "raw_response": raw,
    }


def _normalize_tasks(
    query_context: Dict[str, Any],
    plan: Dict[str, Any],
    results: List[Dict[str, Any]],
    decision: Dict[str, Any],
) -> List[Dict[str, Any]]:
    subquestions = [_mapping(item) for item in _items(query_context.get("subquestions"))]
    coverage = _mapping(decision.get("coverage"))
    result_by_agent = {str(item.get("agent_name")): item for item in results}
    assignments = _mapping(plan.get("task_assignments"))
    tasks: List[Dict[str, Any]] = []

    for index, subquestion in enumerate(subquestions, start=1):
        task_id = str(subquestion.get("subquestion_id") or f"T{index}")
        expected_agents = [str(item) for item in _items(subquestion.get("expected_agents"))]
        assigned = [name for name in expected_agents if name in result_by_agent]
        if not assigned:
            for agent_name, assignment_value in assignments.items():
                assignment = _mapping(assignment_value)
                if task_id in [str(item) for item in _items(assignment.get("subquestion_ids"))]:
                    assigned.append(str(agent_name))
        coverage_item = _mapping(coverage.get(task_id))
        statuses = [str(result_by_agent[name].get("status") or "").upper() for name in assigned]
        if bool(coverage_item.get("answered")):
            status = "completed"
        elif any(item in FAILURE_STATUSES for item in statuses):
            status = "failed"
        elif any(item in WAITING_STATUSES for item in statuses):
            status = "waiting"
        elif any(item in SKIPPED_STATUSES for item in statuses):
            status = "skipped"
        elif statuses and all(item in COMPLETED_STATUSES for item in statuses):
            status = "completed"
        elif bool(plan.get("need_clarification")):
            status = "waiting"
        else:
            status = "waiting"
        tasks.append(
            {
                "task_id": task_id,
                "title": str(subquestion.get("objective") or subquestion.get("text") or f"任务 {index}"),
                "description": str(subquestion.get("text") or ""),
                "status": status,
                "assigned_agents": list(dict.fromkeys(assigned or expected_agents)),
                "required_modalities": [str(item) for item in _items(subquestion.get("required_modalities"))],
                "supporting_evidence_ids": [str(item) for item in _items(coverage_item.get("supporting_evidence_ids"))],
            }
        )

    if tasks:
        return tasks
    for index, (agent_name, assignment_value) in enumerate(assignments.items(), start=1):
        assignment = _mapping(assignment_value)
        result = result_by_agent.get(str(agent_name), {})
        result_status = str(result.get("status") or "")
        tasks.append(
            {
                "task_id": str(assignment.get("task_id") or f"T{index}"),
                "title": str(assignment.get("objective") or assignment.get("role") or agent_name),
                "description": str(assignment.get("query") or ""),
                "status": _task_status(result_status),
                "assigned_agents": [str(agent_name)],
                "required_modalities": [str(item) for item in _items(assignment.get("required_evidence_types"))],
                "supporting_evidence_ids": [str(item) for item in _items(result.get("evidence_ids"))],
            }
        )
    return tasks


def _normalize_agents(plan: Dict[str, Any], results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    assignments = _mapping(plan.get("task_assignments"))
    result_by_agent = {str(item.get("agent_name")): item for item in results}
    ordered_names = [str(item) for item in _items(plan.get("execution_order") or plan.get("selected_agents"))]
    ordered_names.extend(str(item.get("agent_name")) for item in results)
    agents: List[Dict[str, Any]] = []
    for name in dict.fromkeys(item for item in ordered_names if item):
        result = result_by_agent.get(name, {})
        assignment = _mapping(assignments.get(name))
        observations = [_mapping(item) for item in _items(result.get("observations"))]
        result_metadata = _mapping(result.get("metadata"))
        tools = []
        for observation in observations:
            tools.extend(part.strip() for part in str(observation.get("tool_name") or "").split(",") if part.strip())
        tools.extend(str(item) for item in _items(result_metadata.get("available_tools")))
        raw_status = str(result.get("status") or "WAITING").upper()
        error = str(
            result.get("error")
            or result.get("error_message")
            or result_metadata.get("error")
            or result.get("abstain_reason")
            or ""
        )
        if not error and raw_status in {"ABSTAIN", "NEED_MORE_EVIDENCE", "NEED_CLARIFICATION"}:
            error = "；".join(str(item) for item in _items(result.get("missing_information")))
        agents.append(
            {
                "agent_id": name.lower().replace(" ", "_").replace("-", "_"),
                "name": name,
                "task": str(assignment.get("objective") or result_metadata.get("objective") or ""),
                "status": _agent_status(raw_status),
                "raw_status": raw_status,
                "tools": list(dict.fromkeys(tools)),
                "evidence_count": len(_items(result.get("evidence_ids"))),
                "evidence_ids": [str(item) for item in _items(result.get("evidence_ids"))],
                "elapsed_ms": int(_number(result.get("latency_ms"))),
                "confidence": str(result.get("confidence") or "NOT_AVAILABLE"),
                "conclusion": str(result.get("answer_fragment") or result.get("abstain_reason") or ""),
                "error": error or None,
                "observations": observations,
                "claims": [_mapping(item) for item in _items(result.get("claims"))],
            }
        )
    return agents


def _normalize_agent_execution(plan: Dict[str, Any]) -> Dict[str, Any]:
    """Preserve the Supervisor's real sequential/parallel execution contract."""
    execution_order = [str(item) for item in _items(plan.get("execution_order")) if str(item)]
    groups: List[List[str]] = []
    for raw_group in _items(plan.get("parallel_groups")):
        members = [str(item) for item in _items(raw_group) if str(item)]
        if members:
            groups.append(members)
    mode = str(plan.get("execution_mode") or "").lower()
    if not mode:
        mode = "single" if len(execution_order) <= 1 else "sequential"
    return {
        "mode": mode,
        "execution_order": execution_order,
        "parallel_groups": groups,
    }


def _normalize_evidence(
    evidence: Dict[str, Any],
    evidence_id_map: Dict[str, str],
    final_ids: set[str],
    claim_links: Dict[str, List[str]],
) -> Dict[str, Any]:
    raw_id = str(evidence.get("evidence_id") or "")
    metadata = _mapping(evidence.get("metadata"))
    score = max(
        _number(evidence.get("quality_score")),
        _number(evidence.get("normalized_score")),
        _number(evidence.get("retrieval_score")),
    )
    match_level = str(evidence.get("model_match_level") or evidence.get("metadata", {}).get("model_match_level") or "unknown")
    image_path = str(
        evidence.get("resolved_image_path")
        or evidence.get("image_path")
        or evidence.get("raw_image_path")
        or ""
    )
    if match_level == "cross_family":
        model_consistent: bool | None = False
    elif match_level == "unknown":
        model_consistent = None
    else:
        model_consistent = True
    safety_checked = evidence.get("safety_checked")
    if not isinstance(safety_checked, bool):
        safety_checked = metadata.get("safety_checked")
    if not isinstance(safety_checked, bool):
        safety_checked = None
    return {
        "evidence_id": raw_id,
        "display_id": evidence_id_map.get(raw_id, raw_id or "未编号"),
        "source_type": str(evidence.get("source_type") or evidence.get("modality") or "unknown"),
        "modality": str(evidence.get("modality") or "unknown"),
        "document_name": str(evidence.get("manual_title") or evidence.get("title") or evidence.get("source") or "未命名资料"),
        "document_id": str(evidence.get("document_id") or ""),
        "family": str(evidence.get("device_family") or ""),
        "model": str(evidence.get("module_model") or evidence.get("module") or ""),
        "order_number": str(evidence.get("order_number") or ""),
        "page": evidence.get("page"),
        "section": str(evidence.get("section") or ""),
        "figure_id": str(evidence.get("figure_id") or ""),
        "figure_number": str(evidence.get("manual_figure_number") or evidence.get("figure_number") or ""),
        "content": str(evidence.get("text") or evidence.get("compact_excerpt") or ""),
        "excerpt": str(evidence.get("compact_excerpt") or evidence.get("text") or ""),
        "image_path": image_path,
        "visual_status": str(evidence.get("visual_evidence_status") or "missing"),
        "retriever": str(evidence.get("retrieval_backend") or "unknown"),
        "collection": str(evidence.get("collection_name") or ""),
        "score": score,
        "confidence_level": _confidence_level(score),
        "supports_claims": claim_links.get(raw_id, [str(item) for item in _items(evidence.get("claim_links"))]),
        "model_match_level": match_level,
        "model_consistent": model_consistent,
        "safety_checked": safety_checked,
        "accepted": raw_id in final_ids,
        "direct_evidence": bool(evidence.get("direct_evidence")),
        "agents": [str(item) for item in _items(evidence.get("agent_names"))],
        "metadata": metadata,
    }


def _normalize_rejected(
    pool: Dict[str, Any],
    decision: Dict[str, Any],
    evidence_id_map: Dict[str, str],
) -> List[Dict[str, Any]]:
    metadata = _mapping(pool.get("metadata"))
    rejected = []
    for item in _items(metadata.get("rejected_evidence")):
        record = _mapping(item)
        raw_id = str(record.get("evidence_id") or "")
        rejected.append(
            {
                "evidence_id": raw_id,
                "display_id": evidence_id_map.get(raw_id, raw_id or "未编号"),
                "reason": str(record.get("reason") or "未记录原因"),
                "page": record.get("page"),
                "backend": str(record.get("backend") or ""),
                "model_match_level": str(record.get("model_match_level") or "unknown"),
            }
        )
    known = {item["evidence_id"] for item in rejected}
    model_consistency = _mapping(decision.get("model_consistency"))
    for raw_id in _items(model_consistency.get("rejected_evidence_ids")):
        value = str(raw_id)
        if value and value not in known:
            rejected.append(
                {
                    "evidence_id": value,
                    "display_id": evidence_id_map.get(value, value),
                    "reason": "型号一致性检查未通过",
                    "page": None,
                    "backend": "",
                    "model_match_level": "cross_family",
                }
            )
    return rejected


def _normalize_answer(
    raw: Dict[str, Any],
    query_context: Dict[str, Any],
    decision: Dict[str, Any],
    accepted_claims: List[Dict[str, Any]],
    evidence_id_map: Dict[str, str],
    final_ids: List[str],
    evidences: List[Dict[str, Any]],
    work_order: Dict[str, Any],
) -> Dict[str, Any]:
    raw_text = str(raw.get("final_answer") or decision.get("final_answer") or "")
    if not raw_text and bool(query_context.get("clarify_question")):
        raw_text = str(query_context.get("clarify_question"))
    claims = []
    for index, claim in enumerate(accepted_claims, start=1):
        claim_ids = [str(item) for item in _items(claim.get("evidence_ids"))]
        claims.append(
            {
                "claim_id": str(claim.get("claim_id") or f"claim_{index}"),
                "text": str(claim.get("claim_text") or ""),
                "type": str(claim.get("claim_type") or "claim"),
                "model_scope": str(claim.get("model_scope") or ""),
                "confidence": str(claim.get("confidence") or "NOT_AVAILABLE"),
                "evidence_ids": [evidence_id_map.get(item, item) for item in claim_ids],
                "raw_evidence_ids": claim_ids,
                "direct_support": bool(claim.get("direct_support")),
                "metadata": _mapping(claim.get("metadata")),
            }
        )
    if not claims and final_ids:
        display_ids = [evidence_id_map.get(item, item) for item in final_ids]
        for index, text in enumerate(_items(decision.get("supported_claims")), start=1):
            claims.append(
                {
                    "claim_id": f"supported_{index}",
                    "text": str(text),
                    "type": "claim",
                    "model_scope": "",
                    "confidence": str(decision.get("confidence") or "NOT_AVAILABLE"),
                    "evidence_ids": display_ids,
                    "raw_evidence_ids": final_ids,
                    "direct_support": bool(display_ids),
                    "metadata": {},
                }
            )
    parameters = [claim for claim in claims if claim["type"].lower() in {"parameter", "numeric", "technical_parameter"}]
    risk_level = str(raw.get("operation_risk_level") or query_context.get("risk_level") or "")
    safety_notes = []
    risk_tip = str(work_order.get("risk_tip") or query_context.get("risk_reason") or "")
    if risk_tip and (risk_level not in {"", "SAFE", "LOW"} or raw.get("action") == "REFUSE"):
        safety_notes.append({"text": risk_tip, "evidence_ids": []})
    limitations = [str(item) for item in _items(raw.get("warnings")) if str(item).strip()]
    missing_slots = [str(item) for item in _items(query_context.get("missing_slots"))]
    if missing_slots:
        limitations.append("缺少必要信息：" + "、".join(missing_slots))
    needs_figure = "figure" in [str(item).lower() for item in _items(query_context.get("required_modalities"))]
    if needs_figure and not any(item.get("image_path") for item in evidences):
        limitations.append("当前证据未包含可解析的手册图片；图示结论仅按现有证据状态展示。")
    verdict = str(raw.get("verdict") or decision.get("verdict") or "")
    return {
        "summary": raw_text or "当前没有可展示的最终回答。",
        "claims": claims,
        "steps": [],
        "parameters": parameters,
        "safety_notes": safety_notes,
        "limitations": list(dict.fromkeys(limitations)),
        "raw_text": raw_text,
        "evidence_ids": [evidence_id_map.get(item, item) for item in final_ids],
        "status": _answer_status(verdict, str(raw.get("action") or "")),
    }


def _normalize_judge(
    raw: Dict[str, Any],
    query_context: Dict[str, Any],
    decision: Dict[str, Any],
    verifier: Dict[str, Any],
    accepted_claims: List[Dict[str, Any]],
) -> Dict[str, Any]:
    checks: Dict[str, Dict[str, Any]] = {}
    coverage = _mapping(decision.get("coverage"))
    if coverage:
        answered = sum(bool(_mapping(value).get("answered")) for value in coverage.values())
        score = answered / max(1, len(coverage))
        checks["coverage"] = _check(
            "passed" if score == 1 else "warning",
            score,
            f"{answered}/{len(coverage)} 个子问题有 Judge 支持记录",
        )
    elif decision.get("need_clarification"):
        checks["coverage"] = _check("warning", 0.0, "需补充信息后才能覆盖问题")
    else:
        checks["coverage"] = _check("not_checked", None, "未返回子问题覆盖明细")

    model_consistency = _mapping(decision.get("model_consistency"))
    if "pass" in model_consistency:
        model_pass = bool(model_consistency.get("pass"))
        rejected = len(_items(model_consistency.get("rejected_evidence_ids")))
        checks["model_consistency"] = _check(
            "passed" if model_pass else "failed",
            1.0 if model_pass else 0.0,
            "未发现跨型号证据" if model_pass else f"拦截或拒绝 {rejected} 条型号不一致证据",
        )
    else:
        checks["model_consistency"] = _check("not_checked", None, "Judge 未返回型号一致性字段")

    question_type = str(raw.get("question_type") or query_context.get("question_type") or "").upper()
    numeric_mismatch = _items(verifier.get("numeric_mismatch_claim_ids"))
    if question_type == "PARAMETER" or any(str(item.get("claim_type") or "").lower() == "parameter" for item in accepted_claims):
        if numeric_mismatch:
            checks["numeric_unit"] = _check("failed", 0.0, f"{len(numeric_mismatch)} 条数值 claim 不一致")
        elif verifier:
            checks["numeric_unit"] = _check("passed", 1.0, "Verifier 未发现数值不一致")
        else:
            checks["numeric_unit"] = _check("not_checked", None, "Verifier 未返回数值检查")
    else:
        checks["numeric_unit"] = _check("not_checked", None, "当前任务不要求参数数值检查")

    requires_figure = "figure" in [str(item).lower() for item in _items(query_context.get("required_modalities"))]
    if requires_figure:
        figure_pass = verifier.get("figure_requirement_pass")
        if figure_pass is None:
            checks["figure_support"] = _check("not_checked", None, "Verifier 未返回图示检查")
        else:
            checks["figure_support"] = _check(
                "passed" if bool(figure_pass) else "warning",
                1.0 if bool(figure_pass) else 0.5,
                "图示要求具有证据关联" if bool(figure_pass) else "缺少完整图示支撑",
            )
    else:
        checks["figure_support"] = _check("not_checked", None, "当前任务未要求图示证据")

    claim_count = len(accepted_claims)
    cited_count = sum(bool(_items(item.get("evidence_ids"))) for item in accepted_claims)
    if claim_count:
        citation_score = cited_count / claim_count
        checks["citation_completeness"] = _check(
            "passed" if citation_score == 1 else "warning",
            citation_score,
            f"{cited_count}/{claim_count} 条 Judge 接受 claim 绑定证据",
        )
    elif str(decision.get("verdict") or "") in {"REFUSE", "NEED_CLARIFICATION", "NEED_MORE_EVIDENCE", "ABSTAIN"}:
        checks["citation_completeness"] = _check("not_checked", None, "当前动作不形成事实性结论")
    else:
        checks["citation_completeness"] = _check("warning", 0.0, "未返回可核对的结构化 claim")

    risk_level_value = raw.get("operation_risk_level") or query_context.get("risk_level")
    risk_decision_value = query_context.get("risk_decision")
    risk_level = str(risk_level_value or "未记录")
    risk_decision = str(risk_decision_value or "")
    if raw.get("action") == "REFUSE" or (risk_decision and risk_decision != "ALLOW"):
        checks["safety"] = _check("warning", 0.75, f"风险级别 {risk_level}，系统已限制操作建议")
    elif risk_level_value is not None or risk_decision_value is not None:
        checks["safety"] = _check("passed", 1.0, f"风险级别 {risk_level}，未触发危险操作边界")
    else:
        checks["safety"] = _check("not_checked", None, "未返回结构化安全检查字段")

    conflicts = _items(decision.get("conflicting_claims")) + _items(decision.get("conflict_groups"))
    checks["evidence_conflict"] = _check(
        "failed" if conflicts else "passed",
        0.0 if conflicts else 1.0,
        f"发现 {len(conflicts)} 个冲突" if conflicts else "未发现 Judge 证据冲突",
    )
    checked_scores = [float(item["score"]) for item in checks.values() if item.get("score") is not None]
    closure_score = sum(checked_scores) / len(checked_scores) if checked_scores else 0.0
    return {
        "verdict": str(decision.get("verdict") or raw.get("verdict") or "UNKNOWN"),
        "confidence": str(decision.get("confidence") or raw.get("confidence") or "NOT_AVAILABLE"),
        "decision_reason": str(decision.get("decision_reason") or ""),
        "checks": checks,
        "closure_score": round(closure_score, 4),
        "closure_score_source": "frontend_visible_checks",
        "final_status": _answer_status(str(decision.get("verdict") or ""), str(raw.get("action") or "")),
        "accepted_agents": [str(item) for item in _items(decision.get("accepted_agent_outputs"))],
        "rejected_agents": [str(item) for item in _items(decision.get("rejected_agent_outputs"))],
        "unsupported_claims": [str(item) for item in _items(decision.get("unsupported_claims"))],
        "conflicting_claims": [str(item) for item in _items(decision.get("conflicting_claims"))],
        "final_evidence_ids": [str(item) for item in _items(decision.get("final_evidence_ids"))],
        "verifier": verifier,
    }


def _device_context(
    selected: Dict[str, str],
    query_context: Dict[str, Any],
    evidences: List[Dict[str, Any]],
    source: str,
    declared_demo_context: Dict[str, str],
) -> Dict[str, str]:
    slots = _mapping(query_context.get("slots"))
    model_slot = _mapping(slots.get("module_model"))
    query_model = str(model_slot.get("value") or "")
    evidence_model = str(next((item.get("model") for item in evidences if item.get("model")), ""))
    evidence_family = str(next((item.get("family") for item in evidences if item.get("family")), ""))
    selected_model = str(selected.get("model") or "")
    selected_family = str(selected.get("family") or "")

    if source == "offline_demo_snapshot":
        declared_model = str(declared_demo_context.get("model") or "")
        declared_family = str(declared_demo_context.get("family") or "")
        model = _first_constrained(query_model, evidence_model, declared_model, selected_model)
        family = _first_constrained(evidence_family, declared_family, selected_family)
        detection_source = "demo_fixed"
    else:
        user_selected = selected_model not in {"", "自动识别"}
        model = selected_model if user_selected else query_model or evidence_model
        family = (
            selected_family
            if selected_family not in {"", "自动识别"}
            else evidence_family
        )
        if user_selected or selected_family not in {"", "自动识别"}:
            detection_source = "user_selected"
        elif query_model:
            detection_source = "query_auto_detected"
        elif evidence_model or evidence_family:
            detection_source = "evidence_inferred"
        else:
            detection_source = "unknown"
    return {
        "family": family or "未识别",
        "model": model or "未识别",
        "document_scope": str(selected.get("document_scope") or "全部资料"),
        "answer_mode": str(selected.get("answer_mode") or "标准查证"),
        "task_hint": str(selected.get("task_hint") or "自动识别"),
        "detection_source": detection_source,
    }


def _first_constrained(*values: str) -> str:
    return next((str(value) for value in values if str(value) not in {"", "自动识别"}), "")


def _evidence_stats(
    evidences: List[Dict[str, Any]],
    rejected: List[Dict[str, Any]],
    pool: Dict[str, Any],
) -> Dict[str, Any]:
    modality_counts: Dict[str, int] = {}
    consistent = 0
    checked = 0
    for item in evidences:
        modality = str(item.get("modality") or "unknown").lower()
        modality_counts[modality] = modality_counts.get(modality, 0) + 1
        if item.get("model_consistent") is not None:
            checked += 1
            consistent += int(bool(item.get("model_consistent")))
    return {
        "total": len(evidences),
        "accepted": sum(bool(item.get("accepted")) for item in evidences),
        "text": sum(modality_counts.get(key, 0) for key in ("text", "policy")),
        "figure": sum(modality_counts.get(key, 0) for key in ("figure", "visual")),
        "table": modality_counts.get("table", 0),
        "model_consistent": consistent,
        "model_checked": checked,
        "rejected": len(rejected),
        "cross_model_blocked": sum(
            item.get("model_match_level") == "cross_family" or "型号" in str(item.get("reason") or "")
            for item in rejected
        ),
        "backend_counts": _mapping(_mapping(pool.get("metadata")).get("backend_counts")),
    }


def _accepted_claims(decision: Dict[str, Any], results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    metadata = _mapping(decision.get("metadata"))
    final_ids = {
        str(item)
        for item in _items(decision.get("final_evidence_ids"))
        if str(item)
    }
    if not final_ids:
        return []
    accepted = []
    for item in _items(metadata.get("accepted_claims")):
        claim = _mapping(item)
        claim_ids = {str(value) for value in _items(claim.get("evidence_ids")) if str(value)}
        if claim.get("claim_text") and claim_ids.intersection(final_ids):
            accepted.append(claim)
    if accepted:
        return accepted
    accepted_agents = {
        str(item)
        for item in _items(decision.get("accepted_agent_outputs"))
        if str(item)
    }
    claims: List[Dict[str, Any]] = []
    for result in results:
        agent_name = str(result.get("agent_name") or "")
        if accepted_agents and agent_name not in accepted_agents:
            continue
        if str(result.get("status") or "").upper() not in {"ANSWERED", "PARTIAL"}:
            continue
        for item in _items(result.get("claims")):
            claim = _mapping(item)
            claim_ids = {str(value) for value in _items(claim.get("evidence_ids")) if str(value)}
            if claim_ids.intersection(final_ids):
                claims.append(claim)
    return claims


def _claim_links(claims: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    result: Dict[str, List[str]] = {}
    for claim in claims:
        claim_id = str(claim.get("claim_id") or claim.get("claim_text") or "")
        for evidence_id in _items(claim.get("evidence_ids")):
            result.setdefault(str(evidence_id), []).append(claim_id)
    return result


def _task_status(status: str) -> str:
    return {
        "ANSWERED": "completed",
        "PARTIAL": "completed",
        "REFUSE": "completed",
        "ABSTAIN": "skipped",
        "NEED_MORE_EVIDENCE": "skipped",
        "NEED_CLARIFICATION": "waiting",
        "WAITING": "waiting",
        "ERROR": "failed",
        "FAILED": "failed",
        "TIMEOUT": "failed",
        "EXCEPTION": "failed",
    }.get(str(status or "").upper(), "waiting")


def _agent_status(status: str) -> str:
    return {
        "ANSWERED": "completed",
        "PARTIAL": "warning",
        "REFUSE": "completed",
        "ABSTAIN": "skipped",
        "NEED_MORE_EVIDENCE": "skipped",
        "NEED_CLARIFICATION": "waiting",
        "WAITING": "waiting",
        "ERROR": "failed",
        "FAILED": "failed",
        "TIMEOUT": "failed",
        "EXCEPTION": "failed",
    }.get(str(status or "").upper(), "failed")


def _confidence_level(score: float) -> str:
    if score <= 0:
        return "unknown"
    if score >= 0.8:
        return "high"
    if score >= 0.55:
        return "medium"
    return "low"


def _answer_status(verdict: str, action: str) -> str:
    if action == "REFUSE" or verdict == "REFUSE":
        return "检测到安全风险，已限制操作建议"
    if verdict == "PASS":
        return "证据充分，可作为教学与维护查证参考"
    if verdict in {"PARTIAL", "REVIEW"}:
        return "证据部分缺失，建议人工复核"
    if verdict in {"CONFLICT", "FAIL"}:
        return "存在证据或型号冲突，不建议直接执行"
    if verdict == "NEED_CLARIFICATION":
        return "需要补充设备信息后继续查证"
    if verdict in {"NEED_MORE_EVIDENCE", "ABSTAIN"}:
        return "证据不足，当前不形成事实性结论"
    return "等待 Judge 判定"


def _check(status: str, score: float | None, detail: str) -> Dict[str, Any]:
    return {"status": status, "score": score, "detail": detail}


def _empty_judge_result() -> Dict[str, Any]:
    return {
        "verdict": "UNKNOWN",
        "confidence": "NOT_AVAILABLE",
        "decision_reason": "",
        "checks": {},
        "closure_score": 0.0,
        "closure_score_source": "frontend_visible_checks",
        "final_status": "响应兼容性异常",
        "verifier": {},
    }


def _empty_evidence_stats() -> Dict[str, Any]:
    return {
        "total": 0,
        "accepted": 0,
        "text": 0,
        "figure": 0,
        "table": 0,
        "model_consistent": 0,
        "model_checked": 0,
        "rejected": 0,
        "cross_model_blocked": 0,
        "backend_counts": {},
    }


def _plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _plain(value.to_dict())
    if is_dataclass(value):
        return _plain(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_plain(item) for item in value]
    return value


def _plain_or_repr(value: Any) -> Any:
    try:
        return _plain(value)
    except Exception:
        return repr(value)


def _mapping(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _items(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, (tuple, set)):
        return list(value)
    return [value]


def _number(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0
