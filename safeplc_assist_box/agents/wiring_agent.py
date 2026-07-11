#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from ..evidence.evidence_pool import SharedEvidencePool
from ..schemas import AgentResult, AgentStatus
from ..tools.tool_registry import ToolRegistry
from .base_agent import BaseAgent


class WiringAgent(BaseAgent):
    agent_name = "Wiring Agent"
    role_description = "Specialist for terminal definitions, wiring constraints and installation safety notes."
    tool_names = ["search_hybrid", "search_table"]

    def execute(self, task, registry: ToolRegistry, evidence_pool: SharedEvidencePool):
        query = self._join_query(task)
        risky_terms = ["短接", "绕过", "带电", "强制输出", "屏蔽安全门"]
        if any(term in query for term in risky_terms):
            boundary = registry.search_text("OFFLINE READ-ONLY 工业操作安全边界", top_k=1)
            ids = evidence_pool.add_many(boundary, self.agent_name, claim="Wiring Agent refused dangerous execution steps.")
            return AgentResult(
                agent_name=self.agent_name,
                task_id=task.task_id,
                status=AgentStatus.REFUSE.value,
                answer_fragment="接线问题涉及危险操作时不输出可执行步骤，只能给出断电、隔离和人工复核方向。",
                evidence_ids=ids,
                confidence="HIGH" if ids else "NOT_AVAILABLE",
                abstain_reason="" if ids else "No safety boundary evidence was found.",
            )
        evidences = registry.search_hybrid(query, modalities=["text", "table", "figure"], top_k=4)
        if not evidences:
            return self._abstain(task, "No wiring or terminal evidence was found.")
        top = evidences[0]
        answer = (
            f"接线查证：{top.title}，页码 {top.page or '-'}。"
            f"{top.text} 现场作业需由具备资质人员按图纸执行。"
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

