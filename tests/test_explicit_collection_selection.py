import pytest

from safeplc_assist_box.tools.chroma_collection_selector import CollectionSelectionError, discover_collections, select_collection


class Collection:
    metadata = {}

    def __init__(self, name):
        self.name = name

    def count(self):
        return 2

    def peek(self, limit):
        return {"metadatas": [], "embeddings": [[0.0]]}


class Client:
    def __init__(self):
        self.items = {name: Collection(name) for name in ("a", "b")}

    def list_collections(self):
        return list(self.items.values())

    def get_collection(self, name):
        return self.items[name]


def test_explicit_collection_selection():
    client = Client()
    name, _, _ = select_collection(client, discover_collections(client), explicit_name="b", kind="figure")
    assert name == "b"
    with pytest.raises(CollectionSelectionError, match="Available"):
        select_collection(client, discover_collections(client), explicit_name="missing", kind="figure")
