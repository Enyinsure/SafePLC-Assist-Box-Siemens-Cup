from benchmark.full_core_30.acceptance_rules import load_cases


ORIGINAL_IDS = [
    "parameter_voltage", "wiring_general", "troubleshooting_comm_led", "topology_hmi_profinet",
    "emc_ground_shield", "clarify_missing_model", "safety_live_bypass", "unsupported_x9",
    "cross_model_control", "compound_location_ports_fault",
]


def test_full_core_30_preserves_original_10_in_order():
    first = load_cases()[:10]
    assert [case["case_id"] for case in first] == ORIGINAL_IDS
    assert all(case["origin"] == "preserved_full_smoke_10" and case["server_verified"] for case in first)


def test_original_10_keep_frozen_acceptance_semantics():
    cases = {case["case_id"]: case["expected"] for case in load_cases()[:10]}
    assert cases["parameter_voltage"]["allowed_actions"] == ["ANSWER"]
    assert cases["parameter_voltage"]["allowed_verdicts"] == ["PASS"]
    assert cases["wiring_general"]["wiring_requirement"] is True
    assert cases["troubleshooting_comm_led"]["required_evidence_pages"] == [2482]
    assert cases["topology_hmi_profinet"]["exact_agents"] == []
    assert cases["topology_hmi_profinet"]["allowed_verdicts"] == ["NEED_CLARIFICATION"]
    assert cases["emc_ground_shield"]["required_evidence_pages"] == [6495]
    assert cases["compound_location_ports_fault"]["required_evidence_pages"] == [2476, 2482]
    assert cases["compound_location_ports_fault"]["required_agents"] == ["Figure Agent", "Troubleshooting Agent"]
