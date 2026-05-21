# SafePLC-Assist Box Demo Video Script

This script is for the planned final demo video. The final video has not been added yet and should be recorded after the physical prototype is completed.

## Suggested Duration

4 to 6 minutes.

## 1. Opening

Introduce SafePLC-Assist Box as a safety-aware industrial knowledge QA terminal prototype for Siemens Cup.

Key message:

- Industrial manuals are large and technical.
- Users need fast knowledge lookup, traceable evidence, and safety-aware behavior.
- The prototype is offline, read-only, and does not control PLC devices.

## 2. Pain Points

Explain the main problems:

- Manual search is slow for long Siemens PLC-related documents.
- User questions may omit module, model, or parameter context.
- Generic language models may produce unsupported claims.
- PLC-related questions may involve unsafe write, download, start, stop, or control actions.
- Text-only answers are difficult to audit.

## 3. Product Overview

Show the SafePLC-Assist Box Streamlit interface.

Mention the main product capabilities:

- Question classification
- Safety Risk Guard
- Evidence Confidence
- Answer-Evidence Check
- Structured evidence cards
- Visual evidence rendering in the local demo environment
- Physical terminal prototype design

## 4. Missing Context Demo

Example input:

```text
What is the permitted power supply voltage range for this module?
```

Expected behavior:

- The system should avoid giving an overconfident answer.
- It should request or highlight missing module context.
- The result should show that ambiguous industrial questions need review.

## 5. Evidence-based Parameter Query

Example context:

```text
PS 60W 24/48/60VDC HF
```

Expected behavior:

- The system returns a manual-based answer.
- Evidence Confidence is displayed.
- Structured evidence cards show page, source, title, module, parameter, and snippet fields when available.
- Answer-Evidence Check indicates whether the answer is aligned with the evidence.

## 6. Visual Evidence Rendering

Example evidence fields:

```text
page: 641
figure_id: page_0641_visual
```

Expected behavior:

- When the corresponding local visual evidence asset exists, the UI renders the visual evidence image in the evidence card panel.
- The public repository does not include the full visual evidence assets for repository size and copyright reasons.

## 7. High-risk Request Demo

Example input:

```text
How can I bypass a safety circuit so the equipment keeps running?
```

Expected behavior:

- The system identifies the request as HIGH_RISK.
- It refuses to provide executable unsafe steps.
- It reminds the user to follow official manuals, site procedures, and qualified engineering review.
- It reinforces that the prototype is offline, read-only, and not connected to real PLCs.

## 8. Physical Terminal Prototype

Show the in-progress physical terminal shell design or final shell after completion.

Highlight:

- Product nameplate
- SAFE / CAUTION / HIGH_RISK / CHECK indicators
- Query / Demo / Export Log buttons
- OFFLINE / READ-ONLY label
- PLC CONTROL DISABLED label
- KNOWLEDGE QA ONLY label

Do not present the physical shell as finished until the final build is complete.

## 9. Repository Boundary

State clearly:

- Full Siemens manuals are not included in the public repository.
- Full OCR outputs are not included.
- Vector databases are not included.
- Model weights are not included.
- Full visual evidence assets are not included.
- Tokens, environment files, and compressed release packages are not included.

These assets are excluded for repository size, copyright, privacy, and safety boundary reasons.

## 10. Closing

Summarize the value of SafePLC-Assist Box:

- Safety-aware industrial QA
- Evidence Confidence
- Answer-Evidence Check
- Structured evidence cards
- Visual evidence rendering
- Offline/read-only boundary
- Productized physical terminal prototype design

End by noting that physical prototype photos and the final demo video will be added after the physical prototype is completed.
