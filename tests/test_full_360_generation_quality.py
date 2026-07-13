from __future__ import annotations

import copy

from benchmark.generation.build_full_360 import (
    _balanced_brackets,
    _has_figure_location,
    _natural_work_order,
    _scope,
    generated_case_quality_issues,
)
from benchmark.generation.common import CORE_CASES_PATH, sha256_file
from benchmark.generation.validate_full_360 import validate_dataset
from full_360_test_support import build_fixture_dataset, make_seed


def test_generated_answer_queries_have_explicit_complete_identities():
    dataset = build_fixture_dataset()
    seed_by_id = {seed["seed_id"]: seed for seed in dataset["seeds"]}
    generated = dataset["natural"] + dataset["stress"]
    relevant = [
        case
        for case in generated
        if "ANSWER" in case["expected_action"] or case["category"] == "multimodal_missing_or_mismatch"
    ]
    assert relevant
    for case in relevant:
        sources = [seed_by_id[seed_id] for seed_id in case["source_seed_ids"]]
        assert "该模块" not in case["query"]
        assert _balanced_brackets(case["query"])
        assert generated_case_quality_issues(case, sources) == []


def test_quality_checker_rejects_placeholder_unbalanced_and_truncated_queries():
    dataset = build_fixture_dataset()
    case = next(item for item in dataset["natural"] if item["category"] == "parameter")
    seed_by_id = {seed["seed_id"]: seed for seed in dataset["seeds"]}
    sources = [seed_by_id[seed_id] for seed_id in case["source_seed_ids"]]

    broken = copy.deepcopy(case)
    broken["query"] = "该模块（订货号 6ES7517-3AP00-"
    issues = generated_case_quality_issues(broken, sources)
    assert "placeholder_identity_in_query" in issues
    assert "unbalanced_query_brackets" in issues
    assert "truncated_siemens_order_number" in issues
    assert "query_ends_with_partial_alphanumeric_token" in issues


def test_scope_uses_last_breadcrumb_and_never_splits_identity_tokens():
    seed = make_seed(1)
    model = seed["module_model"]
    seed["section"] = "Manual root > Installation > " + ("接口与参数说明，" * 8) + model + "（前视图）后续说明"
    scope = _scope(seed)
    assert "Manual root" not in scope
    assert model in scope
    assert _balanced_brackets(scope)

    order_seed = make_seed(2)
    order_seed["module_model"] = ""
    order_number = order_seed["order_number"]
    order_seed["section"] = "Manual > " + ("供电参数，" * 12) + order_number + "，安装条件"
    order_scope = _scope(order_seed)
    if order_number[:6] in order_scope:
        assert order_number in order_scope
    assert not order_scope.endswith(("-", "/", "(" , "（"))


def test_non_figure_categories_do_not_inherit_seed_figure_requirements():
    dataset = build_fixture_dataset()
    non_figure = {"parameter", "wiring", "troubleshooting", "emc", "compound_multi_agent"}
    cases = [case for case in dataset["natural"] if case["category"] in non_figure]
    assert cases
    assert all(case["required_figure_ids"] == [] for case in cases)
    assert all(case["required_evidence_pages"] == [] for case in cases)
    assert all(case["required_evidence_modalities"] == [] for case in cases)
    figure_cases = [case for case in dataset["natural"] if case["category"] == "figure_location"]
    assert all(case["required_figure_ids"] for case in figure_cases)


def test_parameter_generation_keeps_only_hard_nonempty_constraints():
    dataset = build_fixture_dataset()
    parameter_cases = [case for case in dataset["natural"] if case["category"] == "parameter"]
    assert parameter_cases
    for case in parameter_cases:
        expected = case["required_structured_facts"]["parameter"]
        assert not {"complete", "condition", "parameter_name"} & set(expected)
        assert all(value not in (None, "", []) for value in expected.values())


def test_figure_maintenance_requires_matching_caption_interface_location_and_figure():
    seed = make_seed(1)
    seed["structured_facts"] = {
        "interfaces": ["X1"],
        "ports": [{"interface": "X1", "port_count": 2}],
        "location_markers": {"X1": "⑦"},
        "figure": {"number": seed["figure_id"], "caption": f"{seed['module_model']} 前视图"},
    }
    assert _has_figure_location(seed) is True
    case = _natural_work_order(1, seed)
    assert case["expected_agents"] == ["Figure Agent", "Work-order Agent"]
    assert case["required_figure_ids"] == [seed["figure_id"]]

    mismatched = copy.deepcopy(seed)
    mismatched["structured_facts"]["figure"]["caption"] = "CPU 1518-4 PN/DP 前视图"
    assert _has_figure_location(mismatched) is False

    captionless = copy.deepcopy(seed)
    captionless["structured_facts"]["figure"] = {"number": seed["figure_id"]}
    assert _has_figure_location(captionless) is True


def test_validator_blocks_placeholder_and_inherited_figure_requirement():
    dataset = build_fixture_dataset()
    cases = copy.deepcopy(dataset["full"])
    generated = next(case for case in cases if case.get("benchmark_layer") == "natural" and case["category"] == "parameter")
    generated["query"] = generated["query"].replace(generated["target_model"], "该模块")
    generated["required_figure_ids"] = ["图 BAD"]
    report = validate_dataset(cases, dataset["seeds"], dataset["core"], require_exact_counts=False)
    codes = {item["code"] for item in report["errors"] if item.get("case_id") == generated["case_id"]}
    assert "generated_query_quality_failed" in codes
    assert "non_figure_case_inherits_figure_requirement" in codes


def test_core_cases_and_acceptance_rules_remain_byte_frozen():
    acceptance_path = CORE_CASES_PATH.with_name("acceptance_rules.py")
    assert sha256_file(CORE_CASES_PATH) == "960b49fa349bfe4d165d0cc341252b7180e2d9849ab38ea8aa69d35980337335"
    assert sha256_file(acceptance_path) == "44057f27781ef0aadd5d1eab21bf7ddb1c89dcbc4af0dd41e6ae563ad334ae95"
