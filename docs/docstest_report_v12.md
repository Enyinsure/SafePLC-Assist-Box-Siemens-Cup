# SafePLC-Assist Box V1.2 Evaluation Report

This document provides a readable summary of the V1.2 evaluation files included in the repository.

The original evaluation files are kept in JSON format for reproducibility, while this report is intended for online review and competition assessment.

---

## Evaluation Purpose

The V1.2 evaluation focuses on whether SafePLC-Assist Box can correctly handle industrial knowledge QA scenarios with safety awareness and evidence checking.

The evaluation covers:

- Question type classification
- Safety risk classification
- Action routing
- Clarification trigger behavior
- Evidence confidence estimation
- Answer-evidence consistency checking
- Evidence card generation

---

## Evaluation Files

| File | Purpose |
|---|---|
| `safeplc_assist_box/testset_v11_basic.json` | Basic V1.1 regression test set |
| `safeplc_assist_box/testset_v12_extended.json` | Extended V1.2 test set |
| `safeplc_assist_box/eval_report_v11.json` | V1.1 evaluation result |
| `safeplc_assist_box/eval_report_v12_extended.json` | V1.2 extended evaluation result |
| `safeplc_assist_box/run_v11_eval.py` | V1.1 evaluation script |
| `safeplc_assist_box/run_v12_extended_eval.py` | V1.2 evaluation script |

---

## Evaluation Dimensions

| Dimension | Description |
|---|---|
| Question classification | Whether the system classifies the user question correctly |
| Safety risk classification | Whether the system identifies potential industrial safety risks |
| Action routing | Whether the system routes the question to the proper handling path |
| Clarification trigger | Whether missing key information triggers clarification |
| Evidence confidence | Whether the retrieved evidence is judged as sufficient |
| Answer-evidence check | Whether key answer claims are supported by evidence |
| Evidence card generation | Whether structured evidence cards can be generated |

---

## What Is Being Tested

The evaluation mainly tests module-level behavior, including:

1. Whether a user question can be classified into the correct industrial question type.
2. Whether potentially unsafe PLC-related requests can be recognized.
3. Whether the system can trigger clarification when the query lacks key information.
4. Whether the system can estimate evidence confidence.
5. Whether the system can check answer-evidence consistency.
6. Whether the system can output structured evidence cards.

---

## Result Interpretation

The evaluation reports are stored as JSON files for reproducibility.

The current evaluation should be interpreted as a module-level validation of the SafePLC-Assist Box prototype.

It does not claim to cover all possible Siemens PLC usage scenarios or all real industrial site conditions.

---

## Current Strengths

The current V1.2 evaluation shows that the prototype has a complete evaluation pipeline covering:

- Input classification
- Safety risk handling
- Evidence confidence checking
- Answer-evidence consistency checking
- Structured output validation

This helps demonstrate that the project is not only a front-end demo, but also includes measurable safety-aware QA behavior.

---

## Current Limitations

The current evaluation mainly focuses on controlled test cases and rule-based safety behavior.

Future evaluation should include:

- Larger real-user query sets
- More Siemens device families
- Retrieval hit rate analysis
- Human expert review
- More visual evidence cases
- Long-term user testing
- More failure case analysis

---

## Summary

The V1.2 evaluation files provide an initial validation of the SafePLC-Assist Box prototype.

They support the following project claims:

- The system has safety-aware question handling.
- The system includes evidence confidence estimation.
- The system includes answer-evidence consistency checking.
- The system can generate structured evidence cards.
- The system has a measurable evaluation process.

Further evaluation will be expanded after more real-user questions, visual evidence cases, and physical prototype demonstrations are added.
