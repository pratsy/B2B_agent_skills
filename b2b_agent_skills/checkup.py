"""GTM checkup: an honest scorecard of an early-stage B2B company's go-to-market.

    b2b-skills checkup [yourcompany.com] [--answers answers.json] [--docs folder-or-files ...]

Inputs, all optional but at least one required:
- the founder's answers to ten questions (asked interactively, or from --answers)
- documents the founder already has (--docs): lead sheets, CRM/deal exports, customer lists,
  PMF surveys, call notes, the pitch deck. Spreadsheets are summarized in code (documents.py)
- the website: what a buyer reads (positioning, messaging, proof)

Eight areas, each owned by a role on a GTM team (CMO, Strategy, Growth, Head of Sales, RevOps),
scored by named methods. The math is done in code; every point quotes its source (the page or
the founder's answer or document); areas without data say "unknown" and what would unlock them.
"""

from __future__ import annotations

import datetime as _dt
import json
import re
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .documents import DocumentSet, read_documents
from .errors import ProviderError, SkillOutputError, SkillsError
from .extraction import extract_inputs, quote_in_source
from .providers import Provider, get_provider
from .runner import run_skill
from .workspace import Workspace

QUESTIONS = [
    "What stage are you at, and how many paying customers do you have?",
    "Who are your best customers, and why did they buy?",
    "Who churned or never converted, and why?",
    "Where do your leads and customers come from today?",
    "What happens from first conversation to signed deal, and who sells?",
    "Roughly what's your win rate and sales cycle?",
    "How do you price, what's a typical deal size, and how often do you discount?",
    "Are customers staying and expanding? How do you know they'd miss you?",
    "What's in your open pipeline versus this quarter's target?",
    "What's your biggest GTM headache right now?",
]

# Allowed point values per criterion, enforced in code.
WEBSITE_RUBRIC: dict[str, dict[str, tuple[int, ...]]] = {
    "icp_clarity": {
        "target_customer_named": (0, 15, 30),
        "buyer_role_named": (0, 10, 20),
        "problem_or_trigger_named": (0, 15, 30),
        "focus_or_exclusion": (0, 10, 20),
    },
    "positioning": {
        "category_clear": (0, 10, 20),
        "alternative_addressed": (0, 10, 20),
        "unique_attributes_stated": (0, 10, 20),
        "value_concrete": (0, 10, 20),
        "value_tied_to_customer": (0, 10, 20),
    },
    "differentiation": {"swap_test": (0, 20, 40), "differentiators_specific": (0, 15, 30), "differentiators_provable": (0, 15, 30)},
    "proof": {"customer_evidence": (0, 15, 30), "quantified_results": (0, 20, 40), "third_party_credibility": (0, 15, 30)},
}
FOUNDER_RUBRIC: dict[str, dict[str, tuple[int, ...]]] = {
    "icp": {"best_customer_pattern": (0, 20, 40), "buying_trigger_known": (0, 15, 30), "loss_reasons_known": (0, 15, 30)},
    "pmf": {"retention": (0, 20, 40), "pull_signals": (0, 15, 30), "must_have_evidence": (0, 15, 30)},
    "demand": {"repeatable_channel": (0, 20, 40), "source_mix_known": (0, 15, 30), "beyond_founder_network": (0, 15, 30)},
    "pricing": {"value_based": (0, 15, 30), "deal_size_fits_motion": (0, 15, 30), "discount_discipline": (0, 20, 40)},
    "sales_motion": {"defined_process": (0, 15, 30), "qualification": (0, 15, 30), "metrics_known": (0, 20, 40)},
    "pipeline": {"coverage": (0, 20, 40), "tracked_in_crm": (0, 15, 30), "next_steps_on_deals": (0, 15, 30)},
}

# key, name, owner, question it answers
AREAS = [
    ("icp", "ICP", "CMO", "Do you know exactly who buys, and does your site say so?"),
    ("pmf", "Product-market fit", "Strategy", "Do customers stay, and would they miss you?"),
    ("positioning", "Positioning & messaging", "CMO", "Is the story specific, differentiated, and clear?"),
    ("proof", "Proof", "CMO", "Do you back your claims?"),
    ("demand", "Demand & channels", "Growth", "Is there a repeatable way to get leads?"),
    ("pricing", "Pricing & value", "Strategy", "Does the price capture value?"),
    ("sales_motion", "Sales motion", "Head of Sales", "Are deals run on a process and evidence?"),
    ("pipeline", "Pipeline & RevOps", "RevOps", "Can the pipeline hit the target?"),
]

UNLOCK = {
    "icp": "Answer questions 2-3 (best customers, churn), and/or add a customer list with won/lost: `--docs accounts.csv`",
    "pmf": "Answer question 8 (retention), and/or send the Sean Ellis survey and add `--docs responses.csv`",
    "positioning": "Add your website: `b2b-skills checkup yourcompany.com`",
    "proof": "Add your website: `b2b-skills checkup yourcompany.com`",
    "demand": "Answer question 4 (where leads come from), and/or add your lead sheet: `--docs leads.csv`",
    "pricing": "Answer question 7 (pricing, deal size, discounting)",
    "sales_motion": "Answer questions 5-6 (process, win rate, cycle), add a CRM export with closed deals (`--docs deals.csv`), then debrief real calls with `b2b-skills playbook call-debrief`",
    "pipeline": "Answer question 9 (pipeline vs. target), and/or add your CRM deal export: `--docs deals.csv`",
}

SINGLE_CRITERION_CAP = 60.0  # an area scored from one answered criterion is at most "decent"

ICON = {"strong": "🟢", "decent": "🟡", "weak": "🟠", "missing": "🔴", "unknown": "⚪"}


def band(score: float | None) -> str:
    if score is None:
        return "unknown"
    return "strong" if score >= 80 else "decent" if score >= 60 else "weak" if score >= 40 else "missing"


@dataclass
class Area:
    key: str
    name: str
    owner: str
    question: str
    score: float | None = None
    finding: str = ""
    sources: list[str] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    fix: str = ""
    unlock: str = ""

    @property
    def band(self) -> str:
        return band(self.score)


@dataclass
class CheckupResult:
    website: str | None
    areas: list[Area]
    fixes: list[dict[str, str]]
    report: str
    overall: float | None
    scored: int
    biggest_risk: str = ""
    documents: list[dict[str, str]] = field(default_factory=list)
    saved_to: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "website": self.website,
            "overall": self.overall,
            "scored_areas": self.scored,
            "biggest_risk": self.biggest_risk,
            "areas": [{**asdict(a), "band": a.band} for a in self.areas],
            "fixes": self.fixes,
            "documents": self.documents,
            "saved_to": self.saved_to,
        }


def parse_answers(text: str) -> dict[str, str]:
    """Answers as JSON ({"q1": "..."} or a list) or as text lines/paragraphs starting with 'q1:' / '1.'."""
    text = text.strip()
    if text.startswith(("{", "[")):
        data = json.loads(text)
        if isinstance(data, list):
            return {f"q{i}": str(a) for i, a in enumerate(data, 1) if str(a).strip()}
        return {f"q{re.sub(r'[^0-9]', '', str(k))}": str(v) for k, v in data.items() if str(v).strip() and re.sub(r"[^0-9]", "", str(k))}
    answers: dict[str, str] = {}
    current = None
    for line in text.splitlines():
        m = re.match(r"^\s*(?:q|question\s*)?(\d{1,2})\s*[:.)-]\s*(.*)$", line, re.I)
        if m:
            current = f"q{int(m.group(1))}"
            answers[current] = m.group(2).strip()
        elif current and line.strip():
            answers[current] = (answers[current] + " " + line.strip()).strip()
    return {k: v for k, v in answers.items() if v}


def answers_text(answers: dict[str, str]) -> str:
    out = []
    for i, q in enumerate(QUESTIONS, 1):
        a = answers.get(f"q{i}", "").strip()
        if a:
            out.append(f"Q{i}. {q}\nA: {a}")
    return "\n\n".join(out)


def _snap(raw: Any, allowed: tuple[int, ...]) -> int:
    points = int(raw) if isinstance(raw, (int, float)) and not isinstance(raw, bool) else 0
    return max((v for v in allowed if v <= points), default=0)


def score_website_area(area: str, items: list[dict[str, Any]], page_text: str) -> tuple[float, list[dict[str, Any]]]:
    """Clamp to the rubric; zero any points whose quote isn't on the page. Absent criteria score 0 (absence is the finding)."""
    by_criterion = {str(i.get("criterion")): i for i in items if isinstance(i, dict)}
    checked: list[dict[str, Any]] = []
    total = 0
    for criterion, allowed in WEBSITE_RUBRIC[area].items():
        item = by_criterion.get(criterion, {})
        evidence = str(item.get("evidence") or "").strip()
        verified = bool(evidence) and quote_in_source(evidence, page_text)
        points = _snap(item.get("points"), allowed) if verified else 0
        checked.append({"criterion": criterion, "points": points, "max": allowed[-1], "evidence": evidence if verified else ""})
        total += points
    return float(total), checked


def score_founder_area(area: str, items: list[dict[str, Any]], source: str) -> tuple[float | None, list[dict[str, Any]]]:
    """A criterion counts only if its evidence quotes the founder; an area with no answered criteria is unknown (None)."""
    by_criterion = {str(i.get("criterion")): i for i in items if isinstance(i, dict)}
    checked: list[dict[str, Any]] = []
    total, answered = 0, 0
    for criterion, allowed in FOUNDER_RUBRIC[area].items():
        item = by_criterion.get(criterion, {})
        evidence = str(item.get("evidence") or "").strip()
        if evidence and quote_in_source(evidence, source):
            answered += 1
            points = _snap(item.get("points"), allowed)
            checked.append({"criterion": criterion, "points": points, "max": allowed[-1], "evidence": evidence})
            total += points
        else:
            checked.append({"criterion": criterion, "points": 0, "max": allowed[-1], "evidence": "", "unanswered": True})
    if not answered:
        return None, checked
    # Unanswered criteria don't count against the founder: rescale to the answered maximum.
    answered_max = sum(c["max"] for c in checked if not c.get("unanswered"))
    return round(total / answered_max * 100, 1), checked


def _messaging_score(asset_score: Any) -> float | None:
    if not isinstance(asset_score, (int, float)):
        return None
    return round(max(0.0, min(100.0, (float(asset_score) - 4) / 16 * 100)), 1)


def _pmf_score(pct: Any) -> float | None:
    """Sean Ellis: 40% very disappointed is the benchmark; 40% -> 80, 50%+ -> 100."""
    return round(min(100.0, float(pct) * 2), 1) if isinstance(pct, (int, float)) else None


def _pipeline_from_csv(path: str | Path) -> tuple[float, str]:
    from .review import deals_from_csv

    deals = deals_from_csv(path)
    if not deals:
        raise SkillsError(f"{path} has no deals")
    return _pipeline_score(deals)


def _pipeline_score(deals: list[dict[str, Any]]) -> tuple[float, str]:
    from .review import code_flags

    bad = [d for d in deals if code_flags(d, _dt.date.today())]
    return round(
        100 * (1 - len(bad) / len(deals)), 1
    ), f"{len(bad)} of {len(deals)} open deals are overdue, silent 14+ days, or stuck 45+ days"


def _mean(values: Sequence[float | None]) -> float | None:
    known = [v for v in values if v is not None]
    return round(sum(known) / len(known), 1) if known else None


AREA_QUESTIONS = {
    "icp": ("q2", "q3"),
    "pmf": ("q8",),
    "demand": ("q4",),
    "pricing": ("q7",),
    "sales_motion": ("q5", "q6"),
    "pipeline": ("q9",),
}


def quote_sources(quote: str, named_sources: list[tuple[str, str]]) -> list[str]:
    """Which sources a verified quote came from. Evidence joined from several places ("… ") may span several files."""
    from .extraction import _FRAGMENT_SPLIT

    whole = [name for name, text in named_sources if text and quote_in_source(quote, text)]
    if whole:
        return whole[:1]
    found: list[str] = []
    for fragment in _FRAGMENT_SPLIT.split(quote):
        if len(fragment.strip(".\"' ")) < 4:
            continue
        name = next((n for n, text in named_sources if text and quote_in_source(fragment, text)), None)
        if name and name not in found:
            found.append(name)
    return found


def _answered(area: str, answers: dict[str, str]) -> bool:
    return any(answers.get(q, "").strip() for q in AREA_QUESTIONS[area])


def _weak(checked: list[dict[str, Any]]) -> list[str]:
    return [c["criterion"].replace("_", " ") for c in checked if not c.get("unanswered") and c["points"] < c["max"] / 2]


def run_checkup(
    website: str | None = None,
    *,
    answers: dict[str, str] | None = None,
    page_text: str | None = None,
    survey_csv: str | Path | None = None,
    pipeline_csv: str | Path | None = None,
    competitors: list[str] | None = None,
    documents: Sequence[str | Path] | DocumentSet | None = None,
    provider: Provider | str | None = None,
    workspace: Workspace | None = None,
) -> CheckupResult:
    provider = get_provider(provider) if provider is None or isinstance(provider, str) else provider
    answers = {k: v for k, v in (answers or {}).items() if v and v.strip()}
    if website and page_text is None:
        from .init_wizard import fetch_website_text

        page_text = fetch_website_text(website, limit=20000)
    if page_text is not None and len(page_text.strip()) < 200:
        raise SkillsError(
            f"only {len(page_text.strip())} characters of text came back from {website} (it may render with JavaScript). "
            "Save the homepage text to a file and pass --text homepage.txt"
        )
    docs = documents if isinstance(documents, DocumentSet) else read_documents(list(documents or []))
    if documents and not docs and not answers and not page_text:
        raise SkillsError("none of the documents could be read: " + "; ".join(docs.skipped))
    if not answers and not page_text and not survey_csv and not pipeline_csv and not docs:
        raise SkillsError("give the checkup something to work with: answer the questions, point it at your documents, add your website")

    context = workspace.company_context() if workspace else None
    qa = answers_text(answers)
    # What the founder told us: their answers plus their documents. Every founder-side point must quote this.
    founder_src = "\n\n".join(x for x in (qa, docs.evidence_text()) if x)
    raw: dict[str, Any] = {}
    errors: list[str] = []

    named = [("your answers", qa), *((d.name, d.text) for d in docs.docs)]
    founder_input: dict[str, Any] = {"answers": answers}
    if docs:
        founder_input["documents"] = docs.for_skill()

    def founder() -> None:
        if not founder_src:
            return
        out = run_skill("gtm-founder-diagnostic", founder_input, provider=provider, context=context, raise_on_invalid=False).output or {}
        missed = [
            area
            for area in FOUNDER_RUBRIC
            if _answered(area, answers) and score_founder_area(area, (out.get(area) or {}).get("items", []), founder_src)[0] is None
        ]
        if missed:  # the founder answered these, so a second look must quote them
            feedback = {
                **founder_input,
                "_feedback": f"The founder answered the questions for {', '.join(missed)}, but your evidence for those areas was "
                "missing or not word-for-word. Score them again, quoting the founder's exact words in each evidence field.",
            }
            retry = run_skill("gtm-founder-diagnostic", feedback, provider=provider, context=context, raise_on_invalid=False).output or {}
            for area in missed:
                if retry.get(area):
                    out[area] = retry[area]
            out.setdefault("biggest_risk", retry.get("biggest_risk", ""))
        raw["founder"] = out

    def audit() -> None:
        if page_text:
            raw["audit"] = run_skill(
                "gtm-website-audit",
                {"website": website, "page_text": page_text, "known_competitors": competitors or []},
                provider=provider,
                context=context,
                raise_on_invalid=False,
            ).output

    def messaging() -> None:
        if page_text:
            ex = extract_inputs("messaging-clarity-auditor", page_text, provider=provider, context=context)
            if ex.input.get("core_claims"):
                raw["messaging"] = run_skill(
                    "messaging-clarity-auditor", ex.input, provider=provider, context=context, raise_on_invalid=False
                ).output

    def positioning() -> None:
        sources = [s for s in (page_text, qa) if s]
        if page_text:
            ex = extract_inputs("brand-positioning-synthesizer", sources, provider=provider, context=context)
            raw["positioning"] = run_skill(
                "brand-positioning-synthesizer",
                ex.input or {"_note": "website only"},
                provider=provider,
                context=context,
                raise_on_invalid=False,
            ).output

    def pmf() -> None:
        rows = docs.survey_rows
        if survey_csv:
            from .tables import read_csv

            _, rows = read_csv(survey_csv)
        if rows:
            raw["pmf"] = run_skill(
                "pmf-survey-analyzer", {"responses": rows}, provider=provider, context=context, raise_on_invalid=False
            ).output

    def safe(fn: Any) -> None:
        try:
            fn()
        except (ProviderError, SkillOutputError, SkillsError, ValueError) as e:
            errors.append(f"{fn.__name__}: {e}")

    with ThreadPoolExecutor(max_workers=5) as pool:
        list(pool.map(safe, [founder, audit, messaging, positioning, pmf]))

    areas = {k: Area(k, name, owner, q) for k, name, owner, q in AREAS}
    fdx = raw.get("founder") or {}
    for key in FOUNDER_RUBRIC:
        block = fdx.get(key) or {}
        score, checked = score_founder_area(key, block.get("items", []), founder_src) if founder_src else (None, [])
        if score is not None:
            a = areas[key]
            answered = [c for c in checked if not c.get("unanswered")]
            for c in answered:  # where each quote came from: the answers, or which documents
                c["source"] = ", ".join(quote_sources(c["evidence"], named)) or ("your answers" if qa else "your documents")
            missing = [c["criterion"].replace("_", " ") for c in checked if c.get("unanswered")]
            sources = list(dict.fromkeys(src for c in answered for src in c["source"].split(", ")))
            # One call note or one deck is one voice: like a single answered criterion, it can't make an area strong.
            single_note = len(answered) > 1 and len(sources) == 1 and docs.kind_of(sources[0]) in {"notes", "deck"}
            if len(answered) == 1 or single_note:
                score = min(score, SINGLE_CRITERION_CAP)
            a.score, a.evidence, a.sources = score, checked, sources
            weak = _weak(checked)
            a.finding = ("weak on: " + ", ".join(weak)) if weak else "solid on what you described"
            if single_note:
                a.finding = f"provisional (all from one document, {sources[0]}); {a.finding}"
            if len(answered) == 1:
                a.finding = f"provisional (1 of {len(checked)} criteria answered; unknown: {', '.join(missing)}); {a.finding}"
            a.fix = str(block.get("fix") or "")

    audit_out = raw.get("audit") or {}
    site: dict[str, tuple[float, list[dict[str, Any]]]] = {}
    for key in WEBSITE_RUBRIC:
        items = (audit_out.get(key) or {}).get("items", [])
        if items and page_text:
            site[key] = score_website_area(key, items, page_text)
    msg = raw.get("messaging") or {}

    if "icp_clarity" in site:  # ICP = founder evidence and what the site says, averaged
        a = areas["icp"]
        site_score, checked = site["icp_clarity"]
        a.score = _mean([a.score, site_score])
        a.sources.append("website")
        a.evidence += [{**c, "source": "website"} for c in checked]
        if not a.finding:
            site_weak = _weak(checked)
            a.finding = ("site is weak on: " + ", ".join(site_weak)) if site_weak else "the site says clearly who it's for"
        elif site_score < 40:
            a.finding += "; the site doesn't say who it's for"
    parts = [site[k][0] for k in ("positioning", "differentiation") if k in site] + [
        s for s in [_messaging_score(msg.get("asset_score"))] if s is not None
    ]
    if parts:
        a = areas["positioning"]
        a.score, a.sources = _mean(parts), ["website"]
        a.evidence = [{**c, "source": "website"} for k in ("positioning", "differentiation") if k in site for c in site[k][1]]
        weak = _weak(a.evidence)
        fixes = msg.get("priority_fixes") or []
        msg_finding = _grounded(str(fixes[0]), [page_text or ""]) if fixes else ""
        a.finding = "; ".join(x for x in [("weak on: " + ", ".join(weak[:3])) if weak else "", msg_finding] if x)
    if "proof" in site:
        a = areas["proof"]
        a.score, a.evidence, a.sources = site["proof"][0], [{**c, "source": "website"} for c in site["proof"][1]], ["website"]
        weak = _weak(a.evidence)
        a.finding = ("missing: " + ", ".join(weak)) if weak else "claims are backed"
    if raw.get("pmf"):
        p, a = raw["pmf"], areas["pmf"]
        a.score = _pmf_score(p.get("pmf_score_pct"))
        a.sources = [f"PMF survey ({docs.survey_name})" if docs.survey_rows and not survey_csv else "PMF survey (Sean Ellis)"]
        a.finding = f"{p.get('pmf_score_pct')}% very disappointed ({p.get('pmf_band')}); strongest segment: {p.get('strongest_segment')}"
    if pipeline_csv or docs.open_deals:
        try:
            score, finding = _pipeline_from_csv(pipeline_csv) if pipeline_csv else _pipeline_score(docs.open_deals)
            a = areas["pipeline"]
            label = "pipeline export" if pipeline_csv else docs.pipeline_name
            a.score, a.finding = _mean([a.score, score]), finding
            a.sources = list(dict.fromkeys([*a.sources, label]))
        except (SkillsError, ValueError) as e:
            errors.append(f"pipeline: {e}")
    for key, text in UNLOCK.items():
        if areas[key].score is None:
            areas[key].unlock = text

    ordered = [areas[k] for k, *_ in AREAS]
    founder_side = sum(1 for a in ordered if a.score is not None and any(s != "website" for s in a.sources))
    # A GTM score needs the founder's side of the story (answers or documents); a website alone only gets a website score.
    overall = _mean([a.score for a in ordered]) if founder_side >= 3 else None
    website_score = _mean(
        [a.score for a in ordered if a.sources == ["website"]] + ([site["icp_clarity"][0]] if "icp_clarity" in site else [])
    )
    # Numbers in fixes are checked against what the founder said and shared, not the question labels ("Q3.", "10 questions").
    grounding = [s for s in (page_text, "\n".join(answers.values()), docs.evidence_text()) if s]
    fixes = build_fixes(ordered, raw, sources=grounding)
    risk = _grounded(str(fdx.get("biggest_risk") or ""), grounding) or _grounded(str(audit_out.get("biggest_gap") or ""), grounding)
    report = render_report(
        website,
        ordered,
        overall,
        fixes,
        risk,
        audit_out.get("headline"),
        errors,
        site_score=website_score if page_text else None,
        documents=docs,
    )
    result = CheckupResult(
        website=website,
        areas=ordered,
        fixes=fixes,
        report=report,
        overall=overall,
        scored=sum(1 for a in ordered if a.score is not None),
        biggest_risk=risk,
        documents=docs.to_list(),
        raw=raw,
    )
    if workspace:
        path = workspace.gtm / "checkups" / f"{_dt.date.today().isoformat()}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report, encoding="utf-8")
        result.saved_to = str(path.relative_to(workspace.root))
        workspace.log_run(
            {"type": "checkup", "website": website, "answers": answers, "documents": docs.to_list(), "result": result.to_dict()}
        )
    return result


NUMBER_WORDS = (
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "twice",
    "half",
    "double",
    "triple",
    "dozen",
    "hundreds",
    "thousands",
)


UNITS = r"(?:days?|weeks?|months?|quarters?|years?|hours?|minutes?|seats?|deals?|customers?|leads?|accounts?|calls?|reps?|users?)"


def numbers_supported(text: str, sources: list[str]) -> bool:
    """Every number in a suggested fix or finding must appear in the sources: as a whole number (not inside "51-200"),
    with its "$" if it's money, and with its unit if it has one ("60 days"; number words: "two weeks")."""
    joined = re.sub(r"(?<=\d),(?=\d)", "", " ".join(sources).lower())
    squeezed = re.sub(r"\s+", "", joined)
    pattern = r"(\$)?(\d[\d,.]*\d|\d)\s*([kmb]\b|%)?(\s*" + UNITS + r"\b)?"
    for m in re.finditer(pattern, text.lower()):
        dollar, core, suffix, unit = m.group(1), m.group(2).replace(",", ""), m.group(3) or "", m.group(4)
        if not re.search(rf"(?<![\d.\-–]){re.escape(core)}(?!\d|\.\d)", joined):
            return False
        if dollar and f"${core}{suffix}" not in squeezed:
            return False
        if unit and not re.search(rf"(?<![\d.]){re.escape(core)}\s*{unit.strip().rstrip('s')}", joined):
            return False
    # A number word must appear with the word after it ("two weeks"), not just anywhere ("two agencies").
    phrases = re.findall(r"\b((?:" + "|".join(NUMBER_WORDS) + r")\s+[a-z]+)", text.lower())
    normalized = re.sub(r"\s+", " ", joined)
    return all(re.sub(r"\s+", " ", ph) in normalized for ph in phrases)


def _grounded(text: str, sources: list[str]) -> str:
    """Keep only sentences whose numbers and claims the sources support."""
    from .playbooks import unsupported_claims

    sentences = re.split(r"(?<=[.;])\s+|;\s*", text)
    kept = [s for s in sentences if s.strip() and numbers_supported(s, sources) and not unsupported_claims(s)]
    return "; ".join(s.strip().rstrip(";") for s in kept)


def build_fixes(areas: list[Area], raw: dict[str, Any], sources: list[str] | None = None) -> list[dict[str, str]]:
    """The three weakest scored areas, each with a fix taken from the skills' own outputs (no new claims)."""
    from .playbooks import unsupported_claims

    sources = sources or []
    msg, pos = raw.get("messaging") or {}, raw.get("positioning") or {}
    rewrite = next((c.get("suggested_rewrite") for c in msg.get("claims_scored", []) if c.get("suggested_rewrite")), "")
    next_step = {
        "icp": "b2b-skills playbook find-icp --customers accounts.csv",
        "pmf": "b2b-skills run pmf-survey-analyzer --csv responses.csv",
        "positioning": "b2b-skills playbook fix-my-message --website <url>",
        "proof": "Ask your two happiest customers for a before/after number and a quote you can use.",
        "demand": "b2b-skills playbook score-list --csv leads.csv",
        "pricing": "b2b-skills run pricing-justification-builder --notes pricing.md",
        "sales_motion": "b2b-skills playbook call-debrief --notes call.txt",
        "pipeline": "b2b-skills playbook monday-review --csv deals.csv",
    }
    if rewrite and not (numbers_supported(rewrite, sources) and not unsupported_claims(rewrite)):
        rewrite = ""  # a draft with numbers or claims the sources don't support is worse than no draft
    audience = str(pos.get("selected_target_market") or "")
    website_fix = {
        "positioning": f'Rewrite the headline so a competitor couldn\'t use it. Draft: "{rewrite}"'
        if rewrite
        else "Rewrite the headline to name who it's for, what it replaces, and the outcome; run fix-my-message for drafts.",
        "proof": "Add one named customer result (a before/after number and a quote) next to the headline.",
        "icp": f"Say who it's for in the headline or subhead. The audience your site seems to target: {audience}."
        if audience and numbers_supported(audience, sources)
        else "Say who it's for in the headline or subhead: company type, size, and the role that buys.",
    }
    out = []
    for a in sorted((a for a in areas if a.score is not None and a.score < 80), key=lambda a: a.score or 0):
        detail = (a.fix or website_fix.get(a.key, "")).strip()
        if not detail or unsupported_claims(detail) or not numbers_supported(detail, sources):
            continue
        out.append({"area": a.name, "owner": a.owner, "fix": detail, "next": next_step[a.key]})
        if len(out) == 3:
            break
    return out


def render_report(
    website: str | None,
    areas: list[Area],
    overall: float | None,
    fixes: list[dict[str, str]],
    risk: str,
    headline: Any,
    errors: list[str],
    site_score: float | None = None,
    documents: DocumentSet | None = None,
) -> str:
    scored = [a for a in areas if a.score is not None]
    lines = [f"# GTM checkup{': ' + website if website else ''}", ""]
    if overall is not None:
        lines.append(f"**GTM score: {overall:.0f}/100** ({band(overall)}), from {len(scored)} of {len(areas)} areas.")
    elif site_score is not None:
        lines += [
            f"**Website score: {site_score:.0f}/100** ({band(site_score)}). This covers only what a buyer reads on your site.",
            "",
            "> This is not your GTM score: product-market fit, demand, pricing, sales motion, and pipeline can't be judged "
            "from a website. Answer the 10 questions (`b2b-skills checkup` without `--website-only`, about 3 minutes) "
            "or point it at your documents (`--docs leads.csv deals.csv notes/`) to score them.",
        ]
    if risk:
        lines += ["", f"**Biggest risk:** {risk}"]
    lines += ["", "| Area | Owner | Score | What we found | Based on |", "|---|---|---|---|---|"]
    for a in areas:
        score = f"{ICON[a.band]} {a.score:.0f}" if a.score is not None else f"{ICON['unknown']} unknown"
        found = (a.finding or "-") if a.score is not None else "not enough information yet"
        lines.append(f"| {a.name} | {a.owner} | {score} | {found.replace('|', '/')} | {', '.join(a.sources) or '-'} |")
    if fixes:
        lines += ["", "## Top 3 fixes", ""]
        for i, f in enumerate(fixes, 1):
            step = f["next"].replace("<url>", website or "yourcompany.com")
            lines += [
                f"{i}. **{f['area']}** ({f['owner']}): {f['fix']}",
                f"   - Next: `{step}`" if step.startswith("b2b-skills") else f"   - Next: {step}",
            ]
    unknown = [a for a in areas if a.score is None]
    if unknown:
        lines += ["", "## Unlock the rest", ""] + [f"- **{a.name}**: {a.unlock}" for a in unknown]
    if documents and (documents.docs or documents.skipped):
        lines += ["", "## What we read", ""] + [f"- `{d.name}`: {d.summary}" for d in documents.docs]
        lines += [f"- skipped `{s}`" for s in documents.skipped]
    quotes = [(a, e) for a in areas for e in a.evidence if e.get("evidence")]
    if quotes:
        lines += ["", "## Evidence", ""]
        for a, e in quotes[:14]:
            src = e.get("source") or "your answers"
            where = "site" if src == "website" else "you said" if src == "your answers" else src
            lines.append(f'- {a.name} · {e["criterion"].replace("_", " ")} {e["points"]}/{e["max"]} ({where}): "{e["evidence"]}"')
    if headline:
        lines += ["", f'Homepage headline as written: "{headline}"']
    if errors:
        lines += ["", "> Some checks didn't complete: " + "; ".join(errors)]
    lines += [
        "",
        "_Scored with named methods (Dunford positioning, Sean Ellis PMF test, MEDDPICC-style qualification, pipeline coverage); every point quotes your answers, your documents, or your site._",
    ]
    return "\n".join(lines) + "\n"
