# B2B Agent Skills

[![CI](https://github.com/pratsy/skills-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/pratsy/skills-AI/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/b2b-agent-skills)](https://pypi.org/project/b2b-agent-skills/)
[![Python](https://img.shields.io/pypi/pyversions/b2b-agent-skills)](https://pypi.org/project/b2b-agent-skills/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**45 AI skills for B2B sales, marketing, RevOps and GTM, each built on a named methodology with a scoring model you can check and a JSON Schema output contract.**

Most AI prompt libraries give you one instruction and stop there. Each skill here encodes how an experienced operator works the problem: MEDDPICC scored by *evidence quality* rather than rep confidence, pipeline coverage calibrated to *your* win rate, TAM reconciled top-down against bottom-up. The output is a decision you can verify and wire into a pipeline, not generic text.

Use the skills in **Claude Code**, from any **MCP client**, from **Python**, or over **HTTP**. One skill definition powers all four.

![Demo: scoring a deal with deal-risk-assessor](docs/assets/demo.gif)

```bash
pip install b2b-agent-skills
b2b-skills run deal-risk-assessor -i examples/fixtures/deal_risk_input.json --provider claude-code   # uses your Claude login, no API key
```

```json
{
  "deal_id": "opp_5521",
  "pillar_scores": { "metrics": 3, "economic_buyer": 1, "decision_criteria": 2, "decision_process": 0, "paper_process": 0, "identify_pain": 3, "champion": 2, "competition": 1 },
  "total_score": 12,
  "risk_band": "high",
  "single_point_of_failure": ["economic_buyer"],
  "forecast_recommendation": "Pipeline only; do not forecast as closing this period",
  "priority_action": "get a direct CFO conversation to confirm they are the economic buyer, validate the decision process, and surface the paper process"
}
```

<sub>Real output (Claude Sonnet via `--provider claude-code`) for the sample deal, recorded in [docs/assets/demo-session.txt](docs/assets/demo-session.txt). Wording varies between runs; the scores follow the rubric.</sub>

## Quick start

| You want to… | Do this |
|---|---|
| Use the skills in **Claude Code** | `/plugin marketplace add pratsy/skills-AI`, then `/plugin install b2b-agent-skills@b2b-agent-skills`, then describe your problem |
| Use them in **Claude Desktop, Cursor, or any MCP client** | `pip install "b2b-agent-skills[mcp]"` and add `b2b-skills mcp` as a server ([guide](docs/mcp.md)) |
| Call them from **Python** | `run_skill("pipeline-health-monitor", data, provider="anthropic")` ([guide](docs/sdk.md)) |
| Try them **without an API key** | `b2b-skills run <skill> -i input.json --provider claude-code` runs through your Claude Code login / Claude subscription |
| Call them from **another service** | `b2b-skills serve` or the Docker image: an authenticated REST API ([guide](docs/http-api.md)) |

Full documentation: **https://pratsy.github.io/skills-AI/**

## What's in it

| Pack | Covers | Skills |
|---|---|---|
| [Sales](b2b-agent-skills-sales/) | deal risk (MEDDPICC), forecast category, stakeholder maps, discovery (SPIN), objections, negotiation, pricing/ROI, renewals | 17 |
| [Marketing](b2b-agent-skills-marketing/) | ICP refinement, segmentation, positioning (Dunford), messaging clarity, campaign diagnostics, ABM, lifecycle, content gaps | 15 |
| [RevOps](b2b-agent-skills-revops/) | pipeline health, forecast bias, CRM data quality, attribution, handoff quality | 5 |
| [GTM](b2b-agent-skills-gtm/) | market sizing (TAM/SAM/SOM), competitor and market signals, strategic account selection, win/loss themes | 8 |

Every skill README has the same parts: when to use it, the methodology, the scoring model, inputs, a worked example with real numbers, common failure patterns, the output schema, and sources. Browse the [skill catalog](https://pratsy.github.io/skills-AI/skills/).

## Why you can build on it

- **Structured outputs, validated.** Each skill ships a JSON Schema ([`schema.json`](.claude/skills/deal-risk-assessor/schema.json)). Claude and OpenAI are constrained to it, every response is validated, and invalid output is retried once with the errors as feedback, then raised as an error. You never get unvalidated output silently.
- **Golden evals check answers, not just shape.** [`evals/golden/`](evals/golden/) has 60 cases covering all 45 skills, e.g. *forecast-confidence-model must call a MEDDPICC-20 deal Best Case when it's stalled at 1.89× the median time-in-stage*. Run them against any model with `b2b-skills eval`, including through your Claude subscription (`--provider claude-code`), or from GitHub Actions.
- **Production defaults.** Prompt caching on skill instructions, server-side refusal fallbacks on Claude, token usage on every result, a bearer-token HTTP server that refuses to start without auth, and a non-root Docker image.
- **Minimal footprint.** The core depends only on `jsonschema`. Providers, MCP, and the server are optional extras.

## Repository layout

```
.claude/skills/<skill>/        SKILL.md + schema.json - the one definition every surface reads
b2b-agent-skills-<pack>/       human-readable methodology READMEs (source of truth for schemas)
b2b_agent_skills/              Python package: SDK, CLI, MCP server, HTTP server
evals/golden/                  golden eval cases
.claude-plugin/                Claude Code plugin + marketplace manifests
docs/                          documentation site (MkDocs)
```

## Contributing

The most useful contributions right now are **more golden eval cases** (contrast and edge cases), fixes to skill methodology, and real-model eval reports. See [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md). Report security issues privately ([SECURITY.md](SECURITY.md)).

## License

[MIT](LICENSE)
