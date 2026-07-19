"""System capabilities and repository-backed benchmark page."""

from __future__ import annotations

import logging
from typing import Any, Dict, Mapping

import streamlit as st

from ..components.common import empty_state, esc, section_heading
from ..components.status_header import render_status_header
from ..demo_loader import get_demo_case
from ..hidden_demo_matcher import prevalidate_hidden_snapshots
from ..report_loader import load_report_bundle, load_showcase_cases, load_supported_device_catalog
from ..runtime import FrontendSettings, probe_runtime
from ..state import bind_demo_case, initialize_session_state, invalidate_query_inputs


LOGGER = logging.getLogger(__name__)

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


@st.cache_resource(show_spinner=False)
def _probe_production_modules() -> dict[str, Any]:
    """Probe production modules independently without claiming they executed."""
    probes: dict[str, Any] = {}
    try:
        from safeplc_assist_box.agents.orchestrator import run_agent_system

        probes["orchestrator"] = {
            "available": callable(run_agent_system),
            "detail": "run_agent_system 可导入",
        }
    except Exception as exc:
        LOGGER.exception("Unable to import the production orchestrator")
        probes["orchestrator"] = {"available": False, "detail": type(exc).__name__}
    try:
        from safeplc_assist_box.agents.orchestrator import AGENT_FACTORY

        probes["agent_pool"] = {
            "available": bool(AGENT_FACTORY),
            "count": len(AGENT_FACTORY),
            "names": list(AGENT_FACTORY),
            "detail": f"{len(AGENT_FACTORY)} 个专业 Agent 可导入",
        }
    except Exception as exc:
        LOGGER.exception("Unable to import the production Agent factory")
        probes["agent_pool"] = {
            "available": False,
            "count": 0,
            "names": [],
            "detail": type(exc).__name__,
        }
    try:
        from safeplc_assist_box.agents.judge_agent import JudgeAgent

        probes["judge"] = {
            "available": callable(JudgeAgent),
            "detail": "JudgeAgent 可导入",
        }
    except Exception as exc:
        LOGGER.exception("Unable to import JudgeAgent")
        probes["judge"] = {"available": False, "detail": type(exc).__name__}
    try:
        from safeplc_assist_box.evidence.answer_evidence_verifier import verify_answer_evidence

        probes["verifier"] = {
            "available": callable(verify_answer_evidence),
            "detail": "verify_answer_evidence 可导入",
        }
    except Exception as exc:
        LOGGER.exception("Unable to import the answer verifier")
        probes["verifier"] = {"available": False, "detail": type(exc).__name__}
    return probes


def render() -> None:
    initialize_session_state(st.session_state)
    result = st.session_state.get("pipeline_result")
    settings = FrontendSettings.from_env()
    runtime = probe_runtime(
        settings,
        result.get("runtime", {}) if isinstance(result, Mapping) else {},
        effective_pipeline_mode=str(
            st.session_state.get("ui_pipeline_mode") or settings.pipeline_mode
        ),
    )
    device = result.get("device_context", {}) if isinstance(result, Mapping) else st.session_state.device_context
    render_status_header(runtime, device, "系统审计")
    reports = _reports()

    section_heading("系统能力概览", "SYSTEM")
    catalog = _catalog()
    module_probes = _probe_production_modules()
    agent_probe = dict(module_probes.get("agent_pool") or {})
    query_states = _query_module_states(result)
    capability_cols = st.columns(4)
    capability_cols[0].metric("专业 Agent", int(agent_probe.get("count") or 0))
    capability_cols[1].metric("已收录系列", len(catalog))
    capability_cols[2].metric("已收录型号", sum(len(items) for items in catalog.values()))
    capability_cols[3].metric("工单导出", "JSON / MD / TXT")
    table_rows = [
        {"能力": "Text Chroma", "当前状态": runtime.get("text_chroma"), "来源": "运行配置 / 后端审计"},
        {"能力": "Figure Chroma", "当前状态": runtime.get("figure_chroma"), "来源": "运行配置 / 后端审计"},
        {"能力": "Embedding", "当前状态": runtime.get("model"), "来源": "运行配置"},
        *_module_rows(module_probes, query_states),
        {"能力": "PDF 工单", "当前状态": "未启用", "来源": "当前 exporter 能力"},
    ]
    st.dataframe(table_rows, width="stretch", hide_index=True)
    failed_modules = [name for name, probe in module_probes.items() if not probe.get("available")]
    if failed_modules:
        st.warning("以下生产模块不可导入：" + "、".join(failed_modules) + "。详情已写入服务日志。")
    if catalog:
        with st.expander("真实支持设备目录", expanded=False):
            st.json(catalog, expanded=True)

    if settings.hidden_demo_enabled:
        package = prevalidate_hidden_snapshots()
        section_heading("离线验收包", "OFFLINE SAMPLE")
        package_cols = st.columns(3)
        package_cols[0].metric("离线验收快照", package.hidden_case_count)
        package_cols[1].metric("视觉资产", package.visual_asset_count)
        package_cols[2].metric("完整性检查", "通过" if package.ok else "失败")
        if not package.ok:
            st.error("离线视觉资产校验失败，已禁用验收快照加载。")

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
                availability_label = (
                    "离线快照可用"
                    if case.get("offline_snapshot_available")
                    else "需要 auto/online 模式"
                )
                st.markdown(
                    f"""
                    <div class="case-card">
                      <span>{esc(case.get('category'))}</span>
                      <strong>{esc(case.get('title'))}</strong>
                      <p>{esc(case.get('query'))}</p>
                      <small>{esc(case.get('source'))} · {esc(case.get('expected_action'))} · {esc(availability_label)}</small>
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
                    demo_case = get_demo_case(str(case.get("demo_id") or ""))
                    if demo_case:
                        bind_demo_case(st.session_state, demo_case)
                        st.switch_page("pages/1_workbench.py")
                    elif settings.frontend_mode == "demo":
                        st.warning("该 Benchmark 案例没有离线快照，请切换到 auto 或 online 模式运行。")
                    else:
                        invalidate_query_inputs(st.session_state)
                        st.session_state.current_query = str(case.get("query") or "")
                        st.session_state.query_context_text = str(case.get("context") or "")
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


def _module_rows(
    probes: Mapping[str, Any],
    query_states: Mapping[str, str],
) -> list[dict[str, str]]:
    labels = {
        "orchestrator": "统一 Orchestrator",
        "agent_pool": "Agent Pool",
        "judge": "Judge Agent",
        "verifier": "Evidence Verifier",
    }
    rows = []
    for key, label in labels.items():
        probe = dict(probes.get(key) or {})
        rows.append(
            {
                "能力": label,
                "当前状态": "模块可导入" if probe.get("available") else "模块不可用",
                "本次查询": str(query_states.get(key) or "未执行"),
                "来源": str(probe.get("detail") or "未返回探针明细"),
            }
        )
    return rows


def _query_module_states(result: Any) -> dict[str, str]:
    """Separate import capability from what the current request actually ran."""
    if not isinstance(result, Mapping):
        return {key: "未执行" for key in ("orchestrator", "agent_pool", "judge", "verifier")}
    runtime = dict(result.get("runtime") or {})
    source = str(runtime.get("source") or "")
    if source == "offline_demo_snapshot":
        return {key: "快照记录，非本次执行" for key in ("orchestrator", "agent_pool", "judge", "verifier")}
    if source != "online_pipeline":
        return {key: "未执行" for key in ("orchestrator", "agent_pool", "judge", "verifier")}
    raw = result.get("raw_response")
    raw_response = dict(raw) if isinstance(raw, Mapping) else {}
    features = dict(runtime.get("feature_switches") or {})
    selected_agents = list(result.get("selected_agents") or [])
    return {
        "orchestrator": "已执行",
        "agent_pool": f"已执行 {len(selected_agents)} 个 Agent" if selected_agents else "未选择专业 Agent",
        "judge": (
            "已关闭"
            if features.get("enable_judge") is False
            else "已执行"
            if isinstance(raw_response.get("judge_decision"), Mapping)
            else "未返回结果"
        ),
        "verifier": (
            "已关闭"
            if features.get("enable_verifier") is False
            else "已执行"
            if isinstance(raw_response.get("verifier"), Mapping)
            else "未返回结果"
        ),
    }
