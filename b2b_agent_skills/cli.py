"""``b2b-skills`` command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import __version__
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


def _provider(args: argparse.Namespace) -> Any:
    from .providers import get_provider

    kwargs = {"model": args.model} if getattr(args, "model", None) else {}
    return get_provider(args.provider, **kwargs)


def cmd_list(args: argparse.Namespace) -> int:
    for name in list_skills():
        skill = get_skill(name)
        if args.verbose:
            print(f"{name}\n    {skill.description}\n")
        else:
            print(name)
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    skill = get_skill(args.skill)
    if args.schema:
        print(json.dumps(skill.schema, indent=2))
    else:
        print(f"# {skill.name}\n\n{skill.description}\n\n{skill.instructions}")
        print("\n## Output fields\n\n" + ", ".join(skill.output_fields))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    from .runner import run_skill

    try:
        result = run_skill(args.skill, _read_input(args.input), provider=_provider(args))
    except SkillOutputError as e:
        print(f"error: {e}", file=sys.stderr)
        print(e.result.raw_text, file=sys.stderr)
        return 2
    payload = result.to_dict() if args.full else result.output
    print(json.dumps(payload, indent=2))
    return 0


def cmd_eval(args: argparse.Namespace) -> int:
    from .evaluation import run_golden

    report = run_golden(provider=_provider(args), skills=args.skill or None, concurrency=args.concurrency)
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="b2b-skills", description="Run evidence-grounded B2B revenue skills with any LLM.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("list", help="list available skills")
    p.add_argument("-v", "--verbose", action="store_true", help="include descriptions")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("show", help="print a skill's instructions or output schema")
    p.add_argument("skill")
    p.add_argument("--schema", action="store_true", help="print the JSON Schema instead")
    p.set_defaults(func=cmd_show)

    for name, func, help_ in (("run", cmd_run, "run a skill on JSON input"), ("eval", cmd_eval, "run the golden evals")):
        p = sub.add_parser(name, help=help_)
        p.add_argument("--provider", help="mock | anthropic | openai | claude-code (default: $PROVIDER, then mock)")
        p.add_argument("--model", help="override the provider's default model")
        p.set_defaults(func=func)
        if name == "run":
            p.add_argument("skill")
            p.add_argument("-i", "--input", help="path to a JSON file, or - for stdin")
            p.add_argument("--full", action="store_true", help="print the full result (validation, usage, raw text)")
        else:
            p.add_argument("--skill", action="append", help="limit to a skill (repeatable)")
            p.add_argument("--json", help="write the report as JSON to this path")
            p.add_argument("--markdown", help="write the report as Markdown to this path")
            p.add_argument("--min-pass-rate", type=float, help="exit 1 if the pass rate is below this (0-1)")
            p.add_argument("--concurrency", type=int, default=1, help="cases to run in parallel (default 1)")

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
    except (SkillsError, ValueError, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
