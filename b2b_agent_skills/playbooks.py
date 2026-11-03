"""Playbooks: multi-skill workflows that turn a founder's raw material into a one-page answer.

A playbook lives in ``playbooks/<name>/``:

    playbook.json   steps (which skills to run), report headings, where to save
    report.md       instructions for the final one-page report
    SKILL.md        the same playbook for Claude Code (runs natively, no CLI needed)

Running one: each step extracts that skill's inputs from the notes (keeping only
quote-backed facts), runs the skill, and the results are combined into a short
markdown report with fixed headings. Steps run in parallel.
"""

from __future__ import annotations

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .errors import ProviderError, SkillOutputError, SkillsError
from .extraction import Extraction, extract_inputs
from .providers import Provider, get_provider
from .runner import SkillResult, run_skill
from .workspace import Workspace

_PACKAGE_DIR = Path(__file__).resolve().parent


def playbooks_dir() -> Path:
    override = os.getenv("B2B_PLAYBOOKS_DIR")
    if override:
        return Path(override).expanduser().resolve()
    bundled = _PACKAGE_DIR / "_playbooks"
    return bundled if bundled.is_dir() else _PACKAGE_DIR.parent / "playbooks"


def list_playbooks() -> list[str]:
    root = playbooks_dir()
    return sorted(p.parent.name for p in root.glob("*/playbook.json")) if root.is_dir() else []


def load_playbook(name: str) -> dict[str, Any]:
    path = playbooks_dir() / name / "playbook.json"
    if not path.is_file():
        raise SkillsError(f"Unknown playbook '{name}'. Available: {', '.join(list_playbooks())}")
    spec = json.loads(path.read_text(encoding="utf-8"))
    spec.setdefault("kind", "notes")
    spec.setdefault("steps", [])
    report_md = path.parent / "report.md"
    spec["report_instructions"] = report_md.read_text(encoding="utf-8") if report_md.is_file() else ""
    return spec


@dataclass
class StepResult:
    id: str
    skill: str
    status: str  # "ok" | "skipped" | "failed"
    extraction: dict[str, Any] = field(default_factory=dict)
    output: dict[str, Any] | None = None
    error: str | None = None


@dataclass
class PlaybookResult:
    playbook: str
    steps: dict[str, StepResult]
    report: str
    missing: list[dict[str, str]]
    saved_to: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "steps": {k: asdict(v) for k, v in self.steps.items()}}


def _run_step(step: dict[str, Any], sources: list[str], provider: Provider, context: str | None, known: dict[str, Any]) -> StepResult:
    skill = step["skill"]
    try:
        extraction: Extraction = extract_inputs(skill, sources, provider=provider, context=context, known=known.get(step["id"]))
    except (ProviderError, ValueError) as e:
        return StepResult(step["id"], skill, "failed", error=f"extraction failed: {e}")
    ex = {"input": extraction.input, "evidence": extraction.evidence, "missing": extraction.missing, "dropped": extraction.dropped}
    requires = step.get("requires", [])
    if requires and not all(extraction.input.get(r) for r in requires):
        return StepResult(step["id"], skill, "skipped", extraction=ex, error=f"notes don't contain {', '.join(requires)}")
    data = dict(extraction.input)
    if extraction.missing:
        data["_missing_inputs"] = [m["field"] for m in extraction.missing]
    try:
        result: SkillResult = run_skill(skill, data or {"_note": "no usable evidence in the notes"}, provider=provider, context=context)
    except (ProviderError, SkillOutputError) as e:
        return StepResult(step["id"], skill, "failed", extraction=ex, error=str(e))
    return StepResult(step["id"], skill, "ok", extraction=ex, output=result.output)


def _report_prompt(spec: dict[str, Any]) -> str:
    headings = "\n".join(f"- ## {h}" for h in spec["report"]["headings"])
    return (
        f"{spec['report_instructions'].strip()}\n\n"
        "Write the report in markdown with exactly these second-level headings, in this order:\n\n"
        f"{headings}\n\n"
        "Use only facts from the skill results and the source notes. Where the skills flagged missing evidence, "
        "say so plainly rather than filling the gap. Keep it to one page. Output only the markdown report."
    )


def _clean_markdown(text: str) -> str:
    fenced = re.match(r"^\s*```(?:markdown|md)?\s*\n(.*)\n```\s*$", text, re.S)
    return (fenced.group(1) if fenced else text).strip()


def run_playbook(
    name: str,
    sources: str | list[str],
    *,
    provider: Provider | str | None = None,
    workspace: Workspace | None = None,
    subject: str | None = None,
    known: dict[str, dict[str, Any]] | None = None,
    save: bool = True,
) -> PlaybookResult:
    """Run playbook ``name`` on ``sources`` (notes/transcripts as text).

    ``subject`` names what the report is about (e.g. the deal) and decides the
    file it is saved to in the workspace. ``known`` holds user answers per step id.
    """
    spec = load_playbook(name)
    if spec["kind"] != "notes":
        raise SkillsError(
            f"'{name}' doesn't take notes; run it with `b2b-skills playbook {name}` and its inputs ({spec.get('inputs', '')})"
        )
    if provider is None or isinstance(provider, str):
        provider = get_provider(provider)
    texts = [sources] if isinstance(sources, str) else list(sources)
    context = workspace.company_context() if workspace else None
    known = known or {}

    with ThreadPoolExecutor(max_workers=len(spec["steps"])) as pool:
        results = list(pool.map(lambda s: _run_step(s, texts, provider, context, known), spec["steps"]))
    steps = {r.id: r for r in results}

    missing: list[dict[str, str]] = []
    seen = set()
    for r in results:
        for m in r.extraction.get("missing", []):
            key = m["field"].split(".")[-1]
            if key not in seen:
                seen.add(key)
                missing.append({**m, "step": r.id})

    payload = {
        "skill_results": {r.id: {"skill": r.skill, "status": r.status, "output": r.output, "note": r.error} for r in results},
        "missing_evidence": missing,
    }
    user = ""
    if context:
        user += f"## Company context\n\n{context}\n\n"
    user += (
        f"## Skill results\n\n```json\n{json.dumps(payload, indent=2, ensure_ascii=False)}\n```\n\n## Source notes\n\n"
        + "\n\n---\n\n".join(texts)
    )

    report = ""
    message = user
    for _ in range(3):
        completion = provider.complete(system=_report_prompt(spec), user=message, schema=None, skill=f"{name}:report")
        report = _clean_markdown(completion.text)
        problems = [f"missing heading '## {h}'" for h in spec["report"]["headings"] if f"## {h}".lower() not in report.lower()]
        problems += consistency_problems(report, steps)
        if not problems:
            break
        message = (
            user
            + "\n\nYour previous draft contradicted the skill results or broke the format:\n- "
            + "\n- ".join(problems)
            + "\nRewrite the report so it matches the skill results exactly."
        )

    result = PlaybookResult(playbook=name, steps=steps, report=report, missing=missing)
    if workspace and save:
        subject = subject or _subject_from(results, spec) or "untitled"
        target = workspace.root / spec["report"]["save_to"].format(subject=re.sub(r"[^a-z0-9]+", "-", subject.lower()).strip("-"))
        # Keep the raw notes with the debrief: later re-scoring (e.g. monday-review) needs primary evidence, not a summary.
        sources = "\n\n---\n\n".join(t.strip() for t in texts)
        workspace.append_note(target, spec["title"], f"{report}\n\n<details><summary>Source notes</summary>\n\n{sources}\n\n</details>")
        workspace.log_run(
            {
                "type": "playbook",
                "playbook": name,
                "subject": subject,
                "model": getattr(provider, "model", provider.name),
                "result": result.to_dict(),
            }
        )
        result.saved_to = str(target.relative_to(workspace.root))
    return result


def consistency_problems(report: str, steps: dict[str, StepResult]) -> list[str]:
    """Facts the report must state the same way the skills computed them (checked in code, not trusted to the prompt)."""
    problems = []
    risk = (steps.get("risk") or StepResult("", "", "")).output or {}
    total = risk.get("total_score")
    if isinstance(total, (int, float)):
        found = re.findall(r"\b(\d{1,2})\s*/\s*24\b", report)
        if not found:
            problems.append(f"state the MEDDPICC total as {total:g}/24")
        elif any(abs(float(n) - float(total)) > 0.5 for n in found):
            problems.append(f"the MEDDPICC total is {total:g}/24 (the report says {', '.join(sorted(set(found)))}/24)")
    if re.search(r"/\s*40\b", report):
        problems.append("MEDDPICC is out of 24, not 40")
    stakeholders = (steps.get("stakeholders") or StepResult("", "", "")).output or {}
    single = stakeholders.get("single_threading_risk")
    claim = re.search(r"single.threading risk\W{0,6}(yes|no|not|true|false|high|low|none)", report, re.I)
    if isinstance(single, bool) and claim:
        says_yes = claim.group(1).lower() in {"yes", "true", "high"}
        if says_yes != single:
            problems.append(
                f"the stakeholder skill found single-threading risk = {'yes' if single else 'no'}; the report says the opposite"
            )
    return problems


def _subject_from(results: list[StepResult], spec: dict[str, Any]) -> str | None:
    key = spec["report"].get("subject_field")
    for r in results:
        value = (r.output or {}).get(key) or r.extraction.get("input", {}).get(key)
        if value:
            return str(value)
    return None
