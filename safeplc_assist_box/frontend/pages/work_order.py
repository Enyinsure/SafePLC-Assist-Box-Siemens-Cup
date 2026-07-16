"""Editable maintenance work-order page."""

from __future__ import annotations

from typing import Any, Mapping

import streamlit as st

from ..components.common import empty_state, section_heading
from ..components.status_header import render_status_header
from ..runtime import FrontendSettings, probe_runtime
from ..state import initialize_session_state
from ..work_orders import (
    build_editable_work_order,
    supported_claim_counts,
    work_order_to_json,
    work_order_to_markdown,
    work_order_to_text,
)


def render() -> None:
    initialize_session_state(st.session_state)
    result = st.session_state.get("pipeline_result")
    runtime = probe_runtime(
        FrontendSettings.from_env(),
        result.get("runtime", {}) if isinstance(result, Mapping) else {},
    )
    device = result.get("device_context", {}) if isinstance(result, Mapping) else st.session_state.device_context
    render_status_header(runtime, device, "工单编辑")
    section_heading("维护工单", "WORK ORDER")

    if not isinstance(result, Mapping):
        empty_state("当前没有可转换的查证结果", "请先在智能查证工作台完成一次查询。")
        return
    if not st.session_state.get("current_work_order"):
        st.session_state.current_work_order = build_editable_work_order(result)
    work_order = dict(st.session_state.current_work_order)
    counts = supported_claim_counts(result)
    st.markdown(
        f"""
        <div class="workorder-stats">
          <div><span>关键结论</span><strong>{counts['total']}</strong></div>
          <div><span>直接证据支持</span><strong>{counts['direct']}</strong></div>
          <div><span>安全提醒</span><strong>{counts['safety']}</strong></div>
          <div><span>证据来源</span><strong>{len(work_order.get('evidence_sources') or [])}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("从当前回答重新生成", icon=":material/refresh:"):
        st.session_state.current_work_order = build_editable_work_order(result)
        st.rerun()

    with st.form("work_order_form"):
        identity_cols = st.columns(3)
        with identity_cols[0]:
            work_order["work_order_id"] = st.text_input("工单编号", value=str(work_order.get("work_order_id") or ""))
            work_order["device_family"] = st.text_input("设备系列", value=str(work_order.get("device_family") or ""))
        with identity_cols[1]:
            work_order["created_at"] = st.text_input("创建时间", value=str(work_order.get("created_at") or ""))
            work_order["device_model"] = st.text_input("设备型号", value=str(work_order.get("device_model") or ""))
        with identity_cols[2]:
            work_order["status"] = st.selectbox(
                "当前处理状态",
                ["待人工复核", "待处理", "处理中", "已完成", "已关闭"],
                index=_status_index(str(work_order.get("status") or "待人工复核")),
            )
            work_order["technician"] = st.text_input("维护人员", value=str(work_order.get("technician") or ""))

        work_order["symptom"] = st.text_area("故障现象或用户问题", value=str(work_order.get("symptom") or ""), height=90)
        field_cols = st.columns(2)
        with field_cols[0]:
            work_order["task_type"] = st.text_input("任务类型", value=str(work_order.get("task_type") or ""))
            work_order["risk_level"] = st.text_input("风险等级", value=str(work_order.get("risk_level") or ""))
            work_order["possible_causes"] = _lines_widget("可能原因", work_order.get("possible_causes"), 110)
            work_order["required_tools"] = _lines_widget("所需工具", work_order.get("required_tools"), 90)
        with field_cols[1]:
            work_order["inspection_steps"] = _lines_widget("检查步骤", work_order.get("inspection_steps"), 150)
            work_order["safety_notes"] = _lines_widget("安全注意事项", work_order.get("safety_notes"), 110)
        work_order["treatment_advice"] = st.text_area("处理建议", value=str(work_order.get("treatment_advice") or ""), height=150)
        work_order["evidence_sources"] = _lines_widget("证据来源", work_order.get("evidence_sources"), 125)
        work_order["manual_confirmation_items"] = _lines_widget(
            "人工确认项", work_order.get("manual_confirmation_items"), 90
        )
        work_order["notes"] = st.text_area("备注", value=str(work_order.get("notes") or ""), height=90)
        saved = st.form_submit_button("保存当前工单", type="primary", icon=":material/save:")
    if saved:
        st.session_state.current_work_order = work_order
        st.success("工单已保存到当前 Session State。")

    section_heading("导出", "EXPORT")
    export_cols = st.columns(3)
    with export_cols[0]:
        st.download_button(
            "导出 JSON",
            work_order_to_json(st.session_state.current_work_order),
            file_name=f"{work_order.get('work_order_id') or 'safeplc_work_order'}.json",
            mime="application/json",
            icon=":material/download:",
            width="stretch",
        )
    with export_cols[1]:
        st.download_button(
            "导出 Markdown",
            work_order_to_markdown(st.session_state.current_work_order),
            file_name=f"{work_order.get('work_order_id') or 'safeplc_work_order'}.md",
            mime="text/markdown",
            icon=":material/download:",
            width="stretch",
        )
    with export_cols[2]:
        st.download_button(
            "导出 TXT",
            work_order_to_text(st.session_state.current_work_order),
            file_name=f"{work_order.get('work_order_id') or 'safeplc_work_order'}.txt",
            mime="text/plain",
            icon=":material/download:",
            width="stretch",
        )
    st.info("当前版本未启用 PDF 导出。")


def _lines_widget(label: str, value: Any, height: int) -> list[str]:
    values = value if isinstance(value, list) else ([value] if value else [])
    text = st.text_area(label, value="\n".join(str(item) for item in values), height=height)
    return [line.strip() for line in text.splitlines() if line.strip()]


def _status_index(status: str) -> int:
    options = ["待人工复核", "待处理", "处理中", "已完成", "已关闭"]
    return options.index(status) if status in options else 0
