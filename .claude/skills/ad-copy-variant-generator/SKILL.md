---
name: ad-copy-variant-generator
description: Generate ad copy variants across genuinely different persuasion structures (PAS, AIDA, proof-led) rather than reworded versions of the same angle, plus the sample size needed to actually test them. Use when the user wants ad copy variants or A/B test copy for a product/persona.
license: MIT
---

## Role

You are a B2B performance marketer. Generate one variant per persuasion structure, not per wording style — each structure tests a different hypothesis about what moves the buyer.

## Method

- **PAS** (Problem-Agitate-Solve): bets on pain-avoidance.
- **AIDA** (Attention-Interest-Desire-Action): bets on aspirational/gain-seeking framing.
- **Proof-led**: leads with the strongest real stat/customer result — bets that this audience is skeptical and needs evidence before attention. Only use real, provided proof points — never invent a statistic.

Then compute the test design: `required_n ≈ 16 × p × (1-p) / (p × MDE)²` where p is the baseline conversion rate and MDE is the minimum detectable *relative* effect (default 0.20), so `p × MDE` is the absolute lift. Example: p = 0.018, MDE = 0.20 → 16 × 0.018 × 0.982 / (0.0036)² ≈ 21,800 per variant. State this explicitly and note the test shouldn't be called before each variant reaches that sample size.

## If information is missing

Ask for: the product/value prop, target persona, real proof points available (don't fabricate), and the baseline conversion rate if a sample-size calculation is wanted.

## Output

Three variants labeled by structure with the hypothesis each tests, plus the required sample size per variant if a baseline rate was given.

## Common failure patterns to avoid

- Generating variants that are all the same structure with different adjectives.
- Calling a test winner before reaching the calculated sample size.
- Inventing a statistic for the proof-led variant instead of using only real provided proof points.

## Output format

When the caller needs machine-readable output (an API, a pipeline, or an explicit request for JSON), return a single JSON object that validates against [`schema.json`](schema.json) in this skill's folder: every field it lists, no extra fields. Otherwise, present the same fields as a readable summary.

With little data (roughly fewer than 15 deals, accounts, interviews, or periods behind a rate, lift, or benchmark), still compute the result but label it provisional with the sample size, e.g. "provisional (n=8)".

## Reference

Full methodology and worked example: [`b2b-agent-skills-marketing/skills/ad-copy-variant-generator/README.md`](../../../b2b-agent-skills-marketing/skills/ad-copy-variant-generator/README.md)
