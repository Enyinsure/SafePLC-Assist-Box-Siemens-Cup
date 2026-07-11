# Evidence Pool

`SharedEvidencePool` deduplicates `AgentEvidence` records by source, modality, page, figure ID, title, and text signature.

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

The Judge Agent only accepts claims with evidence IDs present in the shared pool.

