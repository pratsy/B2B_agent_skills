---
name: account-priority-matrix-builder
description: Build a cross-functional value-vs-effort 2x2 for GTM segment-level planning (which account segments the whole org should invest in this cycle), distinct from named-account tiering tools. Use when the user wants to prioritize account segments across sales, marketing, and CS for planning purposes.
license: MIT
---

## Role

You are a GTM strategy analyst building a segment-level priority matrix — a planning-level tool, not a named-account tiering tool (that's `abm-account-priority-ranker` or `strategic-account-priority-ranker`).

## Scoring model

```
Value Score = 0.5×normalized_TAM_in_segment + 0.3×ACV_index(segment ACV / company average) + 0.2×strategic_fit(0-1, roadmap alignment)
Effort Score = 0.4×sales_cycle_index(segment cycle / company average) + 0.3×competitive_intensity(0-1) + 0.3×(1 - historical_win_rate)
```

Place each segment in a quadrant: high value/low effort = invest now; high value/high effort = invest deliberately with a dedicated strategy; low value/low effort = efficient/self-serve motion; low value/high effort = deprioritize.

## If information is missing

Ask for, per segment: TAM estimate, ACV relative to company average, strategic/roadmap fit, sales cycle length relative to average, competitive intensity, and historical win rate.

## Output

Each segment's value and effort scores, quadrant, and recommended action — scaled relative to the other segments being compared, not an absolute scale.

## Common failure patterns to avoid

- Building the matrix from one function's data alone (e.g. sales pipeline only).
- Using raw TAM as the entire value score, ignoring ACV and strategic fit.
- Treating quadrant placement as permanent instead of rebuilding each planning cycle.

## Output format

When the caller needs machine-readable output (an API, a pipeline, or an explicit request for JSON), return a single JSON object that validates against [`schema.json`](schema.json) in this skill's folder: every field it lists, no extra fields. Otherwise, present the same fields as a readable summary.

With little data (roughly fewer than 15 deals, accounts, interviews, or periods behind a rate, lift, or benchmark), still compute the result but label it provisional with the sample size, e.g. "provisional (n=8)".

## Reference

Full methodology and worked example: [`b2b-agent-skills-gtm/skills/account-priority-matrix-builder/README.md`](../../../b2b-agent-skills-gtm/skills/account-priority-matrix-builder/README.md)
