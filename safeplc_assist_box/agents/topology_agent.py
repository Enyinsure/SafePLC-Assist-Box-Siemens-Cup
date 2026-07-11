#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from ..evidence.evidence_pool import SharedEvidencePool
from ..schemas import AgentStatus
from ..tools.tool_registry import ToolRegistry
from .base_agent import BaseAgent


class TopologyAgent(BaseAgent):
    agent_name = "Topology Agent"
    role_description = "Specialist for PROFINET, HMI, CPU, IO topology and device relationships."
    tool_names = ["search_hybrid", "search_text", "search_figure"]

    def execute(self, task, registry: ToolRegistry, evidence_pool: SharedEvidencePool):
        query = self._join_query(task)
        evidences = registry.search_hybrid(query, modalities=["figure", "text"], top_k=4)
        if not evidences:
            return self._abstain(task, "No topology evidence was found.")
        top = evidences[0]
        answer = (
            f"拓扑查证：{top.title}，页码 {top.page or '-'}，图号 {top.figure_id or '-'}。"
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

