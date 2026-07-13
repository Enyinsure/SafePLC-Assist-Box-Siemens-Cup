#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import traceback
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from benchmark.full_360.acceptance_rules import evaluate_case
from benchmark.generation.common import (
    CORE_CASES_PATH,
    FULL_360_DIR,
    SCHEMA_VERSION,
    load_jsonl,
    sha256_file,
    stable_hash,
    write_json,
)
from safeplc_assist_box.agents.orchestrator import run_agent_system
from safeplc_assist_box.config import SafePLCConfig
from scripts.run_full_core_30 import resolve_selected_collections, truthfulness_errors, validate_full_environment


SUBSET_PATHS = {
    "core30": CORE_CASES_PATH,
    "dev120": FULL_360_DIR / "dev_120.jsonl",
    "full360": FULL_360_DIR / "full_360.jsonl",
}
DEFAULT_OUTPUT_DIRS = {
    "core30": PROJECT_ROOT / "reports" / "runtime" / "full360_core30",
    "dev120": PROJECT_ROOT / "reports" / "runtime" / "full360_dev120",
    "full360": PROJECT_ROOT / "reports" / "runtime" / "full360_all",
}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def git_value(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=PROJECT_ROOT, text=True, capture_output=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else "UNKNOWN"


def dirty_worktree() -> bool:
    return bool(git_value("status", "--porcelain"))


def append_log(path: Path, message: str) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"[{now_iso()}] {message}\n")


def select_cases(
    cases: Sequence[Dict[str, Any]],
    *,
    case_ids: Sequence[str] = (),
    categories: Sequence[str] = (),
    start_index: int = 0,
    max_cases: int = 0,
) -> List[Dict[str, Any]]:
    wanted_ids = set(case_ids)
    wanted_categories = set(categories)
    selected = [
        case for case in cases
        if (not wanted_ids or str(case.get("case_id") or "") in wanted_ids)
        and (not wanted_categories or str(case.get("category") or "") in wanted_categories)
    ]
    if wanted_ids:
        missing = wanted_ids - {str(case.get("case_id") or "") for case in selected}
        if missing:
            raise ValueError("Unknown case ids: " + ", ".join(sorted(missing)))
    selected = selected[max(0, start_index):]
    return selected[:max_cases] if max_cases > 0 else selected


def case_input_hash(case: Dict[str, Any], dataset_sha256: str) -> str:
    return stable_hash({"case": case, "dataset_sha256": dataset_sha256, "schema_version": SCHEMA_VERSION})


def load_checkpoint(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {"schema": "safeplc.full_360.checkpoint.v1", "cases": {}}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("cases"), dict):
        raise ValueError(f"Invalid checkpoint: {path}")
    return value


def should_resume_case(
    checkpoint: Dict[str, Any],
    case_id: str,
    input_hash: str,
    output_path: Path,
) -> bool:
    item = (checkpoint.get("cases") or {}).get(case_id)
    return bool(
        isinstance(item, dict)
        and item.get("input_hash") == input_hash
        and item.get("complete") is True
        and output_path.is_file()
    )


def _row_from_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    case = payload.get("case") if isinstance(payload.get("case"), dict) else {}
    response = payload.get("response") if isinstance(payload.get("response"), dict) else {}
    acceptance = payload.get("acceptance") if isinstance(payload.get("acceptance"), dict) else {}
    return {
        "case_id": str(case.get("case_id") or ""),
        "benchmark_layer": str(case.get("benchmark_layer") or "core"),
        "category": str(case.get("category") or ""),
        "difficulty": str(case.get("difficulty") or "core"),
        "status": str(acceptance.get("status") or payload.get("status") or "ERROR"),
        "action": str(response.get("action") or ""),
        "verdict": str(response.get("verdict") or ""),
        "agent_calls": int(response.get("total_agent_calls") or 0),
        "latency_ms": int(response.get("total_latency_ms") or 0),
        "error": str((payload.get("error") or {}).get("message") or "") if isinstance(payload.get("error"), dict) else "",
    }


def _environment_record(config: SafePLCConfig, dataset_path: Path, dataset_sha256: str, started_at: str) -> Dict[str, Any]:
    return {
        "schema": "safeplc.full_360.environment.v1",
        "schema_version": SCHEMA_VERSION,
        "git_sha": git_value("rev-parse", "HEAD"),
        "dirty_worktree": dirty_worktree(),
        "dataset_path": str(dataset_path),
        "dataset_sha256": dataset_sha256,
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "mode": config.mode,
        "text_chroma_path": config.chroma_dir,
        "configured_text_collection": config.text_collection or "<auto-discover>",
        "selected_text_collection": "",
        "figure_chroma_path": config.figure_chroma_dir,
        "configured_figure_collection": config.figure_collection or "<auto-discover>",
        "selected_figure_collection": "",
        "embedding_backend": config.embedding_backend,
        "embedding_model": config.embedding_model_path,
        "jsonl_fallback_enabled": config.allow_jsonl_fallback,
        "jsonl_hybrid_enabled": config.enable_jsonl_hybrid,
        "query_expansion_enabled": config.enable_query_expansion,
        "max_expanded_queries": config.max_expanded_queries,
        "started_at": started_at,
        "finished_at": "",
        "status": "STARTED",
    }


def _default_run_case(case: Dict[str, Any]) -> Dict[str, Any]:
    return run_agent_system(
        str(case.get("query") or ""),
        context=str(case.get("context") or ""),
        mode="FULL",
        routing_strategy="adaptive",
        max_agents=4,
    ).to_dict()


def run_benchmark(
    *,
    cases_path: Path,
    output_dir: Path,
    case_ids: Sequence[str] = (),
    categories: Sequence[str] = (),
    max_cases: int = 0,
    resume: bool = False,
    start_index: int = 0,
    stop_on_error: bool = False,
    run_case: Callable[[Dict[str, Any]], Dict[str, Any]] = _default_run_case,
    environment_validator: Callable[[SafePLCConfig], List[str]] = validate_full_environment,
    collection_resolver: Callable[[SafePLCConfig], Dict[str, Any]] = resolve_selected_collections,
) -> int:
    if not cases_path.is_file():
        print(f"FULL-360 dataset is missing: {cases_path}", file=sys.stderr)
        return 2
    dataset_sha256 = sha256_file(cases_path)
    try:
        cases = load_jsonl(cases_path)
        selected = select_cases(
            cases,
            case_ids=case_ids,
            categories=categories,
            start_index=start_index,
            max_cases=max_cases,
        )
    except (ValueError, OSError) as exc:
        print(f"FULL-360 dataset selection failed: {exc}", file=sys.stderr)
        return 2

    os.environ["SAFEPLC_MODE"] = "FULL"
    os.environ["SAFEPLC_ALLOW_JSONL_FALLBACK"] = "0"
    os.environ["SAFEPLC_ENABLE_JSONL_HYBRID"] = "0"
    config = SafePLCConfig.from_env(mode="FULL")
    output_dir.mkdir(parents=True, exist_ok=True)
    environment_path = output_dir / "environment.json"
    checkpoint_path = output_dir / "checkpoint.json"
    run_log = output_dir / "run.log"
    acceptance_log = output_dir / "acceptance.log"
    if not resume:
        run_log.write_text("", encoding="utf-8")
        acceptance_log.write_text("", encoding="utf-8")

    started_at = now_iso()
    environment = _environment_record(config, cases_path, dataset_sha256, started_at)
    write_json(environment_path, environment)
    environment_errors = environment_validator(config)
    if environment_errors:
        environment.update({"status": "ERROR", "finished_at": now_iso(), "errors": environment_errors})
        write_json(environment_path, environment)
        append_log(run_log, "ENVIRONMENT ERROR " + ";".join(environment_errors))
        return 2
    try:
        environment.update(collection_resolver(config))
        write_json(environment_path, environment)
    except Exception as exc:
        environment.update({
            "status": "ERROR",
            "finished_at": now_iso(),
            "errors": [f"collection_resolution_failed:{type(exc).__name__}:{exc}"],
        })
        write_json(environment_path, environment)
        append_log(run_log, "ENVIRONMENT ERROR collection_resolution_failed")
        return 2

    try:
        checkpoint = load_checkpoint(checkpoint_path) if resume else {"schema": "safeplc.full_360.checkpoint.v1", "cases": {}}
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    rows: List[Dict[str, Any]] = []
    observed_text_collections = set()
    observed_figure_collections = set()
    for case in selected:
        case_id = str(case["case_id"])
        output_path = output_dir / f"{case_id}.json"
        input_hash = case_input_hash(case, dataset_sha256)
        if resume and should_resume_case(checkpoint, case_id, input_hash, output_path):
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            rows.append(_row_from_payload(payload))
            append_log(run_log, f"CASE RESUME-SKIP {case_id}")
            continue
        append_log(run_log, f"CASE START {case_id}")
        try:
            response = run_case(case)
            for evidence in _response_evidences(response):
                collection = str(evidence.get("collection_name") or "")
                if not collection:
                    continue
                backend = str(evidence.get("retrieval_backend") or "")
                (observed_figure_collections if "figure" in backend else observed_text_collections).add(collection)
            authenticity = truthfulness_errors(response)
            acceptance = evaluate_case(case, response)
            if authenticity:
                acceptance.update({"passed": False, "status": "ERROR", "authenticity_errors": authenticity})
            payload = {"case": case, "response": response, "acceptance": acceptance, "input_hash": input_hash}
            write_json(output_path, payload)
            append_log(
                acceptance_log,
                f"{case_id}\t{acceptance['status']}\t{json.dumps(acceptance.get('failures', []), ensure_ascii=False)}",
            )
        except Exception as exc:
            payload = {
                "case": case,
                "status": "ERROR",
                "input_hash": input_hash,
                "error": {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()},
            }
            write_json(output_path, payload)
            append_log(acceptance_log, f"{case_id}\tERROR\t{type(exc).__name__}: {exc}")
        row = _row_from_payload(payload)
        rows.append(row)
        checkpoint["dataset_sha256"] = dataset_sha256
        checkpoint["updated_at"] = now_iso()
        checkpoint.setdefault("cases", {})[case_id] = {
            "input_hash": input_hash,
            "complete": True,
            "status": row["status"],
            "output_file": output_path.name,
        }
        write_json(checkpoint_path, checkpoint)
        append_log(run_log, f"CASE END {case_id} status={row['status']}")
        if stop_on_error and row["status"] in {"FAIL", "ERROR"}:
            break

    counts = dict(Counter(row["status"] for row in rows))
    summary = {
        "schema": "safeplc.full_360.run_summary.v1",
        "git_sha": environment["git_sha"],
        "dataset_sha256": dataset_sha256,
        "case_count": len(rows),
        "counts": {status: counts.get(status, 0) for status in ("PASS", "FAIL", "ERROR")},
        "started_at": started_at,
        "finished_at": now_iso(),
        "cases": rows,
    }
    write_json(output_dir / "summary.json", summary)
    with (output_dir / "summary.tsv").open("w", encoding="utf-8", newline="\n") as handle:
        columns = (
            "case_id", "benchmark_layer", "category", "difficulty", "status", "action", "verdict",
            "agent_calls", "latency_ms", "error",
        )
        handle.write("\t".join(columns) + "\n")
        for row in rows:
            handle.write("\t".join(str(row[column]).replace("\t", " ").replace("\n", " ") for column in columns) + "\n")
    environment.update({
        "status": "COMPLETE",
        "finished_at": summary["finished_at"],
        "case_count": len(rows),
        "counts": summary["counts"],
        "observed_text_collections": sorted(observed_text_collections),
        "observed_figure_collections": sorted(observed_figure_collections),
    })
    write_json(environment_path, environment)
    append_log(run_log, f"END PASS={counts.get('PASS', 0)} FAIL={counts.get('FAIL', 0)} ERROR={counts.get('ERROR', 0)}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if counts.get("FAIL", 0) == 0 and counts.get("ERROR", 0) == 0 else 1


def _response_evidences(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    pool = response.get("evidence_pool") if isinstance(response.get("evidence_pool"), dict) else {}
    return [item for item in pool.get("evidences") or [] if isinstance(item, dict)]


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run SafePLC FULL-360 against real FULL Chroma assets.")
    parser.add_argument("--subset", choices=sorted(SUBSET_PATHS), default="dev120")
    parser.add_argument("--cases", default="", help="Explicit dataset path for controlled validation.")
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--category", action="append", default=[])
    parser.add_argument("--max-cases", type=int, default=0)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--stop-on-error", action="store_true")
    parser.add_argument("--output-dir", default="")
    args = parser.parse_args(argv)
    cases_path = Path(args.cases).expanduser().resolve() if args.cases else SUBSET_PATHS[args.subset]
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else DEFAULT_OUTPUT_DIRS[args.subset]
    return run_benchmark(
        cases_path=cases_path,
        output_dir=output_dir,
        case_ids=args.case_id,
        categories=args.category,
        max_cases=max(0, args.max_cases),
        resume=args.resume,
        start_index=max(0, args.start_index),
        stop_on_error=args.stop_on_error,
    )


if __name__ == "__main__":
    raise SystemExit(main())
