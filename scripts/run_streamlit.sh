#!/usr/bin/env bash
set -euo pipefail

export SAFEPLC_MODE="${SAFEPLC_MODE:-SAMPLE}"
streamlit run safeplc_assist_box/app_assist_box.py
