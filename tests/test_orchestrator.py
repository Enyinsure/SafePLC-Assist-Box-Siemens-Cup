from conftest import clear_safeplc_runtime_env, run_sample


def test_orchestrator_returns_metrics_and_shared_pool():
    response = run_sample("CPU 1517-3 PN 的 X1 接口在哪里？")
    assert response.metrics["total_agent_calls"] >= 1
    assert response.total_agent_calls == response.metrics["total_agent_calls"]
    assert response.selected_agents == response.agent_plan.selected_agents
    assert response.evidence_pool.evidences
    assert response.verifier["pass"]


def test_orchestrator_respects_max_agents():
    response = run_sample(
        "CPU 1517-3 PN 的 X1 接口在哪里，并说明 PROFINET 与 HMI 连接时的注意事项。",
        max_agents=1,
    )
    assert response.total_agent_calls <= 1


def test_full_missing_assets_warns_and_uses_same_orchestrator(monkeypatch):
    clear_safeplc_runtime_env(monkeypatch)
    response = run_sample(
        "CPU 1517-3 PN 的 X1 接口在哪里？",
        mode="FULL",
    )
    assert response.mode == "FULL"
    assert response.warnings
    assert any("FULL mode requested" in warning for warning in response.warnings)
    assert any("SAMPLE evidence was not used" in warning for warning in response.warnings)


