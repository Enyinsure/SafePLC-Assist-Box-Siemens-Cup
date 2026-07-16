"""Primary three-column intelligent evidence workbench."""

from __future__ import annotations

from typing import Any, Mapping

import streamlit as st

from ..components.answer_panel import render_answer_panel
from ..components.common import empty_state
from ..components.device_panel import initialize_control_state, render_device_panel
from ..components.evidence_panel import render_evidence_pool
from ..components.judge_panel import render_judge_panel
from ..components.query_panel import render_query_panel
from ..components.status_header import render_status_header
from ..components.task_agent_panel import render_agent_flow, render_task_plan
from ..demo_loader import load_demo_cases
from ..pipeline_adapter import PipelineRequest, execute_pipeline
from ..report_loader import load_supported_device_catalog
from ..runtime import FrontendSettings, probe_runtime
from ..state import initialize_session_state, record_query


@st.cache_data(show_spinner=False)
def _cached_cases() -> list[dict[str, Any]]:
    return load_demo_cases()


@st.cache_data(show_spinner=False)
def _cached_catalog() -> dict[str, list[str]]:
    return load_supported_device_catalog()


def render() -> None:
    initialize_session_state(st.session_state)
    settings = FrontendSettings.from_env()
    result = st.session_state.get("pipeline_result")
    response_runtime = result.get("runtime", {}) if isinstance(result, Mapping) else {}
    runtime = probe_runtime(settings, response_runtime)
    initialize_control_state(runtime)

    device_context = (
        result.get("device_context", {})
        if isinstance(result, Mapping)
        else st.session_state.get("device_context", {})
    )
    render_status_header(runtime, device_context, st.session_state.query_status)

    left_col, center_col, right_col = st.columns([1.0, 2.1, 1.35], gap="medium")
    with left_col:
        controls = render_device_panel(_cached_catalog(), runtime, result)
        st.session_state.device_context = controls["device_context"]
        _render_session_history()

    with center_col:
        submitted = render_query_panel(_cached_cases())
        if submitted:
            _run_current_query(controls, settings)
        current_result = st.session_state.get("pipeline_result")
        if current_result:
            render_task_plan(current_result)
            render_agent_flow(current_result)
            render_answer_panel(current_result)
        else:
            empty_state("等待智能查证", "Supervisor 计划、动态 Agent 与证据闭合回答将在此显示。")
            _render_error()

    with right_col:
        current_result = st.session_state.get("pipeline_result")
        if current_result:
            render_evidence_pool(current_result)
            render_judge_panel(current_result)
        else:
            empty_state("Evidence Pool 未建立", "完成一次查询后显示证据、Judge 与 Verifier 检查。")


def _run_current_query(controls: Mapping[str, Any], settings: FrontendSettings) -> None:
    query = str(st.session_state.get("current_query") or "").strip()
    st.session_state.query_status = "查询中"
    context = _build_pipeline_context(
        str(st.session_state.get("query_context_text") or ""),
        controls.get("device_context", {}),
    )
    request = PipelineRequest(
        query=query,
        context=context,
        pipeline_mode=str(controls.get("pipeline_mode") or settings.pipeline_mode),
        routing_strategy=str(controls.get("routing_strategy") or "adaptive"),
        max_agents=int(controls.get("max_agents") or 4),
        feature_switches=dict(controls.get("feature_switches") or {}),
        device_context=dict(controls.get("device_context") or {}),
        selected_demo_id=str(st.session_state.get("selected_demo_id") or ""),
    )
    with st.spinner("Supervisor 正在执行检索与证据判定"):
        outcome = execute_pipeline(request, settings)
    if outcome.ok and outcome.normalized:
        st.session_state.pipeline_result = outcome.normalized
        st.session_state.raw_pipeline_response = outcome.raw
        st.session_state.current_work_order = None
        st.session_state.last_error = ""
        st.session_state.last_error_detail = outcome.debug_error
        st.session_state.query_status = "查证完成"
        record_query(st.session_state, outcome.normalized)
        st.rerun()
    st.session_state.pipeline_result = None
    st.session_state.last_error = outcome.user_error
    st.session_state.last_error_detail = outcome.debug_error
    st.session_state.query_status = "查证失败"
    st.rerun()


def _build_pipeline_context(user_context: str, device: Mapping[str, str]) -> str:
    context_parts = [user_context.strip()] if user_context.strip() else []
    selected = []
    if device.get("family") not in {None, "", "自动识别"}:
        selected.append(f"设备系列：{device['family']}")
    if device.get("model") not in {None, "", "自动识别"}:
        selected.append(f"设备型号：{device['model']}")
    if device.get("task_hint") not in {None, "", "自动识别"}:
        selected.append(f"用户任务类型提示：{device['task_hint']}")
    if device.get("document_scope"):
        selected.append(f"用户文档范围偏好：{device['document_scope']}")
    if device.get("answer_mode"):
        selected.append(f"用户回答模式偏好：{device['answer_mode']}")
    if selected:
        context_parts.append("；".join(selected))
    return "\n".join(context_parts)


def _render_session_history() -> None:
    history = list(st.session_state.get("query_history") or [])
    with st.expander(f"当前会话记录 · {len(history)}", expanded=False):
        if not history:
            st.write("尚无查询记录。")
        for item in history[:8]:
            st.markdown(
                f"**{item.get('verdict') or item.get('action') or 'UNKNOWN'}**  "
                f"{item.get('query') or ''}  \n"
                f"`{item.get('request_id') or ''}` · {item.get('generated_at') or '未记录时间'}"
            )


def _render_error() -> None:
    if st.session_state.get("last_error"):
        st.error(st.session_state.last_error)
    if st.session_state.get("last_error_detail"):
        with st.expander("开发调试信息", expanded=False):
            st.code(st.session_state.last_error_detail, language="text")
