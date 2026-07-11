#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime

from ..evidence.evidence_pool import SharedEvidencePool
from ..schemas import AgentResult, AgentStatus
from ..tools.tool_registry import ToolRegistry
from .base_agent import BaseAgent


class WorkOrderAgent(BaseAgent):
    agent_name = "Work-order Agent"
    role_description = "Specialist for turning final answers into maintenance assistance records."
    tool_names = ["structured_export"]

    def execute(self, task, registry: ToolRegistry, evidence_pool: SharedEvidencePool):
        claim = (
            f"运维辅助记录：问题={task.query}; 设备={task.input_slots.get('module_model', '-')}; "
            f"生成时间={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        evidence_pool.add_agent_claim(self.agent_name, claim)
        return AgentResult(
            agent_name=self.agent_name,
            task_id=task.task_id,
            status=AgentStatus.PARTIAL.value,
            answer_fragment=claim,
            evidence_ids=[],
            confidence="LOW",
            assumptions=["Work-order Agent depends on Judge final answer for complete export."],
            abstain_reason="Work-order export is finalized after Judge decision.",
            metadata={"role_description": self.role_description, "available_tools": list(self.tool_names)},
        )

