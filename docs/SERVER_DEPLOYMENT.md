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
- `SAFEPLC_EMBEDDING_BACKEND`
- `SAFEPLC_EMBEDDING_MODEL_PATH`
- `SAFEPLC_EMBEDDING_DEVICE`
- `SAFEPLC_EMBEDDING_NORMALIZE`
- `SAFEPLC_EMBEDDING_QUERY_PREFIX`
- `SAFEPLC_ALLOW_CHROMA_DEFAULT_EMBEDDING`
- `SAFEPLC_ALLOW_REMOTE_MODEL_DOWNLOAD`
- `SAFEPLC_ENABLE_QUERY_EXPANSION`
- `SAFEPLC_MAX_EXPANDED_QUERIES`
- `SAFEPLC_REPORT_DIR`
- `SAFEPLC_AGENT_TIMEOUT`
- `SAFEPLC_MAX_AGENTS`
- `SAFEPLC_ROUTING_STRATEGY`
- `SAFEPLC_ALLOW_JSONL_FALLBACK`
- `SAFEPLC_ENABLE_JSONL_HYBRID`
- `SAFEPLC_JSONL_FALLBACK_MIN_SCORE`
- `SAFEPLC_REQUIRE_FIGURE_BACKEND`

Use `scripts/configure_server_paths.py --write-env config/full.env` to write an ignored local configuration without changing the active shell. Business code does not hard-code server user paths.

Run `python scripts/inspect_chroma_schema.py` and then `python scripts/check_full_assets.py --mode FULL --strict --require-chroma --output reports/runtime/full_asset_check.json` before FULL startup. The check discovers Chroma collections, counts records, lists sampled metadata fields, counts figure cards and resolvable images, and exits with code 2 when startup conditions are not met. Collection selection is exact and explicit. FULL tries Chroma first; JSONL fallback is opt-in and conditional, and SAMPLE fixture evidence is never returned. Embedding models are local by default: model download and Chroma default embedding both require explicit opt-in.
