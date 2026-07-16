from __future__ import annotations

import json
from pathlib import Path

from safeplc_assist_box.frontend.result_normalizer import normalize_response


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_normalizer_maps_real_sample_response_to_frontend_schema() -> None:
    payload = json.loads((PROJECT_ROOT / "reports" / "sample_acceptance_x1.json").read_text(encoding="utf-8"))

    result = normalize_response(payload)

    assert result["query"] == payload["query"]
    assert [agent["name"] for agent in result["selected_agents"]] == ["Figure Agent", "Topology Agent"]
    assert result["evidence_stats"]["total"] == 2
    assert result["answer"]["claims"]
    assert result["answer"]["claims"][0]["evidence_ids"] == ["E1"]
    assert result["judge_result"]["verdict"] == "PASS"
    assert result["judge_result"]["closure_score_source"] == "frontend_visible_checks"
    assert result["raw_response"]["final_answer"] == payload["final_answer"]


def test_normalizer_preserves_malformed_raw_response_without_raising() -> None:
    result = normalize_response(["unexpected", "response"])

    assert result["request_id"] == "normalization_failed"
    assert result["compatibility_warnings"]
    assert result["raw_response"] == ["unexpected", "response"]


def test_missing_safety_fields_are_not_presented_as_passed() -> None:
    result = normalize_response({"query": "测试", "judge_decision": {"verdict": "NEED_MORE_EVIDENCE"}})

    assert result["judge_result"]["checks"]["safety"] == {
        "status": "not_checked",
        "score": None,
        "detail": "未返回结构化安全检查字段",
    }


def test_evidence_safety_check_is_preserved_when_backend_provides_it() -> None:
    result = normalize_response(
        {
            "query": "测试",
            "evidence_pool": {
                "evidences": [
                    {
                        "evidence_id": "ev_1",
                        "text": "直接证据",
                        "metadata": {"safety_checked": True},
                    }
                ]
            },
            "judge_decision": {"final_evidence_ids": ["ev_1"]},
        }
    )

    assert result["evidence_pool"][0]["safety_checked"] is True
