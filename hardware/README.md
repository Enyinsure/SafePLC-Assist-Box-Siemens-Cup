# SafePLC-Assist Box Hardware Prototype

This document describes the hardware prototype design of SafePLC-Assist Box.

The hardware part is designed to make the software prototype look and behave like a productized industrial knowledge QA terminal rather than a pure software demo.

---

## Prototype Scheme

SafePLC-Assist Box adopts Scheme B:

```text
External computing host + productized physical terminal shell
```

In this scheme, a laptop is used as the external computing host, while the physical terminal shell provides the display area, interaction elements, status indicators, labels, and product identity.

The current hardware design focuses on the product form and safety boundary presentation.

---

## Design Purpose

The physical prototype is designed to support the following goals:

- Present the system as an industrial knowledge QA terminal
- Provide a visible product form for competition review
- Show the offline / read-only safety boundary clearly
- Separate knowledge assistance from real PLC control
- Display software safety states through physical indicators
- Support future demonstration with screenshots, photos, and videos

The hardware prototype does not turn the system into a PLC controller.

---

## Current Hardware Status

| Item | Status |
|---|---|
| External computing host | Available |
| Streamlit UI running on laptop | Available |
| Hardware concept design | Completed |
| Front panel layout design | Completed |
| Assembly guide | Completed |
| BOM document | In progress |
| Physical shell | In progress |
| Final prototype photos | Planned for final submission |
| Final demo video | Planned for final submission |

---

## Planned Physical Components

| Component | Purpose |
|---|---|
| External host | Runs the SafePLC-Assist Box software |
| Terminal shell | Provides the industrial product form |
| Display area | Shows the Streamlit product interface |
| SAFE indicator | Shows low-risk knowledge query state |
| CAUTION indicator | Shows review-required or incomplete-context state |
| HIGH_RISK indicator | Shows potentially unsafe operation request state |
| CHECK indicator | Shows evidence checking completion |
| Query button | Product interaction metaphor for question submission |
| Demo button | Product interaction metaphor for demo case execution |
| Export Log button | Product interaction metaphor for log export |
| Nameplate | Shows SafePLC-Assist Box product identity |
| Boundary labels | Clearly show offline, read-only, and no-control boundaries |

---

## Safety Boundary

The physical terminal must clearly display the following labels:

```text
OFFLINE / READ-ONLY
PLC CONTROL DISABLED
KNOWLEDGE QA ONLY
```

These labels are not decorative. They are part of the safety design.

The project involves PLC-related industrial knowledge, so the prototype must clearly communicate that it is only a knowledge assistance terminal.

---

## What the Hardware Does

The physical terminal is designed to:

- Display the SafePLC-Assist Box UI
- Provide product-like interaction elements
- Show safety states using indicators
- Show clear system boundary labels
- Support competition presentation and demonstration

---

## What the Hardware Does Not Do

The physical terminal does not:

- Connect to real PLC devices
- Connect to TIA Portal
- Execute PLC communication
- Execute PLC write, download, start, stop, or control actions
- Collect real IT / OT network data
- Replace certified industrial safety procedures

---

## Related Hardware Documents

| Document | Description |
|---|---|
| `hardware/front_panel_layout.md` | Front panel layout and software-to-panel mapping |
| `hardware/assembly_guide.md` | Planned assembly process and safety checklist |
| `hardware/bom.md` | Planned hardware component list |

---

## Software-Hardware Relationship

The hardware prototype provides a physical form for the software system.

```text
User
↓
SafePLC-Assist Box physical terminal
↓
External computing host
↓
Streamlit product UI
↓
Safety-aware QA
↓
Evidence Confidence
↓
Answer-Evidence Check
↓
Visual Evidence Rendering
```

The physical terminal helps present the project as a complete product prototype, while the core intelligence and safety logic remain in the software system.

---

## Current Stage

The current stage focuses on hardware design documentation and prototype planning.

The software system is already implemented. The physical terminal shell and final demonstration materials will be completed during the final prototype build stage.
