"""Documents for the checkup: recognizing files by content, computing facts in code, and using them as evidence."""

import json
import zipfile
from pathlib import Path

from b2b_agent_skills import MockProvider, get_skill
from b2b_agent_skills.checkup import quote_sources, run_checkup
from b2b_agent_skills.cli import main
from b2b_agent_skills.documents import read_documents, read_xlsx
from b2b_agent_skills.providers import Completion, Provider

DEMO_DOCS = Path(__file__).resolve().parents[1] / "examples" / "demo" / "docs"


def test_demo_documents_are_recognized_and_summarized_in_code():
    docs = read_documents([DEMO_DOCS])
    kinds = {d.name: d.kind for d in docs.docs}
    assert kinds == {"hubspot-deals.csv": "deal export", "leads.csv": "lead sheet", "call-notes-ledgerly.md": "notes"}
    text = docs.evidence_text()
    assert "Win rate on closed deals: 9 of 31 (29%)." in text
    assert "Lead source: Founder referral 41 of 60 (68%), LinkedIn 12 of 60 (20%), Website 7 of 60 (12%)." in text
    assert "Lost reasons: No budget 10 of 22 (45%)" in text
    assert len(docs.open_deals) == 8 and docs.pipeline_name == "hubspot-deals.csv"


def test_survey_customer_list_and_unknown_files(tmp_path):
    (tmp_path / "pmf.csv").write_text(
        "user,answer\n" + "\n".join(f"u{i},{'Very disappointed' if i < 4 else 'Not disappointed'}" for i in range(10)), encoding="utf-8"
    )
    rows = ["company,industry,status"] + [f"A{i},fintech,customer" for i in range(4)] + [f"B{i},agency,prospect" for i in range(4)]
    (tmp_path / "accounts.csv").write_text("\n".join(rows), encoding="utf-8")
    (tmp_path / "logo.png").write_bytes(b"\x89PNG")
    docs = read_documents([tmp_path, tmp_path / "missing.csv"])
    by_name = {d.name: d for d in docs.docs}
    assert by_name["pmf.csv"].kind == "PMF survey" and "Very disappointed: 4 of 10 (40%)." in by_name["pmf.csv"].text
    assert len(docs.survey_rows) == 10
    assert by_name["accounts.csv"].kind == "customer list"
    assert "industry fintech (lift 2.0, 4 of 4 customers)" in by_name["accounts.csv"].text
    assert "Provisional (n=4 customers)." in by_name["accounts.csv"].text
    assert any("logo.png" in s for s in docs.skipped) and any("missing.csv" in s for s in docs.skipped)


def _office(path: Path, members: dict[str, str]) -> Path:
    with zipfile.ZipFile(path, "w") as z:
        for name, xml in members.items():
            z.writestr(name, xml)
    return path


NS_W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
NS_A = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
NS_S = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'


def test_docx_pptx_and_xlsx_are_read_without_extra_dependencies(tmp_path):
    _office(
        tmp_path / "winloss.docx",
        {
            "word/document.xml": f"<w:document {NS_W}><w:body><w:p><w:r><w:t>We lost Acme on </w:t></w:r><w:r><w:t>price.</w:t></w:r></w:p></w:body></w:document>"
        },
    )
    _office(
        tmp_path / "deck.pptx",
        {
            "ppt/slides/slide1.xml": f"<p:sld xmlns:p='p' {NS_A}><a:p><a:r><a:t>Northwind</a:t></a:r></a:p></p:sld>",
            "ppt/slides/slide2.xml": f"<p:sld xmlns:p='p' {NS_A}><a:p><a:r><a:t>12 paying customers</a:t></a:r></a:p></p:sld>",
        },
    )
    sheet = (
        f"<worksheet {NS_S}><sheetData>"
        '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c><c r="C1" t="inlineStr"><is><t>Lead Source</t></is></c></row>'
        '<row r="2"><c r="A2" t="inlineStr"><is><t>Acme</t></is></c><c r="B2" t="inlineStr"><is><t>VP Sales</t></is></c><c r="C2" t="inlineStr"><is><t>LinkedIn</t></is></c></row>'
        '<row r="3"><c r="A3" t="inlineStr"><is><t>Beta</t></is></c><c r="C3" t="inlineStr"><is><t>Referral</t></is></c></row>'
        "</sheetData></worksheet>"
    )
    shared = f"<sst {NS_S}><si><t>Company</t></si><si><t>Title</t></si></sst>"
    xlsx = _office(tmp_path / "leads.xlsx", {"xl/worksheets/sheet1.xml": sheet, "xl/sharedStrings.xml": shared})
    headers, rows = read_xlsx(xlsx)
    assert headers == ["Company", "Title", "Lead Source"]
    assert rows[1] == {"Company": "Beta", "Title": "", "Lead Source": "Referral"}

    docs = {d.name: d for d in read_documents([tmp_path]).docs}
    assert docs["winloss.docx"].text == "We lost Acme on price."
    assert docs["deck.pptx"].kind == "deck" and "[slide 2]\n12 paying customers" in docs["deck.pptx"].text
    assert docs["leads.xlsx"].kind == "lead sheet"
    assert "Lead source: LinkedIn 1 of 2 (50%), Referral 1 of 2 (50%)." in docs["leads.xlsx"].text


def test_quote_sources_spans_several_files():
    named = [("your answers", ""), ("leads.csv", "Lead source: Referral 41 of 60 (68%)."), ("deals.csv", "Win rate: 9 of 31 (29%).")]
    assert quote_sources("Win rate: 9 of 31 (29%)", named) == ["deals.csv"]
    assert quote_sources("Lead source: Referral 41 of 60 (68%) … Win rate: 9 of 31 (29%)", named) == ["leads.csv", "deals.csv"]


def test_checkup_from_documents_only_scores_pipeline_from_the_deal_export():
    result = run_checkup(documents=[DEMO_DOCS], provider=MockProvider())
    pipeline = {a.key: a for a in result.areas}["pipeline"]
    assert pipeline.score is not None and "hubspot-deals.csv" in pipeline.sources
    assert "4 of 8 open deals" in pipeline.finding
    assert [d["name"] for d in result.documents] == ["call-notes-ledgerly.md", "hubspot-deals.csv", "leads.csv"]
    assert "## What we read" in result.report and "`leads.csv`: lead sheet, 60 leads" in result.report


class QuotesDocuments(Provider):
    """A founder diagnostic that quotes documents: one area from two spreadsheets, one area from a single call note."""

    name = "quotes-docs"

    def complete(self, *, system, user, schema, skill):
        if skill != "gtm-founder-diagnostic":
            return MockProvider().complete(system=system, user=user, schema=schema, skill=skill)
        out = json.loads(json.dumps(get_skill("gtm-founder-diagnostic").example_output))
        for area in ("icp", "pricing", "sales_motion", "pipeline"):
            out[area]["items"] = []
        out["demand"]["items"] = [
            {"criterion": "repeatable_channel", "points": 0, "max": 40, "evidence": "Won deals by source: Founder referral 7 of 9 (78%)"},
            {
                "criterion": "source_mix_known",
                "points": 30,
                "max": 30,
                "evidence": "Lead source: Founder referral 41 of 60 (68%) … Win rate on closed deals: 9 of 31 (29%)",
            },
        ]
        out["pmf"]["items"] = [
            {"criterion": "retention", "points": 40, "max": 40, "evidence": "They added 4 more seats in September"},
            {"criterion": "must_have_evidence", "points": 30, "max": 30, "evidence": "if you turned this off tomorrow"},
        ]
        return Completion(text=json.dumps(out), model="x")


def test_document_evidence_is_attributed_and_one_call_note_cannot_make_an_area_strong():
    result = run_checkup(documents=[DEMO_DOCS], provider=QuotesDocuments())
    areas = {a.key: a for a in result.areas}
    assert areas["demand"].sources == ["hubspot-deals.csv", "leads.csv"]
    assert areas["pmf"].sources == ["call-notes-ledgerly.md"]
    assert areas["pmf"].score == 60 and "all from one document" in areas["pmf"].finding
    assert "(hubspot-deals.csv)" in result.report  # evidence lines name the file, not "you said"


def test_cli_checkup_with_docs(capsys):
    assert main(["checkup", "--docs", str(DEMO_DOCS), "--no-questions", "--provider", "mock", "--brief"]) == 0
    out = capsys.readouterr().out
    assert "hubspot-deals.csv" in out and "## Evidence" not in out
