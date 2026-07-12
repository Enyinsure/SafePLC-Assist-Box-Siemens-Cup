from safeplc_assist_box.agents.judge_agent import JudgeAgent
from safeplc_assist_box.agents.parameter_agent import ParameterAgent
from safeplc_assist_box.config import SafePLCConfig
from safeplc_assist_box.evidence.evidence_pool import SharedEvidencePool
from safeplc_assist_box.schemas import AgentTask, QueryContext, SubQuestion
from safeplc_assist_box.tools.chroma_text_retriever import ChromaTextRetriever
from safeplc_assist_box.tools.tool_registry import ToolRegistry


PAGE_TEXT = """PS 60W 24/48/60VDC HF
电源电压
额定值 (DC)
24 V / 48 V / 60 V
允许范围，下限 (DC)
静态 19.2 V，动态 18.5 V
允许范围，上限 (DC)
静态 72 V，动态 75.5 V"""


class BatchAdapter:
    last_audit = {}

    def query_arguments_many(self, collection, queries):
        return {"query_embeddings": [[0.1, 0.2] for _ in queries]}


class TextCollection:
    metadata = {"hnsw:space": "cosine"}

    def query(self, **kwargs):
        count = len(kwargs["query_embeddings"])
        metadata = {
            "page_no": 6313,
            "section": "PS 60W 24/48/60VDC HF - 电源电压",
            "source": "device-manual.pdf",
            "modality": "table",
        }
        return {
            "documents": [[PAGE_TEXT] for _ in range(count)],
            "metadatas": [[metadata] for _ in range(count)],
            "distances": [[0.08] for _ in range(count)],
        }


def test_parameter_agent_real_chroma_layout_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setenv("SAFEPLC_ENABLE_QUERY_EXPANSION", "0")
    monkeypatch.setenv("SAFEPLC_ALLOW_JSONL_FALLBACK", "0")
    config = SafePLCConfig.from_env(mode="FULL")
    registry = ToolRegistry(config)
    retriever = ChromaTextRetriever(str(tmp_path), "manual", embedding_adapter=BatchAdapter())
    retriever.collection = TextCollection()
    registry._text_retriever = retriever
    registry.backend_audit["text_backend_active"] = True

    query = "PS 60W 24/48/60VDC HF 的电源电压允许范围是多少？"
    task = AgentTask(
        "task_parameter",
        "Parameter Agent",
        "Parameter Agent",
        query,
        input_slots={"module_model": "PS 60W 24/48/60VDC HF"},
        required_evidence_types=["table", "text"],
        subquestion_ids=["sq_parameter"],
    )
    pool = SharedEvidencePool()
    result = ParameterAgent().run(task, registry, pool)
    pool_schema = pool.to_schema()
    pool_schema.metadata["retrieval_backend_audit"] = dict(registry.backend_audit)
    context = QueryContext(
        query,
        question_type="PARAMETER",
        required_modalities=["table", "text"],
        subquestions=[SubQuestion("sq_parameter", query, "Extract the supported voltage range.")],
    )

    decision = JudgeAgent().decide(context, [result], pool_schema)

    assert result.status == "ANSWERED"
    assert pool_schema.evidences[0].page == 6313
    assert decision.verdict == "PASS"
    assert "静态 19.2～72 V DC" in decision.final_answer
    assert "动态 18.5～75.5 V DC" in decision.final_answer
    assert registry.backend_audit["jsonl_fallback_active"] is False
