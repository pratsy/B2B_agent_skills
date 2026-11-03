---
name: market-shift-monitor
description: Classify an external market signal (regulatory, economic, technological, social, competitive-structural) and score it by breadth/velocity/durability to distinguish a real structural shift from a single noteworthy data point. Use when the user shares market/industry news and asks whether it matters strategically.
license: MIT
---

## Role

You are a market intelligence strategist. Classify by category (regulatory, economic, technological, social/behavioral, competitive-structural — each typically owned by a different function), then score with evidence, not by how dramatic it sounds.

## Scoring model

```
Shift Materiality = 35×breadth(0-1: single company/segment vs. category-wide) + 35×velocity(0-1: isolated data point vs. accelerating confirmed pattern) + 30×durability(0-1: temporary blip vs. lasting structural change)
```

**70-100** Structural — warrants explicit strategic planning response. **40-69** Emerging — monitor closely, prepare contingency, don't over-react. **<40** Noise — log only.

## If information is missing

Ask for the signal description, evidence of how many sources/companies/segments show it (breadth), how fast/recently it developed (velocity), and why it is or isn't likely lasting (durability).

## Output

Category, the three sub-scores with brief rationale, the materiality score and band, and a response recommendation matched to the band.

## Common failure patterns to avoid

- Reacting to every market news item with the same urgency.
- Scoring durability from how dramatic a signal sounds instead of actual evidence of a lasting pattern.
- Missing breadth by evaluating only against your own company's experience instead of checking if it's category-wide.

## Output format

When the caller needs machine-readable output (an API, a pipeline, or an explicit request for JSON), return a single JSON object that validates against [`schema.json`](schema.json) in this skill's folder: every field it lists, no extra fields. Otherwise, present the same fields as a readable summary.

With little data (roughly fewer than 15 deals, accounts, interviews, or periods behind a rate, lift, or benchmark), still compute the result but label it provisional with the sample size, e.g. "provisional (n=8)".

## Reference

Full methodology and worked example: [`b2b-agent-skills-gtm/skills/market-shift-monitor/README.md`](../../../b2b-agent-skills-gtm/skills/market-shift-monitor/README.md)
