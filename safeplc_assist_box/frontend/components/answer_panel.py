"""Evidence-closed answer presentation."""

from __future__ import annotations

from typing import Any, Mapping

import streamlit as st

from ..work_orders import build_editable_work_order, work_order_to_json
from .common import badge, esc, section_heading


def render_answer_panel(result: Mapping[str, Any]) -> None:
    answer = dict(result.get("answer") or {})
    judge = dict(result.get("judge_result") or {})
    section_heading("证据闭合回答", "ANSWER")
    verdict = str(judge.get("verdict") or "UNKNOWN")
    st.markdown(
        f"""
        <div class="answer-status">
          <div><span>回答状态</span><strong>{esc(answer.get('status'))}</strong></div>
          {badge(verdict, verdict)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    answer_tab, claims_tab, boundary_tab = st.tabs(["核心回答", "结构化结论", "使用边界"])
    with answer_tab:
        st.markdown(str(answer.get("summary") or "当前没有可展示的最终回答。"))
        evidence_ids = list(answer.get("evidence_ids") or [])
        if evidence_ids:
            refs = "".join(f'<span class="evidence-ref">[{esc(item)}]</span>' for item in evidence_ids)
            st.markdown(f'<div class="answer-evidence-line"><span>Judge 最终证据</span>{refs}</div>', unsafe_allow_html=True)
    with claims_tab:
        claims = list(answer.get("claims") or [])
        if not claims:
            st.info("Judge 未返回可展示的结构化支持结论。")
        for claim in claims:
            refs = " ".join(f"[{item}]" for item in claim.get("evidence_ids", [])) or "[无绑定证据]"
            st.markdown(
                f"""
                <div class="claim-row">
                  <div><strong>{esc(claim.get('text'))}</strong><small>{esc(claim.get('model_scope'))}</small></div>
                  <span class="claim-refs">{esc(refs)}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
    with boundary_tab:
        safety_notes = list(answer.get("safety_notes") or [])
        limitations = list(answer.get("limitations") or [])
        if safety_notes:
            st.markdown("**安全注意事项**")
            for item in safety_notes:
                st.warning(str(item.get("text") or ""))
        if limitations:
            st.markdown("**证据与使用边界**")
            for item in limitations:
                st.markdown(f"- {item}")
        if not safety_notes and not limitations:
            st.info("未返回额外安全提醒或使用边界。")

    action_col, status_col = st.columns([1.2, 1])
    with action_col:
        if st.button(
            "生成或更新维护工单",
            key="build_work_order",
            icon=":material/assignment:",
            width="stretch",
        ):
            st.session_state.current_work_order = build_editable_work_order(result)
            st.success("维护工单已写入当前会话。")
    with status_col:
        if st.session_state.get("current_work_order"):
            current_work_order = st.session_state.current_work_order
            st.download_button(
                "下载工单 JSON",
                work_order_to_json(current_work_order),
                file_name=f"{current_work_order.get('work_order_id') or 'safeplc_work_order'}.json",
                mime="application/json",
                icon=":material/download:",
                width="stretch",
            )
