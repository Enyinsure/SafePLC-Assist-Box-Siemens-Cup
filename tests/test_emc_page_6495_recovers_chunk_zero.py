from safeplc_assist_box.evidence.fact_extractors import extract_emc_facts
from test_same_page_chunk_aggregation import aggregated_items


def test_emc_page_6495_recovers_chunk_zero(tmp_path):
    facts = extract_emc_facts(aggregated_items(tmp_path)[0].text)
    assert "可采用接地控制柜或控制箱。" in facts
    assert "可在电源线上使用噪声滤波器。" in facts
