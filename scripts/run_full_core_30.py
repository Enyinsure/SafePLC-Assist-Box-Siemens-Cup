#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from benchmark.full_core_30.acceptance_rules import CASES_PATH, evaluate_case, load_cases, validate_case_definition
from safeplc_assist_box.agents.orchestrator import run_agent_system
from safeplc_assist_box.config import SafePLCConfig
from safeplc_assist_box.tools.chroma_figure_retriever import ChromaFigureRetriever
from safeplc_assist_box.tools.chroma_text_retriever import ChromaTextRetriever
from safeplc_assist_box.tools.embedding_adapter import EmbeddingAdapter


DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "reports" / "runtime" / "full_core_30"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def git_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, text=True,
        capture_output=True, check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "UNKNOWN"


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_log(path: Path, message: str) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"[{now_iso()}] {message}\n")


def environment_record(config: SafePLCConfig, started_at: str) -> Dict[str, Any]:
    return {
        "schema": "safeplc.full_core_30.environment.v1",
        "git_sha": git_sha(),
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "mode": config.mode,
        "retrieval_source": "real_chroma",
        "chroma_path": config.chroma_dir,
        "configured_text_collection": config.text_collection or "<auto-discover>",
        "selected_text_collection": "",
        "figure_chroma_path": config.figure_chroma_dir,
        "configured_figure_collection": config.figure_collection or "<auto-discover>",
        "selected_figure_collection": "",
        "embedding_model": config.embedding_model_path or config.embedding_backend,
        "embedding_backend": config.embedding_backend,
        "query_expansion_enabled": config.enable_query_expansion,
        "max_expanded_queries": config.max_expanded_queries,
        "jsonl_fallback_enabled": config.allow_jsonl_fallback,
        "jsonl_hybrid_enabled": config.enable_jsonl_hybrid,
        "started_at": started_at,
        "finished_at": "",
        "status": "STARTED",
    }


def validate_full_environment(config: SafePLCConfig) -> List[str]:
    errors = []
    if config.mode != "FULL":
        errors.append("mode_must_be_FULL")
    if config.allow_jsonl_fallback or config.enable_jsonl_hybrid:
        errors.append("JSONL_fallback_and_hybrid_must_be_disabled")
    if not config.chroma_dir or not Path(config.chroma_dir).is_dir():
        errors.append("real_text_Chroma_directory_is_required")
    if not config.figure_chroma_dir or not Path(config.figure_chroma_dir).is_dir():
        errors.append("real_figure_Chroma_directory_is_required")
    if not config.enable_query_expansion:
        errors.append("query_expansion_must_be_enabled")
    if config.max_expanded_queries < 2:
        errors.append("max_expanded_queries_must_be_at_least_2")
    backend = str(config.embedding_backend or "").lower()
    if backend not in EmbeddingAdapter.VALID_BACKENDS:
        errors.append("embedding_backend_is_not_supported")
    model_available = bool(
        config.embedding_model_path
        and (Path(config.embedding_model_path).exists() or config.allow_remote_model_download)
    )
    default_available = bool(
        config.allow_chroma_default_embedding and backend in {"auto", "chroma_default"}
    )
    if not model_available and not default_available:
        errors.append("embedding_model_path_or_backend_is_not_available")
    return errors


def resolve_selected_collections(config: SafePLCConfig) -> Dict[str, Any]:
    text_embedding = EmbeddingAdapter.from_config(config)
    figure_embedding = EmbeddingAdapter.from_config(config)
    text = ChromaTextRetriever(
        config.chroma_dir,
        config.text_collection,
        embedding_adapter=text_embedding,
    )
    figure = ChromaFigureRetriever(
        config.figure_chroma_dir,
        config.figure_collection,
        config.figure_cards_jsonl,
        config.visual_dir,
        embedding_adapter=figure_embedding,
    )
    text_collection = text._collection()
    figure_collection = figure._collection()
    text_embedding.query_arguments(text_collection, "SafePLC FULL Core 30 environment validation")
    figure_embedding.query_arguments(figure_collection, "SafePLC FULL Core 30 figure environment validation")
    return {
        "selected_text_collection": text.collection_name,
        "selected_figure_collection": figure.collection_name,
        "text_embedding_audit": dict(text_embedding.last_audit),
        "figure_embedding_audit": dict(figure_embedding.last_audit),
    }


def truthfulness_errors(response: Dict[str, Any]) -> List[str]:
    errors = []
    if response.get("mode") != "FULL":
        errors.append("response_mode_is_not_FULL")
    audit = response.get("metrics", {}).get("retrieval_backend_audit", {})
    if isinstance(audit, dict):
        if audit.get("sample_fixture_active"):
            errors.append("SAMPLE_fixture_was_used")
        if audit.get("jsonl_fallback_active") or audit.get("jsonl_fallback_triggered"):
            errors.append("JSONL_fallback_was_used")
        calls = audit.get("tool_calls") or []
        used = {
            backend
            for call in calls if isinstance(call, dict)
            for backend in call.get("backend_used") or []
        }
        if any("jsonl" in str(item).lower() or "sample" in str(item).lower() for item in used):
            errors.append("non_Chroma_retrieval_backend_was_used")
    for evidence in response.get("evidence_pool", {}).get("evidences", []) or []:
        backend = str(evidence.get("retrieval_backend") or "").lower() if isinstance(evidence, dict) else ""
        if "jsonl" in backend or "sample" in backend:
            errors.append("non_FULL_evidence_detected")
            break
    return list(dict.fromkeys(errors))


def select_cases(cases: List[Dict[str, Any]], case_ids: List[str], limit: int) -> List[Dict[str, Any]]:
    selected = [case for case in cases if not case_ids or case["case_id"] in set(case_ids)]
    if case_ids:
        missing = set(case_ids) - {case["case_id"] for case in selected}
        if missing:
            raise ValueError("Unknown case ids: " + ", ".join(sorted(missing)))
    return selected[:limit] if limit else selected


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the SafePLC 30-case core benchmark against real FULL Chroma.")
    parser.add_argument("--cases", default=str(CASES_PATH))
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    os.environ["SAFEPLC_MODE"] = "FULL"
    os.environ["SAFEPLC_ALLOW_JSONL_FALLBACK"] = "0"
    os.environ["SAFEPLC_ENABLE_JSONL_HYBRID"] = "0"
    config = SafePLCConfig.from_env(mode="FULL")
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    run_log = output_dir / "run.log"
    acceptance_log = output_dir / "acceptance.log"
    run_log.write_text("", encoding="utf-8")
    acceptance_log.write_text("", encoding="utf-8")

    started_at = now_iso()
    environment = environment_record(config, started_at)
    write_json(output_dir / "environment.json", environment)
    append_log(run_log, f"START git={environment['git_sha']} mode=FULL cases={args.cases}")

    environment_errors = validate_full_environment(config)
    if environment_errors:
        environment.update({"finished_at": now_iso(), "status": "ERROR", "errors": environment_errors})
        write_json(output_dir / "environment.json", environment)
        append_log(run_log, "ENVIRONMENT ERROR " + ";".join(environment_errors))
        raise SystemExit(2)
    try:
        environment.update(resolve_selected_collections(config))
        write_json(output_dir / "environment.json", environment)
        append_log(
            run_log,
            "COLLECTIONS "
            f"text={environment['selected_text_collection']} figure={environment['selected_figure_collection']}",
        )
    except Exception as exc:
        error = f"collection_resolution_failed:{type(exc).__name__}:{exc}"
        environment.update({"finished_at": now_iso(), "status": "ERROR", "errors": [error]})
        write_json(output_dir / "environment.json", environment)
        append_log(run_log, "ENVIRONMENT ERROR " + error)
        raise SystemExit(2)

    cases = load_cases(Path(args.cases))
    definition_errors = {
        case.get("case_id", f"ordinal_{case.get('ordinal')}"): validate_case_definition(case)
        for case in cases
        if validate_case_definition(case)
    }
    if definition_errors:
        environment.update({"finished_at": now_iso(), "status": "ERROR", "case_definition_errors": definition_errors})
        write_json(output_dir / "environment.json", environment)
        append_log(run_log, "CASE DEFINITION ERROR " + json.dumps(definition_errors, ensure_ascii=False))
        raise SystemExit(2)

    selected = select_cases(cases, args.case_id, max(0, args.limit))
    rows = []
    observed_text_collections = set()
    observed_figure_collections = set()
    for case in selected:
        case_id = case["case_id"]
        append_log(run_log, f"CASE START {case_id}")
        try:
            response = run_agent_system(
                case["query"], context=case.get("context", ""), mode="FULL",
                routing_strategy="adaptive", max_agents=4,
            ).to_dict()
            for evidence in response.get("evidence_pool", {}).get("evidences", []) or []:
                if not isinstance(evidence, dict) or not evidence.get("collection_name"):
                    continue
                backend = str(evidence.get("retrieval_backend") or "")
                target = observed_figure_collections if "figure" in backend else observed_text_collections
                target.add(str(evidence["collection_name"]))
            authenticity = truthfulness_errors(response)
            acceptance = evaluate_case(case, response)
            if authenticity:
                acceptance["passed"] = False
                acceptance["status"] = "ERROR"
                acceptance["authenticity_errors"] = authenticity
            status = acceptance["status"]
            payload = {"case": case, "response": response, "acceptance": acceptance}
            write_json(output_dir / f"{case_id}.json", payload)
            append_log(acceptance_log, f"{case_id}\t{status}\t{json.dumps(acceptance.get('failures', []), ensure_ascii=False)}")
            rows.append({
                "ordinal": case["ordinal"], "case_id": case_id, "category": case["category"],
                "status": status, "action": response.get("action", ""), "verdict": response.get("verdict", ""),
                "latency_ms": response.get("total_latency_ms", 0),
            })
            append_log(run_log, f"CASE END {case_id} status={status}")
        except Exception as exc:
            error = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
            write_json(output_dir / f"{case_id}.json", {"case": case, "error": error, "status": "ERROR"})
            append_log(acceptance_log, f"{case_id}\tERROR\t{type(exc).__name__}: {exc}")
            append_log(run_log, f"CASE ERROR {case_id} {type(exc).__name__}: {exc}")
            rows.append({"ordinal": case["ordinal"], "case_id": case_id, "category": case["category"], "status": "ERROR", "action": "", "verdict": "", "latency_ms": 0})

    counts = {status: sum(row["status"] == status for row in rows) for status in ("PASS", "FAIL", "ERROR")}
    summary = {
        "schema": "safeplc.full_core_30.summary.v1",
        "git_sha": environment["git_sha"],
        "mode": "FULL",
        "case_count": len(rows),
        "counts": counts,
        "started_at": started_at,
        "finished_at": now_iso(),
        "cases": rows,
    }
    write_json(output_dir / "summary.json", summary)
    with (output_dir / "summary.tsv").open("w", encoding="utf-8", newline="") as handle:
        handle.write("ordinal\tcase_id\tcategory\tstatus\taction\tverdict\tlatency_ms\n")
        for row in rows:
            handle.write("\t".join(str(row[key]) for key in ("ordinal", "case_id", "category", "status", "action", "verdict", "latency_ms")) + "\n")

    environment.update({
        "finished_at": summary["finished_at"], "status": "COMPLETE", "case_count": len(rows), "counts": counts,
        "observed_text_collections": sorted(observed_text_collections),
        "observed_figure_collections": sorted(observed_figure_collections),
    })
    write_json(output_dir / "environment.json", environment)
    append_log(run_log, f"END PASS={counts['PASS']} FAIL={counts['FAIL']} ERROR={counts['ERROR']}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    raise SystemExit(0 if counts["FAIL"] == 0 and counts["ERROR"] == 0 else 1)


if __name__ == "__main__":
    main()
