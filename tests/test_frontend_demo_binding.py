from __future__ import annotations

import json
from pathlib import Path

from safeplc_assist_box.frontend.demo_loader import (
    demo_request_matches,
    load_demo_cases,
)
from safeplc_assist_box.frontend.pipeline_adapter import PipelineRequest
from safeplc_assist_box.frontend.result_normalizer import normalize_response
from safeplc_assist_box.frontend.state import (
    bind_demo_case,
    initialize_session_state,
    reconcile_demo_binding,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _request(case: dict, **changes) -> PipelineRequest:
    device = dict(case["device_context"])
    device.update(changes.pop("device_context", {}))
    values = {
        "query": case["query"],
        "context": case["context"],
        "user_context": case["context"],
        "device_context": device,
        "pipeline_mode": case["pipeline_mode"],
        "selected_demo_id": case["id"],
    }
    values.update(changes)
    return PipelineRequest(**values)


def test_demo_rejects_changed_model() -> None:
    case = load_demo_cases()[0]

    matches, reasons = demo_request_matches(
        case,
        _request(case, device_context={"model": "CPU 1518-4 PN/DP"}),
    )

    assert matches is False
    assert any("设备型号不匹配" in reason for reason in reasons)


def test_demo_rejects_changed_context() -> None:
    case = load_demo_cases()[0]

    matches, reasons = demo_request_matches(case, _request(case, user_context="新增现场信息"))

    assert matches is False
    assert "补充上下文与典型案例不匹配" in reasons


def test_demo_rejects_changed_pipeline_mode() -> None:
    case = load_demo_cases()[0]

    matches, reasons = demo_request_matches(case, _request(case, pipeline_mode="FULL"))

    assert matches is False
    assert any("流水线模式不匹配" in reason for reason in reasons)


def test_loaded_demo_binding_is_cleared_after_control_change() -> None:
    case = load_demo_cases()[0]
    state: dict = {"ui_answer_mode": "标准查证"}
    initialize_session_state(state)
    bind_demo_case(state, case)

    assert reconcile_demo_binding(state) is True
    state["ui_model"] = "CPU 1518-4 PN/DP"

    assert reconcile_demo_binding(state) is False
    assert state["selected_demo_id"] == ""
    assert state["pipeline_result"] is None


def test_demo_button_preserves_full_mode_and_does_not_bind_sample_snapshot() -> None:
    case = load_demo_cases()[0]
    state: dict = {"ui_answer_mode": "标准查证", "ui_pipeline_mode": "FULL"}
    initialize_session_state(state)

    bind_demo_case(state, case)

    assert state["ui_pipeline_mode"] == "FULL"
    assert state["selected_demo_preset_id"] == case["id"]
    assert state["selected_demo_id"] == ""
    assert state["selected_demo_snapshot"] == ""
    assert state["loaded_demo_fingerprint"] == {}
    assert state["current_query"] == case["query"]
    assert state["query_status"] == "已载入 FULL 查询预设"


def test_offline_snapshot_device_is_not_overridden_by_user_selection() -> None:
    case = load_demo_cases()[0]
    payload = json.loads((PROJECT_ROOT / case["snapshot"]).read_text(encoding="utf-8"))

    result = normalize_response(
        payload,
        device_context={"family": "S7-1500R/H", "model": "CPU 1518-4 PN/DP"},
        source="offline_demo_snapshot",
        frontend_mode="demo",
        declared_demo_context=case["device_context"],
    )

    assert result["device_context"]["model"] == "CPU 1517-3 PN/DP"
    assert result["device_context"]["family"] == "S7-1500"
    assert result["device_context"]["detection_source"] == "demo_fixed"
