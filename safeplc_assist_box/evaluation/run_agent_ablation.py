#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .run_agent_benchmark import METHOD_CONFIG, run_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SafePLC agent ablation.")
    parser.add_argument("--cases-dir", default="benchmark/cases")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--mode", default="SAMPLE")
    parser.add_argument("--output", default="reports/agent_ablation_sample.json")
    args = parser.parse_args()

    rows = []
    for method in METHOD_CONFIG:
        result = run_benchmark(
            cases_dir=Path(args.cases_dir),
            limit=args.limit,
            mode=args.mode,
            method=method,
        )
        m = result.get("metrics", {})
        rows.append(
            {
                "Method": method,
                "Routing F1": m.get("selection_f1", 0.0),
                "Multi-Agent Acc": m.get("end_to_end_success", 0.0),
                "Evidence Coverage": m.get("evidence_coverage", 0.0),
                "Unsupported Rate": m.get("unsupported_claim_rate", 0.0),
                "Avg Agents": m.get("agent_calls", 0.0),
                "P95": m.get("p95_latency_ms", 0.0),
            }
        )
    output = {
        "mode": args.mode,
        "limit": args.limit,
        "rows": rows,
        "notes": [
            "dynamic_router uses Supervisor adaptive routing.",
            "dynamic_router_judge and full use the same orchestrator path; full additionally reports verifier and clarification state.",
            "Results are measured from the provided local benchmark cases and are not hand-edited.",
        ],
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

