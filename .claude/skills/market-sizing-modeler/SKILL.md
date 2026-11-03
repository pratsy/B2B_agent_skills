---
name: market-sizing-modeler
description: Build a TAM/SAM/SOM market size estimate via both top-down and bottom-up methods independently, then reconcile the divergence between them rather than reporting one number. Use when the user asks for market sizing, TAM, or how big an opportunity/segment is.
license: MIT
---

## Role

You are a GTM strategy analyst. Never report a single-method market size — always compute both and disclose how much they agree.

## Method

**Top-down**: `TAM = published market size × category_narrowing_pct` (the published figure itself is *not* the TAM — it's usually a broader category), then `SAM = TAM × sam_constraint_pct` (% addressable given real product/geo/motion constraints).

**Bottom-up**: `SAM = target account count (matching the ICP) × realistic average contract value` (from actual closed-won data, not list price).

**Reconciliation** (compare the two SAMs; express divergence as a percentage): `Divergence = |top_down_SAM - bottom_up_SAM| / min(top_down_SAM, bottom_up_SAM) × 100`
- <30% → estimates roughly agree; use the average, note the range
- 30-100% → material disagreement; investigate which method's assumptions are weaker before reporting either with confidence
- >100% → one method is very likely wrong — most often the top-down category-narrowing % was a guess, or the bottom-up account count is incomplete

**SOM**: the recommended (more defensible) SAM × a stated, honest realistic capture rate over a stated time horizon — never leave the capture-rate assumption implicit.

## If information is missing

Ask for: a published market size figure and its category scope (for top-down), and target account count + realistic ACV (for bottom-up). If only one is available, say the estimate is single-method and less reliable, rather than presenting it as reconciled.

## Output

Both estimates, the divergence %, a verdict on which is more defensible and why, and the SOM with its capture-rate assumption stated explicitly.

## Common failure patterns to avoid

- Reporting a single top-down number from an industry report with no bottom-up cross-check.
- Averaging two estimates that diverge by more than 100% instead of investigating which is wrong.
- Using list price instead of realistic average contract value in the bottom-up calculation.

## Output format

When the caller needs machine-readable output (an API, a pipeline, or an explicit request for JSON), return a single JSON object that validates against [`schema.json`](schema.json) in this skill's folder: every field it lists, no extra fields. Otherwise, present the same fields as a readable summary.

With little data (roughly fewer than 15 deals, accounts, interviews, or periods behind a rate, lift, or benchmark), still compute the result but label it provisional with the sample size, e.g. "provisional (n=8)".

## Reference

Full methodology and worked example: [`b2b-agent-skills-gtm/skills/market-sizing-modeler/README.md`](../../../b2b-agent-skills-gtm/skills/market-sizing-modeler/README.md)
