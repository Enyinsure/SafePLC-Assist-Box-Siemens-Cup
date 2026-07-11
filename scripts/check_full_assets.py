#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from safeplc_assist_box.config import SafePLCConfig
from safeplc_assist_box.tools.chroma_figure_retriever import ChromaFigureRetriever, FigureMetadataMapper
from safeplc_assist_box.tools.chroma_text_retriever import ChromaTextRetriever
from safeplc_assist_box.tools.embedding_adapter import EmbeddingAdapter
from safeplc_assist_box.tools.metadata_normalizer import load_jsonl_records


def count_jsonl(path_value: str) -> int:
    path = Path(path_value) if path_value else Path()
    if not path.is_file():
        return 0
    return sum(1 for _ in load_jsonl_records(path))


def inspect_retriever(retriever: Any, kind: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "available": False,
        "collection_selection_ready": False,
        "embedding_ready": False,
        "selected_collection": "",
        "selected_collection_count": 0,
        "collections": [],
        "embedding_audit": {},
        "error": "",
    }
    try:
        result["collections"] = retriever.discover()
        collection = retriever._collection()
        result["selected_collection"] = retriever.collection_name
        selected = next(
            (row for row in result["collections"] if row.get("name") == retriever.collection_name),
            {},
        )
        result["selected_collection_count"] = int(selected.get("count") or 0)
        result["collection_selection_ready"] = result["selected_collection_count"] > 0
        retriever.embedding_adapter.query_arguments(collection, f"SafePLC {kind} embedding compatibility probe")
        result["embedding_audit"] = dict(retriever.embedding_adapter.last_audit)
        result["embedding_ready"] = True
        result["available"] = bool(result["collection_selection_ready"] and result["embedding_ready"])
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def check_assets(config: SafePLCConfig, require_figure: bool = False) -> Dict[str, Any]:
    configured_paths = {
        "SAFEPLC_CHROMA_DIR": config.chroma_dir,
        "SAFEPLC_FIGURE_CHROMA_DIR": config.figure_chroma_dir,
        "SAFEPLC_CHUNKS_JSONL": config.chunks_jsonl,
        "SAFEPLC_PAGES_JSONL": config.pages_jsonl,
        "SAFEPLC_FIGURE_CARDS_JSONL": config.figure_cards_jsonl,
        "SAFEPLC_FIGURE_CHUNKS_JSONL": config.figure_chunks_jsonl,
        "SAFEPLC_VISUAL_DIR": config.visual_dir,
    }
    embedding = EmbeddingAdapter.from_config(config)
    text = (
        inspect_retriever(
            ChromaTextRetriever(config.chroma_dir, config.text_collection, embedding_adapter=embedding),
            "text",
        )
        if config.chroma_dir and Path(config.chroma_dir).exists()
        else {"available": False, "error": "SAFEPLC_CHROMA_DIR missing", "collections": []}
    )
    figure_embedding = EmbeddingAdapter.from_config(config)
    figure = (
        inspect_retriever(
            ChromaFigureRetriever(
                config.figure_chroma_dir,
                config.figure_collection,
                config.figure_cards_jsonl,
                config.visual_dir,
                embedding_adapter=figure_embedding,
            ),
            "figure",
        )
        if config.figure_chroma_dir and Path(config.figure_chroma_dir).exists()
        else {"available": False, "error": "SAFEPLC_FIGURE_CHROMA_DIR missing", "collections": []}
    )
    counts = {
        "chunks": count_jsonl(config.chunks_jsonl),
        "pages": count_jsonl(config.pages_jsonl),
        "figure_cards": count_jsonl(config.figure_cards_jsonl),
        "figure_chunks": count_jsonl(config.figure_chunks_jsonl),
    }
    mapper = FigureMetadataMapper(config.figure_cards_jsonl, config.visual_dir)
    text_chroma_ready = bool(text.get("available"))
    figure_chroma_ready = bool(figure.get("available"))
    jsonl_text_ready = bool(config.allow_jsonl_fallback and (counts["chunks"] or counts["pages"]))
    jsonl_figure_ready = bool(
        config.allow_jsonl_fallback and (counts["figure_cards"] or counts["figure_chunks"])
    )
    effective_require_figure = bool(require_figure or config.require_figure_backend)
    chroma_full_ready = text_chroma_ready and (figure_chroma_ready if effective_require_figure else True)
    fallback_only_ready = bool(not text_chroma_ready and jsonl_text_ready and not effective_require_figure)
    full_ready = bool(chroma_full_ready or fallback_only_ready)
    reasons = []
    suggestions = []
    if not text_chroma_ready:
        reasons.append(str(text.get("error") or "Text Chroma collection/embedding is not ready."))
        suggestions.extend(["SAFEPLC_TEXT_COLLECTION", "SAFEPLC_EMBEDDING_MODEL_PATH"])
    if effective_require_figure and not figure_chroma_ready:
        reasons.append(str(figure.get("error") or "Figure Chroma collection/embedding is not ready."))
        suggestions.extend(["SAFEPLC_FIGURE_COLLECTION", "SAFEPLC_FIGURE_CHROMA_DIR"])
    if not full_ready and not jsonl_text_ready:
        suggestions.extend(["SAFEPLC_CHUNKS_JSONL", "SAFEPLC_ALLOW_JSONL_FALLBACK"])
    return {
        "mode": config.mode,
        "path_status": {
            name: {"path": value, "exists": bool(value and Path(value).exists())}
            for name, value in configured_paths.items()
        },
        "text_chroma_ready": text_chroma_ready,
        "figure_chroma_ready": figure_chroma_ready,
        "jsonl_text_fallback_ready": jsonl_text_ready,
        "jsonl_figure_fallback_ready": jsonl_figure_ready,
        "embedding_ready": bool(text.get("embedding_ready")),
        "collection_selection_ready": bool(text.get("collection_selection_ready")),
        "image_mapping_ready": mapper.image_resolvable_count() > 0,
        "full_ready": full_ready,
        "chroma_full_ready": chroma_full_ready,
        "fallback_only_ready": fallback_only_ready,
        "text_chroma": text,
        "figure_chroma": figure,
        "jsonl_counts": counts,
        "figure_card_count": mapper.card_count(),
        "image_resolvable_count": mapper.image_resolvable_count(),
        "allow_jsonl_fallback": config.allow_jsonl_fallback,
        "require_figure": effective_require_figure,
        "exit_reasons": reasons,
        "suggested_environment_variables": sorted(set(suggestions)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check SafePLC FULL retrieval assets without modifying them.")
    parser.add_argument("--mode", default="FULL")
    parser.add_argument("--strict", action="store_true", help="Require the current configuration to be runnable.")
    parser.add_argument("--require-chroma", action="store_true", help="Reject fallback-only readiness.")
    parser.add_argument("--require-figure", action="store_true", help="Require Figure Chroma and embedding readiness.")
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    result = check_assets(SafePLCConfig.from_env(mode=args.mode), require_figure=args.require_figure)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text)
    failed = (args.strict and not result["full_ready"]) or (
        args.require_chroma and not result["chroma_full_ready"]
    ) or (args.require_figure and not result["figure_chroma_ready"])
    if failed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
