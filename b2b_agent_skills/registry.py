"""Discover and load skill definitions.

Each skill lives in a directory containing ``SKILL.md`` (instructions with YAML
frontmatter) and ``schema.json`` (the JSON Schema its output must satisfy). The
same directories are used by Claude Code, the Claude Code plugin, the MCP
server, and this SDK, so there is one copy of every skill.

Lookup order for the skills directory:

1. ``B2B_SKILLS_DIR`` environment variable, if set.
2. ``_skills/`` bundled inside the installed package (wheel installs).
3. ``.claude/skills/`` at the repository root (editable installs / git checkout).
"""

from __future__ import annotations

import copy
import json
import os
import re
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Any

from .errors import SkillNotFoundError

_PACKAGE_DIR = Path(__file__).resolve().parent
_FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)

# JSON Schema keywords that are documentation only. They are stripped before a
# schema is sent to a model provider (some structured-output APIs reject them).
_ANNOTATION_KEYS = ("$schema", "title", "description", "examples")


@dataclass(frozen=True)
class Skill:
    """A single skill: its instructions plus its output contract."""

    name: str
    description: str
    instructions: str
    schema: dict[str, Any] = field(repr=False)
    path: Path = field(repr=False)

    @property
    def example_output(self) -> dict[str, Any] | None:
        """The worked-example output from the skill's README, if documented."""
        examples = self.schema.get("examples") or []
        return copy.deepcopy(examples[0]) if examples else None

    @property
    def output_schema(self) -> dict[str, Any]:
        """The schema with documentation-only keys removed, ready to send to a provider."""
        return {k: v for k, v in self.schema.items() if k not in _ANNOTATION_KEYS}

    @property
    def output_fields(self) -> list[str]:
        return list(self.schema.get("required", []))


def skills_dir() -> Path:
    override = os.getenv("B2B_SKILLS_DIR")
    if override:
        return Path(override).expanduser().resolve()
    bundled = _PACKAGE_DIR / "_skills"
    if bundled.is_dir():
        return bundled
    return _PACKAGE_DIR.parent / ".claude" / "skills"


def normalize_name(name: str) -> str:
    """Accept ``deal_risk_assessor`` or ``deal-risk-assessor``; return the slug."""
    return name.strip().replace("_", "-").lower()


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = _FRONTMATTER.match(text)
    if not match:
        return {}, text.strip()
    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, match.group(2).strip()


@cache
def _load(directory: str, slug: str) -> Skill:
    skill_dir = Path(directory) / slug
    skill_md = skill_dir / "SKILL.md"
    schema_path = skill_dir / "schema.json"
    if not skill_md.is_file():
        raise SkillNotFoundError(slug, available=list_skills())
    meta, body = _parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8")) if schema_path.is_file() else {}
    return Skill(
        name=meta.get("name", slug),
        description=meta.get("description", ""),
        instructions=body,
        schema=schema,
        path=skill_dir,
    )


def get_skill(name: str) -> Skill:
    """Load a skill by name (dashes or underscores)."""
    return _load(str(skills_dir()), normalize_name(name))


def list_skills() -> list[str]:
    """All available skill slugs, sorted."""
    root = skills_dir()
    if not root.is_dir():
        return []
    return sorted(p.parent.name for p in root.glob("*/SKILL.md"))
