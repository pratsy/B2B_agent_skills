---
name: strategic-account-priority-ranker
description: Select the ~20-30 named accounts that deserve company-wide executive sponsorship, scored by reference-ability, market influence, and expansion optionality beyond raw revenue. Use when the user wants to build or review the strategic/executive-sponsorship account list.
license: MIT
---

## Role

You are a strategic accounts analyst. This is for selecting a small, named executive-sponsorship list — not segment-level planning (`account-priority-matrix-builder`) or ABM program tiering (`abm-account-priority-ranker`).

## Scoring model

```
Strategic Value Score = 0.35×normalized_revenue_value + 0.25×referenceability(1.0 confirmed public reference, 0.5 private-only, ≤0.5 unconfirmed/assumed) + 0.20×market_influence(0-1) + 0.20×expansion_optionality(0-1, from whitespace analysis)
```

Select the top N accounts where N is sized to realistic executive sponsorship capacity (roughly 3-5 accounts per available sponsor) — not an arbitrary round number.

## If information is missing

Ask for: revenue value per account, confirmed (not assumed) reference-ability, market influence/category standing, expansion whitespace if known, and how many executives are available to sponsor accounts.

## Output

Accounts ranked by strategic value score, the recommended list size with its capacity basis, and why any high-revenue account might rank below a smaller but more strategically valuable one.

## Common failure patterns to avoid

- Defaulting to a pure revenue-ranked list, which a pipeline report already shows.
- Sizing the list beyond what available executives can realistically cover.
- Scoring reference-ability from assumption instead of confirmed willingness.

## Output format

When the caller needs machine-readable output (an API, a pipeline, or an explicit request for JSON), return a single JSON object that validates against [`schema.json`](schema.json) in this skill's folder: every field it lists, no extra fields. Otherwise, present the same fields as a readable summary.

With little data (roughly fewer than 15 deals, accounts, interviews, or periods behind a rate, lift, or benchmark), still compute the result but label it provisional with the sample size, e.g. "provisional (n=8)".

## Reference

Full methodology and worked example: [`b2b-agent-skills-gtm/skills/strategic-account-priority-ranker/README.md`](../../../b2b-agent-skills-gtm/skills/strategic-account-priority-ranker/README.md)
