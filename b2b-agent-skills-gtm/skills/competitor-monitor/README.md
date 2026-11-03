# Competitor Monitor

Classify raw competitor signals (product launches, pricing changes, hires, funding, messaging shifts) into a structured move-type taxonomy and score each by strategic materiality — instead of a running feed of competitor news with no way to tell what actually matters.

## When to use this

- Competitive intel currently means someone forwards interesting links with no consistent structure or prioritization.
- Leadership asks "has anything changed with [competitor]" and the honest answer requires re-reading a month of scattered notes.
- You need to feed structured, prioritized competitor signals into [`competitor-signal-clusterer`](../competitor-signal-clusterer/README.md) for theme-level analysis.

## Methodology

Classify every signal into one move type — because the right response differs completely by type, and lumping them together as "competitor news" obscures that:

| Move type | Examples | Typical response owner |
|---|---|---|
| **Product** | feature launch, platform expansion, acquisition of capability | Product/PMM |
| **Pricing/packaging** | price change, new tier, packaging restructure | RevOps/Sales leadership |
| **GTM motion** | new channel partnership, sales-led → PLG shift, new segment entry | Sales/Marketing leadership |
| **Messaging/positioning** | new category claim, rebrand, campaign theme shift | Marketing/PMM |
| **Organizational** | key exec hire/departure, funding round, layoffs | Executive/strategy |

## Scoring model

```
Materiality Score (0-100) = 
    40 x Overlap (0-1: how directly this move competes with your specific ICP/use case, not just broad category)
  + 30 x Signal_Strength (0=rumor/unconfirmed, 0.5=confirmed but early/limited rollout, 1=confirmed and broadly launched)
  + 30 x Velocity_Relevance (0=isolated event, 0.5=part of a pattern of 2-3 similar moves in the last quarter, 1=part of a clear accelerating pattern of 4+ moves)

Materiality Band:
  70-100  High - brief leadership within 48 hours
  40-69   Moderate - include in next regular competitive update
  <40     Low - log for pattern tracking, no individual alert needed
```

## Inputs

| Field | Type | Example |
|---|---|---|
| `competitor` | string | |
| `signal_description` | string | raw signal as observed |
| `move_type` | enum | product \| pricing \| gtm_motion \| messaging \| organizational |
| `overlap_with_icp` | float (0-1) | |
| `confirmation_level` | enum | rumor \| confirmed_limited \| confirmed_broad |
| `related_moves_last_quarter` | int | count of similar-type moves from this competitor recently |

## Worked example

Signal: Competitor X launches a new "explainable scoring" feature (confirmed, broadly rolled out), directly overlapping with your own core differentiator (overlap 0.9). This is the 3rd product move in this direction from them in the last quarter (part of a pattern).

```
Materiality = 40(0.9) + 30(1.0) + 30(0.5) = 36 + 30 + 15 = 81 → High materiality
```

This crosses the High threshold specifically because of the overlap with a stated core differentiator (see [`brand-positioning-synthesizer`](../../../b2b-agent-skills-marketing/skills/brand-positioning-synthesizer/README.md)) — the same feature launch from a competitor with no overlap to your differentiation would score much lower on the Overlap component alone, even if equally "big news" in the abstract.

## Common failure patterns

- Treating all competitor news as equally worth surfacing, which trains stakeholders to tune out competitive updates entirely (alert fatigue from low-materiality noise).
- Scoring materiality only by how impressive a move sounds, without weighting overlap with your specific ICP/differentiation — a competitor's move into a segment you don't compete in is low materiality regardless of how large the announcement is.
- Acting on unconfirmed rumors with the same urgency as confirmed, broadly-launched moves.
- Missing the pattern signal — three individually low-materiality product moves in the same direction within a quarter is a materially different (and often more important) finding than any one of them in isolation.

## Output schema

```json
{
  "competitor": "Competitor X",
  "signal_description": "launched explainable scoring feature, broad rollout",
  "move_type": "product",
  "overlap_with_icp": 0.9,
  "confirmation_level": "confirmed_broad",
  "related_moves_last_quarter": 3,
  "materiality_score": 81,
  "materiality_band": "high",
  "recommended_action": "brief leadership within 48 hours; feed into competitive-differentiation-coach battlecard update"
}
```

## Recommended prompt

> You are a competitive intelligence analyst. Classify the signal below by move type (product, pricing/packaging, GTM motion, messaging/positioning, organizational). Compute Materiality Score = 40 x overlap_with_icp + 30 x signal_strength (0/0.5/1 for rumor/confirmed-limited/confirmed-broad) + 30 x velocity_relevance (0/0.5/1 for isolated/pattern of 2-3/pattern of 4+ similar moves this quarter). Assign a materiality band and recommended response urgency. Return JSON matching the schema above.

## Grounded in

A move-type taxonomy and overlap/confirmation/pattern-weighted materiality scoring method for competitive intelligence, built to prevent alert fatigue by distinguishing signals that overlap with your actual differentiation from generic competitor news.

See [sources-and-frameworks.md](../../sources-and-frameworks.md) for the pack's general reference list.
