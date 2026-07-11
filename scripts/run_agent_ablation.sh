#!/usr/bin/env bash
set -euo pipefail

export SAFEPLC_MODE="${SAFEPLC_MODE:-SAMPLE}"
python -m safeplc_assist_box.evaluation.run_agent_ablation --cases-dir benchmark/sample_regression --mode "$SAFEPLC_MODE" --output reports/runtime/agent_ablation_sample.json
