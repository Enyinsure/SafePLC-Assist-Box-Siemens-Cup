# Full RAG Multimodal V2 Repair Summary

## Scope Completed

- Added Chroma-first text and figure retrievers with collection discovery, counts, metadata sampling, and explicit errors.
- Kept JSONL as an opt-in FULL fallback. FULL never returns SAMPLE fixture evidence.
- Normalized text, table, and figure evidence into one schema with backend, document/chunk, model/order, page/figure, image, distance, score, match level, and claim links.
- Added model identity normalization, cross-family rejection, evidence reranking, semantic/page deduplication, conflict records, and Shared Evidence Pool audits.
- Added query decomposition, bounded Supervisor routing, structured Agent claims, claim-level Judge decisions, answer-evidence verification, and deterministic evidence-closed synthesis.
- Updated Streamlit to display mode, actual backends, subquestions, Agent outputs, claims, evidence metadata, Judge coverage, model consistency, quality scores, and verifier state.
- Reworked benchmark ingestion to read each unique TSV row once and preserve provenance. It no longer pads case counts with scenario suffixes.
- Added real runtime ablation switches for decomposition, routing, model filtering, figure backend, reranking, Judge, verifier, and second retrieval.
- Added FULL requirements/configuration, asset checks, CI for Python 3.10/3.11, and focused tests.

## Local Verification

| Command | Exit | Result |
|---|---:|---|
| `python -m compileall -q safeplc_assist_box scripts tests` | 0 | Passed |
| `python -m pytest -q` | 0 | 43 passed |
| `git diff --check` | 0 | Passed; Windows line-ending notices only |
| `python scripts/check_full_assets.py --mode FULL --strict --output reports/full_asset_check.log` | 2 | Expected failure: server assets are not configured locally |
| local curated benchmark build | 0 | 10 unique SAMPLE regression cases |
| SAMPLE benchmark, method `full` | 0 | Report generated; not an industrial accuracy claim |
| SAMPLE ablation | 0 | Six runtime profiles generated |

## FULL Asset Status

- Text Chroma real hit: not verified locally.
- Text collection/count: unavailable locally.
- Figure Chroma real hit: not verified locally.
- Figure collection/count: unavailable locally.
- Resolvable image count: unavailable locally.
- JSONL fallback: implemented but disabled in the local FULL run.
- `full_ready`: `false` in the local FULL audit.
- Local FULL acceptance used zero SAMPLE evidence and returned `NEED_MORE_EVIDENCE`/`ABSTAIN` for evidence-dependent questions.

## X1 Acceptance

The SAMPLE regression found direct evidence for CPU 1517-3 PN/DP, order number `6ES7517-3AP00-0AB0`, page 2476, Figure 2-237, marker ⑦, and ports X1 P1/X1 P2. Final evidence pages were 2476 and 2477. Pages 533 and 535 were absent from the final evidence. The fixture has no real image path, so its status is `page_text_only`.

The FULL X1 run did not retrieve evidence because the server assets do not exist in this workspace. It did not substitute the SAMPLE fixture. The real page/figure/image hit must be rerun on the server.

## Benchmark And Ablation

`benchmark/cases_real` contains 10 manual curated cases for local regression because `/home/scc/pb23061092/s7_agent_v2_questions.tsv` is unavailable here. `reports/agent_benchmark_full_real.json` and `reports/agent_ablation_full_real.json` explicitly record `executed=false`; no FULL metrics were invented.

The six ablation profiles execute different paths. The local SAMPLE report shows average Agent calls of 0.9 (`single_agent`), 0.9 (`static_router`), 5.7 (`all_agents`), and 1.6 for the three adaptive profiles. Only `full` enables the verifier; only Judge profiles run claim adjudication.

## Remaining Limitations

- Target-server Chroma collection names, record counts, embedding compatibility, real X1 hits, and image coverage remain unverified.
- The 10-case curated SAMPLE benchmark is a regression suite, not a measure of industrial accuracy.
- Server acceptance reports must overwrite the local `executed=false` FULL reports after the real TSV and Chroma assets are configured.

## Server Reproduction

```bash
python -m compileall safeplc_assist_box scripts tests
python -m pytest -q 2>&1 | tee pytest_server_after_repair.log
python scripts/check_full_assets.py --mode FULL --strict --output reports/full_asset_check.log
python scripts/build_agent_benchmark_from_bundle.py --questions-tsv /home/scc/pb23061092/s7_agent_v2_questions.tsv --output-dir benchmark/cases_real
python -m safeplc_assist_box.agents.orchestrator "CPU 1517-3 PN 的 X1 接口在哪里？" --mode FULL --routing-strategy adaptive --max-agents 4 --json --output reports/full_acceptance_x1.json
python -m safeplc_assist_box.evaluation.run_agent_benchmark --cases-dir benchmark/cases_real --mode FULL --method full --output reports/agent_benchmark_full_real.json
python -m safeplc_assist_box.evaluation.run_agent_ablation --cases-dir benchmark/cases_real --mode FULL --output reports/agent_ablation_full_real.json
```
