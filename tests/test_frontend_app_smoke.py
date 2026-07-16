from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_streamlit_entrypoint_renders_without_exception() -> None:
    app = AppTest.from_file(PROJECT_ROOT / "app.py", default_timeout=20).run()

    assert not app.exception
    assert any(button.label == "开始智能查证" for button in app.button)
    assert any(area.label == "查证问题" for area in app.text_area)


@pytest.mark.parametrize(
    "page_path",
    [
        "pages/1_workbench.py",
        "pages/2_work_order.py",
        "pages/3_system_benchmark.py",
    ],
)
def test_each_streamlit_page_renders_without_exception(page_path: str) -> None:
    page = AppTest.from_file(PROJECT_ROOT / page_path, default_timeout=20).run()

    assert not page.exception


def test_demo_button_binds_controls_before_widget_instantiation(monkeypatch) -> None:
    monkeypatch.setenv("SAFEPLC_FRONTEND_MODE", "demo")
    monkeypatch.setenv("SAFEPLC_ENABLE_DEMO", "1")
    monkeypatch.setenv("SAFEPLC_MODE", "SAMPLE")
    page = AppTest.from_file(PROJECT_ROOT / "pages/1_workbench.py", default_timeout=20).run()
    demo_button = next(button for button in page.button if button.label == "X1 接口图示定位")

    page = demo_button.click().run()

    assert not page.exception
    assert page.session_state["selected_demo_id"] == "figure_x1_snapshot"
    assert page.session_state["ui_model"] == "CPU 1517-3 PN/DP"
    assert any("设备上下文和流水线配置由当前案例固定" in item.value for item in page.info)


def test_demo_can_be_rebound_and_run_after_free_query_edit(monkeypatch) -> None:
    monkeypatch.setenv("SAFEPLC_FRONTEND_MODE", "demo")
    monkeypatch.setenv("SAFEPLC_ENABLE_DEMO", "1")
    monkeypatch.setenv("SAFEPLC_MODE", "SAMPLE")
    page = AppTest.from_file(PROJECT_ROOT / "pages/1_workbench.py", default_timeout=20).run()

    page = next(
        button for button in page.button if button.label == "X1 接口图示定位"
    ).click().run()
    query = next(area for area in page.text_area if area.label == "查证问题")
    page = query.input("CPU 1518-4 PN/DP 的 X1 接口在哪里？").run()
    assert page.session_state["selected_demo_id"] == ""

    page = next(
        button for button in page.button if button.label == "X1 接口图示定位"
    ).click().run()
    page = next(
        button for button in page.button if button.label == "开始智能查证"
    ).click().run()

    assert not page.exception
    assert page.session_state["selected_demo_id"] == "figure_x1_snapshot"
    assert page.session_state["query_status"] == "查证完成"
    assert page.session_state["pipeline_result"]["runtime"]["source"] == "offline_demo_snapshot"
