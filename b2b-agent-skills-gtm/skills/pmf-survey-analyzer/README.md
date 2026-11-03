# PMF Survey Analyzer

Measure product-market fit with the Sean Ellis test: the share of active users who would be "very disappointed" if they could no longer use the product, against the 40% benchmark. Then find the segment where fit is strongest and what those users value most, instead of averaging everyone into one number.

## When to use this

- You've run (or are about to run) the "How would you feel if you could no longer use the product?" survey and need to read the results honestly.
- The founders disagree on whether you have product-market fit, and you want a number with a known benchmark rather than anecdotes.
- You need to decide which customer segment to focus on next, and want evidence of where the product is already a must-have.

## Methodology

The Sean Ellis test asks active users: *"How would you feel if you could no longer use [product]?"* with three answers: very disappointed, somewhat disappointed, not disappointed. Sean Ellis found that companies where at least 40% of users answer "very disappointed" tend to have the pull that makes growth sustainable; below 40%, growth usually stalls.

Two refinements make the result useful, not just a score (popularized by Superhuman's PMF engine):

1. **Segment before you conclude.** A 30% overall score can hide one segment at 55% (a must-have for them) and another at 10% (wrong fit). Compute the score per segment (role, company size, use case) and focus where it's highest.
2. **Learn from the "very disappointed" group.** Their answers to "What's the main benefit you get?" tell you what to protect and amplify. The "somewhat disappointed" users who value that same benefit are the ones most likely to convert to "very disappointed" if you fix what holds them back.

Only count **active users** (used the product recently, e.g. at least twice in the last two weeks). Churned or barely-onboarded users drag the score down for reasons the test isn't designed to measure.

## Scoring model

```
PMF score = very_disappointed / total_active_responses

>= 40%   PMF signal: strong pull; protect the core benefit, scale the segment
25-39%   Close: find the segment above 40% and narrow focus to it
< 25%    No PMF signal yet: revisit the problem, the segment, or the product

Per segment: the same ratio, reported only with its sample size.
n < 30 responses (overall or per segment) -> provisional; n < 10 -> don't report a segment score at all.
```

## Inputs

| Field | Type | Example |
|---|---|---|
| `responses` | list[{respondent_id, disappointment, segment, main_benefit, improvement, active}] | one row per survey response; `disappointment` is very / somewhat / not |
| `active_user_definition` | string | `"used the product 2+ times in the last 14 days"` |
| `segment_field` | string | which attribute to segment by, e.g. `"role"` or `"company_size"` |

## Worked example

52 responses, 4 excluded as inactive, leaving 48 active users: 18 very disappointed, 20 somewhat, 10 not.

```
PMF score = 18 / 48 = 37.5% -> close, below the 40% benchmark
```

By segment: RevOps leaders 12 of 20 very disappointed (60%, n=20, provisional); sales managers 4 of 18 (22%, n=18, provisional); founders 2 of 10 (20%, n=10, provisional).

Read: overall the product is just under the benchmark, but for RevOps leaders it is a must-have at 60%. The "very disappointed" users most often name **"forecast calls take half the time"** as the main benefit (11 of 18). Recommendation: narrow the ICP and messaging to RevOps leaders, protect the forecast-call workflow, and interview the somewhat-disappointed RevOps users who named the same benefit to find what's blocking them.

## Common failure patterns

- Reporting one blended score: the segment where you already have fit gets averaged away.
- Including inactive or churned users, which deflates the score for reasons outside the product's core value.
- Treating 37% on 15 responses as meaningfully different from 40%. Below ~30 responses the score is directional.
- Asking for feature requests from everyone equally, instead of weighting what the "very disappointed" group values.

## Output schema

```json
{
  "active_responses": 48,
  "excluded_inactive": 4,
  "very_disappointed": 18,
  "somewhat_disappointed": 20,
  "not_disappointed": 10,
  "pmf_score_pct": 37.5,
  "pmf_band": "close",
  "segments": [
    {"segment": "RevOps leader", "responses": 20, "very_disappointed": 12, "pmf_score_pct": 60, "confidence": "provisional"},
    {"segment": "Sales manager", "responses": 18, "very_disappointed": 4, "pmf_score_pct": 22.2, "confidence": "provisional"}
  ],
  "strongest_segment": "RevOps leader",
  "top_benefit_among_very_disappointed": "forecast calls take half the time",
  "recommended_focus": "narrow ICP and messaging to RevOps leaders; protect the forecast-call workflow",
  "confidence_note": "provisional (n=48 active responses; segments under 30)"
}
```

## Recommended prompt

> You are a product strategist analyzing a Sean Ellis product-market-fit survey. Exclude inactive users. Compute the PMF score (very disappointed / active responses) and compare it to the 40% benchmark: 40%+ PMF signal, 25-39% close, below 25% no signal. Compute the score per segment with sample sizes (provisional under 30, don't report segments under 10). Identify the main benefit named by the very-disappointed group and recommend where to focus. Return JSON matching the schema above.

## Grounded in

Sean Ellis's product-market-fit survey and 40% benchmark (developed from his work at Dropbox, LogMeIn, and Eventbrite, described in *Hacking Growth*, 2017), and the segmentation and benefit analysis popularized by Rahul Vohra's "How Superhuman built an engine to find product/market fit" (First Round Review, 2018).

See [sources-and-frameworks.md](../../sources-and-frameworks.md) for the pack's general reference list.
