"""Free query and curated-case controls."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import streamlit as st

from ..state import (
    bind_demo_case,
    clear_query_session,
    invalidate_query_inputs,
    reconcile_demo_binding,
)
from .common import section_heading


def render_query_panel(cases: Sequence[Mapping[str, Any]]) -> bool:
    section_heading("问题输入", "QUERY")
    case_columns = st.columns(3)
    for index, case in enumerate(cases[:6]):
        with case_columns[index % 3]:
            if st.button(
                str(case.get("title") or case.get("category") or "典型案例"),
                key=f"load_case_{case.get('id', index)}",
                icon=":material/bookmark:",
                width="stretch",
            ):
                bind_demo_case(st.session_state, case)
                st.rerun()

    st.text_area(
        "查证问题",
        key="current_query",
        height=126,
        placeholder="输入设备型号、接口、参数或故障现象",
        on_change=_invalidate_inputs,
    )
    with st.expander("补充上下文", expanded=bool(st.session_state.query_context_text)):
        st.text_area(
            "现场现象、报警码或已知条件",
            key="query_context_text",
            height=86,
            on_change=_invalidate_inputs,
        )

    run_col, clear_col = st.columns([3, 1])
    with run_col:
        submitted = st.button(
            "开始智能查证",
            type="primary",
            icon=":material/search:",
            width="stretch",
        )
    with clear_col:
        if st.button(
            "清空",
            icon=":material/restart_alt:",
            width="stretch",
        ):
            clear_query_session(st.session_state)
            st.rerun()
    return submitted


def _invalidate_inputs() -> None:
    # Streamlit can emit a delayed widget on_change after a demo button restores
    # the exact manifest value. Keep that valid binding; real edits fail the
    # fingerprint check and are invalidated by reconcile_demo_binding().
    if reconcile_demo_binding(st.session_state):
        return
    invalidate_query_inputs(st.session_state)
