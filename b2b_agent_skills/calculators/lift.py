"""Attribute lift: which account attributes are over-represented among your best customers.

    lift = (share of best accounts with the attribute) / (share of all accounts with it)

> 1.5 strong positive signal, 1.0-1.5 weak, < 1.0 negative. Fewer than 15 best
accounts with an attribute is flagged low confidence: small samples make lift noisy.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from ..tables import to_number

SIZE_BANDS = ((1, 10), (11, 50), (51, 200), (201, 500), (501, 1000), (1001, 5000), (5001, 10**9))
WON = {"won", "closed won", "closed-won", "customer", "yes", "true", "1", "active", "best"}


@dataclass
class AttributeLift:
    attribute: str
    value: str
    best_with: int
    best_total: int
    all_with: int
    all_total: int
    lift: float
    confidence: str
    signal: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def size_band(employees: Any) -> str | None:
    n = to_number(employees)
    if n is None:
        return None
    lo, hi = next(b for b in SIZE_BANDS if b[0] <= n <= b[1])
    return f"{lo}-{hi}" if hi < 10**9 else f"{lo}+"


def is_best(row: dict[str, Any]) -> bool:
    return str(row.get("outcome", "")).strip().lower() in WON


def _values(row: dict[str, Any], attribute: str) -> list[str]:
    if attribute == "size":
        band = size_band(row.get("employees"))
        return [band] if band else []
    raw = str(row.get(attribute) or "").strip()
    if not raw:
        return []
    parts = [p.strip().lower() for p in raw.replace(";", ",").split(",")] if attribute == "technologies" else [raw.lower()]
    return [p for p in parts if p]


def attribute_lifts(
    rows: list[dict[str, Any]], attributes: tuple[str, ...] = ("industry", "size", "geography", "title", "technologies")
) -> list[AttributeLift]:
    best = [r for r in rows if is_best(r)]
    if not best or len(best) == len(rows):
        raise ValueError("need both best accounts (outcome = won/customer) and others to compare against")
    out: list[AttributeLift] = []
    for attribute in attributes:
        counts_all: dict[str, int] = {}
        counts_best: dict[str, int] = {}
        for r in rows:
            for v in set(_values(r, attribute)):
                counts_all[v] = counts_all.get(v, 0) + 1
                if is_best(r):
                    counts_best[v] = counts_best.get(v, 0) + 1
        for value, n_all in counts_all.items():
            n_best = counts_best.get(value, 0)
            if n_all < 2:
                continue
            lift = round((n_best / len(best)) / (n_all / len(rows)), 2)
            signal = "positive" if lift > 1.5 else "negative" if lift < 1.0 else "weak"
            confidence = "high" if n_best >= 15 else "low"
            out.append(AttributeLift(attribute, value, n_best, len(best), n_all, len(rows), lift, confidence, signal))
    return sorted(out, key=lambda a: (-a.lift, -a.best_with))


def propose_icp(lifts: list[AttributeLift], current: dict[str, Any] | None = None) -> dict[str, Any]:
    """Draft gtm/icp.json from lift results: include positive signals, exclude clearly negative ones."""
    icp: dict[str, Any] = {k: v for k, v in (current or {}).items() if k in ("weights",)}
    keys = {"industry": "industries", "geography": "geographies", "title": "titles", "technologies": "technologies"}
    for attr, key in keys.items():
        pos = [a.value for a in lifts if a.attribute == attr and a.signal == "positive" and a.best_with >= 2]
        if pos:
            icp[key] = pos
    sizes = [a.value for a in lifts if a.attribute == "size" and a.signal == "positive" and a.best_with >= 2]
    if sizes:
        bounds = [int(s.rstrip("+").split("-")[0]) for s in sizes] + [int(s.split("-")[1]) for s in sizes if "-" in s]
        icp["employee_range"] = [min(bounds), max(bounds)]
    exclude: dict[str, list[str]] = {}
    for attr, key in (("industry", "industries"), ("title", "titles")):
        neg = [a.value for a in lifts if a.attribute == attr and a.lift == 0 and a.all_with >= 3]
        if neg:
            exclude[key] = neg
    if exclude:
        icp["exclude"] = exclude
    return icp
