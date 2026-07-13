# FULL-360 Industrial Evidence Benchmark

## Purpose

FULL-360 evaluates the SafePLC-Assist Box as a dynamic multi-agent industrial evidence terminal. It measures routing, evidence grounding, model scope, clarification, abstention, safety refusal, and claim-level Judge behavior against real PLC manual assets. It is not a training set and it is not a target-answer patch list.

## Three Layers

The benchmark has exactly 360 cases when generation is complete:

| Layer | Count | Role |
| --- | ---: | --- |
| Core-30 | 30 | Frozen, high-value regression cases |
| Natural-240 | 240 | Evidence-derived everyday lookup and compound tasks |
| Stress-90 | 90 | Controlled unsupported, conflicting, cross-model, visual, and safety boundaries |

Natural-240 contains parameter, wiring, troubleshooting, figure location, topology clarification, EMC, compound multi-agent, missing-slot clarification, and maintenance work-order cases. Stress-90 contains cross-model, unsupported-entity, industrial-safety, distractor/conflict, and missing-or-mismatched visual cases.

## Data Sources

Seed generation reads only paths configured through these environment variables:

```text
SAFEPLC_CHROMA_DIR
SAFEPLC_TEXT_COLLECTION
SAFEPLC_FIGURE_CHROMA_DIR
SAFEPLC_FIGURE_COLLECTION
SAFEPLC_CHUNKS_JSONL
SAFEPLC_PAGES_JSONL
SAFEPLC_FIGURE_CARDS_JSONL
SAFEPLC_FIGURE_CHUNKS_JSONL
```

Absolute server paths are not stored in generated cases. Each seed records the environment-variable name, selected collection, source record ID, page, and a bounded evidence excerpt.

## Evidence Seed Bank

Run `benchmark/generation/build_evidence_seed_bank.py` on the asset host. It filters empty, garbled, low-information, directory, and duplicate records. It reuses the production metadata normalizer, model identity parser, parameter parser, interface-marker parser, LED extractor, wiring extractor, topology extractor, and EMC extractor without changing their behavior.

A seed is marked `source_verified=true` only when it was read from a configured local Chroma or JSONL asset. Unknown fields remain empty or zero; the builder does not infer a page, order number, model, or figure ID that the source cannot support.

## Case Generation

`benchmark/generation/build_full_360.py` uses random seed `42`, audited templates, structured slots, and controlled negative transformations. It does not call a remote model. Every generated case has source seed IDs, and every mutation records its parent, mutation fields, trigger, and expected safe behavior. A seed can participate in at most five cases.

Core-30 is loaded unchanged. Its source file is protected by `benchmark/cases/full_360/frozen_core_30.sha256`; generation stops if the current SHA256 differs.

## Human Review

Generated cases always start with:

```json
{"manual_reviewed": false, "review_status": "pending"}
```

Exact duplicate queries fail validation. Token and character 3-gram near-duplicates are retained and written to `manual_review_queue.jsonl`. A human reviewer must inspect wording, evidence scope, mutation validity, and expected behavior before changing review status.

## Leakage And Hardcoding Controls

- ANSWER cases require verified source seeds and traceable pages.
- Negative cases describe a mutation instead of inventing a source page.
- Runtime acceptance examines Judge-final evidence and structured claims.
- Query text does not satisfy an evidence requirement.
- Cross-model cases carry explicit forbidden-model or scope conditions.
- Case IDs, pages, and expected answers are never added to production agents.
- Dataset validation rejects vocabulary from unrelated project domains.

## Build And Validate

On the FULL asset host:

```bash
python benchmark/generation/build_evidence_seed_bank.py
python benchmark/generation/build_full_360.py
python benchmark/generation/build_dev_120.py
python benchmark/generation/validate_full_360.py
```

If no readable real asset is configured, seed generation exits with code `2` and does not write a formal seed bank. Do not replace this step with synthetic data. Unit tests use temporary fixtures only to test deterministic code paths.

## Dev-120

Dev-120 always contains all Core-30 cases plus 90 cases sampled from Natural and Stress with seed `42`. Sampling covers every generated category, all three difficulty levels, ANSWER, CLARIFY, ABSTAIN, REFUSE, and compound routing. Re-running the builder on the same FULL-360 file produces the same case IDs and order.

## FULL Runtime

The runner is single-process by default and refuses incomplete environments. Both JSONL fallback switches are forced off.

```bash
python scripts/run_full_360.py --subset core30 --output-dir reports/runtime/full360_core30
python scripts/run_full_360.py --subset dev120 --output-dir reports/runtime/full360_dev120
python scripts/run_full_360.py --subset full360 --output-dir reports/runtime/full360_all
```

Useful controls include `--case-id`, `--category`, `--max-cases`, `--start-index`, `--resume`, and `--stop-on-error`. Each completed case updates `checkpoint.json`. Resume skips a case only when its stored input hash matches the current case and dataset hash.

Exit codes are:

- `0`: every selected case passed.
- `1`: at least one case failed or raised a case-level error.
- `2`: dataset, checkpoint, collection, embedding, or FULL environment validation failed.

`environment.json` records the Git SHA, dirty-worktree flag, dataset SHA256, schema version, selected collections, embedding configuration, fallback state, Python version, and timestamps. Runtime output belongs under the ignored `reports/runtime/` directory.

## Metrics

Run:

```bash
python scripts/summarize_full_360.py reports/runtime/full360_dev120
```

The summary includes overall and layer pass rates, category pass rates, action, verdict, routing, clarification, abstention, refusal, parameter-fact, figure-grounding and evidence-page accuracy, claim support, unsupported claims, cross-model contamination, no-evidence fabrication, agent calls, latency percentiles, and errors. It writes `summary.json`, `summary.tsv`, `category_metrics.tsv`, `failure_analysis.jsonl`, `latency_metrics.json`, and `manual_review_metrics.json`.

## Current Limits

Automatic templates cannot certify that every phrasing is natural, that every Chroma record is semantically complete, or that every negative transformation is pedagogically useful. Visual records can contain page text without an available image. Chroma collection and embedding compatibility must be checked on the target host. These limitations are review items, not reasons to weaken validation.

## Why 100 Percent Is Not The Goal

FULL-360 is intended to expose retrieval gaps, ambiguous slots, unsupported entities, model contamination, incomplete visual evidence, and legitimate refusal paths. Failures are retained for analysis. Production logic must not be changed case by case merely to increase the score.

## Reproducing An Experiment

1. Record the repository SHA and verify a clean or intentionally documented worktree.
2. Configure all required Text Chroma, Figure Chroma, collection, and local embedding variables.
3. Build the seed bank and inspect its rejection/count report.
4. Generate FULL-360 and Dev-120.
5. Run the validator and inspect every near-duplicate review candidate.
6. Run a five-case Dev-120 smoke test.
7. Run the desired subset and preserve its `environment.json` with the reports.
8. Summarize results without changing expected cases or production behavior.

The source checkout may contain only the frozen Core manifest until real host assets are available. A missing formal seed bank or dataset means generation has not been completed; it must never be reported as a 360-case result.
