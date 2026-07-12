from safeplc_assist_box.agents.parameter_agent import ParameterAgent
from safeplc_assist_box.evidence.evidence_pool import SharedEvidencePool
from safeplc_assist_box.schemas import AgentTask
from retrieval_test_support import evidence


class Registry:
    tool_call_count = 0
    def search_table(self, query, top_k=8): return []
    def search_text(self, query, top_k=8):
        return [evidence("ps", "静态范围 19.2 V 至 72 V，动态范围 18.5 V 至 75.5 V。", model="PS 60W 24/48/60VDC HF")]


def test_parameter_text_backend_survives_missing_table_backend():
    task = AgentTask("t", "Parameter Agent", "Parameter Agent", "PS 60W 24/48/60VDC HF 电压范围", input_slots={"module_model": "PS 60W 24/48/60VDC HF"})
    assert ParameterAgent().run(task, Registry(), SharedEvidencePool()).status == "ANSWERED"
