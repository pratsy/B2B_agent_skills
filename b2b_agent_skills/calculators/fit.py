"""ICP fit score (0-100) for one row of a lead/account list, against gtm/icp.json.

icp.json:
    {
      "industries": ["fintech", "saas"],          # substring match, case-insensitive
      "employee_range": [50, 500],
      "geographies": ["US", "Canada"],
      "titles": ["vp sales", "revops", "cro"],    # keywords in the contact's title
      "technologies": ["salesforce"],
      "exclude": {"industries": ["government"], "titles": ["intern"]},
      "weights": {"industry": 30, "size": 25, "title": 25, "geography": 10, "technology": 10}
    }

Criteria with no data in the row are left out and the remaining weights are
rescaled (missing data isn't scored as a mismatch); the row is flagged so the
reader knows what was unknown. Rows with fewer than two known criteria get no
score ("insufficient data").
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..tables import to_number

DEFAULT_WEIGHTS = {"industry": 30, "size": 25, "title": 25, "geography": 10, "technology": 10}
TIERS = ((80, "A"), (60, "B"), (40, "C"))


@dataclass
class FitResult:
    score: float | None
    tier: str
    reasons: list[str] = field(default_factory=list)
    unknown: list[str] = field(default_factory=list)


def _any_in(needles: list[str], haystack: str) -> str | None:
    h = haystack.lower()
    return next((n for n in needles if n and n.lower() in h), None)


def tier_for(score: float | None) -> str:
    if score is None:
        return "unknown"
    return next((t for floor, t in TIERS if score >= floor), "skip")


def fit_score(row: dict[str, Any], icp: dict[str, Any]) -> FitResult:
    weights = {**DEFAULT_WEIGHTS, **icp.get("weights", {})}
    exclude = icp.get("exclude", {})
    for key, col in (("industries", "industry"), ("titles", "title"), ("geographies", "geography")):
        hit = _any_in(exclude.get(key, []), str(row.get(col) or ""))
        if hit:
            return FitResult(0.0, "skip", [f"excluded: {col} matches '{hit}'"])

    earned, possible, reasons, unknown = 0.0, 0.0, [], []

    def criterion(name: str, value: Any, wanted: list[str] | None, label: str) -> None:
        nonlocal earned, possible
        if not wanted or not weights.get(name):
            return
        if not value:
            unknown.append(label)
            return
        possible += weights[name]
        hit = _any_in(wanted, str(value))
        if hit:
            earned += weights[name]
            reasons.append(f"{label} match ({value})")
        else:
            reasons.append(f"{label} outside ICP ({value})")

    criterion("industry", row.get("industry"), icp.get("industries"), "industry")
    criterion("title", row.get("title"), icp.get("titles"), "title")
    criterion("geography", row.get("geography"), icp.get("geographies"), "geography")
    criterion("technology", row.get("technologies"), icp.get("technologies"), "tech")

    size_range = icp.get("employee_range")
    if size_range and weights.get("size"):
        raw_size = str(row.get("employees") or "").strip()
        employees = to_number(raw_size)
        if employees is None:
            unknown.append("company size")
        else:
            lo, hi = size_range
            possible += weights["size"]
            if lo <= employees <= hi:
                earned += weights["size"]
                reasons.append(f"{raw_size} employees, in range")
            elif lo * 0.5 <= employees <= hi * 1.5:
                earned += weights["size"] * 0.5
                reasons.append(f"{raw_size} employees, near range")
            else:
                reasons.append(f"{raw_size} employees, outside range")

    known = sum(1 for r in reasons)
    if known < 2 or possible == 0:
        return FitResult(None, "unknown", reasons, unknown)
    score = round(earned / possible * 100, 1)
    return FitResult(score, tier_for(score), reasons, unknown)
