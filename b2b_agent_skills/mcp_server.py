"""MCP server exposing every skill to any MCP client (Claude Desktop, Claude Code, Cursor, ...).

Two ways to use a skill over MCP:

* **Host model runs it (no API key needed).** Each skill is an MCP *prompt*,
  and the ``get_skill`` tool returns its instructions and output schema, so
  the client's own model applies the methodology.
* **Server runs it.** If ``PROVIDER`` is set to ``anthropic`` or ``openai``,
  a ``run_skill`` tool calls that provider and returns schema-validated JSON.

Start with ``b2b-skills mcp`` (stdio) or ``b2b-skills mcp --transport streamable-http``.
Requires the ``mcp`` extra: ``pip install 'b2b-agent-skills[mcp]'``.
"""

from __future__ import annotations

import json
import os
from typing import Any

from . import __version__
from .registry import get_skill, list_skills
from .runner import build_system_prompt, build_user_prompt

INSTRUCTIONS = (
    "Evidence-grounded B2B revenue skills (sales, marketing, RevOps, GTM). Call list_skills to find the "
    "right skill for the user's problem, then get_skill to load its methodology and output schema, and apply "
    "it to the user's data. Score from evidence the user provides; ask for missing inputs instead of guessing."
)


def _make_prompt(slug: str):
    def prompt(input_json: str = "{}") -> str:
        skill = get_skill(slug)
        try:
            data = json.loads(input_json) if input_json.strip() else {}
        except json.JSONDecodeError:
            data = {"notes": input_json}
        return build_system_prompt(skill) + "\n\n" + build_user_prompt(data if isinstance(data, dict) else {"input": data})

    return prompt


def build_server() -> Any:
    try:
        from mcp.server.mcpserver import MCPServer
        from mcp.server.mcpserver.prompts import Prompt
    except ImportError as e:  # pragma: no cover - exercised only without the extra
        raise SystemExit("The MCP server needs the mcp extra: pip install 'b2b-agent-skills[mcp]'") from e

    server = MCPServer(name="b2b-agent-skills", version=__version__, instructions=INSTRUCTIONS)

    def list_skills_tool() -> list[dict[str, str]]:
        return [{"name": s, "description": get_skill(s).description} for s in list_skills()]

    def get_skill_tool(name: str) -> dict[str, Any]:
        skill = get_skill(name)
        return {
            "name": skill.name,
            "description": skill.description,
            "instructions": skill.instructions,
            "output_schema": skill.output_schema,
        }

    server.add_tool(
        list_skills_tool, name="list_skills", description="List every available skill with a one-line description of when to use it."
    )
    server.add_tool(
        get_skill_tool,
        name="get_skill",
        description="Load a skill's methodology (instructions) and the JSON Schema its output must follow.",
    )

    from .playbooks import list_playbooks, load_playbook, playbooks_dir
    from .workspace import find_workspace

    def list_playbooks_tool() -> list[dict[str, str]]:
        return [{"name": n, "description": load_playbook(n)["description"]} for n in list_playbooks()]

    def get_playbook_tool(name: str) -> dict[str, Any]:
        spec = load_playbook(name)
        steps_md = (playbooks_dir() / name / "SKILL.md").read_text(encoding="utf-8")
        return {
            "name": name,
            "description": spec["description"],
            "instructions": steps_md,
            "skills_used": [s["skill"] for s in spec["steps"]],
        }

    server.add_tool(list_playbooks_tool, name="list_playbooks", description="List multi-step GTM playbooks (e.g. call-debrief).")
    server.add_tool(
        get_playbook_tool,
        name="get_playbook",
        description="Load a playbook's step-by-step instructions and the skills it uses; follow them with get_skill for each step.",
    )

    workspace = find_workspace()
    if workspace:

        def get_company_context_tool() -> str:
            return workspace.company_context()

        server.add_tool(
            get_company_context_tool,
            name="get_company_context",
            description="The company's context (company.md): product, ICP, competitors, proof points. Background, not deal evidence.",
        )

    provider_name = os.getenv("PROVIDER", "").lower()
    if provider_name in {"anthropic", "openai", "claude-code"}:
        from .providers import get_provider
        from .runner import run_skill

        provider = get_provider(provider_name)

        def run_skill_tool(name: str, input: dict[str, Any]) -> dict[str, Any]:
            result = run_skill(name, input, provider=provider, raise_on_invalid=False)
            return {"skill": result.skill, "valid": result.valid, "errors": result.errors, "output": result.output}

        server.add_tool(
            run_skill_tool,
            name="run_skill",
            description=f"Run a skill server-side on {provider_name} and return schema-validated JSON output.",
        )

        from .playbooks import run_playbook

        def run_playbook_tool(name: str, notes: str, subject: str | None = None) -> dict[str, Any]:
            result = run_playbook(name, notes, provider=provider, workspace=workspace, subject=subject)
            return {"report": result.report, "missing_evidence": result.missing, "saved_to": result.saved_to}

        server.add_tool(
            run_playbook_tool,
            name="run_playbook",
            description=f"Run a playbook server-side on {provider_name} from raw notes; returns the one-page report and saves it to the workspace.",
        )

    for slug in list_skills():
        skill = get_skill(slug)
        server.add_prompt(Prompt.from_function(_make_prompt(slug), name=slug, description=skill.description))

    return server


def main(transport: str = "stdio") -> None:
    build_server().run(transport=transport)


if __name__ == "__main__":
    main()
