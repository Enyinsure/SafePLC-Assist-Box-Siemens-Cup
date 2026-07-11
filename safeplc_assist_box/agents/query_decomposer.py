#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
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
        if "x1" in low and any(token in low for token in ["哪里", "位置", "前面", "front", "where"]):
            subquestions.append(
                SubQuestion(
                    subquestion_id="sq_x1_location",
                    text="Locate the X1 physical interface.",
                    objective="Find the direct front-view or figure evidence for X1.",
                    expected_agents=["Figure Agent"],
                    required_modalities=["figure"],
                    required_slots=["module_model", "interface_name"],
                    metadata={"trigger": "x1_location", "source_span": query},
                )
            )
        port_trigger = next(
            (
                token
                for token in [
                    "几个端口",
                    "端口数量",
                    "p1/p2",
                    "x1 p1",
                    "x1 p2",
                    "port count",
                    "ports",
                    "两个端口",
                    "端口标签",
                    "端口名称",
                ]
                if token in low
            ),
            "",
        )
        if "x1" in low and port_trigger:
            subquestions.append(
                SubQuestion(
                    subquestion_id="sq_x1_ports",
                    text="Identify X1 port count and labels.",
                    objective="Verify whether X1 has ports such as X1 P1 and X1 P2.",
                    expected_agents=["Figure Agent", "Topology Agent"],
                    required_modalities=["figure", "table"],
                    metadata={"trigger": port_trigger, "source_span": query},
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
                    metadata={"trigger": "PROFINET/HMI", "source_span": query},
                )
            )
        network_context = any(token in low for token in ["profinet", "hmi", "网络", "network", "ip", "组态"])
        if network_context and any(token in low for token in ["注意", "组态", "ip", "布线", "network"]):
            subquestions.append(
                SubQuestion(
                    subquestion_id="sq_network_notes",
                    text="List supported network and cabling notes.",
                    objective="Return only evidenced PROFINET/HMI notes and mark general guidance.",
                    expected_agents=["Topology Agent", "Wiring Agent"],
                    required_modalities=["text"],
                    metadata={"trigger": "network_notes", "source_span": query},
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
                    metadata={"trigger": context.question_type, "source_span": query},
                )
            )
        unique = []
        seen = set()
        for item in subquestions:
            key = (item.subquestion_id, re.sub(r"\s+", " ", item.text.strip().lower()))
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)
        return unique[:4]
