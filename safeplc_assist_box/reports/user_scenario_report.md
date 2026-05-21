# SafePLC-Assist Box User Scenario Report

This document describes the main user scenarios of the SafePLC-Assist Box prototype.

The purpose of this report is to show how the system can be used as a safety-aware industrial knowledge QA terminal, instead of a simple search engine or generic chatbot.

---

## Target Users

SafePLC-Assist Box is designed for the following user groups:

| User Type | Scenario |
|---|---|
| Student / learner | Learning Siemens PLC-related industrial knowledge |
| Competition reviewer | Reviewing the system capability and safety boundary |
| Industrial training user | Checking manual-based knowledge in a training environment |
| Maintenance assistant user | Looking up parameter, module, or safety-related information |
| Instructor / demonstrator | Demonstrating evidence-based industrial QA workflow |

The system is not designed to replace certified engineers or official Siemens documentation.

---

## Scenario 1: Industrial Manual Knowledge Query

### User Goal

The user wants to ask a knowledge question related to Siemens S7-1500 / ET 200MP manuals.

### Example Question

```text
What is the meaning of a specific S7-1500 module parameter?
```

### System Behavior

The system should:

1. Accept the question through the Streamlit product interface.
2. Retrieve or reuse relevant industrial manual evidence.
3. Generate an answer based on the available evidence.
4. Display evidence confidence.
5. Display structured evidence cards.
6. Provide traceable source information.

### Expected Value

The user can quickly understand industrial manual information without manually searching through a long PDF.

---

## Scenario 2: Missing Context or Ambiguous Question

### User Goal

The user asks a question that lacks key information, such as module model, parameter name, or operating context.

### Example Question

```text
How should I configure this module?
```

### System Behavior

The system should:

1. Detect that the question lacks key context.
2. Trigger clarification logic or indicate that more information is needed.
3. Avoid giving overconfident answers.
4. Recommend checking the exact module model, manual section, or parameter context.

### Expected Value

The system avoids producing unsupported or misleading answers when the user question is incomplete.

---

## Scenario 3: Safety-related Industrial Question

### User Goal

The user asks a question related to safety, maintenance, or industrial operation.

### Example Question

```text
What should I pay attention to before modifying this PLC-related configuration?
```

### System Behavior

The system should:

1. Identify the safety-related nature of the question.
2. Emphasize that the system is offline and read-only.
3. Avoid giving executable control instructions.
4. Recommend official manuals, site procedures, and qualified engineering review.
5. Provide evidence-based explanation when available.

### Expected Value

The system provides safety reminders and does not behave like an uncontrolled automation assistant.

---

## Scenario 4: High-risk PLC Operation Request

### User Goal

The user asks for an instruction that may involve real PLC control, write, download, start, stop, or unsafe operation.

### Example Question

```text
How can I directly write this value into the PLC and force the output?
```

### System Behavior

The system should:

1. Detect the potentially high-risk nature of the request.
2. Avoid providing executable PLC control instructions.
3. Clearly state the technical boundary.
4. Remind the user that the system does not connect to real PLC devices.
5. Redirect the user to official documentation and qualified personnel.

### Expected Value

The system reduces the risk of unsafe industrial operation guidance.

---

## Scenario 5: Evidence Confidence Review

### User Goal

The user wants to know whether the answer is well supported by evidence.

### System Behavior

The system should display Evidence Confidence, such as:

- High
- Medium
- Low
- Conflict

The system should also explain why the confidence level is assigned.

### Expected Value

The user can distinguish between strongly supported answers and answers that require review.

---

## Scenario 6: Answer-Evidence Consistency Check

### User Goal

The user wants to verify whether the answer is supported by the evidence.

### System Behavior

The system should provide an Answer-Evidence Check result, such as:

- PASS
- REVIEW
- FAIL

If claims are not fully supported, the system should indicate that review is needed.

### Expected Value

The answer becomes more auditable and less like a black-box language model response.

---

## Scenario 7: Visual Evidence Rendering

### User Goal

The user wants to see the original visual evidence, such as a manual page screenshot or visual candidate page.

### Example Evidence Card

```text
page: 641
figure_id: page_0641_visual
```

### System Behavior

The system should:

1. Parse the page number or `figure_id`.
2. Search for the corresponding local visual evidence image.
3. Render the image in the V1.1 evidence card panel if the asset exists locally.

Expected image example:

```text
page_0641.jpg
```

### Expected Value

The user can review not only text snippets, but also the original visual evidence.

This makes the system different from a plain text search engine.

Full visual evidence assets are not included in the public repository for repository size and copyright reasons.

---

## Scenario 8: Competition Demonstration

### User Goal

A reviewer or audience member wants to understand the system quickly during competition review.

### System Behavior

The project should present:

1. Clear product positioning.
2. Safety boundary.
3. Core software modules.
4. Evidence confidence and answer-evidence checking.
5. Visual evidence rendering capability.
6. Hardware prototype design.
7. Evaluation files and reports.

### Expected Value

The project can be reviewed as a complete competition prototype rather than a loose code repository.

---

## Scenario 9: Physical Terminal Demonstration

### User Goal

The user interacts with the system through a physical terminal prototype.

### Current Design

The project adopts Scheme B:

```text
External computing host + productized physical terminal shell
```

The laptop acts as the external computing host, while the physical terminal shell provides:

- Display area
- Status indicators
- Query / Demo / Export Log buttons
- Product nameplate
- Offline / read-only labels
- PLC control disabled label

### Expected Value

The physical terminal gives the project a product form and helps communicate the safety boundary.

The physical terminal shell is in progress. Physical prototype photos will be added after the physical prototype is completed.

---

## Scenario-to-Module Mapping

| Scenario | Related Module / Document |
|---|---|
| Industrial manual query | `app_assist_box.py` |
| Missing context handling | `question_classifier_v11.py` |
| Safety-related question | `safety_risk_guard_v11.py` |
| Evidence confidence review | `evidence_confidence_v11.py` |
| Answer-evidence consistency check | `answer_evidence_checker_v11.py` |
| Evidence card display | `evidence_card_formatter.py` |
| Visual evidence rendering | `app_assist_box.py` |
| Evaluation | `run_v12_extended_eval.py`, `eval_report_v12_extended.json` |
| Hardware terminal design | `hardware/` |

---

## Current Scenario Coverage

| Scenario | Current Status |
|---|---|
| Industrial manual knowledge query | Supported |
| Missing context handling | Supported at module level |
| Safety-related question handling | Supported |
| High-risk operation request handling | Supported |
| Evidence Confidence | Supported |
| Answer-Evidence Check | Supported |
| Structured evidence cards | Supported |
| Visual evidence rendering | Supported in local demo environment |
| Physical terminal demonstration | In progress |
| Final video demonstration | Planned for final submission stage |

---

## Limitations

Current limitations include:

- Full Siemens manual assets are not included in the public repository.
- Full OCR outputs and vector databases are not included in the public repository.
- Full visual evidence image assets are not included in the public repository.
- Model weights, tokens, environment files, and compressed release packages are not included in the public repository.
- The physical prototype is still in progress.
- Final photos and demo video will be added during the final submission stage.
- The current evaluation focuses on controlled test cases and module-level behavior.

---

## Summary

SafePLC-Assist Box is designed around reviewable industrial QA scenarios.

The system is intended to support:

- Knowledge lookup
- Safety-aware response behavior
- Evidence confidence review
- Answer-evidence consistency checking
- Structured evidence cards
- Visual evidence rendering
- Productized physical terminal presentation

The current prototype is suitable for software-level and documentation-level review, and will be further strengthened with final physical prototype materials and demo media.
