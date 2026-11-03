# Lead Prioritization Agent

Score leads on independent fit and intent axes (not one blended score) so reps can distinguish "great-fit, not ready yet" from "ready now, mediocre fit" — the two most commonly confused lead types in flat lead-scoring models.

## When to use this

- A single blended lead score sends reps chasing high-scoring leads that are actually just high-fit-but-cold, wasting outreach on people not currently in a buying window.
- Reps and marketing disagree on what "good lead" means because the score doesn't distinguish why a lead scored high.
- You need to route leads differently by type (fast-follow vs. nurture vs. deprioritize) rather than a single ranked list.

## Methodology

Two independent axes, each 0–100, deliberately kept separate rather than blended into one number, because the right action differs completely depending on which axis is driving the score:

- **Fit**: how well the lead's firmographic/role profile matches the ICP (see [`icp-refinement-agent`](../../../b2b-agent-skills-marketing/skills/icp-refinement-agent/README.md) in the marketing pack for how to derive fit weights from evidence, not assumption).
- **Intent**: how much active buying behavior this specific lead is showing right now (recency/frequency/depth of engagement, similar to the RFM approach in [`audience-segmentation-optimizer`](../../../b2b-agent-skills-marketing/skills/audience-segmentation-optimizer/README.md), plus any explicit high-intent action like a demo/pricing request).

## Scoring model

```
Fit Score (0-100) = weighted sum of ICP-attribute matches (industry, size, role seniority, tech stack), using lift-derived weights where available

Intent Score (0-100) =
    40 x recency_points (40 if action in last 3d, 25 if last 14d, 10 if last 30d, 0 otherwise)
  + 35 x explicit_high_intent_action (35 if requested demo/pricing/trial, 0 otherwise)
  + 25 x engagement_depth (capped 25, per-touch weight similar to RFM depth scoring)
```

### 2x2 routing (not a single rank)

| | High Intent (≥60) | Low Intent (<60) |
|---|---|---|
| **High Fit (≥60)** | **Route to rep now** — best-fit, active buying signal | **Marketing nurture, fit-matched content** — good account, not yet active; don't burn rep time |
| **Low Fit (<60)** | **Light-touch rep follow-up** — active signal but fit is uncertain; verify before investing heavily | **Deprioritize / suppress** — low value even if this lead is easy to reach |

## Inputs

| Field | Type | Example |
|---|---|---|
| `lead_id` | string | |
| `icp_attributes` | object | industry, size, role, tech stack |
| `icp_weights` | object | attribute weights, ideally lift-derived |
| `engagement_events` | list[{date, type, weight}] | |
| `explicit_high_intent_action` | bool | requested demo/pricing/trial |

## Worked example

Lead: Director of RevOps at a 400-person FinTech company. Fit Score (weighted against ICP attributes): 82. Engagement: visited pricing page 2 days ago, requested a demo.

```
Intent Score = 40(recency=3d→40pts scaled) + 35(explicit action=true) + 25(depth, pricing page=high) 
             ≈ 88
```
Fit 82, Intent 88 → both ≥60 → **Route to rep now.** Contrast with a lead scoring Fit 85, Intent 15 (great firmographic match, zero recent engagement) — same fit tier, completely different action: nurture, not a rep call, because there's no current buying signal to act on.

## Common failure patterns

- Blending fit and intent into one number, which makes a high-fit-zero-intent lead and a low-fit-high-intent lead look identical on a sorted list despite needing opposite treatment.
- Scoring intent from marketing-email engagement alone (opens/clicks) without weighting explicit high-intent actions (demo/pricing requests) much more heavily — these are qualitatively different signals.
- Using static ICP weights that were never validated against actual win data — see icp-refinement-agent for deriving weights from evidence instead of assumption.
- Not re-scoring intent as it decays — a lead that was High Intent two weeks ago with no follow-up engagement should drop out of the "route to rep now" quadrant, not stay there indefinitely.

## Output schema

```json
{
  "lead_id": "lead_9182",
  "fit_score": 82,
  "intent_score": 88,
  "quadrant": "high fit / high intent",
  "routing": "route to rep now",
  "rationale": "strong ICP match and an explicit demo request within the last 3 days"
}
```

## Recommended prompt

> You are a lead scoring analyst. Compute Fit Score (0-100, weighted match against the ICP attributes/weights given) and Intent Score (0-100 = recency points + 35 if an explicit high-intent action occurred + engagement depth, capped) independently — do not blend them into one number. Assign the lead to one of four quadrants (high fit/high intent, high fit/low intent, low fit/high intent, low fit/low intent) using a 60/60 threshold, and state the routing action for that quadrant. Return JSON matching the schema above.

## Grounded in

A fit/intent two-axis lead scoring model, standard in B2B predictive lead scoring, kept deliberately unblended so routing logic can differ by quadrant instead of collapsing distinct lead types into one rank-ordered list.

See [sources-and-frameworks.md](../../sources-and-frameworks.md) for the pack's general reference list.
