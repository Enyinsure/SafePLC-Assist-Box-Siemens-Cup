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
    normalized_model: str = ""
    product_type: str = ""
    device_family: str = ""
    model_name: str = ""
    variant: str = ""
    order_numbers: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    normalized_models: List[str] = field(default_factory=list)
    family_hints: List[str] = field(default_factory=list)


def normalize_text(text: str) -> str:
    value = unicodedata.normalize("NFKC", text or "").upper()
    value = re.sub(r"[‐‑‒–—−]", "-", value)
    value = value.replace("／", "/")
    value = re.sub(r"\s*/\s*", "/", value)
    value = re.sub(r"\s*-\s*", "-", value)
    value = re.sub(r"\s+", " ", value)
    value = value.replace("PN DP", "PN/DP").replace("PN-DP", "PN/DP")
    return value.strip()


def normalize_model(text: str) -> str:
    identity = extract_model_identity(text)
    return identity.normalized_model or normalize_text(text)


def extract_order_numbers(text: str) -> List[str]:
    normalized = normalize_text(text)
    return list(dict.fromkeys(re.findall(r"\b6ES7[A-Z0-9-]{5,}\b", normalized)))


def extract_model_identity(text: str) -> ModelIdentity:
    normalized = normalize_text(text)
    orders = extract_order_numbers(normalized)
    model = ""
    product_type = ""
    family = ""
    variant = ""
    aliases: List[str] = []

    cpu = re.search(
        r"(?:CPU\s*)?(15(?:11|13|15|16|17|18)(?:-\d)?)\s*(PN/DP|PN|DP|HF|H)?\b",
        normalized,
    )
    if cpu:
        base = cpu.group(1)
        variant = (cpu.group(2) or "").strip()
        if base == "1517-3" and variant == "PN":
            aliases = ["CPU 1517-3 PN", "CPU 1517-3 PN/DP"]
            variant = "PN/DP"
        model = f"CPU {base}" + (f" {variant}" if variant else "")
        product_type = "CPU"
        family = "S7-1500R/H" if variant in {"H", "HF"} else "S7-1500"
    if not model:
        et = re.search(r"ET\s*200\s*(MP|SP)\b", normalized)
        if et:
            variant = et.group(1)
            model = f"ET 200{variant}"
            product_type = "ET"
            family = model
    if not model:
        ps = re.search(
            r"\b(PS|PM)\s+((?:\d+\s*W\s+)?[\d/]+\s*VDC(?:\s+HF)?|[A-Z0-9][A-Z0-9./-]*(?:\s+[A-Z0-9][A-Z0-9./-]*){0,3})",
            normalized,
        )
        if ps:
            product_type = ps.group(1)
            model = re.sub(r"\s+", " ", f"{product_type} {ps.group(2).strip()}")
            variant = "HF" if re.search(r"\bHF\b", model) else ""
            family = "S7-1500 POWER"
    if not model:
        module = re.search(r"\b(SM|IM|CM|CP|TM)\b\s*([A-Z0-9-]+)?(?:\s+(DI|DQ|AI|AQ))?\b", normalized)
        if module:
            product_type = module.group(1)
            suffix = " ".join(part for part in (module.group(2), module.group(3)) if part)
            model = f"{product_type} {suffix}".strip()
            variant = module.group(3) or ""
            family = "S7-1500 MODULE"

    if is_redundant_family_text(normalized):
        family = "S7-1500R/H"
    elif not family and "S7-1500" in normalized:
        family = "S7-1500"
    family_hints = [family] if family else []
    if "S7-1500" in normalized and "S7-1500" not in family_hints:
        family_hints.append("S7-1500")
    normalized_models = [model] if model else []
    if model and not aliases:
        aliases = [model]
    return ModelIdentity(
        raw_text=text,
        normalized_model=model,
        product_type=product_type,
        device_family=family,
        model_name=model,
        variant=variant,
        order_numbers=orders,
        aliases=list(dict.fromkeys(aliases)),
        normalized_models=normalized_models,
        family_hints=list(dict.fromkeys(family_hints)),
    )


def is_redundant_family_text(text: str) -> bool:
    normalized = normalize_text(text)
    return bool(
        re.search(r"S7[- ]?1500\s*R/H", normalized)
        or re.search(r"\b15(?:17|18)\s*H(?:F)?\b", normalized)
        or re.search(r"\bCPU\s*15(?:17|18)H(?:F)?\b", normalized)
        or "R/H" in normalized
    )


def classify_model_match(query: str, evidence: AgentEvidence) -> str:
    expected = extract_model_identity(query)
    actual = extract_model_identity(evidence.module_model or evidence.module or "")
    secondary = extract_model_identity(
        " ".join(
            [
                evidence.module_model or "",
                evidence.order_number or "",
                evidence.text or "",
                evidence.compact_excerpt or "",
                evidence.manual_title or "",
                evidence.source or "",
            ]
        )
    )
    actual.order_numbers = list(dict.fromkeys(actual.order_numbers + secondary.order_numbers))
    actual.family_hints = list(dict.fromkeys(actual.family_hints + secondary.family_hints))
    if not actual.normalized_model and secondary.normalized_model:
        actual.normalized_model = secondary.normalized_model
        actual.normalized_models = secondary.normalized_models
        actual.aliases = secondary.aliases
        actual.product_type = secondary.product_type
        actual.device_family = secondary.device_family
        actual.variant = secondary.variant
    if expected.order_numbers:
        if set(expected.order_numbers) & set(actual.order_numbers):
            return "exact_order_number"
        if actual.order_numbers:
            return "cross_family"
    if expected.device_family == "S7-1500" and actual.device_family == "S7-1500R/H":
        return "cross_family"
    if expected.device_family == "S7-1500R/H" and actual.device_family == "S7-1500":
        return "cross_family"
    if expected.normalized_model:
        if actual.normalized_model == expected.normalized_model:
            return "exact_model"
        if set(expected.aliases) & set(actual.aliases):
            return "compatible_alias"
        if actual.normalized_model:
            return "cross_family"
        if expected.device_family and expected.device_family in actual.family_hints:
            return "same_family_general"
        return "unknown"
    if expected.device_family and actual.device_family:
        return "same_family_general" if expected.device_family in actual.family_hints else "cross_family"
    if actual.device_family:
        return "same_family_general"
    return "unknown"


def reject_cross_family(evidences: Iterable[AgentEvidence], query: str) -> List[AgentEvidence]:
    accepted: List[AgentEvidence] = []
    for evidence in evidences:
        level = classify_model_match(query, evidence)
        evidence.model_match_level = level
        evidence.metadata["model_match_level"] = level
        evidence.metadata["model_identity"] = extract_model_identity(evidence.module_model or evidence.text).__dict__
        if level != "cross_family":
            accepted.append(evidence)
    return accepted
