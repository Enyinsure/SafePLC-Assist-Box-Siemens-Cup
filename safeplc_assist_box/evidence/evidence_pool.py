#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import hashlib
import re
from typing import Dict, Iterable, List, Optional

from ..schemas import AgentEvidence, EvidencePool


def _semantic_key(text: str) -> str:
    clean = re.sub(r"\s+", "", (text or "").lower())
    return hashlib.sha256(clean[:600].encode("utf-8", errors="ignore")).hexdigest()[:16]


class SharedEvidencePool:
    """Deduplicated evidence store shared by all professional agents."""

    def __init__(self) -> None:
        self._items: Dict[str, AgentEvidence] = {}
        self._signature_to_id: Dict[str, str] = {}
        self._page_to_id: Dict[str, str] = {}
        self._semantic_to_id: Dict[str, str] = {}
        self.agent_claims: Dict[str, List[str]] = {}
        self.conflicts: List[Dict[str, object]] = []
        self.rejected_evidence: List[Dict[str, object]] = []

    def add(self, evidence: AgentEvidence, agent_name: str, claim: str = "") -> str:
        ev = self._with_stable_id(evidence)
        signature = ev.signature()
        existing_id = self._signature_to_id.get(signature)

        semantic_id = self._semantic_to_id.get(_semantic_key(ev.text))
        page_key = self._page_key(ev)
        page_id = self._page_to_id.get(page_key) if page_key else None

        merge_id = existing_id or semantic_id or self._same_page_duplicate_id(ev, page_id)
        if merge_id:
            self._merge_into(merge_id, ev, agent_name, claim)
            return merge_id

        if agent_name and agent_name not in ev.agent_names:
            ev.agent_names.append(agent_name)
        if claim and claim not in ev.claim_links:
            ev.claim_links.append(claim)

        self._items[ev.evidence_id] = ev
        self._signature_to_id[signature] = ev.evidence_id
        self._semantic_to_id[_semantic_key(ev.text)] = ev.evidence_id
        if page_key:
            self._page_to_id[page_key] = ev.evidence_id
        self._detect_conflict(ev)
        return ev.evidence_id

    def add_many(
        self,
        evidences: Iterable[AgentEvidence],
        agent_name: str,
        claim: str = "",
    ) -> List[str]:
        ids: List[str] = []
        for ev in evidences:
            ev_id = self.add(ev, agent_name=agent_name, claim=claim)
            if ev_id not in ids:
                ids.append(ev_id)
        return ids

    def add_agent_claim(self, agent_name: str, claim: str) -> None:
        if not claim:
            return
        self.agent_claims.setdefault(agent_name, [])
        if claim not in self.agent_claims[agent_name]:
            self.agent_claims[agent_name].append(claim)

    def record_conflict(
        self,
        evidence_ids: List[str],
        reason: str,
        agents: Optional[List[str]] = None,
    ) -> None:
        conflict = {
            "evidence_ids": evidence_ids,
            "reason": reason,
            "agents": agents or [],
        }
        self.conflicts.append(conflict)
        for ev_id in evidence_ids:
            ev = self._items.get(ev_id)
            if not ev:
                continue
            for other in evidence_ids:
                if other != ev_id and other not in ev.conflict_with:
                    ev.conflict_with.append(other)

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
        return [ev for ev in self._items.values() if agent_name in ev.agent_names]

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

    def _with_stable_id(self, evidence: AgentEvidence) -> AgentEvidence:
        if evidence.evidence_id:
            return evidence
        digest = hashlib.sha256(evidence.signature().encode("utf-8")).hexdigest()[:16]
        evidence.evidence_id = f"ev_{digest}"
        return evidence

    def _merge_into(self, existing_id: str, ev: AgentEvidence, agent_name: str, claim: str) -> None:
        existing = self._items[existing_id]
        if agent_name and agent_name not in existing.agent_names:
            existing.agent_names.append(agent_name)
        if claim and claim not in existing.claim_links:
            existing.claim_links.append(claim)
        if ev.retrieval_score > existing.retrieval_score:
            existing.retrieval_score = ev.retrieval_score
            existing.quality_score = ev.quality_score
            existing.metadata["merged_higher_score_from"] = ev.evidence_id
        if ev.retrieval_backend and ev.retrieval_backend not in str(existing.metadata.get("merged_backends", "")):
            merged = set(existing.metadata.get("merged_backends", []))
            merged.add(ev.retrieval_backend)
            existing.metadata["merged_backends"] = sorted(merged)

    def _same_page_duplicate_id(self, ev: AgentEvidence, page_id: Optional[str]) -> Optional[str]:
        if not page_id:
            return None
        existing = self._items.get(page_id)
        if not existing:
            return None
        if not ev.text or not existing.text:
            return None
        shorter = min(len(ev.text), len(existing.text))
        if shorter < 80:
            return None
        overlap_seed = _semantic_key(ev.text[:shorter])
        existing_seed = _semantic_key(existing.text[:shorter])
        if overlap_seed == existing_seed:
            return page_id
        return None

    def _page_key(self, ev: AgentEvidence) -> str:
        if not ev.page:
            return ""
        return "|".join([ev.source or ev.manual_title or "", str(ev.page), ev.figure_id or ev.chunk_id or "page"])

    def _detect_conflict(self, ev: AgentEvidence) -> None:
        if ev.model_match_level == "cross_family":
            self.record_conflict([ev.evidence_id], "cross_family_contamination", ev.agent_names)
            return
        if not ev.parameter:
            return
        for other in self._items.values():
            if other.evidence_id == ev.evidence_id:
                continue
            if other.parameter and other.parameter == ev.parameter and other.module_model != ev.module_model:
                self.record_conflict(
                    [other.evidence_id, ev.evidence_id],
                    "same_parameter_different_model_scope",
                    list(set(other.agent_names + ev.agent_names)),
                )

    def _backend_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for ev in self._items.values():
            backend = ev.retrieval_backend or "unknown"
            counts[backend] = counts.get(backend, 0) + 1
        return counts
