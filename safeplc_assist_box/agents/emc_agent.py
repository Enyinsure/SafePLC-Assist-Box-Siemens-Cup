#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re

from ..evidence.evidence_pool import SharedEvidencePool
from ..schemas import AgentStatus
from ..tools.tool_registry import ToolRegistry
from .base_agent import BaseAgent
from ..evidence.evidence_ranker import rank_evidence
from ..evidence.fact_extractors import extract_emc_facts


class EMCAgent(BaseAgent):
    agent_name = "EMC Agent"
    role_description = "Specialist for EMC, shielding, grounding, cable layout and installation environment."
    tool_names = ["search_text", "search_hybrid"]
    default_claim_type = "procedure"

    def execute(self, task, registry: ToolRegistry, evidence_pool: SharedEvidencePool):
        query = self._join_query(task)
        evidences = rank_evidence(registry.search_text(query, top_k=10), query=query, top_k=12)
        selected = next(((item, extract_emc_facts(item.text)) for item in evidences if extract_emc_facts(item.text)), None)
        if not selected:
            return self._abstain(task, "No EMC evidence was found.")
        top, facts = selected
        claim = "".join(facts)
        if "屏蔽" in query and not re.search(r"屏蔽层|shield (?:connection|termination)", top.text, re.I):
            claim += "当前证据未直接覆盖屏蔽层连接方法，需要继续查证对应安装章节。"
        answer = f"{claim} Evidence: {top.manual_title or top.source}, page {top.page or '-'}."
        return self._finish_with_evidence(
            task,
            [top],
            evidence_pool,
            answer_fragment=answer,
            claim=claim,
            confidence="MEDIUM",
            status=AgentStatus.PARTIAL.value,
            claim_type="procedure",
            claim_metadata={
                "evidence_span": top.compact_excerpt,
                "fact_type": "emc_installation_measure",
                "source_page": top.page,
                "source_section": top.section,
                "inference_level": "direct",
                "partial_coverage": True,
            },
        )
