from benchmark.full_core_30.acceptance_rules import evaluate_case, load_cases


CASES = {item["case_id"]: item for item in load_cases()}


def base_response(action, verdict, answer, evidence=None, supported=None, selected_agents=None, missing_slots=None):
    evidences = evidence or []
    final_ids = [item["evidence_id"] for item in evidences]
    return {
        "action": action,
        "verdict": verdict,
        "selected_agents": selected_agents if selected_agents is not None else (
            ["Wiring Agent"] if "wiring" in answer.lower() or "模块型号" in answer else ["Troubleshooting Agent"]
        ),
        "final_answer": answer,
        "missing_slots": missing_slots or [],
        "unsupported_claims": ["allowed diagnostic detail"],
        "evidence_pool": {"evidences": evidences},
        "judge_decision": {
            "verdict": verdict, "final_evidence_ids": final_ids,
            "supported_claims": supported or [], "unsupported_claims": ["allowed diagnostic detail"],
            "metadata": {"accepted_claims": []},
        },
        "agent_results": [],
    }


def test_case_15_answer_requires_tm_npu_evidence_scope():
    response = base_response(
        "ANSWER", "PARTIAL", "wiring 结论仅限 TM NPU。",
        [{"evidence_id": "tm", "module_model": "TM NPU", "text": "Connect the terminal."}],
        ["TM NPU terminal requirement"],
    )
    assert evaluate_case(CASES["wiring_specific_module_not_generalized"], response)["passed"] is True
    response["evidence_pool"]["evidences"][0]["module_model"] = "S7-1500 general"
    assert evaluate_case(CASES["wiring_specific_module_not_generalized"], response)["passed"] is False


def test_case_15_clarification_needs_model_or_order_number_but_no_evidence():
    response = base_response(
        "CLARIFY", "NEED_CLARIFICATION", "请提供具体模块型号或订货号。", selected_agents=[]
    )
    assert response["evidence_pool"]["evidences"] == []
    assert response["selected_agents"] == []
    assert evaluate_case(CASES["wiring_specific_module_not_generalized"], response)["passed"] is True


def test_case_18_answer_requires_x2_supported_scope():
    response = base_response(
        "ANSWER", "PARTIAL", "X2 可确认端口 X2 P1。",
        [{"evidence_id": "x2", "module_model": "CPU 1517-3 PN/DP", "text": "X2 P1 LINK RX/TX LED"}],
        ["X2 P1 LINK RX/TX LED"],
    )
    assert evaluate_case(CASES["troubleshooting_x2_scope"], response)["passed"] is True


def test_case_18_abstain_does_not_require_x2_in_answer():
    response = base_response("ABSTAIN", "ABSTAIN", "没有直接端口 LED 证据，本次不作答。")
    assert evaluate_case(CASES["troubleshooting_x2_scope"], response)["passed"] is True
