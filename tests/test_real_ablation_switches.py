from safeplc_assist_box.evaluation.run_agent_benchmark import METHOD_CONFIG
from safeplc_assist_box.agents.orchestrator import run_agent_system


def test_real_ablation_switches_are_distinct():
    assert METHOD_CONFIG["single_agent"]["enable_dynamic_routing"] is False
    assert METHOD_CONFIG["full"]["enable_verifier"] is True
    assert METHOD_CONFIG["dynamic_router_judge"]["enable_judge"] is True
    assert METHOD_CONFIG["dynamic_router_judge"]["enable_verifier"] is False
    assert METHOD_CONFIG["all_agents"]["routing_strategy"] == "all_agents"


def test_ablation_switches_change_runtime_path():
    config = METHOD_CONFIG["static_router"]
    response = run_agent_system(
        "CPU 1517-3 PN 的 X1 接口在哪里？",
        mode="SAMPLE",
        routing_strategy=config["routing_strategy"],
        max_agents=config["max_agents"],
        feature_switches={key: value for key, value in config.items() if key.startswith("enable_")},
    )
    assert response.routing_strategy == "static"
    assert response.metrics["feature_switches"]["enable_query_decomposition"] is False
    assert response.judge_decision.metadata["judge_enabled"] is False
    assert response.verifier["enabled"] is False
