"""v0.3: input schemas, stages, free-text extraction, workspace, init, playbooks."""

import json

import pytest

from b2b_agent_skills import MockProvider, get_skill, list_skills
from b2b_agent_skills.cli import main
from b2b_agent_skills.extraction import extract_inputs, quote_in_source
from b2b_agent_skills.init_wizard import create_workspace, render_company_md
from b2b_agent_skills.playbooks import list_playbooks, load_playbook, run_playbook
from b2b_agent_skills.providers import Completion, Provider
from b2b_agent_skills.runner import build_system_prompt, build_user_prompt
from b2b_agent_skills.transcripts import read_notes
from b2b_agent_skills.workspace import find_workspace

NOTES = """Priya (VP RevOps): I'm sponsoring this evaluation and set up our internal review for Tuesday.
Tom: I think Martin, the CFO, probably signs anything over $50K, but I'm not sure.
Priya: the price is more than we budgeted for."""


class Scripted(Provider):
    name = "scripted"

    def __init__(self, by_skill):
        self.by_skill = by_skill
        self.calls = []

    def complete(self, *, system, user, schema, skill):
        self.calls.append({"skill": skill, "system": system, "user": user})
        value = self.by_skill.get(skill)
        if value is None:
            from b2b_agent_skills.providers import MockProvider

            return MockProvider().complete(system=system, user=user, schema=schema, skill=skill)
        text = value if isinstance(value, str) else "working...\n```json\n" + json.dumps(value) + "\n```"
        return Completion(text=text, model="scripted")


@pytest.mark.parametrize("slug", list_skills())
def test_every_skill_has_documented_inputs_and_a_stage(slug):
    skill = get_skill(slug)
    assert skill.input_fields, f"{slug}: no input fields generated from its README"
    assert skill.stage in {"early", "growth", "scale"}


def test_stage_split_and_list_filter(capsys):
    assert main(["list", "--stage", "early"]) == 0
    early = capsys.readouterr().out.split()
    assert "deal-risk-assessor" in early and "forecast-bias-detector" not in early


def test_contract_has_small_sample_rule_and_context_goes_in_user_message():
    assert "provisional (n=8)" in build_system_prompt(get_skill("icp-refinement-agent"))
    user = build_user_prompt({"a": 1}, context="We sell to fintech.")
    assert user.index("Company context") < user.index("Input data") and "fintech" in user


def test_quote_matching_is_normalized_but_strict():
    assert quote_in_source("Martin, the CFO, probably signs", NOTES)
    assert quote_in_source("“I’m sponsoring this evaluation”", NOTES.replace("I'm", "I’m"))
    assert not quote_in_source("Martin confirmed he signs", NOTES)


def test_extraction_drops_unverified_values_and_asks_instead():
    provider = Scripted(
        {
            "deal-risk-assessor:extract": {
                "input": {
                    "deal_id": "acme",
                    "pillar_evidence": {
                        "champion": "VP RevOps sponsoring, set up internal review",
                        "economic_buyer": "CFO confirmed he signs",
                    },
                },
                "evidence": [
                    {"field": "pillar_evidence.champion", "quote": "I'm sponsoring this evaluation"},
                    {"field": "pillar_evidence.economic_buyer", "quote": "Martin confirmed he will sign"},
                ],
                "missing": [{"field": "pillar_evidence.paper_process", "question": "Who handles legal review?"}],
            }
        }
    )
    ex = extract_inputs("deal-risk-assessor", NOTES, provider=provider)
    assert ex.input == {"pillar_evidence": {"champion": "VP RevOps sponsoring, set up internal review"}}
    assert set(ex.dropped) == {"deal_id", "pillar_evidence.economic_buyer"}
    assert {m["field"] for m in ex.missing} >= {"pillar_evidence.paper_process", "pillar_evidence.economic_buyer", "deal_id"}
    assert "verbatim" in provider.calls[0]["system"]


def test_extraction_keeps_user_answers():
    provider = Scripted(
        {"deal-risk-assessor:extract": {"input": {}, "evidence": [], "missing": [{"field": "deal_id", "question": "Deal name?"}]}}
    )
    ex = extract_inputs("deal-risk-assessor", NOTES, provider=provider, known={"deal_id": "acme-q4"})
    assert ex.input["deal_id"] == "acme-q4" and not any(m["field"] == "deal_id" for m in ex.missing)


def test_read_notes_strips_subtitle_timing(tmp_path):
    vtt = tmp_path / "call.vtt"
    vtt.write_text("WEBVTT\n\n1\n00:00:01.000 --> 00:00:03.000\n<v Priya>We need this live by Q1.</v>\n")
    assert read_notes(vtt) == "Priya: We need this live by Q1."
    js = tmp_path / "call.json"
    js.write_text(json.dumps({"transcript": [{"speaker": "Tom", "text": "Budget is tight."}]}))
    assert read_notes(js) == "Tom: Budget is tight."


def test_init_creates_workspace_and_refuses_to_overwrite(tmp_path):
    answers = {"company": "Acme Analytics", "product": "Forecast risk scoring for B2B sales teams"}
    info = create_workspace(tmp_path / "ws", answers=answers)
    root = tmp_path / "ws"
    assert info["answered"] == 2
    assert "# Acme Analytics" in (root / "company.md").read_text()
    assert "Draft emails, never send them" in (root / "CLAUDE.md").read_text()
    assert json.loads((root / ".mcp.json").read_text())["mcpServers"]["b2b-agent-skills"]["args"] == ["mcp"]
    assert (root / "gtm" / "deals").is_dir()
    assert find_workspace(root / "gtm" / "deals").root == root
    with pytest.raises(FileExistsError):
        create_workspace(root, answers=answers)


def test_company_md_marks_website_drafts():
    md = render_company_md({"company": "X", "product": "drafted"}, drafted={"product"})
    assert "What we sell *(from website, verify)*" in md


def test_cli_init_noninteractive(tmp_path, capsys):
    assert main(["init", str(tmp_path / "w"), "--yes"]) == 0
    assert (tmp_path / "w" / "company.md").exists()


def test_call_debrief_playbook_is_well_formed():
    assert "call-debrief" in list_playbooks()
    spec = load_playbook("call-debrief")
    for step in spec["steps"]:
        assert step["skill"] in list_skills()
    assert spec["report"]["headings"][0] == "Verdict"


def test_playbook_runs_end_to_end_offline_and_saves_to_workspace(tmp_path):
    create_workspace(tmp_path, answers={"company": "Acme Analytics"})
    ws = find_workspace(tmp_path)
    result = run_playbook("call-debrief", NOTES, provider=MockProvider(), workspace=ws, subject="Acme Logistics")
    assert result.steps["risk"].status == "ok"
    assert result.steps["objection"].status == "skipped", "mock extraction finds no objection_text"
    assert "## Verdict" in result.report and "## Draft follow-up email" in result.report
    assert result.saved_to == "gtm/deals/acme-logistics.md"
    assert "## Call debrief" in (tmp_path / result.saved_to).read_text()
    runs = list((tmp_path / "gtm" / "runs").glob("*.jsonl"))
    assert runs and json.loads(runs[0].read_text().splitlines()[-1])["playbook"] == "call-debrief"


def test_playbook_uses_company_context_and_extracted_inputs(tmp_path):
    create_workspace(tmp_path, answers={"company": "Acme Analytics", "product": "forecast risk scoring"})
    provider = Scripted(
        {
            "objection-response-coach:extract": {
                "input": {"objection_text": "the price is more than we budgeted for"},
                "evidence": [{"field": "objection_text", "quote": "the price is more than we budgeted for"}],
                "missing": [],
            },
        }
    )
    result = run_playbook("call-debrief", NOTES, provider=provider, workspace=find_workspace(tmp_path), save=False)
    assert result.steps["objection"].status == "ok"
    skill_calls = [c for c in provider.calls if c["skill"] == "objection-response-coach"]
    assert "forecast risk scoring" in skill_calls[0]["user"], "company context reaches the skill"
    assert "the price is more than we budgeted for" in skill_calls[0]["user"]


def test_playbook_golden_suite_is_well_formed():
    from b2b_agent_skills.evaluation import load_playbook_golden

    suites = load_playbook_golden()
    assert {s["playbook"] for s in suites} == set(list_playbooks())
    inputs = {"notes": "notes", "list": "rows", "icp": "customers", "review": "deals"}
    for s in suites:
        kind = load_playbook(s["playbook"])["kind"]
        for c in s["cases"]:
            assert c[inputs[kind]] and c["assertions"]


def test_cli_playbook_list(capsys):
    assert main(["playbook", "list"]) == 0
    assert "call-debrief" in capsys.readouterr().out


def test_consistency_problems_catch_contradictions():
    from b2b_agent_skills.playbooks import StepResult, consistency_problems

    steps = {
        "risk": StepResult("risk", "deal-risk-assessor", "ok", output={"total_score": 12}),
        "stakeholders": StepResult("stakeholders", "stakeholder-map-builder", "ok", output={"single_threading_risk": False}),
    }
    assert consistency_problems("## Verdict\n12/24, high. Single-threading risk: no.", steps) == []
    problems = consistency_problems("## Verdict\n10/40. Single-threading risk: yes", steps)
    assert (
        any("out of 24" in p for p in problems) and any("single-threading" in p for p in problems) and any("12/24" in p for p in problems)
    )
    assert consistency_problems("8/24", steps) == ["the MEDDPICC total is 12/24 (the report says 8/24)"]


def test_playbook_retries_when_report_contradicts_skills(tmp_path):
    from b2b_agent_skills.providers import Completion

    class Contradicts(Scripted):
        reports = 0

        def complete(self, *, system, user, schema, skill):
            if skill.endswith(":report"):
                Contradicts.reports += 1
                st = "yes" if Contradicts.reports == 1 else "no"
                body = "\n\n".join(
                    f"## {h}\n\nx"
                    for h in ["Verdict", "Next 3 actions", "Missing evidence", "Stakeholders", "Objection", "Draft follow-up email"]
                )
                return Completion(text=body.replace("## Verdict\n\nx", f"## Verdict\n\n14/24. Single-threading risk: {st}."), model="x")
            return super().complete(system=system, user=user, schema=schema, skill=skill)

    provider = Contradicts(
        {"stakeholder-map-builder": {**get_skill("stakeholder-map-builder").example_output, "single_threading_risk": False}}
    )
    result = run_playbook("call-debrief", NOTES, provider=provider, save=False)
    assert Contradicts.reports == 2 and "Single-threading risk: no" in result.report


def test_unsupported_generalizations_are_detected():
    from b2b_agent_skills.playbooks import unsupported_claims

    bad = "Most mid-market sales teams can't run Clari. Customers tell us it's slow. Teams we talk to agree."
    assert unsupported_claims(bad) == ["Customers tell us", "Most mid-market sales teams", "we talk to"]
    assert unsupported_claims("Ana, how do you flag at-risk deals today? Most of the pipeline is in Proposal.") == []
