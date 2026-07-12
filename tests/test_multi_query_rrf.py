from safeplc_assist_box.evidence.evidence_ranker import reciprocal_rank_fusion
from retrieval_test_support import evidence
from safeplc_assist_box.tools.chroma_text_retriever import ChromaTextRetriever


def test_multi_query_rrf_accumulates_ranks_and_provenance():
    original = evidence("same", "front view X1", page=10)
    original.metadata.update(retrieval_query="original", rank_within_query=8)
    expanded = evidence("same", "front view X1", page=10)
    expanded.metadata.update(retrieval_query="expanded", rank_within_query=2)
    fused = reciprocal_rank_fusion([original, expanded])
    assert len(fused) == 1
    assert fused[0].metadata["query_ranks"] == {"original": 8, "expanded": 2}
    assert fused[0].metadata["matched_query_count"] == 2
    assert fused[0].metadata["best_query_rank"] == 2
    assert fused[0].metadata["rrf_score"] > 0


class BatchAdapter:
    last_audit = {}

    def __init__(self):
        self.queries = []

    def query_arguments_many(self, collection, queries):
        self.queries = list(queries)
        return {"query_embeddings": [[0.1, 0.2] for _ in queries]}


class BatchCollection:
    metadata = {"hnsw:space": "cosine"}

    def query(self, **kwargs):
        assert len(kwargs["query_embeddings"]) == 2
        return {
            "documents": [["original result"], ["expanded result"]],
            "metadatas": [[{}], [{}]],
            "distances": [[0.3], [0.2]],
        }


def test_search_many_batches_embeddings_and_keeps_query_metadata(tmp_path):
    adapter = BatchAdapter()
    retriever = ChromaTextRetriever(str(tmp_path), "manual", embedding_adapter=adapter)
    retriever.collection = BatchCollection()
    items = retriever.search_many(["original", "expanded"], 12, ["location_front_view"])
    assert adapter.queries == ["original", "expanded"]
    assert [item.metadata["retrieval_query_index"] for item in items] == [0, 1]
    assert items[1].metadata["query_expansion_reason"] == "location_front_view"
    assert all(item.metadata["rank_within_query"] == 1 for item in items)
    assert items[1].retrieval_query == "expanded"
    assert items[1].retrieval_query_index == 1
    assert items[1].rank_within_query == 1
