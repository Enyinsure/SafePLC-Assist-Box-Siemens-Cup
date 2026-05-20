# SafePLC-Assist Box

SafePLC-Assist Box is a safety-aware industrial knowledge QA terminal prototype for Siemens Cup.

## Project Positioning

This project focuses on:

- Industrial manual knowledge retrieval
- Safety-aware question answering
- Evidence confidence estimation
- Answer-evidence consistency checking
- Streamlit-based product UI
- Physical terminal prototype with an external computing host

## Technical Boundary

This system does not:

- Connect to real PLC devices
- Connect to TIA Portal
- Execute PLC communication, download, write, start, stop, or control actions
- Collect real IT / OT network data
- Replace Siemens official manuals, site safety rules, or certified engineers

## Run

```bash
conda activate s7rag_ui
bash run_streamlit_safeplc_assist_box.sh
