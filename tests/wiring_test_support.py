from safeplc_assist_box.agents.wiring_agent import WiringAgent
from safeplc_assist_box.evidence.evidence_pool import SharedEvidencePool
from safeplc_assist_box.schemas import AgentTask


class Registry:
    tool_call_count = 0

    def __init__(self, evidences):
        self.evidences = evidences

    def search_text(self, query, top_k=8):
        return list(self.evidences)

    def search_table(self, query, top_k=8):
        return []

    def search_figure(self, query, top_k=5):
        return []


def run_wiring(evidences, query="S7-1500 端子接线注意事项是什么？"):
    task = AgentTask("wiring", "Wiring Agent", "Wiring Agent", query)
    pool = SharedEvidencePool()
    result = WiringAgent().run(task, Registry(evidences), pool)
    return result, pool.to_schema()
