#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from benchmark.generation.common import FULL_360_DIR, GENERATOR_SEED, load_jsonl, write_json, write_jsonl


DEFAULT_FULL_PATH = FULL_360_DIR / "full_360.jsonl"
DEFAULT_DEV_PATH = FULL_360_DIR / "dev_120.jsonl"


def build_dev_120(cases: Sequence[Dict[str, Any]], random_seed: int = GENERATOR_SEED) -> List[Dict[str, Any]]:
    core = [case for case in cases if str(case.get("benchmark_layer") or "core") == "core"]
    generated = [case for case in cases if str(case.get("benchmark_layer") or "core") != "core"]
    if len(core) != 30:
        raise ValueError(f"Dev-120 requires all 30 Core cases, found {len(core)}")
    if len(generated) < 90:
        raise ValueError(f"Dev-120 requires at least 90 Natural/Stress cases, found {len(generated)}")

    rng = random.Random(random_seed)
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for case in generated:
        groups[str(case.get("category") or "")].append(case)
    if any(not category for category in groups):
        raise ValueError("Every generated case must have a category")
    for values in groups.values():
        values.sort(key=lambda item: str(item.get("case_id") or ""))
        rng.shuffle(values)

    selected: List[Dict[str, Any]] = []
    selected_ids = set()
    for category in sorted(groups):
        item = groups[category].pop()
        selected.append(item)
        selected_ids.add(item["case_id"])

    remaining = [case for values in groups.values() for case in values if case["case_id"] not in selected_ids]
    remaining.sort(key=lambda item: str(item.get("case_id") or ""))
    rng.shuffle(remaining)
    selected.extend(remaining[:90 - len(selected)])
    selected.sort(key=lambda item: str(item.get("case_id") or ""))
    result = list(core) + selected

    if len(result) != 120 or len({case["case_id"] for case in result}) != 120:
        raise ValueError("Deterministic Dev-120 sampling did not produce 120 unique cases")
    generated_difficulties = {str(case.get("difficulty") or "") for case in selected}
    if not {"easy", "medium", "hard"}.issubset(generated_difficulties):
        raise ValueError("Dev-120 must cover easy, medium, and hard cases")
    actions = {action for case in selected for action in case.get("expected_action") or []}
    if not {"ANSWER", "CLARIFY", "ABSTAIN", "REFUSE"}.issubset(actions):
        raise ValueError("Dev-120 must cover answer, clarification, abstention, and refusal")
    if not any(case.get("category") == "compound_multi_agent" for case in selected):
        raise ValueError("Dev-120 must include a compound multi-agent case")
    return result


def dev_report(cases: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "schema": "safeplc.full_360.dev_120_report.v1",
        "random_seed": GENERATOR_SEED,
        "case_count": len(cases),
        "layer_counts": dict(Counter(str(case.get("benchmark_layer") or "core") for case in cases)),
        "category_counts": dict(Counter(str(case.get("category") or "") for case in cases)),
        "difficulty_counts": dict(Counter(str(case.get("difficulty") or "core") for case in cases)),
        "action_counts": dict(Counter(action for case in cases for action in case.get("expected_action") or [])),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build the deterministic stratified FULL-360 Dev-120 subset.")
    parser.add_argument("--full", default=str(DEFAULT_FULL_PATH))
    parser.add_argument("--output", default=str(DEFAULT_DEV_PATH))
    parser.add_argument("--report", default="")
    args = parser.parse_args(argv)
    try:
        dev = build_dev_120(load_jsonl(Path(args.full)))
    except (FileNotFoundError, ValueError) as exc:
        print(f"Dev-120 generation blocked: {exc}", file=sys.stderr)
        return 2
    output = Path(args.output)
    write_jsonl(output, dev)
    report = dev_report(dev)
    if args.report:
        write_json(Path(args.report), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
