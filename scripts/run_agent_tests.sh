#!/usr/bin/env bash
set -euo pipefail

export SAFEPLC_MODE="${SAFEPLC_MODE:-SAMPLE}"
python -m pytest tests

