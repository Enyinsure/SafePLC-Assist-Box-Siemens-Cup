#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from ..evidence.evidence_pool import SharedEvidencePool
from ..schemas import AgentClaim, AgentResult, AgentStatus
from ..tools.tool_registry import ToolRegistry
from .base_agent import BaseAgent


class SafetyBoundaryAgent(BaseAgent):
    agent_name = "Safety Boundary Agent"
    role_description = "Industrial operation safety boundary agent for offline/read-only refusal and safe alternatives."
    tool_names = ["search_text"]
    default_claim_type = "safety"

    def execute(self, task, registry: ToolRegistry, evidence_pool: SharedEvidencePool):
        evidences = registry.search_text("OFFLINE READ-ONLY industrial operation boundary real PLC dangerous operation", top_k=1)
        ids = evidence_pool.add_many(evidences, self.agent_name, claim="safety_refusal")
        claim_text = (
            "Dangerous industrial operation requests must be refused; only stop, isolation, documentation "
            "and qualified review alternatives are allowed."
        )
        answer = (
            "OFFLINE / READ-ONLY refusal: this request asks for a dangerous industrial operation. "
            "I will not provide bypass, short-circuit, live-wiring, forced-output or real PLC control steps. "
            "Safe alternative: stop and isolate the equipment, record symptoms, verify drawings/manuals, "
            "and have qualified personnel handle the site procedure."
        )
        claim = AgentClaim(
            claim_id="claim_safety_refusal",
            claim_text=claim_text,
            claim_type="safety",
            evidence_ids=ids,
            model_scope="SafePLC-Assist Box",
            confidence="HIGH" if ids else "NOT_AVAILABLE",
            direct_support=bool(ids),
            subquestion_ids=list(getattr(task, "subquestion_ids", []) or []),
            metadata={"refusal": True},
        )
        return AgentResult(
            agent_name=self.agent_name,
            task_id=task.task_id,
            status=AgentStatus.REFUSE.value,
            answer_fragment=answer,
            evidence_ids=ids,
            confidence="HIGH" if ids else "NOT_AVAILABLE",
            abstain_reason="" if ids else "No operation-boundary evidence found.",
            claims=[claim] if ids else [],
            metadata={
                "role_description": self.role_description,
                "available_tools": list(self.tool_names),
                "offline_read_only": True,
            },
        )
