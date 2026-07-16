from __future__ import annotations

from safeplc_assist_box.frontend.report_loader import (
    load_report_bundle,
    load_showcase_cases,
    load_supported_device_catalog,
)
from safeplc_assist_box.frontend.pages.system_benchmark import _query_module_states


def test_frontend_reports_only_use_repository_data() -> None:
    reports = load_report_bundle()
    cases = load_showcase_cases()
    catalog = load_supported_device_catalog()

    assert reports["benchmark"]["mode"] == "SAMPLE"
    assert reports["benchmark"]["case_count"] == 10
    assert 3 <= len(cases) <= 6
    assert all(case["source"] == "manual_curated_sample" for case in cases)
    assert sum(bool(case["offline_snapshot_available"]) for case in cases) == 5
    assert sum(not bool(case["offline_snapshot_available"]) for case in cases) == 1
    assert catalog == {"S7-1500": ["CPU 1517-3 PN/DP", "PS 60W 24/48/60VDC HF"]}


def test_system_page_distinguishes_module_import_from_query_execution() -> None:
    offline = _query_module_states({"runtime": {"source": "offline_demo_snapshot"}})
    online = _query_module_states(
        {
            "runtime": {
                "source": "online_pipeline",
                "feature_switches": {"enable_judge": False, "enable_verifier": True},
            },
            "selected_agents": [{"name": "Figure Agent"}],
            "raw_response": {"verifier": {"pass": True}},
        }
    )

    assert offline["judge"] == "快照记录，非本次执行"
    assert online["orchestrator"] == "已执行"
    assert online["agent_pool"] == "已执行 1 个 Agent"
    assert online["judge"] == "已关闭"
    assert online["verifier"] == "已执行"
