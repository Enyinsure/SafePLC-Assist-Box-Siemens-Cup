#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import List

from ..schemas import QueryContext, SubQuestion


class QueryDecomposer:
    """Rule-based atomic task splitter for deterministic offline operation."""

    def decompose(self, context: QueryContext) -> List[SubQuestion]:
        query = context.original_query
        if context.missing_slots or context.is_dangerous_operation:
            return []

        subquestions: List[SubQuestion] = []
        low = query.lower()
        if "x1" in low and any(token in query for token in ["哪里", "位置", "front", "where"]):
            subquestions.append(
                SubQuestion(
                    subquestion_id="sq_x1_location",
                    text="Locate the X1 physical interface.",
                    objective="Find the direct front-view or figure evidence for X1.",
                    expected_agents=["Figure Agent"],
                    required_modalities=["figure"],
                    required_slots=["module_model", "interface_name"],
                )
            )
        if "x1" in low and any(token in low for token in ["p1", "p2", "port", "端口", "接口"]):
            subquestions.append(
                SubQuestion(
                    subquestion_id="sq_x1_ports",
                    text="Identify X1 port count and labels.",
                    objective="Verify whether X1 has ports such as X1 P1 and X1 P2.",
                    expected_agents=["Figure Agent", "Topology Agent"],
                    required_modalities=["figure", "table"],
                )
            )
        if "profinet" in low or "hmi" in low:
            subquestions.append(
                SubQuestion(
                    subquestion_id="sq_profinet_hmi",
                    text="Check HMI and PROFINET connection guidance.",
                    objective="Separate model-specific interface evidence from general PROFINET guidance.",
                    expected_agents=["Topology Agent"],
                    required_modalities=["text"],
                )
            )
        if any(token in query for token in ["注意", "组态", "IP", "ip", "布线"]):
            subquestions.append(
                SubQuestion(
                    subquestion_id="sq_network_notes",
                    text="List supported network and cabling notes.",
                    objective="Return only evidenced PROFINET/HMI notes and mark general guidance.",
                    expected_agents=["Topology Agent", "Wiring Agent"],
                    required_modalities=["text"],
                )
            )

        if not subquestions:
            subquestions.append(
                SubQuestion(
                    subquestion_id="sq_main",
                    text=query,
                    objective=f"Answer the {context.question_type} question using direct evidence.",
                    expected_agents=[],
                    required_modalities=list(context.required_modalities),
                )
            )
        return subquestions[:4]
