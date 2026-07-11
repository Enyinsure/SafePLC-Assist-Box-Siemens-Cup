#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import hashlib
import time
from typing import Dict, Iterable, List, Optional

from ..evidence.evidence_pool import SharedEvidencePool
from ..schemas import AgentClaim, AgentEvidence, AgentObservation, AgentResult, AgentStatus, compact_text
from ..tools.tool_registry import ToolRegistry


class BaseAgent:
    agent_name = "Base Agent"
    role_description = "Base agent"
    tool_names: List[str] = []
    default_claim_type = "grounded_qa"

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
        claim_type: Optional[str] = None,
        claim_metadata: Optional[Dict[str, object]] = None,
        direct_support: Optional[bool] = None,
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

        claim_text = compact_text(claim or answer_fragment, limit=260)
        claim_id = self._claim_id(task.task_id, claim_text)
        evidence_ids = evidence_pool.add_many(unique, self.agent_name, claim=claim_id)
        evidence_pool.add_agent_claim(self.agent_name, claim_text)
        direct = any(ev.direct_evidence or ev.metadata.get("direct_evidence") for ev in unique)
        if direct_support is not None:
            direct = direct_support
        agent_claim = AgentClaim(
            claim_id=claim_id,
            claim_text=claim_text,
            claim_type=claim_type or self.default_claim_type,
            evidence_ids=evidence_ids,
            model_scope=self._model_scope(unique),
            confidence=confidence,
            direct_support=bool(direct),
            subquestion_ids=list(getattr(task, "subquestion_ids", []) or []),
            metadata=dict(claim_metadata or {}),
        )
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
            answer_fragment=compact_text(answer_fragment, limit=420),
            evidence_ids=evidence_ids,
            confidence=confidence,
            observations=[observation],
            claims=[agent_claim],
            metadata={
                "role_description": self.role_description,
                "available_tools": list(self.tool_names),
                "objective": getattr(task, "objective", ""),
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
                "objective": getattr(task, "objective", ""),
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

    def _claim_id(self, task_id: str, claim: str) -> str:
        seed = f"{self.agent_name}|{task_id}|{claim}"
        return "claim_" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]

    def _model_scope(self, evidences: Iterable[AgentEvidence]) -> str:
        scopes = []
        for ev in evidences:
            scope = ev.module_model or ev.module or ev.device_family
            if scope and scope not in scopes:
                scopes.append(scope)
        return "; ".join(scopes[:3])

    def _evidence_refs(self, evidences: Iterable[AgentEvidence]) -> str:
        parts = []
        for ev in evidences:
            ref = ev.manual_title or ev.source
            if ev.page:
                ref += f", page {ev.page}"
            if ev.figure_number:
                ref += f", {ev.figure_number}"
            parts.append(ref)
        return "; ".join(parts[:3])
