#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Iterable, List

from ..schemas import AgentEvidence


MODEL_MATCH_LEVELS = {
    "exact_order_number",
    "exact_model",
    "compatible_alias",
    "same_family_general",
    "cross_family",
    "unknown",
}


@dataclass
class ModelIdentity:
    raw_text: str
    normalized_models: List[str] = field(default_factory=list)
    order_numbers: List[str] = field(default_factory=list)
    family_hints: List[str] = field(default_factory=list)


def normalize_text(text: str) -> str:
    value = unicodedata.normalize("NFKC", text or "")
    value = value.upper()
    value = value.replace("／", "/").replace("–", "-").replace("—", "-")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_model(text: str) -> str:
    value = normalize_text(text)
    value = value.replace("CPU", "CPU ")
    value = re.sub(r"\s+", " ", value)
    value = value.replace(" PN DP", " PN/DP")
    value = value.replace("PN / DP", "PN/DP")
    if re.search(r"\b1517-3\s+PN\b", value) and "PN/DP" not in value:
        return "CPU 1517-3 PN/DP"
    m = re.search(r"(?:CPU\s*)?(\d{4}(?:-\d)?\s*(?:PN/DP|PN|DP|H|HF)?)", value)
    if m:
        model = m.group(1).strip()
        if not model.startswith("CPU"):
            model = "CPU " + model
        return re.sub(r"\s+", " ", model)
    return value


def extract_order_numbers(text: str) -> List[str]:
    normalized = normalize_text(text)
    return list(dict.fromkeys(re.findall(r"\b6ES\d[\w\-]*\b", normalized)))


def extract_model_identity(text: str) -> ModelIdentity:
    normalized = normalize_text(text)
    order_numbers = extract_order_numbers(normalized)
    candidates = re.findall(r"(?:CPU\s*)?\d{4}(?:-\d)?\s*(?:PN/DP|PN|DP|H|HF)?", normalized)
    models = [normalize_model(candidate) for candidate in candidates]
    if "1517-3 PN" in normalized and "CPU 1517-3 PN/DP" not in models:
        models.append("CPU 1517-3 PN/DP")
    family_hints = []
    if "S7-1500" in normalized or "1500" in normalized:
        family_hints.append("S7-1500")
    if is_redundant_family_text(normalized):
        family_hints.append("S7-1500R/H")
    return ModelIdentity(
        raw_text=text,
        normalized_models=list(dict.fromkeys(models)),
        order_numbers=order_numbers,
        family_hints=list(dict.fromkeys(family_hints)),
    )


def is_redundant_family_text(text: str) -> bool:
    normalized = normalize_text(text)
    return bool(
        re.search(r"S7[- ]?1500\s*R/H", normalized)
        or re.search(r"\b15(17|18)\s*H(F)?\b", normalized)
        or "R/H" in normalized
    )


def classify_model_match(query: str, evidence: AgentEvidence) -> str:
    expected = extract_model_identity(query)
    evidence_text = " ".join(
        [
            evidence.text or "",
            evidence.compact_excerpt or "",
            evidence.module_model or "",
            evidence.module or "",
            evidence.manual_title or "",
            evidence.source or "",
            evidence.order_number or "",
        ]
    )
    actual = extract_model_identity(evidence_text)

    if "S7-1500R/H" in actual.family_hints and "S7-1500R/H" not in expected.family_hints:
        return "cross_family"

    if expected.order_numbers:
        if set(expected.order_numbers) & set(actual.order_numbers):
            return "exact_order_number"
        if evidence.order_number and evidence.order_number.upper() not in expected.order_numbers:
            return "cross_family"

    if expected.normalized_models:
        expected_models = set(expected.normalized_models)
        actual_models = set(actual.normalized_models)
        if expected_models & actual_models:
            return "exact_model"
        if "CPU 1517-3 PN/DP" in expected_models and any(m in actual_models for m in {"CPU 1517-3 PN", "CPU 1517-3 PN/DP"}):
            return "compatible_alias"
        if actual.family_hints and expected.family_hints and set(actual.family_hints) & set(expected.family_hints):
            return "same_family_general"
        if actual_models:
            return "cross_family"

    if actual.family_hints or expected.family_hints:
        return "same_family_general"
    return "unknown"


def reject_cross_family(evidences: Iterable[AgentEvidence], query: str) -> List[AgentEvidence]:
    out: List[AgentEvidence] = []
    for ev in evidences:
        level = classify_model_match(query, ev)
        ev.model_match_level = level
        ev.metadata["model_match_level"] = level
        if level != "cross_family":
            out.append(ev)
    return out
