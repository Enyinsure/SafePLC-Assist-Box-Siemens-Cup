#!/usr/bin/env python3
"""Load all 15 hidden snapshots through the frontend adapter and report results."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from safeplc_assist_box.frontend.hidden_demo_matcher import (  # noqa: E402
    load_hidden_demo_registry,
)
from safeplc_assist_box.frontend.pipeline_adapter import (  # noqa: E402
    PipelineRequest,
    execute_pipeline,
)
from safeplc_assist_box.frontend.runtime import FrontendSettings  # noqa: E402


REPORT_JSON = PROJECT_ROOT / "reports" / "hidden_demo_15_smoke.json"
REPORT_CSV = PROJECT_ROOT / "reports" / "hidden_demo_15_smoke.csv"


def main() -> int:
    settings = FrontendSettings(
        frontend_mode="demo",
        demo_enabled=True,
        pipeline_mode="SAMPLE",
        hidden_demo_enabled=True,
        hidden_demo_debug=False,
    )
    rows: List[Dict[str, Any]] = []
    for case in load_hidden_demo_registry():
        outcome = execute_pipeline(PipelineRequest(query=str(case["query"])), settings)
        normalized = outcome.normalized or {}
        runtime = normalized.get("runtime") or {}
        judge = normalized.get("judge_result") or {}
        evidences = normalized.get("evidence_pool") or []
        visual_count = sum(
            bool(item.get("image_path")) and item.get("visual_status") == "image_available"
            for item in evidences
        )
        agents = [str(item.get("name") or "") for item in normalized.get("selected_agents") or []]
        row = {
            "case_id": case["id"],
            "ok": bool(outcome.ok),
            "source": outcome.source,
            "pipeline_mode": runtime.get("pipeline_mode"),
            "action": runtime.get("action"),
            "verdict": judge.get("verdict"),
            "agents": " | ".join(agents),
            "evidence_count": len(evidences),
            "visual_evidence_count": visual_count,
            "model_consistency": (judge.get("checks") or {}).get("model_consistency", {}).get("status"),
            "error": outcome.user_error or outcome.debug_error,
        }
        expected_verdict = {
            "ANSWER": "PASS",
            "PARTIAL": "PARTIAL",
            "REFUSE": "REFUSE",
        }.get(str(case["expected_action"]), str(case["expected_action"]))
        row["passed"] = bool(
            row["ok"]
            and row["source"] == "offline_demo_snapshot"
            and row["pipeline_mode"] == "SAMPLE"
            and row["evidence_count"] >= 3
            and row["visual_evidence_count"] == row["evidence_count"]
            and row["verdict"] == expected_verdict
        )
        rows.append(row)

    passed = sum(bool(row["passed"]) for row in rows)
    report = {
        "schema_version": "hidden-demo-smoke-v1",
        "source": "offline_demo_snapshot",
        "pipeline_mode": "SAMPLE",
        "summary": {"passed": passed, "total": len(rows)},
        "cases": rows,
    }
    REPORT_JSON.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    with REPORT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Hidden demo smoke: {passed}/{len(rows)}")
    print(f"JSON: {REPORT_JSON.relative_to(PROJECT_ROOT).as_posix()}")
    print(f"CSV: {REPORT_CSV.relative_to(PROJECT_ROOT).as_posix()}")
    return 0 if passed == len(rows) == 15 else 2


if __name__ == "__main__":
    raise SystemExit(main())
