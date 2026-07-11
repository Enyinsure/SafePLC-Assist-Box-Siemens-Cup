import pytest

from safeplc_assist_box.tools.chroma_collection_selector import AmbiguousCollectionError, discover_collections, select_collection


class Collection:
    metadata = {}

    def __init__(self, name):
        self.name = name

    def count(self):
        return 2

    def peek(self, limit):
        return {"metadatas": [], "embeddings": [[0.0, 0.0]]}


class Client:
    def __init__(self):
        self.items = {name: Collection(name) for name in ("a", "b")}

    def list_collections(self):
        return list(self.items.values())

    def get_collection(self, name):
        return self.items[name]


def test_ambiguous_collection_requires_config():
    client = Client()
    with pytest.raises(AmbiguousCollectionError, match="a.*b"):
        select_collection(client, discover_collections(client), kind="text")
