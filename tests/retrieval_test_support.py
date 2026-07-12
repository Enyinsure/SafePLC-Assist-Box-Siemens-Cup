from safeplc_assist_box.schemas import AgentEvidence


def evidence(evidence_id, text, model="CPU 1517-3 PN/DP", page=None, score=0.5, **kwargs):
    return AgentEvidence(
        evidence_id=evidence_id,
        source="manual",
        source_type="manual",
        modality="text",
        text=text,
        module_model=model,
        page=page,
        retrieval_score=score,
        normalized_score=score,
        vector_similarity=score,
        **kwargs,
    )
