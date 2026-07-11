#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List

from ..agents.orchestrator import run_agent_system
from .agent_metrics import aggregate_metrics, evaluate_case


METHOD_CONFIG = {
    "single_agent": {
        "routing_strategy": "single_best",
        "max_agents": 1,
        "enable_dynamic_routing": False,
        "enable_query_decomposition": False,
        "enable_model_filter": False,
        "enable_figure_backend": False,
        "enable_judge": False,
        "enable_verifier": False,
        "enable_second_retrieval": False,
        "enable_evidence_reranker": False,
    },
    "static_router": {
        "routing_strategy": "static",
        "max_agents": 2,
        "enable_dynamic_routing": False,
        "enable_query_decomposition": False,
        "enable_model_filter": True,
        "enable_figure_backend": True,
        "enable_judge": False,
        "enable_verifier": False,
        "enable_second_retrieval": False,
        "enable_evidence_reranker": True,
    },
    "all_agents": {
        "routing_strategy": "all_agents",
        "max_agents": 8,
        "enable_dynamic_routing": False,
        "enable_query_decomposition": False,
        "enable_model_filter": True,
        "enable_figure_backend": True,
        "enable_judge": False,
        "enable_verifier": False,
        "enable_second_retrieval": False,
        "enable_evidence_reranker": True,
    },
    "dynamic_router": {
        "routing_strategy": "adaptive",
        "max_agents": 4,
        "enable_dynamic_routing": True,
        "enable_query_decomposition": True,
        "enable_model_filter": True,
        "enable_figure_backend": True,
        "enable_judge": False,
        "enable_verifier": False,
        "enable_second_retrieval": False,
        "enable_evidence_reranker": True,
    },
    "dynamic_router_judge": {
        "routing_strategy": "adaptive",
        "max_agents": 4,
        "enable_dynamic_routing": True,
        "enable_query_decomposition": True,
        "enable_model_filter": True,
        "enable_figure_backend": True,
        "enable_judge": True,
        "enable_verifier": False,
        "enable_second_retrieval": False,
        "enable_evidence_reranker": True,
    },
    "full": {
        "routing_strategy": "adaptive",
        "max_agents": 4,
        "enable_dynamic_routing": True,
        "enable_query_decomposition": True,
        "enable_model_filter": True,
        "enable_figure_backend": True,
        "enable_judge": True,
        "enable_verifier": True,
        "enable_second_retrieval": True,
        "enable_evidence_reranker": True,
    },
}


def iter_cases(cases_dir: Path, suite: str = "") -> Iterable[Dict[str, object]]:
    files = sorted(cases_dir.glob("*.jsonl"))
    for path in files:
        if suite and path.stem != suite:
            continue
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)


def run_benchmark(
    cases_dir: Path,
    suite: str = "",
    limit: int = 0,
    mode: str = "SAMPLE",
    method: str = "full",
) -> Dict[str, object]:
    config = METHOD_CONFIG.get(method, METHOD_CONFIG["full"])
    rows: List[Dict[str, float]] = []
    failures: List[Dict[str, object]] = []
    case_count = 0
    for case in iter_cases(cases_dir, suite=suite):
        if limit and case_count >= limit:
            break
        response = run_agent_system(
            str(case.get("query", "")),
            context=str(case.get("context", "")),
            mode=mode,
            routing_strategy=config["routing_strategy"],
            max_agents=int(config["max_agents"]),
            feature_switches={key: bool(value) for key, value in config.items() if key.startswith("enable_")},
        )
        response_dict = response.to_dict()
        metrics = evaluate_case(case, response_dict)
        rows.append(metrics)
        case_count += 1
        if metrics.get("end_to_end_success", 0.0) < 1.0:
            failures.append(
                {
                    "case_id": case.get("case_id"),
                    "suite": case.get("suite"),
                    "query": case.get("query"),
                    "selected_agents": response.agent_plan.selected_agents,
                    "verdict": response.judge_decision.verdict,
                    "metrics": metrics,
                }
            )
    return {
        "method": method,
        "mode": mode,
        "method_features": {
            key: value
            for key, value in config.items()
            if key.startswith("enable_")
        },
        "case_count": case_count,
        "metrics": aggregate_metrics(rows),
        "failures": failures[:20],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SafePLC agent benchmark.")
    parser.add_argument("--cases-dir", default="benchmark/cases")
    parser.add_argument("--suite", default="")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--mode", default="SAMPLE")
    parser.add_argument("--method", default="full", choices=sorted(METHOD_CONFIG))
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    result = run_benchmark(
        cases_dir=Path(args.cases_dir),
        suite=args.suite,
        limit=args.limit,
        mode=args.mode,
        method=args.method,
    )
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
