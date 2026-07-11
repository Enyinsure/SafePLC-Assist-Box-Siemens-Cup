# FULL Server Validation

This procedure is intentionally user-run. It records commands and pass/fail criteria only; it does not claim that any target server or production asset has been tested.

## 1. Clone the Reviewed Branch

```bash
git clone --branch codex/full-rag-multimodal-v2 --single-branch https://github.com/Enyinsure/SafePLC-Assist-Box-Siemens-Cup.git
cd SafePLC-Assist-Box-Siemens-Cup
git rev-parse HEAD
```

Record the commit SHA with the validation output.

## 2. Prepare Python

Create or activate a Python 3.10 or 3.11 environment, then install the base, test, and optional FULL dependencies:

```bash
python --version
python -m pip install -r requirements.txt -r requirements-dev.txt -r requirements-full.txt
```

## 3. Configure Assets

Create an untracked `config/full.env` from `config/full.env.example`, replace every placeholder, and load it into the shell. Set exact text and figure collection names. Use a local embedding model path unless the collection was deliberately created with Chroma's default embedding function.

```bash
set -a
source config/full.env
set +a
```

Keep `SAFEPLC_ALLOW_REMOTE_MODEL_DOWNLOAD=0`. Set `SAFEPLC_ALLOW_CHROMA_DEFAULT_EMBEDDING=1` only after confirming that the collection expects that embedding function. JSONL fallback and hybrid retrieval are disabled by default.

## 4. Inspect Chroma

```bash
python scripts/inspect_chroma_schema.py --kind all --json
```

Select `SAFEPLC_TEXT_COLLECTION` and `SAFEPLC_FIGURE_COLLECTION` from the discovered names. An empty database, an unknown name, or more than one collection without an explicit selection is not ready.

## 5. Check Readiness

```bash
mkdir -p reports/runtime
python scripts/check_full_assets.py --mode FULL --strict --require-chroma --require-figure --output reports/runtime/full_asset_check.json
```

Pass requires exit code 0, `chroma_full_ready=true`, the selected collections to contain records, and both collection selection and embedding readiness to be true. `fallback_only_ready=true` does not satisfy `--require-chroma`.

An `EmbeddingDimensionMismatch` means the query model output dimension differs from the stored collection vectors. Configure the exact local model used to build that collection; do not bypass the error or silently switch embeddings.

## 6. Probe Retrieval

```bash
python scripts/probe_full_retrieval.py "CPU 1517-3 PN 的 X1 接口在哪里？" --top-k 8
```

Inspect `backend_audit`, collection names, model matches, pages, figure numbers, and visual status. For figure evidence, every claimed `image_path` must resolve to a real file under the configured visual directory. A metadata string without an existing image is not verified visual evidence.

## 7. Run Tests

```bash
python -m compileall safeplc_assist_box scripts tests
python -m pytest -q
```

Both commands must exit successfully. These tests include SAMPLE regression and mock Chroma behavior; they do not replace asset validation.

## 8. Run the X1 FULL Case

```bash
python -m safeplc_assist_box.agents.orchestrator "CPU 1517-3 PN 的 X1 接口在哪里？" --mode FULL --json > reports/runtime/full_acceptance_x1.json
```

Review selected agents, per-agent abstention, evidence provenance, model identity, Judge claim decisions, verifier output, figure status, and retrieval backend audit. The answer must not assert a location or figure that lacks accepted evidence.

## 9. Run Benchmark and Ablation

Use a separately reviewed dataset with documented provenance for a real FULL evaluation:

```bash
python -m safeplc_assist_box.evaluation.run_agent_benchmark --cases-dir /path/to/reviewed_cases --mode FULL --method full --output reports/runtime/agent_benchmark_full.json
python -m safeplc_assist_box.evaluation.run_agent_ablation --cases-dir /path/to/reviewed_cases --mode FULL --output reports/runtime/agent_ablation_full.json
```

Do not treat tracked SAMPLE reports or `benchmark/sample_regression` as FULL accuracy evidence. Keep all server-generated outputs under ignored `reports/runtime/` and record the commit SHA, environment, collection names, embedding model, and dataset provenance alongside the results.
