---
name: monday-review
description: Run the weekly pipeline review - flag stale, overdue, and stuck deals, re-score risk from the deal notes already in the workspace, name this week's focus, and propose CRM updates for approval. Use on Mondays, before a pipeline or forecast meeting, or when the user asks which deals need attention.
license: MIT
---

## Role

You are the founder's RevOps partner. The review uses hard CRM signals plus the evidence the workspace has collected from call debriefs, not optimism.

## Steps

1. **Get the open deals.** If the `b2b-skills` CLI is available, run `b2b-skills playbook monday-review --hubspot` (or `--csv pipeline.csv`); it does the rest and writes `gtm/reviews/<date>.md`. Otherwise read the pipeline the user gives you.
2. **Flag in code-like fashion**: close date passed; no activity for 14+ days; 45+ days in stage.
3. **Re-score from evidence**: for each deal with a file in `gtm/deals/`, apply the `deal-risk-assessor` skill to that file's notes. Deals with no file are "no evidence on file".
4. **Write the review** with these headings: `## This week's focus`, `## Deals at risk`, `## No evidence on file`, `## Pipeline snapshot`. Save it to `gtm/reviews/<YYYY-MM-DD>.md`.
5. **CRM updates** (risk band, MEDDPICC score, next action): show them as proposed changes. Apply only after the user approves (`b2b-skills approve`).

## Rules

- Report scores and flags as computed; MEDDPICC is out of 24.
- No notes means no evidence: don't guess a deal's health.
