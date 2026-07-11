#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.check_full_assets import check_assets
from safeplc_assist_box.config import SafePLCConfig


ENV_KEYS = [
    "SAFEPLC_MODE",
    "SAFEPLC_CHROMA_DIR",
    "SAFEPLC_TEXT_COLLECTION",
    "SAFEPLC_FIGURE_CHROMA_DIR",
    "SAFEPLC_FIGURE_COLLECTION",
    "SAFEPLC_CHUNKS_JSONL",
    "SAFEPLC_PAGES_JSONL",
    "SAFEPLC_FIGURE_CARDS_JSONL",
    "SAFEPLC_FIGURE_CHUNKS_JSONL",
    "SAFEPLC_VISUAL_DIR",
    "SAFEPLC_REPORT_DIR",
    "SAFEPLC_ROUTING_STRATEGY",
    "SAFEPLC_MAX_AGENTS",
    "SAFEPLC_ALLOW_JSONL_FALLBACK",
    "SAFEPLC_REQUIRE_FIGURE_BACKEND",
]


def build_env(args: argparse.Namespace) -> Dict[str, str]:
    project = Path(__file__).resolve().parents[1]
    values = {key: os.environ.get(key, "") for key in ENV_KEYS}
    values.update(
        {
            "SAFEPLC_MODE": args.mode or values["SAFEPLC_MODE"] or "FULL",
            "SAFEPLC_CHROMA_DIR": args.chroma_dir or values["SAFEPLC_CHROMA_DIR"],
            "SAFEPLC_TEXT_COLLECTION": args.text_collection or values["SAFEPLC_TEXT_COLLECTION"],
            "SAFEPLC_FIGURE_CHROMA_DIR": args.figure_chroma_dir or values["SAFEPLC_FIGURE_CHROMA_DIR"],
            "SAFEPLC_FIGURE_COLLECTION": args.figure_collection or values["SAFEPLC_FIGURE_COLLECTION"],
            "SAFEPLC_CHUNKS_JSONL": args.chunks_jsonl or values["SAFEPLC_CHUNKS_JSONL"],
            "SAFEPLC_PAGES_JSONL": args.pages_jsonl or values["SAFEPLC_PAGES_JSONL"],
            "SAFEPLC_FIGURE_CARDS_JSONL": args.figure_cards_jsonl or values["SAFEPLC_FIGURE_CARDS_JSONL"],
            "SAFEPLC_FIGURE_CHUNKS_JSONL": args.figure_chunks_jsonl or values["SAFEPLC_FIGURE_CHUNKS_JSONL"],
            "SAFEPLC_VISUAL_DIR": args.visual_dir or values["SAFEPLC_VISUAL_DIR"],
            "SAFEPLC_REPORT_DIR": args.report_dir or values["SAFEPLC_REPORT_DIR"] or str(project / "reports"),
            "SAFEPLC_ROUTING_STRATEGY": args.routing_strategy or values["SAFEPLC_ROUTING_STRATEGY"] or "adaptive",
            "SAFEPLC_MAX_AGENTS": str(args.max_agents or values["SAFEPLC_MAX_AGENTS"] or "4"),
            "SAFEPLC_ALLOW_JSONL_FALLBACK": "1" if args.allow_jsonl_fallback else values["SAFEPLC_ALLOW_JSONL_FALLBACK"] or "0",
            "SAFEPLC_REQUIRE_FIGURE_BACKEND": "1" if args.require_figure_backend else values["SAFEPLC_REQUIRE_FIGURE_BACKEND"] or "0",
        }
    )
    return values


def env_text(values: Dict[str, str]) -> str:
    return "\n".join(f"{key}={values.get(key, '')}" for key in ENV_KEYS) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare SafePLC FULL env file without changing the active shell.")
    parser.add_argument("--mode", default="")
    parser.add_argument("--chroma-dir", default="")
    parser.add_argument("--text-collection", default="")
    parser.add_argument("--figure-chroma-dir", default="")
    parser.add_argument("--figure-collection", default="")
    parser.add_argument("--chunks-jsonl", default="")
    parser.add_argument("--pages-jsonl", default="")
    parser.add_argument("--figure-cards-jsonl", default="")
    parser.add_argument("--figure-chunks-jsonl", default="")
    parser.add_argument("--visual-dir", default="")
    parser.add_argument("--report-dir", default="")
    parser.add_argument("--routing-strategy", default="")
    parser.add_argument("--max-agents", default="")
    parser.add_argument("--allow-jsonl-fallback", action="store_true")
    parser.add_argument("--require-figure-backend", action="store_true")
    parser.add_argument("--write-env", default="")
    args = parser.parse_args()

    values = build_env(args)
    if args.write_env:
        out = Path(args.write_env)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(env_text(values), encoding="utf-8")

    old_env = {key: os.environ.get(key) for key in ENV_KEYS}
    try:
        os.environ.update(values)
        config = SafePLCConfig.from_env(mode=values["SAFEPLC_MODE"])
        audit = check_assets(config)
    finally:
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    print(json.dumps({"env": values, "asset_audit": audit}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
