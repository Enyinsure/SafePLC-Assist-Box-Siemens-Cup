from __future__ import annotations

from pathlib import Path

from safeplc_assist_box.frontend.demo_loader import load_demo_cases
from safeplc_assist_box.frontend.pipeline_adapter import PipelineRequest, execute_pipeline
from safeplc_assist_box.frontend.runtime import FrontendSettings


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_every_declared_demo_snapshot_exists() -> None:
    cases = load_demo_cases()

    assert len(cases) >= 6
    for case in cases:
        assert (PROJECT_ROOT / case["snapshot"]).is_file()


def test_demo_mode_requires_explicit_matching_case() -> None:
    settings = FrontendSettings(frontend_mode="demo", demo_enabled=True, pipeline_mode="SAMPLE")

    free_query = execute_pipeline(PipelineRequest(query="自由问题"), settings)
    mismatch = execute_pipeline(
        PipelineRequest(query="被修改的问题", selected_demo_id="figure_x1_snapshot"),
        settings,
    )

    assert free_query.ok is False
    assert "自由问题" in free_query.user_error
    assert mismatch.ok is False
    assert "偏离典型案例" in mismatch.user_error


def test_demo_mode_loads_real_sample_snapshot_and_marks_source() -> None:
    case = load_demo_cases()[0]
    settings = FrontendSettings(frontend_mode="demo", demo_enabled=True, pipeline_mode="SAMPLE")

    outcome = execute_pipeline(
        PipelineRequest(
            query=case["query"],
            context=case["context"],
            user_context=case["context"],
            device_context=dict(case["device_context"]),
            pipeline_mode=case["pipeline_mode"],
            selected_demo_id=case["id"],
        ),
        settings,
    )

    assert outcome.ok is True
    assert outcome.source == "offline_demo_snapshot"
    assert outcome.normalized["runtime"]["source"] == "offline_demo_snapshot"
    assert any("SAMPLE" in warning for warning in outcome.normalized["runtime"]["warnings"])


def test_online_timeout_is_reported_without_demo_substitution(monkeypatch) -> None:
    from safeplc_assist_box.frontend import pipeline_adapter

    def raise_timeout(*_args, **_kwargs):
        raise TimeoutError("retrieval timed out")

    monkeypatch.setattr(pipeline_adapter, "_load_orchestrator", lambda: raise_timeout)
    settings = FrontendSettings(frontend_mode="online", demo_enabled=True, pipeline_mode="FULL")

    outcome = execute_pipeline(PipelineRequest(query="自由问题"), settings)

    assert outcome.ok is False
    assert "请求超时" in outcome.user_error
    assert outcome.source == "online_pipeline"


def test_normalization_failure_is_not_pipeline_success(monkeypatch) -> None:
    from safeplc_assist_box.frontend import pipeline_adapter

    monkeypatch.setattr(pipeline_adapter, "_load_orchestrator", lambda: lambda *_args, **_kwargs: ["bad"])
    settings = FrontendSettings(frontend_mode="online", demo_enabled=False, pipeline_mode="SAMPLE")

    outcome = execute_pipeline(PipelineRequest(query="测试"), settings)

    assert outcome.ok is False
    assert outcome.normalized["normalization"]["status"] == "failed"
    assert outcome.raw == ["bad"]
    assert outcome.normalized["raw_response"] == ["bad"]
    assert "无法解析" in outcome.user_error


def test_free_query_is_never_replaced_by_demo_snapshot(monkeypatch) -> None:
    from safeplc_assist_box.frontend import pipeline_adapter

    def backend_failure(*_args, **_kwargs):
        raise RuntimeError("backend unavailable")

    monkeypatch.setattr(pipeline_adapter, "_load_orchestrator", lambda: backend_failure)
    settings = FrontendSettings(frontend_mode="auto", demo_enabled=True, pipeline_mode="SAMPLE")

    outcome = execute_pipeline(PipelineRequest(query="完全自由的问题"), settings)

    assert outcome.ok is False
    assert outcome.normalized is None
    assert outcome.source == "online_pipeline"


def test_full_pipeline_failure_never_falls_back_to_selected_sample_snapshot(monkeypatch) -> None:
    from safeplc_assist_box.frontend import pipeline_adapter

    case = load_demo_cases()[0]

    def backend_failure(*_args, **_kwargs):
        raise RuntimeError("FULL backend unavailable")

    monkeypatch.setattr(pipeline_adapter, "_load_orchestrator", lambda: backend_failure)
    settings = FrontendSettings(frontend_mode="auto", demo_enabled=True, pipeline_mode="FULL")
    outcome = execute_pipeline(
        PipelineRequest(
            query=case["query"],
            context=case["context"],
            user_context=case["context"],
            device_context=dict(case["device_context"]),
            pipeline_mode="FULL",
            selected_demo_id=case["id"],
        ),
        settings,
    )

    assert outcome.ok is False
    assert outcome.source == "online_pipeline"
    assert outcome.normalized is None
