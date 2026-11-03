# Strategic Account Priority Ranker

Select the small set of named accounts (typically 20-30) that warrant company-wide executive sponsorship, ranked by strategic value criteria beyond deal size — market influence, reference-ability, and expansion optionality — not just revenue.

## How this differs from similar-sounding skills

See the comparison table in [`account-priority-matrix-builder`](../account-priority-matrix-builder/README.md#how-this-differs-from-similar-sounding-skills) for how this fits alongside the other account-scoring skills in this repo. In short: this skill selects a small, named, cross-functional executive-sponsorship list; it is not a segment-level planning tool (that's account-priority-matrix-builder) or an ABM program tiering tool (that's abm-account-priority-ranker in the marketing pack).

## When to use this

- Deciding which ~20-30 accounts get a named executive sponsor for the year — a limited, high-commitment resource that shouldn't be allocated by deal size alone.
- An account is large but strategically unremarkable (won't be referenceable, won't expand, doesn't influence the market) and is consuming executive attention that could go elsewhere.
- Building the strategic account list for board or leadership review.

## Methodology

Four criteria beyond raw deal size, because an executive sponsorship program exists to advance company-level strategic goals, not just to service the biggest contracts:

| Criterion | What it measures |
|---|---|
| **Revenue value** | current + expansion-adjusted contract value |
| **Reference-ability** | willingness and credibility to serve as a public reference, case study, or analyst reference — directly affects the ability to win other deals |
| **Market influence** | this account's standing in its industry — do other companies in the category watch what this account does |
| **Expansion optionality** | realistic whitespace within the account (see [`account-plan-generator`](../../../b2b-agent-skills-sales/skills/account-plan-generator/README.md)), not just current contract size |

## Scoring model

```
Strategic Value Score (0-100) = 
    0.35 x Revenue_Value (normalized against the largest account in the candidate pool)
  + 0.25 x Reference_ability (0-1: 0=would not reference, 0.5=would reference privately/on request,
           1=confirmed willing to be a named public reference)
  + 0.20 x Market_Influence (0-1: proxy from company size/category standing/analyst visibility)
  + 0.20 x Expansion_Optionality (0-1: whitespace priority score from account-plan-generator,
           normalized against the pool)

Select the top N accounts by score, where N is the program's sponsorship capacity (typically
1 executive sponsor can realistically cover 3-5 accounts well - do not oversize the list beyond
realistic executive bandwidth, which dilutes the program's value).
```

## Inputs

| Field | Type | Example |
|---|---|---|
| `account_id` | string | |
| `revenue_value` | number | |
| `referenceability` | float (0-1) | |
| `market_influence` | float (0-1) | |
| `expansion_optionality` | float (0-1) | from account-plan-generator whitespace score, normalized |
| `available_executive_sponsors` | int | used to size the final list |

## Worked example

Account A: revenue $800K (largest in pool, normalized 1.0), referenceability 0.5 (would reference privately, not publicly confirmed), market influence 0.3 (mid-tier player, limited category visibility), expansion optionality 0.6.
```
Strategic Value = 0.35(1.0) + 0.25(0.5) + 0.20(0.3) + 0.20(0.6) = 0.35 + 0.125 + 0.06 + 0.12 = 0.655 → 65.5
```
Account B: revenue $350K (normalized 0.44), referenceability 1.0 (confirmed public reference, category-recognized), market influence 0.9 (category leader others watch closely), expansion optionality 0.7.
```
Strategic Value = 0.35(0.44) + 0.25(1.0) + 0.20(0.9) + 0.20(0.7) = 0.154 + 0.25 + 0.18 + 0.14 = 0.724 → 72.4
```

Account B outranks Account A despite less than half the revenue, because its reference-ability and market influence make it disproportionately valuable to the company's broader GTM motion (every other deal in the category benefits from B's public advocacy) — exactly the kind of account an executive sponsorship program should prioritize over a larger but strategically unremarkable one.

## Common failure patterns

- Defaulting to a pure revenue-ranked list, which is what a territory or pipeline report already shows — the strategic list should surface accounts a revenue-only view would miss or over-rank.
- Sizing the sponsorship list beyond what available executives can realistically cover (3-5 accounts per sponsor) — an oversized list dilutes attention and turns "executive sponsorship" into a title without substance.
- Scoring reference-ability from assumption ("they seem happy") instead of confirmed willingness — an unconfirmed reference should score at most 0.5, not 1.0.
- Not revisiting the list regularly — market influence and reference-ability shift as accounts grow, change leadership, or have public events; an annual-only refresh can miss a now-more-strategic account.

## Output schema

```json
{
  "accounts_ranked": [
    {"account_id": "acct_B", "revenue_value": 350000, "referenceability": 1.0, "market_influence": 0.9, "expansion_optionality": 0.7, "strategic_value_score": 72.4}
  ],
  "recommended_list_size": 25,
  "sponsorship_capacity_basis": "5 executives x 5 accounts each"
}
```

## Recommended prompt

> You are a strategic accounts analyst selecting the company's executive-sponsorship account list. Compute Strategic Value Score = 0.35 x normalized revenue value + 0.25 x referenceability (score confirmed public reference willingness as 1.0, private-only as 0.5, unconfirmed/assumed as at most 0.5) + 0.20 x market influence + 0.20 x expansion optionality. Rank all candidate accounts and select the top N accounts where N is sized to realistic executive sponsorship capacity (roughly 3-5 accounts per available sponsor), not an arbitrary round number. Return JSON matching the schema above.

## Grounded in

Strategic account selection for executive sponsorship programs, weighted beyond revenue to reference-ability, market influence, and expansion optionality, and explicitly capacity-constrained to the number of accounts an executive can realistically sponsor well.

See [sources-and-frameworks.md](../../sources-and-frameworks.md) for the pack's general reference list.
