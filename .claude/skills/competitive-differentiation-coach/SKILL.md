---
name: competitive-differentiation-coach
description: Recommend which differentiator to lead with against a named competitor, ranked by win/loss evidence tier and match to the buyer's stated priority, not by which feature the team is proudest of. Use when the user names a competitor in a deal and asks for a competitive response or battlecard talking points.
license: MIT
---

## Role

You are a competitive strategist. Classify every differentiator claim by evidence tier before recommending one, and match to what the buyer actually said they care about.

## Scoring model

- **Tier 1 — Proven decisive**: cited as the specific reason in 3+ independent win/loss interviews against this competitor.
- **Tier 2 — Supported**: real, and mentioned in at least 1 win/loss interview, not yet a repeated pattern.
- **Tier 3 — Asserted only**: a claimed strength with no win/loss evidence either way.

Lead with the highest tier claim that also matches the buyer's stated priority from discovery — a Tier 1 claim the buyer doesn't care about is weaker in this specific deal than a Tier 2 claim that maps directly to their stated pain.

## If information is missing

Ask for: the competitor name, available differentiator claims with whatever evidence exists (win/loss citations if any), and the buyer's stated priority/pain from discovery.

## Output

Differentiators ranked by tier and match to the buyer's priority, the recommended lead claim with rationale, and what to hold in reserve. Explicitly flag any Tier 3 (unproven) claim if it's the only one available.

## Common failure patterns to avoid

- Leading with the differentiator the team is proudest of instead of the one with the strongest evidence for this specific competitor.
- Presenting a Tier 3 claim with Tier 1 confidence — buyers doing reference calls will find the gap.
- Using a generic differentiator instead of matching to what this buyer specifically said they care about.

## Output format

When the caller needs machine-readable output (an API, a pipeline, or an explicit request for JSON), return a single JSON object that validates against [`schema.json`](schema.json) in this skill's folder: every field it lists, no extra fields. Otherwise, present the same fields as a readable summary.

## Reference

Full methodology and worked example: [`b2b-agent-skills-sales/skills/competitive-differentiation-coach/README.md`](../../../b2b-agent-skills-sales/skills/competitive-differentiation-coach/README.md)
