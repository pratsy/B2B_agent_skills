"""Turn messy notes (call transcripts, emails, pasted CRM text) into a skill's inputs.

The model fills the skill's documented input fields and must back every value
with a verbatim quote from the source. The quotes are then checked in code:
a value whose quote does not appear in the source is dropped and turned into a
question for the user. A model that invents evidence ("champion confirmed")
therefore cannot get it past this step.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from .errors import ProviderError
from .providers import Provider, get_provider
from .registry import get_skill
from .validation import extract_json

_MAX_QUESTIONS = 6


@dataclass
class Extraction:
    skill: str
    input: dict[str, Any]
    evidence: list[dict[str, str]] = field(default_factory=list)
    missing: list[dict[str, str]] = field(default_factory=list)
    dropped: list[str] = field(default_factory=list)

    def questions(self) -> list[dict[str, str]]:
        return self.missing[:_MAX_QUESTIONS]


def _normalize(text: str) -> str:
    text = text.lower().replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = re.sub(r"[^\w%$.'\"-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def quote_in_source(quote: str, source: str) -> bool:
    q = _normalize(quote).strip(".\"' ")
    return bool(q) and q in _normalize(source)


def _delete_path(data: dict[str, Any], path: str) -> None:
    parts = path.split(".")
    node: Any = data
    for part in parts[:-1]:
        if not isinstance(node, dict) or part not in node:
            return
        node = node[part]
    if isinstance(node, dict):
        node.pop(parts[-1], None)
        # drop now-empty parents
        if len(parts) > 1 and not node:
            _delete_path(data, ".".join(parts[:-1]))


def _set_path(data: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    node = data
    for part in parts[:-1]:
        node = node.setdefault(part, {})
        if not isinstance(node, dict):
            return
    node[parts[-1]] = value


def _paths(data: Any, prefix: str = "") -> list[str]:
    """Leaf-ish paths: top-level keys, plus one level into objects (pillar_evidence.metrics)."""
    out = []
    if isinstance(data, dict):
        for k, v in data.items():
            path = f"{prefix}{k}"
            if isinstance(v, dict) and v and not prefix:
                out += _paths(v, f"{path}.")
            else:
                out.append(path)
    return out


def build_extraction_prompt(skill_name: str) -> str:
    skill = get_skill(skill_name)
    fields = "\n".join(f"- `{name}`: {desc}" for name, desc in skill.input_fields.items())
    return f"""You prepare inputs for the `{skill.name}` skill: {skill.description}

## The skill's input fields

{fields}

## How the skill uses them

{skill.instructions}

## Your task

Read the source material and fill in as many input fields as the material supports. Return JSON:

```json
{{
  "input": {{ "<field>": <value>, ... }},
  "evidence": [ {{"field": "<field or field.subfield>", "quote": "<verbatim text from the source>"}} ],
  "missing": [ {{"field": "<field or field.subfield>", "question": "<one short question to ask the user>"}} ]
}}
```

Rules:
1. Only use facts stated in the source material. Do not infer favorable facts from silence: "they seemed keen" is not a confirmed champion; an unnamed approver is not a confirmed economic buyer. When the skill scores evidence quality, record who said what and how it was confirmed.
2. Every value you fill must have at least one evidence entry whose `quote` is copied exactly, word for word, from the source (one sentence or phrase, under 200 characters). Values without a verbatim quote will be discarded.
3. For a nested object (e.g. one entry per pillar), use `field.subfield` in evidence and missing (e.g. `pillar_evidence.economic_buyer`).
4. List in `missing` the fields the skill's scoring depends on that the source does not answer, with a question the user can answer in one line. Skip fields that are irrelevant for this material.
5. Normalize values (numbers as numbers, dates as YYYY-MM-DD). Put descriptions in your own words inside values, but keep quotes verbatim.

Write any working briefly, then end with the JSON object in a ```json fenced block."""


def extract_inputs(
    skill: str,
    sources: str | list[str],
    *,
    provider: Provider | str | None = None,
    context: str | None = None,
    known: dict[str, Any] | None = None,
) -> Extraction:
    """Extract ``skill`` inputs from free text, keeping only values backed by verified quotes."""
    spec = get_skill(skill)
    if provider is None or isinstance(provider, str):
        provider = get_provider(provider)
    texts = [sources] if isinstance(sources, str) else list(sources)
    source = "\n\n---\n\n".join(t.strip() for t in texts if t and t.strip())
    if not source:
        raise ValueError("no source text to extract from")

    user = ""
    if context:
        user += f"## Company context (background only, not evidence)\n\n{context.strip()}\n\n"
    if known:
        user += f"## Facts the user already confirmed\n\n```json\n{json.dumps(known, indent=2)}\n```\n\n"
    user += f"## Source material\n\n{source}"

    completion = provider.complete(system=build_extraction_prompt(spec.name), user=user, schema=None, skill=f"{spec.name}:extract")
    try:
        payload = extract_json(completion.text)
    except ValueError as e:
        raise ProviderError(f"extraction for {spec.name} returned no JSON") from e
    if not isinstance(payload, dict):
        raise ProviderError(f"extraction for {spec.name} returned a non-object")

    raw_input = payload.get("input")
    data: dict[str, Any] = raw_input if isinstance(raw_input, dict) else {}
    evidence = [e for e in payload.get("evidence", []) if isinstance(e, dict) and e.get("field") and e.get("quote")]
    missing = [m for m in payload.get("missing", []) if isinstance(m, dict) and m.get("field")]

    verified = [e for e in evidence if quote_in_source(str(e["quote"]), source)]
    supported = {e["field"] for e in verified}

    def is_supported(path: str) -> bool:
        return any(path == s or path.startswith(s + ".") or s.startswith(path + ".") for s in supported)

    dropped = []
    for path in _paths(data):
        if not is_supported(path):
            dropped.append(path)
            _delete_path(data, path)
    already = {m["field"] for m in missing}
    for path in dropped:
        if path not in already:
            missing.append({"field": path, "question": f"The notes don't clearly state `{path}`. What do you know about it?"})

    for path, value in (known or {}).items():
        _set_path(data, path, value)
        missing = [m for m in missing if m["field"] != path]

    return Extraction(skill=spec.name, input=data, evidence=verified, missing=missing, dropped=dropped)
