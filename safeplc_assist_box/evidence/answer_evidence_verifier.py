#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
from typing import Dict, Iterable, List

from ..schemas import AgentClaim, AgentEvidence, JudgeDecision


def verify_answer_evidence(
    final_answer: str,
    decision: JudgeDecision,
    evidences: Iterable[AgentEvidence],
) -> Dict[str, object]:
    evidence_by_id = {ev.evidence_id: ev for ev in evidences}
    missing_ids = [ev_id for ev_id in decision.final_evidence_ids if ev_id not in evidence_by_id]
    accepted_claims = decision.metadata.get("accepted_claims", []) if isinstance(decision.metadata, dict) else []
    unsupported_claim_ids: List[str] = []
    model_mismatch_claim_ids: List[str] = []
    numeric_mismatch_claim_ids: List[str] = []
    missing_figure_claim_ids: List[str] = []

    for raw_claim in accepted_claims:
        claim = _coerce_claim(raw_claim)
        if claim is None:
            continue
        claim_evidence = [evidence_by_id[ev_id] for ev_id in claim.evidence_ids if ev_id in evidence_by_id]
        if not claim_evidence:
            unsupported_claim_ids.append(claim.claim_id)
            continue
        if any(ev.model_match_level == "cross_family" for ev in claim_evidence):
            model_mismatch_claim_ids.append(claim.claim_id)
        if claim.claim_type == "location" and not any(ev.figure_id or ev.figure_number or ev.page for ev in claim_evidence):
            missing_figure_claim_ids.append(claim.claim_id)
        if _numeric_mismatch(claim.claim_text, claim_evidence):
            numeric_mismatch_claim_ids.append(claim.claim_id)

    raw_ocr_dump_detected = _raw_ocr_dump(final_answer)
    coverage_pass = bool(decision.metadata.get("coverage_pass", True)) if isinstance(decision.metadata, dict) else True
    model_consistency_pass = bool(decision.model_consistency.get("pass", True))
    conciseness_pass = len(final_answer or "") <= 900 and not raw_ocr_dump_detected
    figure_requirement_pass = bool(decision.metadata.get("figure_requirement_pass", True)) if isinstance(decision.metadata, dict) else True
    critical_fail = any(
        [
            missing_ids,
            unsupported_claim_ids,
            model_mismatch_claim_ids,
            numeric_mismatch_claim_ids,
            missing_figure_claim_ids,
            raw_ocr_dump_detected,
            not coverage_pass,
            not model_consistency_pass,
            not conciseness_pass,
            not figure_requirement_pass,
        ]
    )

    return {
        "verifier": "answer_evidence_verifier_v2",
        "missing_evidence_ids": missing_ids,
        "unsupported_claim_ids": unsupported_claim_ids,
        "model_mismatch_claim_ids": model_mismatch_claim_ids,
        "numeric_mismatch_claim_ids": numeric_mismatch_claim_ids,
        "missing_figure_claim_ids": missing_figure_claim_ids,
        "raw_ocr_dump_detected": raw_ocr_dump_detected,
        "coverage_pass": coverage_pass,
        "model_consistency_pass": model_consistency_pass,
        "conciseness_pass": conciseness_pass,
        "figure_requirement_pass": figure_requirement_pass,
        "has_text_support": bool(decision.final_evidence_ids) or decision.verdict in {"NEED_CLARIFICATION", "REFUSE"},
        "has_page_or_figure": any(
            evidence_by_id[ev_id].page is not None or evidence_by_id[ev_id].figure_id or evidence_by_id[ev_id].figure_number
            for ev_id in decision.final_evidence_ids
            if ev_id in evidence_by_id
        ),
        "unsupported_claims": list(decision.unsupported_claims),
        "pass": not critical_fail and bool(final_answer.strip()),
    }


def _coerce_claim(value) -> AgentClaim | None:
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


def _numeric_mismatch(claim_text: str, evidences: List[AgentEvidence]) -> bool:
    numbers = re.findall(r"\b\d+(?:\.\d+)?\b", claim_text or "")
    if not numbers:
        return False
    evidence_text = " ".join(
        " ".join(
            [
                ev.text,
                str(ev.page or ""),
                ev.figure_number,
                ev.figure_id,
                ev.order_number,
                ev.module_model,
            ]
        )
        for ev in evidences
    )
    return any(number not in evidence_text for number in numbers)


def _raw_ocr_dump(text: str) -> bool:
    if len(text or "") > 900:
        return True
    return len(re.findall(r"\n", text or "")) > 12
