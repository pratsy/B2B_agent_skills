## What this changes

<!-- One or two sentences. Link the issue if there is one. -->

## Type

- [ ] Improves an existing skill (methodology, scoring, example, wording)
- [ ] New skill
- [ ] SDK / CLI / MCP / server / plugin
- [ ] Docs or project infrastructure

## Checklist

- [ ] `pytest` passes locally
- [ ] If a README's **Output schema** changed: ran `python scripts/generate_schemas.py` and committed the updated `schema.json` (this is a breaking change for anyone parsing that skill's output; say so above)
- [ ] New skill: README in its pack, `.claude/skills/<name>/SKILL.md`, generated `schema.json`, and at least one golden case in `evals/golden/<name>.json`
- [ ] No real customer, prospect, or deal data in examples, fixtures, or golden cases
