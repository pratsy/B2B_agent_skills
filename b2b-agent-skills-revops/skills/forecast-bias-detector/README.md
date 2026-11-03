# Forecast Bias Detector

Detect systematic forecast bias per rep or segment by comparing forecast calls to actual outcomes over multiple periods — classifying the bias as sandbagging (consistently under-forecasting) or sniping (consistently over-forecasting late deals) — instead of judging forecast accuracy from a single period's miss.

## When to use this

- One rep's forecast is consistently wrong in the same direction, quarter after quarter, and you want to quantify the pattern instead of relitigating it each cycle.
- Aggregate forecast accuracy looks fine but you suspect it's masking offsetting biases (some reps sandbagging, others sniping) that cancel out at the team level.
- Setting forecast trust/scrutiny levels per rep for the [`forecast-confidence-model`](../../../b2b-agent-skills-sales/skills/forecast-confidence-model/README.md) rep-calibration input.

## Methodology

Bias is a *pattern across periods*, not a single miss — a rep who's wrong once in either direction has noisy forecasting, not necessarily biased forecasting. Compute bias direction and consistency over a trailing window (recommend 4+ quarters or 8+ months of data before drawing conclusions).

**Two distinct bias types**, requiring opposite corrections:

- **Sandbagging**: rep's Commit calls consistently under-state what actually closes (actual closed-won routinely exceeds the Commit number). Looks safe but hides real capacity/hiring-plan signal from leadership.
- **Sniping** (over-forecasting): rep's Commit calls consistently include deals that don't close, often deals pulled in from next period. Creates the volatility and last-minute misses leadership actually fears.

## Scoring model

```
Bias Ratio (per period) = actual_closed_won_in_commit / self_declared_commit_amount

Trailing Bias Score = mean(Bias Ratio across trailing N periods)

Bias Ratio consistently > 1.15 across periods → Sandbagging (rep under-calls by >15% on average)
Bias Ratio consistently < 0.85 across periods → Sniping (rep over-calls by >15% on average)
Bias Ratio fluctuating between periods with no consistent direction → Noisy, not biased (do not apply a correction factor)

Consistency Check: require at least 3 of the last 4 periods in the same direction before classifying as a
true bias pattern - a single outlier period should not trigger a bias label.
```

## Inputs

| Field | Type | Example |
|---|---|---|
| `rep_id` | string | |
| `period_history` | list[{period, self_declared_commit, actual_closed_won_from_commit_deals}] | trailing 4+ periods |

## Worked example

Rep A, trailing 4 quarters: Bias Ratios of 1.22, 1.31, 1.18, 1.09 — all above 1.15 except the most recent (1.09, still above 1.0). 3 of 4 periods clearly above 1.15 threshold.

Trailing Bias Score = mean(1.22, 1.31, 1.18, 1.09) = **1.20 → Sandbagging, confirmed pattern (3 of 4 periods qualify).**

Interpretation: this rep's Commit number should be adjusted upward by roughly 20% for planning purposes, and — more importantly — leadership is likely under-resourcing based on this rep's understated forecasts. The fix is coaching the rep on forecast calibration, not just mentally discounting (or in this case, inflating) their number every quarter without addressing the root pattern.

## Common failure patterns

- Labeling a rep "biased" from a single bad quarter — bias requires a consistent multi-period pattern; a single miss is noise until proven otherwise.
- Treating sandbagging as a harmless, safe habit — it distorts capacity planning and hiring decisions just as much as over-forecasting does, in the opposite direction.
- Computing bias only at the team level, which can hide offsetting individual biases (one sandbagger and one sniper averaging out to a falsely "accurate" team forecast).
- Applying a flat correction factor without first checking consistency — smoothing over what is actually noisy, not biased, forecasting produces false precision.

## Output schema

```json
{
  "rep_id": "rep_882",
  "period_bias_ratios": [1.22, 1.31, 1.18, 1.09],
  "trailing_bias_score": 1.20,
  "consistency": "3 of 4 periods above threshold",
  "classification": "sandbagging",
  "recommended_correction_factor": 1.20,
  "coaching_focus": "forecast calibration - rep is under-calling Commit by an average of 20%"
}
```

## Recommended prompt

> You are a RevOps forecast analyst. Given a rep's trailing period history of self-declared Commit amounts and actual closed-won from those Commit deals, compute Bias Ratio per period = actual / self_declared. Compute the trailing mean. Classify as sandbagging if the ratio is consistently above 1.15 in at least 3 of the last 4 periods, sniping if consistently below 0.85 in at least 3 of 4, or "noisy, not biased" if there's no consistent direction. Recommend a correction factor only for a confirmed pattern, not for noisy data. Return JSON matching the schema above.

## Grounded in

Forecast calibration analysis (the same underlying logic as calibration-curve/Brier-score evaluation in forecasting theory, applied to sales Commit-vs-actual data), requiring multi-period consistency before labeling a bias pattern so single-period misses aren't mistaken for systematic rep behavior.

See [sources-and-frameworks.md](../../sources-and-frameworks.md) for the pack's general reference list.
