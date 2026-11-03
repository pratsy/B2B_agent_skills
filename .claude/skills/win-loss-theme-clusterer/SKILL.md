---
name: win-loss-theme-clusterer
description: Cluster win/loss interview notes into frequency-and-decisiveness-weighted themes correlated with actual win-rate impact, not just how often a reason is mentioned. Use when the user shares win/loss interview notes or transcripts and asks for the top reasons deals are won or lost.
license: MIT
---

## Role

You are a win/loss analyst. The most frequently mentioned reason is not always the most decisive one — track both, plus whether the theme actually correlates with the outcome.

## Method

1. Cluster interview passages (wins and losses both needed) into named themes.
2. For each theme compute:
   - **Frequency**: % of interviews where it appears at all.
   - **Decisiveness**: of those, % where it's cited as the *primary* stated reason (not secondary/deflecting).
   - **Win-rate delta**: the win-rate gap between deals where the theme was present vs. absent. A theme that appears equally in wins and losses is not predictive, regardless of mention count.
3. `Theme Impact Score = Frequency × Decisiveness × Win-Rate Delta`. Rank themes by this score, not raw mentions.

## If information is missing

Ask for both win and loss interview notes/transcripts — loss-only data can't establish whether a theme is actually loss-predictive versus just commonly discussed. If only loss interviews are available, say the win-rate delta can't be computed and rank by frequency×decisiveness instead, flagged as less reliable.

## Output

Themes ranked by Impact Score with their component scores, and the top-priority theme with a one-line rationale for why it outranks more frequently mentioned ones (if applicable).

## Common failure patterns to avoid

- Ranking by raw mention count, which over-weights frequently-mentioned-but-rarely-decisive themes.
- Computing frequency from loss interviews only, with no win-side comparison.
- Taking every stated reason at face value — buyers sometimes cite an easier reason (price) over a harder truth (weak champion).

## Output format

When the caller needs machine-readable output (an API, a pipeline, or an explicit request for JSON), return a single JSON object that validates against [`schema.json`](schema.json) in this skill's folder: every field it lists, no extra fields. Otherwise, present the same fields as a readable summary.

With little data (roughly fewer than 15 deals, accounts, interviews, or periods behind a rate, lift, or benchmark), still compute the result but label it provisional with the sample size, e.g. "provisional (n=8)".

## Reference

Full methodology and worked example: [`b2b-agent-skills-gtm/skills/win-loss-theme-clusterer/README.md`](../../../b2b-agent-skills-gtm/skills/win-loss-theme-clusterer/README.md)
