# Assembly Guide

This document describes the planned assembly process of the SafePLC-Assist Box physical prototype.

## Current Prototype Scheme

The project adopts Scheme B:

```text
External computing host + productized physical terminal shell
```

A laptop is used as the external computing host. The physical box acts as the display and interaction terminal.

The terminal is designed to provide a product-like industrial interaction form while keeping the system offline, read-only, and disconnected from real PLC control.

---

## Assembly Goal

The goal of the physical prototype is to turn the software system into a visible industrial terminal form.

The prototype should make the following boundaries clear:

- The system is for industrial knowledge QA only.
- The system does not connect to real PLC devices.
- The system does not execute PLC write, download, start, stop, or control actions.
- The system provides evidence-based assistance and safety reminders.

---

## Planned Components

| Component | Description |
|---|---|
| External host | Laptop running the SafePLC-Assist Box software |
| Shell | Industrial-style enclosure |
| Display | Small HDMI / USB display or tablet-like screen |
| Buttons | Query / Demo / Export Log buttons |
| Indicators | SAFE / CAUTION / HIGH_RISK / CHECK indicators |
| Labels | OFFLINE / READ-ONLY, PLC CONTROL DISABLED, KNOWLEDGE QA ONLY |
| Power | External power supply or USB power depending on the display module |
| Mounting parts | Screws, brackets, adhesive labels, and internal support parts |

---

## Planned Assembly Steps

1. Prepare the enclosure shell.
2. Mark the front panel layout.
3. Mount the display area or reserve the display window.
4. Add status indicator positions.
5. Add Query / Demo / Export Log button positions.
6. Attach the SafePLC-Assist Box nameplate.
7. Attach the safety boundary labels.
8. Connect the display to the external computing host.
9. Run the Streamlit product interface on the external host.
10. Verify that no PLC control interface is connected.
11. Verify that the interface displays the OFFLINE / READ-ONLY safety boundary.
12. Test demo questions and evidence card rendering.

---

## Safety Verification Checklist

| Check Item | Expected Result |
|---|---|
| Real PLC connection | Not connected |
| TIA Portal connection | Not connected |
| PLC write / download / control function | Disabled / not implemented |
| IT / OT network data collection | Not collected |
| Evidence card panel | Available in software interface |
| Visual evidence rendering | Available in local demo environment |
| Safety boundary labels | Visible on the front panel |

---

## Software-Hardware Relationship

The physical box is not an independent PLC controller.

It is a productized shell for the SafePLC-Assist Box software system.

```text
User
↓
Physical terminal interface
↓
External computing host
↓
SafePLC-Assist Box Streamlit UI
↓
Safety-aware QA / Evidence Confidence / Evidence Check
```

---

## Current Status

The current hardware work focuses on prototype design documentation.

The final physical shell, photos, and demonstration media will be added after the hardware prototype is completed.
