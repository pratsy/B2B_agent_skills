# Territory Prioritization Agent

Rank accounts within a rep's territory by whitespace-adjusted TAM (total addressable market potential weighted by realistic capture likelihood), so territory planning allocates time to the accounts with the best combination of size and winnability — not just the largest logos.

## When to use this

- A territory has 200+ accounts and a rep needs a defensible top-30 target list, not an alphabetical account list.
- Territory planning currently ranks by account size alone, and reps spend disproportionate time on large accounts they have little realistic chance of penetrating this cycle.
- You're rebalancing territories and need an objective sizing method rather than tenure-based or arbitrary assignment.

## Methodology

Two components, deliberately kept separate before combining, because a large account with low capture likelihood and a smaller account with high capture likelihood require very different time investment even if their raw TAM is similar:

- **TAM estimate**: realistic addressable spend for this account within your product line, sized from firmographic proxies (headcount, revenue band) calibrated against actual comparable-customer contract values — not a generic "% of company revenue" guess.
- **Capture Likelihood**: probability of winning this account in a reasonable planning horizon (this cycle/year), driven by fit (see ICP lift scoring), existing relationship/whitespace status (see [`account-plan-generator`](../account-plan-generator/README.md) for owned accounts), and competitive displacement difficulty (is there an entrenched incumbent).

## Scoring model

```
Territory Priority Score = TAM_estimate x Capture_Likelihood (0-1)

Capture_Likelihood = 
    0.4 x icp_fit_score (0-1, from lift-based fit scoring)
  + 0.3 x relationship_status (1.0 existing account/warm relationship, 0.5 some prior touch, 0.1 cold)
  + 0.3 x competitive_openness (1.0 no entrenched incumbent or known dissatisfaction with one, 0.5 incumbent present but contract nearing renewal, 0.1 recently-signed entrenched incumbent)
```

Rank accounts by Territory Priority Score, not TAM alone. Segment the ranked list into tiers (e.g., top 20% = primary focus, next 30% = secondary, remainder = light-touch/inbound-only) rather than treating the list as strictly sequential — this mirrors the ABM tiering logic in [`abm-account-priority-ranker`](../../../b2b-agent-skills-marketing/skills/abm-account-priority-ranker/README.md) but applied to an individual rep's full territory rather than a curated named-account list.

## Inputs

| Field | Type | Example |
|---|---|---|
| `territory_accounts` | list[{account_id, tam_estimate, icp_fit_score, relationship_status, competitive_openness}] | |
| `rep_capacity` | int | realistic number of accounts a rep can meaningfully work this cycle, used to size the primary tier |

## Worked example

Account A: TAM $200K, ICP fit 0.9, relationship 0.1 (cold), competitive_openness 0.1 (recently-signed incumbent).
```
Capture Likelihood = 0.4(0.9) + 0.3(0.1) + 0.3(0.1) = 0.36 + 0.03 + 0.03 = 0.42
Priority Score = 200,000 x 0.42 = 84,000
```
Account B: TAM $90K, ICP fit 0.8, relationship 1.0 (existing warm relationship), competitive_openness 0.5 (incumbent present, contract renewal approaching).
```
Capture Likelihood = 0.4(0.8) + 0.3(1.0) + 0.3(0.5) = 0.32 + 0.30 + 0.15 = 0.77
Priority Score = 90,000 x 0.77 = 69,300
```

Account A still ranks higher on raw priority score (84,000 vs 69,300) despite lower capture likelihood, because its TAM is more than double — but the gap is much narrower than the raw TAM difference (200K vs 90K) would suggest, and a rep with limited capacity should weigh that Account B is meaningfully more likely to convert this cycle. Present both the score and the underlying likelihood so the rep can make the time-allocation call with full information, not just the blended number.

## Common failure patterns

- Ranking territory accounts by TAM/company size alone, which sends reps chasing large, cold, incumbent-locked accounts at the expense of smaller, warmer, winnable ones.
- Treating competitive_openness as static — an incumbent's contract renewal date is a real, trackable signal that should update this score on a schedule, not be set once.
- Sizing TAM from a flat percentage-of-revenue rule instead of calibrating against actual comparable-customer contract values, which tends to wildly overstate TAM for large accounts and understate it for mid-size ones with higher per-seat intensity.
- Presenting only the blended Priority Score without the underlying Capture Likelihood, which hides the size-vs-winnability tradeoff a rep needs to see to allocate time well.

## Output schema

```json
{
  "accounts_ranked": [
    {"account_id": "acct_A", "tam_estimate": 200000, "capture_likelihood": 0.42, "priority_score": 84000, "tier": "primary"},
    {"account_id": "acct_B", "tam_estimate": 90000, "capture_likelihood": 0.77, "priority_score": 69300, "tier": "primary"}
  ],
  "tiering": {"primary_pct": 20, "secondary_pct": 30, "light_touch_pct": 50}
}
```

## Recommended prompt

> You are a sales operations analyst prioritizing a rep's territory. For each account, compute Capture Likelihood = 0.4 x icp_fit_score + 0.3 x relationship_status + 0.3 x competitive_openness, then Territory Priority Score = tam_estimate x Capture Likelihood. Rank accounts by priority score, but report capture likelihood alongside it so the size-vs-winnability tradeoff is visible, not hidden in the blended number. Segment into primary/secondary/light-touch tiers sized to the rep's stated capacity. Return JSON matching the schema above.

## Grounded in

TAM-times-capture-likelihood territory scoring, consistent with account-based territory design practice in B2B sales operations, kept as two visible components so time allocation decisions aren't made on a single opaque number.

See [sources-and-frameworks.md](../../sources-and-frameworks.md) for the pack's general reference list.
