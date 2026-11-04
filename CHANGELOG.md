# Changelog

## [Unreleased]

### Added

- **Checkup reads your documents** (`--docs PATH ...`, files or folders): CRM deal exports, lead sheets, customer lists, PMF surveys (CSV or XLSX), and call notes, transcripts, decks, and docs (TXT, MD, VTT, SRT, DOCX, PPTX, HTML; PDF with the new `docs-reader` extra). Files are recognized by content. Spreadsheet numbers (win rate, deal size, sales cycle, lost reasons, lead-source mix, customer-attribute lift, stale open deals) are computed in code and given to the model as quotable sentences. Every score names the file it came from; documents alone can produce a GTM score; one call note or deck alone can't make an area strong. Sample files in `examples/demo/docs/`.
- **GTM checkup** (`b2b-skills checkup [yourcompany.com]`): the new front door. Ten quick questions plus the website produce a scorecard across 8 areas (ICP, product-market fit, positioning and messaging, proof, demand and channels, pricing, sales motion, pipeline), each owned by a GTM role, with the biggest risk, the top 3 fixes, and what would unlock unknown areas. Optional `--survey` and `--pipeline` data deepen it. Rubric points and every score are computed in code; every point quotes the founder's answers or the page; unknown is never scored as zero; one answered criterion can't make an area strong; a website alone gets a website score, not a GTM score. Passes its evals on Claude Sonnet 4.5, and was checked on two real startup websites.
- **`gtm-founder-diagnostic`** and **`gtm-website-audit`** skills (now 48): the founder interview scored on six rubrics, and the website scored on ICP clarity, Dunford positioning components, the swap test, and proof.
- The page reader now keeps the page title, meta description, and image alt text (customer logos are often images).
- **`fix-my-message` playbook** (marketing): `b2b-skills playbook fix-my-message --website <url> --notes win-loss.md` turns your current copy and win/loss evidence into a positioning statement, claim-by-claim clarity scores, a rewritten headline and subhead, three outbound angles, and the proof you still need. Never invents proof points: gaps become bracketed placeholders. Evals fail on invented customer counts or unsupported generalizations. Passes 3/3 on Claude Sonnet 4.5.
- `--website` on notes playbooks reads a web page as source material.

### Changed

- Numbers in suggested fixes are checked against the founder's answers, not the question labels ("Q3.", "Q5." no longer let "3-stage" or "5 questions" through).
- Numbers in suggested fixes must appear whole in the sources, with their "$" and unit: "$200/seat" no longer passes because "51-200" is in a lead sheet, and "60 days" needs "60 days".
- The README leads with the checkup and presents the skills as a GTM team: CMO, Head of Sales, RevOps lead, Strategy advisor.
- Evidence gathered from several places on a page is accepted when every fragment is verbatim.
- The repository is now `pratsy/B2B_agent_skills` (was `pratsy/skills-AI`). GitHub redirects old repo and clone URLs; the docs site moved to https://pratsy.github.io/B2B_agent_skills/.
- The README and docs present the workspace for sales, marketing, and RevOps, with jobs by team; previously they pitched founder-led sales only.
- New demo GIF of a real checkup with answers, documents, and the homepage; the teaser video shows documents too.

## [0.5.0] - Unreleased

Connect the tools founders work in: HubSpot, call transcripts, Slack, a weekly review, and approvals for every outside change.

### Added

- **`monday-review` playbook**: `b2b-skills playbook monday-review --hubspot` (or `--csv pipeline.csv`). Code flags overdue, silent, and stuck deals and deals with no evidence on file. Deals with debrief notes are re-scored with `deal-risk-assessor` from the raw notes. Priority is computed in code, and the report is checked against it and retried if it re-orders. Writes `gtm/reviews/<date>.md`.
- **HubSpot connector**: reads open deals with their companies (CRM v3 API, private app token). `b2b-skills hubspot setup` creates four write-back deal properties; `b2b-skills hubspot deals` lists open deals. Tested against a simulated API, not yet a live portal.
- **Approvals**: playbooks propose outside changes into `gtm/pending/`; `b2b-skills pending`, `approve <id|all> [--dry-run]`, and `reject` act on them. Failed writes stay pending; decisions are kept in `gtm/applied/` and `gtm/rejected/`.
- **Transcript inbox**: `b2b-skills inbox` debriefs every new file in `gtm/inbox/` (any recorder's text export) and moves it to `processed/`. Deal name comes from the file name.
- **Webhook**: `POST /v1/playbooks/{name}/run` on `b2b-skills serve`, for Zapier/Make or recorder webhooks.
- **Slack digests**: `--slack` on `inbox` and `monday-review` (incoming webhook).
- **Outcomes**: `b2b-skills outcome <deal> won|lost` appends to `gtm/outcomes.csv`, the data future calibration will learn from.
- **Weekly automation**: `init` writes `.github/workflows/gtm-weekly.yml`, which debriefs the inbox, reviews the pipeline, posts to Slack, and commits notes every Monday, on a Claude subscription token.
- Docs: Playbooks and Workspace & connectors pages; the README now leads with the founder workspace.

### Changed

- Debriefs now save the raw notes (collapsed) with each report, so later reviews re-score from primary evidence, not a summary.

## [0.4.0] - Unreleased

Lists and ICP: score a lead list, find who to sell to, measure product-market fit.

### Added

- **`score-list` playbook**: `b2b-skills playbook score-list --csv leads.csv` ranks every row of an Apollo/Clay/HubSpot/LinkedIn export against `gtm/icp.json`. Fit is computed in code (exact, instant, no model calls), with an A/B/C/skip tier and reasons per row. Missing data is reported as unknown, not scored as a mismatch. The top rows (default 50) get a why-now and an opening line from the model, which may only use the row's own fields and the company context: no invented statistics, social proof, or numbers. Writes `gtm/lists/<name>-scored.csv` and `gtm/lists/<name>.md`.
- **`find-icp` playbook**: `b2b-skills playbook find-icp --customers accounts.csv [--notes interviews/]` computes attribute lift from won vs. lost accounts in code, extracts triggers and anxieties from interviews, writes a one-page ICP brief with an honest confidence level, and proposes `gtm/icp.proposed.json` (`--apply` writes `gtm/icp.json`).
- **`pmf-survey-analyzer` skill** (46th): the Sean Ellis 40% test, segmented, with the top benefit among must-have users. `b2b-skills run pmf-survey-analyzer --csv responses.csv`.
- **`b2b-skills batch <skill> rows.csv -o out.csv`**: run any skill once per CSV row, with columns matched to the skill's inputs.
- **`run --csv`**: feed CSV rows into a skill's list input (e.g. survey responses).
- **Calculators** (`b2b_agent_skills.calculators`): ICP fit scoring and attribute lift, exact and repeatable.
- **Column mapping** for common export headers (`--map field=Column` overrides), including semicolon-separated files and size ranges like "51-200".
- Playbook evals for score-list (including checks that fail on invented statistics in opening lines) and find-icp. Both pass on Claude Sonnet 4.5.

## [0.3.0] - Unreleased

Founder workspace: company context, free-text input, and the first playbook.

### Added

- **`b2b-skills init`**: creates a GTM workspace (`company.md`, agent rules in `CLAUDE.md`, `.mcp.json`, `gtm/` for deals and run history). Ten short questions; `--website` drafts the answers from the company's site first and marks them "verify".
- **Company context**: inside a workspace, `company.md` is added to every skill and playbook call, so output is specific to the company. It goes in the user message, so skill instructions stay cacheable.
- **Free-text input**: `b2b-skills run <skill> --notes call.txt` extracts the skill's inputs from notes or transcripts (.txt, .md, .vtt, .srt, JSON exports). Every extracted value needs a verbatim quote, and quotes are checked in code: unverifiable values are dropped and become questions for the user.
- **Input schemas**: `.claude/skills/<skill>/input.schema.json`, generated from each README's Inputs table (drift-checked in CI). `b2b-skills show <skill> --inputs`.
- **Playbooks**: `b2b-skills playbook call-debrief --notes call.txt` turns a call into a verdict, next 3 actions, missing evidence, stakeholders, objection handling, and a draft follow-up email, appended to `gtm/deals/<deal>.md`. Also available as a Claude Code skill (via the plugin) and over MCP (`list_playbooks`, `get_playbook`, `run_playbook`).
- **Playbook evals** (`evals/playbooks/`, `b2b-skills eval --playbooks`), including cases that fail if the report invents evidence or proof points. 3/3 pass on Claude Sonnet 4.5.
- **Stages**: every skill is labeled early, growth, or scale; `b2b-skills list --stage early`.
- **Small-sample rule**: results built on little data are labeled "provisional (n=...)".
- **Run log**: every run inside a workspace is appended to `gtm/runs/YYYY-MM.jsonl`.

## [0.2.0] - 2026-11-03

Production release: installable package, structured outputs, golden evals, MCP server, Claude Code plugin.

### Breaking

- The Python package is now `b2b_agent_skills` (was `sdk`), installed from PyPI as `b2b-agent-skills`. `requirements.txt` and `bin/skills-ai` are replaced by `pyproject.toml` extras and the `b2b-skills` command.
- `run_skill(skill, input, provider=...)` returns a `SkillResult` with schema-validated `output`, and raises `SkillOutputError` when the model's output is still invalid after one retry. It previously returned unvalidated `{"skill", "result"|"raw"}`.
- `sdk.evaluation.SKILL_EXPECTED_FIELDS` / `evaluate_skill_output` are removed. Use each skill's `schema.json` (`get_skill(name).schema`) and `b2b_agent_skills.validation.validate_output`.
- `examples/webhook_app.py` and `benchmarks/` are removed. Use `b2b-skills serve` and `evals/golden/` instead.

### Added

- **Per-skill JSON Schemas**: `.claude/skills/<skill>/schema.json`, generated from each README's Output schema by `scripts/generate_schemas.py` (CI fails on drift). Every `SKILL.md` now points at its schema.
- **Structured outputs**: Claude via `output_config.format` (with prompt caching on the skill instructions and server-side refusal fallbacks), OpenAI via `response_format: json_schema`. JSON parsing tolerates markdown fences. Invalid output is retried once with validation feedback.
- **Golden evals**: 60 cases covering all 45 skills that check actual answers (numbers, bands, decisions), the `b2b-skills eval` command (with `--concurrency`), and a manually triggered GitHub workflow that runs them against a real model. CI requires every skill to have a golden suite. First real-model run: 59/60 on Claude Sonnet 4.5 ([evals/results/](evals/results/)).
- **`claude-code` provider**: runs skills through the local Claude Code CLI (`claude -p`, isolated and tool-less), so you can use a Claude subscription instead of an API key. The GitHub eval workflow uses it by default via a `CLAUDE_CODE_OAUTH_TOKEN` secret.
- **MCP server** (`b2b-skills mcp`): `list_skills` and `get_skill` tools, one prompt per skill, and a `run_skill` tool when a real provider is configured.
- **Claude Code plugin and marketplace** (`.claude-plugin/`): install with `/plugin marketplace add pratsy/skills-AI`.
- **HTTP API** (`b2b-skills serve`): bearer-token auth (required by default), body-size limit, sanitized errors. Plus a `Dockerfile`.
- `pyproject.toml` with optional extras (`anthropic`, `openai`, `mcp`, `server`, `dotenv`, `all`, `dev`, `docs`). The wheel bundles the skills and golden evals.
- Documentation site (MkDocs Material, deployed to GitHub Pages) with a generated skill catalog.
- A demo GIF of a real run (`docs/assets/demo.gif`), rendered by `scripts/render_demo_gif.py` from a recorded session, with no VHS or ffmpeg needed.
- CI matrix for Python 3.10-3.13, ruff, mypy, and a check that the built wheel installs and works; PyPI trusted-publishing release workflow; Dependabot; pre-commit.
- Community files: Code of Conduct, issue forms (bug, skill quality, new skill), PR template, CODEOWNERS. `SECURITY.md` now has a private reporting process.

### Fixed

- An incorrect sample-size formula in ad-copy-variant-generator's SKILL.md (divided by MDE² instead of (p × MDE)², under-sizing tests about 3x).
- Skill rubrics that real-model evals showed were underspecified: renewal-risk-scorer (engagement-breadth and sentiment scales), competitor-monitor (velocity lookup), forecast-confidence-model (Omitted takes precedence), market-sizing-modeler (TAM = published x narrowing; divergence compares SAMs), deal-risk-assessor (`single_point_of_failure` lists pillar keys), territory-prioritization-agent (strict sort by priority score), pipeline-health-monitor (unrounded coverage ratio), account-plan-generator (strict sort), forecast-bias-detector (correction-factor direction), stakeholder-map-builder (only confirmed contacts count), campaign-performance-diagnostician (CTR is part of the funnel check), nurture-sequence-architect (step 1 on day 0), value-proposition-tester (lead message is the claim text).
- The output contract now asks the model to work through the scoring model before answering (and to put the final JSON last) when the provider doesn't constrain output to the schema, and includes the skill's documented example as a format reference (number scales, label vocabulary, list-item format). Together with the rubric fixes above, this took the real-model pass rate from 53% to 97-98%.
- README worked examples whose numbers didn't add up: audience-segmentation-optimizer (depth 16 → 18, so 65 → 67 and 91.25 → 91.75; the tier summary was 0) and abm-account-priority-ranker (tier summary was 0).
- The default Anthropic model is `claude-opus-5-5` (was `claude-sonnet-5`), and `max_tokens` is 16000 (was 1500, which truncated larger outputs).
- 13 cross-pack links in skill READMEs that resolved to non-existent paths.

## Earlier changes (unversioned)

- Renamed `skills_ai/` to `sdk/` — the old name overloaded "skills" for a
  fourth thing in a repo that already has `b2b-agent-skills-*/skills/` and
  `.claude/skills/`, which was a source of confusion. Updated every import,
  CLI reference, and doc link accordingly.
- Rewrote `sdk/providers.py`: fixed `OpenAIProvider`, which was written
  against the pre-1.0 `openai.ChatCompletion` API while `requirements.txt`
  installed the current SDK (v1+) — the old code would have raised an
  `AttributeError` on first real call. Added a native `AnthropicProvider`
  alongside it, since this is fundamentally a Claude Code skills repo and
  didn't have one. `PROVIDER=mock|anthropic|openai` are now equally
  supported, matching `.env.example`.
- Rewrote `SECURITY.md`, which was generic AI-security boilerplate hardcoded
  to OpenAI despite the SDK being provider-agnostic, and ended with an
  unrelated paragraph about GitHub Actions approval-gate policy. Now
  describes what data actually leaves the machine, how to configure any of
  the three providers, and flags that `examples/webhook_app.py` has no auth
  and isn't production-ready.
- `sdk.runner.run_skill()` now accepts `input_data` directly instead of
  requiring a JSON file path; simplified `examples/webhook_app.py`
  accordingly (it previously round-tripped the request payload through a
  temp file, and was hardcoded to `MockProvider` regardless of `.env`
  configuration, so it could never call a real model).
- Packaged all 45 skills as real Claude Code Skills (`.claude/skills/<slug>/SKILL.md`),
  not just markdown to read — clone the repo and Claude Code invokes them directly.
- Rebuilt `skills_ai`'s runner to read those same `SKILL.md` files as its prompt
  source instead of maintaining separate Jinja templates. Removed the 5 bespoke
  `skills_ai/skills/*.py` wrappers, their `.j2` templates, and `template_loader.py`
  (and the now-unused `jinja2` dependency) — every skill now runs through one
  generic path, so all 45 are runnable via the Python SDK, not a hardcoded 5.
- Expanded `skills_ai.evaluation.SKILL_EXPECTED_FIELDS` from 5 to all 45 skills,
  extracted directly from each skill's own "Output schema" section, and fixed the
  scoring formula (previously hardcoded to a 5-field/20-point split).
- Fixed `benchmarks/sample_dataset.json`, which still used a pre-rewrite output
  schema for `renewal-risk-scorer` and `executive-sponsor-identifier`; expanded it
  to one representative skill per domain pack with real worked-example data, and
  removed the now-redundant inline CI "smoke test" in favor of the test suite's
  own full-coverage checks.
- Moved `docs/prompt-packs.md` to root-level `PROMPT_PACKS.md` and removed the
  now-empty `docs/` folder (it held only that one file).
- Removed the legacy pre-split `b2b-agent-skills/` folder and merged near-duplicate
  skills (`content-gap-identifier`, `pipeline-health-audit-agent`) into their
  stronger counterparts, bringing the library to 45 skills with no overlap.
- Replaced the repeated, unlinked reference list at the bottom of every skill
  README with a pointer to each pack's `sources-and-frameworks.md`.
- Rewrote the root README for clarity and cut duplicated sections; corrected
  stale skill counts and featured-skill lists that referenced renamed/removed
  skills.
- Added launch-ready CLI and Python SDK wrapper.
- Added OpenAI provider abstraction and template loading.
- Added sales and marketing skill library templates.
- Added evaluation harness and GitHub Actions CI.
- Added security guidance and API example.

## [0.1.0] - 2026-09-10

- Initial public skill library release for B2B sales and marketing workflows.
- Added initial sales skill packs and marketing skill packs.
- Added prompt, example-output, and rubric documentation.
- Added test suite and example fixtures.
