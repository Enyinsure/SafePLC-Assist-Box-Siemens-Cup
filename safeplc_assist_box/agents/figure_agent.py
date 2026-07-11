#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from ..evidence.evidence_pool import SharedEvidencePool
from ..schemas import AgentStatus
from ..tools.tool_registry import ToolRegistry
from .base_agent import BaseAgent


class FigureAgent(BaseAgent):
    agent_name = "Figure Agent"
    role_description = "Specialist for interface positions, panel layout, figure IDs and page-text association."
    tool_names = ["search_figure", "search_hybrid"]

    def execute(self, task, registry: ToolRegistry, evidence_pool: SharedEvidencePool):
        query = self._join_query(task)
        evidences = registry.search_figure(query, top_k=3) + registry.search_hybrid(query, modalities=["figure", "text"], top_k=2)
        if not evidences:
            return self._abstain(task, "No figure or page-location evidence was found.")
        top = evidences[0]
        answer = (
            f"图示查证：{top.title}，图号 {top.figure_id or '-'}，页码 {top.page or '-'}。"
            f"{top.text}"
        )
        return self._finish_with_evidence(
            task,
            evidences,
            evidence_pool,
            answer_fragment=answer,
            claim=answer,
            confidence="HIGH" if top.figure_id else "MEDIUM",
            status=AgentStatus.ANSWERED.value,
        )

