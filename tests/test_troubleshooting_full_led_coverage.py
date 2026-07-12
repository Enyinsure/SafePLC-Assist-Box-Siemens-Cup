from retrieval_test_support import evidence
from safeplc_assist_box.agents.judge_agent import JudgeAgent
from safeplc_assist_box.schemas import QueryContext
from troubleshooting_test_support import run_troubleshooting


def test_troubleshooting_full_led_coverage():
    text = "RUN/STOP LED ERROR LED MAINT LED 端口 X1 P1 的 LINK RX/TX LED 端口 X1 P2 的 LINK RX/TX LED"
    query, result, pool = run_troubleshooting([evidence("full-led", text, model="CPU 1517-3 PN/DP")])
    metadata = result.claims[0].metadata
    decision = JudgeAgent().decide(QueryContext(query, question_type="TROUBLESHOOTING"), [result], pool)
    assert result.status == "ANSWERED"
    assert metadata["missing_led_groups"] == []
    assert metadata["coverage_ratio"] == 1.0
    assert decision.verdict == "PASS"
