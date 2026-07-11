from safeplc_assist_box.agents.context_analyzer import ContextAnalyzer
from safeplc_assist_box.agents.supervisor_agent import SupervisorAgent


def test_supervisor_selects_figure_without_all_agents():
    ctx = ContextAnalyzer().analyze("CPU 1517-3 PN 的 X1 接口在哪里？")
    plan = SupervisorAgent().plan(ctx, routing_strategy="adaptive", max_agents=4)
    assert "Figure Agent" in plan.selected_agents
    assert len(plan.selected_agents) < 8
    assert "Parameter Agent" in plan.rejected_agents

