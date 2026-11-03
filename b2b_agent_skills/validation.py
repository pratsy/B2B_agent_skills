"""Parse model output into JSON and validate it against a skill's schema."""

from __future__ import annotations

import json
import re
from typing import Any

from jsonschema import Draft202012Validator

_FENCE = re.compile(r"```(?:json)?\s*\n(.*?)\n?```", re.S)


def extract_json(text: str) -> Any:
    """Parse JSON from model output.

    Structured-output providers return bare JSON. Without that feature, the
    contract asks the model to show its working and end with the answer in a
    ```json fence. Try, in order: the whole string, fenced blocks from last to
    first (the final answer comes last), then the outermost {...}.
    Raises ValueError if none of them parse to a JSON object.
    """
    candidates = [text.strip()]
    candidates += [m.group(1).strip() for m in reversed(list(_FENCE.finditer(text)))]
    start, end = text.find("{"), text.rfind("}")
    if 0 <= start < end:
        candidates.append(text[start : end + 1])

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except (json.JSONDecodeError, TypeError):
            continue
    raise ValueError("model output does not contain parseable JSON")


def _format_path(path: Any) -> str:
    out = ""
    for part in path:
        out += f"[{part}]" if isinstance(part, int) else (f".{part}" if out else str(part))
    return out or "<root>"


def validate_output(schema: dict[str, Any], output: Any) -> list[str]:
    """Return a list of human-readable schema violations (empty means valid)."""
    if not schema:
        return []
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(output), key=lambda e: list(e.absolute_path))
    return [f"{_format_path(e.absolute_path)}: {e.message}" for e in errors]
