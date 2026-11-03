"""Read notes and call transcripts (.txt, .md, .vtt, .srt, .json exports) as plain text."""

from __future__ import annotations

import json
import re
from pathlib import Path

NOTE_SUFFIXES = {".txt", ".md", ".markdown", ".vtt", ".srt", ".json"}
_TIMESTAMP = re.compile(r"^\s*(\d+\s*)?$|^\s*\d{1,2}:\d{2}(:\d{2})?[.,]\d{1,3}\s*-->.*$|^WEBVTT.*$|^NOTE\b.*$")


def read_notes(path: str | Path) -> str:
    """Return the text of a notes/transcript file, with subtitle timing stripped."""
    p = Path(path)
    raw = p.read_text(encoding="utf-8", errors="replace")
    suffix = p.suffix.lower()
    if suffix in {".vtt", ".srt"}:
        lines = [ln for ln in raw.splitlines() if not _TIMESTAMP.match(ln)]
        cleaned = [re.sub(r"<v\s+([^>]+)>", r"\1: ", ln).replace("</v>", "") for ln in lines]
        return "\n".join(ln for ln in cleaned if ln.strip())
    if suffix == ".json":
        data = json.loads(raw)
        return _json_transcript(data)
    return raw


def _json_transcript(data: object) -> str:
    """Best effort for JSON exports: a list of {speaker, text} segments, or an object with a transcript field."""
    if isinstance(data, dict):
        for key in ("transcript", "text", "content", "segments", "utterances"):
            if key in data:
                return _json_transcript(data[key])
        return json.dumps(data, indent=2)
    if isinstance(data, list):
        out = []
        for seg in data:
            if isinstance(seg, dict):
                speaker = seg.get("speaker") or seg.get("speaker_name") or seg.get("name") or ""
                text = seg.get("text") or seg.get("content") or seg.get("words") or ""
                out.append(f"{speaker}: {text}" if speaker else str(text))
            else:
                out.append(str(seg))
        return "\n".join(out)
    return str(data)
