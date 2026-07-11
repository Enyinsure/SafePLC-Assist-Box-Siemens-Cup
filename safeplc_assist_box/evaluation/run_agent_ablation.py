#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .run_agent_benchmark import METHOD_CONFIG, run_benchmark


REPORT_FIELDS = [
    "routing_accuracy",
    "agent_selection_precision",
    "agent_selection_recall",
    "evidence_coverage",
    "coverage",
    "grounded_claim_rate",
    "model_consistency_rate",
    "cross_family_contamination_rate",
    "figure_evidence_success_rate",
    "clarification_accuracy",
    "refusal_accuracy",
    "judge_precision",
    "verifier_pass_rate",
    "average_agent_calls",
    "average_tool_calls",
    "p50_latency_ms",
    "p95_latency_ms",
    "answer_length",
    "raw_ocr_dump_rate",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SafePLC agent ablation.")
    parser.add_argument("--cases-dir", default="benchmark/cases")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--mode", default="SAMPLE")
    parser.add_argument("--output", default="reports/agent_ablation_sample.json")
    args = parser.parse_args()

    rows = []
    for method, config in METHOD_CONFIG.items():
        result = run_benchmark(
            cases_dir=Path(args.cases_dir),
            limit=args.limit,
            mode=args.mode,
            method=method,
        )
        m = result.get("metrics", {})
        rows.append(
            {
                "method": method,
                "feature_switches": {k: v for k, v in config.items() if k.startswith("enable_")},
                "routing_strategy": config["routing_strategy"],
                "max_agents": config["max_agents"],
                "metrics": {field: m.get(field, 0.0) for field in REPORT_FIELDS},
            }
        )
    output = {
        "mode": args.mode,
        "limit": args.limit,
        "methods": rows,
        "notes": [
            "Each method uses a distinct feature switch profile and routing/max-agent configuration.",
            "SAMPLE results are regression checks and must not be presented as FULL industrial accuracy.",
            "FULL runs require real Chroma assets and should be generated on the server.",
        ],
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
