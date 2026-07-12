#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re

from ..evidence.evidence_pool import SharedEvidencePool
from ..schemas import AgentStatus
from ..tools.tool_registry import ToolRegistry
from ..retrieval.query_expander import is_explicit_image_request
from ..evidence.model_identity import extract_model_identity
from ..tools.metadata_normalizer import extract_location_marker
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
        interface_slot = str(getattr(task, "input_slots", {}).get("interface_name") or "")
        interface_match = re.search(r"\bX\d+\b", interface_slot or task.query, re.I)
        interface_name = interface_match.group(0).upper() if interface_match else ""
        slot_model = str(getattr(task, "input_slots", {}).get("module_model") or "")
        query_model = extract_model_identity(f"{task.query} {getattr(task, 'context', '')}").normalized_model
        target_model = slot_model or query_model or top.module_model or top.module or "目标模块"
        ports_requested = "sq_x1_ports" in (getattr(task, "subquestion_ids", []) or [])
        image_requested = is_explicit_image_request(query)
        marker = extract_location_marker(top.text, interface_name)
        if not marker and str(top.metadata.get("location_marker_interface") or "").upper() == interface_name:
            marker = str(top.metadata.get("location_marker") or "")
        interface_low = interface_name.lower()
        has_two_ports = bool(re.search(r"(?:带|with)\s*2\s*(?:个\s*)?(?:端口|ports?)", top.text, re.I)) or (
            bool(interface_low) and f"{interface_low} p1" in top.text.lower() and f"{interface_low} p2" in top.text.lower()
        )
        front_location = "拆下前面板后可见的模块前部连接区域" if "不带前面板" in top.text else "模块前部连接区域"
        claim = (
            f"{target_model} {interface_name or '目标接口'} is located in the {front_location}; "
            f"the cited manual front-view text identifies {interface_name or 'the interface'}" + (f" with marker {marker}" if marker else "") + "."
        )
        if ports_requested and interface_low and f"{interface_low} p1" in top.text.lower() and f"{interface_low} p2" in top.text.lower():
            claim = (
                f"{target_model} {interface_name} is a PROFINET IO interface with two RJ45 ports, "
                f"{interface_name} P1 and {interface_name} P2, in the front connector area."
            )
        elif has_two_ports:
            claim = claim.rstrip(".") + f"; {interface_name or 'the interface'} is a PROFINET IO interface with two ports."
        answer = (
            f"{claim} Evidence: {top.manual_title or top.source}, page {top.page or '-'}, "
            f"{top.manual_figure_number or top.figure_number or '-'}, visual_status={visual_status}."
        )
        result = self._finish_with_evidence(
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
                "location_marker_interface": interface_name if marker else "",
                "interface_name": interface_name,
                "ports": [f"{interface_name} P1", f"{interface_name} P2"] if ports_requested and interface_low and f"{interface_low} p1" in top.text.lower() and f"{interface_low} p2" in top.text.lower() else [],
                "has_two_ports": has_two_ports,
                "visual_evidence_status": visual_status,
                "image_path": top.resolved_image_path,
                "visual_image_required": image_requested,
                "evidence_span": top.compact_excerpt,
                "fact_type": "interface_location_and_ports" if has_two_ports else "interface_location",
                "source_page": top.page,
                "source_section": top.section,
                "inference_level": "direct",
            },
        )
        if result.claims and target_model != "目标模块":
            result.claims[0].model_scope = target_model
        return result
