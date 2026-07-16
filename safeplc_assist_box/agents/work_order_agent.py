#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime

from ..evidence.evidence_pool import SharedEvidencePool
from ..schemas import AgentStatus
from ..tools.tool_registry import ToolRegistry
from .base_agent import BaseAgent


class WorkOrderAgent(BaseAgent):
    agent_name = "Work-order Agent"
    role_description = "Specialist for turning verified evidence into maintenance assistance records."
    tool_names = ["structured_export"]
    default_claim_type = "maintenance_record"

    def execute(self, task, registry: ToolRegistry, evidence_pool: SharedEvidencePool):
        evidences = evidence_pool.list()
        if not evidences:
            return self._abstain(
                task,
                "Work-order export requires evidence from a specialist agent; no evidence is available yet.",
            )

        model = task.input_slots.get("module_model", "") or task.input_slots.get("order_number", "") or "待确认设备"
        refs = self._evidence_refs(evidences)
        claim = (
            f"已基于 {len(evidences)} 条已检索证据生成维护辅助记录草稿；"
            f"设备范围为 {model}，正式执行前仍需现场人员核对型号、现象和安全状态。"
        )
        answer = (
            f"维护工单草稿：问题={task.query}；设备={model}；"
            f"证据={refs or '见 Evidence Pool'}；"
            f"生成时间={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}。"
        )
        return self._finish_with_evidence(
            task,
            evidences,
            evidence_pool,
            answer_fragment=answer,
            claim=claim,
            confidence="MEDIUM",
            status=AgentStatus.PARTIAL.value,
            claim_type="maintenance_record",
            direct_support=False,
            claim_metadata={
                "fact_type": "maintenance_work_order",
                "evidence_count": len(evidences),
                "manual_confirmation_required": True,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
        )
