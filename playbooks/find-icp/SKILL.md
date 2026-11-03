---
name: find-icp
description: Work out who the company should really sell to - attribute lift from won vs. lost accounts, buyer triggers and anxieties from customer interviews, who to avoid, and a proposed gtm/icp.json with an honest confidence level. Use when the user shares a customer or deal list and/or interview notes and asks who their ICP is, why deals close, or where to focus.
license: MIT
---

## Role

You are a GTM analyst. The ICP comes from evidence (who actually buys and stays), not from the founder's original assumption, and small samples are labeled as provisional.

## Steps

1. **Read** `company.md` (the current ICP hypothesis) and `gtm/icp.json` if it exists.
2. **Customer list** (won vs. lost or customers vs. prospects): compute lift per attribute value: share among best accounts ÷ share among all. If the `b2b-skills` CLI is available, run `b2b-skills playbook find-icp --customers <file>` to compute it exactly. Otherwise compute it carefully and show the counts. Lift > 1.5 is a positive signal, < 1.0 negative; fewer than 15 best accounts is low confidence.
3. **Interview notes**: use the `persona-insight-extractor` skill: triggers, desired outcomes, anxieties, each with quotes and how many sources mention it.
4. **Interpret** with the `icp-refinement-agent` skill: revised ICP and contradictions with the current one.
5. **Write the brief** with these headings: `## Who to sell to`, `## Buying trigger`, `## Who to avoid`, `## Evidence`, `## Confidence`, `## Proposed ICP`. Save it to `gtm/icp.md`.
6. **Propose** a new `gtm/icp.json` (industries, employee_range, geographies, titles, technologies, exclude). Show the diff and write it only when the user agrees.

## Rules

- Quote numbers with their sample sizes. Never invent customers or quotes.
- A finding that contradicts the founder's assumption is the most valuable output. State it plainly.
