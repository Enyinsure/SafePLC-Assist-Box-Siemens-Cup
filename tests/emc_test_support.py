from safeplc_assist_box.agents.emc_agent import EMCAgent
from safeplc_assist_box.evidence.evidence_pool import SharedEvidencePool
from safeplc_assist_box.schemas import AgentTask


class Registry:
    tool_call_count = 0

    def __init__(self, evidences):
        self.evidences = evidences

    def search_text(self, query, top_k=10):
        return list(self.evidences)


def run_emc(evidences):
    query = "EMC 安装时接地和屏蔽需要注意什么？"
    task = AgentTask("emc", "EMC Agent", "EMC Agent", query)
    pool = SharedEvidencePool()
    result = EMCAgent().run(task, Registry(evidences), pool)
    return result, pool.to_schema()
