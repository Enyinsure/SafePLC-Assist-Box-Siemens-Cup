# SafePLC-Assist Box

SafePLC-Assist Box is an agent-first industrial knowledge terminal for PLC teaching, trainee engineer practice, and maintenance evidence lookup.

The system uses a Dynamic Supervisor to select specialist agents, lets each agent gather text/table/figure evidence through a shared tool layer, and lets a Judge Agent accept, reject, or mark conflicts before producing a structured answer.

## Core Architecture

- Dynamic Supervisor
- Professional Agent Pool
- Shared Evidence Pool
- Judge Agent
- Active Clarification
- Multimodal Industrial Tools

RAG is treated as a tool layer, not as the product architecture. The frontend, CLI, benchmark, and ablation scripts all call the same `run_agent_system()` orchestrator.

## Runtime Requirement

SafePLC-Assist Box supports **Python 3.10 and Python 3.11**.

## Run

```bash
python -m safeplc_assist_box.agents.orchestrator "CPU 1517-3 PN 的 X1 接口在哪里" --mode SAMPLE --json
python -m safeplc_assist_box.evaluation.run_agent_benchmark --cases-dir benchmark/sample_regression --mode SAMPLE --method full
streamlit run app.py
```

## Frontend Quick Start

The Streamlit frontend is a three-page engineering workspace backed by the same `run_agent_system()` entrypoint as the CLI and benchmark. It does not maintain a separate answer generator.

```bash
cd <project_root>
pip install -r requirements.txt
streamlit run app.py
```

The navigation contains the intelligent evidence workbench, editable maintenance work order, and system/benchmark audit pages. The former `safeplc_assist_box/app_assist_box.py` command remains available as a single-page compatibility launcher.

### Frontend Modes

`SAFEPLC_FRONTEND_MODE` controls only how the UI obtains a response. `SAFEPLC_MODE` still controls the production retrieval pipeline (`SAMPLE`, `MOCK`, or `FULL`).

```bash
export SAFEPLC_FRONTEND_MODE=auto
export SAFEPLC_MODE=SAMPLE
streamlit run app.py
```

`auto` calls the real unified orchestrator first. If that call raises an error, an offline snapshot is allowed only when the user explicitly loaded a matching demo case. A free-form question is never replaced with demo output.

```bash
export SAFEPLC_FRONTEND_MODE=online
export SAFEPLC_MODE=FULL
streamlit run app.py
```

`online` only calls the unified orchestrator and exposes backend errors without substituting demo evidence.

```bash
export SAFEPLC_FRONTEND_MODE=demo
export SAFEPLC_ENABLE_DEMO=true
streamlit run app.py
```

`demo` only reads immutable SAMPLE response snapshots declared in `safeplc_assist_box/frontend/data/demo_cases.json`. The status header marks this mode as offline and does not report Text/Figure Chroma as connected.

### FULL Assets

Start from `config/full.env.example`. A FULL frontend normally needs:

- `SAFEPLC_CHROMA_DIR` and `SAFEPLC_TEXT_COLLECTION`
- `SAFEPLC_FIGURE_CHROMA_DIR` and `SAFEPLC_FIGURE_COLLECTION`
- `SAFEPLC_EMBEDDING_BACKEND` and `SAFEPLC_EMBEDDING_MODEL_PATH`
- `SAFEPLC_VISUAL_DIR` for resolvable manual images
- optional JSONL paths only when `SAFEPLC_ALLOW_JSONL_FALLBACK=1`

The header distinguishes an observed backend connection from a merely configured path. Before the first query, an existing FULL path is shown as configured but pending query verification; after a response, the retrieval backend audit supplies the observed state. Missing images show a safe placeholder and retain the original evidence path.

Repository-backed SAMPLE benchmark data is read from `reports/agent_benchmark_sample.json` and `reports/agent_ablation_sample.json`. Reproducible cases come from `benchmark/sample_regression`. The page labels these as SAMPLE regression results, not FULL industrial accuracy. Runtime FULL reports remain under the ignored `reports/runtime/` directory.

For startup failures, check the frontend and pipeline modes first, then run `scripts/check_full_assets.py --mode FULL --strict --require-chroma`. Backend exceptions are logged server-side; the normal UI shows a concise error and keeps details in the developer expander. PDF work-order export is not enabled by the current exporter; JSON, Markdown, and TXT export are available in-session.

## Modes

- `SAMPLE`: built-in industrial manual snippets; no GPU or server assets required.
- `MOCK`: reserved for lightweight demos using the same code path.
- `FULL`: uses explicitly selected persistent text and figure Chroma collections. JSONL is used only when `SAFEPLC_ALLOW_JSONL_FALLBACK=1` and strict fallback conditions are met; SAMPLE evidence is never used as a FULL fallback.

Copy `config/full.env.example` to an ignored local env file and set the collection names, local embedding model, and asset paths. FULL mode does not download an embedding model and does not use Chroma's default embedding unless the corresponding opt-in variable is enabled. Run `scripts/inspect_chroma_schema.py` and `scripts/check_full_assets.py --mode FULL --strict --require-chroma` before startup. Missing or ambiguous collections, incompatible embedding dimensions, and missing required backends exit non-zero instead of silently passing.

`benchmark/sample_regression` is a local regression set, not evidence of FULL industrial accuracy. Real Chroma, Figure Chroma, image paths, FULL benchmark results, and server performance must be validated by the user on the target server using `docs/FULL_SERVER_VALIDATION.md`; runtime reports belong under the ignored `reports/runtime/` directory.

The auditable FULL-360 benchmark builder, validator, resumable runner, metric definitions, and real-asset generation boundary are documented in [`docs/FULL_360_BENCHMARK.md`](docs/FULL_360_BENCHMARK.md). Formal Natural/Stress cases are generated only from a verified evidence seed bank on the FULL asset host; unit-test fixtures are never published as benchmark data.

## Evidence Contract

The Supervisor decomposes compound questions and selects a bounded subset of specialist agents. Agents return structured claims with independent evidence IDs and abstain when unsupported. The Shared Evidence Pool normalizes and deduplicates evidence, model identity filtering rejects cross-family matches, and the claim-level Judge plus verifier check coverage, model consistency, numeric support, and figure requirements.

For explicit interface-location intent, FULL retrieval can generate one bounded front-view expansion (`SAFEPLC_ENABLE_QUERY_EXPANSION=1`) and batch it with the original query. Candidates are model-filtered before Reciprocal Rank Fusion and location-directness reranking. The expansion contains no page, figure number, marker, or database-derived answer.

The deterministic synthesizer only uses Judge-accepted claims and evidence. Streamlit exposes routing, subquestions, claims, retrieval backends, model matching, evidence provenance, Judge coverage, and verifier status through the same orchestrator used by CLI and evaluation.

## Boundaries

SafePLC-Assist Box is OFFLINE / READ-ONLY. It does not connect to real PLC devices, TIA Portal, live OT networks, or execute write/control actions. Dangerous industrial operation requests are routed to the Safety Boundary Agent.
