"""CSV in, CSV out: read exports from Apollo, Clay, HubSpot, LinkedIn and map their columns."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

# Canonical field -> header aliases seen in common exports (compared after normalizing).
ALIASES: dict[str, list[str]] = {
    "company": ["company", "company name", "account", "account name", "organization", "organization name", "company_name"],
    "domain": ["domain", "website", "company domain", "company website", "url", "company url"],
    "industry": ["industry", "industries", "sector", "vertical", "company industry"],
    "employees": [
        "employees",
        "employee count",
        "# employees",
        "number of employees",
        "headcount",
        "company size",
        "size",
        "num employees",
        "estimated num employees",
    ],
    "geography": ["country", "geography", "location", "region", "hq country", "company country", "hq location", "state", "city"],
    "title": ["title", "job title", "position", "role", "contact title"],
    "name": ["name", "full name", "contact name", "first name"],
    "email": ["email", "email address", "work email"],
    "technologies": ["technologies", "tech stack", "technology", "tools", "installed technologies"],
    "seniority": ["seniority", "management level", "level"],
    "last_activity": ["last activity", "last activity date", "last engaged", "last touch", "last visit"],
    "engagement": ["engagement", "page views", "visits", "email opens", "intent", "intent score", "activity count"],
    "outcome": ["outcome", "status", "result", "stage", "deal stage", "won", "closed won", "is won"],
    "value": ["value", "amount", "deal value", "acv", "arr", "revenue", "deal amount"],
}


def _norm(header: str) -> str:
    return re.sub(r"[^a-z0-9#]+", " ", header.lower()).strip()


def read_csv(path: str | Path) -> tuple[list[str], list[dict[str, str]]]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect: Any = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(f, dialect=dialect)
        rows = [{k.strip(): (v or "").strip() for k, v in row.items() if k} for row in reader]
        return [h.strip() for h in (reader.fieldnames or [])], rows


def map_columns(
    headers: list[str],
    overrides: dict[str, str] | None = None,
    fields: list[str] | None = None,
    aliases: dict[str, list[str]] | None = None,
) -> dict[str, str]:
    """Map canonical field -> CSV header. Exact alias match first, then 'alias contained in header'."""
    overrides = overrides or {}
    table = {**ALIASES, **(aliases or {})}
    wanted = fields or list(table)
    mapping: dict[str, str] = {}
    used: set[str] = set()
    for field, header in overrides.items():
        if header not in headers:
            raise ValueError(f"--map {field}={header!r}: no such column. Columns: {', '.join(headers)}")
        mapping[field] = header
        used.add(header)
    normalized = {h: _norm(h) for h in headers}
    for exact in (True, False):
        for field in wanted:
            if field in mapping:
                continue
            for alias in table.get(field, [_norm(field)]):
                hit = next(
                    (
                        h
                        for h, n in normalized.items()
                        if h not in used and (n == alias if exact else re.search(rf"\b{re.escape(alias)}\b", n))
                    ),
                    None,
                )
                if hit:
                    mapping[field] = hit
                    used.add(hit)
                    break
    return mapping


def parse_overrides(pairs: list[str] | None) -> dict[str, str]:
    out = {}
    for pair in pairs or []:
        if "=" not in pair:
            raise ValueError(f"--map expects field=Column Name, got {pair!r}")
        field, header = pair.split("=", 1)
        out[field.strip()] = header.strip()
    return out


def to_number(value: str | None) -> float | None:
    if value is None:
        return None
    text = str(value).strip().lower().replace(",", "")
    if not text:
        return None
    rng = re.match(r"^\$?(\d+(?:\.\d+)?)\s*[kmb]?\s*[-–to]+\s*\$?(\d+(?:\.\d+)?)\s*([kmb]?)", text)
    if rng:  # "51-200" -> midpoint
        lo, hi = float(rng.group(1)), float(rng.group(2))
        return _scale((lo + hi) / 2, rng.group(3))
    m = re.match(r"^\$?(\d+(?:\.\d+)?)\s*([kmb]?)\+?", text)
    return _scale(float(m.group(1)), m.group(2)) if m else None


def _scale(n: float, suffix: str) -> float:
    return n * {"k": 1e3, "m": 1e6, "b": 1e9}.get(suffix, 1)


def flatten(prefix: str, value: Any) -> dict[str, str]:
    """Flatten a skill output into CSV columns: scalars as-is, nested values as JSON."""
    if isinstance(value, dict):
        out: dict[str, str] = {}
        for k, v in value.items():
            out.update(
                flatten(f"{prefix}{k}" if not prefix else f"{prefix}.{k}", v)
                if isinstance(v, dict)
                else {f"{prefix}.{k}" if prefix else k: _cell(v)}
            )
        return out
    return {prefix: _cell(value)}


def _cell(v: Any) -> str:
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False)
    return "" if v is None else str(v)


def write_csv(path: str | Path, rows: list[dict[str, Any]], first: list[str] | None = None) -> None:
    columns: list[str] = list(first or [])
    for row in rows:
        for k in row:
            if k not in columns:
                columns.append(k)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
