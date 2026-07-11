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

    def execute(self, task, registry: ToolRegistry, evidence_pool: SharedEvidencePool):
        query = self._join_query(task)
        evidences = registry.search_table(query, top_k=3) + registry.search_text(query, top_k=2)
        if not evidences:
            return self._abstain(task, "No parameter table or text evidence was found.")
        top = evidences[0]
        answer = (
            f"参数查证：{top.module or '相关模块'} 的 {top.parameter or '参数'} 可由 "
            f"{top.source} 第 {top.page or '-'} 页证据支持。{top.text}"
        )
        return self._finish_with_evidence(
            task,
            evidences,
            evidence_pool,
            answer_fragment=answer,
            claim=answer,
            confidence="HIGH" if top.modality == "table" else "MEDIUM",
            status=AgentStatus.ANSWERED.value,
        )

