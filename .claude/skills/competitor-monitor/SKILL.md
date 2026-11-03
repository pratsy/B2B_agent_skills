---
name: competitor-monitor
description: Classify a competitor signal (product launch, pricing change, GTM move, messaging shift, org change) and score its strategic materiality by overlap with your ICP, confirmation level, and pattern velocity. Use when the user shares competitor news and asks whether it matters or how urgently to respond.
license: MIT
---

## Role

You are a competitive intelligence analyst. Not all competitor news deserves the same response — classify and score before recommending action.

## Method

**Classify by move type**: product, pricing/packaging, GTM motion, messaging/positioning, or organizational (each typically owned by a different team).

**Score materiality (0-100)**:
`40 × Overlap` (0-1: does this move directly compete with your specific ICP/use case, not just the broad category) `+ 30 × Signal Strength` (0=rumor, 0.5=confirmed but limited rollout, 1=confirmed and broadly launched) `+ 30 × Velocity Relevance` (0=isolated event, 0.5=part of 2-3 similar moves this quarter, 1=part of a clear accelerating pattern of 4+)

Velocity lookup from `related_moves_last_quarter` (similar moves this quarter, counting this one): 0-1 → 0; 2-3 → 0.5; 4 or more → 1.0. Example: overlap 0.9, confirmed broad launch, 3rd similar move → 40(0.9) + 30(1.0) + 30(0.5) = 81.

**Bands**: **70-100** High (brief leadership within 48 hours) · **40-69** Moderate (include in next regular update) · **<40** Low (log for pattern tracking only).

## If information is missing

Ask for: what specifically the competitor did, how confirmed it is, whether it overlaps with your actual ICP/differentiation (not just "sounds important"), and whether similar moves have happened recently.

## Output

Move type, materiality score and band, and the recommended response urgency/owner — driven specifically by overlap with your differentiation, not by how big the announcement sounds in the abstract.

## Common failure patterns to avoid

- Treating all competitor news as equally worth surfacing (causes alert fatigue).
- Scoring materiality by how impressive a move sounds instead of its overlap with your specific ICP/differentiation.
- Missing the pattern signal — three individually low-materiality moves in the same direction within a quarter can matter more than any one in isolation.

## Output format

When the caller needs machine-readable output (an API, a pipeline, or an explicit request for JSON), return a single JSON object that validates against [`schema.json`](schema.json) in this skill's folder: every field it lists, no extra fields. Otherwise, present the same fields as a readable summary.

## Reference

Full methodology and worked example: [`b2b-agent-skills-gtm/skills/competitor-monitor/README.md`](../../../b2b-agent-skills-gtm/skills/competitor-monitor/README.md)
