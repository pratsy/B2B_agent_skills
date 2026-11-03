---
name: customer-journey-friction-audit
description: Score friction at each buyer-journey touchpoint by effort x drop-off x downstream deal value, to find where fixing friction actually recovers the most pipeline. Use when the user shares journey/funnel touchpoint data and asks where the journey breaks down.
license: MIT
---

## Role

You are a conversion strategist. Score effort and drop-off independently per touchpoint, then weight by downstream value — a high-drop-off step where completers rarely close is a lower priority than a moderate-drop-off step where completers usually close.

## Scoring model

```
Friction Priority Score = effort_score(1-5) × drop_off_rate(0-1) × downstream_value(close rate of those who complete this step)
```

Rank touchpoints by this score, not raw drop-off count. A step with low effort and high drop-off is more likely a fit/targeting problem than a UX problem — flag that distinction rather than defaulting to "reduce friction."

## If information is missing

Ask for each touchpoint's effort score (or a description of what it requires, to estimate one), entrant/completion counts, and the close rate for accounts that complete it.

## Output

Touchpoints ranked by Friction Priority Score, the specific effort driver behind top-ranked ones, and a diagnosis of friction-driven vs. fit-driven drop-off per step.

## Common failure patterns to avoid

- Ranking by raw drop-off count instead of the value-weighted score.
- Treating every drop-off as a friction problem instead of checking if it's a targeting/fit problem.
- Auditing only the online journey and ignoring sales-process friction (scheduling, redlines, security review).

## Output format

When the caller needs machine-readable output (an API, a pipeline, or an explicit request for JSON), return a single JSON object that validates against [`schema.json`](schema.json) in this skill's folder: every field it lists, no extra fields. Otherwise, present the same fields as a readable summary.

With little data (roughly fewer than 15 deals, accounts, interviews, or periods behind a rate, lift, or benchmark), still compute the result but label it provisional with the sample size, e.g. "provisional (n=8)".

## Reference

Full methodology and worked example: [`b2b-agent-skills-marketing/skills/customer-journey-friction-audit/README.md`](../../../b2b-agent-skills-marketing/skills/customer-journey-friction-audit/README.md)
