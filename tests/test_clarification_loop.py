from conftest import run_sample


def test_missing_key_model_triggers_clarification_before_agents():
    response = run_sample("某个模块的电源电压允许范围是多少？")
    assert response.agent_plan.need_clarification
    assert response.agent_results == []
    assert response.judge_decision.verdict == "NEED_CLARIFICATION"


