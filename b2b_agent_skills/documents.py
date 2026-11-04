"""Read the documents a founder points the checkup at, and turn them into quotable evidence.

    b2b-skills checkup acme.com --docs ./gtm-stuff leads.xlsx deck.pdf

Each file is recognized by its content, not its name:

- spreadsheets (.csv, .tsv, .xlsx): a PMF survey, a deal export (open pipeline and/or closed
  won/lost deals), a customer list with outcomes, or a lead sheet. The numbers that matter
  (win rate, lead-source mix, attribute lift, overdue deals) are computed here, in code, and
  written as plain sentences so the model can quote them and cannot invent them.
- text (.txt, .md, .vtt, .srt, .json transcripts, .docx, .pptx, .pdf, .html): call notes,
  win/loss interviews, pitch decks, pricing docs. Passed as text, truncated to a budget.

Every fact keeps the name of the file it came from, so the report can say "Based on: leads.csv".
"""

from __future__ import annotations

import datetime as _dt
import re
import statistics
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from .tables import map_columns, read_csv, to_number

TABLE_SUFFIXES = {".csv", ".tsv", ".xlsx"}
TEXT_SUFFIXES = {".txt", ".md", ".markdown", ".vtt", ".srt", ".json", ".docx", ".pptx", ".pdf", ".html", ".htm"}
MAX_FILES = 40
TEXT_BUDGET = 8000  # characters per text document
TOTAL_BUDGET = 48000  # characters of text documents in all

WON_WORDS = ("won", "closed won", "closed-won")
LOST_WORDS = ("lost", "closed lost", "closed-lost")
EXTRA_ALIASES = {
    "source": ["lead source", "source", "original source", "channel", "utm source", "acquisition channel", "how did you hear"],
    "lost_reason": ["lost reason", "closed lost reason", "loss reason", "reason lost", "churn reason"],
    "created": ["create date", "created date", "created", "created at", "date created"],
}


@dataclass
class Document:
    name: str
    kind: str
    summary: str
    text: str


@dataclass
class DocumentSet:
    docs: list[Document] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    survey_rows: list[dict[str, str]] = field(default_factory=list)
    survey_name: str = ""
    open_deals: list[dict[str, Any]] = field(default_factory=list)
    pipeline_name: str = ""

    def __bool__(self) -> bool:
        return bool(self.docs)

    def evidence_text(self) -> str:
        return "\n\n".join(f"=== {d.name} ({d.kind}) ===\n{d.text}" for d in self.docs if d.text)

    def for_skill(self) -> list[dict[str, str]]:
        return [{"name": d.name, "kind": d.kind, "text": d.text} for d in self.docs if d.text]

    def kind_of(self, name: str) -> str:
        return next((d.kind for d in self.docs if d.name == name), "")

    def to_list(self) -> list[dict[str, str]]:
        return [{"name": d.name, "kind": d.kind, "summary": d.summary} for d in self.docs]


def read_documents(paths: list[str | Path]) -> DocumentSet:
    out = DocumentSet()
    files: list[Path] = []
    for raw in paths:
        p = Path(raw).expanduser()
        if p.is_dir():
            files += sorted(f for f in p.rglob("*") if f.is_file() and not any(part.startswith(".") for part in f.relative_to(p).parts))
        elif p.is_file():
            files.append(p)
        else:
            out.skipped.append(f"{raw} (not found)")
    budget = TOTAL_BUDGET
    for f in files:
        suffix = f.suffix.lower()
        if suffix not in TABLE_SUFFIXES | TEXT_SUFFIXES:
            out.skipped.append(f"{f.name} (unsupported type)")
            continue
        if len(out.docs) >= MAX_FILES:
            out.skipped.append(f"{f.name} (more than {MAX_FILES} files)")
            continue
        try:
            if suffix in TABLE_SUFFIXES:
                headers, rows = read_xlsx(f) if suffix == ".xlsx" else read_csv(f)
                doc = _table_document(f.name, headers, rows, out)
            else:
                text = read_text_document(f).strip()
                if not text:
                    out.skipped.append(f"{f.name} (no text found)")
                    continue
                kind = "deck" if suffix == ".pptx" or (suffix == ".pdf" and "deck" in f.name.lower()) else "notes"
                cut = text[: min(TEXT_BUDGET, max(budget, 0))]
                if not cut:
                    out.skipped.append(f"{f.name} (text budget used up)")
                    continue
                budget -= len(cut)
                summary = f"{kind}, {len(text.split())} words" + (" (truncated)" if len(cut) < len(text) else "")
                doc = Document(f.name, kind, summary, cut)
        except (OSError, ValueError, KeyError, zipfile.BadZipFile, ElementTree.ParseError, UnicodeDecodeError) as e:
            out.skipped.append(f"{f.name} ({e})")
            continue
        except ImportError as e:
            out.skipped.append(f"{f.name} ({e})")
            continue
        out.docs.append(doc)
    return out


# --- text documents --------------------------------------------------------------------------


def read_text_document(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return _zip_text(path, ["word/document.xml"], "p")
    if suffix == ".pptx":
        with zipfile.ZipFile(path) as z:
            slides = sorted((n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)), key=lambda n: int(re.sub(r"\D", "", n)))
        return "\n\n".join(f"[slide {i}]\n{_zip_text(path, [s], 'p')}" for i, s in enumerate(slides, 1))
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as e:
            raise ImportError("reading PDFs needs pypdf: pip install 'b2b-agent-skills[docs-reader]'") from e
        return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
    if suffix in {".html", ".htm"}:
        from .init_wizard import html_to_text

        return html_to_text(path.read_text(encoding="utf-8", errors="replace"))
    from .transcripts import read_notes

    return read_notes(path)


def _zip_text(path: Path, members: list[str], para_tag: str) -> str:
    """Paragraph text from Office XML: concatenate <t> runs inside each paragraph."""
    lines = []
    with zipfile.ZipFile(path) as z:
        for m in members:
            root = ElementTree.fromstring(z.read(m))
            for el in root.iter():
                if el.tag.rsplit("}", 1)[-1] == para_tag:
                    text = "".join(t.text or "" for t in el.iter() if t.tag.rsplit("}", 1)[-1] == "t")
                    if text.strip():
                        lines.append(text.strip())
    return "\n".join(lines)


def read_xlsx(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """The first worksheet of an .xlsx file as (headers, rows), without extra dependencies."""
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        shared: list[str] = []
        if "xl/sharedStrings.xml" in names:
            for si in ElementTree.fromstring(z.read("xl/sharedStrings.xml")):
                shared.append("".join(t.text or "" for t in si.iter() if t.tag.endswith("}t")))
        sheet = (
            "xl/worksheets/sheet1.xml"
            if "xl/worksheets/sheet1.xml" in names
            else sorted(n for n in names if n.startswith("xl/worksheets/sheet"))[0]
        )
        grid: list[list[str]] = []
        for row in ElementTree.fromstring(z.read(sheet)).iter():
            if not row.tag.endswith("}row"):
                continue
            cells: dict[int, str] = {}
            for c in row:
                if not c.tag.endswith("}c"):
                    continue
                col = _col_index(c.get("r", ""))
                kind = c.get("t")
                v = next((x.text or "" for x in c if x.tag.endswith("}v")), "")
                if kind == "s" and v:
                    v = shared[int(v)]
                elif kind == "inlineStr":
                    v = "".join(t.text or "" for t in c.iter() if t.tag.endswith("}t"))
                cells[col if col >= 0 else len(cells)] = v.strip()
            if cells:
                grid.append([cells.get(i, "") for i in range(max(cells) + 1)])
    if not grid:
        return [], []
    headers = [h.strip() for h in grid[0]]
    rows = [{h: (r[i] if i < len(r) else "") for i, h in enumerate(headers) if h} for r in grid[1:] if any(x.strip() for x in r)]
    return [h for h in headers if h], rows


def _col_index(ref: str) -> int:
    letters = re.match(r"[A-Z]+", ref)
    if not letters:
        return -1
    n = 0
    for ch in letters.group(0):
        n = n * 26 + ord(ch) - 64
    return n - 1


# --- spreadsheets ----------------------------------------------------------------------------


def _pct(n: int, total: int) -> str:
    return f"{n} of {total} ({round(100 * n / total)}%)"


def _mix(rows: list[dict[str, Any]], field_name: str, top: int = 5) -> str:
    values = [str(r.get(field_name) or "").strip() for r in rows]
    values = [v for v in values if v]
    if not values:
        return ""
    counts = Counter(v.title() if v.islower() else v for v in values)
    return ", ".join(f"{v} {_pct(n, len(values))}" for v, n in counts.most_common(top))


def _money(x: float) -> str:
    return f"${x:,.0f}"


def _table_document(name: str, headers: list[str], rows: list[dict[str, str]], out: DocumentSet) -> Document:
    if not rows:
        raise ValueError("no rows")
    n = len(rows)
    # 1. a Sean Ellis survey: a column of "very / somewhat / not disappointed"
    for h in headers:
        vals = [r.get(h, "").lower() for r in rows if r.get(h)]
        if vals and sum("disappointed" in v for v in vals) >= 0.3 * len(vals):
            very = sum("very" in v for v in vals)
            out.survey_rows, out.survey_name = rows, name
            text = f"{name} is a PMF survey with {n} responses. Very disappointed: {_pct(very, len(vals))}."
            return Document(name, "PMF survey", f"PMF survey, {n} responses", text)

    from .review import DEAL_ALIASES, DEAL_FIELDS, code_flags

    deal_map = map_columns(headers, fields=[*DEAL_FIELDS, *EXTRA_ALIASES], aliases={**DEAL_ALIASES, **EXTRA_ALIASES})
    # 2. a deal export: stage plus amount or close date
    if "stage" in deal_map and ("amount" in deal_map or "close_date" in deal_map):
        deals = [{f: r.get(h, "") for f, h in deal_map.items()} for r in rows]
        stage = lambda d: str(d.get("stage") or "").lower()  # noqa: E731
        won = [d for d in deals if any(w in stage(d) for w in WON_WORDS) and "lost" not in stage(d)]
        lost = [d for d in deals if any(w in stage(d) for w in LOST_WORDS)]
        open_ = [d for d in deals if d not in won and d not in lost]
        lines = [f"{name} is a deal export with {n} deals: {len(open_)} open, {len(won)} won, {len(lost)} lost."]
        if won or lost:
            lines.append(f"Win rate on closed deals: {_pct(len(won), len(won) + len(lost))}.")
            amounts = [a for a in (to_number(str(d.get("amount") or "")) for d in won) if a]
            if amounts:
                lines.append(f"Median won deal size: {_money(statistics.median(amounts))} across {len(amounts)} won deals.")
            cycles = []
            for d in won:
                created, closed = _date(d.get("created")), _date(d.get("close_date"))
                if created and closed and closed >= created:
                    cycles.append((closed - created).days)
            if cycles:
                lines.append(f"Median sales cycle on won deals: {statistics.median(cycles):.0f} days.")
            reasons = _mix(lost, "lost_reason")
            if reasons:
                lines.append(f"Lost reasons: {reasons}.")
            sources = _mix(won, "source")
            if sources:
                lines.append(f"Won deals by source: {sources}.")
        if open_:
            total = sum(a for a in (to_number(str(d.get("amount") or "")) for d in open_) if a)
            today = _dt.date.today()
            flagged = [d for d in open_ if code_flags(d, today)]
            lines.append(f"Open pipeline: {len(open_)} deals worth {_money(total)}.")
            lines.append(f"Open deals overdue, silent 14+ days, or stuck 45+ days: {_pct(len(flagged), len(open_))}.")
            out.open_deals, out.pipeline_name = open_, name
        summary = f"deal export, {len(open_)} open and {len(won) + len(lost)} closed deals"
        return Document(name, "deal export", summary, "\n".join(lines))

    lead_map = map_columns(
        headers, fields=["company", "industry", "employees", "geography", "title", "outcome", "email", "source"], aliases=EXTRA_ALIASES
    )
    mapped = [{f: r.get(h, "") for f, h in lead_map.items()} for r in rows]
    # 3. a customer list with outcomes: who became a customer, and what they have in common
    if "outcome" in lead_map:
        from .calculators import attribute_lifts
        from .calculators.lift import is_best

        best = sum(1 for r in mapped if is_best(r))
        if 0 < best < n:
            lines = [f"{name} is an account list with {n} accounts, {best} of them won or customers."]
            try:
                lifts = attribute_lifts(mapped)
            except ValueError:
                lifts = []
            pos = [a for a in lifts if a.signal == "positive" and a.best_with >= 2][:4]
            neg = [a for a in lifts if a.lift == 0 and a.all_with >= 3][:3]
            if pos:
                lines.append(
                    "Over-represented among customers: "
                    + "; ".join(f"{a.attribute} {a.value} (lift {a.lift}, {a.best_with} of {a.best_total} customers)" for a in pos)
                    + "."
                )
            if neg:
                lines.append("Never became customers: " + "; ".join(f"{a.attribute} {a.value} (0 of {a.all_with})" for a in neg) + ".")
            if best < 15:
                lines.append(f"Provisional (n={best} customers).")
            return Document(name, "customer list", f"account list, {n} accounts, {best} customers", "\n".join(lines))
    # 4. a lead sheet: who is in the funnel and where they come from
    if {"company", "email", "title"} & set(lead_map):
        from .calculators.lift import size_band

        lines = [f"{name} is a lead sheet with {n} leads."]
        for label, key in (("Lead source", "source"), ("Industry", "industry"), ("Title", "title"), ("Geography", "geography")):
            mix = _mix(mapped, key)
            if mix:
                lines.append(f"{label}: {mix}.")
        if "employees" in lead_map:
            bands = [{"band": size_band(r.get("employees"))} for r in mapped]
            mix = _mix([b for b in bands if b["band"]], "band")
            if mix:
                lines.append(f"Company size (employees): {mix}.")
        if "source" not in lead_map:
            lines.append("The lead sheet has no lead source column.")
        return Document(name, "lead sheet", f"lead sheet, {n} leads", "\n".join(lines))
    return Document(name, "table", f"table, {n} rows", f"{name} is a table with {n} rows and columns: {', '.join(headers[:20])}.")


def _date(value: Any) -> _dt.date | None:
    from .review import _date as parse

    return parse(value)
