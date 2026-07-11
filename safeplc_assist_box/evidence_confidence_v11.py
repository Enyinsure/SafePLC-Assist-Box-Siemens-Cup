#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
import re


CONFIDENCE_HIGH = "High"
CONFIDENCE_MEDIUM = "Medium"
CONFIDENCE_LOW = "Low"
CONFIDENCE_CONFLICT = "Conflict"


@dataclass
class EvidenceItem:
    source: str = ""
    page: Optional[int] = None
    figure_id: str = ""
    evidence_type: str = "text"
    title: str = ""
    text: str = ""
    module: str = ""
    parameter: str = ""
    score: Optional[float] = None
    meta: Optional[Dict[str, Any]] = None

    @classmethod
    def from_any(cls, obj: Any) -> "EvidenceItem":
        if isinstance(obj, cls):
            return obj

        if isinstance(obj, str):
            return cls(text=obj)

        if isinstance(obj, dict):
            return cls(
                source=str(obj.get("source", obj.get("doc", "")) or ""),
                page=_safe_int(obj.get("page", obj.get("page_no"))),
                figure_id=str(obj.get("figure_id", obj.get("fig_id", "")) or ""),
                evidence_type=str(obj.get("evidence_type", obj.get("type", "text")) or "text"),
                title=str(obj.get("title", obj.get("section", "")) or ""),
                text=str(obj.get("text", obj.get("content", obj.get("chunk", ""))) or ""),
                module=str(obj.get("module", obj.get("model", "")) or ""),
                parameter=str(obj.get("parameter", obj.get("param", "")) or ""),
                score=_safe_float(obj.get("score", obj.get("distance", None))),
                meta={},
            )

        return cls(
            source=str(getattr(obj, "source", "") or ""),
            page=_safe_int(getattr(obj, "page", None)),
            figure_id=str(getattr(obj, "figure_id", "") or ""),
            evidence_type=str(getattr(obj, "evidence_type", "text") or "text"),
            title=str(getattr(obj, "title", "") or ""),
            text=str(getattr(obj, "text", "") or ""),
            module=str(getattr(obj, "module", "") or ""),
            parameter=str(getattr(obj, "parameter", "") or ""),
            score=_safe_float(getattr(obj, "score", None)),
            meta=None,
        )

    def all_text(self) -> str:
        return " ".join([
            self.source or "",
            str(self.page or ""),
            self.figure_id or "",
            self.evidence_type or "",
            self.title or "",
            self.text or "",
            self.module or "",
            self.parameter or "",
        ])

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _safe_int(x: Any) -> Optional[int]:
    try:
        if x is None or x == "":
            return None
        return int(x)
    except Exception:
        return None


def _safe_float(x: Any) -> Optional[float]:
    try:
        if x is None or x == "":
            return None
        return float(x)
    except Exception:
        return None


def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = str(s).strip()
    s = s.replace("Ｖ", "V").replace("ｖ", "V").replace("－", "-").replace("—", "-")
    s = re.sub(r"\s+", " ", s)
    return s


def extract_model_terms(text: str) -> List[str]:
    if not text:
        return []

    t = normalize_text(text)

    patterns = [
        r"\bCPU\s*\d{4,5}(?:-\d)?(?:\s*[A-Z]{1,4})?\b",
        r"\bPS\s*\d+W\s*[\d/]+VDC\s*\w*\b",
        r"\bET\s*200MP\b",
        r"\bS7[- ]?1500\b",
        r"\b\dES\d\s*[\w\-]+\b",
        r"\bX\d+\b",
        r"\bPROFINET\b",
        r"\bPROFIBUS\b",
        r"\bEMC\b",
    ]

    terms: List[str] = []
    for p in patterns:
        for m in re.findall(p, t, flags=re.IGNORECASE):
            item = normalize_text(m).strip()
            if item and item.lower() not in {x.lower() for x in terms}:
                terms.append(item)

    return terms


def extract_numeric_claims(text: str) -> List[str]:
    if not text:
        return []

    t = normalize_text(text)

    patterns = [
        r"\b\d+(?:\.\d+)?\s*V(?:DC)?\b",
        r"\b\d+(?:\.\d+)?\s*A\b",
        r"\b\d+(?:\.\d+)?\s*W\b",
        r"\b[-+]?\d+(?:\.\d+)?\s*°?C\b",
        r"\bX\d+\b",
        r"第\s*\d+\s*页",
        r"页码[:：]?\s*\d+",
    ]

    claims: List[str] = []
    for p in patterns:
        for m in re.findall(p, t, flags=re.IGNORECASE):
            item = normalize_text(m).strip()
            if item and item.lower() not in {x.lower() for x in claims}:
                claims.append(item)

    return claims


def evidence_contains(evidence_text: str, term: str) -> bool:
    e_raw = normalize_text(evidence_text)
    x_raw = normalize_text(term)

    e = e_raw.lower()
    x = x_raw.lower()

    if not x:
        return True

    if x in e:
        return True

    if x.replace(" ", "") in e.replace(" ", ""):
        return True

    # 页码归一化：答案里可能写“页码 6313”或“第 6313 页”，
    # 证据字段里可能只保存为 page=6313。
    if "页" in x_raw or "页码" in x_raw:
        nums = re.findall(r"\d+", x_raw)
        if nums and any(num in e_raw for num in nums):
            return True

    return False


def assess_evidence_confidence(
    question: str,
    answer: str,
    evidence_items: List[Any],
) -> Dict[str, Any]:
    items = [EvidenceItem.from_any(x) for x in evidence_items]
    evidence_text = "\n".join([ev.all_text() for ev in items])

    q_terms = extract_model_terms(question)
    a_claims = extract_numeric_claims(answer)

    if not items or not normalize_text(evidence_text):
        return {
            "confidence": CONFIDENCE_LOW,
            "reason": "未检索到可用证据，不能形成可靠回答。",
            "missing": ["evidence"],
            "unsupported_claims": a_claims,
            "conflict_notes": [],
        }

    missing_terms = [t for t in q_terms if not evidence_contains(evidence_text, t)]
    unsupported_claims = [c for c in a_claims if not evidence_contains(evidence_text, c)]

    has_page = any(ev.page is not None for ev in items)
    has_type = any(ev.evidence_type for ev in items)
    has_model_hit = len(missing_terms) == 0 if q_terms else True
    answer_supported = len(unsupported_claims) == 0

    if has_page and has_type and has_model_hit and answer_supported:
        conf = CONFIDENCE_HIGH
        reason = "型号、关键词、页码和答案关键参数均能在证据中找到支撑。"
    elif has_page and has_type and (has_model_hit or answer_supported):
        conf = CONFIDENCE_MEDIUM
        reason = "证据与问题相关，但型号或部分答案参数未完全闭合，建议人工复核。"
    else:
        conf = CONFIDENCE_LOW
        reason = "证据链不完整，存在型号缺失或答案关键参数未被证据支撑。"

    return {
        "confidence": conf,
        "reason": reason,
        "missing": missing_terms,
        "unsupported_claims": unsupported_claims,
        "conflict_notes": [],
    }


def build_evidence_cards(evidence_items: List[Any], confidence: Optional[str] = None) -> List[Dict[str, Any]]:
    cards: List[Dict[str, Any]] = []

    for idx, raw in enumerate(evidence_items, start=1):
        ev = EvidenceItem.from_any(raw)
        snippet = normalize_text(ev.text)

        if len(snippet) > 260:
            snippet = snippet[:260] + "..."

        cards.append({
            "card_id": f"E{idx:02d}",
            "evidence_type": ev.evidence_type or "text",
            "page": ev.page,
            "figure_id": ev.figure_id,
            "source": ev.source,
            "title": ev.title,
            "module": ev.module,
            "parameter": ev.parameter,
            "score": ev.score,
            "confidence": confidence,
            "snippet": snippet,
        })

    return cards


def format_standard_answer(
    conclusion: str,
    basis: str,
    conditions: str = "",
    risk_tip: str = "",
) -> str:
    return (
        "【结论】\n"
        f"{conclusion.strip()}\n\n"
        "【依据】\n"
        f"{basis.strip()}\n\n"
        "【适用条件】\n"
        f"{(conditions or '仅适用于当前检索到的 S7-1500 / ET 200MP 手册证据范围，实际工程以设备铭牌、订货号、现场设计文件和厂家官方资料为准。').strip()}\n\n"
        "【风险提示】\n"
        f"{(risk_tip or '涉及接线、调试、带电作业和安全功能时，应由具备资质的人员在停机、断电、挂牌上锁等安全条件下操作。').strip()}"
    )


if __name__ == "__main__":
    question = "某个模块的电源电压允许范围是多少 PS 60W 24/48/60VDC HF"

    answer = (
        "额定值 24 V / 48 V / 60 V；"
        "允许范围下限静态 19.2 V、动态 18.5 V；"
        "上限静态 72 V、动态 75.5 V；证据页码 6313。"
    )

    evidence = [{
        "source": "S7-1500 / ET 200MP 中文手册",
        "page": 6313,
        "evidence_type": "table",
        "title": "PS 60W 24/48/60VDC HF 电源电压",
        "module": "PS 60W 24/48/60VDC HF",
        "parameter": "电源电压允许范围",
        "text": "额定值 24 V、48 V、60 V；允许范围下限 静态 19.2 V，动态 18.5 V；允许范围上限 静态 72 V，动态 75.5 V。"
    }]

    result = assess_evidence_confidence(question, answer, evidence)

    print("=" * 60)
    print("Evidence Confidence 测试")
    print(result)

    print("=" * 60)
    print("证据卡片测试")
    print(build_evidence_cards(evidence, result["confidence"]))

    print("=" * 60)
    print("标准回答结构测试")
    print(format_standard_answer(
        conclusion="该模块支持 24 V / 48 V / 60 V 额定输入。",
        basis="证据来自 S7-1500 / ET 200MP 中文手册第 6313 页表格。",
    ))
