#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


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
    terms = ("端子", "接线", "电源隔离", "保护导线", "保护性导线", "selv", "pelv", "极性", "线径", "terminal", "wiring", "protective conductor", "rated voltage")
    return _sentences_with_terms(text, terms)


def extract_led_checks(text: str) -> List[str]:
    value = str(text or "")
    labels = []
    patterns = [
        r"RUN/STOP\s+LED", r"ERROR\s+LED", r"MAINT\s+LED",
        r"X1\s*P1\s+LINK\s+RX/TX\s+LED", r"X1\s*P2\s+LINK\s+RX/TX\s+LED",
    ]
    for pattern in patterns:
        match = re.search(pattern, value, re.I)
        if match:
            labels.append(re.sub(r"\s+", " ", match.group(0)).upper().replace(" LED", " LED"))
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
    if re.search(r"industrial environment|工业环境", value, re.I):
        facts.append("该系统适用于工业环境。")
    if re.search(r"EN\s*55011[^。\n]{0,30}Class\s*B|住宅环境[^。\n]{0,50}Class\s*B", value, re.I):
        facts.append("用于住宅环境时应满足 EN 55011 Class B。")
    return facts


def _sentences_with_terms(text: str, terms: tuple[str, ...]) -> List[str]:
    sentences = [item.strip() for item in re.split(r"[。；;\n]+", str(text or "")) if item.strip()]
    return [item for item in sentences if any(term in item.lower() for term in terms)][:5]
