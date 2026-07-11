#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
from typing import Dict, List, Tuple

from ..schemas import (
    AgentClaim,
    AgentResult,
    AgentStatus,
    EvidencePool,
    JudgeConfidence,
    JudgeDecision,
    JudgeVerdict,
    QueryContext,
)
from .evidence_closed_synthesizer import EvidenceClosedSynthesizer


class JudgeAgent:
    role_description = "Claim-level evidence judge for support, coverage, model consistency and conflicts."

    def decide(
        self,
        query_context: QueryContext,
        results: List[AgentResult],
        evidence_pool: EvidencePool,
    ) -> JudgeDecision:
        evidence_by_id = {ev.evidence_id: ev for ev in evidence_pool.evidences}
        accepted_agents: List[str] = []
        rejected_agents: List[str] = []
        accepted_claims: List[AgentClaim] = []
        unsupported: List[str] = []
        conflicting = [str(group.get("reason", group)) for group in evidence_pool.conflicts if isinstance(group, dict)]
        quality_scores: Dict[str, float] = {}

        for result in results:
            if result.status == AgentStatus.REFUSE.value and result.evidence_ids:
                accepted_agents.append(result.agent_name)
                accepted_claims.extend(result.claims or [self._claim_from_result(result)])
                continue
            if result.status not in {AgentStatus.ANSWERED.value, AgentStatus.PARTIAL.value}:
                rejected_agents.append(result.agent_name)
                if result.abstain_reason:
                    unsupported.append(f"{result.agent_name}: {result.abstain_reason}")
                continue
            claims = result.claims or [self._claim_from_result(result)]
            claim_accept_count = 0
            for claim in claims:
                ok, reasons = self._validate_claim(query_context, claim, evidence_by_id)
                if ok:
                    accepted_claims.append(claim)
                    claim_accept_count += 1
                    for ev_id in claim.evidence_ids:
                        if ev_id in evidence_by_id:
                            quality_scores[ev_id] = evidence_by_id[ev_id].quality_score or evidence_by_id[ev_id].retrieval_score
                else:
                    unsupported.extend([f"{claim.claim_id}: {reason}" for reason in reasons])
            if claim_accept_count:
                accepted_agents.append(result.agent_name)
            else:
                rejected_agents.append(result.agent_name)

        final_ids = self._final_evidence_ids(accepted_claims, evidence_by_id)
        coverage = self._coverage(query_context, accepted_claims)
        coverage_pass = all(item["answered"] for item in coverage.values()) if coverage else bool(accepted_claims)
        model_consistency = self._model_consistency(query_context, accepted_claims, evidence_by_id)
        figure_required = "figure" in query_context.required_modalities or query_context.question_type == "FIGURE"
        figure_ok = not figure_required or any(
            (evidence_by_id.get(ev_id) and (evidence_by_id[ev_id].figure_id or evidence_by_id[ev_id].figure_number or evidence_by_id[ev_id].page))
            for ev_id in final_ids
        )
        safety_refusal = any(r.status == AgentStatus.REFUSE.value for r in results)

        if query_context.missing_slots or any(r.status == AgentStatus.NEED_CLARIFICATION.value for r in results):
            verdict = JudgeVerdict.NEED_CLARIFICATION.value
            confidence = JudgeConfidence.NOT_AVAILABLE.value
            reason = "Required slots are missing."
        elif safety_refusal:
            verdict = JudgeVerdict.REFUSE.value
            confidence = JudgeConfidence.HIGH.value if final_ids else JudgeConfidence.NOT_AVAILABLE.value
            reason = "Dangerous industrial operation refused with operation-boundary evidence."
        elif evidence_pool.conflicts:
            verdict = JudgeVerdict.CONFLICT.value
            confidence = JudgeConfidence.CONFLICT.value
            reason = "Evidence pool contains conflicts."
        elif not accepted_claims:
            verdict = JudgeVerdict.NEED_MORE_EVIDENCE.value
            confidence = JudgeConfidence.NOT_AVAILABLE.value
            reason = "No claim passed evidence support checks."
        elif not model_consistency["pass"]:
            verdict = JudgeVerdict.REVIEW.value
            confidence = JudgeConfidence.LOW.value
            reason = "Model or order-number consistency check failed."
        elif not coverage_pass or not figure_ok:
            verdict = JudgeVerdict.PARTIAL.value
            confidence = JudgeConfidence.MEDIUM.value if final_ids else JudgeConfidence.LOW.value
            reason = "Some subquestions or required figure evidence are not covered."
        elif unsupported:
            verdict = JudgeVerdict.REVIEW.value
            confidence = JudgeConfidence.MEDIUM.value
            reason = "Accepted evidence exists, but some agent claims were rejected."
        else:
            verdict = JudgeVerdict.PASS.value
            confidence = JudgeConfidence.HIGH.value if len(final_ids) >= 1 else JudgeConfidence.LOW.value
            reason = "All accepted claims are supported by Evidence Pool records."

        final_answer = EvidenceClosedSynthesizer().synthesize(query_context, accepted_claims, evidence_by_id, verdict)
        return JudgeDecision(
            accepted_agent_outputs=list(dict.fromkeys(accepted_agents)),
            rejected_agent_outputs=list(dict.fromkeys(rejected_agents)),
            conflict_groups=list(evidence_pool.conflicts),
            supported_claims=[claim.claim_text for claim in accepted_claims],
            unsupported_claims=unsupported,
            conflicting_claims=conflicting,
            final_evidence_ids=final_ids,
            need_more_evidence=verdict == JudgeVerdict.NEED_MORE_EVIDENCE.value,
            need_clarification=verdict == JudgeVerdict.NEED_CLARIFICATION.value,
            final_answer=final_answer,
            verdict=verdict,
            confidence=confidence,
            decision_reason=reason,
            coverage=coverage,
            model_consistency=model_consistency,
            quality_scores=quality_scores,
            metadata={
                "judge_role": self.role_description,
                "accepted_claims": [claim for claim in accepted_claims],
                "coverage_pass": coverage_pass,
                "figure_requirement_pass": figure_ok,
            },
        )

    def _validate_claim(
        self,
        query_context: QueryContext,
        claim: AgentClaim,
        evidence_by_id: Dict[str, object],
    ) -> Tuple[bool, List[str]]:
        reasons: List[str] = []
        if not claim.evidence_ids:
            reasons.append("missing_evidence_ids")
        claim_text = claim.claim_text or ""
        if self._raw_ocr_dump(claim_text):
            reasons.append("raw_ocr_dump_detected")
        for ev_id in claim.evidence_ids:
            ev = evidence_by_id.get(ev_id)
            if not ev:
                reasons.append(f"unknown_evidence_id:{ev_id}")
                continue
            if getattr(ev, "model_match_level", "") == "cross_family":
                reasons.append(f"cross_family_evidence:{ev_id}")
            if claim.claim_type == "location" and not (ev.figure_id or ev.figure_number or ev.page):
                reasons.append(f"missing_figure_reference:{ev_id}")
            if claim.claim_type == "parameter" and not (ev.parameter or ev.text):
                reasons.append(f"parameter_not_located:{ev_id}")
        if query_context.question_type == "FIGURE" and claim.claim_type == "location" and not claim.direct_support:
            reasons.append("figure_claim_without_direct_support")
        return not reasons, reasons

    def _coverage(self, query_context: QueryContext, claims: List[AgentClaim]) -> Dict[str, Dict[str, object]]:
        coverage: Dict[str, Dict[str, object]] = {}
        for subq in query_context.subquestions:
            supporting = [claim for claim in claims if subq.subquestion_id in claim.subquestion_ids]
            coverage[subq.subquestion_id] = {
                "answered": bool(supporting),
                "supporting_claim_ids": [claim.claim_id for claim in supporting],
                "supporting_evidence_ids": list(dict.fromkeys(ev_id for claim in supporting for ev_id in claim.evidence_ids)),
            }
        return coverage

    def _model_consistency(
        self,
        query_context: QueryContext,
        claims: List[AgentClaim],
        evidence_by_id: Dict[str, object],
    ) -> Dict[str, object]:
        rejected: List[str] = []
        levels: Dict[str, str] = {}
        for claim in claims:
            for ev_id in claim.evidence_ids:
                ev = evidence_by_id.get(ev_id)
                if not ev:
                    continue
                level = getattr(ev, "model_match_level", "unknown")
                levels[ev_id] = level
                if level == "cross_family":
                    rejected.append(ev_id)
        identity = query_context.metadata.get("model_identity", {}) if isinstance(query_context.metadata, dict) else {}
        return {
            "expected_model": ", ".join(identity.get("models", []) or []),
            "accepted_levels": levels,
            "rejected_evidence_ids": rejected,
            "pass": not rejected,
        }

    def _final_evidence_ids(self, claims: List[AgentClaim], evidence_by_id: Dict[str, object]) -> List[str]:
        ids: List[str] = []
        for claim in claims:
            for ev_id in claim.evidence_ids:
                if ev_id in evidence_by_id and ev_id not in ids:
                    ids.append(ev_id)
        return ids[:6]

    def _raw_ocr_dump(self, text: str) -> bool:
        if len(text or "") > 900:
            return True
        return len(re.findall(r"\n", text or "")) > 12

    def _claim_from_result(self, result: AgentResult) -> AgentClaim:
        return AgentClaim(
            claim_id=f"claim_{result.task_id}",
            claim_text=result.answer_fragment,
            claim_type="grounded_qa",
            evidence_ids=list(result.evidence_ids),
            confidence=result.confidence,
            direct_support=bool(result.evidence_ids),
        )
