#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


WIRING_ANCHORS = (
    "端子", "接线", "电源", "保护导线", "保护性导线", "SELV", "PELV",
    "极性", "线径", "屏蔽", "前连接器", "terminal", "wiring", "power",
    "protective conductor", "polarity", "wire size", "shield", "front connector",
)
WIRING_HEADING_FRAGMENTS = {
    "接线", "端子", "端子分配", "接线图", "方框图", "端子分配和接口说明", "接线图和方框图",
}


@dataclass
class ParameterFacts:
    parameter_name: str = ""
    rated_values: List[float] = field(default_factory=list)
    static_lower: Optional[float] = None
    dynamic_lower: Optional[float] = None
    static_upper: Optional[float] = None
    dynamic_upper: Optional[float] = None
    unit: str = "V DC"
    condition: str = ""
    evidence_span: str = ""

    @property
    def complete(self) -> bool:
        return all(value is not None for value in (self.static_lower, self.dynamic_lower, self.static_upper, self.dynamic_upper))


def extract_parameter_facts(text: str, parameter_intent: str = "") -> ParameterFacts:
    value = str(text or "")
    facts = ParameterFacts(parameter_name=parameter_intent or "电源电压允许范围", evidence_span=value[:600])
    rated_window = _rated_value_window(value)
    if rated_window:
        facts.rated_values = [float(item) for item in re.findall(r"(\d+(?:\.\d+)?)\s*V", rated_window, re.I)]
    static = _range(value, ("静态", "static"))
    dynamic = _range(value, ("动态", "dynamic"))
    if static:
        facts.static_lower, facts.static_upper = static
    if dynamic:
        facts.dynamic_lower, facts.dynamic_upper = dynamic
    bounded = _bounded_range_values(value)
    facts.static_lower = facts.static_lower if facts.static_lower is not None else bounded.get("static_lower")
    facts.dynamic_lower = facts.dynamic_lower if facts.dynamic_lower is not None else bounded.get("dynamic_lower")
    facts.static_upper = facts.static_upper if facts.static_upper is not None else bounded.get("static_upper")
    facts.dynamic_upper = facts.dynamic_upper if facts.dynamic_upper is not None else bounded.get("dynamic_upper")
    facts.condition = "静态/动态" if facts.complete else "部分范围"
    return facts


def _rated_value_window(text: str) -> str:
    title = re.search(
        r"(?:额定(?:值|输入)?|rated(?:\s+inputs?)?)(?:\s*[（(]\s*DC\s*[)）])?",
        text,
        re.I,
    )
    if not title:
        return ""
    tail = text[title.end():title.end() + 120]
    lines = tail.splitlines()
    if lines and not lines[0].strip():
        lines = lines[1:]
    window = "\n".join(lines[:2])
    return re.split(r"[。；;]|允许范围|静态范围|动态范围", window, maxsplit=1)[0]


def _bounded_range_values(text: str) -> dict[str, float]:
    header = re.compile(
        r"(?:允许范围\s*[,，]?\s*)?(?P<bound>下限|上限|lower|upper)"
        r"(?:\s*[（(]\s*DC\s*[)）])?",
        re.I,
    )
    matches = list(header.finditer(text))
    values: dict[str, float] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.end():min(end, match.end() + 240)]
        bound = "lower" if match.group("bound").lower() in {"下限", "lower"} else "upper"
        for label, key in (("静态|static", "static"), ("动态|dynamic", "dynamic")):
            found = re.search(
                rf"(?:{label})\s*(-?\d+(?:\.\d+)?)\s*V(?:\s*DC)?",
                block,
                re.I,
            )
            if found:
                values[f"{key}_{bound}"] = float(found.group(1))
    return values


def _range(text: str, labels: tuple[str, ...]) -> Optional[tuple[float, float]]:
    label = "|".join(re.escape(item) for item in labels)
    patterns = [
        rf"(?:{label})[^。\n]{{0,45}}?(-?\d+(?:\.\d+)?)\s*V?\s*(?:DC)?\s*(?:至|到|～|~|-|to)\s*(-?\d+(?:\.\d+)?)\s*V",
        rf"(?:{label})[^。\n]{{0,30}}?(?:下限|lower)[^\d]{{0,8}}(-?\d+(?:\.\d+)?)\s*V[^。\n]{{0,35}}?(?:上限|upper)[^\d]{{0,8}}(-?\d+(?:\.\d+)?)\s*V",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            return float(match.group(1)), float(match.group(2))
    lower = re.search(rf"(?:{label})?[^。\n]{{0,18}}?(?:下限|lower)[^\d]{{0,8}}(-?\d+(?:\.\d+)?)\s*V", text, re.I)
    upper = re.search(rf"(?:{label})?[^。\n]{{0,18}}?(?:上限|upper)[^\d]{{0,8}}(-?\d+(?:\.\d+)?)\s*V", text, re.I)
    return (float(lower.group(1)), float(upper.group(1))) if lower and upper else None


def extract_wiring_facts(text: str) -> List[str]:
    facts = []
    for sentence in _sentences(text):
        if is_wiring_heading_fragment(sentence) or _is_cross_reference(sentence):
            continue
        if not any(anchor.lower() in sentence.lower() for anchor in WIRING_ANCHORS):
            continue
        if not has_wiring_normative_predicate(sentence):
            continue
        facts.append(sentence)
    return facts[:5]


def has_wiring_normative_predicate(text: str) -> bool:
    value = str(text or "").strip()
    if re.search(r"必须|应当|不得|禁止|需要|确保|只能|请勿", value):
        return True
    if re.search(r"应(?=设置|采用|连接|使用|确保|检查|核对|符合|设计)", value):
        return True
    if re.search(r"需(?=设置|采用|连接|使用|确保|检查|核对|符合)", value):
        return True
    if re.search(r"连接(?!器|关系|说明|示意|图|元件)|使用(?!说明)|检查|核对|符合(?!性)|设计为", value):
        return True
    return bool(re.search(r"\b(?:must|shall|should|connect|use|ensure|verify|require|designed)\b", value, re.I))


def is_wiring_heading_fragment(text: str) -> bool:
    value = str(text or "").strip()
    normalized = re.sub(r"[：:。；;\s]+$", "", value)
    if normalized in WIRING_HEADING_FRAGMENTS:
        return True
    if re.match(r"^(?:下图显示|下图所示|在下文中介绍|以下介绍)", normalized):
        return True
    if value.endswith(("：", ":")):
        return True
    if len(normalized) <= 12 and not has_wiring_normative_predicate(normalized):
        return True
    return False


def wiring_fact_score(
    text: str,
    facts: Optional[List[str]] = None,
    *,
    system_level: bool = False,
    specific_module: bool = False,
    rh_scope: bool = False,
) -> int:
    extracted = facts if facts is not None else extract_wiring_facts(text)
    score = 3 if any(has_wiring_normative_predicate(item) for item in extracted) else 0
    specialized = ("保护导线", "保护性导线", "selv", "pelv", "极性", "隔离", "线径")
    if any(term in " ".join(extracted).lower() for term in specialized):
        score += 2
    if system_level:
        score += 1
    if is_wiring_heading_fragment(text):
        score -= 4
    if _is_cross_reference(text):
        score -= 3
    if specific_module:
        score -= 3
    if rh_scope:
        score -= 4
    return score


def _is_cross_reference(text: str) -> bool:
    value = str(text or "").strip()
    return bool(re.search(r"https?://|www\.|请参见|参见.+(?:章节|部分)|中的[“\"]?接线[”\"]?部分", value, re.I))


def extract_led_checks(text: str, interface_name: str = "X1") -> List[str]:
    value = str(text or "")
    labels = [
        label
        for label, pattern in (
            ("RUN/STOP LED", r"RUN/STOP\s+LED"),
            ("ERROR LED", r"ERROR\s+LED"),
            ("MAINT LED", r"MAINT\s+LED"),
        )
        if re.search(pattern, value, re.I)
    ]
    interface = interface_name.upper() if re.fullmatch(r"X\d+", str(interface_name or ""), re.I) else "X1"
    for port in ("P1", "P2"):
        full = (
            rf"(?:端口\s*)?{re.escape(interface)}\s*{port}R?\s*(?:的\s*)?"
            r"LINK\s*(?:RX\s*/\s*TX|TX\s*/\s*RX)\s*LED"
        )
        short = rf"(?<![A-Z0-9]){re.escape(interface)}\s*{port}R(?![A-Z0-9])"
        if re.search(full, value, re.I | re.S) or re.search(short, value, re.I):
            labels.append(f"{interface} {port} LINK RX/TX LED")
    return labels


def extract_topology_fact(text: str) -> str:
    value = str(text or "")
    hmi_x1 = bool(re.search(r"HMI[^。\n]{0,60}PROFINET\s*X1", value, re.I))
    cpu_x2 = bool(re.search(r"(?:R/H\s*)?CPU[^。\n]{0,60}PROFINET\s*X2", value, re.I))
    if hmi_x1 and cpu_x2:
        return "在该 S7-1500R/H 示例中，HMI 侧使用 PROFINET X1，CPU 侧使用 PROFINET X2。"
    return ""


def extract_emc_facts(text: str) -> List[str]:
    value = str(text or "")
    facts = []
    if re.search(r"(?:grounded|接地)[^。\n]{0,40}(?:control cabinets?|control boxes?|控制柜|控制箱)", value, re.I):
        facts.append("可采用接地控制柜或控制箱。")
    if re.search(r"(?:noise filters?|噪声滤波器)[^。\n]{0,50}(?:supply lines?|电源线)?", value, re.I):
        facts.append("可在电源线上使用噪声滤波器。")
    if re.search(r"industrial (?:environment|applications?)|工业环境", value, re.I):
        facts.append("该系统适用于工业环境。")
    if re.search(r"EN\s*55011[^。\n]{0,30}Class\s*B|住宅环境[^。\n]{0,50}Class\s*B", value, re.I):
        facts.append("用于住宅环境时应满足 EN 55011 Class B。")
    return facts


def _sentences_with_terms(text: str, terms: tuple[str, ...]) -> List[str]:
    sentences = _sentences(text)
    return [item for item in sentences if any(term in item.lower() for term in terms)][:5]


def _sentences(text: str) -> List[str]:
    return [item.strip() for item in re.split(r"[。；;\n]+", str(text or "")) if item.strip()]
