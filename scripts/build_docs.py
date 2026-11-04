#!/usr/bin/env python3
"""Copy the skill packs into docs/ and generate the skill catalog page.

The pack READMEs stay the source of truth; this script mirrors them into
docs/<pack>/ (git-ignored) so MkDocs can render them. Relative links between
copied files keep working because the directory layout is preserved; links to
anything outside docs/ (SKILL.md, schema.json, code) are rewritten to GitHub.

    python scripts/build_docs.py && mkdocs serve
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS = REPO_ROOT / "docs"
GITHUB_BLOB = "https://github.com/pratsy/B2B_agent_skills/blob/main/"
PACKS = {
    "b2b-agent-skills-sales": "Sales",
    "b2b-agent-skills-marketing": "Marketing",
    "b2b-agent-skills-revops": "RevOps",
    "b2b-agent-skills-gtm": "GTM",
}
LINK = re.compile(r"\]\(([^)\s#]+)(#[^)\s]*)?\)")


def rewrite_links(text: str, source: Path, copied: set[Path]) -> str:
    def repl(m: re.Match[str]) -> str:
        target, anchor = m.group(1), m.group(2) or ""
        if re.match(r"[a-z]+:", target):
            return m.group(0)
        resolved = (source.parent / target).resolve()
        if resolved in copied:
            return m.group(0)
        if resolved.is_relative_to(REPO_ROOT):
            return f"]({GITHUB_BLOB}{resolved.relative_to(REPO_ROOT).as_posix()}{anchor})"
        return m.group(0)

    return LINK.sub(repl, text)


def summary(slug: str) -> str:
    """The 'what it does' half of the SKILL.md description (before 'Use when')."""
    text = (REPO_ROOT / ".claude" / "skills" / slug / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r"^description:\s*(.+)$", text, re.M)
    return match.group(1).split(" Use when")[0].strip() if match else ""


def main() -> None:
    sources = [p for pack in PACKS for p in (REPO_ROOT / pack).rglob("*.md")]
    copied = {p.resolve() for p in sources}
    for pack in PACKS:
        shutil.rmtree(DOCS / pack, ignore_errors=True)
    for src in sources:
        dest = DOCS / src.relative_to(REPO_ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(rewrite_links(src.read_text(encoding="utf-8"), src, copied), encoding="utf-8")

    golden = {p.stem for p in (REPO_ROOT / "evals" / "golden").glob("*.json")}
    lines = [
        "# Skill catalog",
        "",
        "All 48 skills. Each page has the methodology, scoring model, inputs, a worked example, and the output schema. ",
        "✅ marks skills with golden eval cases that check the actual answer, not just the output shape.",
        "",
    ]
    for pack, label in PACKS.items():
        lines += [f"## {label}", "", "| Skill | What it does | Golden evals |", "|---|---|---|"]
        for readme in sorted((REPO_ROOT / pack / "skills").glob("*/README.md")):
            slug = readme.parent.name
            summary_text = summary(slug).replace("|", "/")
            lines.append(f"| [`{slug}`]({pack}/skills/{slug}/README.md) | {summary_text} | {'✅' if slug in golden else ''} |")
        lines.append("")
    (DOCS / "skills.md").write_text("\n".join(lines), encoding="utf-8")
    total = sum(len(json.loads(p.read_text())["cases"]) for p in (REPO_ROOT / "evals" / "golden").glob("*.json"))
    print(f"copied {len(sources)} pages; catalog lists {len(golden)} skills with {total} golden cases")


if __name__ == "__main__":
    main()
