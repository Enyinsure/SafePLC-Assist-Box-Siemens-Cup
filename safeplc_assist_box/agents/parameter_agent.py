#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from ..evidence.evidence_pool import SharedEvidencePool
from ..schemas import AgentStatus
from ..tools.tool_registry import ToolRegistry
from .base_agent import BaseAgent


class ParameterAgent(BaseAgent):
    agent_name = "Parameter Agent"
    role_description = "Specialist for module parameters, order numbers, voltage, current, power and table evidence."
    tool_names = ["search_table", "search_text"]
    default_claim_type = "parameter"

    def execute(self, task, registry: ToolRegistry, evidence_pool: SharedEvidencePool):
        query = self._join_query(task)
        evidences = registry.search_table(query, top_k=5) + registry.search_text(query, top_k=3)
        if not evidences:
            return self._abstain(task, "No parameter table or text evidence was found.")
        top = evidences[0]
        claim = f"{top.module_model or top.module or 'Target module'}: {top.compact_excerpt}"
        answer = f"{claim} Excerpt: {top.compact_excerpt}"
        return self._finish_with_evidence(
            task,
            [top],
            evidence_pool,
            answer_fragment=answer,
            claim=claim,
            confidence="HIGH" if top.modality == "table" else "MEDIUM",
            status=AgentStatus.ANSWERED.value,
            claim_type="parameter",
            claim_metadata={
                "parameter_name": top.parameter,
                "value": top.metadata.get("value", ""),
                "unit": top.metadata.get("unit", ""),
                "condition": top.metadata.get("condition", ""),
                "source_page": top.page,
            },
        )
