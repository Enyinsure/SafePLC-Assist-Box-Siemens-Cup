from conftest import run_sample


def test_orchestrator_returns_metrics_and_shared_pool():
    response = run_sample("CPU 1517-3 PN 的 X1 接口在哪里？")
    assert response.metrics["total_agent_calls"] >= 1
    assert response.evidence_pool.evidences
    assert response.verifier["pass"]


