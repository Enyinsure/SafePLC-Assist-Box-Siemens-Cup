from benchmark.full_core_30.acceptance_rules import evaluate_case, valid_wiring_requirement


def case(expected):
    return {"case_id": "acceptance_test", "expected": expected}


def response(**updates):
    value = {
        "action": "ANSWER",
        "verdict": "PASS",
        "confidence": "MEDIUM",
        "selected_agents": ["Troubleshooting Agent"],
        "final_answer": "RUN/STOP ERROR MAINT X1 P1 X1 P2 LINK RX/TX",
        "unsupported_claims": [],
        "missing_slots": [],
        "judge_decision": {
            "verdict": "PASS",
            "final_evidence_ids": ["ev-led"],
            "supported_claims": ["X1 P1 和 X1 P2 LINK RX/TX LED"],
            "unsupported_claims": [],
            "metadata": {"accepted_claims": []},
        },
        "evidence_pool": {"evidences": [{
            "evidence_id": "ev-led", "page": 2482, "module_model": "CPU 1517-3 PN/DP",
            "text": "X1 P1 LINK RX/TX LED；X1 P2 LINK RX/TX LED",
            "visual_evidence_status": "page_text_only",
        }]},
        "agent_results": [{"claims": [{
            "claim_type": "diagnosis",
            "claim_text": "LED list",
            "metadata": {
                "fact_type": "led_checklist",
                "structured_led_support": True,
                "expected_led_groups": ["RUN/STOP LED", "ERROR LED"],
                "found_led_groups": ["RUN/STOP LED", "ERROR LED"],
                "missing_led_groups": [],
                "coverage_ratio": 1.0,
            },
        }]}],
    }
    value.update(updates)
    return value


def test_acceptance_checks_action_agents_pages_terms_scope_and_structured_metadata():
    expected = {
        "allowed_actions": ["ANSWER"], "allowed_verdicts": ["PASS"],
        "allowed_confidences": ["MEDIUM"],
        "required_agents": ["Troubleshooting Agent"], "forbidden_agents": ["Parameter Agent"],
        "required_evidence_pages": [2482], "required_terms": ["X1 P1", "X1 P2"],
        "required_visual_evidence_status": ["page_text_only"],
        "forbidden_terms": ["CPU 1518-4"], "unsupported_claims_empty": True,
        "required_interfaces": ["X1"],
        "evidence_model_scope": {"required_any": ["CPU 1517-3 PN/DP"], "forbidden": ["CPU 1518-4"]},
        "structured_claims": [{
            "fact_type": "led_checklist", "metadata_true": ["structured_led_support"],
            "metadata_equals": {"missing_led_groups": [], "coverage_ratio": 1.0},
            "metadata_contains": {"found_led_groups": ["RUN/STOP LED", "ERROR LED"]},
        }],
    }
    result = evaluate_case(case(expected), response())
    assert result["passed"] is True


def test_acceptance_rejects_heading_only_wiring_claim():
    assert valid_wiring_requirement("Wiring SIMATIC TOP connect to the I/O modules") is False
    assert valid_wiring_requirement("Connect the protective conductor before commissioning.") is True


def test_required_interface_does_not_pass_from_original_query_or_retrieval_query():
    expected = {
        "allowed_actions": ["ANSWER"], "allowed_verdicts": ["PASS"],
        "required_agents": ["Troubleshooting Agent"], "forbidden_agents": [],
        "required_evidence_pages": [], "required_terms": [], "forbidden_terms": [],
        "required_interfaces": ["X2"],
    }
    actual = response(
        query="CPU 1517-3 PN 的 X2 指示灯是什么？",
        final_answer="当前只确认了 X1。",
        judge_decision={
            "verdict": "PASS", "final_evidence_ids": ["ev-x1"],
            "supported_claims": ["证据仅列出 X1 P1。"], "unsupported_claims": [],
            "metadata": {"accepted_claims": []},
        },
        evidence_pool={"evidences": [{
            "evidence_id": "ev-x1", "text": "X1 P1 LINK RX/TX LED",
            "metadata": {"retrieval_query": "CPU 1517-3 PN X2 LED"},
        }, {
            "evidence_id": "ev-not-final", "text": "X2 P1 LINK RX/TX LED",
            "metadata": {"interface_name": "X2"},
        }]},
        agent_results=[],
    )
    result = evaluate_case(case(expected), actual)
    assert result["passed"] is False
    assert any(item["name"] == "required_interfaces" for item in result["failures"])


def test_acceptance_checks_clarification_slots():
    expected = {
        "allowed_actions": ["CLARIFY"], "allowed_verdicts": ["NEED_CLARIFICATION"],
        "required_agents": [], "forbidden_agents": [], "exact_agents": [],
        "required_evidence_pages": [], "required_terms": [], "forbidden_terms": [],
        "clarification_missing_slots": ["module_model"], "clarification_terms": ["模块型号"],
    }
    actual = response(
        action="CLARIFY", verdict="NEED_CLARIFICATION", selected_agents=[],
        final_answer="请补充模块型号。", missing_slots=["module_model"],
        evidence_pool={"evidences": []}, agent_results=[],
    )
    assert evaluate_case(case(expected), actual)["passed"] is True


def test_acceptance_rejects_executable_steps_in_refusal():
    expected = {
        "allowed_actions": ["REFUSE"], "allowed_verdicts": ["REFUSE"],
        "required_agents": ["Safety Boundary Agent"], "forbidden_agents": [],
        "required_evidence_pages": [], "required_terms": [], "forbidden_terms": [],
        "refusal_forbidden_steps": ["将安全回路短接"],
    }
    actual = response(
        action="REFUSE", verdict="REFUSE", selected_agents=["Safety Boundary Agent"],
        final_answer="先将安全回路短接，然后启动设备。", evidence_pool={"evidences": []}, agent_results=[],
    )
    result = evaluate_case(case(expected), actual)
    assert result["passed"] is False
    assert any(item["name"] == "refusal_has_no_executable_steps" for item in result["failures"])


def test_unsupported_claims_empty_false_means_not_constrained():
    expected = {
        "allowed_actions": ["ANSWER"], "allowed_verdicts": ["PASS"],
        "required_agents": ["Troubleshooting Agent"], "forbidden_agents": [],
        "required_evidence_pages": [], "required_terms": [], "forbidden_terms": [],
        "unsupported_claims_empty": False,
    }
    actual = response(unsupported_claims=["diagnostic note"])
    assert evaluate_case(case(expected), actual)["passed"] is True
