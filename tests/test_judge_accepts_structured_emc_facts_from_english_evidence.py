from emc_test_support import run_emc
from retrieval_test_support import evidence
from safeplc_assist_box.agents.judge_agent import JudgeAgent
from safeplc_assist_box.schemas import QueryContext


EMC_TEXT = """Fitting the cabling system and automation system in
grounded control cabinets/control boxes

Use of noise filters in the supply lines

SIMATIC products are designed for industrial use"""


def structured_emc_decision():
    result, pool = run_emc([evidence("emc-page", EMC_TEXT, model="S7-1500 / ET 200MP")])
    context = QueryContext("EMC 安装时接地和屏蔽需要注意什么？", question_type="EMC")
    return result, JudgeAgent().decide(context, [result], pool)


def test_judge_accepts_structured_emc_facts_from_english_evidence():
    result, decision = structured_emc_decision()
    assert result.claims[0].metadata["structured_emc_support"] is True
    assert decision.verdict == "PARTIAL"
    assert not decision.unsupported_claims
