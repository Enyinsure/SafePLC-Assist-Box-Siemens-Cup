from retrieval_test_support import evidence
from safeplc_assist_box.agents.judge_agent import JudgeAgent
from safeplc_assist_box.schemas import QueryContext
from troubleshooting_test_support import run_troubleshooting


def test_troubleshooting_partial_when_link_led_missing():
    query, result, pool = run_troubleshooting([
        evidence("partial-led", "RUN/STOP LED ERROR LED MAINT LED", model="CPU 1517-3 PN/DP")
    ])
    decision = JudgeAgent().decide(QueryContext(query, question_type="TROUBLESHOOTING"), [result], pool)
    assert result.status == "PARTIAL"
    assert result.claims[0].metadata["missing_led_groups"] == [
        "X1 P1 LINK RX/TX LED", "X1 P2 LINK RX/TX LED",
    ]
    assert decision.verdict == "PARTIAL"
