"""Golden evals: check a skill's actual answers, not just its output shape.

A golden file (``evals/golden/<skill>.json``) holds cases built from a skill's
README worked example: realistic input plus assertions on the answer the
methodology must produce (e.g. deal-risk-assessor must total 14/24 and flag
the economic buyer as a single point of failure).

Assertion ops (each assertion has a ``path`` and one op):

  equals    exact match; strings compare case/space/underscore-insensitively
  approx    number within ``tol`` (absolute, default 1% of expected)
  one_of    value equals any listed option (same string normalization)
  contains  substring of a string (case-insensitive) or member of a list
  matches   regex search on a string (case-insensitive)
  gte, lte  numeric bounds
  length    list/string length

Paths use dots and indexes - ``checks.time_in_stage_pass``, ``themes[0].name`` -
and ``[key=value]`` selects a list element by field, so assertions don't depend
on ordering: ``accounts_ranked[account_id=acct_B].tier``.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .errors import ProviderError, SkillOutputError
from .providers import Provider, get_provider
from .registry import get_skill
from .runner import run_skill
from .validation import validate_output

_PACKAGE_DIR = Path(__file__).resolve().parent
_MISSING = object()
_SEGMENT = re.compile(r"([^.\[\]]+)|\[(\d+)\]|\[([^=\]]+)=([^\]]+)\]")


def golden_dir() -> Path:
    override = os.getenv("B2B_EVALS_DIR")
    if override:
        return Path(override).expanduser().resolve()
    bundled = _PACKAGE_DIR / "_evals"
    if bundled.is_dir():
        return bundled
    return _PACKAGE_DIR.parent / "evals" / "golden"


def load_golden(skill: str | None = None) -> list[dict[str, Any]]:
    """Load golden suites (all, or one skill's)."""
    root = golden_dir()
    paths = [root / f"{skill}.json"] if skill else sorted(root.glob("*.json"))
    suites = []
    for p in paths:
        if p.is_file():
            suites.append(json.loads(p.read_text(encoding="utf-8")))
    return suites


def resolve_path(data: Any, path: str) -> Any:
    current = data
    for name, index, key, value in _SEGMENT.findall(path):
        if name:
            if not isinstance(current, dict) or name not in current:
                return _MISSING
            current = current[name]
        elif index:
            i = int(index)
            if not isinstance(current, list) or i >= len(current):
                return _MISSING
            current = current[i]
        else:
            if not isinstance(current, list):
                return _MISSING
            match = [item for item in current if isinstance(item, dict) and str(item.get(key)) == value]
            if not match:
                return _MISSING
            current = match[0]
    return current


def _norm(v: Any) -> Any:
    if isinstance(v, str):
        return re.sub(r"[\s_\-]+", " ", v).strip().lower()
    return v


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def check_assertion(output: Any, assertion: dict[str, Any]) -> tuple[bool, str]:
    path = assertion["path"]
    actual = resolve_path(output, path)
    if actual is _MISSING:
        return False, f"{path}: missing"

    if "equals" in assertion:
        expected = assertion["equals"]
        ok = _norm(actual) == _norm(expected) or (_is_number(actual) and _is_number(expected) and float(actual) == float(expected))
        return ok, f"{path}: expected {expected!r}, got {actual!r}"
    if "approx" in assertion:
        expected = float(assertion["approx"])
        tol = float(assertion.get("tol", abs(expected) * 0.01 or 0.01))
        ok = _is_number(actual) and abs(float(actual) - expected) <= tol
        return ok, f"{path}: expected {expected} ± {tol}, got {actual!r}"
    if "one_of" in assertion:
        options = assertion["one_of"]
        return _norm(actual) in [_norm(o) for o in options], f"{path}: expected one of {options!r}, got {actual!r}"
    if "contains" in assertion:
        needle = assertion["contains"]
        if isinstance(actual, str):
            ok = _norm(needle) in _norm(actual)
        elif isinstance(actual, list):
            ok = _norm(needle) in [_norm(a) for a in actual]
        else:
            ok = False
        return ok, f"{path}: expected to contain {needle!r}, got {actual!r}"
    if "matches" in assertion:
        pattern = assertion["matches"]
        return isinstance(actual, str) and re.search(pattern, actual, re.I) is not None, f"{path}: expected /{pattern}/, got {actual!r}"
    if "gte" in assertion:
        return _is_number(actual) and actual >= assertion["gte"], f"{path}: expected >= {assertion['gte']}, got {actual!r}"
    if "lte" in assertion:
        return _is_number(actual) and actual <= assertion["lte"], f"{path}: expected <= {assertion['lte']}, got {actual!r}"
    if "length" in assertion:
        ok = hasattr(actual, "__len__") and len(actual) == assertion["length"]
        return ok, f"{path}: expected length {assertion['length']}, got {actual!r}"
    raise ValueError(f"assertion on {path} has no recognised op: {assertion}")


@dataclass
class CaseResult:
    skill: str
    case_id: str
    passed: bool
    schema_valid: bool
    assertions_passed: int
    assertions_total: int
    failures: list[str] = field(default_factory=list)
    error: str | None = None
    usage: dict[str, int] = field(default_factory=dict)
    latency_ms: int = 0


@dataclass
class EvalReport:
    provider: str
    model: str
    cases: list[CaseResult]

    @property
    def passed(self) -> int:
        return sum(c.passed for c in self.cases)

    @property
    def pass_rate(self) -> float:
        return self.passed / len(self.cases) if self.cases else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "passed": self.passed,
            "total": len(self.cases),
            "pass_rate": round(self.pass_rate, 4),
            "cases": [asdict(c) for c in self.cases],
        }

    def to_markdown(self) -> str:
        lines = [
            f"## Golden eval results — {self.provider} / {self.model}",
            "",
            f"**{self.passed}/{len(self.cases)} cases passed ({self.pass_rate:.0%})**",
            "",
            "| Skill | Case | Result | Assertions | Notes |",
            "|---|---|---|---|---|",
        ]
        for c in self.cases:
            note = c.error or "; ".join(c.failures[:3])
            lines.append(
                f"| `{c.skill}` | {c.case_id} | {'✅' if c.passed else '❌'} | {c.assertions_passed}/{c.assertions_total} | {note.replace('|', '/')} |"
            )
        return "\n".join(lines) + "\n"


def evaluate_case(skill: str, case: dict[str, Any], output: dict[str, Any] | None) -> CaseResult:
    """Score one output against one golden case (no model call)."""
    spec = get_skill(skill)
    schema_errors = validate_output(spec.schema, output) if output is not None else ["no output"]
    failures = [f"schema: {e}" for e in schema_errors[:5]]
    assertions = case.get("assertions", [])
    passed_count = 0
    for a in assertions:
        ok, message = check_assertion(output, a)
        if ok:
            passed_count += 1
        else:
            failures.append(f"{message} ({a['why']})" if a.get("why") else message)
    return CaseResult(
        skill=skill,
        case_id=case["id"],
        passed=not schema_errors and passed_count == len(assertions),
        schema_valid=not schema_errors,
        assertions_passed=passed_count,
        assertions_total=len(assertions),
        failures=failures,
    )


def _run_case(skill: str, case: dict[str, Any], provider: Provider) -> tuple[CaseResult, str | None]:
    try:
        run = run_skill(skill, case["input"], provider=provider, raise_on_invalid=False)
    except (ProviderError, SkillOutputError) as e:
        return CaseResult(skill, case["id"], False, False, 0, len(case.get("assertions", [])), error=str(e)), None
    result = evaluate_case(skill, case, run.output)
    result.usage, result.latency_ms = run.usage, run.latency_ms
    return result, run.model


def run_golden(
    provider: Provider | str | None = None,
    skills: list[str] | None = None,
    concurrency: int = 1,
) -> EvalReport:
    """Run every golden case (optionally only for ``skills``) against ``provider``.

    ``concurrency`` runs that many cases in parallel threads; results keep file order.
    """
    from concurrent.futures import ThreadPoolExecutor

    if provider is None or isinstance(provider, str):
        provider = get_provider(provider)
    wanted = set(skills) if skills else None
    jobs = [(s["skill"], c) for s in load_golden() if not wanted or s["skill"] in wanted for c in s["cases"]]
    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
        outcomes = list(pool.map(lambda job: _run_case(job[0], job[1], provider), jobs))
    models = [m for _, m in outcomes if m]
    model = models[-1] if models else getattr(provider, "model", provider.name)
    return EvalReport(provider=provider.name, model=str(model), cases=[r for r, _ in outcomes])
