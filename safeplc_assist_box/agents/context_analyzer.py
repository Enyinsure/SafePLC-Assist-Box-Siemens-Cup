#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
from typing import Dict, List

from ..schemas import QueryContext, SlotResult


def _has_any(text: str, words: List[str]) -> bool:
    low = text.lower()
    return any(w.lower() in low for w in words)


class ContextAnalyzer:
    slot_names = [
        "module_model",
        "order_number",
        "parameter_name",
        "interface_name",
        "port_number",
        "alarm_code",
        "indicator_state",
        "network_type",
        "device_type",
        "operating_condition",
        "expected_output_type",
    ]

    def analyze(self, query: str, context: str = "") -> QueryContext:
        text = f"{query}\n{context}".strip()
        normalized = re.sub(r"\s+", " ", text).strip()
        slots = self._extract_slots(text)
        risk = self._assess_risk(text)
        qtype = self._question_type(text, slots, risk)
        required_modalities = self._required_modalities(qtype, text)
        missing = self._missing_slots(qtype, text, slots)
        clarify = self._clarification_prompt(missing, qtype)

        return QueryContext(
            original_query=query,
            context=context,
            normalized_query=normalized,
            question_type=qtype,
            slots=slots,
            missing_slots=missing,
            required_modalities=required_modalities,
            risk_level=risk["risk_level"],
            risk_decision=risk["decision"],
            risk_reason=risk["reason"],
            is_dangerous_operation=risk["risk_level"] in {"HIGH_RISK", "EMERGENCY"},
            expected_output_type=slots["expected_output_type"].value or "answer",
            clarify_question=clarify,
            metadata={"analyzer": "Context Analyzer"},
        )

    def _extract_slots(self, text: str) -> Dict[str, SlotResult]:
        def first(patterns: List[str]) -> str:
            for pat in patterns:
                m = re.search(pat, text, flags=re.IGNORECASE)
                if m:
                    return re.sub(r"\s+", " ", m.group(0)).strip()
            return ""

        module = first(
            [
                r"CPU\s*\d{4,5}(?:-\d)?(?:\s*[A-Z]{1,4})?",
                r"PS\s*\d+W\s*[\d/]+VDC\s*\w*",
                r"ET\s*200MP",
                r"S7[- ]?1500",
            ]
        )
        order_number = first([r"\b\dES\d[\w\-]*\b", r"\b6ES\d[\w\-]*\b"])
        interface = first([r"\bX\d+\b", r"PROFINET", r"PROFIBUS", r"RJ45"])
        port = first([r"\bX\d+\b", r"端口\s*\d+", r"port\s*\d+"])
        alarm = first([r"(?:报警|报错|故障|error|fault|alarm)[：:\s]*[\w\u4e00-\u9fff\- ]{0,40}"])

        parameter = ""
        for word in [
            "电源电压",
            "输入电压",
            "允许范围",
            "额定",
            "电流",
            "功率",
            "温度",
            "订货号",
            "端子",
            "接口",
            "拓扑",
            "EMC",
            "接地",
            "屏蔽",
        ]:
            if word.lower() in text.lower():
                parameter = word
                break

        values = {
            "module_model": module,
            "order_number": order_number,
            "parameter_name": parameter,
            "interface_name": interface,
            "port_number": port,
            "alarm_code": alarm,
            "indicator_state": "指示灯" if _has_any(text, ["指示灯", "LED", "红灯", "绿灯", "黄灯"]) else "",
            "network_type": "PROFINET" if _has_any(text, ["PROFINET", "环网", "拓扑"]) else "",
            "device_type": "HMI" if _has_any(text, ["HMI", "触摸屏", "人机界面"]) else ("CPU" if "CPU" in text.upper() else ""),
            "operating_condition": "离线查证" if _has_any(text, ["查", "查询", "在哪里", "说明"]) else "",
            "expected_output_type": "work_order" if _has_any(text, ["工单", "运维记录", "维护记录"]) else "answer",
        }
        return {
            name: SlotResult(
                name=name,
                value=values.get(name, ""),
                confidence=0.9 if values.get(name) else 0.0,
                required=False,
            )
            for name in self.slot_names
        }

    def _assess_risk(self, text: str) -> Dict[str, str]:
        emergency = ["火灾", "起火", "冒烟", "触电", "电击", "人员伤害", "爆炸"]
        dangerous = [
            "短接安全回路",
            "短接急停",
            "绕过急停",
            "绕过保护",
            "屏蔽安全门",
            "带电接线",
            "带电拆线",
            "强制输出",
            "强制运行",
            "控制真实 PLC",
            "下载程序到 PLC",
        ]
        caution = ["接线", "端子", "上电", "断电", "调试", "复位", "接地", "屏蔽"]
        if _has_any(text, emergency):
            return {
                "risk_level": "EMERGENCY",
                "decision": "REFUSE_DANGEROUS_STEPS",
                "reason": "涉及事故或人身安全，需要现场应急流程。",
            }
        if _has_any(text, dangerous):
            return {
                "risk_level": "HIGH_RISK",
                "decision": "REFUSE_DANGEROUS_STEPS",
                "reason": "涉及绕过保护、带电操作、强制输出或真实 PLC 控制。",
            }
        if _has_any(text, caution):
            return {
                "risk_level": "CAUTION",
                "decision": "ANSWER_WITH_SAFETY_TIP",
                "reason": "涉及接线、调试或安装注意事项，需要安全提示。",
            }
        return {"risk_level": "SAFE", "decision": "ALLOW", "reason": "未识别到危险工业操作。"}

    def _question_type(self, text: str, slots: Dict[str, SlotResult], risk: Dict[str, str]) -> str:
        if risk["risk_level"] in {"HIGH_RISK", "EMERGENCY"}:
            return "SAFETY_BOUNDARY"
        if _has_any(text, ["工单", "运维记录", "维护记录"]):
            return "WORK_ORDER"
        if _has_any(text, ["故障", "报警", "通信不上", "通信异常", "不能启动", "指示灯", "排查"]):
            return "TROUBLESHOOTING"
        if _has_any(text, ["拓扑", "环网", "HMI", "网络连接"]):
            return "TOPOLOGY"
        if _has_any(text, ["接口图", "图纸", "图在哪里", "前面板", "端子图", "X1", "X2"]):
            return "FIGURE"
        if _has_any(text, ["接线", "端子", "怎么接", "线缆"]):
            return "WIRING"
        if _has_any(text, ["EMC", "电磁兼容", "接地", "屏蔽", "线缆布置", "安装距离"]):
            return "EMC"
        if _has_any(text, ["电压", "电流", "功率", "温度", "额定", "参数", "订货号", "允许范围"]):
            return "PARAMETER"
        return "GENERAL_INDUSTRIAL_QA"

    def _required_modalities(self, qtype: str, text: str) -> List[str]:
        mapping = {
            "PARAMETER": ["table", "text"],
            "FIGURE": ["figure", "text"],
            "WIRING": ["figure", "table", "text"],
            "TOPOLOGY": ["figure", "text"],
            "TROUBLESHOOTING": ["text", "table"],
            "EMC": ["text"],
            "SAFETY_BOUNDARY": ["policy"],
            "WORK_ORDER": ["text"],
        }
        return mapping.get(qtype, ["text"])

    def _missing_slots(self, qtype: str, text: str, slots: Dict[str, SlotResult]) -> List[str]:
        required: List[str] = []
        if qtype == "PARAMETER":
            required = ["parameter_name"]
            if _has_any(text, ["某个模块", "这个模块", "该模块", "模块的", "电源电压"]):
                required.append("module_model")
        elif qtype == "FIGURE":
            required = ["module_model", "interface_name"]
        elif qtype == "WIRING":
            required = ["module_model"]
        elif qtype == "TROUBLESHOOTING":
            required = []
            if not slots["indicator_state"].value and not slots["alarm_code"].value:
                required = ["alarm_code"]
        elif qtype == "TOPOLOGY":
            required = ["network_type"]
        missing = []
        for name in required:
            if not slots.get(name) or not slots[name].value:
                missing.append(name)
                slots[name].required = True
        return missing[:2]

    def _clarification_prompt(self, missing: List[str], qtype: str) -> str:
        if not missing:
            return ""
        names = {
            "module_model": "模块型号或订货号",
            "parameter_name": "要查询的参数名称",
            "interface_name": "接口名，例如 X1 或 X2",
            "alarm_code": "报警号、指示灯状态或故障现象",
            "network_type": "网络类型，例如 PROFINET",
        }
        items = "、".join(names.get(x, x) for x in missing[:2])
        examples = {
            "PARAMETER": "例如：PS 60W 24/48/60VDC HF 的电源电压允许范围是多少？",
            "FIGURE": "例如：CPU 1517-3 PN 的 X1 接口在哪里？",
            "TROUBLESHOOTING": "例如：CPU 1517-3 PN 的 ERROR 指示灯异常，通信不上。",
        }
        return f"为了让专业 Agent 精确查证，请补充{items}。{examples.get(qtype, '例如补充设备型号、接口名或故障现象。')}"
