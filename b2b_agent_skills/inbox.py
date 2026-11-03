"""Transcript inbox: drop call transcripts into gtm/inbox/ (by hand, from a Zapier/Make zap, or a
recorder's export) and `b2b-skills inbox` debriefs each new one, then moves it to gtm/inbox/processed/.

Works with any recorder that can export or forward text: Fathom, Granola, Gong, Otter, Zoom, Google Meet
(.txt, .md, .vtt, .srt, or JSON transcript exports). The deal is taken from the file name, so name files
after the deal or company (e.g. "acme-logistics-2026-11-03.vtt").
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from .playbooks import PlaybookResult, run_playbook
from .providers import Provider
from .transcripts import NOTE_SUFFIXES, read_notes
from .workspace import Workspace


@dataclass
class InboxItem:
    file: str
    subject: str
    result: PlaybookResult | None = None
    error: str | None = None


def subject_from_filename(path: Path) -> str:
    stem = re.sub(r"[-_ ]?\d{4}-\d{2}-\d{2}.*$", "", path.stem)  # drop a trailing date
    stem = re.sub(r"[-_ ]?(call|transcript|notes|meeting)$", "", stem, flags=re.I)
    return stem.replace("_", " ").replace("-", " ").strip() or path.stem


def process_inbox(workspace: Workspace, provider: Provider, playbook: str = "call-debrief") -> list[InboxItem]:
    inbox = workspace.gtm / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    done = inbox / "processed"
    items = []
    for path in sorted(p for p in inbox.iterdir() if p.is_file() and p.suffix.lower() in NOTE_SUFFIXES):
        item = InboxItem(file=path.name, subject=subject_from_filename(path))
        try:
            item.result = run_playbook(playbook, read_notes(path), provider=provider, workspace=workspace, subject=item.subject)
            done.mkdir(exist_ok=True)
            shutil.move(str(path), done / path.name)
        except Exception as e:  # keep processing the rest; the file stays in the inbox for a retry
            item.error = str(e)
        items.append(item)
    return items
