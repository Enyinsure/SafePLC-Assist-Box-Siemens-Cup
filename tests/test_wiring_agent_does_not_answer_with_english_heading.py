from retrieval_test_support import evidence
from safeplc_assist_box.agents.judge_agent import JudgeAgent
from safeplc_assist_box.schemas import QueryContext
from wiring_test_support import run_wiring


def test_wiring_agent_does_not_answer_with_english_heading():
    heading = "Wiring SIMATIC TOP connect to the I/O modules"
    result, pool = run_wiring([evidence("top-connect", heading, model="S7-1500 / ET 200MP")])
    decision = JudgeAgent().decide(QueryContext("S7-1500 端子接线注意事项是什么？"), [result], pool)
    assert result.status not in {"ANSWERED", "PARTIAL"}
    assert decision.verdict != "PASS"
    assert heading not in decision.final_answer
