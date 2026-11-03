# Claude Code plugin

Install all 45 skills into Claude Code with two commands. No Python, API key, or package install needed: Claude itself applies the methodology.

```text
/plugin marketplace add pratsy/skills-AI
/plugin install b2b-agent-skills@b2b-agent-skills
```

Or from your shell:

```bash
claude plugin marketplace add pratsy/skills-AI
claude plugin install b2b-agent-skills@b2b-agent-skills
```

Then just describe the problem: *"Here are my notes on the Acme deal, is it really Commit?"* Claude picks the matching skill (here `deal-risk-assessor`) from its description. Skills are namespaced under the plugin, e.g. `b2b-agent-skills:deal-risk-assessor`.

Update later with `/plugin marketplace update b2b-agent-skills`.

## Without the plugin

- **Inside a clone of this repo**, the skills in `.claude/skills/` are already active.
- **In your own project**, copy individual skill folders:

```bash
cp -r .claude/skills/deal-risk-assessor /path/to/project/.claude/skills/
```

Copy the whole folder: `SKILL.md` refers to the `schema.json` next to it.

## Getting JSON back

By default Claude presents results as a readable summary. Ask for JSON ("return it as JSON") and it returns an object matching the skill's `schema.json`.
