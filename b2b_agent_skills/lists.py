"""Score a lead/account list (score-list playbook) and run any skill over CSV rows (batch)."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .calculators import fit_score
from .errors import ProviderError, SkillOutputError, SkillsError
from .providers import Provider, get_provider
from .registry import get_skill
from .runner import run_skill
from .tables import flatten, map_columns, read_csv, write_csv
from .validation import extract_json
from .workspace import Workspace

ANGLE_CHUNK = 25

ANGLES_PROMPT = """You help a founder prioritize outreach. For each lead below (already ranked by ICP fit, computed in code), write:
- `why`: one sentence on why this lead is worth contacting now, using ONLY the lead's own fields and the fit reasons. Don't invent facts about the lead (funding, news, hiring) that aren't in its fields.
- `opening_line`: a first line for a cold email or LinkedIn message, specific to the lead's role and company type and to what the seller does (from the company context). No flattery, no made-up personal details, under 30 words.

Never invent: no statistics or benchmarks ("most VPs lose 2 deals a quarter"), no claims about what customers or peers say ("RevOps leaders tell us..."), no results or proof points unless they appear in the company context. Quote field values exactly as given (write "51-200 employees", never a computed number). Phrase the problem as a question or an observation about their role, not as a fact you can't back up.

Return JSON: {"leads": [{"row": <row number>, "why": "...", "opening_line": "..."}]} - one entry per lead, same row numbers. End with the JSON in a ```json block."""


@dataclass
class ListResult:
    rows: list[dict[str, Any]]
    mapping: dict[str, str]
    counts: dict[str, int]
    report: str
    saved_csv: str | None = None
    saved_report: str | None = None
    warnings: list[str] = field(default_factory=list)


def _angles(chunk: list[dict[str, Any]], provider: Provider, context: str | None) -> dict[int, dict[str, str]]:
    payload = [{"row": r["_row"], **{k: v for k, v in r["_fields"].items() if v}, "fit_reasons": r["fit_reasons"]} for r in chunk]
    user = (
        f"## Company context (the seller)\n\n{context}\n\n" if context else ""
    ) + f"## Leads\n\n```json\n{json.dumps(payload, indent=2)}\n```"
    from .playbooks import unsupported_claims

    out: dict[int, dict[str, str]] = {}
    message = user
    for _ in range(2):
        completion = provider.complete(system=ANGLES_PROMPT, user=message, schema=None, skill="score-list:angles")
        try:
            data = extract_json(completion.text)
        except ValueError:
            return out
        leads = data.get("leads", []) if isinstance(data, dict) else []
        out = {int(x["row"]): x for x in leads if isinstance(x, dict) and str(x.get("row", "")).isdigit()}
        bad = sorted({c for x in out.values() for c in unsupported_claims(f"{x.get('why', '')} {x.get('opening_line', '')}")})
        if not bad:
            return out
        message = (
            user
            + f"\n\nYour previous answer made unsupported generalizations ({'; '.join(bad)}). Rewrite every line using only the lead's own fields."
        )
    for x in out.values():  # still generalizing after a retry: drop those lines rather than ship them
        if unsupported_claims(f"{x.get('why', '')} {x.get('opening_line', '')}"):
            x["why"], x["opening_line"] = "", ""
    return out


def score_list(
    csv_path: str | Path,
    icp: dict[str, Any],
    *,
    provider: Provider | str | None = None,
    workspace: Workspace | None = None,
    overrides: dict[str, str] | None = None,
    top: int = 50,
    output: str | Path | None = None,
    concurrency: int = 2,
) -> ListResult:
    """Fit-score every row in code, then write reasons and opening lines for the top ``top`` with the LLM."""
    if not icp:
        raise SkillsError(
            "no ICP to score against. Run the find-icp playbook, or write gtm/icp.json (see `b2b-skills playbook show score-list`)."
        )
    headers, raw_rows = read_csv(csv_path)
    if not raw_rows:
        raise SkillsError(f"{csv_path} has no rows")
    mapping = map_columns(headers, overrides)
    warnings = []
    needed = {"industry", "employees", "title", "geography", "technologies"}
    if not needed & set(mapping):
        warnings.append(f"none of the ICP columns were recognized in {headers}; map them with --map field=Column")

    scored: list[dict[str, Any]] = []
    for i, raw in enumerate(raw_rows, start=1):
        fields = {f: raw.get(h, "") for f, h in mapping.items()}
        fit = fit_score(fields, icp)
        scored.append(
            {
                "_row": i,
                "_raw": raw,
                "_fields": fields,
                "fit_score": fit.score,
                "fit_tier": fit.tier,
                "fit_reasons": "; ".join(fit.reasons),
                "unknown": ", ".join(fit.unknown),
            }
        )
    scored.sort(key=lambda r: (r["fit_score"] is None, -(r["fit_score"] or 0), r["_row"]))

    head = [r for r in scored if r["fit_tier"] in ("A", "B")][:top]
    if head and provider is not None:
        provider = get_provider(provider) if isinstance(provider, str) else provider
        context = workspace.company_context() if workspace else None
        chunks = [head[i : i + ANGLE_CHUNK] for i in range(0, len(head), ANGLE_CHUNK)]
        with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
            for angles in pool.map(lambda c: _angles(c, provider, context), chunks):
                for r in head:
                    if r["_row"] in angles:
                        r["why"] = angles[r["_row"]].get("why", "")
                        r["opening_line"] = angles[r["_row"]].get("opening_line", "")

    counts: dict[str, int] = {}
    for r in scored:
        counts[r["fit_tier"]] = counts.get(r["fit_tier"], 0) + 1
    out_rows = [
        {
            **r["_raw"],
            "fit_score": r["fit_score"],
            "fit_tier": r["fit_tier"],
            "fit_reasons": r["fit_reasons"],
            "unknown_fields": r["unknown"],
            "why": r.get("why", ""),
            "opening_line": r.get("opening_line", ""),
        }
        for r in scored
    ]
    report = _list_report(scored, head, counts, mapping, warnings)
    result = ListResult(rows=out_rows, mapping=mapping, counts=counts, report=report, warnings=warnings)

    target = Path(output) if output else (workspace.gtm / "lists" / f"{Path(csv_path).stem}-scored.csv" if workspace else None)
    if target:
        target.parent.mkdir(parents=True, exist_ok=True)
        write_csv(target, out_rows, first=headers)
        result.saved_csv = str(target)
    if workspace:
        md = workspace.gtm / "lists" / f"{Path(csv_path).stem}.md"
        md.parent.mkdir(parents=True, exist_ok=True)
        md.write_text(report, encoding="utf-8")
        result.saved_report = str(md.relative_to(workspace.root))
        workspace.log_run(
            {
                "type": "playbook",
                "playbook": "score-list",
                "subject": Path(csv_path).name,
                "counts": counts,
                "top": [r["_row"] for r in head],
            }
        )
    return result


def _label(fields: dict[str, str]) -> str:
    who = " - ".join(x for x in (fields.get("name"), fields.get("title")) if x)
    company = fields.get("company") or fields.get("domain") or ""
    return f"{who} @ {company}" if who and company else who or company or "(unnamed)"


def _list_report(
    scored: list[dict[str, Any]], head: list[dict[str, Any]], counts: dict[str, int], mapping: dict[str, str], warnings: list[str]
) -> str:
    lines = [
        "# Scored list",
        "",
        f"{len(scored)} rows: " + ", ".join(f"{counts.get(t, 0)} {t}" for t in ("A", "B", "C", "skip", "unknown")),
        "",
    ]
    lines += [
        "Tiers: A (80+) contact this week · B (60-79) next · C (40-59) nurture · skip (<40 or excluded) · unknown (not enough data to score)",
        "",
    ]
    lines.append("Columns used: " + ", ".join(f'{f} ← "{h}"' for f, h in mapping.items()))
    lines += [f"> ⚠ {w}" for w in warnings] + ["", f"## Top {len(head)}", ""]
    for n, r in enumerate(head, 1):
        lines.append(f"{n}. **{_label(r['_fields'])}** - fit {r['fit_score']:.0f} ({r['fit_tier']})")
        lines.append(f"   - Why: {r.get('why') or r['fit_reasons']}")
        if r.get("opening_line"):
            lines.append(f"   - Opening line: {r['opening_line']}")
    unknown = counts.get("unknown", 0)
    if unknown:
        lines += ["", f"{unknown} rows couldn't be scored (too few known fields). Enrich them with industry, size, and title, then re-run."]
    return "\n".join(lines) + "\n"


def batch_skill(
    skill: str,
    csv_path: str | Path,
    *,
    provider: Provider | str | None = None,
    overrides: dict[str, str] | None = None,
    output: str | Path | None = None,
    concurrency: int = 2,
    context: str | None = None,
    limit: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Run ``skill`` once per CSV row. Columns are matched to the skill's input fields by name."""
    spec = get_skill(skill)
    if provider is None or isinstance(provider, str):
        provider = get_provider(provider)
    headers, rows = read_csv(csv_path)
    rows = rows[:limit] if limit else rows
    fields = list(spec.input_fields)
    mapping = map_columns(headers, overrides, fields=fields)
    for h in headers:  # columns already named like an input field
        if h in fields and h not in mapping:
            mapping[h] = h

    def run(row: dict[str, str]) -> dict[str, Any]:
        data: dict[str, Any] = {f: row[h] for f, h in mapping.items() if row.get(h)}
        data.update({f"_{k}": v for k, v in row.items() if k not in mapping.values() and v})
        try:
            result = run_skill(spec.name, data, provider=provider, context=context, raise_on_invalid=False)
            return {**row, **flatten("", result.output or {}), "_valid": result.valid, "_errors": "; ".join(result.errors[:3])}
        except (ProviderError, SkillOutputError, ValueError) as e:
            return {**row, "_valid": False, "_errors": str(e)}

    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
        out = list(pool.map(run, rows))
    if output:
        write_csv(output, out, first=headers)
    return out, mapping
