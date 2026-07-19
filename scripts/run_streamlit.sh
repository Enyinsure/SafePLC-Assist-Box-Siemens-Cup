#!/usr/bin/env bash
set -euo pipefail

export SAFEPLC_MODE="${SAFEPLC_MODE:-SAMPLE}"
exec python -m streamlit run app.py \
  --server.address 0.0.0.0 \
  --server.port 8502 \
  --server.headless true
