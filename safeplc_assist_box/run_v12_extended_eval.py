#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
from pathlib import Path

from question_classifier_v11 import classify_question
from safety_risk_guard_v11 import assess_industrial_risk


TESTSET_PATH = "testset_v12_extended.json"
REPORT_PATH = "eval_report_v12_extended.json"


def load_cases(path: str = TESTSET_PATH):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def evaluate(cases):
    total = len(cases)

    qtype_ok = 0
    action_ok = 0
    risk_ok = 0

    clarify_total = 0
    clarify_ok = 0

    details = []

    for c in cases:
        q = c["question"]
        ctx = c.get("context", "")

        cls = classify_question(q, ctx)
        risk = assess_industrial_risk(q, ctx)

        pred_qtype = cls["question_type"]
        pred_action = cls["action"]
        pred_risk = risk["risk_level"]

        exp_qtype = c["expected_question_type"]
        exp_action = c["expected_action"]
        exp_risk = c["expected_risk_level"]

        q_ok = pred_qtype == exp_qtype
        a_ok = pred_action == exp_action
        r_ok = pred_risk == exp_risk

        qtype_ok += int(q_ok)
        action_ok += int(a_ok)
        risk_ok += int(r_ok)

        if exp_action == "CLARIFY":
            clarify_total += 1
            clarify_ok += int(pred_action == "CLARIFY")

        details.append({
            "id": c["id"],
            "question": q,
            "context": ctx,
            "pred_qtype": pred_qtype,
            "exp_qtype": exp_qtype,
            "qtype_ok": q_ok,
            "pred_action": pred_action,
            "exp_action": exp_action,
            "action_ok": a_ok,
            "pred_risk": pred_risk,
            "exp_risk": exp_risk,
            "risk_ok": r_ok,
            "classifier_raw": cls,
            "risk_raw": risk,
            "note": c.get("notes", ""),
        })

    result = {
        "project": "SafePLC-Assist Box",
        "version": "V1.2 extended evaluation",
        "testset": TESTSET_PATH,
        "total": total,
        "question_type_accuracy": round(qtype_ok / total, 4) if total else 0,
        "action_route_accuracy": round(action_ok / total, 4) if total else 0,
        "risk_level_accuracy": round(risk_ok / total, 4) if total else 0,
        "clarify_trigger_accuracy": round(clarify_ok / clarify_total, 4) if clarify_total else None,
        "details": details,
    }

    return result


def main():
    cases = load_cases()
    result = evaluate(cases)

    Path(REPORT_PATH).write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("SafePLC-Assist Box V1.2 Extended Eval")
    print("=" * 60)
    print("Testset:", result["testset"])
    print("Total cases:", result["total"])
    print("Question type accuracy:", result["question_type_accuracy"])
    print("Action route accuracy:", result["action_route_accuracy"])
    print("Risk level accuracy:", result["risk_level_accuracy"])
    print("Clarify trigger accuracy:", result["clarify_trigger_accuracy"])
    print("Report saved to", REPORT_PATH)

    failed = [
        x for x in result["details"]
        if not (x["qtype_ok"] and x["action_ok"] and x["risk_ok"])
    ]

    if failed:
        print()
        print("Failed / review cases:")
        for x in failed:
            print(
                f"- {x['id']} | "
                f"qtype {x['pred_qtype']} vs {x['exp_qtype']} | "
                f"action {x['pred_action']} vs {x['exp_action']} | "
                f"risk {x['pred_risk']} vs {x['exp_risk']}"
            )
    else:
        print()
        print("All rule-based checks passed.")


if __name__ == "__main__":
    main()
