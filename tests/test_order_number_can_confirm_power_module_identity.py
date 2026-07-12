from safeplc_assist_box.evidence.model_identity import classify_model_match
from retrieval_test_support import evidence


def test_order_number_can_confirm_power_module_identity():
    item = evidence("ps", "power range", model="", order_number="6ES7505-0RB00-0AB0")
    assert classify_model_match("PS 60W 24/48/60VDC HF 6ES7505-0RB00-0AB0", item) == "exact_order_number"
