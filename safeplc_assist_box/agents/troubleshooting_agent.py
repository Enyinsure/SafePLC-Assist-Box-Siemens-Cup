#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from ..evidence.evidence_pool import SharedEvidencePool
from ..schemas import AgentStatus
from ..tools.tool_registry import ToolRegistry
from .base_agent import BaseAgent
from ..evidence.evidence_ranker import rank_evidence
from ..evidence.fact_extractors import extract_led_checks


class TroubleshootingAgent(BaseAgent):
    agent_name = "Troubleshooting Agent"
    role_description = "Specialist for alarms, LED states, communication faults and evidence-grounded check order."
    tool_names = ["search_text", "search_table"]
    default_claim_type = "diagnosis"

    def execute(self, task, registry: ToolRegistry, evidence_pool: SharedEvidencePool):
        query = self._join_query(task)
        candidates = registry.search_text(query, top_k=10) + registry.search_table(query, top_k=6)
        ranked = rank_evidence(candidates, query=query, top_k=12)
        selected = next(((item, extract_led_checks(item.text)) for item in ranked if extract_led_checks(item.text)), None)
        if not selected:
            return self._abstain(task, "No troubleshooting evidence was found.")
        top, checks = selected
        claim = "通信不上且指示灯异常时，先记录并核对：" + "、".join(checks) + "。"
        answer = f"{claim} Evidence: {top.manual_title or top.source}, page {top.page or '-'}."
        return self._finish_with_evidence(
            task,
            [top],
            evidence_pool,
            answer_fragment=answer,
            claim=claim,
            confidence="MEDIUM",
            status=AgentStatus.ANSWERED.value,
            claim_type="diagnosis",
            claim_metadata={
                "general_guidance": False,
                "evidence_span": "、".join(checks),
                "fact_type": "led_checklist",
                "source_page": top.page,
                "source_section": top.section,
                "inference_level": "bounded_inference",
            },
        )
