"""Load curated frontend cases and immutable offline response snapshots."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .paths import DATA_ROOT, resolve_project_path


DEMO_MANIFEST = DATA_ROOT / "demo_cases.json"


def load_demo_cases(path: Path = DEMO_MANIFEST) -> List[Dict[str, Any]]:
    """Return validated demo descriptors; malformed records are ignored."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(payload, list):
        return []
    cases: List[Dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict) or not str(item.get("query") or "").strip():
            continue
        record = dict(item)
        record.setdefault("id", f"case_{len(cases) + 1}")
        record.setdefault("title", record["id"])
        record.setdefault("category", "查证案例")
        record.setdefault("context", "")
        record.setdefault("snapshot", "")
        cases.append(record)
    return cases


def get_demo_case(case_id: str, path: Path = DEMO_MANIFEST) -> Dict[str, Any] | None:
    return next((case for case in load_demo_cases(path) if case.get("id") == case_id), None)


def load_demo_snapshot(case: Dict[str, Any]) -> Dict[str, Any]:
    """Read the raw pipeline snapshot declared by a selected demo case."""
    snapshot = resolve_project_path(str(case.get("snapshot") or ""))
    if not snapshot:
        raise FileNotFoundError("该典型案例没有可用的离线响应快照。")
    try:
        payload = json.loads(snapshot.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"离线快照不存在：{snapshot}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"离线快照 JSON 无法解析：{snapshot.name}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"离线快照必须是对象：{snapshot.name}")
    return payload
