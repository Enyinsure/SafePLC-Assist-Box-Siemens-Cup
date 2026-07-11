from safeplc_assist_box.schemas import AgentClaim, JudgeDecision


def decision_for(claim, evidence_id="ev1", answer="answer"):
    return JudgeDecision(
        ["Agent"], [], [], [claim.claim_text], [], [], [evidence_id], False, False,
        answer, "PASS", "HIGH", "test", metadata={"accepted_claims": [claim]},
    )


def claim(text, claim_type="parameter"):
    return AgentClaim("c1", text, claim_type, ["ev1"], direct_support=True)
