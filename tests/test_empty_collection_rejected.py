import pytest

from safeplc_assist_box.tools.chroma_collection_selector import EmptyCollectionError, discover_collections, select_collection


class Collection:
    name = "empty"
    metadata = {}

    def count(self):
        return 0

    def peek(self, limit):
        return {"metadatas": [], "embeddings": []}


class Client:
    collection = Collection()

    def list_collections(self):
        return [self.collection]

    def get_collection(self, name):
        return self.collection


def test_empty_collection_rejected():
    client = Client()
    with pytest.raises(EmptyCollectionError, match="empty"):
        select_collection(client, discover_collections(client), kind="text")
