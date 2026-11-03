# Changelog

## [0.2.0] - Unreleased

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
