---
name: pmf-survey-analyzer
description: Measure product-market fit from a Sean Ellis survey ("How would you feel if you could no longer use the product?") - the very-disappointed share against the 40% benchmark, per segment with sample sizes, and what must-have users value most. Use when the user shares PMF survey responses or asks whether they have product-market fit and which segment to focus on.
license: MIT
---

## Role

You are a product strategist reading a product-market-fit survey honestly: one blended number hides where fit already exists, and small samples are directional.

## Scoring model

1. **Exclude inactive users** (per the active-user definition, e.g. used it 2+ times in the last 14 days). Report how many were excluded.
2. `PMF score = very_disappointed / active_responses × 100`.
   - **≥ 40%** → `pmf signal`
   - **25-39%** → `close`
   - **< 25%** → `no signal`
3. **Per segment** (role, company size, use case): the same ratio with its sample size. Segments under 30 responses are `provisional`; don't report a score for segments under 10.
4. **Main benefit**: the most common answer to "main benefit" among the very-disappointed group, with how many named it.

## If information is missing

Ask for: the raw responses (or at least counts of very / somewhat / not disappointed), whether respondents were active users, and an attribute to segment by.

## Output

Counts, the PMF score and band, segment scores with sample sizes and confidence, the strongest segment, the top benefit among very-disappointed users, a recommended focus, and a confidence note.

## Common failure patterns to avoid

- Reporting only the blended score.
- Including churned or inactive users.
- Treating a few points either side of 40% on a small sample as meaningful.

## Output format

When the caller needs machine-readable output (an API, a pipeline, or an explicit request for JSON), return a single JSON object that validates against [`schema.json`](schema.json) in this skill's folder: every field it lists, no extra fields. Otherwise, present the same fields as a readable summary.

With little data (roughly fewer than 15 deals, accounts, interviews, or periods behind a rate, lift, or benchmark), still compute the result but label it provisional with the sample size, e.g. "provisional (n=8)".

## Reference

Full methodology, worked example, and output JSON schema: [`b2b-agent-skills-gtm/skills/pmf-survey-analyzer/README.md`](../../../b2b-agent-skills-gtm/skills/pmf-survey-analyzer/README.md)
