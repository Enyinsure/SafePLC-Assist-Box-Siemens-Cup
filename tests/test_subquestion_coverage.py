from conftest import run_sample


def test_subquestion_coverage_for_multitask():
    response = run_sample("CPU 1517-3 PN 的 X1 接口在哪里，并说明 PROFINET 与 HMI 连接时的注意事项。")
    assert response.judge_decision.coverage
    assert response.judge_decision.coverage["sq_x1_location"]["answered"]
    assert response.judge_decision.coverage["sq_profinet_hmi"]["answered"]
