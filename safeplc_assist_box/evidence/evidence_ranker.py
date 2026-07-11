#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import hashlib
import re
from typing import Dict, Iterable, List, Optional, Tuple

from ..schemas import AgentEvidence
from .model_identity import classify_model_match


MODEL_SCORES = {
    "exact_order_number": (1.0, 1.0, 0.0),
    "exact_model": (0.9, 0.0, 0.0),
    "compatible_alias": (0.75, 0.0, 0.0),
    "same_family_general": (0.0, 0.0, 0.25),
    "unknown": (0.0, 0.0, 0.0),
    "cross_family": (0.0, 0.0, 0.0),
}


def rank_evidence(
    evidences: Iterable[AgentEvidence],
    query: str = "",
    required_modality: Optional[str] = None,
    top_k: int = 12,
) -> List[AgentEvidence]:
    candidates = list(evidences)
    scored: List[Tuple[AgentEvidence, Dict[str, float], float, str]] = []
    for evidence in candidates:
        model_match = classify_model_match(query, evidence) if query else evidence.model_match_level or "unknown"
        exact_model, order_number, same_family = MODEL_SCORES.get(model_match, (0.0, 0.0, 0.0))
        vector_score = float(evidence.normalized_score or evidence.retrieval_score or 0.0)
        lexical_score = _lexical_score(query, evidence)
        direct_score = _directness(query, evidence)
        location_query = any(token in query.lower() for token in ("哪里", "位置", "where", "front", "图示", "前视图"))
        if not location_query:
            direct_score *= min(1.0, lexical_score * 2.0)
        modality_score = 0.3 if required_modality and evidence.modality == required_modality else 0.0
        page_score = 0.15 if evidence.page is not None else 0.0
        figure_score = 0.25 if location_query and (evidence.figure_id or evidence.figure_number) else 0.0
        image_score = 0.2 if location_query and (evidence.image_exists or evidence.visual_evidence_status == "image_available") else 0.0
        cross_penalty = 4.0 if model_match == "cross_family" else 0.0
        components = {
            "vector_score": vector_score,
            "lexical_score": lexical_score,
            "exact_model_score": exact_model,
            "order_number_score": order_number,
            "same_family_general_score": same_family,
            "direct_answer_score": direct_score,
            "modality_score": modality_score,
            "page_score": page_score,
            "figure_score": figure_score,
            "image_score": image_score,
            "duplicate_penalty": 0.0,
            "cross_family_penalty": cross_penalty,
        }
        raw_score = (
            0.45 * vector_score
            + 0.35 * lexical_score
            + 1.2 * exact_model * max(0.01, lexical_score * lexical_score)
            + 1.5 * order_number
            + 0.2 * same_family
            + direct_score
            + modality_score
            + page_score
            + figure_score
            + image_score
            - cross_penalty
        )
        scored.append((evidence, components, raw_score, model_match))

    # Determine duplicate penalties after all raw scores exist, independent of input order.
    by_duplicate: Dict[str, List[Tuple[AgentEvidence, Dict[str, float], float, str]]] = {}
    for item in scored:
        by_duplicate.setdefault(_duplicate_key(item[0]), []).append(item)
    for group in by_duplicate.values():
        ordered = sorted(group, key=lambda item: (-item[2], item[0].evidence_id))
        for duplicate_index, item in enumerate(ordered[1:], start=1):
            penalty = min(0.5, 0.15 * duplicate_index)
            item[1]["duplicate_penalty"] = penalty

    adjusted = [
        (evidence, components, raw_score - components["duplicate_penalty"], model_match)
        for evidence, components, raw_score, model_match in scored
    ]
    raw_values = [item[2] for item in adjusted]
    minimum = min(raw_values, default=0.0)
    maximum = max(raw_values, default=0.0)
    for evidence, components, raw_score, model_match in adjusted:
        normalized = 1.0 if maximum == minimum and raw_score > 0 else (
            (raw_score - minimum) / (maximum - minimum) if maximum > minimum else 0.0
        )
        evidence.model_match_level = model_match
        evidence.quality_score = round(normalized, 6)
        evidence.metadata.update(
            {
                "model_match_level": model_match,
                "raw_rank_score": round(raw_score, 6),
                "normalized_rank_score": round(normalized, 6),
                "score_components": {key: round(value, 6) for key, value in components.items()},
                "distance_metric_assumption": evidence.metadata.get(
                    "distance_metric_assumption", "unknown_metric_inverse_1_plus_distance"
                ),
            }
        )
    adjusted.sort(key=lambda item: (-item[2], item[0].evidence_id))
    return [item[0] for item in adjusted[: max(1, top_k)]]


def _tokens(text: str) -> List[str]:
    tokens = list(
        dict.fromkeys(
            token.lower()
            for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9_/\-]*|[\u4e00-\u9fff]{2,}", text or "")
            if token.strip()
        )
    )
    low = (text or "").lower()
    aliases = {
        "通信": ["communication"],
        "指示灯": ["led"],
        "异常": ["fault", "diagnostics"],
        "故障": ["fault", "diagnostics"],
        "排查": ["check", "diagnostics"],
        "接线": ["wiring", "terminal"],
        "端子": ["terminal", "wiring"],
        "电源": ["power", "voltage"],
        "电压": ["voltage"],
        "位置": ["location", "front"],
        "哪里": ["location", "front"],
    }
    for marker, additions in aliases.items():
        if marker in low:
            tokens.extend(item for item in additions if item not in tokens)
    return tokens


def _lexical_score(query: str, evidence: AgentEvidence) -> float:
    tokens = _tokens(query)
    if not tokens:
        return 0.0
    haystack = " ".join(
        [
            evidence.text,
            evidence.compact_excerpt,
            evidence.manual_title,
            evidence.module_model,
            evidence.figure_number,
            evidence.section,
        ]
    ).lower()
    return sum(1 for token in tokens if token in haystack) / len(tokens)


def _directness(query: str, evidence: AgentEvidence) -> float:
    low_query = query.lower()
    low_text = " ".join(
        [evidence.text, evidence.compact_excerpt, evidence.figure_number, evidence.parameter, evidence.section]
    ).lower()
    score = 0.25 if evidence.direct_evidence else 0.0
    if any(token in low_query for token in ("哪里", "位置", "where")):
        if any(token in low_text for token in ("front view", "前视图", "标号", "marker")):
            score += 0.45
        if evidence.figure_number:
            score += 0.25
        if evidence.page is not None:
            score += 0.2
    if "x1" in low_query and "x1" in low_text:
        score += 0.25
    if any(token in low_query for token in ("通信", "指示灯", "故障", "异常", "troubleshoot")) and any(
        token in low_text for token in ("communication", "led", "fault", "diagnostic", "alarm")
    ):
        score += 0.8
    if any(token in low_query for token in ("接线", "端子", "wiring")) and any(
        token in low_text for token in ("wiring", "terminal", "power-off", "cabling")
    ):
        score += 0.8
    return score


def _duplicate_key(evidence: AgentEvidence) -> str:
    normalized_text = re.sub(r"\s+", "", evidence.text.lower())
    document = evidence.document_id or evidence.manual_title or evidence.source
    seed = "|".join([document.lower(), str(evidence.page or ""), evidence.figure_number.lower(), normalized_text[:500]])
    return hashlib.sha256(seed.encode("utf-8", errors="ignore")).hexdigest()
