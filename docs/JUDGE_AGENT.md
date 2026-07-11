# Judge Agent

The Judge Agent reads all `AgentResult` objects and the final `EvidencePool`.

It evaluates each structured claim for subquestion coverage, evidence existence, model/order-number consistency, directness, numeric/unit support, figure metadata, cross-family contamination, duplicate/conflicting evidence, and concise output. It emits:

- accepted and rejected agents
- supported and unsupported claims
- final evidence IDs
- need-more-evidence flag
- need-clarification flag
- final answer
- verdict
- confidence
- decision reason
- per-subquestion coverage
- model consistency details
- quality scores

It does not invent industrial parameters from model knowledge. No evidence means no `PASS`; missing subtask coverage yields `PARTIAL` or `NEED_MORE_EVIDENCE`, and unresolved model conflicts cannot be decided by majority vote.
