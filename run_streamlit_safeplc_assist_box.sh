#!/usr/bin/env bash
set -e
eval "$(conda shell.bash hook)"
conda activate s7rag_ui
streamlit run /home/scc/pb23061092/safeplc_assist_box/app_assist_box.py --server.port 8501 --server.address 0.0.0.0
