"""Read repository benchmark reports and curated regression cases."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .paths import BENCHMARK_ROOT, REPORT_ROOT


REPORT_FILES = {
    "benchmark": REPORT_ROOT / "agent_benchmark_sample.json",
    "ablation": REPORT_ROOT / "agent_ablation_sample.json",
    "figure_coverage": REPORT_ROOT / "figure_coverage_report.json",
    "model_filter": REPORT_ROOT / "model_filter_audit.json",
    "retrieval": REPORT_ROOT / "retrieval_backend_audit.json",
}


def load_json(path: Path) -> Tuple[Dict[str, Any], str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, f"文件不存在：{path.name}"
    except (OSError, json.JSONDecodeError) as exc:
        return {}, f"无法读取 {path.name}：{type(exc).__name__}"
    if not isinstance(payload, dict):
        return {}, f"{path.name} 的顶层结构不是 JSON 对象"
    return payload, ""


def load_report_bundle() -> Dict[str, Any]:
    """Return only report values that really exist in the repository."""
    reports: Dict[str, Any] = {}
    errors: List[str] = []
    for name, path in REPORT_FILES.items():
        value, error = load_json(path)
        if value:
            reports[name] = value
        if error:
            errors.append(error)
    reports["errors"] = errors
    return reports


def load_showcase_cases(limit: int = 6) -> List[Dict[str, Any]]:
    """Load distinct real SAMPLE regression cases for one-click reproduction."""
    case_root = BENCHMARK_ROOT / "sample_regression"
    preferred = [
        "parameter",
        "wiring",
        "troubleshooting",
        "model_mismatch",
        "multi_agent_tasks",
        "operation_boundary",
        "slot_clarification",
        "topology",
    ]
    records: List[Dict[str, Any]] = []
    for suite in preferred:
        path = case_root / f"{suite}.jsonl"
        if not path.exists():
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(item, dict) or not item.get("query"):
                continue
            records.append(
                {
                    "id": str(item.get("case_id") or f"{suite}_{len(records) + 1}"),
                    "title": _case_title(suite),
                    "category": suite,
                    "query": str(item.get("query")),
                    "context": str(item.get("context") or ""),
                    "expected_action": str(item.get("expected_action") or ""),
                    "source": str(item.get("source") or ""),
                }
            )
            break
        if len(records) >= limit:
            break
    return records[:limit]


def load_supported_device_catalog() -> Dict[str, List[str]]:
    """Build selectors from model scopes already present in regression data."""
    catalog: Dict[str, List[str]] = {}
    case_root = BENCHMARK_ROOT / "sample_regression"
    for path in sorted(case_root.glob("*.jsonl")):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            scope = str(item.get("expected_model_scope") or "").strip()
            if not scope or scope.lower().endswith("general") or scope in {"S7-1500 / ET 200MP"}:
                continue
            if not any(token in scope.upper() for token in ("CPU ", "PS ", "PM ", "ET ", "SM ", "TM ")):
                continue
            family = _family_for_model(scope)
            catalog.setdefault(family, [])
            if scope not in catalog[family]:
                catalog[family].append(scope)
    return {family: sorted(models) for family, models in sorted(catalog.items())}


def _family_for_model(model: str) -> str:
    upper = model.upper()
    if "R/H" in upper or "1517H" in upper or "1518H" in upper:
        return "S7-1500R/H"
    if "ET 200" in upper:
        return "ET 200"
    if any(token in upper for token in ("CPU 15", "PS ", "PM ", "SM ", "TM ")):
        return "S7-1500"
    return "其他已收录设备"


def _case_title(suite: str) -> str:
    return {
        "parameter": "参数与单位查证",
        "wiring": "端子接线要求",
        "troubleshooting": "通信故障诊断",
        "model_mismatch": "跨型号污染拦截",
        "multi_agent_tasks": "图示与拓扑联合查证",
        "operation_boundary": "危险操作边界",
        "slot_clarification": "缺少型号主动澄清",
        "topology": "拓扑缺槽位澄清",
    }.get(suite, suite)
