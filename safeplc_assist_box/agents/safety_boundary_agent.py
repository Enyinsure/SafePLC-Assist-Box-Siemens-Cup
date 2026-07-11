#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from ..evidence.evidence_pool import SharedEvidencePool
from ..schemas import AgentResult, AgentStatus
from ..tools.tool_registry import ToolRegistry
from .base_agent import BaseAgent


class SafetyBoundaryAgent(BaseAgent):
    agent_name = "Safety Boundary Agent"
    role_description = "Industrial operation safety boundary agent for offline/read-only refusal and safe alternatives."
    tool_names = ["search_text"]

    def execute(self, task, registry: ToolRegistry, evidence_pool: SharedEvidencePool):
        evidences = registry.search_text("OFFLINE READ-ONLY 工业操作安全边界 真实 PLC 危险操作", top_k=1)
        ids = evidence_pool.add_many(
            evidences,
            self.agent_name,
            claim="Dangerous industrial operation request must be refused.",
        )
        answer = (
            "该请求涉及危险工业操作或真实 PLC 控制边界。系统保持 OFFLINE / READ-ONLY，"
            "不能提供短接、绕过、屏蔽安全功能、带电接线、强制输出或控制真实 PLC 的步骤。"
            "安全替代方向：停机隔离，记录现象，核对图纸、报警、供电、端子和安全回路状态，"
            "由具备资质人员按现场规程和厂家资料处理。"
        )
        return AgentResult(
            agent_name=self.agent_name,
            task_id=task.task_id,
            status=AgentStatus.REFUSE.value,
            answer_fragment=answer,
            evidence_ids=ids,
            confidence="HIGH" if ids else "NOT_AVAILABLE",
            abstain_reason="" if ids else "No operation-boundary evidence found.",
            metadata={
                "role_description": self.role_description,
                "available_tools": list(self.tool_names),
                "offline_read_only": True,
            },
        )

