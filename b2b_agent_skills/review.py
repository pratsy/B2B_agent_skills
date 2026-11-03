"""monday-review playbook: the weekly pipeline review, built from the CRM plus the workspace's own deal notes.

For every open deal, code checks the hard signals (close date passed, no
activity for 14+ days, stuck in stage). Deals that have debrief notes in
gtm/deals/ are re-scored with deal-risk-assessor from that evidence; deals
without notes are flagged as "no evidence on file". The result is a short
report (this week's focus, deals at risk) and, for HubSpot, proposed
write-backs that wait in gtm/pending/ for approval.
"""

from __future__ import annotations

import datetime as _dt
import json
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .approvals import propose
from .errors import ProviderError, SkillOutputError
from .extraction import extract_inputs
from .playbooks import _clean_markdown, _report_prompt, load_playbook
from .providers import Provider, get_provider
from .runner import run_skill
from .tables import map_columns, read_csv, to_number
from .workspace import Workspace, slugify

DEAL_FIELDS = ["deal_id", "deal_name", "company", "amount", "stage", "close_date", "last_activity", "days_in_stage", "owner"]
DEAL_ALIASES = {
    "deal_id": ["deal id", "record id", "id", "opportunity id"],
    "deal_name": ["deal name", "deal", "opportunity", "opportunity name", "name"],
    "amount": ["amount", "deal amount", "value", "acv", "arr"],
    "stage": ["stage", "deal stage", "pipeline stage"],
    "close_date": ["close date", "expected close date", "closedate"],
    "last_activity": ["last activity", "last activity date", "last contacted", "last engagement", "last modified"],
    "days_in_stage": ["days in stage", "time in stage", "days in current stage"],
    "owner": ["owner", "deal owner", "rep"],
}
# Priority = weighted hard signals + evidence-based risk. Overdue and silent deals come first:
# they need action this week whatever their qualification looks like.
FLAG_WEIGHT = {"close date passed": 3, "no activity for": 2, "days in stage": 2, "no evidence on file": 1, "couldn't score": 1}
BAND_WEIGHT = {"critical": 3, "high": 2, "moderate high": 1.5, "moderate": 1, "low": 0}


@dataclass
class DealReview:
    deal: dict[str, Any]
    flags: list[str] = field(default_factory=list)
    notes_file: str | None = None
    risk: dict[str, Any] | None = None
    priority: float = 0.0


@dataclass
class ReviewResult:
    deals: list[DealReview]
    report: str
    proposed: list[dict[str, Any]] = field(default_factory=list)
    saved_to: str | None = None


def deals_from_csv(path: str | Path, overrides: dict[str, str] | None = None) -> list[dict[str, Any]]:
    headers, rows = read_csv(path)
    mapping = map_columns(headers, overrides, fields=DEAL_FIELDS, aliases=DEAL_ALIASES)
    return [{f: r.get(h, "") for f, h in mapping.items()} | {"source": "csv"} for r in rows]


def _date(value: Any) -> _dt.date | None:
    text = str(value or "").strip()[:10]
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return _dt.datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def code_flags(deal: dict[str, Any], today: _dt.date, stale_days: int = 14, stuck_days: int = 45) -> list[str]:
    flags = []
    close = _date(deal.get("close_date"))
    if close and close < today:
        flags.append(f"close date passed ({close.isoformat()})")
    last = _date(deal.get("last_activity"))
    if last and (today - last).days >= stale_days:
        flags.append(f"no activity for {(today - last).days} days")
    days = to_number(str(deal.get("days_in_stage") or ""))
    if days is not None and days >= stuck_days:
        flags.append(f"{days:.0f} days in stage {deal.get('stage') or ''}".strip())
    return flags


def _first_focus_item(report: str) -> str:
    """Text of item 1 under '## This week's focus' (used to verify the report kept the computed order)."""
    section = re.search(r"## This week's focus\s*(.*?)(?:\n## |\Z)", report, re.S | re.I)
    item = re.search(r"^\s*1\.\s*(.+)$", section.group(1), re.M) if section else None
    return item.group(1) if item else ""


def evidence_text(deal_file: str) -> str:
    """Primary evidence from a deal file: the raw source notes saved with each debrief, if present."""
    sources = re.findall(r"<summary>Source notes</summary>\s*(.*?)\s*</details>", deal_file, re.S)
    return "\n\n---\n\n".join(sources) if sources else deal_file


def find_notes(workspace: Workspace | None, deal: dict[str, Any]) -> Path | None:
    if not workspace:
        return None
    folder = workspace.gtm / "deals"
    if not folder.is_dir():
        return None
    keys = [slugify(str(deal.get(k))) for k in ("deal_name", "company") if deal.get(k)]
    for path in sorted(folder.glob("*.md")):
        if any(k and (k in path.stem or path.stem in k) for k in keys):
            return path
    return None


def monday_review(
    deals: list[dict[str, Any]],
    *,
    provider: Provider | str | None = None,
    workspace: Workspace | None = None,
    max_scored: int = 15,
    propose_writebacks: bool = False,
    today: _dt.date | None = None,
    concurrency: int = 3,
) -> ReviewResult:
    provider = get_provider(provider) if provider is None or isinstance(provider, str) else provider
    today = today or _dt.date.today()
    context = workspace.company_context() if workspace else None

    reviews = []
    for deal in deals:
        r = DealReview(deal=deal, flags=code_flags(deal, today))
        path = find_notes(workspace, deal)
        if path:
            r.notes_file = str(path.relative_to(workspace.root)) if workspace else str(path)
        else:
            r.flags.append("no evidence on file (no debrief notes)")
        reviews.append(r)

    with_notes = sorted([r for r in reviews if r.notes_file], key=lambda r: -(to_number(str(r.deal.get("amount") or "")) or 0))[:max_scored]

    def score(r: DealReview) -> None:
        assert workspace is not None
        text = evidence_text((workspace.root / str(r.notes_file)).read_text(encoding="utf-8"))
        try:
            ex = extract_inputs("deal-risk-assessor", text, provider=provider, context=context)
            data = {
                **ex.input,
                "deal_id": r.deal.get("deal_name") or r.deal.get("deal_id"),
                "stage": r.deal.get("stage"),
                "close_date": r.deal.get("close_date"),
            }
            r.risk = run_skill("deal-risk-assessor", data, provider=provider, context=context).output
        except (ProviderError, SkillOutputError, ValueError) as e:
            r.flags.append(f"couldn't score from notes: {e}")

    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
        list(pool.map(score, with_notes))

    for r in reviews:
        band = str((r.risk or {}).get("risk_band", "")).lower().replace("-", " ")
        flag_points = sum(next((w for k, w in FLAG_WEIGHT.items() if k in f), 1) for f in r.flags)
        band_points = next((w for k, w in BAND_WEIGHT.items() if k in band), 0)
        r.priority = flag_points + band_points + (1 if (r.risk or {}).get("single_point_of_failure") else 0)
    reviews.sort(key=lambda r: (-r.priority, -(to_number(str(r.deal.get("amount") or "")) or 0)))

    spec = load_playbook("monday-review")
    table: list[dict[str, Any]] = [
        {
            "deal": r.deal.get("deal_name") or r.deal.get("deal_id"),
            "company": r.deal.get("company"),
            "amount": r.deal.get("amount"),
            "stage": r.deal.get("stage"),
            "close_date": r.deal.get("close_date"),
            "flags": r.flags,
            "meddpicc": (r.risk or {}).get("total_score"),
            "risk_band": (r.risk or {}).get("risk_band"),
            "single_point_of_failure": (r.risk or {}).get("single_point_of_failure"),
            "priority_action": (r.risk or {}).get("priority_action"),
            "priority": r.priority,
        }
        for r in reviews
    ]
    focus = [
        f"{i}. {row['deal']}: {', '.join(row['flags']) or 'scored from notes'}"
        + (f"; risk {row['risk_band']} ({row['meddpicc']}/24)" if row["risk_band"] else "")
        for i, row in enumerate(table[:3], 1)
    ]
    user = (
        (f"## Company context\n\n{context}\n\n" if context else "")
        + f"## Today\n\n{today.isoformat()}\n\n"
        + "## This week's focus: write these items in exactly this order (decided in code)\n\n"
        + "\n".join(focus)
        + f"\n\n## Deals (ranked by priority, computed in code)\n\n```json\n{json.dumps(table, indent=2, ensure_ascii=False)}\n```"
    )
    top = str(table[0]["deal"]) if table else ""
    report = ""
    message = user
    for _ in range(3):
        report = _clean_markdown(
            provider.complete(system=_report_prompt(spec), user=message, schema=None, skill="monday-review:report").text
        )
        headings_ok = all(f"## {h}".lower() in report.lower() for h in spec["report"]["headings"])
        if headings_ok and (not top or _first_focus_item(report).lower().find(top.lower()) >= 0):
            break
        message = (
            user + f"\n\nYour previous draft broke the rules: every heading is required, and focus item 1 must be {top!r}. Rewrite it."
        )
    result = ReviewResult(deals=reviews, report=report)

    if workspace:
        path = workspace.gtm / "reviews" / f"{today.isoformat()}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# Pipeline review {today.isoformat()}\n\n{report}\n", encoding="utf-8")
        result.saved_to = str(path.relative_to(workspace.root))
        if propose_writebacks:
            for r in reviews:
                if r.deal.get("source") != "hubspot" or not r.risk:
                    continue
                changes = {
                    "b2b_risk_band": r.risk.get("risk_band"),
                    "b2b_meddpicc_score": r.risk.get("total_score"),
                    "b2b_next_action": r.risk.get("priority_action"),
                    "b2b_last_review": today.isoformat(),
                }
                result.proposed.append(
                    propose(
                        workspace,
                        target="hubspot",
                        object_type="deal",
                        object_id=str(r.deal["deal_id"]),
                        label=str(r.deal.get("deal_name")),
                        changes=changes,
                        reason=f"Monday review {today.isoformat()}: {', '.join(r.flags) or 'scored from deal notes'}",
                    )
                )
        workspace.log_run({"type": "playbook", "playbook": "monday-review", "deals": table, "proposed": [c["id"] for c in result.proposed]})
    return result
