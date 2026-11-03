"""Golden eval files are well-formed, and agree with each README's worked example."""

import pytest

from b2b_agent_skills import MockProvider, list_skills, run_golden
from b2b_agent_skills.evaluation import check_assertion, evaluate_case, load_golden, resolve_path

SUITES = load_golden()
CASES = [(s["skill"], c) for s in SUITES for c in s["cases"]]
OPS = {"equals", "approx", "one_of", "contains", "matches", "gte", "lte", "length"}


def test_every_skill_has_a_golden_suite():
    assert {s["skill"] for s in SUITES} == set(list_skills())


@pytest.mark.parametrize(("skill", "case"), CASES, ids=[f"{s}:{c['id']}" for s, c in CASES])
def test_case_is_well_formed(skill, case):
    assert case["id"] and case["description"] and case["input"]
    assert case["assertions"], "a golden case without assertions only checks shape"
    for a in case["assertions"]:
        assert "path" in a and len(OPS & set(a)) == 1, a


@pytest.mark.parametrize(
    ("skill", "case"),
    [(s, c) for s, c in CASES if c.get("readme_example")],
    ids=[f"{s}:{c['id']}" for s, c in CASES if c.get("readme_example")],
)
def test_readme_example_satisfies_its_golden_case(skill, case):
    """The documented worked-example answer must pass the golden assertions.

    If this fails, either the README's example output or the golden case is
    wrong - they describe the same scenario and must agree.
    """
    from b2b_agent_skills import get_skill

    result = evaluate_case(skill, case, get_skill(skill).example_output)
    assert result.passed, result.failures


def test_run_golden_end_to_end_on_mock():
    report = run_golden(MockProvider(), skills=["forecast-bias-detector"])
    assert len(report.cases) == 2
    assert report.cases[0].passed and not report.cases[1].passed
    assert "forecast-bias-detector" in report.to_markdown()
    assert report.to_dict()["total"] == 2


def test_path_resolution():
    data = {"a": {"b": [{"id": "x", "v": 1}, {"id": "y", "v": 2}]}}
    assert resolve_path(data, "a.b[1].v") == 2
    assert resolve_path(data, "a.b[id=x].v") == 1
    assert not check_assertion(data, {"path": "a.c", "equals": 1})[0]


@pytest.mark.parametrize(
    ("actual", "assertion", "ok"),
    [
        ("Best Case", {"equals": "best_case"}, True),
        (14.0, {"equals": 14}, True),
        (0.661, {"approx": 0.66, "tol": 0.01}, True),
        (0.70, {"approx": 0.66, "tol": 0.01}, False),
        ("tier 1", {"one_of": [1, "Tier 1"]}, True),
        (["economic_buyer"], {"contains": "economic_buyer"}, True),
        ("get an Economic-Buyer call", {"matches": "economic.buyer"}, True),
        (5, {"gte": 6}, False),
        ([1, 2], {"length": 2}, True),
        (True, {"approx": 1}, False),
    ],
)
def test_assertion_ops(actual, assertion, ok):
    assert check_assertion({"x": actual}, {"path": "x", **assertion})[0] is ok
