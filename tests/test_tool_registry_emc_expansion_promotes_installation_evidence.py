from safeplc_assist_box.config import SafePLCConfig
from safeplc_assist_box.tools.chroma_text_retriever import ChromaTextRetriever
from safeplc_assist_box.tools.tool_registry import ToolRegistry


INSTALLATION = "grounded control cabinets/control boxes; noise filters in the supply lines; designed for industrial use"


class Adapter:
    last_audit = {}

    def query_arguments_many(self, collection, queries):
        return {"query_embeddings": [[0.1, 0.2] for _ in queries]}


class Collection:
    metadata = {"hnsw:space": "cosine"}

    def query(self, **kwargs):
        count = len(kwargs["query_embeddings"])
        docs = [["EMC certification and approvals"]]
        metas = [[{"source": "cert.pdf", "page_no": 10}]]
        distances = [[0.02]]
        for _ in range(1, count):
            docs.append([INSTALLATION])
            metas.append([{"source": "system.pdf", "page_no": 6495}])
            distances.append([0.12])
        return {"documents": docs, "metadatas": metas, "distances": distances}


def test_tool_registry_emc_expansion_promotes_installation_evidence(tmp_path, monkeypatch):
    monkeypatch.setenv("SAFEPLC_ENABLE_QUERY_EXPANSION", "1")
    monkeypatch.setenv("SAFEPLC_MAX_EXPANDED_QUERIES", "2")
    monkeypatch.setenv("SAFEPLC_ALLOW_JSONL_FALLBACK", "0")
    registry = ToolRegistry(SafePLCConfig.from_env(mode="FULL"))
    retriever = ChromaTextRetriever(str(tmp_path), "manual", embedding_adapter=Adapter())
    retriever.collection = Collection()
    registry._text_retriever = retriever
    registry.backend_audit["text_backend_active"] = True

    results = registry.search_text("EMC 安装时接地和屏蔽需要注意什么？", top_k=5)

    assert results[0].text == INSTALLATION
    assert results[0].matched_query_count == 2
    assert registry.backend_audit["retrieval_queries"][0] == "EMC 安装时接地和屏蔽需要注意什么？"
