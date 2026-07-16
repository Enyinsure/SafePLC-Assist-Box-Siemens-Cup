"""Shared Streamlit session-state defaults and history helpers."""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any, Dict


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
    state["selected_demo_id"] = ""
    state["selected_demo_snapshot"] = ""
    state["last_error"] = ""
    state["last_error_detail"] = ""
    state["query_status"] = "等待查询"


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
