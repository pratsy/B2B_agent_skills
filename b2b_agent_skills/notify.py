"""Post digests to Slack through an incoming webhook (SLACK_WEBHOOK_URL)."""

from __future__ import annotations

import json
import os
import re
import urllib.request
from collections.abc import Callable

from .errors import SkillsError


def markdown_to_slack(text: str) -> str:
    text = re.sub(r"^#{1,6}\s*(.+)$", r"*\1*", text, flags=re.M)
    text = re.sub(r"\*\*(.+?)\*\*", r"*\1*", text)
    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"<\2|\1>", text)


def post_slack(text: str, webhook: str | None = None, send: Callable[[str, bytes], int] | None = None) -> None:
    url = webhook or os.getenv("SLACK_WEBHOOK_URL")
    if not url:
        raise SkillsError("set SLACK_WEBHOOK_URL (a Slack incoming webhook) to post digests")
    body = json.dumps({"text": markdown_to_slack(text)[:39000]}).encode()

    def _send(u: str, b: bytes) -> int:
        req = urllib.request.Request(u, data=b, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            return int(resp.status)

    status = (send or _send)(url, body)
    if status >= 300:
        raise SkillsError(f"Slack webhook returned {status}")
