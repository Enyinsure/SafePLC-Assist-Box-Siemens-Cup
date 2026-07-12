#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re

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
        interface_match = re.search(r"\bX\d+\b", task.input_slots.get("interface_name", "") or query, re.I)
        interface = interface_match.group(0).upper() if interface_match else "X1"
        candidates = registry.search_text(query, top_k=10) + registry.search_table(query, top_k=6)
        ranked = rank_evidence(candidates, query=query, top_k=12)
        extracted = [(item, extract_led_checks(item.text, interface)) for item in ranked]
        extracted = [item for item in extracted if item[1]]
        if not extracted:
            return self._abstain(task, "No troubleshooting evidence was found.")
        top, checks = max(extracted, key=lambda item: (len(item[1]), item[0].quality_score))
        expected = [
            "RUN/STOP LED", "ERROR LED", "MAINT LED",
            f"{interface} P1 LINK RX/TX LED", f"{interface} P2 LINK RX/TX LED",
        ]
        missing = [item for item in expected if item not in checks]
        coverage_ratio = len([item for item in expected if item in checks]) / len(expected)
        claim = "该证据页列出的相关状态和端口指示灯包括：" + "、".join(checks) + "。"
        answer = f"{claim} Evidence: {top.manual_title or top.source}, page {top.page or '-'}."
        return self._finish_with_evidence(
            task,
            [top],
            evidence_pool,
            answer_fragment=answer,
            claim=claim,
            confidence="MEDIUM",
            status=AgentStatus.PARTIAL.value if missing else AgentStatus.ANSWERED.value,
            claim_type="diagnosis",
            direct_support=True,
            claim_metadata={
                "general_guidance": False,
                "evidence_span": "、".join(checks),
                "fact_type": "led_checklist",
                "source_page": top.page,
                "source_section": top.section,
                "inference_level": "bounded_inference",
                "expected_led_groups": expected,
                "found_led_groups": checks,
                "missing_led_groups": missing,
                "coverage_ratio": coverage_ratio,
                "partial_coverage": bool(missing),
            },
        )
