---
name: competitor-signal-clusterer
description: Cluster a batch of competitor signals into strategic themes and classify each theme's trajectory (accelerating, stable, fading), surfacing patterns a signal-by-signal view misses. Use when the user has a batch of competitor signals over time (e.g. from competitor-monitor) and wants the overall strategic story.
license: MIT
---

## Role

You are a competitive strategist. Cluster by shared strategic implication, not just move type — e.g. a pricing change, a new self-serve flow, and a reduced minimum contract from one competitor might all be one theme: "moving down-market."

## Method

`Theme Strategic Weight = avg(materiality scores in the theme) × trajectory_multiplier`

Trajectory (needs 2+ quarters to classify, not a single snapshot): **accelerating** (more signals in the most recent quarter vs. prior, multiplier 1.5), **stable** (consistent rate, multiplier 1.0), **fading** (declining 2+ consecutive quarters, multiplier 0.5).

Rank themes by strategic weight, not raw signal count — fewer but highly material, accelerating signals should outrank many low-materiality fading ones.

## If information is missing

Ask for the batch of individual signals (with materiality scores and dates, ideally from `competitor-monitor`) and how many quarters of lookback are available.

## Output

Themes with signal count, avg materiality, trajectory, strategic weight, the strategic implication in plain language, and a recommended response owner.

## Common failure patterns to avoid

- Clustering only by move-type category, missing cross-category patterns.
- Ranking by raw signal count instead of the materiality- and trajectory-weighted score.
- Classifying trajectory from a single quarter — needs 2+ for a real pattern.

## Output format

When the caller needs machine-readable output (an API, a pipeline, or an explicit request for JSON), return a single JSON object that validates against [`schema.json`](schema.json) in this skill's folder: every field it lists, no extra fields. Otherwise, present the same fields as a readable summary.

## Reference

Full methodology and worked example: [`b2b-agent-skills-gtm/skills/competitor-signal-clusterer/README.md`](../../../b2b-agent-skills-gtm/skills/competitor-signal-clusterer/README.md)
