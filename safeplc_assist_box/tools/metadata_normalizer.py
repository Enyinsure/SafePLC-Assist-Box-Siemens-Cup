#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from ..schemas import AgentEvidence, compact_text


VALID_BACKENDS = {
    "chroma_text",
    "chroma_table",
    "chroma_figure",
    "jsonl_chunks",
    "jsonl_pages",
    "sample_fixture",
    "system_boundary",
}


PAGE_KEYS = ("page", "page_no", "page_number", "page_index")
TEXT_KEYS = ("text", "content", "chunk", "document", "ocr_text", "caption")
TITLE_KEYS = ("manual_title", "title", "doc_title", "heading", "source_title")
MODEL_KEYS = ("module_model", "module", "model", "device_model", "product")
ORDER_KEYS = ("order_number", "article_number", "mlfb", "catalog_number")
FIGURE_KEYS = ("figure_id", "fig_id", "image_id")
FIGURE_NUMBER_KEYS = ("figure_number", "fig_no", "figure", "caption_number")
CHUNK_KEYS = ("chunk_id", "id", "uid", "chunk_index")
DOC_KEYS = ("document_id", "doc_id", "source_id", "manual_id")


def first_value(data: Dict[str, Any], keys: Iterable[str], default: str = "") -> str:
    for key in keys:
        value = data.get(key)
        if value not in {None, ""}:
            return str(value)
    return default


def parse_page(value: Any) -> Optional[int]:
    if value in {None, ""}:
        return None
    if isinstance(value, int):
        return value
    match = re.search(r"\d+", str(value))
    return int(match.group(0)) if match else None


def normalize_score(raw_distance: Any, fallback_score: float = 0.0) -> float:
    if raw_distance in {None, ""}:
        return float(fallback_score or 0.0)
    try:
        distance = float(raw_distance)
    except (TypeError, ValueError):
        return float(fallback_score or 0.0)
    if distance < 0:
        return 0.0
    return round(1.0 / (1.0 + distance), 6)


def stable_evidence_id(ev: AgentEvidence) -> str:
    seed = "|".join(
        [
            ev.source or "",
            ev.retrieval_backend or "",
            str(ev.page or ""),
            ev.chunk_id or "",
            ev.figure_id or "",
            hashlib.sha256((ev.text or "").encode("utf-8", errors="ignore")).hexdigest()[:16],
        ]
    )
    return "ev_" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def normalize_metadata(
    *,
    text: str,
    metadata: Optional[Dict[str, Any]] = None,
    backend: str,
    query_text: str = "",
    collection_name: str = "",
    source_path: str = "",
    raw_distance: Any = None,
    fallback_score: float = 0.0,
    modality_hint: str = "text",
) -> AgentEvidence:
    meta = dict(metadata or {})
    if backend not in VALID_BACKENDS:
        raise ValueError(f"Unsupported retrieval backend: {backend}")

    source = first_value(meta, ("source", "source_path", "file", "path", "doc"), Path(source_path).name or backend)
    page = parse_page(first_value(meta, PAGE_KEYS, ""))
    modality = str(meta.get("modality") or meta.get("source_type") or modality_hint or "text").lower()
    if backend == "chroma_table" and modality == "text":
        modality = "table"
    if backend == "chroma_figure":
        modality = "figure"

    normalized = normalize_score(raw_distance, fallback_score=fallback_score)
    raw_image_path = str(meta.get("image_path") or meta.get("image") or "")
    absolute_image = Path(raw_image_path) if raw_image_path else Path()
    image_exists = bool(raw_image_path and absolute_image.is_absolute() and absolute_image.is_file())
    resolved_image_path = str(absolute_image) if image_exists else ""
    figure_number = first_value(meta, FIGURE_NUMBER_KEYS)
    figure_id = first_value(meta, FIGURE_KEYS)
    figure_text = bool(re.search(r"(?:Figure|Fig\.|图)\s*[\d\-.]+|front\s+view|前视图", str(text or ""), re.I))
    visual_status = "image_available" if image_exists else "page_text_only" if (page or figure_id or figure_number or figure_text) else "missing"
    ev = AgentEvidence(
        evidence_id="",
        source=source,
        source_type=str(meta.get("source_type") or meta.get("type") or backend),
        retrieval_backend=backend,
        modality=modality,
        text=str(text or ""),
        compact_excerpt=compact_text(str(text or "")),
        manual_title=first_value(meta, TITLE_KEYS),
        manual_version=str(meta.get("manual_version") or meta.get("version") or ""),
        device_family=str(meta.get("device_family") or meta.get("family") or ""),
        module_model=first_value(meta, MODEL_KEYS),
        order_number=first_value(meta, ORDER_KEYS),
        page=page,
        section=str(meta.get("section") or meta.get("chapter") or ""),
        figure_id=figure_id,
        figure_number=figure_number,
        image_path=resolved_image_path,
        raw_image_path=raw_image_path,
        resolved_image_path=resolved_image_path,
        image_exists=image_exists,
        visual_evidence_status=visual_status,
        chunk_id=first_value(meta, CHUNK_KEYS),
        document_id=first_value(meta, DOC_KEYS),
        collection_name=collection_name,
        query_text=query_text,
        source_path=source_path or str(meta.get("source_path") or ""),
        retrieval_score=normalized,
        raw_distance=float(raw_distance) if raw_distance not in {None, ""} else None,
        normalized_score=normalized,
        title=first_value(meta, TITLE_KEYS),
        module=first_value(meta, MODEL_KEYS),
        parameter=str(meta.get("parameter") or meta.get("param") or ""),
        metadata={
            **meta,
            "retrieval_backend": backend,
            "collection_name": collection_name,
            "raw_distance": raw_distance,
            "normalized_score": normalized,
            "query_text": query_text,
            "retrieval_timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "raw_image_path": raw_image_path,
            "resolved_image_path": resolved_image_path,
            "image_exists": image_exists,
            "visual_evidence_status": visual_status,
        },
    )
    ev.evidence_id = stable_evidence_id(ev)
    return ev


def load_jsonl_records(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                record.setdefault("_line_no", line_no)
                yield record
