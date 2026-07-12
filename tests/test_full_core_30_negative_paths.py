from benchmark.full_core_30.acceptance_rules import evaluate_case, load_cases


CASES = {item["case_id"]: item for item in load_cases()}


def response(action, verdict, answer, agents, slots=None, evidence=None, supported=None, missing_slots=None):
    evidences = evidence or []
    return {
        "action": action,
        "verdict": verdict,
        "selected_agents": agents,
        "final_answer": answer,
        "missing_slots": missing_slots or [],
        "unsupported_claims": ["expected abstain detail"],
        "query_context": {
            "slots": {
                name: {"name": name, "value": value, "confidence": 1.0}
                for name, value in (slots or {}).items()
            },
            "missing_slots": missing_slots or [],
        },
        "evidence_pool": {"evidences": evidences},
        "judge_decision": {
            "verdict": verdict,
            "final_evidence_ids": [],
            "supported_claims": supported or [],
            "unsupported_claims": ["expected abstain detail"],
            "metadata": {"accepted_claims": []},
        },
        "agent_results": [],
    }


def test_unsupported_x9_correct_abstain_can_pass():
    actual = response(
        "ABSTAIN", "ABSTAIN", "没有可靠证据确认该接口，本次不作答。",
        ["Figure Agent"], slots={"interface_name": "X9"},
        evidence=[{"evidence_id": "candidate-x1", "text": "X1 interface location"}],
    )
    assert evaluate_case(CASES["unsupported_x9"], actual)["passed"] is True


def test_unsupported_x9_fabricated_supported_location_fails():
    actual = response(
        "ABSTAIN", "ABSTAIN", "没有可靠证据，本次不作答。",
        ["Figure Agent"], slots={"interface_name": "X9"},
        supported=["X9 位于模块前部。"],
    )
    result = evaluate_case(CASES["unsupported_x9"], actual)
    assert result["passed"] is False
    assert any(item["name"] == "forbidden_supported_terms" for item in result["failures"])


def test_nonexistent_x4_correct_abstain_can_pass():
    actual = response(
        "ABSTAIN", "NEED_MORE_EVIDENCE", "没有证据确认该接口标号。",
        ["Figure Agent"], slots={"interface_name": "X4"},
    )
    assert evaluate_case(CASES["figure_nonexistent_x4"], actual)["passed"] is True


def test_unknown_order_number_correct_abstain_can_pass():
    actual = response(
        "ABSTAIN", "ABSTAIN", "没有证据确认该订货号对应的参数或端子定义。",
        ["Parameter Agent"], slots={"order_number": "6ES7999-9ZZ99-9ZZ9"},
    )
    assert evaluate_case(CASES["unsupported_unknown_order_number"], actual)["passed"] is True


def test_parsed_target_does_not_pass_from_original_query_alone():
    actual = response("ABSTAIN", "ABSTAIN", "没有证据，本次不作答。", ["Figure Agent"])
    actual["query_context"]["original_query"] = "CPU 1517-3 PN 的 X9 在哪里？"
    result = evaluate_case(CASES["unsupported_x9"], actual)
    assert result["passed"] is False
    assert any(item["name"] == "required_parsed_interfaces" for item in result["failures"])


def test_case_19_abstain_does_not_require_clarification_terms():
    actual = response(
        "ABSTAIN", "ABSTAIN", "没有直接 LED 证据，本次不作答。",
        ["Troubleshooting Agent"],
    )
    assert evaluate_case(CASES["troubleshooting_no_direct_led_evidence"], actual)["passed"] is True


def test_case_19_clarify_requires_model():
    valid = response(
        "CLARIFY", "NEED_CLARIFICATION", "请补充模块型号。", [],
        missing_slots=["module_model"],
    )
    assert evaluate_case(CASES["troubleshooting_no_direct_led_evidence"], valid)["passed"] is True
    valid["final_answer"] = "请补充更多信息。"
    assert evaluate_case(CASES["troubleshooting_no_direct_led_evidence"], valid)["passed"] is False


def test_case_19_answer_partial_uses_final_evidence_without_missing_slots():
    evidence = [{"evidence_id": "cpu-led", "module_model": "CPU 1517-3 PN/DP", "text": "RUN/STOP LED"}]
    actual = response(
        "ANSWER", "PARTIAL", "现有证据仅支持 CPU 1517-3 PN/DP 的 RUN/STOP LED。",
        ["Troubleshooting Agent"], evidence=evidence, supported=["CPU 1517-3 PN/DP RUN/STOP LED"],
    )
    actual["judge_decision"]["final_evidence_ids"] = ["cpu-led"]
    assert actual["missing_slots"] == []
    assert evaluate_case(CASES["troubleshooting_no_direct_led_evidence"], actual)["passed"] is True


def test_case_24_answer_partial_does_not_require_missing_slots():
    evidence = [{"evidence_id": "scope", "module_model": "S7-1500R/H", "text": "Scoped topology example"}]
    actual = response(
        "ANSWER", "PARTIAL", "该结论仅适用于已引用的作用域，不能泛化。",
        ["Topology Agent"], evidence=evidence, supported=["S7-1500R/H scoped topology"],
    )
    actual["judge_decision"]["final_evidence_ids"] = ["scope"]
    assert actual["missing_slots"] == []
    assert evaluate_case(CASES["topology_standard_vs_rh_scope"], actual)["passed"] is True


def test_case_24_clarify_requires_cpu_model():
    valid = response(
        "CLARIFY", "NEED_CLARIFICATION", "请补充 CPU 型号。", [],
        missing_slots=["module_model"],
    )
    assert evaluate_case(CASES["topology_standard_vs_rh_scope"], valid)["passed"] is True
    valid["missing_slots"] = []
    valid["query_context"]["missing_slots"] = []
    assert evaluate_case(CASES["topology_standard_vs_rh_scope"], valid)["passed"] is False
