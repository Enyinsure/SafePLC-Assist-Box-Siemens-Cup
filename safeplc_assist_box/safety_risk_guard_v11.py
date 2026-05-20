#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Dict, List


def _hit(text: str, words: List[str]) -> List[str]:
    t = text.lower()
    return [w for w in words if w.lower() in t]


def assess_industrial_risk(question: str, context: str = "") -> Dict[str, object]:
    text = f"{question}\n{context}".strip()

    emergency_terms = [
        "火灾", "起火", "冒烟", "烧焦", "触电", "电击", "伤人", "受伤", "电气事故", "爆炸",
        "有人被电", "有人触电", "人员伤害", "急救", "控制柜起火"
    ]

    high_risk_terms = [
        "短接安全回路", "短接急停", "绕过保护", "绕过急停", "绕过急停按钮",
        "屏蔽安全门", "取消联锁", "强制运行", "强制输出", "让执行器动作",
        "带电接线", "带电拆线", "带电接", "解除保护", "让设备继续运行",
        "禁用安全", "控制真实 plc", "真实 plc 启动", "启动电机", "下载程序到 plc",
        "改程序", "bypass safety", "disable interlock"
    ]

    caution_terms = [
        "接线", "端子", "调试", "复位", "下载程序", "更换模块", "接入电源",
        "继电器", "安全门", "急停", "传感器", "上电", "断电",
        "报警", "故障", "通信不上", "通信异常", "排查", "接地", "屏蔽",
        "真实 ot", "ot 网络", "读取真实"
    ]

    em = _hit(text, emergency_terms)
    hi = _hit(text, high_risk_terms)
    ca = _hit(text, caution_terms)

    # “端子分配图”是图文证据查询，不等同于现场接线操作；
    # 若没有“接线/怎么接/带电”等操作词，则不因“端子”单独提升到 CAUTION。
    if "端子分配图" in text and not _hit(text, ["接线", "怎么接", "线怎么接", "带电", "接到", "接入"]):
        ca = [x for x in ca if x != "端子"]

    if em:
        level = "EMERGENCY"
        decision = "EMERGENCY_GUIDANCE"
        reason = f"检测到事故/人身安全相关关键词：{em}"
        safe_reply = (
            "这属于可能涉及人身伤害或电气事故的紧急情况。应立即停机，切断相关能源，"
            "执行现场应急预案和隔离措施，避免继续操作设备；如涉及人员伤害，应优先呼叫现场急救、消防或电气专业人员。"
            "我不能提供继续运行或现场处置的危险操作步骤。"
        )

    elif hi:
        level = "HIGH_RISK"
        decision = "REFUSE_DANGEROUS_STEPS"
        reason = f"检测到绕过、屏蔽安全功能或带电危险操作关键词：{hi}"
        safe_reply = (
            "这个问题涉及短接、绕过或屏蔽安全保护，我不能提供危险操作步骤。"
            "安全替代排查方向：保持设备停机和隔离状态，记录故障现象；检查急停、安全门、"
            "安全继电器或安全 PLC、传感器、线缆和报警信息是否异常；由具备资质的电气或自动化人员"
            "依据设备图纸、风险评估和厂家手册处理，确认安全功能恢复后再按规程复位。"
        )

    elif ca:
        level = "CAUTION"
        decision = "ANSWER_WITH_SAFETY_TIP"
        reason = f"检测到接线、调试、复位等谨慎操作关键词：{ca}"
        safe_reply = (
            "可以提供手册知识说明，但不替代现场作业规程。涉及接线、调试、上电、复位时，"
            "应先确认停机断电、挂牌上锁、回路无电压，并由具备资质人员按图纸和厂家手册执行。"
        )

    else:
        level = "SAFE"
        decision = "ALLOW"
        reason = "未检测到明显工业安全风险关键词。"
        safe_reply = ""

    return {
        "risk_level": level,
        "decision": decision,
        "reason": reason,
        "safe_alternative_reply": safe_reply,
    }


if __name__ == "__main__":
    test_questions = [
        "EMC 要求是什么",
        "这个端子怎么接线",
        "怎么短接安全回路让设备继续运行",
        "设备冒烟有人触电怎么办",
    ]

    for q in test_questions:
        print("=" * 60)
        print("问题：", q)
        print(assess_industrial_risk(q))
