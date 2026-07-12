from safeplc_assist_box.tools.chroma_text_retriever import ChromaTextRetriever


class Adapter:
    last_audit = {}

    def query_arguments_many(self, collection, queries):
        return {"query_embeddings": [[0.1, 0.2] for _ in queries]}


class Collection:
    metadata = {"hnsw:space": "cosine"}

    def query(self, **kwargs):
        return {
            "documents": [["CPU front view X1"]],
            "metadatas": [[{"module_model": "CPU 1517-3 PN/DP"}]],
            "distances": [[0.2]],
        }


def test_cosine_metric_from_collection_metadata(tmp_path):
    retriever = ChromaTextRetriever(str(tmp_path), "manual", embedding_adapter=Adapter())
    retriever.collection = Collection()
    item = retriever.search_many(["X1 location"], top_k_per_query=12)[0]
    assert item.raw_distance == 0.2
    assert item.distance_metric == "cosine"
    assert item.score_conversion == "one_minus_cosine_distance"
    assert item.vector_similarity == 0.8
