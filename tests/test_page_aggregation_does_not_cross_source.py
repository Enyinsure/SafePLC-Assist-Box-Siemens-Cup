from test_same_page_chunk_aggregation import Collection, aggregated_items


class MixedCollection(Collection):
    def get(self, where, include, limit):
        payload = super().get(where, include, limit)
        payload["documents"].append("foreign source text")
        payload["metadatas"].append({"source": "manual-b", "page_no": 6495, "chunk_index": 0})
        return payload


def test_page_aggregation_does_not_cross_source(tmp_path):
    item = aggregated_items(tmp_path, MixedCollection())[0]
    assert "foreign source" not in item.text
    assert item.metadata["aggregated_chunk_count"] == 2
