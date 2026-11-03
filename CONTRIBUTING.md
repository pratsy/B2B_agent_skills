# Contributing

Thanks for helping. The bar for this repo is that every skill is **specific, evidence-grounded, and checkable**: a named methodology, an explicit scoring model, and an answer you can verify. Contributions that raise that bar are the most welcome.

## Setup

```bash
git clone https://github.com/pratsy/B2B_agent_skills && cd B2B_agent_skills
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
pytest
```

The test suite runs in a few seconds and needs no API key.

## How a skill is put together

Each skill has four files. Only the first two are written by hand:

| File | Role | Written by |
|---|---|---|
| `b2b-agent-skills-<pack>/skills/<name>/README.md` | Full methodology, scoring model, inputs, worked example, **output schema**. The source of truth | you |
| `.claude/skills/<name>/SKILL.md` | Condensed instructions an LLM executes (under ~60 lines), with frontmatter `name` and a `description` that says what it does and "Use when …" | you |
| `.claude/skills/<name>/schema.json` | JSON Schema generated from the README's Output schema block | `python scripts/generate_schemas.py` |
| `evals/golden/<name>.json` | Golden cases: input plus assertions on the right answer | you (strongly encouraged) |

The pre-commit hook regenerates `schema.json` when a README changes, and CI fails if they drift apart.

## Good first contributions

1. **Strengthen golden cases.** Every skill has at least one; many have only one. Add a contrast case that flips the decision, or a harder edge case at a band boundary. See [docs/evals.md](docs/evals.md).
2. **Fix skill quality.** A scoring step that's ambiguous, an example whose numbers don't add up, a missing failure pattern.
3. **Run real-model evals** (`b2b-skills eval --provider anthropic`) and report failures as *Skill gave a wrong or weak answer* issues.

## Adding a new skill

Open a *Propose a new skill* issue first. Check the existing skills for overlap: if yours is a variation of one, improve that skill instead. Then:

1. Write the README using [`memory/skill-template.md`](memory/skill-template.md) and review it against [`memory/domain-memory-checklist.md`](memory/domain-memory-checklist.md).
2. Write `SKILL.md` (copy any existing one as the format reference) and end it with the standard *Output format* section pointing at `schema.json`.
3. Run `python scripts/generate_schemas.py`.
4. Add at least one golden case.
5. Update the skill count in the docs (the tests count skills automatically).

## Changing an existing skill's output schema

Downstream users parse these outputs, so renaming or removing a field is a **breaking change**. Call it out in the PR and in `CHANGELOG.md`. Adding a field is also breaking for strict consumers, so mention it too.

## Code changes

- `ruff check . && ruff format . && mypy && pytest` must pass. Pre-commit runs the first two.
- Keep the core dependency-free beyond `jsonschema`. Provider, MCP, and server dependencies stay in optional extras.
- Provider code must read credentials from the environment only.

## What not to submit

Real customer, prospect, or deal data in examples or golden cases. Internal planning notes. Prompts without a methodology behind them.

By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).
