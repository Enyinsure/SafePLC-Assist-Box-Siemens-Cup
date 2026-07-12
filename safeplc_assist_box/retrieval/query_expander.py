#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from ..evidence.model_identity import extract_model_identity


LOCATION_TERMS = (
    "哪里", "在哪", "位置", "物理位置", "前面", "后面", "正面", "背面",
    "front", "where", "location", "layout",
)
NON_LOCATION_TERMS = (
    "多少个端口", "几个端口", "端口数量", "电压", "参数", "故障", "报警", "排查",
    "how many ports", "voltage", "parameter", "fault", "alarm",
)


@dataclass(frozen=True)
class QueryExpansionResult:
    original_query: str
    expanded_queries: List[str] = field(default_factory=list)
    intent: str = ""
    normalized_model: str = ""
    interface_names: List[str] = field(default_factory=list)
    expansion_reasons: List[str] = field(default_factory=list)

    @property
    def all_queries(self) -> List[str]:
        return [self.original_query, *self.expanded_queries]


class QueryExpander:
    """Generate bounded, rule-based retrieval queries without answer leakage."""

    def expand(self, query: str, max_expanded_queries: int = 2) -> QueryExpansionResult:
        original = str(query or "").strip()
        low = original.lower()
        identity = extract_model_identity(original)
        interfaces = list(dict.fromkeys(item.upper() for item in re.findall(r"\bX\d+\b", original, re.I)))
        if max_expanded_queries > 0 and any(term in low for term in ("emc", "电磁兼容", "接地", "屏蔽", "干扰", "抗干扰")):
            expanded = [
                "electromagnetic compatibility industrial applications residential areas EN 55011 Class B",
                "S7-1500 system cabling grounded control cabinets control boxes noise filters supply lines EMC",
            ][: min(2, max_expanded_queries)]
            return QueryExpansionResult(
                original_query=original,
                expanded_queries=expanded,
                intent="emc",
                normalized_model=identity.normalized_model,
                interface_names=interfaces,
                expansion_reasons=["emc_english_manual_terms"] * len(expanded),
            )
        if max_expanded_queries > 0 and any(term in low for term in ("端子接线", "接线注意", "wiring rules", "terminal wiring")):
            expanded = [
                "S7-1500 ET 200MP 系统手册 接线 操作规则和规定 保护导线 SELV PELV",
                "S7-1500 system wiring rules protective conductor SELV PELV power supply connector",
            ][: min(2, max_expanded_queries)]
            return QueryExpansionResult(
                original_query=original,
                expanded_queries=expanded,
                intent="wiring",
                normalized_model=identity.normalized_model,
                interface_names=interfaces,
                expansion_reasons=["system_level_wiring_rules"] * len(expanded),
            )
        location = any(term in low for term in LOCATION_TERMS) and not any(
            term in low for term in NON_LOCATION_TERMS
        )
        if not location or not identity.normalized_model or not interfaces or max_expanded_queries <= 0:
            return QueryExpansionResult(
                original_query=original,
                intent="location" if location else "",
                normalized_model=identity.normalized_model,
                interface_names=interfaces,
            )

        interface = interfaces[0]
        interface_type = self._interface_type(interface, low)
        descriptor = f"{interface_type} 接口 {interface}" if interface_type else f"接口 {interface}"
        expanded = f"{identity.normalized_model} 不带前面板的模块前视图 {descriptor}"
        return QueryExpansionResult(
            original_query=original,
            expanded_queries=[expanded][: min(2, max_expanded_queries)],
            intent="location",
            normalized_model=identity.normalized_model,
            interface_names=interfaces,
            expansion_reasons=["explicit_location_intent_with_interface"],
        )

    def _interface_type(self, interface: str, query: str) -> str:
        if "profibus" in query:
            return "PROFIBUS"
        if "profinet" in query:
            return "PROFINET IO"
        if interface in {"X1", "X2"}:
            return "PROFINET IO"
        return ""


def is_explicit_image_request(query: str) -> bool:
    low = str(query or "").lower()
    return any(term in low for term in ("给我看图", "显示前视图", "输出图片", "显示图片", "show image", "show the figure"))
