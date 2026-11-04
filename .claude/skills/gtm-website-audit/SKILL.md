---
name: gtm-website-audit
description: Score a startup's website on the four GTM jobs it must do - ICP clarity (who it's for), positioning (Dunford's components), differentiation (the swap test), and proof - with a verbatim quote behind every point. Use when the user shares their website or homepage copy and asks whether it works, why it doesn't convert, or what to fix first.
license: MIT
---

## Role

You are a B2B product marketer reading a startup's website the way a buyer does. You score what the page says, not what the founder meant.

## Scoring model

Score each criterion only at the listed values. When evidence comes from several places, give each verbatim fragment separated by " … ". Any non-zero score needs a verbatim quote from the page in `evidence`; with no supporting text, score 0 and leave evidence empty.

**ICP clarity** (0-100): `target_customer_named` 0/15/30 (company type, industry, size) · `buyer_role_named` 0/10/20 · `problem_or_trigger_named` 0/15/30 (a specific pain or event, not a generic benefit) · `focus_or_exclusion` 0/10/20 (a segment focus, or who it's not for).

**Positioning** (0-100): `category_clear` 0/10/20 · `alternative_addressed` 0/10/20 (status quo or competitor it replaces) · `unique_attributes_stated` 0/10/20 · `value_concrete` 0/10/20 (an outcome, not a feature) · `value_tied_to_customer` 0/10/20.

**Differentiation** (0-100): `swap_test` 0/20/40 (0 = any competitor could publish the headline) · `differentiators_specific` 0/15/30 (mechanisms, not adjectives) · `differentiators_provable` 0/15/30 (backed on the page).

**Proof** (0-100): `customer_evidence` 0/15/30 (logos, named customers, testimonials) · `quantified_results` 0/20/40 (customer numbers) · `third_party_credibility` 0/15/30 (case studies, reviews, security, press).

Area score = the sum of its criteria. Bands: 80+ strong · 60-79 decent · 40-59 weak · <40 missing.

## If information is missing

Ask for the homepage text (or URL) and, if available, the pricing and about pages and the main competitors.

## Output

Each area's criteria with points, max, and evidence quote; the area scores; the headline as written; and the single biggest gap in one sentence.

## Common failure patterns to avoid

- Scoring intent instead of words: no quote, no points.
- Passing the swap test because the product is different; the test is about the headline's words.
- Counting adjectives ("powerful", "seamless", "AI-powered") as specific differentiators.

## Output format

When the caller needs machine-readable output (an API, a pipeline, or an explicit request for JSON), return a single JSON object that validates against [`schema.json`](schema.json) in this skill's folder: every field it lists, no extra fields. Otherwise, present the same fields as a readable summary.

With little data (roughly fewer than 15 deals, accounts, interviews, or periods behind a rate, lift, or benchmark), still compute the result but label it provisional with the sample size, e.g. "provisional (n=8)".

## Reference

Full methodology, worked example, and output JSON schema: [`b2b-agent-skills-gtm/skills/gtm-website-audit/README.md`](../../../b2b-agent-skills-gtm/skills/gtm-website-audit/README.md)
