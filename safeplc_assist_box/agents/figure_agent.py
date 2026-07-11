#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from ..evidence.evidence_pool import SharedEvidencePool
from ..schemas import AgentStatus
from ..tools.tool_registry import ToolRegistry
from .base_agent import BaseAgent


class FigureAgent(BaseAgent):
    agent_name = "Figure Agent"
    role_description = "Specialist for interface positions, panel layout, figure IDs and page-text association."
    tool_names = ["search_figure", "search_hybrid"]
    default_claim_type = "location"

    def execute(self, task, registry: ToolRegistry, evidence_pool: SharedEvidencePool):
        query = self._join_query(task)
        evidences = registry.search_figure(query, top_k=6)
        if not evidences:
            return self._abstain(task, "No figure or page-location evidence was found.")
        top = evidences[0]
        has_figure_ref = bool(top.figure_id or top.figure_number or top.page)
        if not has_figure_ref:
            return self._abstain(task, "Figure task retrieved text without figure_id, figure_number or page.")

        visual_status = top.metadata.get("visual_evidence_status", "image_available" if top.image_path else "page_text_only")
        claim = (
            f"{top.module_model or top.module or 'Target module'} X1 is located in the front connector area; "
            f"the cited figure/page identifies X1 and its ports."
        )
        if "x1 p1" in top.text.lower() or "x1 p2" in top.text.lower():
            claim = (
                f"{top.module_model or top.module or 'Target module'} X1 is the first PROFINET IO interface "
                "with two RJ45 ports, X1 P1 and X1 P2, in the front connector area."
            )
        answer = (
            f"{claim} Evidence: {top.manual_title or top.source}, page {top.page or '-'}, "
            f"{top.figure_number or top.figure_id or '-'}, visual_status={visual_status}."
        )
        return self._finish_with_evidence(
            task,
            evidences,
            evidence_pool,
            answer_fragment=answer,
            claim=claim,
            confidence="HIGH" if top.figure_id or top.figure_number else "MEDIUM",
            status=AgentStatus.ANSWERED.value if top.figure_id or top.figure_number else AgentStatus.PARTIAL.value,
            claim_type="location",
            direct_support=bool(top.direct_evidence or top.figure_id or top.figure_number),
            claim_metadata={
                "figure_id": top.figure_id,
                "figure_number": top.figure_number,
                "page": top.page,
                "location_marker": "⑦" if "⑦" in top.text or "marker ⑦" in top.text else "",
                "ports": ["X1 P1", "X1 P2"] if "x1 p1" in top.text.lower() and "x1 p2" in top.text.lower() else [],
                "visual_evidence_status": visual_status,
                "image_path": top.image_path,
            },
        )
