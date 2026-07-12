from conftest import clear_safeplc_runtime_env

from safeplc_assist_box.agents.figure_agent import FigureAgent
from safeplc_assist_box.agents.judge_agent import JudgeAgent
from safeplc_assist_box.config import SafePLCConfig
from safeplc_assist_box.evidence.evidence_pool import SharedEvidencePool
from safeplc_assist_box.schemas import AgentTask, QueryContext, SubQuestion
from safeplc_assist_box.tools.chroma_text_retriever import ChromaTextRetriever
from safeplc_assist_box.tools.tool_registry import ToolRegistry


TARGET_TEXT = """① 模式选择器
⑥ PROFINET IO 接口 (X2)，带 1 个端口
⑦ PROFINET IO 接口 (X1)，带 2 个端口
图 2-237 不带前面板的 CPU 1517-3 PN/DP 的前视图
6ES7517-3AP00-0AB0"""


class BatchAdapter:
    last_audit = {}

    def query_arguments_many(self, collection, queries):
        assert len(queries) == 2
        assert "不带前面板的模块前视图" in queries[1]
        return {"query_embeddings": [[0.1, 0.2], [0.2, 0.3]]}


class TextCollection:
    metadata = {"hnsw:space": "cosine"}

    def query(self, **kwargs):
        wrong = "CPU 1518-4 PN/DP 前视图，PROFINET IO 接口 (X1)"
        block = "CPU 1517-3 PN/DP X1 方框图和端口结构"
        return {
            "documents": [[wrong, block], [wrong, TARGET_TEXT]],
            "metadatas": [
                [
                    {"page_no": 2681, "section": "CPU 1518-4 PN/DP", "source": "manual.pdf"},
                    {"page_no": 2481, "section": "CPU 1517-3 PN/DP 方框图", "source": "manual.pdf"},
                ],
                [
                    {"page_no": 2681, "section": "CPU 1518-4 PN/DP", "source": "manual.pdf"},
                    {"page_no": 2476, "section": "不带前面板的模块前视图", "source": "manual.pdf"},
                ],
            ],
            "distances": [[0.05, 0.2], [0.04, 0.16]],
        }


def test_location_retrieval_end_to_end_without_jsonl(tmp_path, monkeypatch):
    monkeypatch.setenv("SAFEPLC_FIGURE_CHROMA_DIR", str(tmp_path))
    monkeypatch.setenv("SAFEPLC_FIGURE_COLLECTION", "host_figure_collection")
    clear_safeplc_runtime_env(monkeypatch)
    monkeypatch.setenv("SAFEPLC_ENABLE_QUERY_EXPANSION", "1")
    monkeypatch.setenv("SAFEPLC_MAX_EXPANDED_QUERIES", "2")
    monkeypatch.setenv("SAFEPLC_ALLOW_JSONL_FALLBACK", "0")
    config = SafePLCConfig.from_env(mode="FULL")
    registry = ToolRegistry(config, feature_switches={"enable_figure_backend": False})
    retriever = ChromaTextRetriever(str(tmp_path), "manual", embedding_adapter=BatchAdapter())
    retriever.collection = TextCollection()
    registry._text_retriever = retriever
    registry.backend_audit["text_backend_active"] = True

    query = "CPU 1517-3 PN 的 X1 接口在哪里？"
    task = AgentTask(
        "task_location", "Figure Agent", "Figure Agent", query,
        objective="Locate the interface using direct front-view evidence.",
        input_slots={"module_model": "CPU 1517-3 PN/DP", "interface_name": "X1"},
        required_evidence_types=["figure", "text"], subquestion_ids=["sq_location"],
    )
    pool = SharedEvidencePool()
    result = FigureAgent().run(task, registry, pool)
    pool_schema = pool.to_schema()
    pool_schema.metadata["retrieval_backend_audit"] = dict(registry.backend_audit)
    context = QueryContext(
        query, question_type="FIGURE", required_modalities=["figure", "text"],
        subquestions=[SubQuestion("sq_location", query, "Locate X1")],
    )
    decision = JudgeAgent().decide(context, [result], pool_schema)

    assert pool_schema.evidences[0].page == 2476
    assert all(item.page != 2681 for item in pool_schema.evidences)
    assert registry.backend_audit["chroma_result_count_before_filter"] == 4
    assert registry.backend_audit["chroma_result_count_after_filter"] == 2
    assert registry.backend_audit["backend_attempted"] == ["chroma_text"]
    assert registry.backend_audit["jsonl_fallback_active"] is False
    assert decision.verdict == "PASS"
    assert decision.confidence == "MEDIUM"
    for expected in ("CPU 1517-3 PN/DP", "⑦", "2476", "图 2-237"):
        assert expected in decision.final_answer
    for forbidden in ("①", "Target module", "目标模块", "CPU 1518-4"):
        assert forbidden not in decision.final_answer
    item = pool_schema.evidences[0]
    assert item.visual_evidence_status == "page_text_only"
    assert item.image_exists is False
    assert item.image_path == ""
    assert item.manual_figure_number == "图 2-237"
    assert item.metadata["location_marker"] == "⑦"
