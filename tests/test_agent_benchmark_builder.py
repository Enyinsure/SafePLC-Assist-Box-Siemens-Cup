from scripts.build_agent_benchmark_from_bundle import build_benchmark


def test_benchmark_builder_writes_manifest(tmp_path):
    manifest = build_benchmark(tmp_path)
    assert manifest["total_cases"] == sum(manifest["suite_counts"].values())
    assert (tmp_path / "supervisor_routing.jsonl").exists()

