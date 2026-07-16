#!/usr/bin/env python3
"""SafePLC-Assist Box Streamlit entrypoint."""

from __future__ import annotations

import streamlit as st

from safeplc_assist_box.frontend.components.common import load_styles
from safeplc_assist_box.frontend.state import initialize_session_state


st.set_page_config(
    page_title="SafePLC-Assist Box",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={"About": "SafePLC-Assist Box · OFFLINE / READ-ONLY"},
)
initialize_session_state(st.session_state)
load_styles()

navigation = st.navigation(
    [
        st.Page(
            "pages/1_workbench.py",
            title="智能查证工作台",
            icon=":material/fact_check:",
            default=True,
        ),
        st.Page(
            "pages/2_work_order.py",
            title="维护工单",
            icon=":material/assignment:",
        ),
        st.Page(
            "pages/3_system_benchmark.py",
            title="评测与系统",
            icon=":material/monitoring:",
        ),
    ],
    expanded=True,
)
navigation.run()
