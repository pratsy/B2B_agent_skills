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
    if args.csv:
        from .tables import read_csv

        _, rows = read_csv(args.csv)
        skill = get_skill(args.skill)
        arrays = [k for k, v in skill.input_schema.get("properties", {}).items() if v.get("type") == "array"]
        field = args.csv_field or (arrays[0] if arrays else "rows")
        data[field] = rows

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
    spec = load_playbook(args.name)
    if spec["kind"] == "list":
        return _playbook_list(args)
    if spec["kind"] == "icp":
        return _playbook_icp(args)
    if spec["kind"] == "review":
        return _playbook_review(args)
    if not args.notes and not args.website:
        raise SkillsError(f"give the material to work from, e.g. b2b-skills playbook {args.name} --notes call.txt")
    sources = _read_notes(args.notes) if args.notes else []
    if args.website:
        from .init_wizard import fetch_website_text

        sources.insert(0, f"[website: {args.website}]\n{fetch_website_text(args.website)}")
    ws = _workspace(args)
    result = run_playbook(args.name, sources, provider=_provider(args), workspace=ws, subject=args.subject, save=not args.no_save)
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(result.report)
        if result.saved_to:
            print(f"\n(saved to {result.saved_to})", file=sys.stderr)
        elif not ws:
            print("\n(not saved: run inside a workspace created with `b2b-skills init` to keep a history)", file=sys.stderr)
    return 0


def _playbook_list(args: argparse.Namespace) -> int:
    from .lists import score_list
    from .tables import parse_overrides

    if not args.csv:
        raise SkillsError("give the list to score: b2b-skills playbook score-list --csv leads.csv")
    ws = _workspace(args)
    icp = json.loads(Path(args.icp).read_text(encoding="utf-8")) if args.icp else (ws.icp() if ws else {})
    provider = None if args.no_angles else _provider(args)
    result = score_list(
        args.csv,
        icp,
        provider=provider,
        workspace=ws,
        overrides=parse_overrides(args.map),
        top=args.top,
        output=args.output,
        concurrency=args.concurrency,
    )
    print(result.report)
    for path in filter(None, (result.saved_csv, result.saved_report)):
        print(f"(saved {path})", file=sys.stderr)
    return 0


def _playbook_icp(args: argparse.Namespace) -> int:
    from .icp import find_icp
    from .tables import parse_overrides

    ws = _workspace(args)
    result = find_icp(
        customers_csv=args.customers,
        notes=_read_notes(args.notes) if args.notes else None,
        provider=_provider(args),
        workspace=ws,
        overrides=parse_overrides(args.map),
        apply=args.apply,
    )
    print(result.report)
    for kind, path in result.saved.items():
        print(f"(saved {kind}: {path})", file=sys.stderr)
    if result.saved.get("icp", "").endswith("icp.proposed.json"):
        print("Review gtm/icp.proposed.json; re-run with --apply (or rename it to icp.json) to use it for list scoring.", file=sys.stderr)
    return 0


def _require_workspace(args: argparse.Namespace) -> Any:
    ws = _workspace(args)
    if not ws:
        raise SkillsError("run this inside a workspace (create one with `b2b-skills init`)")
    return ws


def _playbook_review(args: argparse.Namespace) -> int:
    from .review import deals_from_csv, monday_review
    from .tables import parse_overrides

    if args.hubspot:
        from .connectors.hubspot import HubSpot

        deals = HubSpot().open_deals()
    elif args.csv:
        deals = deals_from_csv(args.csv, parse_overrides(args.map))
    else:
        raise SkillsError("give the pipeline: --hubspot, or --csv pipeline.csv (an open-deals export)")
    ws = _workspace(args)
    result = monday_review(
        deals,
        provider=_provider(args),
        workspace=ws,
        max_scored=args.max_scored,
        propose_writebacks=bool(args.hubspot and ws),
        concurrency=args.concurrency,
    )
    print(result.report)
    if result.saved_to:
        print(f"\n(saved to {result.saved_to})", file=sys.stderr)
    if result.proposed:
        print(
            f"{len(result.proposed)} HubSpot update(s) proposed. Review with `b2b-skills pending`, apply with `b2b-skills approve all`.",
            file=sys.stderr,
        )
    if args.slack:
        from .notify import post_slack

        post_slack(result.report)
        print("(posted to Slack)", file=sys.stderr)
    return 0


def cmd_inbox(args: argparse.Namespace) -> int:
    from .inbox import process_inbox

    ws = _require_workspace(args)
    items = process_inbox(ws, _provider(args))
    if not items:
        print(f"Inbox empty. Drop transcripts into {ws.gtm / 'inbox'} (name them after the deal).")
        return 0
    for item in items:
        if item.error:
            print(f"✗ {item.file}: {item.error}")
            continue
        assert item.result is not None
        verdict = item.result.report.split("## Next 3 actions")[0].replace("## Verdict", "").strip()
        print(f"✓ {item.file} -> {item.result.saved_to}\n  {verdict[:300]}")
        if args.slack:
            from .notify import post_slack

            post_slack(f"*Call debrief: {item.subject}*\n\n{item.result.report}")
    return 1 if any(i.error for i in items) else 0


def cmd_pending(args: argparse.Namespace) -> int:
    from .approvals import describe, pending

    items = pending(_require_workspace(args))
    print("\n".join(describe(c) for c in items) if items else "Nothing pending.")
    return 0


def _appliers() -> dict[str, Any]:
    def hubspot(change: dict[str, Any]) -> None:
        from .connectors.hubspot import HubSpot

        HubSpot().update_deal(change["object_id"], change["changes"])

    return {"hubspot": hubspot}


def cmd_approve(args: argparse.Namespace) -> int:
    from .approvals import approve

    results = approve(_require_workspace(args), args.which, _appliers(), dry_run=args.dry_run)
    for r in results:
        print(f"{r['status']:>12}  [{r['id']}] {r['target']} {r['label']}" + (f"  ({r['error']})" if r.get("error") else ""))
    return 1 if any(r["status"] == "failed" for r in results) else 0


def cmd_reject(args: argparse.Namespace) -> int:
    from .approvals import reject

    for r in reject(_require_workspace(args), args.which):
        print(f"rejected  [{r['id']}] {r['label']}")
    return 0


def cmd_outcome(args: argparse.Namespace) -> int:
    from .approvals import record_outcome

    ws = _require_workspace(args)
    path = record_outcome(ws, args.subject, args.result, args.value, args.reason or "")
    ws.log_run({"type": "outcome", "subject": args.subject, "outcome": args.result, "value": args.value, "reason": args.reason})
    print(f"Recorded {args.subject}: {args.result} ({path.relative_to(ws.root)})")
    return 0


def cmd_hubspot(args: argparse.Namespace) -> int:
    from .connectors.hubspot import HubSpot

    hs = HubSpot()
    if args.action == "setup":
        created = hs.ensure_writeback_properties()
        print("Created deal properties: " + ", ".join(created) if created else "Write-back properties already exist.")
    else:
        for d in hs.open_deals(limit=args.limit):
            print(
                f"{d['deal_id']:>12}  {d['deal_name']}  ({d['company'] or 'no company'})  {d['amount'] or ''}  stage={d['stage']}  close={d['close_date']}"
            )
    return 0


def cmd_batch(args: argparse.Namespace) -> int:
    from .lists import batch_skill
    from .tables import parse_overrides

    ws = _workspace(args)
    out, mapping = batch_skill(
        args.skill,
        args.csv,
        provider=_provider(args),
        overrides=parse_overrides(args.map),
        output=args.output,
        concurrency=args.concurrency,
        context=ws.company_context() if ws else None,
        limit=args.limit,
    )
    ok = sum(1 for r in out if r.get("_valid"))
    print(
        f"{ok}/{len(out)} rows scored with {args.skill}. Columns used: " + ", ".join(f"{f} <- {h}" for f, h in mapping.items()),
        file=sys.stderr,
    )
    if args.output:
        print(f"(saved {args.output})", file=sys.stderr)
    else:
        print(json.dumps(out, indent=2, ensure_ascii=False))
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
    p.add_argument("--csv", help="CSV whose rows become one list input (e.g. survey responses)")
    p.add_argument("--csv-field", help="input field for the --csv rows (default: the skill's first list input)")
    p.add_argument("--full", action="store_true", help="print the full result (validation, usage, raw text)")
    _provider_args(p)
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("batch", help="run a skill once per CSV row and write the results as CSV")
    p.add_argument("skill")
    p.add_argument("csv")
    p.add_argument("-o", "--output", help="output CSV (default: print JSON)")
    p.add_argument("--map", action="append", help="input_field=Column Name (repeatable)")
    p.add_argument("--concurrency", type=int, default=2)
    p.add_argument("--limit", type=int, help="only the first N rows")
    p.add_argument("--no-context", action="store_true", help="ignore the workspace's company.md")
    _provider_args(p)
    p.set_defaults(func=cmd_batch)

    p = sub.add_parser("playbook", help="run a playbook (or `playbook list`)")
    p.add_argument("name", help="playbook name, or `list`")
    p.add_argument("-n", "--notes", action="append", help="notes/transcript file or folder (repeatable), or - for stdin")
    p.add_argument("--subject", help="what the report is about (e.g. the deal name); decides the file it's saved to")
    p.add_argument("--no-save", action="store_true", help="don't write to the workspace")
    p.add_argument("--no-context", action="store_true", help="ignore the workspace's company.md")
    p.add_argument("--json", action="store_true", help="print the full result as JSON")
    p.add_argument("--website", help="fix-my-message: read this page as source material")
    p.add_argument("--csv", help="score-list: the lead/account list to score")
    p.add_argument("--icp", help="score-list: ICP JSON file (default: gtm/icp.json)")
    p.add_argument("--top", type=int, default=50, help="score-list: write reasons and opening lines for this many (default 50)")
    p.add_argument("--no-angles", action="store_true", help="score-list: scores only, no LLM calls")
    p.add_argument("-o", "--output", help="score-list: output CSV path")
    p.add_argument("--customers", help="find-icp: account list with an outcome column (won/lost)")
    p.add_argument("--apply", action="store_true", help="find-icp: write gtm/icp.json directly instead of icp.proposed.json")
    p.add_argument("--map", action="append", help="field=Column Name, when a column isn't recognized (repeatable)")
    p.add_argument("--hubspot", action="store_true", help="monday-review: read open deals from HubSpot")
    p.add_argument("--max-scored", type=int, default=15, help="monday-review: re-score at most this many deals from notes")
    p.add_argument("--slack", action="store_true", help="monday-review: post the review to SLACK_WEBHOOK_URL")
    p.add_argument("--concurrency", type=int, default=2)
    _provider_args(p)
    p.set_defaults(func=cmd_playbook)

    p = sub.add_parser("inbox", help="debrief every new transcript in gtm/inbox/")
    p.add_argument("--slack", action="store_true", help="post each debrief to SLACK_WEBHOOK_URL")
    _provider_args(p)
    p.set_defaults(func=cmd_inbox)

    p = sub.add_parser("pending", help="list proposed changes waiting for approval")
    p.set_defaults(func=cmd_pending)
    p = sub.add_parser("approve", help="apply proposed changes (an id, or all)")
    p.add_argument("which")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_approve)
    p = sub.add_parser("reject", help="discard proposed changes (an id, or all)")
    p.add_argument("which")
    p.set_defaults(func=cmd_reject)

    p = sub.add_parser("outcome", help="record a won/lost outcome (for calibration later)")
    p.add_argument("subject", help="deal or lead name")
    p.add_argument("result", choices=["won", "lost", "no-decision"])
    p.add_argument("--value", type=float)
    p.add_argument("--reason")
    p.set_defaults(func=cmd_outcome)

    p = sub.add_parser("hubspot", help="HubSpot connector: `setup` creates write-back properties, `deals` lists open deals")
    p.add_argument("action", choices=["setup", "deals"])
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(func=cmd_hubspot)

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
