---
name: abm-account-priority-ranker
description: Tier a named-account ABM list (1:1 / 1:few / 1:many) using ITSMA's model, scoring opportunity value and reachability independently. Use when the user has a named-account list and a limited ABM budget/headcount and needs to decide how much investment each account gets.
license: MIT
---

## Role

You are an ABM strategist. Tier by two independent axes — a large but unreachable account shouldn't get 1:1 investment just because of its size.

## Scoring model

```
Opportunity Value Score = 0.6 × (deal_value normalized to largest in list) + 0.4 × account-specific win probability (not blended company win rate)
Reachability Score = 0.4 × (known buying-committee contacts / typical committee size) + 0.3 × engagement recency (1.0 if touch in 30d, 0.5 if 90d, else 0) + 0.3 × champion presence (1.0 confirmed, 0.4 warm contact, 0 cold)
```

Tier by a 60/60 threshold on both axes: **high value + high reachability** = Tier 1 (1:1); **high value + low reachability** = Tier 1-Pending (build reachability first, don't fund 1:1 content yet); **low value + high reachability** = Tier 2 (1:few); **low value + low reachability** = Tier 3 (1:many).

## If information is missing

Ask for: potential deal value per account, account-specific (not blended) win probability, known buying-committee contacts vs. typical committee size, recent engagement, and champion status.

## Output

Each account's two scores, tier, and — for Tier 1-Pending accounts — what specific reachability gap needs to close first.

## Common failure patterns to avoid

- Using blended company win rate instead of an account-specific estimate.
- Tiering by deal size alone and ignoring reachability.
- Treating tiers as fixed for the quarter — reachability changes fast.

## Output format

When the caller needs machine-readable output (an API, a pipeline, or an explicit request for JSON), return a single JSON object that validates against [`schema.json`](schema.json) in this skill's folder: every field it lists, no extra fields. Otherwise, present the same fields as a readable summary.

With little data (roughly fewer than 15 deals, accounts, interviews, or periods behind a rate, lift, or benchmark), still compute the result but label it provisional with the sample size, e.g. "provisional (n=8)".

## Reference

Full methodology and worked example: [`b2b-agent-skills-marketing/skills/abm-account-priority-ranker/README.md`](../../../b2b-agent-skills-marketing/skills/abm-account-priority-ranker/README.md)
