#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from safeplc_assist_box.config import SafePLCConfig
from safeplc_assist_box.tools.tool_registry import ToolRegistry


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe FULL retrieval without running the Agent system.")
    parser.add_argument("query")
    parser.add_argument("--top-k", type=int, default=6)
    parser.add_argument("--modalities", default="text,table,figure")
    args = parser.parse_args()
    registry = ToolRegistry(SafePLCConfig.from_env(mode="FULL"))
    evidence = registry.search_hybrid(
        args.query,
        modalities=[item.strip() for item in args.modalities.split(",") if item.strip()],
        top_k=max(1, args.top_k),
    )
    result = {
        "query": args.query,
        "backend_audit": registry.backend_audit,
        "warnings": registry.errors,
        "evidence": [
            {
                "evidence_id": item.evidence_id,
                "backend": item.retrieval_backend,
                "collection": item.collection_name,
                "score": item.normalized_score,
                "model_match": item.model_match_level,
                "model": item.module_model,
                "order_number": item.order_number,
                "page": item.page,
                "figure_number": item.figure_number,
                "image_path": item.image_path,
                "visual_evidence_status": item.metadata.get("visual_evidence_status", "missing"),
            }
            for item in evidence
        ],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
