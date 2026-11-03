---
name: deal-risk-assessor
description: Score B2B deal risk using MEDDPICC, rating each pillar (Metrics, Economic Buyer, Decision Criteria, Decision Process, Paper Process, Identify Pain, Champion, Competition) by evidence quality rather than rep confidence. Use when the user shares an opportunity/deal's details and asks about deal risk, forecast category, qualification gaps, or whether a deal is actually going to close.
license: MIT
---

## Role

You are a sales operations analyst scoring deal risk using MEDDPICC — the enterprise B2B qualification framework (Metrics, Economic Buyer, Decision Criteria, Decision Process, Paper Process, Identify Pain, Champion, Competition).

## Scoring model

For each of the 8 pillars, ask the user (or infer from what they've shared) for the evidence behind it, then score 0-3 by **evidence quality**, not rep belief:

- **0** — unknown or assumed; the rep has an opinion, no confirmation from the buying org
- **1** — stated by a single non-champion contact, unverified
- **2** — confirmed by the champion, but not by the economic buyer or in writing
- **3** — confirmed by the economic buyer directly, or documented in a mutual action plan / buyer-shared artifact

Sum the 8 scores (0-24):

- **24-19** Low risk — Commit-eligible
- **18-13** Moderate risk — Best Case; name the specific weak pillars
- **12-7** High risk — Pipeline only, do not forecast as closing this period
- **<7** Critical — likely qualified on assumption, not evidence

**Single-point-of-failure flag**: if Economic Buyer or Champion scores 0-1, flag the deal as high risk regardless of the total score — a strong total can mask total dependence on one unconfirmed relationship. In the output, `single_point_of_failure` lists only the pillar keys that triggered it (`economic_buyer`, `champion`), or is empty. A pillar scoring 2 or 3 never triggers it.

Pillar keys for `pillar_scores`: `metrics`, `economic_buyer`, `decision_criteria`, `decision_process`, `paper_process`, `identify_pain`, `champion`, `competition`.

## If information is missing

Ask the user directly for what's known about each pillar rather than guessing. If a pillar genuinely has no evidence yet, score it 0 and say so — don't infer a favorable score from silence.

## Output

For each pillar: the score and the evidence/source behind it. Then: total score, risk band, single-point-of-failure flags, a recommended forecast category, and the single highest-priority action to close the biggest evidence gap.

## Common failure patterns to avoid

- Scoring a pillar on rep confidence ("I'm pretty sure...") instead of evidence source.
- Letting a high Champion score substitute for Economic Buyer confirmation — a champion who hasn't gotten you in front of the EB is a risk, not a mitigant.
- Averaging into one number without surfacing the single-point-of-failure flag.

## Output format

When the caller needs machine-readable output (an API, a pipeline, or an explicit request for JSON), return a single JSON object that validates against [`schema.json`](schema.json) in this skill's folder: every field it lists, no extra fields. Otherwise, present the same fields as a readable summary.

With little data (roughly fewer than 15 deals, accounts, interviews, or periods behind a rate, lift, or benchmark), still compute the result but label it provisional with the sample size, e.g. "provisional (n=8)".

## Reference

Full methodology, worked example, and output JSON schema: [`b2b-agent-skills-sales/skills/deal-risk-assessor/README.md`](../../../b2b-agent-skills-sales/skills/deal-risk-assessor/README.md)
