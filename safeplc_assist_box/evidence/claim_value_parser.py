#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .model_identity import extract_model_identity


UNIT_PATTERN = r"Mbit/s|kHz|MHz|mV|mA|kW|Hz|ms|[µμ]s|°C|mm|V|A|W|m|%"


@dataclass(frozen=True)
class ParameterValue:
    value: float
    unit: str
    raw: str
    condition: str = ""


@dataclass
class ParsedClaimValues:
    parameter_values: List[ParameterValue] = field(default_factory=list)
    ranges: List[Tuple[ParameterValue, ParameterValue]] = field(default_factory=list)
    models: List[str] = field(default_factory=list)
    order_numbers: List[str] = field(default_factory=list)
    page_numbers: List[int] = field(default_factory=list)
    figure_numbers: List[str] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)
    port_labels: List[str] = field(default_factory=list)


def parse_claim_values(text: str) -> ParsedClaimValues:
    source = text or ""
    identity = extract_model_identity(source)
    result = ParsedClaimValues(
        models=list(identity.normalized_models),
        order_numbers=list(identity.order_numbers),
        page_numbers=_unique_ints(
            int(value)
            for value in re.findall(r"(?:page|页(?:码)?|资料页)\s*[:：]?\s*(\d+)", source, re.I)
        ),
        figure_numbers=list(
            dict.fromkeys(
                match.strip()
                for match in re.findall(r"(?:Figure|Fig\.|图)\s*[\d]+(?:[-.]\d+)*", source, re.I)
            )
        ),
        interfaces=list(dict.fromkeys(re.findall(r"\bX[1-9]\b", source.upper()))),
        port_labels=list(dict.fromkeys(label.replace(" ", " ") for label in re.findall(r"\bX[1-9]\s*P[1-9]\b", source.upper()))),
    )
    excluded_spans = _excluded_spans(source)
    quantities: List[Tuple[ParameterValue, Tuple[int, int]]] = []
    for match in re.finditer(rf"(?<![A-Z0-9-])(-?\d+(?:\.\d+)?)\s*({UNIT_PATTERN})(?![A-Za-z])", source, re.I):
        if _inside(match.span(), excluded_spans):
            continue
        raw_unit = match.group(2)
        value = ParameterValue(
            value=float(match.group(1)),
            unit=_normalize_unit(raw_unit),
            raw=match.group(0),
            condition=_nearby_condition(source, match.start()),
        )
        quantities.append((value, match.span()))
    result.parameter_values = [item[0] for item in quantities]
    for index in range(len(quantities) - 1):
        left, left_span = quantities[index]
        right, right_span = quantities[index + 1]
        between = source[left_span[1] : right_span[0]].lower()
        if re.search(r"\b(?:to|through)\b|[-~～至到]", between) and left.unit == right.unit:
            result.ranges.append((left, right))
    return result


def same_parameter_value(left: ParameterValue, right: ParameterValue, tolerance: float = 1e-9) -> bool:
    return left.unit == right.unit and abs(left.value - right.value) <= tolerance


def find_numeric_mismatches(claim: ParsedClaimValues, evidence: ParsedClaimValues) -> List[ParameterValue]:
    return [
        value
        for value in claim.parameter_values
        if not any(abs(value.value - candidate.value) <= 1e-9 for candidate in evidence.parameter_values)
    ]


def find_unit_mismatches(claim: ParsedClaimValues, evidence: ParsedClaimValues) -> List[ParameterValue]:
    mismatches = []
    for value in claim.parameter_values:
        same_number = [candidate for candidate in evidence.parameter_values if abs(value.value - candidate.value) <= 1e-9]
        if same_number and not any(candidate.unit == value.unit for candidate in same_number):
            mismatches.append(value)
    return mismatches


def _excluded_spans(text: str) -> List[Tuple[int, int]]:
    patterns = [
        r"6ES7[A-Z0-9-]{5,}",
        r"(?:CPU\s*)?15(?:11|13|15|16|17|18)(?:-\d)?\s*(?:PN/DP|PN|DP|HF|H)?",
        r"(?:page|页(?:码)?|资料页)\s*[:：]?\s*\d+",
        r"(?:Figure|Fig\.|图)\s*[\d]+(?:[-.]\d+)*",
        r"\bX[1-9]\s*P[1-9]\b",
        r"\bX[1-9]\b",
    ]
    return [match.span() for pattern in patterns for match in re.finditer(pattern, text, re.I)]


def _inside(span: Tuple[int, int], excluded: List[Tuple[int, int]]) -> bool:
    return any(span[0] >= item[0] and span[1] <= item[1] for item in excluded)


def _normalize_unit(unit: str) -> str:
    canonical = {
        "v": "V",
        "mv": "mV",
        "a": "A",
        "ma": "mA",
        "w": "W",
        "kw": "kW",
        "hz": "Hz",
        "khz": "kHz",
        "mhz": "MHz",
        "mbit/s": "Mbit/s",
        "ms": "ms",
        "µs": "µs",
        "μs": "µs",
        "°c": "°C",
        "mm": "mm",
        "m": "m",
        "%": "%",
    }
    return canonical[unit.lower()]


def _nearby_condition(text: str, start: int) -> str:
    prefix = text[max(0, start - 50) : start].lower()
    for condition in ("static", "dynamic", "静态", "动态", "rated", "额定"):
        if condition in prefix:
            return condition
    return ""


def _unique_ints(values) -> List[int]:
    return list(dict.fromkeys(values))
