# SafePLC-Assist Box Business Plan

SafePLC-Assist Box is a safety-aware industrial knowledge QA terminal prototype designed for the Siemens Cup Free Exploration Track.

The project focuses on industrial manual knowledge retrieval, safety-aware question handling, Evidence Confidence, Answer-Evidence Check, structured evidence cards, visual evidence rendering, an offline/read-only boundary, and physical terminal prototype design.

---

## 1. Product Overview

SafePLC-Assist Box is designed as an offline, read-only industrial knowledge QA and evidence review terminal.

The system helps users ask questions about Siemens S7-1500 / ET 200MP related industrial manual knowledge and receive answers with traceable evidence.

The project is not a generic chatbot, not a simple search engine, and not a PLC controller.

It is positioned as:

```text
Industrial Knowledge QA Terminal
+
Safety Boundary
+
Evidence Confidence
+
Answer-Evidence Check
+
Visual Evidence Rendering
+
Physical Terminal Prototype
```

---

## 2. Problem Background

Industrial manuals are often large, complex, and difficult to search manually.

In PLC-related learning, training, and maintenance assistance scenarios, users may face several problems:

| Problem | Description |
|---|---|
| Manual overload | Industrial manuals contain many pages and detailed technical descriptions |
| Ambiguous questions | Users may omit module, model, or parameter context |
| Unsupported answers | LLM-style answers may contain claims that are not clearly supported by evidence |
| Safety risk | PLC-related questions may involve unsafe write, download, start, stop, or control actions |
| Low traceability | Plain text answers are hard to audit |
| Weak product form | Pure software demos may look less like complete competition products |

SafePLC-Assist Box is designed to address these problems through safety-aware QA, evidence review, and productized terminal design.

---

## 3. Target Users

| User Type | Need |
|---|---|
| Students and learners | Learn Siemens PLC-related industrial knowledge |
| Competition reviewers | Review prototype capability and safety boundary |
| Industrial training users | Understand manual-based knowledge in a training environment |
| Maintenance assistant users | Look up parameter, module, or safety-related information |
| Instructors and demonstrators | Demonstrate evidence-based industrial QA workflow |

The product is mainly designed for education, training, competition review, and prototype demonstration.

It is not intended for direct industrial deployment or real PLC control.

---

## 4. Product Value

SafePLC-Assist Box provides value in five main areas.

### 4.1 Faster Industrial Knowledge Lookup

The system helps users find relevant manual-based knowledge more efficiently than manually searching long PDF documents.

### 4.2 Safer QA Behavior

The system includes a safety boundary and risk guard to avoid providing unsafe real PLC control instructions.

### 4.3 Evidence-based Review

The system provides Evidence Confidence and Answer-Evidence Check to help users understand whether an answer is sufficiently supported.

### 4.4 Visual Evidence Traceability

The system can render visual evidence images in the local demo environment when corresponding visual evidence assets are available.

This makes the evidence chain more reviewable than plain text snippets.

### 4.5 Productized Competition Form

The physical terminal design makes the system look like an industrial product prototype instead of only a software webpage.

---

## 5. Product Differentiation

| Compared Item | Limitation | SafePLC-Assist Box Difference |
|---|---|---|
| Keyword search | Only returns matching text | Provides answer, evidence confidence, and evidence cards |
| Generic chatbot | May generate unsupported claims | Adds answer-evidence consistency checking |
| Basic RAG demo | Usually lacks safety boundary | Adds industrial safety risk guard |
| Text-only retrieval system | Weak visual traceability | Supports visual evidence rendering |
| Pure software demo | Weak product form | Adds physical terminal prototype design |
| PLC control tool | May involve operation risk | SafePLC-Assist Box is offline, read-only, and not connected to real PLCs |

---

## 6. Core Product Features

Current SafePLC-Assist Box V1.2 includes:

- Streamlit product interface
- Question classification
- Industrial safety risk classification
- Evidence Confidence
- Answer-Evidence Check
- Structured evidence cards
- Visual evidence rendering logic
- Offline / read-only safety boundary
- V1.1 / V1.2 evaluation files
- Online review documentation
- Hardware prototype design documents

---

## 7. Safety Boundary

Safety boundary is a core product requirement.

SafePLC-Assist Box does not:

- Connect to real PLC devices
- Connect to TIA Portal
- Execute PLC communication
- Execute PLC write, download, start, stop, or control actions
- Collect real IT / OT network data
- Replace Siemens official manuals or certified industrial engineers

The product is designed as an offline, read-only industrial knowledge QA and evidence review prototype.

---

## 8. Business / Application Scenarios

### 8.1 Industrial Education

The system can be used as a teaching aid for PLC-related industrial knowledge.

Students can ask questions and review evidence cards instead of only reading long manuals.

### 8.2 Competition Demonstration

The system can be presented as a complete prototype with software interface, evaluation files, safety boundary, evidence checking, and physical terminal design.

### 8.3 Training Environment

The system can help trainees understand manual-based knowledge in a controlled, offline, read-only environment.

### 8.4 Maintenance Knowledge Assistance

The system can assist users in looking up parameters, module information, and safety-related explanations.

It does not replace certified engineers or site procedures.

---

## 9. Development Status

| Area | Status |
|---|---|
| Core software prototype | Completed |
| Streamlit product UI | Completed |
| Question classification | Completed |
| Safety risk guard | Completed |
| Evidence Confidence | Completed |
| Answer-Evidence Check | Completed |
| Structured evidence cards | Completed |
| Visual evidence rendering logic | Completed |
| V1.1 / V1.2 evaluation files | Completed |
| Hardware concept design | Completed |
| Front panel layout | Completed |
| Assembly guide | Completed |
| Physical shell | In progress |
| Final prototype photos | Planned for final submission |
| Final demo video | Planned for final submission |

---

## 10. Market and Competition Insight

The project is not positioned as a direct commercial PLC control product.

Instead, it is closer to:

- Industrial education assistance
- Manual-based knowledge QA
- Safety-aware training tool
- Evidence review terminal
- Competition prototype product

Potential comparable categories include:

| Category | Typical Limitation |
|---|---|
| Manual PDF search | Hard to summarize and review |
| Generic LLM assistant | Lacks industrial safety boundary |
| Basic RAG demo | Often lacks evidence verification |
| Industrial software tools | Usually require real environment integration |
| Training platforms | May lack dynamic QA and evidence tracing |

SafePLC-Assist Box focuses on the gap between industrial knowledge learning and safety-aware evidence-based QA.

---

## 11. Future Development Plan

### Stage 1: Software Prototype

Status: Completed

- Product UI
- Safety boundary
- Question classification
- Safety risk guard
- Evidence confidence
- Answer-evidence checking
- Evidence cards

### Stage 2: Visual Evidence Enhancement

Status: Completed in local demo environment

- Local visual evidence image mapping
- Evidence card image rendering
- Repository boundary explanation

### Stage 3: Hardware Prototype

Status: In progress

- Physical shell design
- Front panel layout
- Indicators and labels
- Assembly guide
- Physical prototype photos

### Stage 4: Final Competition Packaging

Status: Planned

- Final screenshots
- Demo video
- Physical prototype demonstration
- Final submission materials

---

## 12. Risk Analysis

| Risk | Response |
|---|---|
| Copyright-sensitive manual assets cannot be published | Public repository excludes full Siemens manual PDFs and full visual evidence assets |
| Full local environment may be large | Repository excludes full OCR outputs, vector databases, model weights, and compressed release packages |
| PLC-related questions may involve unsafe operations | System includes safety boundary and risk guard |
| Evaluation may be limited | Current report clearly states module-level evaluation scope |
| Physical prototype is not fully completed yet | Hardware documents define current design and final build plan |

---

## 13. Summary

SafePLC-Assist Box is a competition-oriented industrial knowledge QA terminal prototype.

Its main value is not only answering questions, but also making answers safer, more traceable, and more reviewable.

The project combines:

- Industrial manual QA
- Safety-aware behavior
- Evidence confidence
- Answer-evidence consistency checking
- Visual evidence rendering
- Physical terminal design

The current version is ready for software-level and documentation-level review, and will be further strengthened with final physical prototype materials and demo media.

Physical prototype photos and the final demo video are planned for final submission after the physical prototype is completed.
