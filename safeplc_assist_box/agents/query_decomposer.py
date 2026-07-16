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
        model = context.slots.get("module_model").value if context.slots.get("module_model") else ""
        model_prefix = f"{model} 的 " if model else ""

        # A work order is an output format, not an evidence source. First route
        # the problem to the relevant specialist; the Work-order Agent is added
        # later by Supervisor and consumes the shared Evidence Pool.
        if context.question_type == "WORK_ORDER":
            if any(token in low for token in ["电压", "电流", "功率", "参数", "额定", "允许范围"]):
                specialist = "Parameter Agent"
                objective = "Verify the requested parameter before exporting the maintenance record."
                modalities = ["table", "text"]
            elif any(token in low for token in ["接线", "端子", "线缆", "极性", "线径"]):
                specialist = "Wiring Agent"
                objective = "Verify wiring requirements before exporting the maintenance record."
                modalities = ["text", "table", "figure"]
            else:
                specialist = "Troubleshooting Agent"
                objective = "Retrieve supported diagnostic checks before exporting the maintenance record."
                modalities = ["text", "table"]
            subquestions.append(
                SubQuestion(
                    subquestion_id="sq_work_order_evidence",
                    text=query,
                    objective=objective,
                    expected_agents=[specialist],
                    required_modalities=modalities,
                    metadata={"trigger": "work_order_evidence_first", "source_span": query},
                )
            )

        if "x1" in low and any(token in low for token in ["哪里", "位置", "前面", "front", "where"]):
            subquestions.append(
                SubQuestion(
                    subquestion_id="sq_x1_location",
                    text=f"{model_prefix}X1 接口物理位置在哪里？",
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
                    text=f"{model_prefix}X1 包含几个端口？",
                    objective="Verify whether X1 has ports such as X1 P1 and X1 P2.",
                    expected_agents=["Figure Agent"],
                    required_modalities=["figure", "table"],
                    metadata={"trigger": port_trigger, "source_span": query},
                )
            )
        if "profinet" in low or "hmi" in low:
            subquestions.append(
                SubQuestion(
                    subquestion_id="sq_profinet_hmi",
                    text=f"{model_prefix}核对 HMI 与 PROFINET 的设备连接关系。",
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
                    expected_agents=["Topology Agent"],
                    required_modalities=["text"],
                    metadata={"trigger": "network_notes", "source_span": query},
                )
            )
        if any(token in low for token in ["通信不上", "通信异常", "通信中断", "指示灯异常", "led", "run/stop", "error"]):
            subquestions.append(
                SubQuestion(
                    subquestion_id="sq_comm_led_diagnosis",
                    text=f"{model_prefix}通信异常时，应先核对哪些 LED、接口和诊断信息？",
                    objective="Extract only communication and LED checks supported by the manual evidence.",
                    expected_agents=["Troubleshooting Agent"],
                    required_modalities=["text"],
                    metadata={"trigger": "communication_led", "source_span": query},
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
