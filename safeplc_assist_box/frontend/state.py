"""Shared Streamlit session-state defaults and history helpers."""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any, Dict, Mapping

from .demo_loader import demo_case_fingerprint, make_demo_fingerprint


DEFAULT_STATE: Dict[str, Any] = {
    "current_query": "",
    "query_context_text": "",
    "device_context": {
        "family": "自动识别",
        "model": "自动识别",
        "document_scope": "当前型号手册",
        "answer_mode": "标准查证",
        "task_hint": "自动识别",
        "detection_source": "auto_detected",
    },
    "pipeline_result": None,
    "raw_pipeline_response": None,
    "current_work_order": None,
    "query_history": [],
    "selected_demo_id": "",
    "selected_demo_snapshot": "",
    "loaded_demo_fingerprint": {},
    "last_error": "",
    "last_error_detail": "",
    "query_status": "等待查询",
}


def initialize_session_state(state: MutableMapping[str, Any]) -> None:
    """Populate every cross-page key without overwriting an active session."""
    for key, value in DEFAULT_STATE.items():
        if key not in state:
            state[key] = value.copy() if isinstance(value, (dict, list)) else value


def clear_query_session(state: MutableMapping[str, Any]) -> None:
    """Clear transient query data while preserving controls and history."""
    state["current_query"] = ""
    state["query_context_text"] = ""
    state["pipeline_result"] = None
    state["raw_pipeline_response"] = None
    state["current_work_order"] = None
    clear_demo_binding(state)
    state["last_error"] = ""
    state["last_error_detail"] = ""
    state["query_status"] = "等待查询"


def clear_demo_binding(state: MutableMapping[str, Any]) -> None:
    """Detach the session from any immutable demo snapshot."""
    state["selected_demo_id"] = ""
    state["selected_demo_snapshot"] = ""
    state["loaded_demo_fingerprint"] = {}


def invalidate_query_inputs(state: MutableMapping[str, Any]) -> None:
    """Invalidate stale results and snapshots after any input/config change."""
    clear_demo_binding(state)
    state["pipeline_result"] = None
    state["raw_pipeline_response"] = None
    state["current_work_order"] = None
    state["last_error"] = ""
    state["last_error_detail"] = ""
    state["query_status"] = "输入已修改，等待查询"


def bind_demo_case(state: MutableMapping[str, Any], case: Mapping[str, Any]) -> None:
    """Load a manifest case and atomically bind all snapshot-constrained controls."""
    fingerprint = demo_case_fingerprint(case)
    state["current_query"] = fingerprint["query"]
    state["query_context_text"] = fingerprint["context"]
    state["ui_family"] = fingerprint["family"] or "自动识别"
    state["ui_model"] = fingerprint["model"] or "自动识别"
    state["ui_document_scope"] = fingerprint["document_scope"] or "全部资料"
    state["ui_task_hint"] = fingerprint["task_hint"] or "自动识别"
    state["ui_pipeline_mode"] = fingerprint["pipeline_mode"] or "SAMPLE"
    state["device_context"] = {
        "family": state["ui_family"],
        "model": state["ui_model"],
        "document_scope": state["ui_document_scope"],
        "answer_mode": str(state.get("ui_answer_mode") or "标准查证"),
        "task_hint": state["ui_task_hint"],
        "detection_source": "demo_fixed",
    }
    state["selected_demo_id"] = str(case.get("id") or "")
    state["selected_demo_snapshot"] = str(case.get("snapshot") or "")
    state["loaded_demo_fingerprint"] = fingerprint
    state["pipeline_result"] = None
    state["raw_pipeline_response"] = None
    state["current_work_order"] = None
    state["last_error"] = ""
    state["last_error_detail"] = ""
    state["query_status"] = "已载入离线案例"


def reconcile_demo_binding(state: MutableMapping[str, Any]) -> bool:
    """Drop a stale binding if widget state no longer matches its recorded signature."""
    if not state.get("selected_demo_id"):
        return False
    expected = state.get("loaded_demo_fingerprint")
    if not isinstance(expected, Mapping) or not expected:
        clear_demo_binding(state)
        return False
    current = make_demo_fingerprint(
        query=str(state.get("current_query") or ""),
        context=str(state.get("query_context_text") or ""),
        device_context={
            "family": state.get("ui_family"),
            "model": state.get("ui_model"),
            "document_scope": state.get("ui_document_scope"),
            "task_hint": state.get("ui_task_hint"),
        },
        pipeline_mode=str(state.get("ui_pipeline_mode") or ""),
    )
    if dict(expected) != current:
        invalidate_query_inputs(state)
        return False
    return True


def record_query(state: MutableMapping[str, Any], result: Dict[str, Any]) -> None:
    """Store a compact, bounded audit history for the current browser session."""
    history = list(state.get("query_history") or [])
    history.insert(
        0,
        {
            "request_id": result.get("request_id", ""),
            "query": result.get("query", ""),
            "action": result.get("runtime", {}).get("action", ""),
            "verdict": result.get("judge_result", {}).get("verdict", ""),
            "generated_at": result.get("runtime", {}).get("generated_at", ""),
            "source": result.get("runtime", {}).get("source", ""),
        },
    )
    state["query_history"] = history[:20]
