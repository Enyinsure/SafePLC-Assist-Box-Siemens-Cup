from conftest import run_sample


def test_figure_agent_returns_figure_id():
    response = run_sample("CPU 1517-3 PN 的 X1 接口在哪里？")
    figure_ids = [ev.figure_id for ev in response.evidence_pool.evidences]
    assert "fig_cpu1517_3pn_x1_x2" in figure_ids


