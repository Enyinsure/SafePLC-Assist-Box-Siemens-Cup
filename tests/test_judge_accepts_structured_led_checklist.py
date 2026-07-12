from retrieval_test_support import evidence
from safeplc_assist_box.agents.judge_agent import JudgeAgent
from safeplc_assist_box.schemas import QueryContext
from troubleshooting_test_support import run_troubleshooting


LED_TEXT = """RUN/STOP LED 指示灯
ERROR LED 指示灯
MAINT LED 指示灯
端口 X1 P1 的 LINK RX/TX LED 指示灯
端口 X1 P2 的 LINK RX/TX LED 指示灯"""


def structured_led_decision():
    query, result, pool = run_troubleshooting([evidence("led-page", LED_TEXT, model="CPU 1517-3 PN/DP")])
    return result, JudgeAgent().decide(QueryContext(query, question_type="TROUBLESHOOTING"), [result], pool)


def test_judge_accepts_structured_led_checklist():
    result, decision = structured_led_decision()
    assert decision.verdict == "PASS"
    assert result.claims[0].metadata["structured_led_support"] is True
    assert not decision.unsupported_claims
