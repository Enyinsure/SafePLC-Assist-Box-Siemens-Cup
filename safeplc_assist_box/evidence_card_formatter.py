#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SafePLC-Assist Box 证据卡片格式化工具。

功能：
1. 从统一 Orchestrator 输出中提取安全等级。
2. 提取证据页码、figure_id、证据类型。
3. 生成前端可展示的证据卡片数据。
4. 不引入第三方依赖。
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional


HIGH_RISK_KEYWORDS = [
    "HIGH_RISK",
    "高风险",
    "危险操作",
    "拒绝",
    "不能提供",
    "不提供",
    "不应提供",
    "短接安全回路",
    "强制输出",
    "带电接",
]

CLARIFY_KEYWORDS = [
    "需要澄清",
    "请补充",
    "缺少型号",
    "缺少订货号",
    "无法确定具体模块",
    "请提供",
]

NORMAL_KEYWORDS = [
    "NORMAL",
    "证据",
    "页码",
    "根据手册",
    "允许范围",
]


def unique_keep_order(items: List[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        item = str(item).strip()
        if not item:
            continue
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def detect_safety_level(text: str) -> str:
    upper_text = text.upper()
    if "HIGH_RISK" in upper_text:
        return "HIGH_RISK"

    if any(keyword in text for keyword in HIGH_RISK_KEYWORDS):
        if any(k in text for k in ["短接", "带电", "强制输出", "危险操作", "安全回路"]):
            return "HIGH_RISK"

    if any(keyword in text for keyword in CLARIFY_KEYWORDS):
        return "NEED_CLARIFICATION"

    if any(keyword in text for keyword in NORMAL_KEYWORDS):
        return "NORMAL"

    if text.strip():
        return "NORMAL"

    return "UNKNOWN"


def extract_evidence_pages(text: str) -> List[str]:
    patterns = [
        r"第\s*(\d{1,6})\s*页",
        r"页码\s*[:：]\s*(\d{1,6})",
        r"page\s*[:：]?\s*(\d{1,6})",
        r"Page\s*[:：]?\s*(\d{1,6})",
        r"p\.\s*(\d{1,6})",
    ]

    pages: List[str] = []
    for pattern in patterns:
        pages.extend(re.findall(pattern, text))

    return unique_keep_order(pages)


def extract_figure_ids(text: str) -> List[str]:
    patterns = [
        r"figure_id\s*[:：]\s*([A-Za-z0-9_\-./]+)",
        r"figure\s*id\s*[:：]\s*([A-Za-z0-9_\-./]+)",
        r"图像ID\s*[:：]\s*([A-Za-z0-9_\-./]+)",
        r"图文证据\s*[:：]\s*([A-Za-z0-9_\-./]+)",
    ]

    figures: List[str] = []
    for pattern in patterns:
        figures.extend(re.findall(pattern, text, flags=re.IGNORECASE))

    return unique_keep_order(figures)


def infer_evidence_types(text: str) -> List[str]:
    evidence_types: List[str] = []

    if any(k in text for k in ["表格", "table", "Table"]):
        evidence_types.append("表格证据")

    if any(k in text for k in ["接口图", "接线图", "端子", "拓扑图", "图文", "figure", "Figure", "HMI", "PROFINET"]):
        evidence_types.append("图文证据")

    if any(k in text for k in ["页码", "第", "手册", "根据手册"]):
        evidence_types.append("文本证据")

    if any(k in text for k in ["安全", "危险", "拒绝", "HIGH_RISK"]):
        evidence_types.append("安全护栏判断")

    if not evidence_types and text.strip():
        evidence_types.append("回答文本")

    return unique_keep_order(evidence_types)


def summarize_answer(text: str, max_chars: int = 360) -> str:
    cleaned_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.lower().startswith("[stderr]"):
            break
        cleaned_lines.append(stripped)

    cleaned = " ".join(cleaned_lines)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    if not cleaned:
        return "未生成回答摘要。"

    if len(cleaned) <= max_chars:
        return cleaned

    return cleaned[:max_chars].rstrip() + "..."


def detect_status(text: str, return_code: Optional[int] = None) -> str:
    if return_code not in (None, 0):
        return "BACKEND_WARNING"

    if "ERROR:" in text:
        return "ERROR"

    safety = detect_safety_level(text)
    if safety == "HIGH_RISK":
        return "SAFE_REFUSAL"
    if safety == "NEED_CLARIFICATION":
        return "WAITING_FOR_CONTEXT"
    if safety == "NORMAL":
        return "ANSWERED"

    return "UNKNOWN"


def build_evidence_cards(
    answer: str,
    query: str = "",
    context: str = "",
    return_code: Optional[int] = None,
) -> Dict[str, object]:
    safety_level = detect_safety_level(answer)
    pages = extract_evidence_pages(answer)
    figures = extract_figure_ids(answer)
    evidence_types = infer_evidence_types(answer)
    status = detect_status(answer, return_code=return_code)

    return {
        "query": query,
        "context": context,
        "safety_level": safety_level,
        "status": status,
        "evidence_pages": pages,
        "figure_ids": figures,
        "evidence_types": evidence_types,
        "answer_summary": summarize_answer(answer),
    }


if __name__ == "__main__":
    import sys

    content = sys.stdin.read()
    print(build_evidence_cards(content))
