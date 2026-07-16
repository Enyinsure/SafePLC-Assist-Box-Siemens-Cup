from __future__ import annotations

from conftest import clear_safeplc_runtime_env

from safeplc_assist_box.frontend.runtime import FrontendSettings, probe_runtime


def test_demo_runtime_never_claims_chroma_is_connected(monkeypatch) -> None:
    clear_safeplc_runtime_env(monkeypatch)
    settings = FrontendSettings(frontend_mode="demo", demo_enabled=True, pipeline_mode="SAMPLE")

    status = probe_runtime(settings)

    assert status["system"] == "离线演示"
    assert status["text_chroma"] == "离线快照"
    assert status["figure_chroma"] == "离线快照"
    assert status["model"] == "未调用"


def test_full_runtime_distinguishes_configured_path_from_observed_connection(monkeypatch, tmp_path) -> None:
    clear_safeplc_runtime_env(monkeypatch)
    monkeypatch.setenv("SAFEPLC_CHROMA_DIR", str(tmp_path))
    monkeypatch.setenv("SAFEPLC_FIGURE_CHROMA_DIR", str(tmp_path))
    settings = FrontendSettings(frontend_mode="online", demo_enabled=False, pipeline_mode="FULL")

    configured = probe_runtime(settings)
    observed = probe_runtime(
        settings,
        {"backend_audit": {"text_backend_active": True, "figure_backend_active": True}},
    )

    assert configured["text_chroma"] == "路径可用，待查询验证"
    assert configured["figure_chroma"] == "路径可用，待查询验证"
    assert observed["text_chroma"] == "已连接"
    assert observed["figure_chroma"] == "已连接"
