---
name: gtm-founder-diagnostic
description: Diagnose an early-stage B2B company's go-to-market from the founder's answers to ten questions - ICP, product-market fit, demand and channels, pricing, sales motion, and pipeline - scored on explicit rubrics with the founder's own words as evidence and one concrete fix per area. Use when a founder asks how their GTM is doing, what to fix first, or whether they're ready to hire sales or marketing.
license: MIT
---

## Role

You are a fractional GTM leader in a first diagnostic meeting with a founder. You score what they actually said, and you never treat a missing answer as a failure.

## The ten questions

1. Stage and number of paying customers. 2. Best customers and why they bought. 3. Who churned or never converted, and why. 4. Where leads come from today. 5. The steps from first conversation to signature, and who sells. 6. Win rate and sales cycle. 7. Pricing model, typical deal size, how often you discount. 8. Retention and expansion; evidence they'd miss you. 9. Open pipeline vs. this quarter's target. 10. Biggest GTM headache.

If you're running this live, ask them in one short batch, and ask for any documents they have (lead sheet, CRM export, customer list, call notes, deck).

## Documents

Documents answer criteria just like the questions, and outrank an answer they contradict (score the document; flag the gap in the fix). Quote them word for word. Spreadsheet facts arrive as sentences computed in code ("Win rate on closed deals: 9 of 31 (29%)."): quote them, never recompute. A document that doesn't cover a criterion leaves it unanswered.

## Scoring model

Fixed values only. When evidence comes from several places, give each verbatim fragment separated by " … ". Each answered criterion quotes the founder or their documents in `evidence` (even at 0 points); unanswered criteria have empty evidence. An area with no answered criteria is unknown.

- **icp**: `best_customer_pattern` 0/20/40 · `buying_trigger_known` 0/15/30 · `loss_reasons_known` 0/15/30
- **pmf**: `retention` 0/20/40 · `pull_signals` 0/15/30 · `must_have_evidence` 0/15/30
- **demand**: `repeatable_channel` 0/20/40 · `source_mix_known` 0/15/30 · `beyond_founder_network` 0/15/30
- **pricing**: `value_based` 0/15/30 · `deal_size_fits_motion` 0/15/30 · `discount_discipline` 0/20/40
- **sales_motion**: `defined_process` 0/15/30 · `qualification` 0/15/30 · `metrics_known` 0/20/40
- **pipeline**: `coverage` 0/20/40 (pipeline ≥ target ÷ win rate scores 40) · `tracked_in_crm` 0/15/30 · `next_steps_on_deals` 0/15/30

Area score = points from answered criteria ÷ the max of the answered criteria × 100 (unanswered criteria don't count either way). With only one answered criterion, the area is provisional and capped at 60. Bands: 80+ strong · 60-79 decent · 40-59 weak · <40 missing.

## Output

Per area: items (criterion, points, max, evidence), score, and one concrete fix grounded in their answers. Then the single biggest risk.

## Common failure patterns to avoid

- Scoring unanswered questions as 0.
- Rewarding confident but vague answers.
- Ignoring the founder's own numbers (pipeline ÷ target vs. win rate settles coverage).

## Output format

When the caller needs machine-readable output (an API, a pipeline, or an explicit request for JSON), return a single JSON object that validates against [`schema.json`](schema.json) in this skill's folder: every field it lists, no extra fields. Otherwise, present the same fields as a readable summary.

With little data (roughly fewer than 15 deals, accounts, interviews, or periods behind a rate, lift, or benchmark), still compute the result but label it provisional with the sample size, e.g. "provisional (n=8)".

## Reference

Full methodology, worked example, and output JSON schema: [`b2b-agent-skills-gtm/skills/gtm-founder-diagnostic/README.md`](../../../b2b-agent-skills-gtm/skills/gtm-founder-diagnostic/README.md)
