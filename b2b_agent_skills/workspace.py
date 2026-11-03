"""A GTM workspace: the folder where a company's context, deals, and run history live.

    my-gtm/
      company.md          what the company sells, to whom, against whom (written by `b2b-skills init`)
      CLAUDE.md           operating rules for an agent working in this folder
      .mcp.json           connects Claude Code to the b2b-agent-skills MCP server
      gtm/
        icp.json          structured ICP (used for list scoring)
        deals/<deal>.md   per-deal notes: every debrief is appended here
        accounts/         per-account notes
        runs/YYYY-MM.jsonl  log of every skill and playbook run (inputs, outputs, model)

Everything is plain files, so it can be read, edited, and versioned in git.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CONTEXT_FILE = "company.md"


def find_workspace(start: str | Path | None = None) -> Workspace | None:
    """Locate the workspace: $B2B_WORKSPACE, else the nearest folder (upwards) containing company.md."""
    env = os.getenv("B2B_WORKSPACE")
    if env:
        root = Path(env).expanduser().resolve()
        return Workspace(root) if (root / CONTEXT_FILE).is_file() else None
    here = Path(start or Path.cwd()).resolve()
    for folder in (here, *here.parents):
        if (folder / CONTEXT_FILE).is_file():
            return Workspace(folder)
    return None


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:60] or "untitled"


@dataclass
class Workspace:
    root: Path

    @property
    def gtm(self) -> Path:
        return self.root / "gtm"

    def company_context(self) -> str:
        path = self.root / CONTEXT_FILE
        return path.read_text(encoding="utf-8").strip() if path.is_file() else ""

    def icp(self) -> dict[str, Any]:
        path = self.gtm / "icp.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}

    def deal_path(self, deal: str) -> Path:
        return self.gtm / "deals" / f"{slugify(deal)}.md"

    def append_note(self, path: Path, title: str, body: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        stamp = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
        header = "" if path.exists() else f"# {path.stem}\n"
        with path.open("a", encoding="utf-8") as f:
            f.write(f"{header}\n## {title} ({stamp})\n\n{body.strip()}\n")
        return path

    def log_run(self, record: dict[str, Any]) -> None:
        """Append one run to gtm/runs/YYYY-MM.jsonl (the audit trail and future calibration data)."""
        now = _dt.datetime.now()
        path = self.gtm / "runs" / f"{now:%Y-%m}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"at": now.isoformat(timespec="seconds"), **record}, ensure_ascii=False, default=str) + "\n")
