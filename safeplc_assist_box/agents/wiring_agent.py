#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from ..evidence.evidence_pool import SharedEvidencePool
from ..schemas import AgentResult, AgentStatus
from ..tools.tool_registry import ToolRegistry
from .base_agent import BaseAgent
from ..evidence.evidence_ranker import rank_evidence
from ..evidence.fact_extractors import extract_wiring_facts


class WiringAgent(BaseAgent):
    agent_name = "Wiring Agent"
    role_description = "Specialist for terminal definitions, wiring constraints and installation safety notes."
    tool_names = ["search_text", "search_table", "search_figure"]
    default_claim_type = "connection"

    def execute(self, task, registry: ToolRegistry, evidence_pool: SharedEvidencePool):
        query = self._join_query(task)
        risky_terms = ["短接", "绕过", "带电", "force output", "强制输出", "bypass"]
        if any(term.lower() in query.lower() for term in risky_terms):
            boundary = registry.search_text("OFFLINE READ-ONLY industrial operation boundary", top_k=1)
            ids = evidence_pool.add_many(boundary, self.agent_name, claim="wiring_refusal")
            return AgentResult(
                agent_name=self.agent_name,
                task_id=task.task_id,
                status=AgentStatus.REFUSE.value,
                answer_fragment=(
                    "Refused: wiring questions that involve bypassing protection, live wiring or forced output "
                    "must be handled by stop, isolation and qualified review only."
                ),
                evidence_ids=ids,
                confidence="HIGH" if ids else "NOT_AVAILABLE",
                abstain_reason="" if ids else "No safety boundary evidence was found.",
            )
        candidates = registry.search_text(query, top_k=8) + registry.search_table(query, top_k=8)
        direct = [(item, extract_wiring_facts(item.text)) for item in rank_evidence(candidates, query=query, top_k=12)]
        selected = next(((item, facts) for item, facts in direct if facts), None)
        if not selected:
            figures = registry.search_figure(query, top_k=5)
            direct = [(item, extract_wiring_facts(item.text)) for item in figures if extract_wiring_facts(item.text)]
            selected = direct[0] if direct else None
        if not selected:
            return self._abstain(task, "No wiring or terminal evidence was found.")
        top, facts = selected
        general = top.model_match_level == "same_family_general"
        claim = "；".join(facts[:4]) + "。"
        answer = f"{claim} Evidence: {top.manual_title or top.source}, page {top.page or '-'}."
        return self._finish_with_evidence(
            task,
            [top],
            evidence_pool,
            answer_fragment=answer,
            claim=claim,
            confidence="MEDIUM",
            status=AgentStatus.ANSWERED.value,
            claim_type="connection",
            claim_metadata={
                "terminal": top.metadata.get("terminal", ""),
                "signal": top.metadata.get("signal", ""),
                "voltage": top.metadata.get("voltage", ""),
                "polarity": top.metadata.get("polarity", ""),
                "connection_scope": top.module_model or top.device_family,
                "general_guidance": general,
                "evidence_span": "；".join(facts),
                "fact_type": "wiring_requirement",
                "source_page": top.page,
                "source_section": top.section,
                "inference_level": "general_guidance" if general else "direct",
            },
        )
