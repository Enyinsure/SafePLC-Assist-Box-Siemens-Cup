from safeplc_assist_box.agents.judge_agent import JudgeAgent
from safeplc_assist_box.schemas import AgentResult, EvidencePool, QueryContext


def test_judge_rejects_unsupported_result():
    decision = JudgeAgent().decide(
        QueryContext("q"),
        [AgentResult("Parameter Agent", "t1", "ANSWERED", answer_fragment="unsupported")],
        EvidencePool(),
    )
    assert "Parameter Agent" in decision.rejected_agent_outputs
    assert decision.verdict != "PASS"

