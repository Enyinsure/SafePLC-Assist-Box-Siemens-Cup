"""Device and real backend control panel."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping

import streamlit as st

from safeplc_assist_box.config import VALID_MODES, VALID_ROUTING_STRATEGIES

from .common import esc, section_heading


TASK_HINTS = ["自动识别", "参数查证", "接线要求", "图示定位", "故障诊断", "EMC 核验", "维护工单"]
DOCUMENT_SCOPES = ["当前型号手册", "当前系列手册", "全部资料"]
ANSWER_MODES = ["标准查证", "教学解释", "安全维护"]


def render_device_panel(
    catalog: Mapping[str, List[str]],
    runtime: Mapping[str, Any],
    result: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    section_heading("设备与任务", "CONTEXT")
    families = ["自动识别", *catalog.keys()]
    _ensure_option("ui_family", families, "自动识别")
    family = st.selectbox("PLC 系列", families, key="ui_family")

    models = ["自动识别", *catalog.get(family, [])] if family != "自动识别" else ["自动识别"]
    _ensure_option("ui_model", models, "自动识别")
    model = st.selectbox("具体型号", models, key="ui_model")
    task_hint = st.selectbox("查询类型", TASK_HINTS, key="ui_task_hint")
    document_scope = st.selectbox("文档范围", DOCUMENT_SCOPES, key="ui_document_scope")
    answer_mode = st.selectbox("回答模式", ANSWER_MODES, key="ui_answer_mode")

    with st.expander("高级流水线设置", expanded=False):
        pipeline_modes = sorted(VALID_MODES)
        default_mode = str(runtime.get("pipeline_mode") or "SAMPLE")
        _ensure_option("ui_pipeline_mode", pipeline_modes, default_mode)
        pipeline_mode = st.selectbox("后端证据模式", pipeline_modes, key="ui_pipeline_mode")
        strategies = sorted(VALID_ROUTING_STRATEGIES)
        _ensure_option("ui_routing_strategy", strategies, "adaptive")
        routing_strategy = st.selectbox("Supervisor 路由", strategies, key="ui_routing_strategy")
        max_agents = st.slider("最大 Agent 数", 1, 8, key="ui_max_agents")
        enable_figure = st.toggle("启用 Figure 后端", key="ui_enable_figure")
        enable_model_filter = st.toggle("严格型号过滤", key="ui_enable_model_filter")
        enable_judge = st.toggle("启用 Judge", key="ui_enable_judge")
        enable_verifier = st.toggle("启用 Verifier", key="ui_enable_verifier")
        enable_second_retrieval = st.toggle("启用二次检索", key="ui_enable_second_retrieval")
        enable_reranker = st.toggle("启用证据重排", key="ui_enable_reranker")

    blocked = int((result or {}).get("evidence_stats", {}).get("cross_model_blocked", 0))
    blocked_html = (
        f'<div class="context-alert">已拦截 {blocked} 条跨型号证据</div>' if blocked else ""
    )
    st.markdown(
        f"""
        <div class="context-summary">
          <span class="context-summary-title">当前设备上下文</span>
          <dl>
            <dt>系列</dt><dd>{esc(family)}</dd>
            <dt>型号</dt><dd>{esc(model)}</dd>
            <dt>文档范围</dt><dd>{esc(document_scope)}</dd>
            <dt>型号约束</dt><dd>{'严格' if enable_model_filter else '关闭'}</dd>
          </dl>
          {blocked_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
    return {
        "device_context": {
            "family": family,
            "model": model,
            "document_scope": document_scope,
            "answer_mode": answer_mode,
            "task_hint": task_hint,
            "detection_source": "user_selected" if model != "自动识别" else "auto_detected",
        },
        "pipeline_mode": pipeline_mode,
        "routing_strategy": routing_strategy,
        "max_agents": max_agents,
        "feature_switches": {
            "enable_figure_backend": enable_figure,
            "enable_model_filter": enable_model_filter,
            "enable_judge": enable_judge,
            "enable_verifier": enable_verifier,
            "enable_second_retrieval": enable_second_retrieval,
            "enable_evidence_reranker": enable_reranker,
        },
    }


def initialize_control_state(runtime: Mapping[str, Any]) -> None:
    defaults = {
        "ui_family": "自动识别",
        "ui_model": "自动识别",
        "ui_task_hint": "自动识别",
        "ui_document_scope": "当前型号手册",
        "ui_answer_mode": "标准查证",
        "ui_pipeline_mode": str(runtime.get("pipeline_mode") or "SAMPLE"),
        "ui_routing_strategy": "adaptive",
        "ui_max_agents": 4,
        "ui_enable_figure": True,
        "ui_enable_model_filter": True,
        "ui_enable_judge": True,
        "ui_enable_verifier": True,
        "ui_enable_second_retrieval": True,
        "ui_enable_reranker": True,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _ensure_option(key: str, options: List[str], fallback: str) -> None:
    if st.session_state.get(key) not in options:
        st.session_state[key] = fallback if fallback in options else options[0]
