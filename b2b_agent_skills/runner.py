"""Run a skill against input data and return validated, structured output."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .errors import SkillOutputError
from .providers import MockProvider, Provider, get_provider
from .registry import Skill, get_skill
from .validation import extract_json, validate_output


@dataclass
class SkillResult:
    skill: str
    output: dict[str, Any] | None
    valid: bool
    errors: list[str] = field(default_factory=list)
    raw_text: str = ""
    model: str = ""
    attempts: int = 1
    latency_ms: int = 0
    usage: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_system_prompt(skill: Skill) -> str:
    """Skill instructions plus the output contract. Stable per skill, so it caches well."""
    contract = (
        "\n\n## Output contract\n\n"
        "You are being called programmatically. Your answer is a single JSON object that validates against "
        "this JSON Schema (every listed field is required; do not add fields):\n\n"
        f"{json.dumps(skill.output_schema, separators=(',', ':'))}\n\n"
        "Before answering, apply the scoring model exactly as written: compute every formula step by step, "
        "check each band or threshold against the computed number (boundaries matter), and apply category "
        "rules in the order they are listed. If your response is constrained to JSON, do that reasoning "
        "internally and return only the object. Otherwise, write your working briefly, then end your "
        "response with the JSON object in a ```json fenced block; nothing may follow it.\n\n"
        "Enumerated values (bands, categories, statuses, pillar or field names) must use the exact terms "
        "from the instructions above, without extra commentary inside the value. If the input is missing "
        "information a field depends on, still return the field, and say what is missing in the most "
        "relevant free-text field rather than inventing evidence.\n\n"
        "Small samples: when a rate, lift, benchmark, or pattern rests on little data (roughly fewer than 15 "
        "deals, accounts, interviews, or periods), still compute it, but label the conclusion in the free-text "
        "fields as provisional with the sample size, e.g. 'provisional (n=8)'. Never present a small-sample "
        "result with the confidence of a large one."
    )
    example = skill.example_output
    if example:
        contract += (
            "\n\n## Format reference\n\n"
            "Below is an output from this skill's documentation, for a *different* scenario. Use it only to "
            "match conventions: number scales (e.g. a 0-100 score is written 77.1, not 0.771; a share written "
            "0.22 stays a 0-1 fraction), the vocabulary for bands, categories, and statuses, and how list items "
            "are written (e.g. field or pillar keys such as `economic_buyer`, not sentences). Never copy its "
            "values: compute everything from the input data.\n\n"
            f"```json\n{json.dumps(example, indent=2, ensure_ascii=False)}\n```"
        )
    return skill.instructions + contract


def build_user_prompt(input_data: dict[str, Any], context: str | None = None) -> str:
    """The per-call message: optional company context, then the input data."""
    parts = []
    if context:
        parts.append(
            "## Company context\n\nBackground on the company you are working for. Use it to make the output "
            "specific (their product, ICP, competitors, proof points); it is not evidence about this deal or "
            f"account.\n\n{context.strip()}"
        )
    parts.append(f"## Input data\n\n```json\n{json.dumps(input_data, indent=2, sort_keys=True)}\n```")
    return "\n\n".join(parts)


def _load_input(input: dict[str, Any] | str | Path | None) -> dict[str, Any]:
    if input is None:
        return {}
    if isinstance(input, dict):
        return input
    with open(input, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("skill input must be a JSON object")
    return data


def run_skill(
    skill: str,
    input: dict[str, Any] | str | Path | None = None,
    *,
    provider: Provider | str | None = None,
    raise_on_invalid: bool = True,
    max_attempts: int = 2,
    context: str | None = None,
) -> SkillResult:
    """Run ``skill`` on ``input`` (a dict or a path to a JSON file).

    Returns a :class:`SkillResult` whose ``output`` has been validated against
    the skill's schema. If the model's output is unparseable or invalid it is
    retried once with the validation errors as feedback; if it is still
    invalid, :class:`SkillOutputError` is raised (or, with
    ``raise_on_invalid=False``, the result is returned with ``valid=False``).

    ``context`` is background text about the company (e.g. a workspace's
    company.md), added to the message so the output is specific to them.
    """
    spec = get_skill(skill)
    if provider is None or isinstance(provider, str):
        provider = get_provider(provider)
    input_data = _load_input(input)
    if not input_data and not isinstance(provider, MockProvider):
        raise ValueError(
            f"No input data for '{spec.name}'. Pass the inputs described in its SKILL.md; an empty call to a real model only spends tokens."
        )

    system = build_system_prompt(spec)
    user = build_user_prompt(input_data, context)
    schema = spec.output_schema or None

    usage: dict[str, int] = {}
    started = time.monotonic()
    result = SkillResult(skill=spec.name, output=None, valid=False)
    for attempt in range(1, max_attempts + 1):
        completion = provider.complete(system=system, user=user, schema=schema, skill=spec.name)
        for k, v in completion.usage.items():
            usage[k] = usage.get(k, 0) + v

        try:
            output = extract_json(completion.text)
            errors = validate_output(spec.schema, output) if isinstance(output, dict) else ["<root>: output is not a JSON object"]
        except ValueError as e:
            output, errors = None, [str(e)]

        result = SkillResult(
            skill=spec.name,
            output=output if isinstance(output, dict) else None,
            valid=not errors,
            errors=errors,
            raw_text=completion.text,
            model=completion.model,
            attempts=attempt,
        )
        if result.valid:
            break
        user = build_user_prompt(input_data, context) + (
            "\n\nYour previous response was rejected for these reasons:\n- "
            + "\n- ".join(errors[:20])
            + "\nReturn a corrected JSON object."
        )

    result.latency_ms = int((time.monotonic() - started) * 1000)
    result.usage = usage
    if not result.valid and raise_on_invalid:
        raise SkillOutputError(f"{spec.name}: output failed validation after {result.attempts} attempt(s): {result.errors[:5]}", result)
    return result
