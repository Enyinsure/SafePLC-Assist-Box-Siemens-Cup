#!/usr/bin/env bash
set -euo pipefail

exec ./cloudflared tunnel \
  --url http://127.0.0.1:8502 \
  --protocol http2 \
  --no-autoupdate
