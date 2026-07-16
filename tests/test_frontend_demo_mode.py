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
        PipelineRequest(query=case["query"], context=case["context"], selected_demo_id=case["id"]),
        settings,
    )

    assert outcome.ok is True
    assert outcome.source == "offline_demo_snapshot"
    assert outcome.normalized["runtime"]["source"] == "offline_demo_snapshot"
    assert any("SAMPLE" in warning for warning in outcome.normalized["runtime"]["warnings"])
