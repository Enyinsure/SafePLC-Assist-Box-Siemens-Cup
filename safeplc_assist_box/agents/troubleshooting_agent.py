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

    def execute(self, task, registry: ToolRegistry, evidence_pool: SharedEvidencePool):
        query = self._join_query(task)
        evidences = registry.search_hybrid(query, modalities=["text", "table", "figure"], top_k=4)
        if not evidences:
            return self._abstain(task, "No troubleshooting evidence was found.")
        top = evidences[0]
        answer = (
            f"故障排查查证：{top.text} 有证据支持的检查项应优先记录 LED/报警/网络状态；"
            "现场供电、接线和最近变更属于待人工确认项。"
        )
        return self._finish_with_evidence(
            task,
            evidences,
            evidence_pool,
            answer_fragment=answer,
            claim=answer,
            confidence="MEDIUM",
            status=AgentStatus.ANSWERED.value,
        )

