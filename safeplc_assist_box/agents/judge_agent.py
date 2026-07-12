#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
from typing import Dict, List, Tuple

from ..evidence.claim_value_parser import find_numeric_mismatches, find_unit_mismatches, parse_claim_values
from ..evidence.fact_extractors import has_wiring_normative_predicate
from ..evidence.model_identity import classify_model_match, extract_model_identity
from ..schemas import AgentClaim, AgentResult, AgentStatus, EvidencePool, JudgeConfidence, JudgeDecision, JudgeVerdict, QueryContext
from .evidence_closed_synthesizer import EvidenceClosedSynthesizer
from ..retrieval.query_expander import is_explicit_image_request


class JudgeAgent:
    role_description = "Claim-level evidence judge for coverage, support, identity, values, figures and conflicts."

    def decide(self, query_context: QueryContext, results: List[AgentResult], evidence_pool: EvidencePool) -> JudgeDecision:
        evidence_by_id = {item.evidence_id: item for item in evidence_pool.evidences}
        accepted_agents: List[str] = []
        rejected_agents: List[str] = []
        accepted_claims: List[AgentClaim] = []
        unsupported: List[str] = []
        all_claim_count = 0

        for result in results:
            if result.status == AgentStatus.REFUSE.value:
                accepted_agents.append(result.agent_name)
                accepted_claims.extend(result.claims)
                continue
            if result.status not in {AgentStatus.ANSWERED.value, AgentStatus.PARTIAL.value}:
                rejected_agents.append(result.agent_name)
                if result.abstain_reason:
                    unsupported.append(f"{result.agent_name}: {result.abstain_reason}")
                continue
            result_claims = result.claims or [self._claim_from_result(result)]
            all_claim_count += len(result_claims)
            accepted_for_agent = 0
            for claim in result_claims:
                reasons = self._validate_claim(query_context, claim, evidence_by_id)
                if reasons:
                    unsupported.extend(f"{claim.claim_id}: {reason}" for reason in reasons)
                else:
                    accepted_claims.append(claim)
                    accepted_for_agent += 1
            (accepted_agents if accepted_for_agent else rejected_agents).append(result.agent_name)

        coverage = self._coverage(query_context, accepted_claims)
        coverage_score = (
            sum(bool(item["answered"]) for item in coverage.values()) / len(coverage) if coverage else float(bool(accepted_claims))
        )
        final_ids = self._final_evidence_ids(accepted_claims, evidence_by_id)
        final_evidence = [evidence_by_id[item] for item in final_ids]
        model_consistency = self._model_consistency(query_context, final_evidence)
        figure_state = self._figure_state(query_context, final_evidence, evidence_pool)
        conflicting = [str(item.get("reason", item)) for item in evidence_pool.conflicts if isinstance(item, dict)]
        refusal = any(result.status == AgentStatus.REFUSE.value for result in results)
        all_abstained = bool(results) and all(result.status == AgentStatus.ABSTAIN.value for result in results)
        grounding_score = len(accepted_claims) / max(1, all_claim_count)
        quality_scores = self._quality_scores(
            coverage_score,
            grounding_score,
            model_consistency,
            figure_state,
            accepted_claims,
            final_evidence,
            unsupported,
        )

        if query_context.missing_slots or any(item.status == AgentStatus.NEED_CLARIFICATION.value for item in results):
            verdict, confidence, reason = JudgeVerdict.NEED_CLARIFICATION.value, JudgeConfidence.NOT_AVAILABLE.value, "Required model, order number, interface or context is missing."
        elif refusal:
            verdict, confidence, reason = JudgeVerdict.REFUSE.value, JudgeConfidence.HIGH.value, "Dangerous industrial operation refused; no executable bypass steps are allowed."
        elif evidence_pool.conflicts:
            verdict, confidence, reason = JudgeVerdict.CONFLICT.value, JudgeConfidence.CONFLICT.value, "Evidence contains an unresolved same-scope conflict."
        elif not accepted_claims and all_abstained:
            audit = evidence_pool.metadata.get("retrieval_backend_audit", {}) if isinstance(evidence_pool.metadata, dict) else {}
            backend_active = bool(audit.get("text_backend_active") or audit.get("figure_backend_active") or audit.get("jsonl_fallback_active")) if isinstance(audit, dict) else False
            if backend_active:
                verdict, confidence, reason = JudgeVerdict.ABSTAIN.value, JudgeConfidence.NOT_AVAILABLE.value, "Retrieval completed but no reliable claim could be supported."
            else:
                verdict, confidence, reason = JudgeVerdict.NEED_MORE_EVIDENCE.value, JudgeConfidence.NOT_AVAILABLE.value, "No FULL retrieval backend is available; configure collection and embedding before retrying."
        elif not accepted_claims:
            verdict, confidence, reason = JudgeVerdict.NEED_MORE_EVIDENCE.value, JudgeConfidence.NOT_AVAILABLE.value, "No claim passed evidence checks; a bounded retrieval retry may be useful."
        elif not model_consistency["pass"]:
            verdict, confidence, reason = JudgeVerdict.ABSTAIN.value, JudgeConfidence.LOW.value, "Model or order-number scope is inconsistent."
        elif coverage_score < 0.9 or unsupported or figure_state["missing_required_image"] or any(
            self._claim_has_partial_coverage(claim) for claim in accepted_claims
        ):
            verdict, confidence, reason = JudgeVerdict.PARTIAL.value, JudgeConfidence.MEDIUM.value, "Only the covered, evidence-supported portion can be answered."
        elif quality_scores["grounding"] >= 0.9 and quality_scores["model_consistency"] >= 0.95:
            verdict = JudgeVerdict.PASS.value
            confidence = JudgeConfidence.MEDIUM.value if (
                model_consistency["unknown_evidence_ids"] or figure_state["limited_to_page_text"]
            ) else JudgeConfidence.HIGH.value
            reason = "Coverage and claim-level evidence checks passed."
        else:
            verdict, confidence, reason = JudgeVerdict.PARTIAL.value, JudgeConfidence.MEDIUM.value, "Evidence is usable but does not meet full PASS thresholds."

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
                "accepted_claims": accepted_claims,
                "coverage_pass": coverage_score >= 0.9,
                "figure_requirement_pass": figure_state["pass"],
                "figure_state": figure_state,
            },
        )

    def _validate_claim(self, context: QueryContext, claim: AgentClaim, evidence_by_id: Dict[str, object]) -> List[str]:
        reasons: List[str] = []
        if not claim.evidence_ids:
            return ["missing_evidence_ids"]
        if context.subquestions and not claim.subquestion_ids:
            reasons.append("missing_subquestion_scope")
        if self._raw_ocr_dump(claim.claim_text):
            reasons.append("raw_ocr_dump_detected")
        evidences = [evidence_by_id[item] for item in claim.evidence_ids if item in evidence_by_id]
        missing = [item for item in claim.evidence_ids if item not in evidence_by_id]
        reasons.extend(f"unknown_evidence_id:{item}" for item in missing)
        if not evidences:
            return reasons or ["missing_evidence"]
        levels = [classify_model_match(f"{claim.model_scope} {context.original_query}", item) for item in evidences]
        if any(level == "cross_family" for level in levels):
            reasons.append("cross_family_evidence")
        query_identity = extract_model_identity(context.original_query)
        model_specific_query = bool(query_identity.normalized_model or query_identity.order_numbers)
        if model_specific_query and any(level == "same_family_general" for level in levels) and not claim.metadata.get("general_guidance"):
            reasons.append("same_family_general_used_for_model_specific_claim")
        claim_values = parse_claim_values(claim.claim_text)
        evidence_values = parse_claim_values(" ".join(self._evidence_text(item) for item in evidences))
        if claim_values.order_numbers and not set(claim_values.order_numbers) & set(evidence_values.order_numbers):
            reasons.append("order_number_mismatch")
        if find_numeric_mismatches(claim_values, evidence_values):
            reasons.append("numeric_mismatch")
        if find_unit_mismatches(claim_values, evidence_values):
            reasons.append("unit_mismatch")
        if not set(claim_values.interfaces).issubset(set(evidence_values.interfaces)) or not set(
            claim_values.port_labels
        ).issubset(set(evidence_values.port_labels)):
            reasons.append("interface_or_port_mismatch")
        if claim.claim_type == "location" and not any(item.figure_id or item.figure_number or item.page is not None for item in evidences):
            reasons.append("missing_figure_reference")
        if context.question_type == "FIGURE" and claim.claim_type == "location" and not claim.direct_support:
            reasons.append("figure_claim_without_direct_support")
        if claim.claim_type in {"connection", "wiring"} or claim.metadata.get("fact_type") == "wiring_requirement":
            if self._low_information_wiring_claim(claim.claim_text):
                reasons.append("low_information_heading_fragment")
        if claim.metadata.get("fact_type") == "led_checklist" and not claim.direct_support:
            reasons.append("led_checklist_without_direct_support")
        if not self._text_support(claim.claim_text, evidences):
            reasons.append("claim_core_terms_not_supported")
        return list(dict.fromkeys(reasons))

    def _claim_has_partial_coverage(self, claim: AgentClaim) -> bool:
        if claim.metadata.get("partial_coverage"):
            return True
        if claim.metadata.get("fact_type") != "led_checklist":
            return False
        expected = claim.metadata.get("expected_led_groups") or [
            "RUN/STOP LED", "ERROR LED", "MAINT LED",
            "X1 P1 LINK RX/TX LED", "X1 P2 LINK RX/TX LED",
        ]
        found = claim.metadata.get("found_led_groups") or []
        return bool(set(expected) - set(found))

    def _low_information_wiring_claim(self, text: str) -> bool:
        value = str(text or "").strip()
        nouns = re.findall(r"接线|端子|接口|分配|图|说明", value)
        return bool(nouns) and not has_wiring_normative_predicate(value)

    def _coverage(self, context: QueryContext, claims: List[AgentClaim]) -> Dict[str, Dict[str, object]]:
        return {
            subquestion.subquestion_id: {
                "answered": bool(supporting := [claim for claim in claims if subquestion.subquestion_id in claim.subquestion_ids]),
                "supporting_claim_ids": [claim.claim_id for claim in supporting],
                "supporting_evidence_ids": list(dict.fromkeys(item for claim in supporting for item in claim.evidence_ids)),
            }
            for subquestion in context.subquestions
        }

    def _model_consistency(self, context: QueryContext, evidences: List[object]) -> Dict[str, object]:
        levels = {item.evidence_id: classify_model_match(context.original_query, item) for item in evidences}
        cross = [item for item, level in levels.items() if level == "cross_family"]
        unknown = [item for item, level in levels.items() if level == "unknown"]
        identity = extract_model_identity(context.original_query)
        accepted_models = list(dict.fromkeys(item.module_model for item in evidences if item.module_model and item.evidence_id not in cross))
        rejected_models = list(dict.fromkeys(item.module_model for item in evidences if item.evidence_id in cross and item.module_model))
        return {
            "expected_model": identity.normalized_model,
            "expected_order_numbers": identity.order_numbers,
            "accepted_models": accepted_models,
            "rejected_models": rejected_models,
            "accepted_levels": levels,
            "cross_family_evidence_ids": cross,
            "unknown_evidence_ids": unknown,
            "pass": not cross,
        }

    def _figure_state(self, context: QueryContext, evidences: List[object], pool: EvidencePool) -> Dict[str, object]:
        location_information_required = context.question_type == "FIGURE" or any(
            term in context.original_query.lower() for term in ("哪里", "在哪", "位置", "where", "location")
        )
        visual_image_required = is_explicit_image_request(context.original_query)
        required = location_information_required or visual_image_required
        audit = pool.metadata.get("retrieval_backend_audit", {}) if isinstance(pool.metadata, dict) else {}
        figure_backend_active = bool(audit.get("figure_backend_active")) if isinstance(audit, dict) else False
        chroma_figure = any(item.retrieval_backend == "chroma_figure" for item in evidences)
        image = any(item.image_exists or item.visual_evidence_status == "image_available" for item in evidences)
        page_text = any(
            item.visual_evidence_status == "page_text_only" and (item.page is not None or item.figure_id or item.figure_number)
            for item in evidences
        )
        location_complete = not location_information_required or bool(image or page_text)
        image_complete = not visual_image_required or image
        complete = bool(location_complete and image_complete)
        return {
            "required": required,
            "location_information_required": location_information_required,
            "visual_image_required": visual_image_required,
            "figure_backend_active": figure_backend_active,
            "chroma_figure_present": chroma_figure,
            "image_available": image,
            "page_text_only_present": page_text,
            "limited_to_page_text": bool(location_information_required and page_text and not image),
            "missing_required_image": bool(visual_image_required and not image),
            "pass": complete,
        }

    def _quality_scores(self, coverage: float, grounding: float, model: Dict[str, object], figure: Dict[str, object], claims: List[AgentClaim], evidences: List[object], unsupported: List[str]) -> Dict[str, float]:
        all_text = " ".join(claim.claim_text for claim in claims)
        parser = parse_claim_values(all_text)
        evidence_parser = parse_claim_values(" ".join(self._evidence_text(item) for item in evidences))
        numeric = 1.0 if not find_numeric_mismatches(parser, evidence_parser) else 0.0
        units = 1.0 if not find_unit_mismatches(parser, evidence_parser) else 0.0
        interfaces = 1.0 if set(parser.interfaces).issubset(set(evidence_parser.interfaces)) and set(parser.port_labels).issubset(set(evidence_parser.port_labels)) else 0.0
        model_score = 0.0 if model["cross_family_evidence_ids"] else 0.7 if model["unknown_evidence_ids"] else 1.0
        return {
            "coverage": round(coverage, 4),
            "grounding": round(grounding, 4),
            "model_consistency": model_score,
            "order_number_consistency": 1.0,
            "numeric_consistency": numeric,
            "unit_consistency": units,
            "interface_consistency": interfaces,
            "figure_completeness": 1.0 if figure["pass"] and not figure["limited_to_page_text"] else 0.6 if figure["pass"] else 0.0,
            "relevance": round(sum(item.quality_score for item in evidences) / max(1, len(evidences)), 4),
            "directness": round(sum(bool(claim.direct_support) for claim in claims) / max(1, len(claims)), 4),
            "conciseness": 1.0 if len(all_text) <= 700 and not self._raw_ocr_dump(all_text) else 0.0,
        }

    def _final_evidence_ids(self, claims: List[AgentClaim], evidence_by_id: Dict[str, object]) -> List[str]:
        return list(dict.fromkeys(item for claim in claims for item in claim.evidence_ids if item in evidence_by_id))[:8]

    def _text_support(self, claim_text: str, evidences: List[object]) -> bool:
        tokens = set(re.findall(r"[A-Za-z][A-Za-z0-9_/\-]+|[\u4e00-\u9fff]{2,}", claim_text.lower()))
        tokens -= {
            "supported", "evidence", "guidance", "manual", "page", "target", "required", "site", "only",
            "conditions", "qualified", "review", "人工确认", "人工复核", "具备资质", "资料", "证据", "手册",
        }
        if not tokens:
            return True
        evidence_text = " ".join(self._evidence_text(item) for item in evidences).lower()
        return sum(token in evidence_text for token in tokens) / len(tokens) >= 0.2

    def _evidence_text(self, evidence: object) -> str:
        return " ".join(
            filter(
                None,
                [
                    evidence.text,
                    evidence.module_model,
                    evidence.order_number,
                    f"page {evidence.page}" if evidence.page is not None else "",
                    evidence.figure_number,
                    evidence.figure_id,
                ],
            )
        )

    def _raw_ocr_dump(self, text: str) -> bool:
        return len(text or "") > 900 or len(re.findall(r"\n", text or "")) > 12

    def _claim_from_result(self, result: AgentResult) -> AgentClaim:
        return AgentClaim(
            claim_id=f"claim_{result.task_id}",
            claim_text=result.answer_fragment,
            claim_type="grounded_qa",
            evidence_ids=list(result.evidence_ids),
            confidence=result.confidence,
            direct_support=bool(result.evidence_ids),
        )
