from retrieval_test_support import evidence
from safeplc_assist_box.agents.judge_agent import JudgeAgent
from safeplc_assist_box.schemas import QueryContext
from troubleshooting_test_support import run_troubleshooting


def test_judge_rejects_led_label_not_in_evidence():
    text = "RUN/STOP LED ERROR LED MAINT LED 端口 X1 P1 的 LINK RX/TX LED 指示灯"
    query, result, pool = run_troubleshooting([evidence("led-page", text, model="CPU 1517-3 PN/DP")])
    claim = result.claims[0]
    invented = "X1 P2 LINK RX/TX LED"
    claim.metadata["found_led_groups"].append(invented)
    claim.metadata["missing_led_groups"] = []
    claim.metadata["coverage_ratio"] = 1.0
    claim.claim_text = claim.claim_text.rstrip("。") + "、" + invented + "。"
    decision = JudgeAgent().decide(QueryContext(query, question_type="TROUBLESHOOTING"), [result], pool)
    assert decision.verdict != "PASS"
    assert any("structured_led_label_not_in_evidence" in item for item in decision.unsupported_claims)
