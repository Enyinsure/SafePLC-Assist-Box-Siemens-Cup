#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import hashlib
import re
from typing import Dict, Iterable, List, Optional, Tuple

from ..schemas import AgentEvidence
from .model_identity import classify_model_match, extract_model_identity


MODEL_SCORES = {
    "exact_order_number": (1.0, 1.0, 0.0),
    "exact_model": (0.9, 0.0, 0.0),
    "compatible_alias": (0.75, 0.0, 0.0),
    "same_family_general": (0.0, 0.0, 0.25),
    "unknown": (0.0, 0.0, 0.0),
    "cross_family": (0.0, 0.0, 0.0),
}

LOCATION_TERMS = ("哪里", "在哪", "位置", "物理位置", "前面", "后面", "正面", "背面", "front", "where", "location", "layout")
LOCATION_POSITIVE = (
    "不带前面板", "模块前视图", "cpu 正视图", "前视图", "操作和显示元件",
    "操作员控制和连接元件", "连接元件", "接口位置", "标号", "front view", "interface layout",
)
LOCATION_NEGATIVE = (
    "发送周期", "同步域", "耦合", "irt 周期", "尺寸图", "mac 地址分配", "方框图",
    "电源端子分配", "技术数据", "network synchronization", "cycle time",
)


def reciprocal_rank_fusion(evidences: Iterable[AgentEvidence], k: int = 60) -> List[AgentEvidence]:
    """Fuse per-query candidates while preserving query provenance."""
    groups: Dict[str, List[AgentEvidence]] = {}
    for evidence in evidences:
        groups.setdefault(evidence.evidence_id or _duplicate_key(evidence), []).append(evidence)
    fused: List[AgentEvidence] = []
    for group in groups.values():
        best = max(group, key=lambda item: float(item.vector_similarity or item.normalized_score or 0.0))
        ranks: Dict[str, int] = {}
        for item in group:
            retrieval_query = str(item.metadata.get("retrieval_query") or item.query_text or "")
            rank = int(item.metadata.get("rank_within_query") or 10**6)
            if retrieval_query:
                ranks[retrieval_query] = min(rank, ranks.get(retrieval_query, rank))
        rrf_score = sum(1.0 / (max(1, k) + rank) for rank in ranks.values())
        best.metadata.update(
            {
                "query_ranks": ranks,
                "rrf_score": round(rrf_score, 8),
                "matched_query_count": len(ranks),
                "best_query_rank": min(ranks.values(), default=0),
            }
        )
        best.query_ranks = ranks
        best.rrf_score = round(rrf_score, 8)
        best.matched_query_count = len(ranks)
        best.best_query_rank = min(ranks.values(), default=0)
        fused.append(best)
    return fused


def rank_evidence(
    evidences: Iterable[AgentEvidence],
    query: str = "",
    required_modality: Optional[str] = None,
    top_k: int = 12,
) -> List[AgentEvidence]:
    candidates = reciprocal_rank_fusion(evidences)
    scored: List[Tuple[AgentEvidence, Dict[str, float], float, str]] = []
    for evidence in candidates:
        model_match = classify_model_match(query, evidence) if query else evidence.model_match_level or "unknown"
        exact_model, order_number, same_family = MODEL_SCORES.get(model_match, (0.0, 0.0, 0.0))
        vector_score = float(evidence.normalized_score or evidence.retrieval_score or 0.0)
        lexical_score = _lexical_score(query, evidence)
        direct_score = location_directness_score(query, evidence) if _is_location_query(query) else _directness(query, evidence)
        location_query = _is_location_query(query)
        modality_score = 0.3 if required_modality and evidence.modality == required_modality else 0.0
        page_score = 0.15 if evidence.page is not None else 0.0
        manual_figure = evidence.manual_figure_number or evidence.figure_number
        figure_id_type = str(evidence.metadata.get("figure_id_type") or "unknown")
        figure_score = 0.3 if location_query and manual_figure else 0.0
        if figure_id_type == "synthetic_visual_id" and not manual_figure:
            figure_score = 0.0
        image_score = 0.2 if location_query and (evidence.image_exists or evidence.visual_evidence_status == "image_available") else 0.0
        cross_penalty = 4.0 if model_match == "cross_family" else 0.0
        same_family_penalty = 0.45 if (
            model_match == "same_family_general" and extract_model_specific(query) and location_query
        ) else 0.0
        rrf_score = float(evidence.metadata.get("rrf_score") or 0.0)
        low_evidence_text = " ".join([evidence.text, evidence.section, evidence.manual_figure_caption]).lower()
        irrelevant_section_penalty = 0.35 * sum(term in low_evidence_text for term in LOCATION_NEGATIVE) if location_query else 0.0
        manual_review_penalty = 0.2 if evidence.metadata.get("manual_review_required") else 0.0
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
            "rrf_score": rrf_score,
            "same_family_general_penalty": same_family_penalty,
            "different_model_penalty": cross_penalty,
            "location_directness_bonus": max(0.0, direct_score),
            "manual_figure_number_bonus": figure_score,
            "irrelevant_section_penalty": irrelevant_section_penalty,
            "manual_review_penalty": manual_review_penalty,
            "duplicate_penalty": 0.0,
            "cross_family_penalty": cross_penalty,
        }
        raw_score = (
            4.0 * rrf_score
            + 0.3 * vector_score
            + 0.35 * lexical_score
            + 1.2 * exact_model * max(0.1, lexical_score)
            + 1.5 * order_number
            + 0.2 * same_family
            + direct_score
            + modality_score
            + page_score
            + figure_score
            + image_score
            - same_family_penalty
            - manual_review_penalty
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
                "distance_metric": evidence.distance_metric,
                "score_conversion": evidence.score_conversion,
                "vector_similarity": evidence.vector_similarity,
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
    if any(token in low_query for token in ("emc", "电磁兼容", "接地", "屏蔽", "干扰", "抗干扰")):
        score += emc_directness_score(evidence)
    return score


def emc_directness_score(evidence: AgentEvidence) -> float:
    text = " ".join([evidence.text, evidence.compact_excerpt, evidence.section, evidence.manual_title]).lower()
    measures = [
        bool(re.search(r"grounded\s+control\s+(?:cabinets?|boxes?)|接地(?:的)?控制(?:柜|箱)", text, re.I)),
        bool(re.search(r"noise\s+filters?.{0,30}supply\s+lines?|电源线.{0,20}噪声滤波器", text, re.I)),
        "industrial environment" in text or "industrial applications" in text
        or "designed for industrial use" in text or "工业环境" in text,
        bool(re.search(r"EN\s*55011.{0,30}Class\s*B", text, re.I)),
    ]
    count = sum(measures)
    score = 0.55 * count
    if "electromagnetic compatibility" in text or "电磁兼容" in text:
        score += 0.25
    certification = bool(re.search(r"\b(?:approval|certification|certificate)s?\b|认证|许可", text, re.I))
    if certification and not count:
        score -= 1.2
    if ("electromagnetic compatibility" in text or "emc definition" in text) and not count:
        score -= 0.65
    if re.search(r"(?:communication module|通信模块|\b(?:CM|CP)\s*\d)", text, re.I) and certification and not count:
        score -= 0.7
    if "siwarex" in text and not count:
        score -= 0.9
    return score


def _is_location_query(query: str) -> bool:
    low = str(query or "").lower()
    return any(token in low for token in LOCATION_TERMS)


def extract_model_specific(query: str) -> bool:
    return bool(re.search(r"\b(?:CPU\s*)?15\d{2}(?:-\d)?\b|\b6ES7", query or "", re.I))


def location_directness_score(query: str, evidence: AgentEvidence) -> float:
    low_query = str(query or "").lower()
    low_text = " ".join(
        [evidence.text, evidence.compact_excerpt, evidence.section, evidence.manual_figure_caption, evidence.parameter]
    ).lower()
    score = 0.25 if evidence.direct_evidence else 0.0
    score += 0.28 * sum(term in low_text for term in LOCATION_POSITIVE)
    score -= 0.35 * sum(term in low_text for term in LOCATION_NEGATIVE)
    interfaces = re.findall(r"\bX\d+\b", low_query, re.I)
    if interfaces and all(item.lower() in low_text for item in interfaces):
        score += 0.35
    expected = extract_model_identity(query).normalized_model.lower()
    if expected and expected in low_text and interfaces and any(term in low_text for term in ("前视图", "front view")):
        score += 0.8
    if evidence.section and any(term in evidence.section.lower() for term in ("操作和显示元件", "不带前面板的模块前视图")):
        score += 0.65
    if evidence.metadata.get("location_marker"):
        score += 0.3
    if evidence.manual_figure_number or evidence.figure_number:
        score += 0.3
    if re.search(r"PROFINET\s+IO\s+接口\s*[（(]?X\d+[）)]?", evidence.text or "", re.I):
        score += 0.65
    return max(-2.0, score)


def _duplicate_key(evidence: AgentEvidence) -> str:
    normalized_text = re.sub(r"\s+", "", evidence.text.lower())
    document = evidence.document_id or evidence.manual_title or evidence.source
    seed = "|".join([document.lower(), str(evidence.page or ""), evidence.figure_number.lower(), normalized_text[:500]])
    return hashlib.sha256(seed.encode("utf-8", errors="ignore")).hexdigest()
