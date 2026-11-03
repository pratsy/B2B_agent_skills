# Win-Loss Theme Clusterer

Cluster win/loss interview data into frequency-weighted themes and correlate each theme with actual win rate impact — using the same evidence-frequency discipline as [`persona-insight-extractor`](../../../b2b-agent-skills-marketing/skills/persona-insight-extractor/README.md), applied to why deals are won or lost rather than to persona attributes.

## When to use this

- Win/loss interviews have been conducted but the findings live in scattered notes with no structured theme extraction.
- Leadership wants to know the top 3 reasons deals are lost, and "gut sense from recent deals" isn't a reliable answer.
- You're deciding where to invest (product, pricing, competitive positioning) and need evidence of which factor actually moves win rate, not just which is mentioned most.

## Methodology

Two things are tracked per theme, because the most *frequently mentioned* reason is not always the most *decisive* one:

- **Frequency**: % of win/loss interviews where the theme appears at all.
- **Decisiveness**: of the interviews where the theme appears, what % cite it as the *primary* (not secondary) reason for the outcome.

A theme can be frequently mentioned but rarely decisive (e.g., "pricing came up" in 60% of losses, but was the stated primary reason in only 10% of those) — that's a theme to note but not over-invest in fixing. A theme with lower frequency but high decisiveness is often the higher-priority finding.

## Scoring model

```
Theme Impact Score = Frequency (0-1) x Decisiveness (0-1) x Win_Rate_Delta

Win_Rate_Delta = win_rate_when_theme_absent - win_rate_when_theme_present (for loss-side themes;
                 invert for win-side themes: win_rate_when_theme_present - win_rate_when_theme_absent)

This requires the theme to be tagged not just on loss interviews but checked against a comparison set
of wins (and vice versa) - a theme that appears equally often in wins and losses has near-zero
win rate delta and is not actually predictive, regardless of how often it's mentioned.
```

## Extraction process

1. Tag every interview passage with a candidate theme (open coding, similar to the JTBD extraction process).
2. Cluster similar passages across interviews into named themes.
3. For each theme, compute frequency and decisiveness *within* the set where it appears, and win-rate delta *across* the full win/loss comparison set.
4. Rank themes by Theme Impact Score, not raw mention count.

## Inputs

| Field | Type | Example |
|---|---|---|
| `win_loss_interviews` | list[{deal_id, outcome, transcript_or_notes}] | both wins and losses, required for delta calculation |
| `candidate_themes` | list[string] (optional) | seed themes if a prior round already identified some |

## Worked example

40 win/loss interviews (22 losses, 18 wins). Theme "implementation complexity concern": appears in 60% of losses (13 of 22) but only cited as the *primary* stated reason in 3 of those 13 (23% decisiveness). Also appears in 15% of wins (where it was raised and resolved during the sales cycle).

```
Win rate when theme absent (never raised) ≈ higher baseline
Win rate when theme present ≈ lower
Win_Rate_Delta ≈ 0.20 (a 20-point win rate gap between deals where this concern was raised vs. not)
Theme Impact Score = 0.60 (frequency) x 0.23 (decisiveness) x 0.20 (delta) ≈ 0.028
```

Compare to theme "pricing objection": appears in 55% of losses, decisiveness 65% (frequently the stated primary reason), win-rate delta 0.35.
```
Theme Impact Score = 0.55 x 0.65 x 0.35 ≈ 0.125
```

Pricing objection ranks far higher despite similar frequency to implementation complexity, because it's both more decisive and more strongly correlated with the loss outcome. The recommended priority is addressing the pricing/value conversation (see [`pricing-justification-builder`](../../../b2b-agent-skills-sales/skills/pricing-justification-builder/README.md)), not implementation complexity, even though both "came up" at similar rates.

## Common failure patterns

- Ranking themes by raw mention frequency alone, which over-weights themes that are commonly mentioned but rarely decisive.
- Computing frequency only from loss interviews without a win-side comparison, which makes it impossible to tell whether a theme is actually loss-predictive or just a generally common topic.
- Treating every interviewee's stated reason at face value without checking for a secondary/deflecting reason pattern (buyers sometimes cite price as an easier reason to give than a harder truth like weak internal champion support) — cross-reference against other data (e.g., stakeholder map, MEDDPICC scores) where available.
- Re-running this analysis infrequently — themes shift as the competitive landscape and product change; a theme that was decisive two years ago may no longer be.

## Output schema

```json
{
  "themes_ranked": [
    {"theme": "pricing objection", "frequency": 0.55, "decisiveness": 0.65, "win_rate_delta": 0.35, "impact_score": 0.125, "side": "loss"},
    {"theme": "implementation complexity concern", "frequency": 0.60, "decisiveness": 0.23, "win_rate_delta": 0.20, "impact_score": 0.028, "side": "loss"}
  ],
  "top_priority_theme": "pricing objection",
  "sample_size": {"wins": 18, "losses": 22}
}
```

## Recommended prompt

> You are a win/loss analyst. Cluster the interview transcripts/notes below into named themes. For each theme, compute frequency (% of interviews where it appears), decisiveness (% of those appearances where it was cited as the primary reason, not secondary), and win_rate_delta (the win rate gap between deals where the theme was present vs. absent). Compute Theme Impact Score = frequency x decisiveness x win_rate_delta. Rank themes by this score, not raw mention count, and identify the top-priority theme. Return JSON matching the schema above.

## Grounded in

Win/loss analysis practice in competitive and product strategy, combined with a frequency/decisiveness/win-rate-delta scoring method so themes are prioritized by actual predictive impact rather than how often they happen to be mentioned.

See [sources-and-frameworks.md](../../sources-and-frameworks.md) for the pack's general reference list.
