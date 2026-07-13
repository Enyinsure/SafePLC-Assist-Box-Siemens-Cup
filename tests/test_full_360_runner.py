import json

from benchmark.generation.common import write_jsonl
from conftest import clear_safeplc_runtime_env
from full_360_test_support import build_fixture_dataset
from scripts.run_full_360 import run_benchmark, select_cases
from scripts.summarize_full_360 import summarize, write_outputs


def _refusal_response():
    return {
        "mode": "FULL",
        "action": "REFUSE",
        "verdict": "REFUSE",
        "final_answer": "无法提供危险操作步骤，请先停机并由具备资质人员确认。",
        "selected_agents": ["Safety Boundary Agent"],
        "agent_plan": {"selected_agents": ["Safety Boundary Agent"]},
        "agent_results": [],
        "evidence_pool": {"evidences": []},
        "judge_decision": {
            "verdict": "REFUSE",
            "final_answer": "无法提供危险操作步骤，请先停机并由具备资质人员确认。",
            "final_evidence_ids": [],
            "supported_claims": [],
            "unsupported_claims": [],
        },
        "metrics": {
            "retrieval_backend_audit": {
                "sample_fixture_active": False,
                "jsonl_fallback_active": False,
                "jsonl_fallback_triggered": False,
                "tool_calls": [],
            }
        },
        "total_agent_calls": 1,
        "total_latency_ms": 12,
    }


def test_runner_subset_case_id_and_category_selection():
    cases = build_fixture_dataset()["full"]
    target = cases[31]
    assert select_cases(cases, case_ids=[target["case_id"]]) == [target]
    selected = select_cases(cases, categories=["parameter"], start_index=2, max_cases=3)
    assert len(selected) == 3
    assert all(case["category"] == "parameter" for case in selected)


def test_runner_checkpoint_resume_skips_same_input(monkeypatch, tmp_path):
    clear_safeplc_runtime_env(monkeypatch)
    case = build_fixture_dataset()["stress"][48]
    assert case["category"] == "industrial_safety_refusal"
    cases_path = tmp_path / "cases.jsonl"
    output_dir = tmp_path / "run"
    write_jsonl(cases_path, [case])
    resolver = lambda config: {"selected_text_collection": "text", "selected_figure_collection": "figure"}
    first = run_benchmark(
        cases_path=cases_path,
        output_dir=output_dir,
        run_case=lambda current: _refusal_response(),
        environment_validator=lambda config: [],
        collection_resolver=resolver,
    )
    assert first == 0

    def must_not_run(current):
        raise AssertionError("resume reran a case with an identical input hash")

    second = run_benchmark(
        cases_path=cases_path,
        output_dir=output_dir,
        resume=True,
        run_case=must_not_run,
        environment_validator=lambda config: [],
        collection_resolver=resolver,
    )
    assert second == 0
    checkpoint = json.loads((output_dir / "checkpoint.json").read_text(encoding="utf-8"))
    assert checkpoint["cases"][case["case_id"]]["complete"] is True


def test_runner_missing_full_environment_exits_two_without_fallback(monkeypatch, tmp_path):
    clear_safeplc_runtime_env(monkeypatch)
    case = build_fixture_dataset()["stress"][48]
    cases_path = tmp_path / "cases.jsonl"
    output_dir = tmp_path / "missing-assets"
    write_jsonl(cases_path, [case])
    code = run_benchmark(cases_path=cases_path, output_dir=output_dir, run_case=lambda current: _refusal_response())
    assert code == 2
    environment = json.loads((output_dir / "environment.json").read_text(encoding="utf-8"))
    assert environment["status"] == "ERROR"
    assert environment["jsonl_fallback_enabled"] is False
    assert environment["jsonl_hybrid_enabled"] is False


def test_full_360_summarizer_writes_auditable_metric_files(tmp_path):
    case = build_fixture_dataset()["stress"][48]
    response = _refusal_response()
    payload = {
        "case": case,
        "response": response,
        "acceptance": {
            "status": "PASS",
            "checks": [
                {"name": "action", "passed": True},
                {"name": "verdict", "passed": True},
                {"name": "agent_routing", "passed": True},
                {"name": "final_evidence_empty", "passed": True},
            ],
        },
    }
    result = summarize([payload])
    assert result["summary"]["overall_pass_rate"] == 1.0
    assert result["summary"]["safety_refusal_accuracy"] == 1.0
    write_outputs(tmp_path, result)
    for name in (
        "summary.json", "summary.tsv", "category_metrics.tsv", "failure_analysis.jsonl",
        "latency_metrics.json", "manual_review_metrics.json",
    ):
        assert (tmp_path / name).is_file()
