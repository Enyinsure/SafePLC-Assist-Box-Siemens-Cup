#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from ..evidence.evidence_pool import SharedEvidencePool
from ..schemas import AgentStatus
from ..tools.tool_registry import ToolRegistry
from .base_agent import BaseAgent


class TroubleshootingAgent(BaseAgent):
    agent_name = "Troubleshooting Agent"
    role_description = "Specialist for alarms, LED states, communication faults and evidence-grounded check order."
    tool_names = ["search_text", "search_table", "search_hybrid"]
    default_claim_type = "diagnosis"

    def execute(self, task, registry: ToolRegistry, evidence_pool: SharedEvidencePool):
        query = self._join_query(task)
        evidences = registry.search_hybrid(query, modalities=["text", "table", "figure"], top_k=5)
        if not evidences:
            return self._abstain(task, "No troubleshooting evidence was found.")
        top = evidences[0]
        claim = (
            "人工确认/人工复核 required for site-only conditions. For communication or LED faults, "
            "record LED state, diagnostics, device name/IP, connection state, power state and recent changes."
        )
        answer = f"{claim} Evidence: {top.manual_title or top.source}, page {top.page or '-'}."
        return self._finish_with_evidence(
            task,
            evidences,
            evidence_pool,
            answer_fragment=answer,
            claim=claim,
            confidence="MEDIUM",
            status=AgentStatus.ANSWERED.value,
            claim_type="diagnosis",
        )
