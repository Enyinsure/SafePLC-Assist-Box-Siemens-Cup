#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from ..evidence.evidence_pool import SharedEvidencePool
from ..schemas import AgentStatus
from ..tools.tool_registry import ToolRegistry
from .base_agent import BaseAgent


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
        if "hmi" in query.lower() or "profinet" in query.lower():
            top = next(
                (
                    item
                    for item in evidences
                    if "hmi" in (item.text + " " + item.manual_title).lower()
                    or "general" in (item.manual_title or "").lower()
                ),
                evidences[0],
            )
        else:
            top = evidences[0]
        general = top.model_match_level == "same_family_general" or "general" in (top.manual_title or "").lower()
        claim = (
            "General PROFINET guidance: keep HMI/CPU device names, IP addresses, project topology "
            "and physical cabling consistent with the configured network."
            if general
            else f"{top.module_model or 'Target CPU'} topology guidance is supported by cited evidence."
        )
        answer = f"{claim} Evidence: {top.manual_title or top.source}, page {top.page or '-'}."
        return self._finish_with_evidence(
            task,
            [top],
            evidence_pool,
            answer_fragment=answer,
            claim=claim,
            confidence="MEDIUM" if general else "HIGH",
            status=AgentStatus.ANSWERED.value,
            claim_type="connection",
            direct_support=not general,
            claim_metadata={
                "interface": "PROFINET",
                "protocol": "PROFINET",
                "peer_device": "HMI" if "hmi" in query.lower() else "",
                "connection_limit": top.metadata.get("connection_limit", ""),
                "network_requirement": "unique IP/device name and matching topology" if general else "",
                "general_guidance": general,
            },
        )
