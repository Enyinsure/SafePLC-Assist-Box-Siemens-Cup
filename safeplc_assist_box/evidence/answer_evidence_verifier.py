#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional

from ..schemas import AgentClaim, AgentEvidence, JudgeDecision
from .claim_value_parser import find_numeric_mismatches, find_unit_mismatches, parse_claim_values
from .model_identity import classify_model_match


def verify_answer_evidence(
    final_answer: str,
    decision: JudgeDecision,
    evidences: Iterable[AgentEvidence],
) -> Dict[str, object]:
    evidence_by_id = {item.evidence_id: item for item in evidences}
    missing_ids = [item for item in decision.final_evidence_ids if item not in evidence_by_id]
    accepted = decision.metadata.get("accepted_claims", []) if isinstance(decision.metadata, dict) else []
    unsupported: List[str] = []
    model_mismatch: List[str] = []
    order_mismatch: List[str] = []
    numeric_mismatch: List[str] = []
    unit_mismatch: List[str] = []
    interface_mismatch: List[str] = []
    missing_figure: List[str] = []

    for value in accepted:
        claim = _coerce_claim(value)
        if claim is None:
            continue
        claim_evidence = [evidence_by_id[item] for item in claim.evidence_ids if item in evidence_by_id]
        if not claim_evidence:
            unsupported.append(claim.claim_id)
            continue
        claim_values = parse_claim_values(claim.claim_text)
        evidence_values = parse_claim_values(_evidence_text(claim_evidence))
        levels = [classify_model_match(claim.claim_text, item) for item in claim_evidence]
        if claim_values.models and not any(level in {"exact_order_number", "exact_model", "compatible_alias"} for level in levels):
            model_mismatch.append(claim.claim_id)
        if any(item.model_match_level == "cross_family" for item in claim_evidence):
            model_mismatch.append(claim.claim_id)
        if claim_values.order_numbers and not set(claim_values.order_numbers) & set(evidence_values.order_numbers):
            order_mismatch.append(claim.claim_id)
        if find_numeric_mismatches(claim_values, evidence_values):
            numeric_mismatch.append(claim.claim_id)
        if find_unit_mismatches(claim_values, evidence_values):
            unit_mismatch.append(claim.claim_id)
        if not set(claim_values.interfaces).issubset(set(evidence_values.interfaces)) or not set(
            claim_values.port_labels
        ).issubset(set(evidence_values.port_labels)):
            interface_mismatch.append(claim.claim_id)
        if claim.claim_type == "location" and not any(
            item.figure_id or item.figure_number or item.page is not None for item in claim_evidence
        ):
            missing_figure.append(claim.claim_id)
        if not _claim_has_text_support(claim.claim_text, claim_evidence):
            unsupported.append(claim.claim_id)

    final_values = parse_claim_values(final_answer)
    final_evidence_values = parse_claim_values(_evidence_text([evidence_by_id[item] for item in decision.final_evidence_ids if item in evidence_by_id]))
    if find_numeric_mismatches(final_values, final_evidence_values):
        numeric_mismatch.append("__final_answer__")
    if find_unit_mismatches(final_values, final_evidence_values):
        unit_mismatch.append("__final_answer__")

    raw_ocr = _raw_ocr_dump(final_answer)
    coverage_pass = bool(decision.metadata.get("coverage_pass", True)) if isinstance(decision.metadata, dict) else True
    model_pass = bool(decision.model_consistency.get("pass", True)) and not model_mismatch and not order_mismatch
    numeric_pass = not numeric_mismatch
    unit_pass = not unit_mismatch
    interface_pass = not interface_mismatch
    concise = len(final_answer or "") <= 900 and not raw_ocr
    figure_pass = bool(decision.metadata.get("figure_requirement_pass", True)) and not missing_figure
    failures = [
        missing_ids,
        unsupported,
        model_mismatch,
        order_mismatch,
        numeric_mismatch,
        unit_mismatch,
        interface_mismatch,
        missing_figure,
        raw_ocr,
        not coverage_pass,
        not model_pass,
        not numeric_pass,
        not unit_pass,
        not interface_pass,
        not concise,
        not figure_pass,
    ]
    return {
        "verifier": "answer_evidence_verifier_v3",
        "missing_evidence_ids": missing_ids,
        "unsupported_claim_ids": _unique(unsupported),
        "model_mismatch_claim_ids": _unique(model_mismatch),
        "order_number_mismatch_claim_ids": _unique(order_mismatch),
        "numeric_mismatch_claim_ids": _unique(numeric_mismatch),
        "unit_mismatch_claim_ids": _unique(unit_mismatch),
        "interface_mismatch_claim_ids": _unique(interface_mismatch),
        "missing_figure_claim_ids": _unique(missing_figure),
        "raw_ocr_dump_detected": raw_ocr,
        "coverage_pass": coverage_pass,
        "model_consistency_pass": model_pass,
        "numeric_consistency_pass": numeric_pass,
        "unit_consistency_pass": unit_pass,
        "interface_consistency_pass": interface_pass,
        "conciseness_pass": concise,
        "figure_requirement_pass": figure_pass,
        "has_text_support": bool(decision.final_evidence_ids) or decision.verdict in {"NEED_CLARIFICATION", "REFUSE", "ABSTAIN"},
        "has_page_or_figure": any(
            evidence_by_id[item].page is not None or evidence_by_id[item].figure_id or evidence_by_id[item].figure_number
            for item in decision.final_evidence_ids
            if item in evidence_by_id
        ),
        "unsupported_claims": list(decision.unsupported_claims),
        "pass": not any(bool(item) for item in failures) and bool(final_answer.strip()),
    }


def _coerce_claim(value) -> Optional[AgentClaim]:
    if isinstance(value, AgentClaim):
        return value
    if isinstance(value, dict):
        return AgentClaim(
            claim_id=str(value.get("claim_id", "")),
            claim_text=str(value.get("claim_text", "")),
            claim_type=str(value.get("claim_type", "")),
            evidence_ids=list(value.get("evidence_ids", []) or []),
            model_scope=str(value.get("model_scope", "")),
            confidence=str(value.get("confidence", "")),
            direct_support=bool(value.get("direct_support", False)),
            subquestion_ids=list(value.get("subquestion_ids", []) or []),
            metadata=dict(value.get("metadata", {}) or {}),
        )
    return None


def _evidence_text(evidences: List[AgentEvidence]) -> str:
    return " ".join(
        " ".join(
            filter(
                None,
                [
                    item.text,
                    item.module_model,
                    item.order_number,
                    f"page {item.page}" if item.page is not None else "",
                    item.figure_number,
                    item.figure_id,
                ],
            )
        )
        for item in evidences
    )


def _claim_has_text_support(claim_text: str, evidences: List[AgentEvidence]) -> bool:
    claim_tokens = set(re.findall(r"[A-Za-z][A-Za-z0-9_/\-]+|[\u4e00-\u9fff]{2,}", claim_text.lower()))
    ignored = {
        "supported", "evidence", "manual", "page", "guidance", "required", "site", "only", "conditions",
        "qualified", "review", "人工确认", "人工复核", "具备资质", "资料", "证据", "手册",
    }
    claim_tokens -= ignored
    if not claim_tokens:
        return True
    evidence_text = _evidence_text(evidences).lower()
    hits = sum(token in evidence_text for token in claim_tokens)
    return hits / len(claim_tokens) >= 0.2


def _raw_ocr_dump(text: str) -> bool:
    return len(text or "") > 900 or len(re.findall(r"\n", text or "")) > 12


def _unique(values: List[str]) -> List[str]:
    return list(dict.fromkeys(values))
