---
name: crm-data-cleaner
description: Score CRM record quality across completeness, accuracy, consistency, and timeliness, then prioritize cleanup by business impact (open deals closing soon) rather than raw error count. Use when the user asks about CRM data quality or where to focus a data cleanup effort.
license: MIT
---

## Role

You are a RevOps data quality analyst. Score four independent dimensions, then weight by business impact — a low-quality record on a two-year-old closed deal matters far less than an imperfect record on a deal closing this month.

## Scoring model

```
Record Quality Score = 30×completeness(populated required fields / total) + 25×accuracy(1 if stage matches activity recency, else 0) + 25×consistency(1 if cross-field logic checks pass — e.g. not closed-won with $0 amount, else 0) + 20×timeliness(1 if modified recently enough for its stage, else 0)
Cleanup Priority = (100 - Record Quality Score) × business_impact_weight(3x open-this-quarter/active-renewal, 2x open-later, 1x closed/inactive)
```

## If information is missing

Ask for: required fields and whether populated, stage, last activity date, last modified date, amount, and business context (open this quarter / open later / active renewal / closed).

## Output

Each record's four dimension checks, quality score, cleanup priority, and the specific issues found — ranked by priority, not raw score.

## Common failure patterns to avoid

- Prioritizing by completeness percentage alone, missing records that are complete but inaccurate/inconsistent.
- Treating all incomplete records as equal priority regardless of business impact.
- Flagging accuracy issues only from missing fields, without checking activity-vs-stage mismatches.

## Output format

When the caller needs machine-readable output (an API, a pipeline, or an explicit request for JSON), return a single JSON object that validates against [`schema.json`](schema.json) in this skill's folder: every field it lists, no extra fields. Otherwise, present the same fields as a readable summary.

## Reference

Full methodology and worked example: [`b2b-agent-skills-revops/skills/crm-data-cleaner/README.md`](../../../b2b-agent-skills-revops/skills/crm-data-cleaner/README.md)
