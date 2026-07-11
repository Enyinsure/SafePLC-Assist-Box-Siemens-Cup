#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import hashlib
from typing import Dict, Iterable, List, Optional

from ..schemas import AgentEvidence, EvidencePool


class SharedEvidencePool:
    """Deduplicated evidence store shared by all professional agents."""

    def __init__(self) -> None:
        self._items: Dict[str, AgentEvidence] = {}
        self._signature_to_id: Dict[str, str] = {}
        self.agent_claims: Dict[str, List[str]] = {}
        self.conflicts: List[Dict[str, object]] = []

    def add(self, evidence: AgentEvidence, agent_name: str, claim: str = "") -> str:
        ev = self._with_stable_id(evidence)
        signature = ev.signature()
        existing_id = self._signature_to_id.get(signature)

        if existing_id:
            existing = self._items[existing_id]
            if agent_name and agent_name not in existing.agent_names:
                existing.agent_names.append(agent_name)
            if claim and claim not in existing.claim_links:
                existing.claim_links.append(claim)
            return existing_id

        if agent_name and agent_name not in ev.agent_names:
            ev.agent_names.append(agent_name)
        if claim and claim not in ev.claim_links:
            ev.claim_links.append(claim)

        self._items[ev.evidence_id] = ev
        self._signature_to_id[signature] = ev.evidence_id
        return ev.evidence_id

    def add_many(
        self,
        evidences: Iterable[AgentEvidence],
        agent_name: str,
        claim: str = "",
    ) -> List[str]:
        return [self.add(ev, agent_name=agent_name, claim=claim) for ev in evidences]

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
        )

    def _with_stable_id(self, evidence: AgentEvidence) -> AgentEvidence:
        if evidence.evidence_id:
            return evidence
        digest = hashlib.sha256(evidence.signature().encode("utf-8")).hexdigest()[:12]
        evidence.evidence_id = f"ev_{digest}"
        return evidence

