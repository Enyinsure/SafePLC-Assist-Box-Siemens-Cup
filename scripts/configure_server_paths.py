#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import os
from pathlib import Path


def main() -> None:
    bundle = os.environ.get("SAFEPLC_PARTNER_BUNDLE", "")
    project = Path(__file__).resolve().parents[1]
    suggestions = {
        "SAFEPLC_MODE": os.environ.get("SAFEPLC_MODE", "SAMPLE"),
        "SAFEPLC_PARTNER_BUNDLE": bundle,
        "SAFEPLC_CHUNKS_JSONL": os.environ.get("SAFEPLC_CHUNKS_JSONL", ""),
        "SAFEPLC_PAGES_JSONL": os.environ.get("SAFEPLC_PAGES_JSONL", ""),
        "SAFEPLC_REPORT_DIR": os.environ.get("SAFEPLC_REPORT_DIR", str(project / "reports")),
        "SAFEPLC_ROUTING_STRATEGY": os.environ.get("SAFEPLC_ROUTING_STRATEGY", "adaptive"),
        "SAFEPLC_MAX_AGENTS": os.environ.get("SAFEPLC_MAX_AGENTS", "4"),
    }
    print(json.dumps(suggestions, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

