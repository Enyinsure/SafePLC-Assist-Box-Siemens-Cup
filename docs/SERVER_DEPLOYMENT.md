# Server Deployment

Environment variables:

- `SAFEPLC_MODE`
- `SAFEPLC_CHROMA_DIR`
- `SAFEPLC_FIGURE_CHROMA_DIR`
- `SAFEPLC_CHUNKS_JSONL`
- `SAFEPLC_PAGES_JSONL`
- `SAFEPLC_VISUAL_DIR`
- `SAFEPLC_MODEL_PATH`
- `SAFEPLC_REPORT_DIR`
- `SAFEPLC_AGENT_TIMEOUT`
- `SAFEPLC_MAX_AGENTS`
- `SAFEPLC_ROUTING_STRATEGY`

Use `scripts/configure_server_paths.py` to print current settings and verify JSONL asset paths. Business code does not hard-code server user paths.

