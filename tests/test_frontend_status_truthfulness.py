from __future__ import annotations

from conftest import clear_safeplc_runtime_env

from safeplc_assist_box.frontend.components.status_header import _runtime_class
from safeplc_assist_box.frontend.runtime import FrontendSettings, probe_runtime


def test_backend_unavailable_is_failed() -> None:
    assert _runtime_class("后端不可用") == "status-fail"
    assert _runtime_class("模型路径无效") == "status-fail"


def test_path_available_pending_is_warning() -> None:
    assert _runtime_class("路径可用，待查询验证") == "status-warning"


def test_connected_is_passed() -> None:
    assert _runtime_class("已连接") == "status-pass"


def test_runtime_probe_uses_effective_ui_pipeline_mode(monkeypatch) -> None:
    clear_safeplc_runtime_env(monkeypatch)
    settings = FrontendSettings(frontend_mode="online", demo_enabled=False, pipeline_mode="SAMPLE")

    runtime = probe_runtime(settings, effective_pipeline_mode="FULL")

    assert runtime["pipeline_mode"] == "FULL"
    assert runtime["text_chroma"] == "未配置"


def test_response_pipeline_mode_has_highest_priority(monkeypatch) -> None:
    clear_safeplc_runtime_env(monkeypatch)
    settings = FrontendSettings(frontend_mode="online", demo_enabled=False, pipeline_mode="SAMPLE")

    runtime = probe_runtime(
        settings,
        {"pipeline_mode": "MOCK", "source": "online_pipeline"},
        effective_pipeline_mode="FULL",
    )

    assert runtime["pipeline_mode"] == "MOCK"
    assert runtime["result_source_label"] == "真实流水线"
