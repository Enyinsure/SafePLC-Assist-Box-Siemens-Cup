from safeplc_assist_box.agents.troubleshooting_agent import TroubleshootingAgent
from safeplc_assist_box.evidence.evidence_pool import SharedEvidencePool
from safeplc_assist_box.schemas import AgentTask


class Registry:
    tool_call_count = 0

    def __init__(self, evidences):
        self.evidences = evidences

    def search_text(self, query, top_k=10):
        return list(self.evidences)

    def search_table(self, query, top_k=6):
        return []


def run_troubleshooting(evidences):
    query = "CPU 1517-3 PN 通信不上且指示灯异常，应先检查哪些信息？"
    task = AgentTask("led", "Troubleshooting Agent", "Troubleshooting Agent", query)
    pool = SharedEvidencePool()
    result = TroubleshootingAgent().run(task, Registry(evidences), pool)
    return query, result, pool.to_schema()
