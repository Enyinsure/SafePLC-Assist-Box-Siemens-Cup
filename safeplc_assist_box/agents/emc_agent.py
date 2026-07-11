#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from ..evidence.evidence_pool import SharedEvidencePool
from ..schemas import AgentStatus
from ..tools.tool_registry import ToolRegistry
from .base_agent import BaseAgent


class EMCAgent(BaseAgent):
    agent_name = "EMC Agent"
    role_description = "Specialist for EMC, shielding, grounding, cable layout and installation environment."
    tool_names = ["search_text", "search_hybrid"]
    default_claim_type = "procedure"

    def execute(self, task, registry: ToolRegistry, evidence_pool: SharedEvidencePool):
        query = self._join_query(task)
        evidences = registry.search_text(query, top_k=4) + registry.search_hybrid(query, modalities=["text"], top_k=2)
        if not evidences:
            return self._abstain(task, "No EMC evidence was found.")
        top = evidences[0]
        claim = "EMC work should use low-impedance grounding, correct shielding and separated cable routing when supported by cited evidence."
        answer = f"{claim} Evidence: {top.manual_title or top.source}, page {top.page or '-'}."
        return self._finish_with_evidence(
            task,
            evidences,
            evidence_pool,
            answer_fragment=answer,
            claim=claim,
            confidence="MEDIUM",
            status=AgentStatus.ANSWERED.value,
            claim_type="procedure",
        )
