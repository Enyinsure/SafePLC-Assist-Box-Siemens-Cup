from safeplc_assist_box.evidence.fact_extractors import extract_emc_facts
from safeplc_assist_box.retrieval.query_expander import QueryExpander
from safeplc_assist_box.tools.chroma_text_retriever import ChromaTextRetriever


class Adapter:
    last_audit = {}

    def query_arguments_many(self, collection, queries):
        return {"query_embeddings": [[0.1, 0.2] for _ in queries]}


class Collection:
    metadata = {"hnsw:space": "cosine"}

    def query(self, **kwargs):
        return {
            "documents": [[], ["Electromagnetic compatibility\nIndustrial applications"], []],
            "metadatas": [[], [{"source": "system.pdf", "page_no": 6495, "chunk_index": 1}], []],
            "distances": [[], [0.1], []],
        }

    def get(self, **kwargs):
        return {
            "documents": [
                "Electromagnetic compatibility\nIndustrial applications\nUse in residential areas\nEN 55011 Class B",
                "grounded control cabinets/control boxes\nnoise filters in the supply lines",
            ],
            "metadatas": [
                {"source": "system.pdf", "page_no": 6495, "chunk_index": 0},
                {"source": "system.pdf", "page_no": 6495, "chunk_index": 1},
            ],
        }


def test_emc_same_page_aggregation_after_expanded_hit(tmp_path):
    expansion = QueryExpander().expand("EMC 安装时接地和屏蔽需要注意什么？")
    retriever = ChromaTextRetriever(str(tmp_path), "manual", embedding_adapter=Adapter())
    retriever.collection = Collection()
    items = retriever.search_many(expansion.all_queries, expansion_reasons=expansion.expansion_reasons)
    aggregates = [item for item in items if item.metadata.get("page_aggregate")]
    assert len(aggregates) == 1
    assert aggregates[0].retrieval_query == expansion.expanded_queries[0]
    assert len(extract_emc_facts(aggregates[0].text)) == 4
