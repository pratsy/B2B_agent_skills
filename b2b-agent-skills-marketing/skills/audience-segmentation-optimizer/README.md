# Audience Segmentation Optimizer

Score and tier a B2B audience using the four-part model ABM platforms (6sense, Demandbase, Bombora) standardized: firmographic fit, technographic fit, engagement intensity, and intent strength. Output is a ranked account/contact list with a tier and a recommended motion per tier — not a narrative summary.

## When to use this

- You have more accounts in your addressable market than your team can cover with high-touch motion, and no defensible way to say who gets it.
- Campaign performance is reported by channel, not by segment, so you can't tell if a campaign underperformed because of the offer or because it hit the wrong audience.
- Marketing and sales disagree on which accounts are "good fit" because there's no shared, numeric definition of fit.

## Methodology

Four segmentation layers, each answering a different question:

| Layer | Question it answers | Typical signal source |
|---|---|---|
| **Firmographic** | Does this account structurally match the ICP? | industry (NAICS/SIC or vendor taxonomy), employee count band, revenue band, geography |
| **Technographic** | Do they already run tools that make this purchase logical? | stack detection (BuiltWith, HG Insights, Clearbit), integration compatibility, migration signals |
| **Engagement (RFM)** | Are they actively interacting with us? | recency (days since last touch), frequency (touches in trailing 90d), depth (content/page weight — pricing page > blog post) |
| **Intent** | Are they researching this problem right now, anywhere? | third-party topic surge data (Bombora, 6sense), first-party high-intent actions (pricing, comparison pages, docs) |

This is the same layering used by every modern ABM platform under the hood — the value of this skill is making the weighting and thresholds explicit and auditable instead of a black-box vendor score.

## Scoring model

```
Segment Fit Score (0-100) =
    0.35 × Firmographic Fit Score   (0-100)
  + 0.25 × Technographic Fit Score  (0-100)
  + 0.25 × Engagement Intensity Score (0-100)
  + 0.15 × Intent Signal Score      (0-100)
```

**Firmographic Fit Score** — 100 if industry, size band, and geography all match the documented ICP; subtract 30 for each dimension that's a partial match, 50 for each hard mismatch (e.g., below minimum employee count).

**Technographic Fit Score** — 100 if a required/compatible tool is detected and no blocking competitor tool is present; 50 if neutral (no signal either way); 0 if a locked-in competitor replacement would be required.

**Engagement Intensity Score (RFM, trailing 90 days)**:
```
Recency points   = 40 if touch in last 7d, 25 if last 30d, 10 if last 90d, 0 otherwise
Frequency points = min(30, touches_in_90d × 3)
Depth points     = min(30, sum of per-touch weight: pricing/demo=10, product page=6, blog/resource=2)
Engagement Intensity Score = Recency + Frequency + Depth   (capped at 100)
```

**Intent Signal Score** — 100 if the account shows a sustained topic surge (elevated research activity for 2+ consecutive weeks) on a category-relevant topic; 60 for a single-week spike; 20 for baseline/no elevated signal; 0 if no intent data is available for the account (do not treat missing data as zero-interest — flag it as "unscored" instead of scoring it down).

### Tiers and recommended motion

| Score | Tier | Motion |
|---|---|---|
| 80–100 | Tier 1 | Named-account ABM: AE-led outbound, exec sponsor mapping, paid ABM ads |
| 60–79 | Tier 2 | Scaled ABM: SDR sequence + targeted nurture, marketing-led with sales alert on engagement spike |
| 40–59 | Tier 3 | Programmatic/1:many: standard nurture track, no dedicated rep time |
| < 40 | Deprioritize | Suppress from paid spend and outbound; leave in inbound-only nurture |

## Inputs

| Field | Type | Example |
|---|---|---|
| `account_id` | string | `acct_4821` |
| `industry` | string | `"Financial Services"` |
| `employee_count` | int | `340` |
| `geography` | string | `"US-Northeast"` |
| `tech_stack` | list[string] | `["Salesforce", "Marketo", "Snowflake"]` |
| `touches_90d` | list[{date, type, weight}] | see worked example |
| `intent_topics` | list[{topic, weekly_surge_pct}] | `[{"topic": "RevOps automation", "weekly_surge_pct": 62}]` |
| `icp_definition` | object | industry list, size band, geography list, required/competitor tech |

## Worked example

ICP definition: Financial Services or SaaS, 100–1000 employees, US/Canada, Salesforce present, no existing competitor RevOps tool.

| Account | Industry | Size | Firmographic | Tech | RFM (90d) | Intent | **Score** | **Tier** |
|---|---|---|---|---|---|---|---|---|
| Meridian Capital | Financial Services | 340 | 100 | 100 (Salesforce, no competitor) | 3 touches (demo, product, blog pages), last 5d → 40+9+18=67 | 2-week surge on "RevOps automation" → 100 | **91.75** | **Tier 1** |
| Vantage SaaS Co | SaaS | 80 | 65 (below size band) | 100 | 1 touch, last 40d, blog only → 10+3+2=15 | no data → unscored (excluded from denominator) | **~65** (reweighted) | **Tier 2** |
| Ferrow Logistics | Logistics | 500 | 0 (industry mismatch) | 50 (neutral) | 6 touches, last 2d → 40+18+24=82 | single-week spike → 60 | **41.05** | **Tier 3** |

Output for Meridian Capital: `0.35(100) + 0.25(100) + 0.25(67) + 0.15(100) = 35 + 25 + 16.75 + 15 = 91.75`.

## Common failure patterns

- Scoring intent as 0 when data is simply missing, which silently deprioritizes accounts with no intent-data coverage (common for smaller/private companies) — always separate "no signal" from "negative signal."
- Letting firmographic fit alone put an account in Tier 1 with zero engagement — a perfect ICP match with no engagement is a targeting candidate, not a sales-ready account.
- Re-scoring monthly instead of on a rolling trigger — engagement and intent decay fast; a Tier 1 account with no touches in 30 days should auto-demote, not wait for the next review cycle.
- Applying one national ICP definition to a global account list when fit criteria (size bands, buying behavior) genuinely differ by region.

## Output schema

```json
{
  "scored_accounts": [
    {
      "account_id": "acct_4821",
      "firmographic_fit": 100,
      "technographic_fit": 100,
      "engagement_intensity": 67,
      "intent_signal": 100,
      "intent_data_available": true,
      "segment_fit_score": 91.75,
      "tier": 1,
      "recommended_motion": "named-account ABM",
      "rationale": "Full ICP match, active Salesforce user, sustained 2-week intent surge on RevOps automation, engaged within last 5 days."
    }
  ],
  "tier_summary": { "tier_1": 1, "tier_2": 0, "tier_3": 0, "deprioritized": 0 },
  "data_quality_flags": ["accounts_missing_intent_data"]
}
```

## Recommended prompt

> You are a RevOps analyst applying a firmographic/technographic/engagement/intent segmentation model. Given the ICP definition and account list below, compute each component score using this weighting: firmographic 35%, technographic 25%, engagement (RFM, trailing 90 days) 25%, intent 15%. Show your component scores per account, not just the final number. Flag any account with missing intent data as "unscored" rather than scoring it 0, and reweight its composite score across the remaining components. Return the result as JSON matching this schema: [paste Output schema above]. Assign tiers using: 80+ Tier 1, 60-79 Tier 2, 40-59 Tier 3, below 40 deprioritize.

## Grounded in

- The firmographic + technographic + intent segmentation stack as implemented by category ABM platforms (6sense, Demandbase, Bombora).
- RFM (recency / frequency / monetary-or-depth) scoring, adapted from lifecycle and retention marketing to B2B engagement scoring.
- ICP fit-scoring methodology as taught in B2B GTM operating frameworks (e.g. Winning by Design, OpenView's ICP scorecard approach).

See [sources-and-frameworks.md](../../sources-and-frameworks.md) for the pack's general reference list.
