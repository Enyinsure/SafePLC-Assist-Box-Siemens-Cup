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
from safeplc_assist_box.tools.chroma_figure_retriever import ChromaFigureRetriever
from safeplc_assist_box.tools.chroma_text_retriever import ChromaTextRetriever


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only Chroma schema inspection; no query or model download.")
    parser.add_argument("--kind", choices=["text", "figure", "all"], default="all")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    config = SafePLCConfig.from_env(mode="FULL")
    result = {}
    if args.kind in {"text", "all"}:
        try:
            result["text"] = ChromaTextRetriever(config.chroma_dir, config.text_collection).discover()
        except Exception as exc:
            result["text_error"] = f"{type(exc).__name__}: {exc}"
    if args.kind in {"figure", "all"}:
        try:
            result["figure"] = ChromaFigureRetriever(
                config.figure_chroma_dir,
                config.figure_collection,
                config.figure_cards_jsonl,
                config.visual_dir,
            ).discover()
        except Exception as exc:
            result["figure_error"] = f"{type(exc).__name__}: {exc}"
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
