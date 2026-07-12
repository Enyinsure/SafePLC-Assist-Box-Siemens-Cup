from safeplc_assist_box.tools.chroma_text_retriever import ChromaTextRetriever


class Adapter:
    last_audit = {}
    def query_arguments_many(self, collection, queries): return {"query_embeddings": [[0.1, 0.2] for _ in queries]}


class Collection:
    metadata = {"hnsw:space": "cosine"}
    def query(self, **kwargs):
        return {"documents": [["EMC definition and title"]], "metadatas": [[{"source": "manual-a", "page_no": 6495, "chunk_index": 1}]], "distances": [[0.1]]}
    def get(self, where, include, limit):
        return {
            "documents": ["grounded control cabinets/control boxes; noise filters in supply lines", "EMC definition and title"],
            "metadatas": [
                {"source": "manual-a", "page_no": 6495, "chunk_index": 0},
                {"source": "manual-a", "page_no": 6495, "chunk_index": 1},
            ],
        }


def aggregated_items(tmp_path, collection=None):
    retriever = ChromaTextRetriever(str(tmp_path), "manual", embedding_adapter=Adapter())
    retriever.collection = collection or Collection()
    return [item for item in retriever.search("EMC grounding", 10) if item.metadata.get("page_aggregate")]


def test_same_page_chunk_aggregation(tmp_path):
    item = aggregated_items(tmp_path)[0]
    assert item.metadata["aggregated_chunk_count"] == 2
    assert item.metadata["aggregated_chunk_ids"] == ["0", "1"]
    assert item.text.startswith("grounded control cabinets")
