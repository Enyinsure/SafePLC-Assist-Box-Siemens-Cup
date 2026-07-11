from safeplc_assist_box.agents.parameter_agent import ParameterAgent
from safeplc_assist_box.config import SafePLCConfig
from safeplc_assist_box.evidence.evidence_pool import SharedEvidencePool
from safeplc_assist_box.schemas import AgentTask
from safeplc_assist_box.tools.tool_registry import ToolRegistry


def test_agent_abstains_without_evidence():
    task = AgentTask("t1", "Parameter Agent", "Parameter Agent", "unmatched-token-abcdef")
    result = ParameterAgent().run(task, ToolRegistry(SafePLCConfig.from_env(mode="SAMPLE")), SharedEvidencePool())
    assert result.status == "ABSTAIN"
    assert not result.evidence_ids

