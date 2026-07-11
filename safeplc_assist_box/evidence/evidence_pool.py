#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import hashlib
import re
from difflib import SequenceMatcher
from typing import Dict, Iterable, List, Optional, Set, Tuple

from ..schemas import AgentEvidence, EvidencePool


class SharedEvidencePool:
    """Evidence store with deterministic cross-backend deduplication and scoped conflicts."""

    def __init__(self) -> None:
        self._items: Dict[str, AgentEvidence] = {}
        self._normalized_text_to_id: Dict[str, str] = {}
        self.agent_claims: Dict[str, List[str]] = {}
        self.conflicts: List[Dict[str, object]] = []
        self.rejected_evidence: List[Dict[str, object]] = []

    def add(self, evidence: AgentEvidence, agent_name: str, claim: str = "") -> str:
        evidence = self._with_stable_id(evidence)
        duplicate_id, reason = self._find_duplicate(evidence, claim)
        if duplicate_id:
            self._merge_into(duplicate_id, evidence, agent_name, claim, reason)
            return duplicate_id
        if agent_name and agent_name not in evidence.agent_names:
            evidence.agent_names.append(agent_name)
        if claim and claim not in evidence.claim_links:
            evidence.claim_links.append(claim)
        evidence.metadata.setdefault("merged_evidence_ids", [evidence.evidence_id])
        evidence.metadata.setdefault("merged_backends", [evidence.retrieval_backend] if evidence.retrieval_backend else [])
        evidence.metadata.setdefault("merged_sources", [evidence.source] if evidence.source else [])
        self._items[evidence.evidence_id] = evidence
        self._normalized_text_to_id[_normalized_text(evidence.text)] = evidence.evidence_id
        self._detect_conflicts(evidence)
        return evidence.evidence_id

    def add_many(self, evidences: Iterable[AgentEvidence], agent_name: str, claim: str = "") -> List[str]:
        result: List[str] = []
        for evidence in evidences:
            evidence_id = self.add(evidence, agent_name, claim)
            if evidence_id not in result:
                result.append(evidence_id)
        return result

    def add_agent_claim(self, agent_name: str, claim: str) -> None:
        if claim:
            self.agent_claims.setdefault(agent_name, [])
            if claim not in self.agent_claims[agent_name]:
                self.agent_claims[agent_name].append(claim)

    def record_conflict(self, evidence_ids: List[str], reason: str, agents: Optional[List[str]] = None) -> None:
        key = (tuple(sorted(evidence_ids)), reason)
        if any((tuple(sorted(item["evidence_ids"])), item["reason"]) == key for item in self.conflicts):
            return
        self.conflicts.append({"evidence_ids": evidence_ids, "reason": reason, "agents": agents or []})
        for evidence_id in evidence_ids:
            evidence = self._items.get(evidence_id)
            if not evidence:
                continue
            for other_id in evidence_ids:
                if other_id != evidence_id and other_id not in evidence.conflict_with:
                    evidence.conflict_with.append(other_id)

    def reject(self, evidence: AgentEvidence, reason: str) -> None:
        self.rejected_evidence.append(
            {
                "evidence_id": evidence.evidence_id,
                "reason": reason,
                "page": evidence.page,
                "backend": evidence.retrieval_backend,
                "model_match_level": evidence.model_match_level,
            }
        )

    def get(self, evidence_id: str) -> Optional[AgentEvidence]:
        return self._items.get(evidence_id)

    def list(self) -> List[AgentEvidence]:
        return list(self._items.values())

    def by_agent(self, agent_name: str) -> List[AgentEvidence]:
        return [item for item in self._items.values() if agent_name in item.agent_names]

    def to_schema(self) -> EvidencePool:
        return EvidencePool(
            evidences=self.list(),
            agent_claims=self.agent_claims,
            conflicts=self.conflicts,
            metadata={
                "rejected_evidence": self.rejected_evidence,
                "evidence_count": len(self._items),
                "backend_counts": self._backend_counts(),
            },
        )

    def _find_duplicate(self, evidence: AgentEvidence, claim: str) -> Tuple[Optional[str], str]:
        if evidence.evidence_id in self._items:
            return evidence.evidence_id, "exact_evidence_id"
        normalized = _normalized_text(evidence.text)
        if normalized and normalized in self._normalized_text_to_id:
            return self._normalized_text_to_id[normalized], "exact_normalized_text"
        for existing in self._items.values():
            same_document = _document_key(existing) == _document_key(evidence)
            same_page = evidence.page is not None and existing.page == evidence.page
            same_figure = bool(
                (evidence.figure_id and evidence.figure_id == existing.figure_id)
                or (evidence.figure_number and evidence.figure_number == existing.figure_number)
            )
            if same_document and same_page and same_figure:
                return existing.evidence_id, "same_document_page_figure"
            if same_document and same_page and _text_overlap(existing.text, evidence.text) >= 0.78:
                return existing.evidence_id, "same_document_page_overlapping_text"
            if (
                existing.manual_title
                and existing.manual_title == evidence.manual_title
                and existing.section
                and existing.section == evidence.section
                and claim
                and claim in existing.claim_links
            ):
                return existing.evidence_id, "same_manual_section_claim"
            if _cross_backend_pair(existing, evidence) and same_page and _text_overlap(existing.text, evidence.text) >= 0.65:
                return existing.evidence_id, "chroma_jsonl_page_chunk_duplicate"
        return None, ""

    def _merge_into(self, existing_id: str, incoming: AgentEvidence, agent_name: str, claim: str, reason: str) -> None:
        existing = self._items[existing_id]
        if agent_name and agent_name not in existing.agent_names:
            existing.agent_names.append(agent_name)
        if claim and claim not in existing.claim_links:
            existing.claim_links.append(claim)
        incoming_is_better = _evidence_quality(incoming) > _evidence_quality(existing)
        if incoming_is_better:
            for field in (
                "text",
                "compact_excerpt",
                "manual_title",
                "manual_version",
                "device_family",
                "module_model",
                "order_number",
                "page",
                "section",
                "figure_id",
                "figure_number",
                "image_path",
                "raw_image_path",
                "resolved_image_path",
                "image_exists",
                "visual_evidence_status",
                "document_id",
                "chunk_id",
                "normalized_score",
                "retrieval_score",
                "quality_score",
            ):
                value = getattr(incoming, field)
                if value not in (None, "", [], False) or field in {"image_exists"}:
                    setattr(existing, field, value)
        merged_ids = set(existing.metadata.get("merged_evidence_ids", [existing.evidence_id]))
        merged_ids.add(incoming.evidence_id)
        merged_backends = set(existing.metadata.get("merged_backends", []))
        merged_backends.update(filter(None, [existing.retrieval_backend, incoming.retrieval_backend]))
        merged_sources = set(existing.metadata.get("merged_sources", []))
        merged_sources.update(filter(None, [existing.source, incoming.source]))
        existing.metadata.update(
            {
                "merged_evidence_ids": sorted(merged_ids),
                "merged_backends": sorted(merged_backends),
                "merged_sources": sorted(merged_sources),
                "dedup_reason": reason,
            }
        )

    def _with_stable_id(self, evidence: AgentEvidence) -> AgentEvidence:
        if not evidence.evidence_id:
            evidence.evidence_id = "ev_" + hashlib.sha256(evidence.signature().encode("utf-8")).hexdigest()[:16]
        return evidence

    def _detect_conflicts(self, evidence: AgentEvidence) -> None:
        if evidence.model_match_level == "cross_family":
            self.record_conflict([evidence.evidence_id], "cross_family_contamination", evidence.agent_names)
            return
        for other in self._items.values():
            if other.evidence_id == evidence.evidence_id:
                continue
            same_model = bool(
                evidence.module_model and other.module_model and evidence.module_model == other.module_model
            )
            if evidence.order_number and evidence.order_number == other.order_number and evidence.module_model != other.module_model:
                self.record_conflict([other.evidence_id, evidence.evidence_id], "same_order_number_different_model")
            if same_model and evidence.parameter and evidence.parameter == other.parameter:
                if _parameter_values(evidence.text) and _parameter_values(evidence.text) != _parameter_values(other.text):
                    self.record_conflict([other.evidence_id, evidence.evidence_id], "same_model_parameter_value_conflict")
            if same_model and _interface(evidence.text) and _interface(evidence.text) == _interface(other.text):
                if _ports(evidence.text) and _ports(evidence.text) != _ports(other.text):
                    self.record_conflict([other.evidence_id, evidence.evidence_id], "same_interface_port_description_conflict")
            if evidence.figure_number and evidence.figure_number == other.figure_number:
                if evidence.page != other.page or (evidence.module_model and evidence.module_model != other.module_model):
                    self.record_conflict([other.evidence_id, evidence.evidence_id], "same_figure_number_different_scope")

    def _backend_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for item in self._items.values():
            backend = item.retrieval_backend or "unknown"
            counts[backend] = counts.get(backend, 0) + 1
        return counts


def _normalized_text(text: str) -> str:
    return re.sub(r"\W+", "", (text or "").lower(), flags=re.UNICODE)


def _document_key(evidence: AgentEvidence) -> str:
    return (evidence.document_id or evidence.manual_title or evidence.source).strip().lower()


def _text_overlap(left: str, right: str) -> float:
    left_norm, right_norm = _normalized_text(left), _normalized_text(right)
    if not left_norm or not right_norm:
        return 0.0
    left_tokens, right_tokens = _tokens(left), _tokens(right)
    jaccard = len(left_tokens & right_tokens) / max(1, len(left_tokens | right_tokens))
    sequence = SequenceMatcher(None, left_norm, right_norm).ratio()
    return max(jaccard, sequence)


def _tokens(text: str) -> Set[str]:
    return set(re.findall(r"[A-Za-z0-9_/\-]+|[\u4e00-\u9fff]{2,}", (text or "").lower()))


def _cross_backend_pair(left: AgentEvidence, right: AgentEvidence) -> bool:
    return (left.retrieval_backend.startswith("chroma") and right.retrieval_backend.startswith("jsonl")) or (
        right.retrieval_backend.startswith("chroma") and left.retrieval_backend.startswith("jsonl")
    )


def _evidence_quality(evidence: AgentEvidence) -> Tuple[float, int]:
    completeness = sum(
        bool(value)
        for value in (
            evidence.manual_title,
            evidence.module_model,
            evidence.order_number,
            evidence.page,
            evidence.figure_number,
            evidence.resolved_image_path,
            evidence.document_id,
        )
    )
    return max(evidence.quality_score, evidence.normalized_score, evidence.retrieval_score), completeness


def _parameter_values(text: str) -> Set[str]:
    return set(re.findall(r"(?<![A-Z0-9-])\d+(?:\.\d+)?\s*(?:V|MV|A|MA|W|KW|HZ|KHZ|MHZ|MS|MM|M|%|°C)\b", text.upper()))


def _interface(text: str) -> str:
    match = re.search(r"\bX[1-9]\b", text.upper())
    return match.group(0) if match else ""


def _ports(text: str) -> Set[str]:
    return set(re.findall(r"\bX[1-9]\s*P[1-9]\b", text.upper()))
