"""v0.4: CSV mapping, fit and lift calculators, score-list, find-icp, batch, run --csv, PMF skill."""

import json

import pytest

from b2b_agent_skills import MockProvider, get_skill
from b2b_agent_skills.calculators import attribute_lifts, fit_score, propose_icp, tier_for
from b2b_agent_skills.cli import main
from b2b_agent_skills.evaluation import _run_playbook_case, load_playbook_golden
from b2b_agent_skills.icp import find_icp
from b2b_agent_skills.init_wizard import create_workspace
from b2b_agent_skills.lists import batch_skill, score_list
from b2b_agent_skills.tables import map_columns, parse_overrides, read_csv, to_number, write_csv
from b2b_agent_skills.workspace import find_workspace

ICP = {
    "industries": ["fintech", "saas"],
    "employee_range": [50, 500],
    "geographies": ["US"],
    "titles": ["vp sales", "revops"],
    "exclude": {"titles": ["intern"]},
}


def test_column_mapping_handles_common_export_headers():
    headers = ["Full Name", "Job Title", "Company Name", "# Employees", "Company Industry", "HQ Country", "Website"]
    m = map_columns(headers)
    assert m == {
        "company": "Company Name",
        "domain": "Website",
        "industry": "Company Industry",
        "employees": "# Employees",
        "geography": "HQ Country",
        "title": "Job Title",
        "name": "Full Name",
    }
    assert map_columns(headers, {"industry": "Website"})["industry"] == "Website"
    with pytest.raises(ValueError, match="no such column"):
        map_columns(headers, {"industry": "Nope"})
    assert parse_overrides(["title=Job Title"]) == {"title": "Job Title"}


@pytest.mark.parametrize(("text", "n"), [("51-200", 125.5), ("1,200", 1200), ("10k", 10000), ("500+", 500), ("", None), ("n/a", None)])
def test_to_number(text, n):
    assert to_number(text) == n


def test_csv_roundtrip_and_semicolon_exports(tmp_path):
    p = tmp_path / "x.csv"
    p.write_text("Name;Title\nAna;VP Sales\n", encoding="utf-8")
    headers, rows = read_csv(p)
    assert headers == ["Name", "Title"] and rows == [{"Name": "Ana", "Title": "VP Sales"}]
    write_csv(tmp_path / "y.csv", [{"a": 1}, {"b": 2}])
    assert read_csv(tmp_path / "y.csv")[0] == ["a", "b"]


def test_fit_score_rules():
    full = fit_score({"industry": "FinTech", "employees": "120", "geography": "US", "title": "VP Sales"}, ICP)
    assert (full.score, full.tier) == (100.0, "A")
    near = fit_score({"industry": "SaaS", "employees": "700", "geography": "US", "title": "VP Sales"}, ICP)
    assert near.score == pytest.approx(86.1), "77.5 of 90 possible points"
    assert near.score and "near range" in " ".join(near.reasons)
    assert fit_score({"industry": "Fintech", "title": "Marketing Intern"}, ICP).tier == "skip"
    sparse = fit_score({"industry": "Fintech"}, ICP)
    assert sparse.score is None and sparse.tier == "unknown" and "company size" in sparse.unknown
    partial = fit_score({"industry": "Fintech", "title": "VP Sales"}, ICP)
    assert partial.score == 100.0 and "geography" in partial.unknown, "missing data is left out, not scored as a mismatch"
    assert [tier_for(x) for x in (95, 70, 45, 10, None)] == ["A", "B", "C", "skip", "unknown"]


def test_lift_and_proposed_icp():
    rows = (
        [{"industry": "fintech", "employees": "120", "outcome": "won"}] * 6
        + [{"industry": "fintech", "employees": "90", "outcome": "lost"}] * 2
        + [{"industry": "retail", "employees": "3000", "outcome": "lost"}] * 8
        + [{"industry": "retail", "employees": "150", "outcome": "won"}]
    )
    lifts = {(a.attribute, a.value): a for a in attribute_lifts(rows)}
    fintech = lifts[("industry", "fintech")]
    assert (fintech.best_with, fintech.best_total, fintech.lift, fintech.confidence) == (6, 7, 1.82, "low")
    assert lifts[("industry", "retail")].signal == "negative"
    icp = propose_icp(list(lifts.values()))
    assert icp["industries"] == ["fintech"] and icp["employee_range"] == [51, 200]
    with pytest.raises(ValueError):
        attribute_lifts([{"industry": "x", "outcome": "won"}])


def _write_leads(tmp_path):
    p = tmp_path / "leads.csv"
    write_csv(
        p,
        [
            {"Name": "Ana", "Job Title": "VP Sales", "Company": "PayFlow", "Industry": "Fintech", "Employees": "120", "Country": "US"},
            {"Name": "Cara", "Job Title": "Intern", "Company": "PayFlow", "Industry": "Fintech", "Employees": "120", "Country": "US"},
            {"Name": "Dev", "Job Title": "CTO", "Company": "BrickMart", "Industry": "Retail", "Employees": "8000", "Country": "India"},
            {"Name": "Fay", "Job Title": "", "Company": "Unknown", "Industry": "", "Employees": "", "Country": ""},
        ],
    )
    return p


def test_score_list_offline_ranks_and_saves(tmp_path):
    create_workspace(tmp_path / "ws", answers={"company": "Acme"})
    ws = find_workspace(tmp_path / "ws")
    result = score_list(_write_leads(tmp_path), ICP, workspace=ws, top=5)
    tiers = {r["Name"]: r["fit_tier"] for r in result.rows}
    assert tiers == {"Ana": "A", "Cara": "skip", "Dev": "skip", "Fay": "unknown"}
    assert result.rows[0]["Name"] == "Ana"
    assert result.saved_report == "gtm/lists/leads.md" and (ws.root / result.saved_report).exists()
    assert read_csv(result.saved_csv)[0][:6] == ["Name", "Job Title", "Company", "Industry", "Employees", "Country"]


def test_score_list_requires_an_icp(tmp_path):
    from b2b_agent_skills.errors import SkillsError

    with pytest.raises(SkillsError, match="no ICP"):
        score_list(_write_leads(tmp_path), {})


def test_cli_score_list_with_icp_file(tmp_path, capsys):
    icp = tmp_path / "icp.json"
    icp.write_text(json.dumps(ICP))
    out = tmp_path / "scored.csv"
    assert main(["playbook", "score-list", "--csv", str(_write_leads(tmp_path)), "--icp", str(icp), "--no-angles", "-o", str(out)]) == 0
    assert "## Top 1" in capsys.readouterr().out and out.exists()


def test_find_icp_offline_proposes_and_applies(tmp_path):
    create_workspace(tmp_path / "ws", answers={"company": "Acme"})
    ws = find_workspace(tmp_path / "ws")
    cust = tmp_path / "customers.csv"
    write_csv(
        cust,
        [{"Industry": "Fintech", "Employees": "120", "Status": "won"}] * 5
        + [{"Industry": "Retail", "Employees": "3000", "Status": "lost"}] * 6,
    )
    result = find_icp(customers_csv=cust, provider=MockProvider(), workspace=ws)
    assert result.proposed_icp["industries"] == ["fintech"]
    assert result.saved["icp"] == "gtm/icp.proposed.json" and not (ws.gtm / "icp.json").exists()
    assert any("provisional (n=5" in n for n in result.notes)
    find_icp(customers_csv=cust, provider=MockProvider(), workspace=ws, apply=True)
    assert json.loads((ws.gtm / "icp.json").read_text())["industries"] == ["fintech"]


def test_find_icp_needs_an_outcome_column(tmp_path):
    from b2b_agent_skills.errors import SkillsError

    cust = tmp_path / "c.csv"
    write_csv(cust, [{"Industry": "Fintech"}])
    with pytest.raises(SkillsError, match="outcome column"):
        find_icp(customers_csv=cust, provider=MockProvider())


def test_batch_maps_columns_to_skill_inputs(tmp_path):
    p = tmp_path / "rows.csv"
    write_csv(p, [{"competitor": "X", "signal_description": "price cut", "overlap_with_icp": "0.5"}] * 2)
    out, mapping = batch_skill("competitor-monitor", p, provider=MockProvider(), output=tmp_path / "out.csv")
    assert mapping["competitor"] == "competitor" and len(out) == 2 and all(r["_valid"] for r in out)
    assert "materiality_score" in read_csv(tmp_path / "out.csv")[0]


def test_run_csv_feeds_list_input(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("PROVIDER", raising=False)
    p = tmp_path / "survey.csv"
    write_csv(p, [{"respondent_id": "1", "disappointment": "very", "segment": "Ops"}])
    assert main(["run", "pmf-survey-analyzer", "--csv", str(p)]) == 0
    assert "pmf_score_pct" in capsys.readouterr().out


def test_pmf_skill_is_complete():
    skill = get_skill("pmf-survey-analyzer")
    assert skill.stage == "early" and "responses" in skill.input_fields and "pmf_score_pct" in skill.output_fields


@pytest.mark.parametrize("playbook", ["score-list", "find-icp"])
def test_deterministic_playbook_goldens_pass_offline(playbook):
    """List scoring and ICP lift are code, so their goldens must pass without a model (report checks excepted)."""
    suite = next(s for s in load_playbook_golden() if s["playbook"] == playbook)
    for case in suite["cases"]:
        offline = {**case, "assertions": [a for a in case["assertions"] if a["path"] != "report" and "opening_line" not in a["path"]]}
        result, _ = _run_playbook_case(playbook, offline, MockProvider())
        assert result.passed, result.failures
