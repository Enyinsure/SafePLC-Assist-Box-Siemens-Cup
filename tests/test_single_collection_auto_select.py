from safeplc_assist_box.tools.chroma_collection_selector import discover_collections, select_collection


class Collection:
    name = "only"
    metadata = {}

    def count(self):
        return 3

    def peek(self, limit):
        return {"metadatas": [{"page": 1}], "embeddings": [[0.0, 0.0, 0.0]]}


class Client:
    collection = Collection()

    def list_collections(self):
        return ["only"]

    def get_collection(self, name):
        return self.collection


def test_single_collection_auto_select():
    client = Client()
    name, collection, row = select_collection(client, discover_collections(client), kind="text")
    assert name == "only"
    assert collection.count() == 3
    assert row["embedding_dimension"] == 3
