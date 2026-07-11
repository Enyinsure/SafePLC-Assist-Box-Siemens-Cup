#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
from typing import Iterable, List, Optional

from ..schemas import AgentEvidence
from .model_identity import classify_model_match


MODEL_WEIGHTS = {
    "exact_order_number": 1.0,
    "exact_model": 0.8,
    "compatible_alias": 0.65,
    "same_family_general": 0.3,
    "unknown": 0.0,
    "cross_family": -1.0,
}


def _tokens(text: str) -> List[str]:
    return list(
        dict.fromkeys(
            t.lower()
            for t in re.findall(r"[A-Za-z0-9][A-Za-z0-9_/\-]*|[\u4e00-\u9fff]{2,}", text or "")
            if t.strip()
        )
    )


def _lexical_score(query: str, ev: AgentEvidence) -> float:
    tokens = _tokens(query)
    if not tokens:
        return 0.0
    haystack = " ".join(
        [
            ev.text or "",
            ev.compact_excerpt or "",
            ev.manual_title or "",
            ev.module_model or "",
            ev.figure_number or "",
            ev.section or "",
        ]
    ).lower()
    hits = sum(1 for token in tokens if token in haystack)
    return hits / max(len(tokens), 1)


def _directness(query: str, ev: AgentEvidence) -> float:
    q = query.lower()
    text = " ".join([ev.compact_excerpt, ev.figure_number, ev.parameter, ev.section]).lower()
    score = 0.0
    if "x1" in q and "x1" in text:
        score += 0.4
    if "where" in q or "where" in text or "哪里" in query or "位置" in query:
        if ev.figure_id or ev.figure_number or ev.page:
            score += 0.2
    if ev.direct_evidence:
        score += 0.2
    return min(score, 1.0)


def rank_evidence(
    evidences: Iterable[AgentEvidence],
    query: str = "",
    required_modality: Optional[str] = None,
    top_k: int = 12,
) -> List[AgentEvidence]:
    ranked: List[AgentEvidence] = []
    seen_pages = set()
    for ev in evidences:
        vector_score = ev.normalized_score or ev.retrieval_score
        lexical_score = _lexical_score(query, ev)
        model_match = classify_model_match(query, ev) if query else ev.model_match_level or "unknown"
        model_score = MODEL_WEIGHTS.get(model_match, 0.0)
        order_match = 0.4 if ev.order_number and ev.order_number.lower() in query.lower() else 0.0
        direct_score = _directness(query, ev)
        modality_score = 0.25 if required_modality and ev.modality == required_modality else 0.0
        figure_score = 0.2 if (ev.figure_id or ev.figure_number or ev.image_path) else 0.0
        duplicate_penalty = 0.15 if (ev.source, ev.page) in seen_pages else 0.0
        cross_family_penalty = 2.0 if model_match == "cross_family" else 0.0
        seen_pages.add((ev.source, ev.page))
        score = (
            0.35 * vector_score
            + 0.25 * lexical_score
            + 0.2 * max(model_score, 0.0)
            + order_match
            + direct_score
            + modality_score
            + figure_score
            - duplicate_penalty
            - cross_family_penalty
        )
        ev.model_match_level = model_match
        ev.quality_score = round(max(0.0, min(1.0, score)), 6)
        ev.retrieval_score = ev.quality_score
        ev.metadata["model_match_level"] = model_match
        ev.metadata["score_components"] = {
            "vector_score": round(vector_score, 6),
            "lexical_score": round(lexical_score, 6),
            "model_match": model_match,
            "model_score": round(model_score, 6),
            "order_number_match": round(order_match, 6),
            "direct_answer_score": round(direct_score, 6),
            "modality_score": round(modality_score, 6),
            "figure_availability": round(figure_score, 6),
            "duplicate_penalty": round(duplicate_penalty, 6),
            "cross_family_penalty": round(cross_family_penalty, 6),
        }
        ranked.append(ev)
    ranked.sort(key=lambda item: item.quality_score, reverse=True)
    return ranked[: max(1, top_k)]
