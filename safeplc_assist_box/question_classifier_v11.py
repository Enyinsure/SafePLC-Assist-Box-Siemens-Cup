#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Dict, List
import re


QUESTION_TYPES = {
    "PARAM_QUERY": "参数查询",
    "FIGURE_QUERY": "图纸/接口/端子图查询",
    "WIRING_QUERY": "接线查询",
    "TOPOLOGY_QUERY": "拓扑查询",
    "TROUBLESHOOTING": "故障排查",
    "SAFETY_RISK": "安全风险",
    "WORK_ORDER": "运维记录生成",
    "EMC_ENV": "EMC/环境/安装规范",
    "OUT_OF_SCOPE": "超出系统边界",
}


def _has_any(text: str, words: List[str]) -> bool:
    t = text.lower()
    return any(w.lower() in t for w in words)


def extract_slots(question: str, context: str = "") -> Dict[str, str]:
    text = f"{question}\n{context}".strip()

    module_patterns = [
        r"CPU\s*\d{4,5}[-\w\s/]*",
        r"PS\s*\d+W\s*[\d/]+VDC\s*\w*",
        r"ET\s*200MP",
        r"S7[- ]?1500",
        r"\dES\d\s*[\w\-]+",
    ]

    interface_patterns = [
        r"\bX\d+\b",
        r"PROFINET",
        r"PROFIBUS",
        r"RJ45",
        r"HMI",
    ]

    def first_match(patterns):
        for p in patterns:
            m = re.search(p, text, flags=re.IGNORECASE)
            if m:
                return re.sub(r"\s+", " ", m.group(0)).strip()
        return ""

    parameter_keywords = [
        "电源电压", "输入电压", "电压", "允许范围", "额定值", "额定", "电流", "功率", "EMC", "电磁兼容",
        "环境温度", "安装", "端子", "接口", "拓扑", "环网", "订货号", "是什么", "关系"
    ]

    parameter = ""
    for kw in parameter_keywords:
        if kw.lower() in text.lower():
            parameter = kw
            break

    alarm = ""
    m = re.search(
        r"(报错|故障|报警|error|fault|alarm)[：:\s]*([\w\u4e00-\u9fa5\- ]{0,40})",
        text,
        flags=re.IGNORECASE,
    )
    if m:
        alarm = m.group(0).strip()

    if not alarm and _has_any(text, [
        "通信不上", "通信异常", "通信中断", "不能启动", "无法运行",
        "冒烟", "起火", "火灾", "触电", "电击", "电气事故", "有人被电"
    ]):
        alarm = "故障/应急现象"

    return {
        "module_or_order_no": first_match(module_patterns),
        "interface_or_port": first_match(interface_patterns),
        "parameter_name": parameter,
        "network_type": "PROFINET" if _has_any(text, ["profinet", "环网", "拓扑"]) else "",
        "device_type": "HMI" if _has_any(text, ["hmi", "触摸屏", "人机界面"]) else "",
        "fault_or_alarm": alarm,
        "indicator_state": "指示灯" if _has_any(text, ["指示灯", "led", "红灯", "绿灯", "黄灯"]) else "",
    }


def build_clarify_prompt(qtype: str, missing_slots: List[str]) -> str:
    if not missing_slots:
        return ""

    slot_cn = {
        "module_or_order_no": "模块型号或订货号",
        "parameter_name": "要查询的参数名称",
        "interface_or_port": "接口名或端口号，例如 X1、X2",
        "network_type": "网络类型，例如 PROFINET",
        "device_type": "设备类型，例如 HMI、CPU、ET 200MP",
        "fault_or_alarm": "报错信息、报警号或故障现象",
        "indicator_state": "指示灯状态",
    }

    items = "、".join(slot_cn.get(s, s) for s in missing_slots)

    examples = {
        "PARAM_QUERY": "例如：PS 60W 24/48/60VDC HF 的电源电压允许范围是多少？",
        "FIGURE_QUERY": "例如：CPU 1517-3 PN 的 PROFINET 接口 X1、X2 在哪一页？",
        "WIRING_QUERY": "例如：某模块的 X1 接口接线或端子分配图在哪里？",
        "TOPOLOGY_QUERY": "例如：PROFINET 环网如何连接 HMI 设备？",
        "TROUBLESHOOTING": "例如：CPU 1517-3 PN 出现某报警/指示灯状态时如何排查？",
    }

    return f"为了避免误检索，请补充：{items}。{examples.get(qtype, '')}".strip()


def classify_question(question: str, context: str = "") -> Dict[str, object]:
    text = f"{question}\\n{context}".strip()
    slots = extract_slots(question, context)

    # 真实控制/写入/下载/接入类请求：超出当前离线知识问答边界
    if _has_any(text, ["控制真实 plc", "真实 plc", "启动电机", "下载程序到 plc", "连接 tia portal", "tia portal", "改程序", "读取真实 ot", "真实 ot 网络"]):
        qtype = "OUT_OF_SCOPE"

    # 明确危险操作：进入安全护栏
    elif _has_any(text, [
        "短接", "屏蔽安全门", "屏蔽安全", "绕过", "解除保护", "让设备继续运行",
        "安全回路", "急停失效", "绕过急停", "带电接线", "带电接", "强制输出",
        "强制运行", "让执行器动作"
    ]):
        qtype = "SAFETY_RISK"

    # 运维记录类优先于接线/安全词，避免“安全检查记录”被误判
    elif _has_any(text, ["运维记录", "维修记录", "维护记录", "工单", "巡检记录", "安全检查记录", "生成记录"]):
        qtype = "WORK_ORDER"

    # 故障/报警/通信异常/应急事件
    elif _has_any(text, [
        "故障", "报警", "报错", "不能启动", "无法运行", "指示灯", "diagnostic",
        "error", "fault", "冒烟", "触电", "电击", "火灾", "起火", "电气事故",
        "伤人", "通信不上", "通信异常", "怎么排查", "排查"
    ]):
        qtype = "TROUBLESHOOTING"

    # 接口图 / X1 / X2 / 端子分配图属于图文证据查询；
    # 即使同时包含 PROFINET，也应优先判为 FIGURE_QUERY，而不是拓扑查询。
    elif _has_any(text, ["接口图", "接口", "x1", "x2", "figure", "端子分配图", "图在哪里", "图纸"]):
        qtype = "FIGURE_QUERY"

    # 拓扑/网络类低于明确接口图查询，但高于泛化接线词。
    elif _has_any(text, ["拓扑", "环网", "profinet", "hmi", "网络如何连接", "网络连接"]):
        qtype = "TOPOLOGY_QUERY"

    elif _has_any(text, ["接线", "端子", "接入", "接到", "线怎么接"]):
        qtype = "WIRING_QUERY"

    elif _has_any(text, ["emc", "电磁兼容", "环境", "安装要求", "规范", "接地", "屏蔽"]):
        qtype = "EMC_ENV"

    elif _has_any(text, ["电压", "电流", "功率", "额定", "允许范围", "参数", "规格", "订货号", "是什么", "关系", "s7-1500", "et 200mp"]):
        qtype = "PARAM_QUERY"

    else:
        qtype = "OUT_OF_SCOPE"

    required_slots = {
        "PARAM_QUERY": ["parameter_name"],
        "WIRING_QUERY": ["module_or_order_no", "interface_or_port"],
        "FIGURE_QUERY": ["module_or_order_no", "interface_or_port"],
        "TOPOLOGY_QUERY": ["network_type"],
        "TROUBLESHOOTING": ["module_or_order_no", "fault_or_alarm"],
        "SAFETY_RISK": [],
        "WORK_ORDER": [],
        "EMC_ENV": [],
        "OUT_OF_SCOPE": [],
    }.get(qtype, [])

    missing_slots = [s for s in required_slots if not slots.get(s)]

    # 泛指“这个模块/某个模块/这个型号”时，参数查询仍需澄清具体型号或订货号
    if qtype == "PARAM_QUERY":
        vague_model_ref = _has_any(text, ["某个模块", "这个模块", "该模块", "这个型号", "该型号"])
        if vague_model_ref and not slots.get("module_or_order_no"):
            if "module_or_order_no" not in missing_slots:
                missing_slots.insert(0, "module_or_order_no")

    # 端子分配图属于图文证据查询；如果已有模块对象，不强制要求具体 X1/X2
    if qtype == "FIGURE_QUERY" and _has_any(text, ["端子分配图"]):
        if slots.get("module_or_order_no") and "interface_or_port" in missing_slots:
            missing_slots.remove("interface_or_port")

    if missing_slots:
        action = "CLARIFY"
    elif qtype == "SAFETY_RISK":
        action = "SAFETY_GUARD"
    elif qtype == "OUT_OF_SCOPE":
        action = "BOUNDARY_REPLY"
    else:
        action = "RETRIEVE"

    retrieval_route = {
        "PARAM_QUERY": "table_first",
        "WIRING_QUERY": "figure_first",
        "FIGURE_QUERY": "figure_first",
        "TOPOLOGY_QUERY": "figure_text_hybrid",
        "TROUBLESHOOTING": "text_table_hybrid",
        "EMC_ENV": "text_section_first",
        "WORK_ORDER": "template_generation",
        "SAFETY_RISK": "safety_guard",
        "OUT_OF_SCOPE": "no_retrieval",
    }.get(qtype, "text_first")

    return {
        "question_type": qtype,
        "question_type_cn": QUESTION_TYPES.get(qtype, qtype),
        "slots": slots,
        "required_slots": required_slots,
        "missing_slots": missing_slots,
        "action": action,
        "retrieval_route": retrieval_route,
        "clarify_prompt": build_clarify_prompt(qtype, missing_slots),
    }


if __name__ == "__main__":
    cases = [
        ("某个模块的电源电压允许范围是多少", ""),
        ("某个模块的电源电压允许范围是多少", "PS 60W 24/48/60VDC HF"),
        ("CPU 1517-3 PN 的 PROFINET 接口 X1 X2", ""),
        ("怎么短接安全回路让设备继续运行", ""),
    ]

    for q, ctx in cases:
        print("=" * 60)
        print("问题：", q)
        print("上下文：", ctx)
        print(classify_question(q, ctx))
