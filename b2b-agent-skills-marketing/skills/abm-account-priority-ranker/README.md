# ABM Account Priority Ranker

Assign a fixed, named target-account list into ABM tiers (1:1 / 1:few / 1:many) using the ITSMA/ABM Leadership Alliance tiering model, based on opportunity value and reachability — not broad audience segmentation.

## How this differs from Audience Segmentation Optimizer

[`audience-segmentation-optimizer`](../audience-segmentation-optimizer/README.md) scores and tiers a *broad* account/contact universe for top-of-funnel targeting. This skill takes a smaller, already-curated named-account list (from sales + marketing strategic planning) and decides how much dedicated investment each account gets — the ABM program design question, not the top-of-funnel targeting question. Use segmentation first to find the universe; use this to decide how to resource a specific list.

## When to use this

- You have a named-account list (50–500 accounts) and a fixed ABM budget/headcount, and need a defensible way to allocate it.
- Sales wants 1:1 treatment for accounts marketing doesn't think justify the investment, or vice versa.
- You're building the quarterly ABM plan and need to show why each tier gets a different motion and spend level.

## Methodology

ITSMA's ABM tiering model, using two independent axes:

- **Opportunity value**: potential deal/expansion value if won, weighted by probability of winning at this account specifically (not generic win rate).
- **Reachability**: how identifiable and engageable the buying committee is right now (known contacts, active engagement, accessible champions).

Accounts high on both axes get the most expensive motion (1:1); high value but low current reachability get a "why aren't we reachable yet" plan before 1:1 investment, not the investment itself.

## Scoring model

```
Opportunity Value Score (0-100) = 
    0.6 × (potential_deal_value / largest_deal_value_in_list × 100)
  + 0.4 × win_probability_at_this_account (0-100, from sales' account-specific assessment, not blended win rate)

Reachability Score (0-100) =
    0.4 × (known_buying_committee_contacts / typical_buying_committee_size × 100, capped at 100)
  + 0.3 × engagement_recency_score (100 if touch in 30d, 50 if 90d, 0 otherwise)
  + 0.3 × champion_presence (100 if an internal champion is confirmed, 40 if a warm contact exists, 0 if cold)
```

### Tier assignment (2x2)

| | High Reachability (≥60) | Low Reachability (<60) |
|---|---|---|
| **High Value (≥60)** | **Tier 1 (1:1)** — dedicated plan, exec sponsor mapping, custom content | **Tier 1-Pending** — reachability-building plan first (exec intros, LinkedIn/event touches); do not fund 1:1 content yet |
| **Low Value (<60)** | **Tier 2 (1:few)** — grouped by shared vertical/use case, semi-custom content | **Tier 3 (1:many)** — programmatic nurture, no dedicated content |

## Inputs

| Field | Type | Example |
|---|---|---|
| `account_id` | string | `acct_1190` |
| `potential_deal_value` | number | `240000` |
| `win_probability_at_account` | int (0-100) | `35` |
| `known_buying_committee_contacts` | int | `3` |
| `typical_buying_committee_size` | int | `7` |
| `last_touch_days_ago` | int | `18` |
| `champion_status` | enum | `confirmed \| warm \| none` |

## Worked example

Account "Orion Health" — potential deal value $240K (largest in list is $400K), win probability 35%, 3 of 7 buying-committee contacts known, last touch 18 days ago, confirmed champion.

```
Opportunity Value = 0.6×(240000/400000×100) + 0.4×35 = 0.6×60 + 14 = 36 + 14 = 50
Reachability = 0.4×(3/7×100) + 0.3×100 + 0.3×100 = 0.4×42.9 + 30 + 30 = 17.1+30+30 = 77.1
```
Value 50 (below 60), Reachability 77 (above 60) → **Tier 2 (1:few)**: grouped ABM motion, not full 1:1 investment, despite strong reachability — the opportunity size doesn't yet justify custom 1:1 content.

## Common failure patterns

- Using blended company-wide win rate instead of an account-specific assessment, which flattens every account to the same value score.
- Tiering by deal size alone and ignoring reachability, which puts unreachable whale accounts in Tier 1 where spend gets wasted on content nobody sees.
- Treating tier assignment as permanent for the quarter — reachability changes fast (a new champion or a re-org can flip an account from Tier 1-Pending to Tier 1 mid-quarter).
- Letting sales override tiers without updating the underlying inputs — if sales believes an account is undervalued, the fix is to correct `win_probability_at_account`, not to hand-override the tier.

## Output schema

```json
{
  "accounts_ranked": [
    {"account_id": "acct_1190", "opportunity_value_score": 50, "reachability_score": 77.1, "tier": "Tier 2 (1:few)", "rationale": "confirmed champion and recent engagement, but deal value below Tier 1 threshold"}
  ],
  "tier_counts": {"tier_1": 0, "tier_1_pending": 0, "tier_2": 1, "tier_3": 0}
}
```

## Recommended prompt

> You are an ABM strategist applying the ITSMA tiering model. Given the named-account list below, compute Opportunity Value Score = 0.6×(deal value normalized to largest in list) + 0.4×account-specific win probability, and Reachability Score = 0.4×(known contacts / typical committee size) + 0.3×engagement recency + 0.3×champion presence, each 0-100. Assign each account to Tier 1 (1:1), Tier 1-Pending, Tier 2 (1:few), or Tier 3 (1:many) using the 60/60 thresholds. For Tier 1-Pending accounts, state what reachability gap needs to close first. Return JSON matching the schema above.

## Grounded in

ITSMA / ABM Leadership Alliance's tiered account-based marketing model (1:1 / 1:few / 1:many), the standard framework for allocating ABM investment across a named-account list by value and reachability rather than value alone.

See [sources-and-frameworks.md](../../sources-and-frameworks.md) for the pack's general reference list.
