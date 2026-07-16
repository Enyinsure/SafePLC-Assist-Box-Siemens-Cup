"""System capabilities and repository-backed benchmark page."""

from __future__ import annotations

from typing import Any, Dict, Mapping

import streamlit as st

from safeplc_assist_box.agents.orchestrator import AGENT_FACTORY

from ..components.common import empty_state, esc, section_heading
from ..components.status_header import render_status_header
from ..report_loader import load_report_bundle, load_showcase_cases, load_supported_device_catalog
from ..runtime import FrontendSettings, probe_runtime
from ..state import initialize_session_state


METRIC_LABELS = {
    "coverage": "问题覆盖率",
    "model_consistency_rate": "型号一致率",
    "grounded_claim_rate": "引用完整率",
    "figure_evidence_success_rate": "图示证据命中率",
    "cross_family_contamination_rate": "跨型号污染率",
    "average_agent_calls": "平均 Agent 调用",
    "average_tool_calls": "平均工具调用",
    "p95_latency_ms": "P95 响应耗时",
}


@st.cache_data(show_spinner=False)
def _reports() -> Dict[str, Any]:
    return load_report_bundle()


@st.cache_data(show_spinner=False)
def _cases() -> list[dict[str, Any]]:
    return load_showcase_cases()


@st.cache_data(show_spinner=False)
def _catalog() -> dict[str, list[str]]:
    return load_supported_device_catalog()


def render() -> None:
    initialize_session_state(st.session_state)
    result = st.session_state.get("pipeline_result")
    runtime = probe_runtime(
        FrontendSettings.from_env(),
        result.get("runtime", {}) if isinstance(result, Mapping) else {},
    )
    device = result.get("device_context", {}) if isinstance(result, Mapping) else st.session_state.device_context
    render_status_header(runtime, device, "系统审计")
    reports = _reports()

    section_heading("系统能力概览", "SYSTEM")
    catalog = _catalog()
    capability_cols = st.columns(4)
    capability_cols[0].metric("专业 Agent", len(AGENT_FACTORY))
    capability_cols[1].metric("已收录系列", len(catalog))
    capability_cols[2].metric("已收录型号", sum(len(items) for items in catalog.values()))
    capability_cols[3].metric("工单导出", "JSON / MD / TXT")
    table_rows = [
        {"能力": "Text Chroma", "当前状态": runtime.get("text_chroma"), "来源": "运行配置 / 后端审计"},
        {"能力": "Figure Chroma", "当前状态": runtime.get("figure_chroma"), "来源": "运行配置 / 后端审计"},
        {"能力": "Embedding", "当前状态": runtime.get("model"), "来源": "运行配置"},
        {"能力": "Agent Pool", "当前状态": "、".join(AGENT_FACTORY.keys()), "来源": "AGENT_FACTORY"},
        {"能力": "Judge / Verifier", "当前状态": "结构化检查可用", "来源": "统一 Orchestrator"},
        {"能力": "PDF 工单", "当前状态": "未启用", "来源": "当前 exporter 能力"},
    ]
    st.dataframe(table_rows, width="stretch", hide_index=True)
    if catalog:
        with st.expander("真实支持设备目录", expanded=False):
            st.json(catalog, expanded=True)

    section_heading("Benchmark 结果", "EVALUATION")
    benchmark = dict(reports.get("benchmark") or {})
    if benchmark:
        st.warning(
            f"当前展示 {benchmark.get('mode', 'UNKNOWN')} 回归报告，共 {benchmark.get('case_count', 0)} 个案例；"
            "该结果不代表服务器 FULL 工业知识库准确率。"
        )
        metrics = dict(benchmark.get("metrics") or {})
        visible = [(key, metrics[key]) for key in METRIC_LABELS if key in metrics]
        for offset in range(0, len(visible), 4):
            cols = st.columns(4)
            for col, (key, value) in zip(cols, visible[offset : offset + 4]):
                col.metric(METRIC_LABELS[key], _format_metric(key, value))
        with st.expander("完整 SAMPLE 指标", expanded=False):
            st.json(metrics, expanded=False)
    else:
        empty_state("暂无真实 Benchmark 报告", "reports/agent_benchmark_sample.json 未读取成功。")

    ablation = dict(reports.get("ablation") or {})
    methods = list(ablation.get("methods") or [])
    if methods:
        section_heading("消融对比", "ABLATION")
        rows = []
        for item in methods:
            metrics = dict(item.get("metrics") or {})
            rows.append(
                {
                    "方法": item.get("method"),
                    "证据覆盖率": metrics.get("evidence_coverage"),
                    "选择精度": metrics.get("agent_selection_precision"),
                    "Verifier 通过率": metrics.get("verifier_pass_rate"),
                    "平均 Agent 调用": metrics.get("average_agent_calls"),
                }
            )
        st.dataframe(rows, width="stretch", hide_index=True)
        st.bar_chart(rows, x="方法", y=["证据覆盖率", "选择精度", "Verifier 通过率"])

    figure_report = dict(reports.get("figure_coverage") or {})
    if figure_report:
        section_heading("图示资产审计", "FIGURE")
        full_available = bool(figure_report.get("full_figure_chroma_available"))
        state = "FULL Figure Chroma 可用" if full_available else "本机未验证 FULL Figure Chroma"
        st.info(state)
        st.json(figure_report, expanded=False)

    section_heading("典型案例复现", "CASES")
    cases = _cases()
    if not cases:
        empty_state("暂无可载入案例")
    for row_start in range(0, len(cases), 3):
        cols = st.columns(3)
        for col, case in zip(cols, cases[row_start : row_start + 3]):
            with col:
                st.markdown(
                    f"""
                    <div class="case-card">
                      <span>{esc(case.get('category'))}</span>
                      <strong>{esc(case.get('title'))}</strong>
                      <p>{esc(case.get('query'))}</p>
                      <small>{esc(case.get('source'))} · {esc(case.get('expected_action'))}</small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button(
                    "载入工作台",
                    key=f"benchmark_case_{case.get('id')}",
                    icon=":material/input:",
                    width="stretch",
                ):
                    st.session_state.current_query = str(case.get("query") or "")
                    st.session_state.query_context_text = str(case.get("context") or "")
                    st.session_state.selected_demo_id = ""
                    st.session_state.pipeline_result = None
                    st.session_state.current_work_order = None
                    st.session_state.query_status = "已载入 Benchmark 案例"
                    st.switch_page("pages/1_workbench.py")

    if reports.get("errors"):
        with st.expander("报告读取警告", expanded=False):
            for error in reports["errors"]:
                st.warning(error)


def _format_metric(name: str, value: Any) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    if name.endswith("_ms"):
        return f"{numeric:.0f} ms"
    if name in {"average_agent_calls", "average_tool_calls"}:
        return f"{numeric:.2f}"
    return f"{numeric * 100:.1f}%"
