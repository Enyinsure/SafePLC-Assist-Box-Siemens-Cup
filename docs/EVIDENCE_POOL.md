# Evidence Pool

`SharedEvidencePool` normalizes and deduplicates evidence by document/chunk identity and semantic/page signatures. It records backend counts, rejected cross-family evidence, agent provenance, claim links, and conflict groups.

Each evidence item records:

- `evidence_id`
- `source`
- `source_type`
- `modality`
- `page`
- `section`
- `figure_id`
- `title`
- `module`
- `order_number`
- `parameter`
- `text`
- `retrieval_score`
- `agent_names`
- `claim_links`
- `metadata`
- `retrieval_backend`, collection, document, and chunk IDs
- manual/model/order-number identity
- raw distance, normalized score, model match level, and quality score
- figure number, image path, and direct-evidence status

The Judge Agent only accepts claims with evidence IDs present in the shared pool.
