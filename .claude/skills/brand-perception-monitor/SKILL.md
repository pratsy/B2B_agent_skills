---
name: brand-perception-monitor
description: Score brand health across the four sequential brand-funnel stages (awareness, favorability, consideration, differentiation) from trend data, finding the actual bottleneck stage rather than reporting raw mention volume as brand health. Use when the user shares brand/market signal data and asks about brand health or perception.
license: MIT
---

## Role

You are a brand strategist. The brand funnel is sequential — a buyer can't be favorable toward a brand they're not aware of, can't consider one they're not favorable toward. Score each stage against its own trend, not an absolute scale.

## Method

Score each stage 1-5 by trend vs. the prior period (not an absolute benchmark): **Awareness** (branded search trend, share of voice), **Favorability** (mention sentiment, review-site rating trend), **Consideration** (% of closed-lost deals where you made the final shortlist), **Differentiation** (% of win/loss interviewees who could name your differentiator unprompted).

`1` = declining, `3` = flat, `5` = improving. Find the **lowest-scoring upstream stage** as the bottleneck — a downstream fix (e.g. messaging) won't help if an upstream stage (e.g. awareness) is the actual constraint, and vice versa.

## If information is missing

Ask for trend data (current vs. prior period) for each stage's proxy signal — at minimum branded search/SOV, review ratings or sentiment, and shortlist-inclusion rate if available.

## Output

Each stage's score and trend evidence, the identified bottleneck stage, and why fixing a different stage wouldn't address the real constraint.

## Common failure patterns to avoid

- Reporting raw mention volume as the headline brand metric — it only measures awareness.
- Scoring from one data point instead of trend vs. prior period.
- Skipping the differentiation stage because it requires win/loss data instead of a dashboard pull — it's often the most diagnostic.

## Output format

When the caller needs machine-readable output (an API, a pipeline, or an explicit request for JSON), return a single JSON object that validates against [`schema.json`](schema.json) in this skill's folder: every field it lists, no extra fields. Otherwise, present the same fields as a readable summary.

With little data (roughly fewer than 15 deals, accounts, interviews, or periods behind a rate, lift, or benchmark), still compute the result but label it provisional with the sample size, e.g. "provisional (n=8)".

## Reference

Full methodology and worked example: [`b2b-agent-skills-marketing/skills/brand-perception-monitor/README.md`](../../../b2b-agent-skills-marketing/skills/brand-perception-monitor/README.md)
