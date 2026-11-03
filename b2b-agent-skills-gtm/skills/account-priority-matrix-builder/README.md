# Account Priority Matrix Builder

Build a cross-functional value-vs-effort 2x2 for GTM planning — deciding which account segments the *whole organization* (sales, marketing, and CS together) should coordinate investment around for the coming planning cycle, at the segment/tier level rather than the individual-account level.

## How this differs from similar-sounding skills

This pack has several account-scoring skills that look similar but answer different questions at different organizational levels:

| Skill | Question answered | Level |
|---|---|---|
| **This skill** | Which account segments/tiers should the whole GTM org coordinate investment around this cycle? | Leadership/planning, segment-level |
| [`strategic-account-priority-ranker`](../strategic-account-priority-ranker/README.md) (gtm) | Which ~20-30 *named* accounts deserve company-wide executive sponsorship? | Leadership, named-account level |
| [`abm-account-priority-ranker`](../../../b2b-agent-skills-marketing/skills/abm-account-priority-ranker/README.md) (marketing) | Given a named-account list, how much ABM program investment does each get? | Marketing execution, named-account level |
| [`territory-prioritization-agent`](../../../b2b-agent-skills-sales/skills/territory-prioritization-agent/README.md) (sales) | Within one rep's territory, which accounts get their time? | Individual rep, full-book level |

Use this skill first, at planning time, to set segment-level priorities — its output (which segments matter most) becomes an input constraint for the other three.

## Methodology

Classic 2x2 prioritization: **Value** (revenue/strategic potential of the segment) on one axis, **Effort/Winnability** (how hard it is to capture, cycle length, competitive intensity) on the other — but built cross-functionally, using inputs each function actually owns, not one team's unilateral view.

```
Value Score (0-100) = 
    0.5 x normalized_TAM_in_segment (from market-sizing-modeler bottom-up method)
  + 0.3 x average_contract_value_index (this segment's ACV relative to company average)
  + 0.2 x strategic_fit (0-1, does this segment align with the product roadmap and long-term positioning)

Effort Score (0-100, higher = harder) = 
    0.4 x average_sales_cycle_index (relative to company average)
  + 0.3 x competitive_intensity (0-1, from competitor-monitor signal density in this segment)
  + 0.3 x win_rate_inverse (1 - historical win rate in this segment)
```

### Quadrant actions

| | Low Effort | High Effort |
|---|---|---|
| **High Value** | **Invest now** — fastest path to material revenue, fund cross-functionally without reservation | **Invest deliberately** — worth pursuing, but needs a dedicated strategy (see strategic-account-priority-ranker for named-account execution), not default motion |
| **Low Value** | **Efficient/self-serve motion** — don't over-invest high-touch resources here | **Deprioritize** — do not fund dedicated cross-functional motion |

## Inputs

| Field | Type | Example |
|---|---|---|
| `segment_name` | string | |
| `tam_estimate` | number | from market-sizing-modeler |
| `acv_index` | float | this segment's ACV / company average ACV |
| `strategic_fit` | float (0-1) | |
| `sales_cycle_index` | float | this segment's cycle length / company average |
| `competitive_intensity` | float (0-1) | |
| `historical_win_rate` | float | |

## Worked example

Segment "mid-market FinTech": TAM $95M (largest of segments evaluated, normalized to 1.0), ACV index 1.2 (20% above company average), strategic fit 0.9 (aligns with roadmap). Sales cycle index 0.8 (20% faster than average), competitive intensity 0.4 (moderate), win rate 35%.

```
Value = 0.5(1.0) + 0.3(1.2) + 0.2(0.9) = 0.5 + 0.36 + 0.18 = 1.04 → normalize/scale to 0-100: ~87
Effort = 0.4(0.8) + 0.3(0.4) + 0.3(1-0.35) = 0.32 + 0.12 + 0.195 = 0.635 → scale to 0-100: ~64 (moderate-high on a relative scale)
```

Relative to other segments scoring lower on value and higher on effort, mid-market FinTech lands in **High Value / Low-Moderate Effort → Invest now** — the clearest candidate for coordinated cross-functional investment this cycle, ahead of segments with larger raw TAM but longer cycles and lower win rates.

## Common failure patterns

- Building the matrix from one function's data alone (e.g., sales pipeline data only), which misses effort signals marketing or CS would surface (e.g., high competitive intensity in marketing's channel data).
- Using raw TAM as the entire value score, ignoring ACV and strategic fit — a large but low-ACV, roadmap-misaligned segment can outrank a smaller, higher-value one on TAM alone.
- Treating quadrant placement as permanent — segment value/effort shifts as competitive intensity and win rates change; rebuild at least each planning cycle.
- Skipping straight to named-account tactics (ABM tiering, territory ranking) without first setting segment-level priorities here, which risks each function independently prioritizing different segments.

## Output schema

```json
{
  "segments_scored": [
    {"segment": "mid-market FinTech", "value_score": 87, "effort_score": 64, "quadrant": "high value / moderate effort", "action": "invest now"}
  ],
  "planning_cycle": "Q1 2027"
}
```

## Recommended prompt

> You are a GTM strategy analyst building a cross-functional account priority matrix. For each segment, compute Value Score = 0.5 x normalized TAM + 0.3 x ACV index + 0.2 x strategic fit, and Effort Score = 0.4 x sales cycle index + 0.3 x competitive intensity + 0.3 x (1 - historical win rate), each scaled 0-100 relative to the segments being compared. Place each segment in a quadrant (high/low value x high/low effort) and state the recommended action for that quadrant. Return JSON matching the schema above.

## Grounded in

Classic value-vs-effort 2x2 prioritization, built cross-functionally at the segment level to set GTM planning priorities that then constrain named-account-level tools elsewhere in this repo, rather than each function prioritizing independently.

See [sources-and-frameworks.md](../../sources-and-frameworks.md) for the pack's general reference list.
