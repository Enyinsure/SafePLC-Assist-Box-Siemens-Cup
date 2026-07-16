"""Load curated frontend cases and immutable offline response snapshots."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Mapping

from .paths import DATA_ROOT, resolve_project_path


DEMO_MANIFEST = DATA_ROOT / "demo_cases.json"
UNCONSTRAINED_DEMO_VALUES = {"", "自动识别"}
DEMO_DEVICE_FIELDS = ("family", "model", "document_scope", "task_hint")
DEMO_FIELD_LABELS = {
    "family": "设备系列",
    "model": "设备型号",
    "document_scope": "文档范围",
    "task_hint": "查询任务类型",
}


def load_demo_cases(path: Path = DEMO_MANIFEST) -> List[Dict[str, Any]]:
    """Return validated demo descriptors; malformed records are ignored."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(payload, list):
        return []
    cases: List[Dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict) or not str(item.get("query") or "").strip():
            continue
        record = dict(item)
        record.setdefault("id", f"case_{len(cases) + 1}")
        record.setdefault("title", record["id"])
        record.setdefault("category", "查证案例")
        record.setdefault("context", "")
        record.setdefault("device_context", {})
        record.setdefault("pipeline_mode", "SAMPLE")
        record.setdefault("snapshot", "")
        cases.append(record)
    return cases


def get_demo_case(case_id: str, path: Path = DEMO_MANIFEST) -> Dict[str, Any] | None:
    return next((case for case in load_demo_cases(path) if case.get("id") == case_id), None)


def make_demo_fingerprint(
    *,
    query: str,
    context: str,
    device_context: Mapping[str, Any],
    pipeline_mode: str,
) -> Dict[str, str]:
    """Build the immutable input signature that authorizes a demo snapshot."""
    return {
        "query": str(query or "").strip(),
        "context": str(context or "").strip(),
        "family": str(device_context.get("family") or "自动识别").strip(),
        "model": str(device_context.get("model") or "自动识别").strip(),
        "document_scope": str(device_context.get("document_scope") or "").strip(),
        "task_hint": str(device_context.get("task_hint") or "自动识别").strip(),
        "pipeline_mode": str(pipeline_mode or "").strip().upper(),
    }


def demo_case_fingerprint(case: Mapping[str, Any]) -> Dict[str, str]:
    """Return the declared input signature for one manifest case."""
    device_context = case.get("device_context")
    declared = device_context if isinstance(device_context, Mapping) else {}
    return make_demo_fingerprint(
        query=str(case.get("query") or ""),
        context=str(case.get("context") or ""),
        device_context=declared,
        pipeline_mode=str(case.get("pipeline_mode") or "SAMPLE"),
    )


def demo_request_matches(case: Mapping[str, Any], request: Any) -> tuple[bool, List[str]]:
    """Validate every snapshot-bound request field and explain mismatches."""
    request_user_context = getattr(request, "user_context", None)
    if request_user_context is None:
        request_user_context = getattr(request, "context", "")
    request_fingerprint = make_demo_fingerprint(
        query=str(getattr(request, "query", "") or ""),
        context=str(request_user_context or ""),
        device_context=getattr(request, "device_context", {}) or {},
        pipeline_mode=str(getattr(request, "pipeline_mode", "") or ""),
    )
    expected = demo_case_fingerprint(case)
    reasons: List[str] = []
    if request_fingerprint["query"] != expected["query"]:
        reasons.append("问题文本与典型案例不匹配")
    if request_fingerprint["context"] != expected["context"]:
        reasons.append("补充上下文与典型案例不匹配")
    for field in DEMO_DEVICE_FIELDS:
        expected_value = expected[field]
        if expected_value in UNCONSTRAINED_DEMO_VALUES:
            continue
        actual_value = request_fingerprint[field]
        if actual_value != expected_value:
            reasons.append(
                f"{DEMO_FIELD_LABELS[field]}不匹配：案例为 {expected_value}，当前选择为 {actual_value or '未设置'}"
            )
    if request_fingerprint["pipeline_mode"] != expected["pipeline_mode"]:
        reasons.append(
            "流水线模式不匹配："
            f"案例为 {expected['pipeline_mode']}，当前选择为 {request_fingerprint['pipeline_mode'] or '未设置'}"
        )
    return not reasons, reasons


def load_demo_snapshot(case: Dict[str, Any]) -> Dict[str, Any]:
    """Read the raw pipeline snapshot declared by a selected demo case."""
    snapshot = resolve_project_path(str(case.get("snapshot") or ""))
    if not snapshot:
        raise FileNotFoundError("该典型案例没有可用的离线响应快照。")
    try:
        payload = json.loads(snapshot.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"离线快照不存在：{snapshot}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"离线快照 JSON 无法解析：{snapshot.name}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"离线快照必须是对象：{snapshot.name}")
    return payload
