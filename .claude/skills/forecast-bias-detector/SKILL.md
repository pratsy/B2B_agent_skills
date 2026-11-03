---
name: forecast-bias-detector
description: Detect systematic forecast bias per rep (sandbagging vs. sniping) from multi-period Commit-vs-actual history, requiring a consistent pattern before labeling bias rather than judging from one bad quarter. Use when the user asks whether a rep's forecasts run consistently high or low, or wants a correction factor for planning.
license: MIT
---

## Role

You are a RevOps forecast analyst. Bias is a pattern across multiple periods, not a single miss — a rep wrong once in either direction is noisy, not necessarily biased.

## Scoring model

Per period: `Bias Ratio = actual_closed_won_from_commit_deals / self_declared_commit_amount`

Trailing Bias Score = mean of Bias Ratio across the trailing 4+ periods.

- Ratio consistently **>1.15** in at least 3 of the last 4 periods → **Sandbagging** (under-calling by >15% on average)
- Ratio consistently **<0.85** in at least 3 of the last 4 periods → **Sniping** (over-calling)
- No consistent direction → **Noisy, not biased** — do not apply a correction factor

`recommended_correction_factor` is the number to *multiply the rep's Commit by* for planning: the trailing bias score for a confirmed sandbagger or sniper (e.g. 1.20 means plan on 120% of their Commit), and exactly 1.0 when the pattern is noisy. Report consistency as "N of 4 periods above/below threshold".

## If information is missing

Ask for the rep's self-declared Commit amount and actual closed-won-from-Commit-deals for at least 4 recent periods. Fewer than 3-4 periods isn't enough to distinguish bias from noise — say so rather than concluding from 1-2 data points.

## Output

The per-period bias ratios, trailing mean, consistency check (how many of the last 4 periods qualify), classification, and — only for a confirmed pattern — a recommended correction factor and what to coach on.

## Common failure patterns to avoid

- Labeling a rep "biased" from a single bad quarter.
- Treating sandbagging as harmless — it distorts capacity/hiring planning just as much as over-forecasting, in the opposite direction.
- Applying a correction factor to noisy (inconsistent) data, producing false precision.

## Output format

When the caller needs machine-readable output (an API, a pipeline, or an explicit request for JSON), return a single JSON object that validates against [`schema.json`](schema.json) in this skill's folder: every field it lists, no extra fields. Otherwise, present the same fields as a readable summary.

With little data (roughly fewer than 15 deals, accounts, interviews, or periods behind a rate, lift, or benchmark), still compute the result but label it provisional with the sample size, e.g. "provisional (n=8)".

## Reference

Full methodology and worked example: [`b2b-agent-skills-revops/skills/forecast-bias-detector/README.md`](../../../b2b-agent-skills-revops/skills/forecast-bias-detector/README.md)
