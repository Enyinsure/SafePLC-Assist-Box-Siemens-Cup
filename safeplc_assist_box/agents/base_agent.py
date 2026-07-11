#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import time
from typing import Iterable, List

from ..evidence.evidence_pool import SharedEvidencePool
from ..schemas import AgentEvidence, AgentObservation, AgentResult, AgentStatus
from ..tools.tool_registry import ToolRegistry


class BaseAgent:
    agent_name = "Base Agent"
    role_description = "Base agent"
    tool_names: List[str] = []

    def run(
        self,
        task,
        registry: ToolRegistry,
        evidence_pool: SharedEvidencePool,
    ) -> AgentResult:
        started = time.perf_counter()
        calls_before = registry.tool_call_count
        try:
            result = self.execute(task, registry, evidence_pool)
        except Exception as exc:
            result = AgentResult(
                agent_name=self.agent_name,
                task_id=task.task_id,
                status=AgentStatus.ABSTAIN.value,
                abstain_reason=f"Agent execution failed: {exc}",
                confidence="NOT_AVAILABLE",
            )
        result.latency_ms = int((time.perf_counter() - started) * 1000)
        result.tool_calls = max(0, registry.tool_call_count - calls_before)

        if result.status in {AgentStatus.ANSWERED.value, AgentStatus.PARTIAL.value} and not result.evidence_ids:
            result.status = AgentStatus.ABSTAIN.value
            result.confidence = "NOT_AVAILABLE"
            result.abstain_reason = "No evidence was cited by the agent."
            result.answer_fragment = ""
        return result

    def execute(self, task, registry: ToolRegistry, evidence_pool: SharedEvidencePool) -> AgentResult:
        raise NotImplementedError

    def _finish_with_evidence(
        self,
        task,
        evidences: Iterable[AgentEvidence],
        evidence_pool: SharedEvidencePool,
        answer_fragment: str,
        claim: str,
        confidence: str = "MEDIUM",
        status: str = AgentStatus.ANSWERED.value,
    ) -> AgentResult:
        unique = self._unique_evidence(evidences)
        if not unique:
            return AgentResult(
                agent_name=self.agent_name,
                task_id=task.task_id,
                status=AgentStatus.ABSTAIN.value,
                confidence="NOT_AVAILABLE",
                missing_information=list(task.required_evidence_types or []),
                abstain_reason="No matching evidence was retrieved for this agent task.",
            )

        evidence_ids = evidence_pool.add_many(unique, self.agent_name, claim=claim)
        evidence_pool.add_agent_claim(self.agent_name, claim or answer_fragment)
        observation = AgentObservation(
            tool_name=",".join(self.tool_names),
            query=task.query,
            status="OK",
            evidence_ids=evidence_ids,
        )
        return AgentResult(
            agent_name=self.agent_name,
            task_id=task.task_id,
            status=status,
            answer_fragment=answer_fragment,
            evidence_ids=evidence_ids,
            confidence=confidence,
            observations=[observation],
            metadata={
                "role_description": self.role_description,
                "available_tools": list(self.tool_names),
            },
        )

    def _abstain(self, task, reason: str) -> AgentResult:
        return AgentResult(
            agent_name=self.agent_name,
            task_id=task.task_id,
            status=AgentStatus.ABSTAIN.value,
            confidence="NOT_AVAILABLE",
            abstain_reason=reason,
            metadata={
                "role_description": self.role_description,
                "available_tools": list(self.tool_names),
            },
        )

    def _unique_evidence(self, evidences: Iterable[AgentEvidence]) -> List[AgentEvidence]:
        seen = set()
        out: List[AgentEvidence] = []
        for ev in evidences:
            if ev.evidence_id in seen:
                continue
            seen.add(ev.evidence_id)
            out.append(ev)
        return out

    def _join_query(self, task) -> str:
        slot_text = " ".join(v for v in task.input_slots.values() if v)
        return " ".join(part for part in [task.query, task.context, slot_text, task.objective] if part).strip()

