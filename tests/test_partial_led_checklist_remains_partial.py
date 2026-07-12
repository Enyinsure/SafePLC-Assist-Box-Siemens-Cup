from retrieval_test_support import evidence
from safeplc_assist_box.agents.judge_agent import JudgeAgent
from safeplc_assist_box.schemas import QueryContext
from troubleshooting_test_support import run_troubleshooting


def test_partial_led_checklist_remains_partial():
    query, result, pool = run_troubleshooting([
        evidence("led-page", "RUN/STOP LED ERROR LED MAINT LED", model="CPU 1517-3 PN/DP")
    ])
    decision = JudgeAgent().decide(QueryContext(query, question_type="TROUBLESHOOTING"), [result], pool)
    assert result.claims[0].metadata["structured_led_support"] is True
    assert result.claims[0].metadata["partial_coverage"] is True
    assert decision.verdict == "PARTIAL"
