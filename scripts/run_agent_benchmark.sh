#!/usr/bin/env bash
set -euo pipefail

export SAFEPLC_MODE="${SAFEPLC_MODE:-SAMPLE}"
python scripts/build_agent_benchmark_from_bundle.py --output-dir benchmark/sample_regression
python -m safeplc_assist_box.evaluation.run_agent_benchmark --cases-dir benchmark/sample_regression --mode "$SAFEPLC_MODE" --method full --output reports/runtime/agent_benchmark_sample.json
