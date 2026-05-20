# SafePLC-Assist Box Appearance Design

This document describes the planned appearance design of the SafePLC-Assist Box physical terminal prototype.

The purpose of the appearance design is to make the project look like a productized industrial knowledge QA terminal rather than a pure software demo.

---

## 1. Design Concept

SafePLC-Assist Box is designed as an offline, read-only industrial knowledge QA terminal.

The appearance should communicate three key ideas:

```text
Industrial
Safe
Evidence-based
```

The physical terminal should clearly show that the system is:

- A knowledge assistance terminal
- An evidence review terminal
- Offline and read-only
- Not a PLC controller
- Not connected to real PLC devices

---

## 2. Overall Appearance Direction

The appearance design follows an industrial terminal style.

The terminal should look simple, stable, and easy to understand.

Recommended design characteristics:

| Design Aspect | Direction |
|---|---|
| Overall style | Industrial terminal / engineering equipment style |
| Main color | Neutral industrial color, such as white, gray, black, or blue-gray |
| Front panel | Clear display area with status indicators and labels |
| Interaction | Simple Query / Demo / Export Log buttons |
| Safety labels | Highly visible offline and no-control labels |
| Product identity | Clear SafePLC-Assist Box nameplate |

---

## 3. Product Nameplate

The front panel should include a product nameplate.

Recommended text:

```text
SafePLC-Assist Box V1.2
Industrial Knowledge QA Terminal
```

The nameplate should be placed at the top of the front panel so that reviewers can immediately recognize the product identity.

---

## 4. Display Area

The display area is the main visual focus of the terminal.

It should show the Streamlit product interface, including:

- Question input area
- Safety boundary panel
- Evidence Confidence panel
- Answer-Evidence Check panel
- V1.1 evidence card panel
- Visual evidence rendering area

The display area should be large enough for reviewers to see the evidence workflow clearly.

---

## 5. Status Indicators

The front panel should include four status indicators:

```text
SAFE
CAUTION
HIGH_RISK
CHECK
```

Their meanings are:

| Indicator | Meaning |
|---|---|
| SAFE | Low-risk knowledge query |
| CAUTION | Review is needed or context is incomplete |
| HIGH_RISK | Potentially unsafe industrial operation request |
| CHECK | Evidence checking has been completed |

These indicators help connect the software safety state with the physical terminal appearance.

---

## 6. Buttons

The terminal can include three product interaction buttons:

```text
Query
Demo
Export Log
```

Their meanings are:

| Button | Meaning |
|---|---|
| Query | Submit or represent a user question |
| Demo | Run or represent a demo case |
| Export Log | Export or represent interaction records |

These buttons are product interaction metaphors. They help the prototype look like a terminal device, even though the current software interaction is mainly implemented in Streamlit.

---

## 7. Safety Boundary Labels

The front panel should clearly display:

```text
OFFLINE / READ-ONLY
PLC CONTROL DISABLED
KNOWLEDGE QA ONLY
```

These labels are important because the project involves PLC-related industrial knowledge.

The appearance must avoid giving reviewers the impression that the prototype can control real PLC devices.

---

## 8. Suggested Front Panel Structure

```text
┌──────────────────────────────────────────────────────┐
│ SafePLC-Assist Box V1.2                              │
│ Industrial Knowledge QA Terminal                     │
│                                                      │
│ ┌──────────────────────────────────────────────────┐ │
│ │              Streamlit UI Display                 │ │
│ │                                                  │ │
│ │  Question Input                                  │ │
│ │  Safety Boundary Panel                           │ │
│ │  Evidence Confidence / Evidence Check            │ │
│ │  Visual Evidence Card Panel                      │ │
│ └──────────────────────────────────────────────────┘ │
│                                                      │
│ [SAFE]     [CAUTION]     [HIGH_RISK]     [CHECK]     │
│                                                      │
│ [Query]              [Demo]              [Export Log]│
│                                                      │
│ OFFLINE / READ-ONLY                                  │
│ PLC CONTROL DISABLED                                 │
│ KNOWLEDGE QA ONLY                                    │
└──────────────────────────────────────────────────────┘
```

---

## 9. Visual Communication Goals

The appearance should help reviewers understand the project quickly.

The terminal should communicate:

| Message | How It Is Communicated |
|---|---|
| This is an industrial QA terminal | Product nameplate and terminal shell |
| The system is safety-aware | SAFE / CAUTION / HIGH_RISK indicators |
| The system has evidence review | CHECK indicator and evidence panel |
| The system is not a PLC controller | PLC CONTROL DISABLED label |
| The system is offline and read-only | OFFLINE / READ-ONLY label |
| The system has product form | Physical shell, buttons, indicators, and layout |

---

## 10. Relationship with Software UI

The physical appearance should match the software interface.

The Streamlit UI should display:

- Product name
- Technical boundary
- Safety state
- Evidence confidence
- Answer-evidence check
- Evidence cards
- Visual evidence images

The hardware appearance should make these software states visible at the product level.

---

## 11. Current Status

The current appearance design is a planned design for the physical prototype.

The software system has already been implemented and can run on the external computing host.

The physical shell, labels, indicators, and final appearance photos will be completed during the final prototype build stage.

---

## 12. Summary

The SafePLC-Assist Box appearance design aims to support the project’s core positioning:

```text
Safety-aware Industrial Knowledge QA Terminal
```

The appearance should not overstate real industrial control capability.

Instead, it should emphasize:

- Knowledge assistance
- Evidence review
- Safety boundary
- Offline / read-only operation
- Productized terminal form
