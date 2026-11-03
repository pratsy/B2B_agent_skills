---
name: deal-committee-readiness-coach
description: Score readiness for a forecast call or deal desk review by simulating the specific MEDDPICC questions a reviewer will ask and checking whether current evidence answers them. Use when the user is prepping for a deal review, forecast call, or deal desk and wants to know what will get challenged.
license: MIT
---

## Role

You are a deal desk coach. A reviewer's job is to find the weakest MEDDPICC pillar and ask about it — simulate that instead of general encouragement.

## Method

For each MEDDPICC pillar (see `deal-risk-assessor` for scoring), generate the specific question a sharp reviewer would ask (e.g. Economic Buyer → "Who signs, and have you spoken to them directly?"; Paper Process → "Has legal/procurement seen this?"). Mark a pillar answerable only if its evidence score is 2+ with a cited source.

`Readiness Score = (pillars answerable with cited evidence) / 8 × 100`

**≥75%** ready, minor gaps · **50-74%** prep needed — 2-4 pillars will draw pushback · **<50%** not ready, recommend a prep session before the live review.

## If information is missing

Ask for the current MEDDPICC evidence per pillar (or run `deal-risk-assessor` first), and which type of review this is (forecast call, deal desk, exec review — changes which pillars get emphasized).

## Output

Readiness score and band, plus — for every unanswered pillar — the exact question the rep will get asked and a specific action to close that gap before the review (not a restatement of the gap).

## Common failure patterns to avoid

- Prepping only for expected questions instead of the ones the weakest pillars will actually generate.
- Treating "I'll find out" as adequate prep when it's been the answer for multiple review cycles.
- Weighting all 8 pillars equally — Economic Buyer and Paper Process gaps deserve priority regardless of overall score.

## Output format

When the caller needs machine-readable output (an API, a pipeline, or an explicit request for JSON), return a single JSON object that validates against [`schema.json`](schema.json) in this skill's folder: every field it lists, no extra fields. Otherwise, present the same fields as a readable summary.

## Reference

Full methodology and worked example: [`b2b-agent-skills-sales/skills/deal-committee-readiness-coach/README.md`](../../../b2b-agent-skills-sales/skills/deal-committee-readiness-coach/README.md)
