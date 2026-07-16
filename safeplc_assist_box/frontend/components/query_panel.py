"""Free query and curated-case controls."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import streamlit as st

from ..state import clear_query_session
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
                st.session_state.current_query = str(case.get("query") or "")
                st.session_state.query_context_text = str(case.get("context") or "")
                st.session_state.selected_demo_id = str(case.get("id") or "")
                st.session_state.selected_demo_snapshot = str(case.get("snapshot") or "")
                st.session_state.pipeline_result = None
                st.session_state.current_work_order = None
                st.session_state.query_status = "已载入案例"
                st.rerun()

    st.text_area(
        "查证问题",
        key="current_query",
        height=126,
        placeholder="输入设备型号、接口、参数或故障现象",
    )
    with st.expander("补充上下文", expanded=bool(st.session_state.query_context_text)):
        st.text_area(
            "现场现象、报警码或已知条件",
            key="query_context_text",
            height=86,
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
