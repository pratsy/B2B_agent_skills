"""``b2b-skills`` command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .catalog import STAGES
from .errors import SkillOutputError, SkillsError
from .registry import get_skill, list_skills


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def _read_input(arg: str | None) -> dict[str, Any] | None:
    if arg is None:
        return None
    data = json.load(sys.stdin) if arg == "-" else json.loads(Path(arg).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SkillsError("input must be a JSON object")
    return data


def _read_notes(paths: list[str]) -> list[str]:
    from .transcripts import NOTE_SUFFIXES, read_notes

    texts = []
    for raw in paths:
        if raw == "-":
            texts.append(sys.stdin.read())
            continue
        p = Path(raw)
        files = sorted(f for f in p.iterdir() if f.suffix.lower() in NOTE_SUFFIXES) if p.is_dir() else [p]
        texts += [f"[{f.name}]\n{read_notes(f)}" for f in files]
    if not any(t.strip() for t in texts):
        raise SkillsError("the notes are empty")
    return texts


def _provider(args: argparse.Namespace) -> Any:
    from .providers import get_provider

    kwargs = {"model": args.model} if getattr(args, "model", None) else {}
    return get_provider(args.provider, **kwargs)


def _workspace(args: argparse.Namespace) -> Any:
    if getattr(args, "no_context", False):
        return None
    from .workspace import find_workspace

    return find_workspace()


def _interactive(args: argparse.Namespace) -> bool:
    if getattr(args, "no_questions", False):
        return False
    return sys.stdin.isatty() and sys.stdout.isatty()


def cmd_list(args: argparse.Namespace) -> int:
    for name in list_skills():
        skill = get_skill(name)
        if args.stage and skill.stage != args.stage:
            continue
        if args.verbose:
            print(f"{name}  [{skill.stage}]\n    {skill.description}\n")
        else:
            print(name)
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    skill = get_skill(args.skill)
    if args.schema:
        print(json.dumps(skill.schema, indent=2))
    elif args.inputs:
        for name, desc in skill.input_fields.items():
            print(f"{name}: {desc}")
    else:
        print(f"# {skill.name}  [{skill.stage}]\n\n{skill.description}\n\n{skill.instructions}")
        print("\n## Inputs\n\n" + "\n".join(f"- {k}: {v}" for k, v in skill.input_fields.items()))
        print("\n## Output fields\n\n" + ", ".join(skill.output_fields))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    from .runner import run_skill

    provider = _provider(args)
    ws = _workspace(args)
    context = ws.company_context() if ws else None
    data = _read_input(args.input) or {}

    if args.notes:
        from .extraction import _set_path, extract_inputs

        extraction = extract_inputs(args.skill, _read_notes(args.notes), provider=provider, context=context, known=data or None)
        data = extraction.input
        questions = extraction.questions()
        if questions and _interactive(args):
            print(f"The notes don't answer {len(questions)} thing(s) this skill needs. Press Enter to skip any.", file=sys.stderr)
            for q in questions:
                answer = input(f"  {q['question']} > ").strip()
                if answer:
                    _set_path(data, q["field"], f"(stated by the user) {answer}")
                    extraction.missing = [m for m in extraction.missing if m["field"] != q["field"]]
        if extraction.missing:
            data["_missing_inputs"] = [m["field"] for m in extraction.missing]
        if args.show_inputs:
            shown = {"input": data, "evidence": extraction.evidence, "dropped_unverified": extraction.dropped}
            print(json.dumps(shown, indent=2, ensure_ascii=False), file=sys.stderr)

    try:
        result = run_skill(args.skill, data, provider=provider, context=context)
    except SkillOutputError as e:
        print(f"error: {e}", file=sys.stderr)
        print(e.result.raw_text, file=sys.stderr)
        return 2
    if ws:
        ws.log_run({"type": "skill", "skill": result.skill, "model": result.model, "input": data, "output": result.output})
    payload = result.to_dict() if args.full else result.output
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def cmd_playbook(args: argparse.Namespace) -> int:
    from .playbooks import list_playbooks, load_playbook, run_playbook

    if args.name == "list":
        for name in list_playbooks():
            spec = load_playbook(name)
            print(f"{name}  [{spec.get('stage', 'early')}]\n    {spec['description']}\n")
        return 0
    if not args.notes:
        raise SkillsError(f"give the material to work from, e.g. b2b-skills playbook {args.name} --notes call.txt")
    ws = _workspace(args)
    result = run_playbook(
        args.name, _read_notes(args.notes), provider=_provider(args), workspace=ws, subject=args.subject, save=not args.no_save
    )
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(result.report)
        if result.saved_to:
            print(f"\n(saved to {result.saved_to})", file=sys.stderr)
        elif not ws:
            print("\n(not saved: run inside a workspace created with `b2b-skills init` to keep a history)", file=sys.stderr)
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    from .init_wizard import create_workspace

    provider = _provider(args) if args.website else None
    ask = None
    if not args.yes and _interactive(args):
        print("Ten quick questions about your company (Enter accepts the suggestion in brackets, or skips).\n")

        def ask(question: str, default: str) -> str:
            suffix = f" [{default[:120]}{'...' if len(default) > 120 else ''}]" if default else ""
            answer = input(f"{question}{suffix}\n> ").strip()
            return answer or default

    info = create_workspace(args.path, website=args.website, provider=provider, ask=ask)
    print(f"\nCreated workspace in {info['root']}")
    print("  company.md   your company context (edit it any time)")
    print("  CLAUDE.md    rules for an agent working here")
    print("  gtm/         deals, accounts, run history")
    if info["drafted_from_website"]:
        print(f"\nDrafted from your website (please check): {', '.join(info['drafted_from_website'])}")
    print(f"\nNext: cd {args.path} && b2b-skills playbook call-debrief --notes <call-notes.txt>")
    return 0


def cmd_eval(args: argparse.Namespace) -> int:
    from .evaluation import run_golden

    report = run_golden(provider=_provider(args), skills=args.skill or None, concurrency=args.concurrency, playbooks=args.playbooks)
    if args.json:
        Path(args.json).write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    if args.markdown:
        Path(args.markdown).write_text(report.to_markdown(), encoding="utf-8")
    print(report.to_markdown())
    if args.min_pass_rate is not None and report.pass_rate < args.min_pass_rate:
        print(f"pass rate {report.pass_rate:.0%} is below --min-pass-rate {args.min_pass_rate:.0%}", file=sys.stderr)
        return 1
    return 0


def cmd_mcp(args: argparse.Namespace) -> int:
    from .mcp_server import main as mcp_main

    mcp_main(transport=args.transport)
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    from .server import main as serve_main

    serve_main(host=args.host, port=args.port)
    return 0


def _provider_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--provider", help="mock | claude-code | anthropic | openai (default: $PROVIDER, then mock)")
    p.add_argument("--model", help="override the provider's default model")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="b2b-skills", description="GTM skills and playbooks for B2B teams, with any LLM.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="create a GTM workspace (company.md, agent rules, deal history)")
    p.add_argument("path", nargs="?", default=".", help="folder to create (default: current folder)")
    p.add_argument("--website", help="draft answers from your website first")
    p.add_argument("-y", "--yes", action="store_true", help="don't ask questions; accept drafts")
    _provider_args(p)
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("list", help="list available skills")
    p.add_argument("-v", "--verbose", action="store_true", help="include descriptions")
    p.add_argument("--stage", choices=STAGES, help="only skills that fit this company stage")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("show", help="print a skill's instructions, inputs, or output schema")
    p.add_argument("skill")
    p.add_argument("--schema", action="store_true", help="print the output JSON Schema")
    p.add_argument("--inputs", action="store_true", help="print the input fields")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("run", help="run one skill on JSON input or free-text notes")
    p.add_argument("skill")
    p.add_argument("-i", "--input", help="path to a JSON file, or - for stdin")
    p.add_argument("-n", "--notes", action="append", help="notes/transcript file or folder (repeatable); inputs are extracted from it")
    p.add_argument("--show-inputs", action="store_true", help="print the extracted inputs and their evidence to stderr")
    p.add_argument("--no-questions", action="store_true", help="don't ask about missing inputs")
    p.add_argument("--no-context", action="store_true", help="ignore the workspace's company.md")
    p.add_argument("--full", action="store_true", help="print the full result (validation, usage, raw text)")
    _provider_args(p)
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("playbook", help="run a playbook (or `playbook list`)")
    p.add_argument("name", help="playbook name, or `list`")
    p.add_argument("-n", "--notes", action="append", help="notes/transcript file or folder (repeatable), or - for stdin")
    p.add_argument("--subject", help="what the report is about (e.g. the deal name); decides the file it's saved to")
    p.add_argument("--no-save", action="store_true", help="don't write to the workspace")
    p.add_argument("--no-context", action="store_true", help="ignore the workspace's company.md")
    p.add_argument("--json", action="store_true", help="print the full result as JSON")
    _provider_args(p)
    p.set_defaults(func=cmd_playbook)

    p = sub.add_parser("eval", help="run the golden evals")
    _provider_args(p)
    p.add_argument("--skill", action="append", help="limit to a skill (repeatable)")
    p.add_argument("--playbooks", action="store_true", help="also run the playbook evals")
    p.add_argument("--json", help="write the report as JSON to this path")
    p.add_argument("--markdown", help="write the report as Markdown to this path")
    p.add_argument("--min-pass-rate", type=float, help="exit 1 if the pass rate is below this (0-1)")
    p.add_argument("--concurrency", type=int, default=1, help="cases to run in parallel (default 1)")
    p.set_defaults(func=cmd_eval)

    p = sub.add_parser("mcp", help="start the MCP server")
    p.add_argument("--transport", default="stdio", choices=["stdio", "streamable-http", "sse"])
    p.set_defaults(func=cmd_mcp)

    p = sub.add_parser("serve", help="start the HTTP API server")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.set_defaults(func=cmd_serve)
    return parser


def main(argv: list[str] | None = None) -> int:
    _load_dotenv()
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except (SkillsError, ValueError, FileNotFoundError, FileExistsError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
