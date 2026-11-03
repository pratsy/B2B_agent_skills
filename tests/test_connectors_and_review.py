"""v0.5: HubSpot connector, approvals, Slack, transcript inbox, monday-review, outcomes, webhook."""

import datetime as dt
import json

import pytest

from b2b_agent_skills import MockProvider
from b2b_agent_skills.approvals import approve, describe, pending, propose, record_outcome, reject
from b2b_agent_skills.cli import main
from b2b_agent_skills.connectors.hubspot import HubSpot
from b2b_agent_skills.errors import SkillsError
from b2b_agent_skills.evaluation import _run_playbook_case, load_playbook_golden
from b2b_agent_skills.inbox import process_inbox, subject_from_filename
from b2b_agent_skills.init_wizard import create_workspace
from b2b_agent_skills.notify import markdown_to_slack, post_slack
from b2b_agent_skills.review import code_flags, deals_from_csv, monday_review
from b2b_agent_skills.tables import write_csv
from b2b_agent_skills.workspace import find_workspace


@pytest.fixture
def ws(tmp_path):
    create_workspace(tmp_path / "ws", answers={"company": "Acme"})
    return find_workspace(tmp_path / "ws")


class FakeHubSpot:
    """Answers the HubSpot endpoints the connector uses, and records every call."""

    def __init__(self):
        self.calls = []

    def __call__(self, method, url, headers, body):
        path = url.replace("https://api.hubapi.com", "")
        payload = json.loads(body) if body else None
        self.calls.append((method, path, payload, headers))
        if path == "/crm/v3/objects/deals/search":
            if payload.get("after"):
                return 200, json.dumps({"results": [self._deal("2", "Beta renewal")]}).encode()
            return 200, json.dumps({"results": [self._deal("1", "Acme expansion")], "paging": {"next": {"after": "abc"}}}).encode()
        if path == "/crm/v4/associations/deals/companies/batch/read":
            return 200, json.dumps({"results": [{"from": {"id": "1"}, "to": [{"toObjectId": 77}]}]}).encode()
        if path == "/crm/v3/objects/companies/batch/read":
            return 200, json.dumps({"results": [{"id": "77", "properties": {"name": "Acme Corp"}}]}).encode()
        if path.startswith("/crm/v3/objects/deals/") and method == "PATCH":
            return (404, b'{"message": "deal not found"}') if path.endswith("/404") else (200, b'{"id": "1"}')
        if path == "/crm/v3/properties/deals" and method == "GET":
            return 200, json.dumps({"results": [{"name": "b2b_risk_band"}]}).encode()
        if path == "/crm/v3/properties/deals" and method == "POST":
            return 201, b"{}"
        return 404, b'{"message": "unexpected"}'

    @staticmethod
    def _deal(i, name):
        return {
            "id": i,
            "properties": {
                "dealname": name,
                "amount": "1000",
                "dealstage": "proposal",
                "closedate": "2026-12-01T00:00:00Z",
                "hs_lastmodifieddate": "2026-11-01T10:00:00Z",
                "hs_v2_date_entered_current_stage": "2026-10-01T00:00:00Z",
            },
        }


def test_hubspot_reads_open_deals_with_paging_and_companies():
    fake = FakeHubSpot()
    deals = HubSpot("tok", transport=fake).open_deals()
    assert [d["deal_name"] for d in deals] == ["Acme expansion", "Beta renewal"]
    assert deals[0]["company"] == "Acme Corp" and deals[1]["company"] == ""
    assert deals[0]["close_date"] == "2026-12-01" and deals[0]["source"] == "hubspot" and deals[0]["days_in_stage"] >= 0
    search = fake.calls[0]
    assert search[2]["filterGroups"][0]["filters"][0] == {"propertyName": "hs_is_closed", "operator": "NEQ", "value": "true"}
    assert search[3]["Authorization"] == "Bearer tok"


def test_hubspot_update_setup_and_errors(monkeypatch):
    fake = FakeHubSpot()
    hs = HubSpot("tok", transport=fake)
    hs.update_deal("1", {"b2b_risk_band": "high"})
    assert fake.calls[-1][:3] == ("PATCH", "/crm/v3/objects/deals/1", {"properties": {"b2b_risk_band": "high"}})
    assert hs.ensure_writeback_properties() == ["b2b_meddpicc_score", "b2b_next_action", "b2b_last_review"]
    with pytest.raises(SkillsError, match="deal not found"):
        hs.update_deal("404", {"x": 1})
    monkeypatch.delenv("HUBSPOT_ACCESS_TOKEN", raising=False)
    with pytest.raises(SkillsError, match="HUBSPOT_ACCESS_TOKEN"):
        HubSpot()


def test_approval_flow(ws):
    a = propose(ws, target="hubspot", object_type="deal", object_id="1", label="Acme", changes={"b2b_risk_band": "high"}, reason="review")
    b = propose(ws, target="hubspot", object_type="deal", object_id="404", label="Ghost", changes={"x": 1}, reason="review")
    assert {c["id"] for c in pending(ws)} == {a["id"], b["id"]}
    assert "b2b_risk_band = 'high'" in describe(a)

    applied = []
    dry = approve(ws, "all", {"hubspot": applied.append}, dry_run=True)
    assert {r["status"] for r in dry} == {"would apply"} and not applied and len(pending(ws)) == 2

    def apply(change):
        if change["object_id"] == "404":
            raise SkillsError("deal not found")
        applied.append(change["object_id"])

    results = {r["label"]: r["status"] for r in approve(ws, "all", {"hubspot": apply})}
    assert results == {"Acme": "applied", "Ghost": "failed"}
    assert applied == ["1"] and [c["label"] for c in pending(ws)] == ["Ghost"], "failed changes stay pending"
    assert (ws.gtm / "applied" / f"{a['id']}.json").exists()
    reject(ws, b["id"])
    assert not pending(ws) and (ws.gtm / "rejected" / f"{b['id']}.json").exists()
    with pytest.raises(SkillsError):
        approve(ws, "nope", {})


def test_slack_formatting_and_post(monkeypatch):
    assert markdown_to_slack("## Verdict\n**High** risk, see [deal](https://x)") == "*Verdict*\n*High* risk, see <https://x|deal>"
    sent = []
    post_slack("## Hi", webhook="https://hooks.slack.test/x", send=lambda u, b: sent.append((u, json.loads(b))) or 200)
    assert sent == [("https://hooks.slack.test/x", {"text": "*Hi*"})]
    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
    with pytest.raises(SkillsError, match="SLACK_WEBHOOK_URL"):
        post_slack("x")


@pytest.mark.parametrize(
    ("name", "subject"),
    [("acme-logistics-2026-11-03.vtt", "acme logistics"), ("Brightline_call.txt", "Brightline"), ("cobalt.md", "cobalt")],
)
def test_subject_from_filename(tmp_path, name, subject):
    assert subject_from_filename(tmp_path / name) == subject


def test_inbox_debriefs_and_moves_files(ws):
    (ws.gtm / "inbox" / "acme-logistics-2026-11-03.txt").write_text("Priya: we need this live by Q1.")
    (ws.gtm / "inbox" / "ignore.pdf").write_text("x")
    items = process_inbox(ws, MockProvider())
    assert [i.subject for i in items] == ["acme logistics"] and items[0].error is None
    assert (ws.gtm / "deals" / "acme-logistics.md").exists()
    assert (ws.gtm / "inbox" / "processed" / "acme-logistics-2026-11-03.txt").exists()
    assert (ws.gtm / "inbox" / "ignore.pdf").exists()


def test_code_flags():
    today = dt.date(2026, 11, 9)
    flags = code_flags({"close_date": "2026-10-31", "last_activity": "10/01/2026", "days_in_stage": "60", "stage": "Negotiation"}, today)
    assert flags == ["close date passed (2026-10-31)", "no activity for 39 days", "60 days in stage Negotiation"]
    assert code_flags({"close_date": "2027-01-01", "last_activity": "2026-11-08"}, today) == []


def test_deals_from_csv_maps_crm_headers(tmp_path):
    p = tmp_path / "pipe.csv"
    write_csv(
        p,
        [
            {
                "Deal Name": "Acme",
                "Amount": "100",
                "Deal Stage": "Proposal",
                "Close Date": "2026-12-01",
                "Last Activity Date": "2026-11-01",
                "Deal Owner": "Sam",
            }
        ],
    )
    d = deals_from_csv(p)[0]
    assert (d["deal_name"], d["amount"], d["stage"], d["close_date"], d["last_activity"], d["owner"], d["source"]) == (
        "Acme",
        "100",
        "Proposal",
        "2026-12-01",
        "2026-11-01",
        "Sam",
        "csv",
    )


def test_monday_review_offline_proposes_hubspot_writebacks(ws):
    (ws.gtm / "deals" / "acme-expansion.md").write_text("Priya: I'm sponsoring this. Tom: the CFO probably signs.")
    deals = [
        {
            "deal_id": "1",
            "deal_name": "Acme expansion",
            "amount": "1000",
            "close_date": "2026-12-01",
            "last_activity": "2026-11-05",
            "source": "hubspot",
        },
        {
            "deal_id": "2",
            "deal_name": "Beta renewal",
            "amount": "500",
            "close_date": "2026-10-01",
            "last_activity": "2026-09-01",
            "source": "hubspot",
        },
    ]
    result = monday_review(deals, provider=MockProvider(), workspace=ws, propose_writebacks=True, today=dt.date(2026, 11, 9))
    by = {r.deal["deal_name"]: r for r in result.deals}
    assert by["Acme expansion"].risk is not None and by["Acme expansion"].notes_file == "gtm/deals/acme-expansion.md"
    assert "no evidence on file (no debrief notes)" in by["Beta renewal"].flags
    assert result.saved_to == "gtm/reviews/2026-11-09.md" and "## This week's focus" in result.report
    assert [c["object_id"] for c in result.proposed] == ["1"], "only deals scored from evidence get write-backs"
    assert set(result.proposed[0]["changes"]) == {"b2b_risk_band", "b2b_meddpicc_score", "b2b_next_action", "b2b_last_review"}


def test_monday_review_golden_flags_pass_offline():
    suite = next(s for s in load_playbook_golden() if s["playbook"] == "monday-review")
    case = suite["cases"][0]
    offline = {**case, "assertions": [a for a in case["assertions"] if a["path"] != "report" and ".risk." not in a["path"]]}
    result, _ = _run_playbook_case("monday-review", offline, MockProvider())
    assert result.passed, result.failures


def test_outcome_and_pending_cli(ws, monkeypatch, capsys):
    monkeypatch.chdir(ws.root)
    assert main(["outcome", "Acme Logistics", "won", "--value", "48000", "--reason", "CFO bought in"]) == 0
    assert "Acme Logistics,won,48000.0,CFO bought in" in (ws.gtm / "outcomes.csv").read_text()
    record_outcome(ws, "Beta", "lost")
    assert main(["pending"]) == 0 and "Nothing pending." in capsys.readouterr().out


def test_init_writes_weekly_workflow(ws):
    wf = (ws.root / ".github" / "workflows" / "gtm-weekly.yml").read_text()
    assert "CLAUDE_CODE_OAUTH_TOKEN" in wf and "b2b-skills inbox" in wf and "monday-review" in wf
    assert (ws.gtm / "inbox").is_dir()


def test_webhook_endpoint_runs_a_playbook(ws, monkeypatch):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from b2b_agent_skills.server import create_app

    monkeypatch.setenv("B2B_WORKSPACE", str(ws.root))
    client = TestClient(create_app(token="t", provider=MockProvider()))
    auth = {"Authorization": "Bearer t"}
    res = client.post("/v1/playbooks/call-debrief/run", headers=auth, json={"notes": "Priya: budget is tight.", "subject": "Acme"})
    assert res.status_code == 200 and res.json()["saved_to"] == "gtm/deals/acme.md"
    assert client.post("/v1/playbooks/nope/run", headers=auth, json={"notes": "x"}).status_code == 404
    assert client.post("/v1/playbooks/score-list/run", headers=auth, json={"notes": "x"}).status_code == 422


def test_review_helpers_use_raw_evidence_and_verify_focus_order():
    from b2b_agent_skills.review import _first_focus_item, evidence_text

    deal_file = (
        "## Call debrief\n\nVerdict: critical.\n\n<details><summary>Source notes</summary>\n\nPriya: I'm sponsoring this.\n\n</details>"
    )
    assert evidence_text(deal_file) == "Priya: I'm sponsoring this."
    assert evidence_text("plain notes") == "plain notes"
    assert (
        _first_focus_item("## This week's focus\n\n1. **Brightline** - overdue\n2. Acme\n\n## Deals at risk") == "**Brightline** - overdue"
    )


def test_review_retries_until_focus_order_matches(ws):
    from b2b_agent_skills.providers import Completion, Provider

    class Reorders(Provider):
        name = "reorders"

        def __init__(self):
            self.reports = 0

        def complete(self, *, system, user, schema, skill):
            if skill.endswith(":report"):
                self.reports += 1
                first = "Cobalt" if self.reports == 1 else "Brightline"
                body = f"## This week's focus\n\n1. {first}\n\n## Deals at risk\n\n-\n\n## No evidence on file\n\n-\n\n## Pipeline snapshot\n\n-"
                return Completion(text=body, model="x")
            return MockProvider().complete(system=system, user=user, schema=schema, skill=skill)

    deals = [
        {"deal_name": "Brightline", "close_date": "2026-10-01", "last_activity": "2026-09-01"},
        {"deal_name": "Cobalt", "last_activity": "2026-11-08"},
    ]
    provider = Reorders()
    result = monday_review(deals, provider=provider, workspace=ws, today=dt.date(2026, 11, 9))
    assert provider.reports == 2 and "1. Brightline" in result.report
