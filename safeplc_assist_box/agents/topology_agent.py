#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from ..evidence.evidence_pool import SharedEvidencePool
from ..schemas import AgentStatus
from ..tools.tool_registry import ToolRegistry
from .base_agent import BaseAgent
from ..evidence.fact_extractors import extract_topology_fact


class TopologyAgent(BaseAgent):
    agent_name = "Topology Agent"
    role_description = "Specialist for PROFINET, HMI, CPU, IO topology and device relationships."
    tool_names = ["search_hybrid", "search_text", "search_figure"]
    default_claim_type = "connection"

    def execute(self, task, registry: ToolRegistry, evidence_pool: SharedEvidencePool):
        query = self._join_query(task)
        evidences = registry.search_hybrid(query, modalities=["text", "table", "figure"], top_k=6)
        if not evidences:
            return self._abstain(task, "No topology evidence was found.")
        selected = next(((item, extract_topology_fact(item.text)) for item in evidences if extract_topology_fact(item.text)), None)
        if not selected:
            return self._abstain(task, "No direct scoped HMI/CPU interface relationship was found.")
        top, claim = selected
        answer = f"{claim} Evidence: {top.manual_title or top.source}, page {top.page or '-'}."
        return self._finish_with_evidence(
            task,
            [top],
            evidence_pool,
            answer_fragment=answer,
            claim=claim,
            confidence="HIGH",
            status=AgentStatus.ANSWERED.value,
            claim_type="connection",
            direct_support=True,
            claim_metadata={
                "interface": "PROFINET",
                "protocol": "PROFINET",
                "peer_device": "HMI" if "hmi" in query.lower() else "",
                "connection_limit": top.metadata.get("connection_limit", ""),
                "general_guidance": False,
                "scope_limited": True,
                "evidence_span": top.compact_excerpt,
                "fact_type": "scoped_topology_relationship",
                "source_page": top.page,
                "source_section": top.section,
                "inference_level": "direct",
            },
        )
