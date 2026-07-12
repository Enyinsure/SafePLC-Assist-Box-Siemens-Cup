from test_judge_accepts_structured_led_checklist import LED_TEXT
from retrieval_test_support import evidence
from safeplc_assist_box.agents.judge_agent import JudgeAgent
from safeplc_assist_box.schemas import QueryContext
from troubleshooting_test_support import run_troubleshooting


def test_judge_rechecks_led_labels_from_evidence():
    query, result, pool = run_troubleshooting([evidence("led-page", LED_TEXT, model="CPU 1517-3 PN/DP")])
    JudgeAgent().decide(QueryContext(query, question_type="TROUBLESHOOTING"), [result], pool)
    assert result.claims[0].metadata["evidence_led_groups"] == result.claims[0].metadata["found_led_groups"]
