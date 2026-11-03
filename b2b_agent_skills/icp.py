"""find-icp playbook: who to sell to, from your customer list and interview notes."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .calculators import attribute_lifts, propose_icp
from .errors import ProviderError, SkillOutputError, SkillsError
from .extraction import extract_inputs
from .playbooks import _clean_markdown, _report_prompt, load_playbook
from .providers import Provider, get_provider
from .runner import run_skill
from .tables import map_columns, read_csv
from .workspace import Workspace

ICP_FIELDS = ["company", "industry", "employees", "geography", "title", "technologies", "outcome", "value"]


@dataclass
class IcpResult:
    report: str
    lifts: list[dict[str, Any]] = field(default_factory=list)
    proposed_icp: dict[str, Any] = field(default_factory=dict)
    persona: dict[str, Any] | None = None
    refinement: dict[str, Any] | None = None
    saved: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def find_icp(
    *,
    customers_csv: str | Path | None = None,
    notes: list[str] | None = None,
    provider: Provider | str | None = None,
    workspace: Workspace | None = None,
    overrides: dict[str, str] | None = None,
    apply: bool = False,
) -> IcpResult:
    if not customers_csv and not notes:
        raise SkillsError("give a customer list (--customers accounts.csv with an outcome column) and/or interview notes (--notes)")
    provider = get_provider(provider) if provider is None or isinstance(provider, str) else provider
    context = workspace.company_context() if workspace else None
    current = workspace.icp() if workspace else {}
    result = IcpResult(report="")

    rows: list[dict[str, Any]] = []
    if customers_csv:
        headers, raw = read_csv(customers_csv)
        mapping = map_columns(headers, overrides, fields=ICP_FIELDS)
        if "outcome" not in mapping:
            raise SkillsError(
                f"the customer list needs an outcome column (won/lost or customer/prospect); columns: {', '.join(headers)}. Use --map outcome=<column>."
            )
        rows = [{f: r.get(h, "") for f, h in mapping.items()} for r in raw]
        lifts = attribute_lifts(rows)
        result.lifts = [a.to_dict() for a in lifts]
        result.proposed_icp = propose_icp(lifts, current)
        best = sum(
            1
            for r in rows
            if str(r.get("outcome", "")).lower() in {"won", "closed won", "closed-won", "customer", "yes", "true", "1", "active", "best"}
        )
        if best < 15:
            result.notes.append(f"provisional (n={best} best accounts): lift on fewer than ~15 accounts is noisy")

    def persona_step() -> dict[str, Any] | None:
        if not notes:
            return None
        try:
            ex = extract_inputs("persona-insight-extractor", notes, provider=provider, context=context)
            return run_skill(
                "persona-insight-extractor", {**ex.input, "source_count": len(notes)}, provider=provider, context=context
            ).output
        except (ProviderError, SkillOutputError, ValueError) as e:
            result.notes.append(f"persona extraction failed: {e}")
            return None

    def refinement_step() -> dict[str, Any] | None:
        if not result.lifts:
            return None
        data = {
            "best_account_definition": {"metric": "outcome", "threshold": "won / current customer"},
            "current_icp_definition": current or "see company context",
            "precomputed_lifts": result.lifts,
            "_instruction": "Lift was computed exactly in code from the customer list (precomputed_lifts). Use these numbers as given; do not recompute.",
        }
        try:
            return run_skill("icp-refinement-agent", data, provider=provider, context=context).output
        except (ProviderError, SkillOutputError) as e:
            result.notes.append(f"ICP refinement failed: {e}")
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        persona_future, refinement_future = pool.submit(persona_step), pool.submit(refinement_step)
        result.persona, result.refinement = persona_future.result(), refinement_future.result()

    spec = load_playbook("find-icp")
    payload = {
        "exact_attribute_lifts": result.lifts[:25],
        "icp_refinement": result.refinement,
        "persona_insights": result.persona,
        "proposed_icp_json": result.proposed_icp,
        "current_icp_json": current,
        "caveats": result.notes,
    }
    user = (
        f"## Company context\n\n{context}\n\n" if context else ""
    ) + f"## Results\n\n```json\n{json.dumps(payload, indent=2, ensure_ascii=False)}\n```"
    for _ in range(2):
        report = _clean_markdown(provider.complete(system=_report_prompt(spec), user=user, schema=None, skill="find-icp:report").text)
        if all(f"## {h}".lower() in report.lower() for h in spec["report"]["headings"]):
            break
    result.report = report

    if workspace:
        md = workspace.gtm / "icp.md"
        workspace.append_note(md, "ICP analysis", report)
        result.saved["report"] = str(md.relative_to(workspace.root))
        if result.proposed_icp:
            target = workspace.gtm / ("icp.json" if apply else "icp.proposed.json")
            target.write_text(json.dumps(result.proposed_icp, indent=2) + "\n", encoding="utf-8")
            result.saved["icp"] = str(target.relative_to(workspace.root))
        workspace.log_run(
            {"type": "playbook", "playbook": "find-icp", "lifts": result.lifts, "proposed_icp": result.proposed_icp, "applied": apply}
        )
    return result
