# Online Review Guide

This document provides a recommended review path for the SafePLC-Assist Box Siemens Cup project.

## Recommended Review Order

1. Read the project overview in `README.md`.
2. Check the core implementation in `safeplc_assist_box/`.
3. Review the evaluation summary in `docs/test_report_v12.md`.
4. Check the hardware prototype design in `hardware/`.
5. Check the technical boundary in `PROJECT_FINAL_STATUS_SIEMENS_CUP_V12.txt`.
6. Check the Chinese documentation in `docs/中文说明.md`.

## Key Review Points

| Review Point | Location |
|---|---|
| Product interface | `safeplc_assist_box/app_assist_box.py` |
| Question classification | `safeplc_assist_box/question_classifier_v11.py` |
| Safety risk guard | `safeplc_assist_box/safety_risk_guard_v11.py` |
| Evidence confidence | `safeplc_assist_box/evidence_confidence_v11.py` |
| Answer-evidence checking | `safeplc_assist_box/answer_evidence_checker_v11.py` |
| Visual evidence rendering | `safeplc_assist_box/app_assist_box.py` |
| V1.2 evaluation files | `safeplc_assist_box/testset_v12_extended.json` and `safeplc_assist_box/eval_report_v12_extended.json` |
| Hardware prototype plan | `hardware/` |
| Chinese documentation | `docs/中文说明.md` |

## Current Repository Status

| Item | Status |
|---|---|
| Core software prototype | Completed |
| Streamlit product interface | Completed |
| Safety-aware QA modules | Completed |
| Evidence Confidence / Evidence Check | Completed |
| Visual evidence rendering logic | Completed |
| Evaluation files | Completed |
| Hardware prototype design documents | In progress |
| Physical box photos | To be added |
| Demo video | To be added |

## Current Limitations

The current public repository does not include:

- Full Siemens manual PDFs
- Full OCR outputs
- Full vector databases
- Full visual evidence image assets
- Physical prototype photos
- Final demo video

These assets are either excluded for repository size and copyright reasons or planned for later competition submission updates.

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
