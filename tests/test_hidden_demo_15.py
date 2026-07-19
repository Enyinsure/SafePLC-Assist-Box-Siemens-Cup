from __future__ import annotations

import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from conftest import clear_safeplc_runtime_env
from safeplc_assist_box.frontend.demo_loader import load_demo_cases
from safeplc_assist_box.frontend.demo_visual_assets import (
    CORE_VISUAL_MANIFEST,
    load_demo_visual_manifest,
)
from safeplc_assist_box.frontend.hidden_demo_matcher import (
    EXPECTED_CASE_IDS,
    hidden_query_hash,
    load_hidden_demo_registry,
    load_hidden_demo_snapshot,
    match_hidden_demo_query,
    normalize_hidden_query,
    validate_hidden_demo_package,
)
from safeplc_assist_box.frontend.paths import PROJECT_ROOT
from safeplc_assist_box.frontend.pipeline_adapter import PipelineRequest, execute_pipeline
from safeplc_assist_box.frontend.runtime import FrontendSettings


HIDDEN_CASES = load_hidden_demo_registry()
HIDDEN_BY_ID = {case["id"]: case for case in HIDDEN_CASES}


def _snapshot(case_id: str) -> dict:
    case = HIDDEN_BY_ID[case_id]
    return json.loads((PROJECT_ROOT / case["snapshot"]).read_text(encoding="utf-8"))


def _settings(*, enabled: bool, debug: bool = False) -> FrontendSettings:
    return FrontendSettings(
        frontend_mode="demo",
        demo_enabled=True,
        pipeline_mode="SAMPLE",
        hidden_demo_enabled=enabled,
        hidden_demo_debug=debug,
    )


def test_hidden_demo_count_is_exactly_15() -> None:
    assert [case["id"] for case in HIDDEN_CASES] == list(EXPECTED_CASE_IDS)


def test_visual_manifest_count_is_exactly_150() -> None:
    assets = load_demo_visual_manifest(CORE_VISUAL_MANIFEST)
    assert len(assets) == 150
    assert [item["asset_id"] for item in assets] == [
        f"VIS_{index:04d}" for index in range(1, 151)
    ]


def test_visual_manifest_has_no_duplicate_sha256() -> None:
    assets = load_demo_visual_manifest(CORE_VISUAL_MANIFEST)
    assert len({item["sha256"] for item in assets}) == 150
    assert len({item["relative_path"] for item in assets}) == 150


def test_all_visual_assets_exist_and_decode() -> None:
    validation = validate_hidden_demo_package()
    assert validation.ok, validation.errors
    assert validation.decoded_asset_count == 150


def test_all_150_assets_are_referenced() -> None:
    referenced = {
        asset_id
        for case_id in EXPECTED_CASE_IDS
        for asset_id in _snapshot(case_id)["visual_asset_ids"]
    }
    assert referenced == {f"VIS_{index:04d}" for index in range(1, 151)}


def test_hidden_queries_are_not_visible_in_public_demo_list() -> None:
    public_queries = {normalize_hidden_query(case["query"]) for case in load_demo_cases()}
    hidden_queries = {normalize_hidden_query(case["query"]) for case in HIDDEN_CASES}

    assert public_queries.isdisjoint(hidden_queries)
    public_files = [
        PROJECT_ROOT / "safeplc_assist_box" / "frontend" / "data" / "demo_cases.json",
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / "pages" / "1_workbench.py",
        PROJECT_ROOT / "pages" / "3_system_benchmark.py",
    ]
    public_text = "\n".join(path.read_text(encoding="utf-8") for path in public_files)
    assert all(case["query"] not in public_text for case in HIDDEN_CASES)


def test_hidden_demo_disabled_by_default(monkeypatch) -> None:
    clear_safeplc_runtime_env(monkeypatch)
    settings = FrontendSettings.from_env()
    assert settings.hidden_demo_enabled is False
    assert settings.hidden_demo_debug is False


def test_hidden_demo_requires_explicit_enable_flag() -> None:
    case = HIDDEN_CASES[0]

    disabled = execute_pipeline(PipelineRequest(query=case["query"]), _settings(enabled=False))
    enabled = execute_pipeline(PipelineRequest(query=case["query"]), _settings(enabled=True))

    assert disabled.ok is False
    assert enabled.ok is True
    assert enabled.source == "offline_demo_snapshot"


def test_free_query_never_uses_nearest_hidden_snapshot() -> None:
    outcome = execute_pipeline(
        PipelineRequest(query="请随便找一个接近的 PLC 图给我"),
        _settings(enabled=True),
    )

    assert outcome.ok is False
    assert outcome.normalized is None
    assert "没有离线快照" in outcome.user_error


def test_changed_order_number_rejects_hidden_snapshot() -> None:
    query = HIDDEN_BY_ID["HIDDEN_12"]["query"].replace(
        "6ES7505-0RB00-0AB0", "6ES7505-0RA00-0AB0"
    )

    assert match_hidden_demo_query(query) is None
    assert execute_pipeline(PipelineRequest(query=query), _settings(enabled=True)).ok is False


def test_changed_bf_sf_state_rejects_hidden_snapshot() -> None:
    query = HIDDEN_BY_ID["HIDDEN_08"]["query"].replace("SF 未亮", "SF 红色常亮")

    assert match_hidden_demo_query(query) is None
    assert execute_pipeline(PipelineRequest(query=query), _settings(enabled=True)).ok is False


def test_hidden_snapshot_source_is_offline_demo() -> None:
    for case in HIDDEN_CASES:
        snapshot = _snapshot(case["id"])
        assert snapshot["source"] == "offline_demo_snapshot"


def test_hidden_snapshot_never_reports_full_online() -> None:
    for case in HIDDEN_CASES:
        snapshot = _snapshot(case["id"])
        assert snapshot["pipeline_mode"] == "SAMPLE"
        assert snapshot["mode"] == "SAMPLE"
        assert "FULL 查询成功" not in snapshot["final_answer"]


@pytest.mark.parametrize("case_id", EXPECTED_CASE_IDS)
def test_hidden_snapshot_schema(case_id: str) -> None:
    case = HIDDEN_BY_ID[case_id]
    snapshot = _snapshot(case_id)

    assert snapshot["schema_version"] == "hidden-demo-v1"
    assert snapshot["case_id"] == case_id
    assert snapshot["immutable"] is True
    assert snapshot["query_hash"] == hidden_query_hash(case["query"])
    assert snapshot["snapshot_validation"] == {"valid": True, "errors": []}


@pytest.mark.parametrize("case_id", EXPECTED_CASE_IDS)
def test_hidden_snapshot_has_no_dangling_evidence(case_id: str) -> None:
    snapshot = _snapshot(case_id)
    evidences = snapshot["evidence_pool"]["evidences"]
    evidence_ids = {item["evidence_id"] for item in evidences}
    final_ids = set(snapshot["judge_decision"]["final_evidence_ids"])

    assert final_ids
    assert final_ids <= evidence_ids
    assert {item["asset_id"] for item in evidences} == set(snapshot["visual_asset_ids"])
    for claim in snapshot["judge_decision"]["metadata"]["accepted_claims"]:
        assert set(claim["evidence_ids"]) <= final_ids


@pytest.mark.parametrize("case_id", EXPECTED_CASE_IDS)
def test_hidden_snapshot_device_matches_evidence(case_id: str) -> None:
    case = HIDDEN_BY_ID[case_id]
    snapshot = _snapshot(case_id)
    order_number = case["device_context"]["order_number"]
    final_ids = set(snapshot["judge_decision"]["final_evidence_ids"])
    accepted = [
        item
        for item in snapshot["evidence_pool"]["evidences"]
        if item["evidence_id"] in final_ids
    ]

    if order_number:
        assert {item["order_number"] for item in accepted} == {order_number}
    assert snapshot["judge_decision"]["model_consistency"]["pass"] is True


@pytest.mark.parametrize("case_id", EXPECTED_CASE_IDS)
def test_hidden_snapshot_visual_rules(case_id: str) -> None:
    case = HIDDEN_BY_ID[case_id]
    snapshot = load_hidden_demo_snapshot(case)
    visual_ids = snapshot["visual_asset_ids"]

    assert 3 <= len(visual_ids) <= 15
    assert set(snapshot["visual_coverage_reason"]) == set(visual_ids)
    for evidence in snapshot["evidence_pool"]["evidences"]:
        assert evidence["visual_evidence_status"] == "image_available"
        assert evidence["image_exists"] is True
        assert Path(evidence["resolved_image_path"]).is_file()


@pytest.mark.parametrize("case_id", EXPECTED_CASE_IDS)
def test_hidden_snapshot_judge_rules(case_id: str) -> None:
    snapshot = _snapshot(case_id)
    judge = snapshot["judge_decision"]

    assert judge["verdict"] == snapshot["verdict"]
    assert judge["unsupported_claims"] == []
    assert judge["conflicting_claims"] == []
    assert judge["metadata"]["accepted_claims"]
    if case_id == "HIDDEN_14":
        assert snapshot["action"] == snapshot["verdict"] == "REFUSE"
        assert "不得短接" in snapshot["final_answer"]
        assert "不得带电拔插" in snapshot["final_answer"]


@pytest.mark.parametrize("case_id", EXPECTED_CASE_IDS)
def test_hidden_snapshot_renders_in_streamlit(case_id: str) -> None:
    case = HIDDEN_BY_ID[case_id]
    outcome = execute_pipeline(PipelineRequest(query=case["query"]), _settings(enabled=True))

    assert outcome.ok is True
    assert outcome.source == "offline_demo_snapshot"
    assert outcome.normalized["runtime"]["pipeline_mode"] == "SAMPLE"
    assert outcome.normalized["answer"]["summary"]
    assert len(outcome.normalized["evidence_pool"]) == len(_snapshot(case_id)["visual_asset_ids"])
    assert all(item["image_path"] for item in outcome.normalized["evidence_pool"])


def test_case_specific_hidden_demo_contracts() -> None:
    h01 = _snapshot("HIDDEN_01")
    h12 = _snapshot("HIDDEN_12")
    h15 = _snapshot("HIDDEN_15")

    assert {"Wiring Agent", "Figure Agent"} <= {
        item["agent_name"] for item in h01["agent_results"]
    }
    assert "X1" not in h01["final_answer"] and "X2" not in h01["final_answer"]
    assert "静态输入范围为 19.2～72 V DC" in h12["final_answer"]
    assert "动态输入范围为 18.5～75.5 V DC" in h12["final_answer"]
    final_ids = set(h15["judge_decision"]["final_evidence_ids"])
    accepted = [
        item
        for item in h15["evidence_pool"]["evidences"]
        if item["evidence_id"] in final_ids
    ]
    assert {item["module_model"] for item in accepted} == {"CPU 1517-3 PN/DP"}
    assert {item["order_number"] for item in accepted} == {"6ES7517-3AP00-0AB0"}
    assert h15["evidence_pool"]["metadata"]["cross_model_blocked"] > 0


def test_exact_hidden_query_renders_through_streamlit_workbench(monkeypatch) -> None:
    clear_safeplc_runtime_env(monkeypatch)
    monkeypatch.setenv("SAFEPLC_FRONTEND_MODE", "demo")
    monkeypatch.setenv("SAFEPLC_ENABLE_DEMO", "1")
    monkeypatch.setenv("SAFEPLC_ENABLE_HIDDEN_DEMO", "1")
    monkeypatch.setenv("SAFEPLC_MODE", "SAMPLE")
    case = HIDDEN_BY_ID["HIDDEN_12"]
    page = AppTest.from_file(
        PROJECT_ROOT / "pages" / "1_workbench.py",
        default_timeout=30,
    ).run()

    page = next(area for area in page.text_area if area.label == "查证问题").input(
        case["query"]
    ).run()
    page = next(button for button in page.button if button.label == "开始智能查证").click().run()

    assert not page.exception
    result = page.session_state["pipeline_result"]
    assert result["runtime"]["source"] == "offline_demo_snapshot"
    assert result["runtime"]["pipeline_mode"] == "SAMPLE"
    assert len(result["evidence_pool"]) == 6
    assert all(item["image_path"] for item in result["evidence_pool"])
