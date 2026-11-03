# Golden evals

`golden/<skill>.json` holds test cases that check a skill produces the **right answer**, not just valid JSON. Each case has realistic input and assertions on what the skill's methodology must produce.

```bash
b2b-skills eval --provider claude-code --concurrency 4   # all cases, via your Claude subscription
b2b-skills eval --provider anthropic                      # all cases, via the API
b2b-skills eval --provider mock                           # offline smoke run
b2b-skills eval --skill deal-risk-assessor --provider openai --json report.json
```

The file format, assertion ops, and guidance on writing good cases are in [docs/evals.md](../docs/evals.md).

**Coverage:** all 48 skills, 64 cases (38 mirror a README worked example and are checked offline in CI). Contrast cases that flip a decision are the most useful addition.

No API key? `--provider claude-code` runs the evals through your local Claude Code login, including a Claude Pro/Max subscription.

**Latest real-model run (v0.5):** 65/68 skill and playbook cases on Claude Sonnet 4.5, see [results/](results/).

Playbook evals live in [`playbooks/`](playbooks/) (`b2b-skills eval --playbooks`).
