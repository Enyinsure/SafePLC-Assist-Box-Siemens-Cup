#!/usr/bin/env python3
"""Compatibility launcher for the original Streamlit command."""

from __future__ import annotations

import streamlit as st

from safeplc_assist_box.frontend.components.common import load_styles
from safeplc_assist_box.frontend.pages.workbench import render


def main() -> None:
    st.set_page_config(page_title="SafePLC-Assist Box", layout="wide")
    load_styles()
    render()


if __name__ == "__main__":
    main()
