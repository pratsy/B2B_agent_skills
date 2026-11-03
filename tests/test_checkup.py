"""GTM checkup: answers parsing, rubric scoring in code, area combination, CLI."""

import json

from b2b_agent_skills import MockProvider
from b2b_agent_skills.checkup import (
    AREAS,
    answers_text,
    parse_answers,
    run_checkup,
    score_founder_area,
    score_website_area,
)
from b2b_agent_skills.cli import main
from b2b_agent_skills.evaluation import _run_playbook_case, load_playbook_golden

PAGE = """The all-in-one revenue platform.
Our platform empowers revenue teams to unlock their full potential with AI-powered insights.
Real-time CRM sync · Explainable AI risk scoring · No-code rule builder · 15-minute setup. Book a demo today and see it live."""
ANSWERS = {
    "q2": "Mid-market fintech companies, the VP Sales buys after a forecast miss in front of the board.",
    "q3": "Two agencies who never set it up.",
    "q4": "Mostly from my network and a few LinkedIn posts.",
    "q5": "I run every call, no set process.",
    "q7": "$500/month flat, I discount for almost everyone.",
    "q8": "11 of 12 renewed.",
    "q9": "Maybe $40K, target is $60K this quarter.",
}


def test_parse_answers_formats():
    assert parse_answers('{"q1": "Seed", "2": "Fintech"}') == {"q1": "Seed", "q2": "Fintech"}
    assert parse_answers('["Seed", "", "Agencies"]') == {"q1": "Seed", "q3": "Agencies"}
    text = "1. Seed, 12 customers\nQ2: Fintech VPs\n  who had a forecast miss\nquestion 4) my network"
    assert parse_answers(text) == {"q1": "Seed, 12 customers", "q2": "Fintech VPs who had a forecast miss", "q4": "my network"}
    assert "Q2. Who are your best customers" in answers_text({"q2": "Fintech"}) and "Q1." not in answers_text({"q2": "Fintech"})


def test_founder_scoring_unknown_vs_zero_and_rescaling():
    source = answers_text(ANSWERS)
    score, checked = score_founder_area("sales_motion", [], source)
    assert score is None, "no answered criteria means unknown, not 0"
    items = [
        {"criterion": "defined_process", "points": 0, "evidence": "I run every call, no set process"},
        {"criterion": "metrics_known", "points": 20, "evidence": "maybe a third"},  # not in these answers -> unanswered
        {"criterion": "qualification", "points": 30, "evidence": ""},
    ]
    score, checked = score_founder_area("sales_motion", items, source)
    assert score == 0.0 and [c.get("unanswered", False) for c in checked] == [False, True, True]
    items = [
        {"criterion": "retention", "points": 37, "evidence": "11 of 12 renewed"},
        {"criterion": "pull_signals", "points": 15, "evidence": "invented: customers keep referring us"},
    ]
    score, checked = score_founder_area("pmf", items, source)
    assert checked[0]["points"] == 20, "points snap down to an allowed rubric value (37 -> 20)"
    assert score == 50.0, "20 of 40 answered points; the unverified criterion doesn't count"


def test_website_scoring_zeroes_unquoted_points():
    items = [
        {"criterion": "swap_test", "points": 40, "evidence": "Only we flag deals two weeks early"},
        {"criterion": "differentiators_specific", "points": 30, "evidence": "Explainable AI risk scoring"},
    ]
    score, checked = score_website_area("differentiation", items, PAGE)
    assert score == 30.0 and checked[0]["points"] == 0 and checked[0]["evidence"] == ""


def test_checkup_offline_combines_answers_and_website(tmp_path):
    result = run_checkup("northwind.example", answers=ANSWERS, page_text=PAGE, provider=MockProvider())
    areas = {a.key: a for a in result.areas}
    assert [a.key for a in result.areas] == [k for k, *_ in AREAS]
    assert areas["icp"].sources == ["your answers", "website"]
    assert areas["proof"].score == 0 and areas["positioning"].sources == ["website"]
    assert areas["pmf"].score is not None and areas["demand"].score is not None
    assert result.scored == 8 and len(result.fixes) == 3
    assert result.fixes[0]["area"] in {a.name for a in result.areas}
    assert "## Top 3 fixes" in result.report and "GTM score" in result.report


def test_checkup_answers_only_marks_the_rest_unknown():
    result = run_checkup(answers={"q8": "11 of 12 renewed."}, provider=MockProvider())
    areas = {a.key: a for a in result.areas}
    assert areas["pmf"].score == 60.0, "one answered criterion is capped at 60"
    assert areas["pmf"].finding.startswith("provisional (1 of 3 criteria answered")
    assert areas["positioning"].band == "unknown" and "website" in areas["positioning"].unlock
    assert areas["pricing"].band == "unknown" and "question 7" in areas["pricing"].unlock
    assert "## Unlock the rest" in result.report


def test_checkup_needs_some_input():
    import pytest

    from b2b_agent_skills.errors import SkillsError

    with pytest.raises(SkillsError, match="something to work with"):
        run_checkup(provider=MockProvider())
    with pytest.raises(SkillsError, match="--text"):
        run_checkup("spa.example", page_text="<div id=root></div>", provider=MockProvider())


def test_cli_checkup_with_answers_file(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("PROVIDER", raising=False)
    answers = tmp_path / "answers.json"
    answers.write_text(json.dumps(ANSWERS))
    page = tmp_path / "home.txt"
    page.write_text(PAGE)
    assert main(["checkup", "northwind.example", "--text", str(page), "--answers", str(answers), "--no-questions"]) == 0
    out = capsys.readouterr().out
    assert "GTM checkup: northwind.example" in out and "| Sales motion | Head of Sales |" in out
    assert main(["checkup", "--answers", str(answers), "--no-questions", "--brief"]) == 0
    assert "## Evidence" not in capsys.readouterr().out


def test_checkup_golden_unknowns_pass_offline():
    suite = next(s for s in load_playbook_golden() if s["playbook"] == "checkup")
    case = suite["cases"][1]
    offline = {
        **case,
        "assertions": [
            a
            for a in case["assertions"]
            if a["path"].endswith((".band", ".unlock")) and "demand" not in a["path"] and "pmf" not in a["path"]
        ],
    }
    result, _ = _run_playbook_case("checkup", offline, MockProvider())
    assert result.passed, result.failures


def test_website_only_gets_a_website_score_not_a_gtm_score():
    result = run_checkup("northwind.example", page_text=PAGE, provider=MockProvider())
    assert result.overall is None
    assert "Website score" in result.report and "This is not your GTM score" in result.report and "**GTM score:" not in result.report


def test_fix_drafts_with_unsupported_numbers_are_dropped():
    from b2b_agent_skills.checkup import numbers_supported

    assert numbers_supported("Used by 50,000 teams", ["Linear powers over 50,000 product teams"])
    assert not numbers_supported("Used by 76k agents and 30% faster", ["Linear powers over 50,000 product teams"])
    assert numbers_supported("Say who it's for", [])
    assert not numbers_supported("Catch at-risk deals two weeks early", ["Flag at-risk deals from your CRM"])
    assert numbers_supported("Set up in two minutes", ["Set up in two minutes"])
    assert not numbers_supported("flags deals two weeks early", ["Two agencies who never set it up."]), (
        "the word after the number must match"
    )


def test_grounded_drops_unsupported_sentences():
    from b2b_agent_skills.checkup import _grounded

    text = "Headline lacks proof. Indistinguishable from 20+ competitors; most startups say this."
    assert _grounded(text, ["The all-in-one revenue platform"]) == "Headline lacks proof."


def test_answered_area_that_comes_back_unknown_is_retried():
    from b2b_agent_skills import get_skill
    from b2b_agent_skills.providers import Completion, Provider

    example = get_skill("gtm-founder-diagnostic").example_output

    class ForgetsPmfOnce(Provider):
        name = "forgets"
        calls = 0

        def complete(self, *, system, user, schema, skill):
            if skill == "gtm-founder-diagnostic":
                ForgetsPmfOnce.calls += 1
                out = json.loads(json.dumps(example))
                if ForgetsPmfOnce.calls == 1:
                    out["pmf"]["items"] = [{"criterion": "retention", "points": 40, "max": 40, "evidence": ""}]
                return Completion(text=json.dumps(out), model="x")
            return MockProvider().complete(system=system, user=user, schema=schema, skill=skill)

    result = run_checkup(answers=ANSWERS, provider=ForgetsPmfOnce())
    assert ForgetsPmfOnce.calls == 2
    assert {a.key: a for a in result.areas}["pmf"].score is not None
