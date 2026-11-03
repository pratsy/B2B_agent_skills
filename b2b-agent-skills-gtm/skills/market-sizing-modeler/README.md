# Market Sizing Modeler

Build a TAM/SAM/SOM market size estimate using both top-down and bottom-up methods independently, then reconcile the two — instead of presenting a single top-down number, which is the most common way market sizing becomes unreliable (or unfalsifiable) in a GTM plan.

## When to use this

- Building a GTM plan or investor/board narrative that needs a defensible market size, not a rounded industry-report figure.
- Two team members have produced wildly different market size estimates and need a structured way to reconcile them.
- Sizing a new segment or geography before committing GTM investment.

## Methodology

**TAM** (Total Addressable Market): total revenue opportunity if you captured 100% of the market for your category, globally.
**SAM** (Serviceable Addressable Market): the portion of TAM you could realistically serve given your actual product, geography, and go-to-market constraints (e.g., language support, compliance certifications, current sales motion).
**SOM** (Serviceable Obtainable Market): the portion of SAM you could realistically capture in a defined time horizon given competition and your actual execution capacity.

**Two independent methods, always both computed:**

- **Top-down**: start from a published industry market size figure, narrow by the % that matches your specific category/segment, narrow again by your SAM constraints.
- **Bottom-up**: count actual target accounts (from firmographic data — see [`icp-refinement-agent`](../../../b2b-agent-skills-marketing/skills/icp-refinement-agent/README.md)) × realistic average contract value, built up from your own comparable-customer data, not assumption.

## Reconciliation logic

```
Divergence = |top_down_estimate - bottom_up_estimate| / min(top_down_estimate, bottom_up_estimate)

Divergence < 30%    → estimates roughly agree; use the average, note the range
Divergence 30-100%  → material disagreement; investigate which method's assumptions are weaker
                       before reporting either number with confidence
Divergence > 100%   → one method is very likely wrong; most commonly the top-down category-%
                       narrowing was too loose, or the bottom-up target-account count is incomplete
```

Never report a single blended number without disclosing the divergence — a market sizing estimate presented with false precision is a common way GTM plans lose credibility with a sharp board or investor.

## Inputs

| Field | Type | Example |
|---|---|---|
| `published_market_size` | {figure, source, category_scope} | e.g. `{"figure": 12000000000, "source": "industry report X", "category_scope": "broader than our specific segment"}` |
| `category_narrowing_pct` | float | your estimate of what % of the published figure matches your specific category |
| `sam_constraint_pct` | float | % of TAM addressable given your actual product/geo/motion constraints |
| `target_account_count` | int | from bottom-up ICP-matched account counting |
| `realistic_acv` | number | from actual comparable-customer contract values, not list price |
| `time_horizon_years` | int | for SOM capture estimate |
| `realistic_capture_rate` | float | your estimated realistic win share of SAM within the horizon |

## Worked example

Top-down: published market size $12B (broad category). Category narrowing: 15% of that is actually our specific segment → $1.8B TAM (top-down). SAM constraint: 40% addressable given current geo/product scope → $720M SAM (top-down).

Bottom-up: 3,400 target accounts matching ICP × $28,000 realistic ACV (from actual closed-won average, not list price) = **$95.2M SAM (bottom-up).**

```
Divergence = |720,000,000 - 95,200,000| / 95,200,000 ≈ 656% → one method is very likely wrong
```

Investigation: the top-down category-narrowing (15%) was an unvalidated guess; the bottom-up count (3,400 accounts) is directly counted from firmographic data and far more defensible. Reported conclusion: **use the bottom-up SAM ($95.2M) as the primary figure**, flag the top-down estimate as needing a better category-narrowing input before it's usable, rather than averaging two numbers that disagree by 6.5x into a false middle figure.

## Common failure patterns

- Reporting a single top-down number sourced from an industry report without ever cross-checking it against a bottom-up count — the most common way market sizing becomes disconnected from the actual target-account reality.
- Averaging two estimates that diverge by more than 100% instead of investigating which one's assumptions are weak — the average of a very wrong number and a roughly right number is still wrong.
- Using list price instead of realistic average contract value (from actual closed-won data) in the bottom-up calculation, which overstates SOM.
- Computing SOM from SAM without an explicit, honest capture-rate assumption — "we could get 50% of the market" needs to be stated and justified, not implied by omission.

## Output schema

```json
{
  "top_down": {"tam": 1800000000, "sam": 720000000},
  "bottom_up": {"sam": 95200000, "target_account_count": 3400, "realistic_acv": 28000},
  "divergence_pct": 656,
  "divergence_verdict": "material disagreement - top-down category narrowing unvalidated",
  "recommended_primary_estimate": "bottom-up SAM ($95.2M) - more defensible input data",
  "som": {"time_horizon_years": 3, "realistic_capture_rate": 0.08, "estimate": 7616000}
}
```

## Recommended prompt

> You are a GTM strategy analyst. Compute TAM and SAM via top-down (published market size x category narrowing % x SAM constraint %) and separately via bottom-up (target account count x realistic ACV from actual comparable-customer data). Compute the divergence between the two SAM estimates as a percentage. If divergence exceeds 100%, identify which method's assumptions are weakest rather than averaging the two. Compute SOM from the more defensible estimate using the given time horizon and realistic capture rate, stating the capture rate assumption explicitly. Return JSON matching the schema above.

## Grounded in

The TAM/SAM/SOM market-sizing framework standard in GTM and venture strategy, always computed via both top-down and bottom-up methods and explicitly reconciled, since a single-method estimate presented without a cross-check is one of the most common ways market sizing loses credibility.

See [sources-and-frameworks.md](../../sources-and-frameworks.md) for the pack's general reference list.
