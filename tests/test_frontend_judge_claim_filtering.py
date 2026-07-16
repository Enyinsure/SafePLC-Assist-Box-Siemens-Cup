from __future__ import annotations

from safeplc_assist_box.frontend.result_normalizer import normalize_response
from safeplc_assist_box.frontend.work_orders import build_editable_work_order


def _claim_payload(final_ids: list[str], accepted_agents: list[str]) -> dict:
    return {
        "query": "检查接线结论",
        "mode": "SAMPLE",
        "query_context": {
            "question_type": "WIRING",
            "risk_level": "SAFE",
            "risk_decision": "ALLOW",
            "slots": {},
        },
        "agent_plan": {
            "selected_agents": ["Accepted Agent", "Rejected Agent"],
            "execution_order": ["Accepted Agent", "Rejected Agent"],
            "execution_mode": "sequential",
            "task_assignments": {},
        },
        "agent_results": [
            {
                "agent_name": "Accepted Agent",
                "status": "ANSWERED",
                "evidence_ids": ["ev_accepted"],
                "claims": [
                    {
                        "claim_id": "claim_accepted",
                        "claim_text": "仅保留该接线检查",
                        "claim_type": "instruction",
                        "evidence_ids": ["ev_accepted"],
                        "direct_support": True,
                    }
                ],
            },
            {
                "agent_name": "Rejected Agent",
                "status": "ANSWERED",
                "evidence_ids": ["ev_rejected"],
                "claims": [
                    {
                        "claim_id": "claim_rejected",
                        "claim_text": "不得进入回答和工单",
                        "claim_type": "instruction",
                        "evidence_ids": ["ev_rejected"],
                        "direct_support": True,
                    }
                ],
            },
        ],
        "evidence_pool": {
            "evidences": [
                {
                    "evidence_id": "ev_accepted",
                    "text": "接受证据",
                    "manual_title": "Accepted Manual",
                    "page": 10,
                },
                {
                    "evidence_id": "ev_rejected",
                    "text": "拒绝证据",
                    "manual_title": "Rejected Manual",
                    "page": 20,
                },
            ]
        },
        "judge_decision": {
            "verdict": "PASS" if final_ids else "NEED_MORE_EVIDENCE",
            "accepted_agent_outputs": accepted_agents,
            "rejected_agent_outputs": ["Rejected Agent"],
            "final_evidence_ids": final_ids,
        },
        "action": "ANSWER" if final_ids else "ABSTAIN",
        "final_answer": "结构化结果",
    }


def test_empty_final_evidence_does_not_accept_all_claims() -> None:
    result = normalize_response(_claim_payload([], ["Accepted Agent"]))

    assert result["answer"]["claims"] == []
    assert result["answer"]["evidence_ids"] == []


def test_rejected_agent_claim_does_not_enter_answer() -> None:
    result = normalize_response(_claim_payload(["ev_accepted"], ["Accepted Agent"]))

    assert [claim["text"] for claim in result["answer"]["claims"]] == ["仅保留该接线检查"]


def test_only_final_evidence_claims_enter_work_order() -> None:
    result = normalize_response(_claim_payload(["ev_accepted"], ["Accepted Agent"]))

    work_order = build_editable_work_order(result)

    assert work_order["inspection_steps"] == ["仅保留该接线检查 [E1]"]
    assert len(work_order["evidence_sources"]) == 1
    assert "Accepted Manual" in work_order["evidence_sources"][0]
    assert "Rejected Manual" not in "\n".join(work_order["evidence_sources"])
    assert "不得进入回答和工单" not in "\n".join(work_order["inspection_steps"])


def test_safety_refusal_does_not_create_normal_operation_steps() -> None:
    payload = _claim_payload([], [])
    payload["action"] = "REFUSE"
    payload["operation_risk_level"] = "HIGH_RISK"
    payload["work_order"] = {"suggested_checks": ["危险操作步骤"]}

    work_order = build_editable_work_order(normalize_response(payload))

    assert work_order["inspection_steps"] == []
    assert work_order["required_tools"] == []
