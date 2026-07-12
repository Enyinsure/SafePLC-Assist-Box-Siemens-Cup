from safeplc_assist_box.evidence.fact_extractors import extract_wiring_facts


def test_wiring_rejects_heading_fragments():
    text = """接线
端子分配和接口说明
端子分配
TM NPU 底部的端子
下图显示了 TM NPU 底部的端子："""
    assert extract_wiring_facts(text) == []
