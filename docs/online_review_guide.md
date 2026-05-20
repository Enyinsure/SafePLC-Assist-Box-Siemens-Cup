# Online Review Guide

This document provides a recommended review path for the SafePLC-Assist Box Siemens Cup project.

It is intended to help online reviewers quickly understand the repository structure, core implementation, evaluation materials, hardware prototype design, and current project status.

---

## Recommended Review Order

1. Read the project overview in `README.md`.
2. Check the core implementation in `safeplc_assist_box/`.
3. Review the evaluation summary in `docs/test_report_v12.md`.
4. Check the hardware prototype design in `hardware/`.
5. Check the technical boundary in `PROJECT_FINAL_STATUS_SIEMENS_CUP_V12.txt`.
6. Check the Chinese documentation in `docs/中文说明.md`.

---

## Key Review Points

| Review Point | Location |
|---|---|
| Product interface | `safeplc_assist_box/app_assist_box.py` |
| Question classification | `safeplc_assist_box/question_classifier_v11.py` |
| Safety risk guard | `safeplc_assist_box/safety_risk_guard_v11.py` |
| Evidence confidence | `safeplc_assist_box/evidence_confidence_v11.py` |
| Answer-evidence checking | `safeplc_assist_box/answer_evidence_checker_v11.py` |
| Evidence card formatting | `safeplc_assist_box/evidence_card_formatter.py` |
| Visual evidence rendering | `safeplc_assist_box/app_assist_box.py` |
| V1.2 evaluation files | `safeplc_assist_box/testset_v12_extended.json` and `safeplc_assist_box/eval_report_v12_extended.json` |
| Hardware prototype plan | `hardware/` |
| Chinese documentation | `docs/中文说明.md` |

---

## Current Repository Status

| Item | Status |
|---|---|
| Core software prototype | Completed |
| Streamlit product interface | Completed |
| Safety-aware QA modules | Completed |
| Evidence Confidence / Evidence Check | Completed |
| Structured evidence card logic | Completed |
| Visual evidence rendering logic | Completed |
| Evaluation files | Completed |
| Hardware prototype design documents | In progress |
| Physical prototype materials | In progress |
| Final demo media | Planned for final submission |

---

## Project Highlights for Reviewers

| Challenge | SafePLC-Assist Box Solution |
|---|---|
| Industrial manuals are large and difficult to search | Manual-oriented industrial knowledge retrieval |
| User questions may lack module, model, or parameter context | Question classification and clarification logic |
| LLM answers may contain unsupported claims | Evidence Confidence and Answer-Evidence Check |
| PLC-related questions may involve unsafe operations | Safety Risk Guard and offline/read-only boundary |
| Plain text retrieval lacks traceability | Structured evidence cards and visual evidence rendering |
| Pure software form may look like a demo page | Physical terminal prototype design |

---

## Suggested Review Summary

SafePLC-Assist Box is a safety-aware industrial knowledge QA terminal prototype.

The project combines:

- Industrial manual retrieval
- Safety risk classification
- Question routing
- Evidence confidence estimation
- Answer-evidence consistency checking
- Structured evidence cards
- Visual evidence rendering
- Offline / read-only boundary
- Physical terminal prototype design

The current repository focuses on software implementation, evaluation files, technical boundary, and hardware design documentation.

---

## Repository Boundary

The public repository does not include:

- Full Siemens manual PDFs
- Full OCR outputs
- Full vector databases
- Full visual evidence image assets
- Local model weights
- Large compressed release packages
- Private keys, tokens, or environment files

These assets are excluded for repository size, copyright, and safety boundary reasons.

The full local demo environment can render visual evidence images when the corresponding local visual evidence assets are available.

---

## Current Limitations

The current repository should be interpreted as a competition-oriented prototype repository rather than a full industrial deployment package.

Current limitations include:

- The public repository does not include full manual assets.
- The public repository does not include full visual evidence assets.
- The current evaluation mainly focuses on controlled test cases and module-level behavior.
- Physical prototype materials are still in progress.
- Final demo media will be prepared during the final submission stage.

---

## Recommended Reviewer Focus

For online review, the most important parts are:

1. Whether the project has a clear industrial safety boundary.
2. Whether the code contains more than a simple search or RAG interface.
3. Whether the system includes evidence confidence and answer-evidence checking.
4. Whether the project provides structured evidence cards and visual evidence rendering logic.
5. Whether the hardware prototype design supports the productized terminal concept.
6. Whether the evaluation files demonstrate measurable module-level behavior.

---

## Final Note

SafePLC-Assist Box is designed as an offline, read-only industrial knowledge QA and evidence review prototype.

It does not connect to real PLC devices, does not execute PLC control actions, and does not replace official Siemens manuals or certified industrial engineers.
