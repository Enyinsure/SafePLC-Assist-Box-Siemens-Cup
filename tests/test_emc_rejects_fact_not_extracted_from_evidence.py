from emc_test_support import run_emc
from retrieval_test_support import evidence
from safeplc_assist_box.agents.judge_agent import JudgeAgent
from safeplc_assist_box.schemas import QueryContext
from test_judge_accepts_structured_emc_facts_from_english_evidence import EMC_TEXT


def test_emc_rejects_fact_not_extracted_from_evidence():
    result, pool = run_emc([evidence("emc-page", EMC_TEXT, model="S7-1500 / ET 200MP")])
    claim = result.claims[0]
    invented = "应采用低阻抗接地。"
    claim.metadata["positive_facts"].append(invented)
    claim.metadata["installation_fact_count"] += 1
    claim.claim_text += invented
    decision = JudgeAgent().decide(
        QueryContext("EMC 安装时接地和屏蔽需要注意什么？", question_type="EMC"), [result], pool
    )
    assert decision.verdict != "PASS"
    assert any("structured_emc_fact_not_in_evidence" in item for item in decision.unsupported_claims)
