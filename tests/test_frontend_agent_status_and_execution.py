from __future__ import annotations

from safeplc_assist_box.frontend.components.task_agent_panel import _execution_stages
from safeplc_assist_box.frontend.result_normalizer import normalize_response


def _status_payload(status: str) -> dict:
    return {
        "query": "执行状态检查",
        "query_context": {
            "question_type": "WIRING",
            "risk_level": "SAFE",
            "risk_decision": "ALLOW",
            "slots": {},
            "subquestions": [
                {
                    "subquestion_id": "sq_1",
                    "text": "执行专业任务",
                    "objective": "检查任务状态",
                    "expected_agents": ["Status Agent"],
                }
            ],
        },
        "agent_plan": {
            "selected_agents": ["Status Agent"],
            "execution_order": ["Status Agent"],
            "execution_mode": "single",
            "task_assignments": {},
        },
        "agent_results": [
            {
                "agent_name": "Status Agent",
                "status": status,
                "error": "backend failed" if status == "FAILED" else "",
                "claims": [],
                "evidence_ids": [],
            }
        ],
        "evidence_pool": {"evidences": []},
        "judge_decision": {"verdict": "NEED_MORE_EVIDENCE", "coverage": {}},
    }


def test_failed_agent_marks_task_failed() -> None:
    result = normalize_response(_status_payload("FAILED"))

    assert result["task_plan"][0]["status"] == "failed"
    assert result["selected_agents"][0]["status"] == "failed"
    assert result["selected_agents"][0]["error"] == "backend failed"


def test_abstain_agent_marks_task_skipped() -> None:
    result = normalize_response(_status_payload("ABSTAIN"))

    assert result["task_plan"][0]["status"] == "skipped"
    assert result["selected_agents"][0]["status"] == "skipped"


def test_refusal_agent_marks_safety_task_completed() -> None:
    result = normalize_response(_status_payload("REFUSE"))

    assert result["task_plan"][0]["status"] == "completed"
    assert result["selected_agents"][0]["status"] == "completed"


def test_parallel_groups_are_preserved_as_execution_stages() -> None:
    payload = _status_payload("ANSWERED")
    payload["agent_plan"] = {
        "selected_agents": ["Figure Agent", "Wiring Agent", "Safety Boundary Agent"],
        "execution_order": ["Figure Agent", "Wiring Agent", "Safety Boundary Agent"],
        "execution_mode": "parallel",
        "parallel_groups": [["Figure Agent", "Wiring Agent"], ["Safety Boundary Agent"]],
        "task_assignments": {},
    }
    payload["agent_results"] = [
        {"agent_name": name, "status": "ANSWERED", "claims": [], "evidence_ids": []}
        for name in payload["agent_plan"]["selected_agents"]
    ]

    result = normalize_response(payload)
    stages = _execution_stages(
        result["agent_execution"],
        [agent["name"] for agent in result["selected_agents"]],
    )

    assert result["agent_execution"]["mode"] == "parallel"
    assert stages == [["Figure Agent", "Wiring Agent"], ["Safety Boundary Agent"]]
