# Claude Code skills

All 48 skills in this repo are packaged here as real [Claude Code Skills](https://code.claude.com/docs/en/skills) — `SKILL.md` files Claude discovers and can invoke directly, not just markdown you read and copy-paste.

## How to use these

**As a Claude Code plugin** (recommended):

```text
/plugin marketplace add pratsy/B2B_agent_skills
/plugin install b2b-agent-skills@b2b-agent-skills
```

**In this repo**, they're already active: open Claude Code anywhere inside a clone and ask it to score a deal's risk, build a discovery sequence, size a market, and so on.

**In your own project**, copy whole skill folders into your repo's `.claude/skills/`:

```bash
cp -r .claude/skills/deal-risk-assessor /path/to/your-project/.claude/skills/
```

Each folder holds `SKILL.md` (the instructions Claude follows) and `schema.json` (the output contract, generated from the skill's README by `scripts/generate_schemas.py`; don't edit it by hand). No install step, dependency, or API key.

## One definition, every surface

The Python SDK, CLI, MCP server, and HTTP API (package `b2b_agent_skills`) read these same folders, and the PyPI wheel bundles them. A skill's logic lives in exactly one place, so editing a `SKILL.md` here changes every surface.

## Directory

48 skills, matching the four packs exactly:

| Domain | Skills |
|---|---|
| Sales (17) | `account-plan-generator`, `champion-advocacy-builder`, `competitive-differentiation-coach`, `deal-committee-readiness-coach`, `deal-risk-assessor`, `discovery-question-generator`, `executive-briefing-builder`, `executive-sponsor-identifier`, `forecast-confidence-model`, `lead-prioritization-agent`, `multi-threading-plan-builder`, `negotiation-readiness-coach`, `objection-response-coach`, `pricing-justification-builder`, `renewal-risk-scorer`, `stakeholder-map-builder`, `territory-prioritization-agent` |
| Marketing (15) | `abm-account-priority-ranker`, `ad-copy-variant-generator`, `audience-segmentation-optimizer`, `brand-perception-monitor`, `brand-positioning-synthesizer`, `campaign-performance-diagnostician`, `content-gap-analysis-agent`, `customer-journey-friction-audit`, `icp-refinement-agent`, `landing-page-copy-optimizer`, `lifecycle-email-optimizer`, `messaging-clarity-auditor`, `nurture-sequence-architect`, `persona-insight-extractor`, `value-proposition-tester` |
| RevOps (5) | `attribution-model-reviewer`, `crm-data-cleaner`, `forecast-bias-detector`, `pipeline-health-monitor`, `sales-handoff-quality-auditor` |
| GTM (11) | `account-priority-matrix-builder`, `competitor-monitor`, `competitor-signal-clusterer`, `gtm-founder-diagnostic`, `gtm-website-audit`, `market-shift-monitor`, `market-sizing-modeler`, `market-trend-signal-reporter`, `pmf-survey-analyzer`, `strategic-account-priority-ranker`, `win-loss-theme-clusterer` |

## Adding or editing a skill

Use any existing `SKILL.md` as the template: `name` and `description` frontmatter (plus `license: MIT`), then Role / Method / If information is missing / Output / Common failure patterns / Reference sections. Keep it under ~50 lines — the full depth belongs in the pack README it links back to, not duplicated here.
