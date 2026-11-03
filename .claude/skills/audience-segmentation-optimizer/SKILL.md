---
name: audience-segmentation-optimizer
description: Score and tier a B2B account/audience list using firmographic fit, technographic fit, engagement intensity (RFM), and intent signal — the four-part model ABM platforms use. Use when the user shares an account or contact list and an ICP definition and asks for segmentation, tiering, or targeting priority.
license: MIT
---

## Role

You are a RevOps/marketing analyst applying the standard ABM segmentation stack: firmographic + technographic + engagement + intent.

## Scoring model

For each account, compute (0-100 each):

- **Firmographic Fit**: 100 if industry, size band, and geography all match the ICP; -30 per partial mismatch, -50 per hard mismatch.
- **Technographic Fit**: 100 if a required/compatible tool is present with no blocking competitor tool; 50 if neutral; 0 if a locked-in competitor tool is present.
- **Engagement Intensity** (RFM, trailing 90 days): recency points (40 if a touch in last 7d, 25 if last 30d, 10 if last 90d, 0 otherwise) + frequency points (touches×3, capped 30) + depth points (pricing/demo=10, product page=6, blog=2, capped 30).
- **Intent Signal**: 100 for a sustained 2+ week topic surge, 60 for a single-week spike, 20 for baseline. If no intent data exists, mark `intent_data_available: false` and reweight the remaining components proportionally — do not score missing data as 0.

Composite: `0.35*firmographic + 0.25*technographic + 0.25*engagement + 0.15*intent` (reweighted if intent is unavailable).

Tiers: **80-100** Tier 1 (named-account ABM) · **60-79** Tier 2 (scaled ABM) · **40-59** Tier 3 (programmatic) · **<40** deprioritize.

## If information is missing

Ask for the ICP definition (industries, size band, geography, required/competitor tech) and whatever account data is available — firmographics, tech stack signals, recent touches, intent data if any.

## Output

Per account: the four component scores, composite score, tier, and recommended motion.

## Common failure patterns to avoid

- Scoring missing intent data as 0 instead of flagging it and reweighting.
- Letting firmographic fit alone put an account in Tier 1 with zero engagement.
- Not accounting for engagement decay — re-score on a rolling basis, not once.

## Output format

When the caller needs machine-readable output (an API, a pipeline, or an explicit request for JSON), return a single JSON object that validates against [`schema.json`](schema.json) in this skill's folder: every field it lists, no extra fields. Otherwise, present the same fields as a readable summary.

With little data (roughly fewer than 15 deals, accounts, interviews, or periods behind a rate, lift, or benchmark), still compute the result but label it provisional with the sample size, e.g. "provisional (n=8)".

## Reference

Full methodology and worked example: [`b2b-agent-skills-marketing/skills/audience-segmentation-optimizer/README.md`](../../../b2b-agent-skills-marketing/skills/audience-segmentation-optimizer/README.md)
