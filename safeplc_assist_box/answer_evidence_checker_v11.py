#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Dict, List
import re

try:
    from evidence_confidence_v11 import (
        EvidenceItem,
        extract_model_terms,
        extract_numeric_claims,
        evidence_contains,
        normalize_text,
    )
except ImportError:
    from .evidence_confidence_v11 import (
        EvidenceItem,
        extract_model_terms,
        extract_numeric_claims,
        evidence_contains,
        normalize_text,
    )


def extract_key_claims(answer: str) -> List[str]:
    claims: List[str] = []

    claims.extend(extract_model_terms(answer))
    claims.extend(extract_numeric_claims(answer))

    extra_patterns = [
        r"\bPROFINET\b",
        r"\bPROFIBUS\b",
        r"\bHMI\b",
        r"\bEMC\b",
        r"电磁兼容性",
        r"环网",
        r"拓扑",
        r"接线",
        r"端子",
        r"安全回路",
    ]

    for p in extra_patterns:
        for m in re.findall(p, answer, flags=re.IGNORECASE):
            item = normalize_text(m)
            if item and item.lower() not in {x.lower() for x in claims}:
                claims.append(item)

    return claims


def check_answer_evidence_alignment(answer: str, evidence_items: List[Any]) -> Dict[str, Any]:
    items = [EvidenceItem.from_any(x) for x in evidence_items]
    evidence_text = "\n".join([ev.all_text() for ev in items])

    claims = extract_key_claims(answer)

    if not claims:
        return {
            "support_rate": 1.0,
            "supported_claims": [],
            "unsupported_claims": [],
            "verdict": "PASS",
            "note": "未抽取到需要校验的结构化关键声明。",
        }

    supported = []
    unsupported = []

    for claim in claims:
        if evidence_contains(evidence_text, claim):
            supported.append(claim)
        else:
            unsupported.append(claim)

    support_rate = len(supported) / max(len(claims), 1)

    if support_rate >= 0.9 and not unsupported:
        verdict = "PASS"
    elif support_rate >= 0.6:
        verdict = "REVIEW"
    else:
        verdict = "FAIL"

    return {
        "support_rate": round(support_rate, 3),
        "supported_claims": supported,
        "unsupported_claims": unsupported,
        "verdict": verdict,
        "note": {
            "PASS": "答案关键声明基本可由证据支撑。",
            "REVIEW": "部分关键声明未在证据中闭合，建议人工复核。",
            "FAIL": "答案与证据一致性不足，不建议直接输出。",
        }[verdict],
    }


if __name__ == "__main__":
    evidence = [{
        "source": "S7-1500 / ET 200MP 中文手册",
        "page": 2478,
        "evidence_type": "figure",
        "figure_id": "fig_cpu1517_3pn_x1_x2",
        "title": "CPU 1517-3 PN 接口图",
        "text": "CPU 1517-3 PN 包含 PROFINET 接口 X1 和 X2。"
    }]

    answer_ok = "CPU 1517-3 PN 的 PROFINET 接口包括 X1 和 X2，证据页码 2478。"
    answer_bad = "CPU 1517-3 PN 的 PROFINET 接口包括 X1、X2 和 X9，证据页码 9999。"

    print("=" * 60)
    print("PASS 测试")
    print(check_answer_evidence_alignment(answer_ok, evidence))

    print("=" * 60)
    print("REVIEW/FAIL 测试")
    print(check_answer_evidence_alignment(answer_bad, evidence))
