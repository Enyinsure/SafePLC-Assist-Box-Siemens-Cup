"""Editable work-order projection and in-memory export formats."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Mapping


def build_editable_work_order(result: Mapping[str, Any]) -> Dict[str, Any]:
    """Project a normalized answer and backend work order into editable fields."""
    backend = dict(result.get("work_order") or {})
    runtime = dict(result.get("runtime") or {})
    device = dict(result.get("device_context") or {})
    answer = dict(result.get("answer") or {})
    evidence = list(result.get("evidence_pool") or [])
    raw_response = result.get("raw_response") if isinstance(result.get("raw_response"), Mapping) else {}
    request_id = str(result.get("request_id") or "UNKNOWN")
    generated_at = str(runtime.get("generated_at") or backend.get("generated_at") or "")
    digest = hashlib.sha256(request_id.encode("utf-8")).hexdigest()[:4].upper()
    date_token = "".join(character for character in generated_at[:10] if character.isdigit()) or "UNDATED"

    evidence_sources = []
    for item in evidence:
        if not isinstance(item, Mapping) or not item.get("accepted"):
            continue
        location = " / ".join(
            value
            for value in (
                f"第 {item.get('page')} 页" if item.get("page") is not None else "",
                str(item.get("figure_number") or ""),
            )
            if value
        )
        evidence_sources.append(
            " | ".join(
                value
                for value in (
                    str(item.get("display_id") or item.get("evidence_id") or ""),
                    str(item.get("document_name") or ""),
                    location,
                )
                if value
            )
        )

    suggested_checks = _strings(backend.get("suggested_checks"))
    if not suggested_checks:
        suggested_checks = [
            _with_refs(claim) for claim in answer.get("claims", []) if isinstance(claim, Mapping)
        ]
    safety_notes = [
        str(item.get("text") or "")
        for item in answer.get("safety_notes", [])
        if isinstance(item, Mapping) and item.get("text")
    ]
    risk_tip = str(backend.get("risk_tip") or "")
    raw_query_context = raw_response.get("query_context")
    query_context = dict(raw_query_context) if isinstance(raw_query_context, Mapping) else {}
    risk_level = str(
        raw_response.get("operation_risk_level")
        or backend.get("risk_level")
        or query_context.get("risk_level")
        or "未分级"
    )
    action = str(result.get("runtime", {}).get("action") or "")
    if risk_tip and risk_level not in {"SAFE", "LOW", "未分级"} and action == "REFUSE" and risk_tip not in safety_notes:
        safety_notes.append(risk_tip)

    return {
        "work_order_id": str(backend.get("work_order_id") or f"WO-{date_token}-{digest}"),
        "created_at": generated_at,
        "device_family": str(device.get("family") or "未识别"),
        "device_model": str(device.get("model") or "未识别"),
        "symptom": str(backend.get("user_query") or result.get("query") or ""),
        "task_type": "、".join(str(item) for item in result.get("task_type", []) if item),
        "possible_causes": _strings(backend.get("possible_causes")),
        "inspection_steps": suggested_checks,
        "treatment_advice": str(backend.get("final_answer") or answer.get("summary") or ""),
        "required_tools": _strings(backend.get("required_tools")),
        "risk_level": risk_level,
        "safety_notes": safety_notes,
        "evidence_sources": evidence_sources,
        "status": str(backend.get("status") or "待人工复核"),
        "technician": str(backend.get("technician") or ""),
        "notes": str(backend.get("notes") or ""),
        "manual_confirmation_items": _strings(backend.get("manual_confirmation_items")),
        "request_id": request_id,
    }


def work_order_to_json(work_order: Mapping[str, Any]) -> str:
    return json.dumps(dict(work_order), ensure_ascii=False, indent=2)


def work_order_to_markdown(work_order: Mapping[str, Any]) -> str:
    """Render an editable work order without losing its evidence references."""
    fields = [
        ("工单编号", "work_order_id"),
        ("创建时间", "created_at"),
        ("设备系列", "device_family"),
        ("设备型号", "device_model"),
        ("任务类型", "task_type"),
        ("风险等级", "risk_level"),
        ("处理状态", "status"),
        ("维护人员", "technician"),
    ]
    lines = [f"# SafePLC 维护工单 {work_order.get('work_order_id', '')}", ""]
    lines.extend(f"- **{label}：** {work_order.get(key, '')}" for label, key in fields)
    lines.extend(["", "## 故障现象或用户问题", "", str(work_order.get("symptom") or "未填写")])
    lines.extend(_markdown_list("可能原因", work_order.get("possible_causes")))
    lines.extend(_markdown_list("检查步骤", work_order.get("inspection_steps"), ordered=True))
    lines.extend(["", "## 处理建议", "", str(work_order.get("treatment_advice") or "未填写")])
    lines.extend(_markdown_list("所需工具", work_order.get("required_tools")))
    lines.extend(_markdown_list("安全注意事项", work_order.get("safety_notes")))
    lines.extend(_markdown_list("证据来源", work_order.get("evidence_sources")))
    lines.extend(_markdown_list("人工确认项", work_order.get("manual_confirmation_items")))
    lines.extend(["", "## 备注", "", str(work_order.get("notes") or "")])
    return "\n".join(lines).strip() + "\n"


def work_order_to_text(work_order: Mapping[str, Any]) -> str:
    markdown = work_order_to_markdown(work_order)
    return markdown.replace("# ", "").replace("## ", "").replace("**", "")


def supported_claim_counts(result: Mapping[str, Any]) -> Dict[str, int]:
    claims = [item for item in result.get("answer", {}).get("claims", []) if isinstance(item, Mapping)]
    return {
        "total": len(claims),
        "direct": sum(bool(item.get("direct_support")) for item in claims),
        "safety": len(result.get("answer", {}).get("safety_notes", [])),
    }


def _with_refs(claim: Mapping[str, Any]) -> str:
    refs = " ".join(f"[{item}]" for item in claim.get("evidence_ids", []) if item)
    return " ".join(part for part in (str(claim.get("text") or ""), refs) if part).strip()


def _strings(value: Any) -> List[str]:
    if value is None:
        return []
    values = value if isinstance(value, (list, tuple, set)) else [value]
    return [str(item) for item in values if str(item).strip()]


def _markdown_list(title: str, values: Any, ordered: bool = False) -> List[str]:
    items = _strings(values)
    lines = ["", f"## {title}", ""]
    if not items:
        return lines + ["未填写"]
    prefix = (lambda index: f"{index}. ") if ordered else (lambda _index: "- ")
    lines.extend(prefix(index) + item for index, item in enumerate(items, start=1))
    return lines
