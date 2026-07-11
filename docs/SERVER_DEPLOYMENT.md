# Server Deployment

Environment variables:

- `SAFEPLC_MODE`
- `SAFEPLC_CHROMA_DIR`
- `SAFEPLC_FIGURE_CHROMA_DIR`
- `SAFEPLC_TEXT_COLLECTION`
- `SAFEPLC_FIGURE_COLLECTION`
- `SAFEPLC_CHUNKS_JSONL`
- `SAFEPLC_PAGES_JSONL`
- `SAFEPLC_FIGURE_CARDS_JSONL`
- `SAFEPLC_FIGURE_CHUNKS_JSONL`
- `SAFEPLC_VISUAL_DIR`
- `SAFEPLC_REPORT_DIR`
- `SAFEPLC_AGENT_TIMEOUT`
- `SAFEPLC_MAX_AGENTS`
- `SAFEPLC_ROUTING_STRATEGY`
- `SAFEPLC_ALLOW_JSONL_FALLBACK`
- `SAFEPLC_REQUIRE_FIGURE_BACKEND`

Use `scripts/configure_server_paths.py --write-env config/full.env` to write an ignored local configuration without changing the active shell. Business code does not hard-code server user paths.

Run `python scripts/check_full_assets.py --mode FULL --strict --output reports/full_asset_check.log` before FULL startup. The check discovers Chroma collections, counts records, lists sampled metadata fields, counts figure cards and resolvable images, and exits with code 2 when startup conditions are not met. FULL tries Chroma first; JSONL fallback is explicit, and SAMPLE fixture evidence is never returned.
