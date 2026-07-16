"""Judge, Verifier and risk checks."""

from __future__ import annotations

from typing import Any, Mapping

import streamlit as st

from .common import badge, esc, section_heading, status_label


CHECK_LABELS = {
    "coverage": "问题覆盖",
    "model_consistency": "型号一致性",
    "numeric_unit": "数值与单位",
    "figure_support": "图示支撑",
    "citation_completeness": "引用完整性",
    "safety": "安全风险",
    "evidence_conflict": "证据冲突",
}


def render_judge_panel(result: Mapping[str, Any]) -> None:
    judge = dict(result.get("judge_result") or {})
    runtime = dict(result.get("runtime") or {})
    checks = dict(judge.get("checks") or {})
    closure = float(judge.get("closure_score") or 0.0)
    section_heading("Judge 与 Verifier", "VERIFY")
    st.markdown(
        f"""
        <div class="closure-panel">
          <div class="closure-head"><span>证据闭合度</span><strong>{closure * 100:.0f}%</strong></div>
          <div class="closure-track"><span style="width:{max(0, min(100, closure * 100)):.1f}%"></span></div>
          <small>基于下列可见检查项计算的前端展示指标</small>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for key, label in CHECK_LABELS.items():
        item = dict(checks.get(key) or {})
        status = str(item.get("status") or "not_checked")
        st.markdown(
            f"""
            <div class="judge-row">
              <div><strong>{esc(label)}</strong><span>{esc(item.get('detail') or '未返回检查明细')}</span></div>
              {badge(status, status_label(status))}
            </div>
            """,
            unsafe_allow_html=True,
        )

    verifier = dict(judge.get("verifier") or {})
    with st.expander("Verifier 明细", expanded=False):
        if not verifier:
            st.write("Verifier 未返回结构化结果。")
        else:
            verifier_rows = []
            for key in (
                "pass",
                "coverage_pass",
                "model_consistency_pass",
                "figure_requirement_pass",
                "conciseness_pass",
                "raw_ocr_dump_detected",
            ):
                if key in verifier:
                    verifier_rows.append({"检查": key, "结果": verifier[key]})
            st.dataframe(verifier_rows, width="stretch", hide_index=True)
            st.json(verifier, expanded=False)

    warnings = list(runtime.get("warnings") or [])
    if warnings:
        with st.expander(f"运行警告 · {len(warnings)}", expanded=True):
            for warning in warnings:
                st.warning(str(warning))
