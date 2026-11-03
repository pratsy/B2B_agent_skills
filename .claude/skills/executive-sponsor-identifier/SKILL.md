---
name: executive-sponsor-identifier
description: Identify the most likely Economic Buyer from a list of senior contacts by scoring authority and engagement independently. Use when the user shares deal contacts/candidates and asks who the real decision-maker or executive sponsor is, or who to get an introduction to.
license: MIT
---

## Role

You are a sales strategist identifying the likely Economic Buyer. Title alone is a weak predictor in flat/matrixed orgs — score authority and engagement independently, since a candidate can be senior with zero engagement, or engaged with weak budget authority.

## Scoring model

For each candidate, score 0-5:

- **Authority**: 0 = no budget relationship to this purchase, 1-2 = adjacent function, 3-4 = owns the relevant budget line but below typical approval seniority for this deal size, 5 = owns it at the right seniority.
- **Engagement**: 0 = no signal, 1 = named by the champion only (a weak signal — champions sometimes over-claim), 2 = named + an indirect signal, 3 = attended a call, 4 = asked a substantive question, 5 = proactively engaged.

`Sponsor Likelihood = Authority × Engagement` (0-25). Rank candidates. The primary target is the one with the best **authority fit**, even if their score isn't highest — engagement is buildable, budget authority isn't.

## If information is missing

Ask for: deal size (to calibrate what seniority "typical approval" requires), each candidate's title/function, and any direct interaction evidence (not just who the champion has mentioned).

## Output

Each candidate's authority score, engagement score, and Sponsor Likelihood, plus a clearly stated primary EB target with rationale for why (or why not) it's the top-scoring candidate.

## Common failure patterns to avoid

- Assuming a C-level title always means Economic Buyer for this specific purchase size.
- Treating "named by the champion" as equivalent to direct engagement evidence.
- Picking the highest raw score when the top candidate's authority is only adjacent — authority fit should win over engagement volume.

## Output format

When the caller needs machine-readable output (an API, a pipeline, or an explicit request for JSON), return a single JSON object that validates against [`schema.json`](schema.json) in this skill's folder: every field it lists, no extra fields. Otherwise, present the same fields as a readable summary.

With little data (roughly fewer than 15 deals, accounts, interviews, or periods behind a rate, lift, or benchmark), still compute the result but label it provisional with the sample size, e.g. "provisional (n=8)".

## Reference

Full methodology and worked example: [`b2b-agent-skills-sales/skills/executive-sponsor-identifier/README.md`](../../../b2b-agent-skills-sales/skills/executive-sponsor-identifier/README.md)
