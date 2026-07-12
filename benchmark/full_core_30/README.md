# SafePLC FULL Core 30

This suite is the reproducible core FULL benchmark for the industrial assistant. It contains the ten server-verified smoke cases first, followed by twenty boundary cases that must be frozen only after their first real FULL run.

## Safety And Truthfulness

- The runner always uses `FULL` mode.
- `SAFEPLC_ALLOW_JSONL_FALLBACK` and hybrid JSONL retrieval must be disabled.
- A real text Chroma directory must exist before any case runs.
- SAMPLE evidence is rejected by the runner.
- Runtime outputs are generated locally under `reports/runtime/full_core_30/`; no fabricated result files are stored in this benchmark directory.
- New cases do not require unverified page numbers. Verified pages are annotated in `cases.jsonl`.

## Run

```bash
export SAFEPLC_MODE=FULL
export SAFEPLC_CHROMA_DIR=/path/to/text_chroma
export SAFEPLC_TEXT_COLLECTION=your_text_collection
export SAFEPLC_FIGURE_CHROMA_DIR=/path/to/figure_chroma
export SAFEPLC_FIGURE_COLLECTION=your_figure_collection
export SAFEPLC_EMBEDDING_MODEL_PATH=/path/to/embedding_model
export SAFEPLC_ALLOW_JSONL_FALLBACK=0
export SAFEPLC_ENABLE_JSONL_HYBRID=0

python scripts/run_full_core_30.py
```

Use `--case-id`, `--limit`, or `--output-dir` for a bounded diagnostic run. A run creates one JSON response per case plus `summary.json`, `summary.tsv`, `run.log`, `acceptance.log`, and `environment.json`.

## Freeze Policy

The first ten cases have `origin=preserved_full_smoke_10` and preserve their established acceptance semantics. New evidence pages may be added to cases 11-30 only after a real server FULL run confirms them. Production code must never import this benchmark or use its expected pages as routing rules.
