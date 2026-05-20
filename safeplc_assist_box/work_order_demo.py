#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SafePLC-Assist Box 运维辅助记录生成工具。

用途：
把一次工业知识问答整理成可展示、可下载、可贴到答辩材料中的运维辅助记录。
不引入第三方依赖。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from evidence_card_formatter import build_evidence_cards, summarize_answer


def build_safety_tip(safety_level: str) -> str:
    if safety_level == "HIGH_RISK":
        return (
            "系统已识别为高风险操作请求，拒绝提供短接、带电接线、强制输出等危险步骤。"
            "请遵守现场安全规程，执行停机、断电、挂牌上锁和专业人员审批流程。"
        )

    if safety_level == "NEED_CLARIFICATION":
        return (
            "当前问题缺少必要型号、订货号或模块上下文。"
            "建议先补充设备型号、模块名称、订货号或应用场景，再进行手册证据检索。"
        )

    if safety_level == "NORMAL":
        return (
            "请依据手册证据、现场设备铭牌和企业安全规程复核结果。"
            "本系统仅提供工业知识查询辅助，不执行真实控制动作。"
        )

    return (
        "请结合现场规程和人工复核使用本记录。"
        "本系统不连接真实 PLC，不替代工程师判断。"
    )


def generate_work_order_text(
    query: str,
    context: str,
    answer: str,
    operator: str = "SafePLC-Assist Box 演示用户",
    created_at: Optional[str] = None,
) -> str:
    created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cards = build_evidence_cards(answer, query=query, context=context)

    safety_level = str(cards.get("safety_level", "UNKNOWN"))
    status = str(cards.get("status", "UNKNOWN"))
    pages = cards.get("evidence_pages", [])
    figures = cards.get("figure_ids", [])
    evidence_types = cards.get("evidence_types", [])
    summary = summarize_answer(answer, max_chars=520)
    safety_tip = build_safety_tip(safety_level)

    page_text = "、".join([f"第 {p} 页" for p in pages]) if pages else "未提取到明确页码"
    figure_text = "、".join(figures) if figures else "未提取到 figure_id"
    evidence_type_text = "、".join(evidence_types) if evidence_types else "未识别"

    context_text = context.strip() if context.strip() else "无"

    return f"""SafePLC-Assist Box 运维辅助记录

记录时间：
{created_at}

记录人：
{operator}

问题：
{query}

用户补充上下文：
{context_text}

系统判断：
{safety_level}

处理状态：
{status}

回答摘要：
{summary}

证据页码：
{page_text}

图文证据：
{figure_text}

证据类型：
{evidence_type_text}

安全提示：
{safety_tip}

技术边界：
本记录由 SafePLC-Assist Box 工业知识安全问答终端生成。
系统仅用于 S7-1500 / ET 200MP 手册知识查询、证据辅助和安全提醒；
不连接真实 PLC，不进行真实 PLC 通信，不执行任何控制动作，
不能替代现场安全规程、工程师判断和企业审批流程。
"""


if __name__ == "__main__":
    demo = generate_work_order_text(
        query="某个模块的电源电压允许范围是多少",
        context="PS 60W 24/48/60VDC HF",
        answer="额定值：24 V / 48 V / 60 V；允许范围下限：静态 19.2 V，动态 18.5 V；允许范围上限：静态 72 V，动态 75.5 V；证据页码：第 6313 页。",
    )
    print(demo)
