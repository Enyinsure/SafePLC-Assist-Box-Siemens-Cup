#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


def export_work_order(work_order: Dict[str, object], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(work_order, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
