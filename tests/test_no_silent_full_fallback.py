from conftest import clear_safeplc_runtime_env

from safeplc_assist_box.agents.orchestrator import run_agent_system


def test_no_silent_full_fallback(monkeypatch):
    clear_safeplc_runtime_env(monkeypatch)
    monkeypatch.setenv("SAFEPLC_ALLOW_JSONL_FALLBACK", "0")
    monkeypatch.setenv("SAFEPLC_ENABLE_JSONL_HYBRID", "0")
    response = run_agent_system(
        "CPU 1517-3 PN 的 X1 接口在哪里？",
        mode="FULL",
        feature_switches={"enable_figure_backend": False},
    )
    assert response.mode == "FULL"
    assert response.evidence_pool.evidences == []
    assert response.verdict == "NEED_MORE_EVIDENCE"
    assert response.warnings
    assert any("SAMPLE evidence was not used" in warning for warning in response.warnings)
