#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Dict, Iterable, List

from ..schemas import AgentEvidence, JudgeDecision


def verify_answer_evidence(
    final_answer: str,
    decision: JudgeDecision,
    evidences: Iterable[AgentEvidence],
) -> Dict[str, object]:
    evidence_by_id = {ev.evidence_id: ev for ev in evidences}
    missing_ids = [
        ev_id for ev_id in decision.final_evidence_ids if ev_id not in evidence_by_id
    ]
    evidence_text = "\n".join(
        evidence_by_id[ev_id].text for ev_id in decision.final_evidence_ids if ev_id in evidence_by_id
    )
    has_text_support = bool(evidence_text.strip())
    has_page_or_figure = any(
        evidence_by_id[ev_id].page is not None or evidence_by_id[ev_id].figure_id
        for ev_id in decision.final_evidence_ids
        if ev_id in evidence_by_id
    )

    return {
        "verifier": "answer_evidence_verifier",
        "missing_evidence_ids": missing_ids,
        "has_text_support": has_text_support,
        "has_page_or_figure": has_page_or_figure,
        "unsupported_claims": list(decision.unsupported_claims),
        "pass": (
            not missing_ids
            and has_text_support
            and not decision.unsupported_claims
            and bool(final_answer.strip())
        ),
    }

