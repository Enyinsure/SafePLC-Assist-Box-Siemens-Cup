#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from safeplc_assist_box.config import SafePLCConfig
from safeplc_assist_box.tools.chroma_figure_retriever import ChromaFigureRetriever, FigureMetadataMapper
from safeplc_assist_box.tools.chroma_text_retriever import ChromaTextRetriever, ChromaUnavailable
from safeplc_assist_box.tools.metadata_normalizer import load_jsonl_records


def count_jsonl(path_value: str) -> int:
    path = Path(path_value) if path_value else Path()
    if not path.exists() or not path.is_file():
        return 0
    return sum(1 for _ in load_jsonl_records(path))


def discover_text(config: SafePLCConfig) -> Dict[str, object]:
    if not config.chroma_dir or not Path(config.chroma_dir).exists():
        return {"available": False, "error": "SAFEPLC_CHROMA_DIR missing", "collections": []}
    retriever = ChromaTextRetriever(config.chroma_dir, config.text_collection)
    try:
        collections = retriever.discover()
    except ChromaUnavailable as exc:
        return {"available": False, "error": str(exc), "collections": []}
    except Exception as exc:
        return {"available": False, "error": f"Unexpected text Chroma discovery failure: {exc}", "collections": []}
    return {
        "available": bool(collections),
        "selected_collection": config.text_collection or (collections[0]["name"] if collections else ""),
        "collections": collections,
    }


def discover_figure(config: SafePLCConfig) -> Dict[str, object]:
    if not config.figure_chroma_dir or not Path(config.figure_chroma_dir).exists():
        return {"available": False, "error": "SAFEPLC_FIGURE_CHROMA_DIR missing", "collections": []}
    retriever = ChromaFigureRetriever(
        config.figure_chroma_dir,
        config.figure_collection,
        config.figure_cards_jsonl,
        config.visual_dir,
    )
    try:
        collections = retriever.discover()
    except ChromaUnavailable as exc:
        return {"available": False, "error": str(exc), "collections": []}
    except Exception as exc:
        return {"available": False, "error": f"Unexpected figure Chroma discovery failure: {exc}", "collections": []}
    return {
        "available": bool(collections),
        "selected_collection": config.figure_collection or (collections[0]["name"] if collections else ""),
        "collections": collections,
    }


def check_assets(config: SafePLCConfig) -> Dict[str, object]:
    paths = {
        "SAFEPLC_CHROMA_DIR": config.chroma_dir,
        "SAFEPLC_FIGURE_CHROMA_DIR": config.figure_chroma_dir,
        "SAFEPLC_CHUNKS_JSONL": config.chunks_jsonl,
        "SAFEPLC_PAGES_JSONL": config.pages_jsonl,
        "SAFEPLC_FIGURE_CARDS_JSONL": config.figure_cards_jsonl,
        "SAFEPLC_FIGURE_CHUNKS_JSONL": config.figure_chunks_jsonl,
        "SAFEPLC_VISUAL_DIR": config.visual_dir,
    }
    path_status = {
        name: {"path": value, "exists": bool(value and Path(value).exists())}
        for name, value in paths.items()
    }
    text = discover_text(config)
    figure = discover_figure(config)
    figure_cards = FigureMetadataMapper(config.figure_cards_jsonl, config.visual_dir)
    jsonl_counts = {
        "chunks": count_jsonl(config.chunks_jsonl),
        "pages": count_jsonl(config.pages_jsonl),
        "figure_cards": count_jsonl(config.figure_cards_jsonl),
        "figure_chunks": count_jsonl(config.figure_chunks_jsonl),
    }
    text_count = sum(int(row.get("count", 0) or 0) for row in text.get("collections", []) if isinstance(row, dict))
    figure_count = sum(int(row.get("count", 0) or 0) for row in figure.get("collections", []) if isinstance(row, dict))
    full_ready = bool(text.get("available") and text_count > 0)
    if config.require_figure_backend:
        full_ready = full_ready and bool(figure.get("available") and figure_count > 0)
    return {
        "mode": config.mode,
        "path_status": path_status,
        "text_chroma": text,
        "figure_chroma": figure,
        "jsonl_counts": jsonl_counts,
        "figure_card_count": figure_cards.card_count(),
        "image_resolvable_count": figure_cards.image_resolvable_count(),
        "allow_jsonl_fallback": config.allow_jsonl_fallback,
        "require_figure_backend": config.require_figure_backend,
        "full_ready": full_ready,
        "full_ready_reason": (
            "Text Chroma is discoverable; figure Chroma required and discoverable."
            if full_ready and config.require_figure_backend
            else "Text Chroma is discoverable."
            if full_ready
            else "FULL startup conditions are not satisfied."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check SafePLC FULL retrieval assets.")
    parser.add_argument("--mode", default=None)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    config = SafePLCConfig.from_env(mode=args.mode)
    result = check_assets(config)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(text)
    if (args.strict or config.mode == "FULL") and not result["full_ready"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
