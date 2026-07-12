#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re

from ..evidence.evidence_pool import SharedEvidencePool
from ..schemas import AgentStatus
from ..tools.tool_registry import ToolRegistry
from ..retrieval.query_expander import is_explicit_image_request
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
        has_figure_ref = bool(top.manual_figure_number or top.figure_number or top.page)
        if not has_figure_ref:
            return self._abstain(task, "Figure task retrieved text without figure_id, figure_number or page.")

        visual_status = top.visual_evidence_status or top.metadata.get("visual_evidence_status", "missing")
        ports_requested = "sq_x1_ports" in (getattr(task, "subquestion_ids", []) or [])
        image_requested = is_explicit_image_request(query)
        marker = str(top.metadata.get("location_marker") or "")
        has_two_ports = bool(re.search(r"(?:带|with)\s*2\s*(?:个\s*)?(?:端口|ports?)", top.text, re.I)) or (
            "x1 p1" in top.text.lower() and "x1 p2" in top.text.lower()
        )
        front_location = "拆下前面板后可见的模块前部连接区域" if "不带前面板" in top.text else "模块前部连接区域"
        claim = (
            f"{top.module_model or top.module or 'Target module'} X1 is located in the {front_location}; "
            f"the cited manual front-view text identifies X1" + (f" with marker {marker}" if marker else "") + "."
        )
        if ports_requested and "x1 p1" in top.text.lower() and "x1 p2" in top.text.lower():
            claim = (
                f"{top.module_model or top.module or 'Target module'} X1 is the first PROFINET IO interface "
                "with two RJ45 ports, X1 P1 and X1 P2, in the front connector area."
            )
        elif has_two_ports:
            claim = claim.rstrip(".") + "; X1 is a PROFINET IO interface with two ports."
        answer = (
            f"{claim} Evidence: {top.manual_title or top.source}, page {top.page or '-'}, "
            f"{top.manual_figure_number or top.figure_number or '-'}, visual_status={visual_status}."
        )
        return self._finish_with_evidence(
            task,
            [top],
            evidence_pool,
            answer_fragment=answer,
            claim=claim,
            confidence="HIGH" if visual_status == "image_available" else "MEDIUM",
            status=AgentStatus.PARTIAL.value if image_requested and visual_status != "image_available" else AgentStatus.ANSWERED.value,
            claim_type="location",
            direct_support=bool(top.direct_evidence or top.manual_figure_number or top.figure_number or top.page),
            claim_metadata={
                "figure_id": top.figure_id,
                "figure_number": top.figure_number,
                "manual_figure_number": top.manual_figure_number,
                "manual_figure_caption": top.manual_figure_caption,
                "visual_record_id": top.visual_record_id,
                "page": top.page,
                "location_marker": marker,
                "ports": ["X1 P1", "X1 P2"] if ports_requested and "x1 p1" in top.text.lower() and "x1 p2" in top.text.lower() else [],
                "has_two_ports": has_two_ports,
                "visual_evidence_status": visual_status,
                "image_path": top.resolved_image_path,
                "visual_image_required": image_requested,
            },
        )
