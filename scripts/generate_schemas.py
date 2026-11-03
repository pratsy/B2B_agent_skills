#!/usr/bin/env python3
"""Generate .claude/skills/<slug>/schema.json and input.schema.json from each skill's README.

The README's "## Output schema" JSON block is the single source of truth for a
skill's output shape. This script infers a strict JSON Schema from that example
(every documented key required, no extra keys) and writes it next to the
skill's SKILL.md, where the SDK, MCP server, and Claude Code plugin all read it.

The README's "## Inputs" table becomes input.schema.json: a lenient schema
(nothing required, extra fields allowed) that names and describes each input,
used to turn free-text notes and CSV rows into skill inputs.

Usage:
    python scripts/generate_schemas.py          # write schema.json files
    python scripts/generate_schemas.py --check  # exit 1 if any are stale (CI)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / ".claude" / "skills"
OUTPUT_BLOCK = re.compile(r"## Output schema\s*```json\n(.*?)```", re.S)


def _infer(value: Any) -> dict[str, Any]:
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, (int, float)):
        # "number" rather than "integer": a model writing 14.0 for 14 is not wrong.
        return {"type": "number"}
    if isinstance(value, str):
        return {"type": "string"}
    if value is None:
        return {"type": ["string", "null"]}
    if isinstance(value, list):
        return {"type": "array", "items": _infer_items(value)}
    if isinstance(value, dict):
        return {
            "type": "object",
            "properties": {k: _infer(v) for k, v in value.items()},
            "required": list(value.keys()),
            "additionalProperties": False,
        }
    raise TypeError(f"unsupported JSON value: {value!r}")


def _infer_items(items: list[Any]) -> dict[str, Any]:
    if not items:
        # The README example shows an empty list; the element type is not documented.
        return {"type": "string"}
    if all(isinstance(i, dict) for i in items):
        # Merge object elements: union of keys as properties, intersection as required.
        properties: dict[str, Any] = {}
        for item in items:
            for k, v in item.items():
                properties.setdefault(k, _infer(v))
        required = [k for k in items[0] if all(k in i for i in items)]
        return {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        }
    return _infer(items[0])


def readme_for(slug: str) -> Path:
    matches = list(REPO_ROOT.glob(f"b2b-agent-skills-*/skills/{slug}/README.md"))
    if len(matches) != 1:
        raise FileNotFoundError(f"expected exactly one README for {slug}, found {matches}")
    return matches[0]


def build_schema(slug: str) -> dict[str, Any]:
    readme = readme_for(slug)
    match = OUTPUT_BLOCK.search(readme.read_text(encoding="utf-8"))
    if not match:
        raise ValueError(f"{readme}: no '## Output schema' JSON block")
    example = json.loads(match.group(1))
    schema = _infer(example)
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": slug,
        "description": f"Output of the {slug} skill. Generated from {readme.relative_to(REPO_ROOT)} by scripts/generate_schemas.py - edit the README, not this file.",
        **schema,
        "examples": [example],
    }


INPUTS_SECTION = re.compile(r"## Inputs\s*\n(.*?)(?=\n## )", re.S)


def _split_top_level(text: str) -> list[str]:
    parts, depth, cur = [], 0, ""
    for ch in text:
        if ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur.strip())
    return parts


def _input_type(type_text: str) -> dict[str, Any]:
    t = type_text.strip().replace("\\|", "|")
    base = re.sub(r"\s*\(.*$", "", t).strip().lower()
    if base.startswith("list[") or base.startswith("["):
        inner = t[t.index("[") + 1 : t.rindex("]")].strip()
        return {"type": "array", "items": _input_type(inner)}
    if base.startswith("{"):
        keys = [k.split(":")[0].strip() for k in _split_top_level(t.strip()[1:-1])]
        return {"type": "object", "properties": {k: {} for k in keys if k}}
    if base in ("int", "integer", "float", "number"):
        return {"type": "number"}
    if base in ("bool", "boolean"):
        return {"type": "boolean"}
    if base in ("string", "date", "enum"):
        return {"type": "string"}
    if base == "object":
        return {"type": "object"}
    return {}


def build_input_schema(slug: str) -> dict[str, Any]:
    readme = readme_for(slug)
    section = INPUTS_SECTION.search(readme.read_text(encoding="utf-8"))
    if not section:
        raise ValueError(f"{readme}: no '## Inputs' table")
    properties: dict[str, Any] = {}
    for row in section.group(1).splitlines():
        if not row.startswith("| `"):
            continue
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", row)[1:-1]]
        names = re.findall(r"`([^`]+)`", cells[0])
        type_text = cells[1] if len(cells) > 1 else ""
        example = cells[2].replace("\\|", "|").strip() if len(cells) > 2 else ""
        description = type_text.replace("\\|", "|") + (f" - e.g. {example}" if example else "")
        for name in names:
            properties[name] = {**_input_type(type_text), "description": description}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": f"{slug} input",
        "description": f"Inputs for the {slug} skill. Generated from {readme.relative_to(REPO_ROOT)} by scripts/generate_schemas.py. Every field is optional: send what you have, and the skill asks for what's missing.",
        "type": "object",
        "properties": properties,
    }


def render(schema: dict[str, Any]) -> str:
    return json.dumps(schema, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="fail if any schema.json is missing or stale")
    args = parser.parse_args()

    stale = []
    slugs = sorted(p.parent.name for p in SKILLS_DIR.glob("*/SKILL.md"))
    for slug in slugs:
        for filename, builder in (("schema.json", build_schema), ("input.schema.json", build_input_schema)):
            target = SKILLS_DIR / slug / filename
            content = render(builder(slug))
            if args.check:
                if not target.exists() or target.read_text(encoding="utf-8") != content:
                    stale.append(f"{slug}/{filename}")
            else:
                target.write_text(content, encoding="utf-8")

    if args.check and stale:
        print("Stale schemas (run `python scripts/generate_schemas.py`):", *stale, sep="\n  ")
        return 1
    print(f"{'checked' if args.check else 'wrote'} {len(slugs)} schemas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
