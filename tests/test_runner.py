import json

import pytest

from b2b_agent_skills import MockProvider, run_skill
from b2b_agent_skills.errors import SkillOutputError
from b2b_agent_skills.providers import Completion, Provider
from b2b_agent_skills.registry import get_skill, list_skills
from b2b_agent_skills.runner import build_system_prompt
from b2b_agent_skills.validation import extract_json, validate_output


class ScriptedProvider(Provider):
    """Returns queued responses in order and records every call."""

    name = "scripted"

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def complete(self, *, system, user, schema, skill):
        self.calls.append({"system": system, "user": user, "schema": schema, "skill": skill})
        return Completion(text=self.responses.pop(0), model="scripted", usage={"input_tokens": 10, "output_tokens": 5})


@pytest.mark.parametrize("slug", list_skills())
def test_every_skill_runs_end_to_end_on_the_mock(slug):
    result = run_skill(slug, {"note": "smoke"}, provider=MockProvider())
    assert result.valid, result.errors
    assert set(result.output) == set(get_skill(slug).output_fields)


def test_input_can_be_a_file_path(tmp_path):
    path = tmp_path / "in.json"
    path.write_text(json.dumps({"account_id": "acct_1"}))
    assert run_skill("renewal_risk_scorer", path, provider=MockProvider()).valid


def test_prompt_contains_instructions_schema_and_input():
    provider = ScriptedProvider(json.dumps(get_skill("deal-risk-assessor").example_output))
    run_skill("deal-risk-assessor", {"deal_id": "opp_42"}, provider=provider)
    call = provider.calls[0]
    assert "MEDDPICC" in call["system"]
    assert '"single_point_of_failure"' in call["system"]
    assert '"opp_42"' in call["user"]
    assert call["schema"]["required"][0] == "deal_id"
    assert "examples" not in call["schema"]


def test_system_prompt_is_stable_for_caching():
    skill = get_skill("pipeline-health-monitor")
    assert build_system_prompt(skill) == build_system_prompt(skill)


def test_fenced_json_is_parsed():
    example = get_skill("competitor-monitor").example_output
    provider = ScriptedProvider("Here is the analysis:\n```json\n" + json.dumps(example) + "\n```")
    assert run_skill("competitor-monitor", {"x": 1}, provider=provider).output == example


def test_invalid_output_is_retried_with_feedback_then_succeeds():
    good = get_skill("forecast-bias-detector").example_output
    bad = {k: v for k, v in good.items() if k != "classification"}
    provider = ScriptedProvider(json.dumps(bad), json.dumps(good))
    result = run_skill("forecast-bias-detector", {"rep_id": "r"}, provider=provider)
    assert result.valid and result.attempts == 2
    assert "classification" in provider.calls[1]["user"]
    assert result.usage == {"input_tokens": 20, "output_tokens": 10}


def test_persistently_invalid_output_raises():
    provider = ScriptedProvider("not json", "still not json")
    with pytest.raises(SkillOutputError) as exc:
        run_skill("forecast-bias-detector", {"rep_id": "r"}, provider=provider)
    assert exc.value.result.attempts == 2
    assert not exc.value.result.valid


def test_raise_on_invalid_false_returns_result():
    provider = ScriptedProvider("{}", "{}")
    result = run_skill("forecast-bias-detector", {"rep_id": "r"}, provider=provider, raise_on_invalid=False)
    assert not result.valid and any("classification" in e for e in result.errors)


def test_empty_input_is_rejected_for_real_providers():
    with pytest.raises(ValueError, match="No input data"):
        run_skill("deal-risk-assessor", {}, provider=ScriptedProvider("{}"))


def test_working_then_final_fenced_answer_is_parsed():
    text = 'Working: score = {3+1}\n```json\n{"draft": true}\n```\nFinal:\n```json\n{"a": 2}\n```'
    assert extract_json(text) == {"a": 2}


def test_contract_asks_for_working_then_a_final_json_block():
    system = build_system_prompt(get_skill("pipeline-health-monitor"))
    assert "step by step" in system and "```json" in system


def test_extract_json_and_validate_helpers():
    assert extract_json('{"a": 1}') == {"a": 1}
    assert extract_json('noise {"a": 1} trailing') == {"a": 1}
    with pytest.raises(ValueError):
        extract_json("no json here")
    schema = {"type": "object", "properties": {"a": {"type": "number"}}, "required": ["a"], "additionalProperties": False}
    assert validate_output(schema, {"a": 1}) == []
    assert validate_output(schema, {"a": "x", "b": 2})
