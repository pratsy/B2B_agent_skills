"""Approval queue: nothing outside the workspace changes until a person approves it.

Playbooks propose changes (e.g. "set b2b_risk_band=high on HubSpot deal 123")
as JSON files in gtm/pending/. `b2b-skills pending` lists them,
`b2b-skills approve <id|all>` applies them, `b2b-skills reject <id|all>`
discards them. Applied and rejected change sets move to gtm/applied/ and
gtm/rejected/ with the outcome, so there is an audit trail.
"""

from __future__ import annotations

import datetime as _dt
import json
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .errors import SkillsError
from .workspace import Workspace


def propose(
    workspace: Workspace, *, target: str, object_type: str, object_id: str, label: str, changes: dict[str, Any], reason: str
) -> dict[str, Any]:
    change = {
        "id": uuid.uuid4().hex[:8],
        "created": _dt.datetime.now().isoformat(timespec="seconds"),
        "target": target,
        "object_type": object_type,
        "object_id": object_id,
        "label": label,
        "changes": changes,
        "reason": reason,
    }
    folder = workspace.gtm / "pending"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{change['id']}.json").write_text(json.dumps(change, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return change


def pending(workspace: Workspace) -> list[dict[str, Any]]:
    folder = workspace.gtm / "pending"
    items = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(folder.glob("*.json"))] if folder.is_dir() else []
    return sorted(items, key=lambda c: c["created"])


def _select(workspace: Workspace, which: str) -> list[dict[str, Any]]:
    items = pending(workspace)
    chosen = items if which == "all" else [c for c in items if c["id"] == which]
    if not chosen:
        raise SkillsError(f"no pending change '{which}'. Run `b2b-skills pending` to list them.")
    return chosen


def _move(workspace: Workspace, change: dict[str, Any], folder: str, **outcome: Any) -> None:
    src = workspace.gtm / "pending" / f"{change['id']}.json"
    dest = workspace.gtm / folder / src.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        json.dumps({**change, **outcome, "decided": _dt.datetime.now().isoformat(timespec="seconds")}, indent=2) + "\n", encoding="utf-8"
    )
    src.unlink()


def approve(
    workspace: Workspace, which: str, appliers: dict[str, Callable[[dict[str, Any]], Any]], dry_run: bool = False
) -> list[dict[str, Any]]:
    """Apply pending changes. ``appliers`` maps target (e.g. "hubspot") to a function that applies one change set."""
    results = []
    for change in _select(workspace, which):
        apply = appliers.get(change["target"])
        if apply is None:
            results.append({**change, "status": "skipped", "error": f"no connector configured for {change['target']}"})
            continue
        if dry_run:
            results.append({**change, "status": "would apply"})
            continue
        try:
            apply(change)
        except SkillsError as e:
            results.append({**change, "status": "failed", "error": str(e)})
            continue
        _move(workspace, change, "applied", status="applied")
        workspace.log_run({"type": "approval", "change": change, "status": "applied"})
        results.append({**change, "status": "applied"})
    return results


def reject(workspace: Workspace, which: str) -> list[dict[str, Any]]:
    out = []
    for change in _select(workspace, which):
        _move(workspace, change, "rejected", status="rejected")
        out.append({**change, "status": "rejected"})
    return out


def describe(change: dict[str, Any]) -> str:
    fields = ", ".join(f"{k} = {v!r}" for k, v in change["changes"].items())
    return f"[{change['id']}] {change['target']} {change['object_type']} {change['label']} ({change['object_id']}): {fields}\n    why: {change['reason']}"


def record_outcome(workspace: Workspace, subject: str, outcome: str, value: float | None = None, reason: str = "") -> Path:
    """Append a won/lost outcome to gtm/outcomes.csv: the data future calibration learns from."""
    import csv

    path = workspace.gtm / "outcomes.csv"
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if new:
            writer.writerow(["date", "subject", "outcome", "value", "reason"])
        writer.writerow([_dt.date.today().isoformat(), subject, outcome, "" if value is None else value, reason])
    return path
