---
name: score-list
description: Rank a lead or account list against the company's ICP - fit score and A/B/C tier for every row with the reasons, and a why-now plus opening line for the top leads. Use when the user has a CSV or pasted list of leads/accounts (Apollo, Clay, HubSpot, LinkedIn export) and asks who to contact first.
license: MIT
---

## Role

You help a founder decide who to contact this week. Fit is scored with explicit rules, not vibes, so the ranking is repeatable and explainable.

## Steps

1. **Load the ICP** from `gtm/icp.json` in the workspace. If it doesn't exist, help the user write one (industries, employee_range, geographies, titles, technologies, exclude) from `company.md`, or suggest running the `find-icp` playbook first.
2. **Score fit for every row.** If the `b2b-skills` CLI is available, run `b2b-skills playbook score-list --csv <file>`: it computes fit exactly in code and writes `gtm/lists/`. Otherwise score each row yourself with the same rule: industry 30, size 25, title 25, geography 10, technology 10 points; leave criteria with no data out and rescale; excluded industries/titles score 0. Tiers: A ≥80, B 60-79, C 40-59, skip <40.
3. **For the top A/B rows**, write a one-sentence why-now and an opening line, using only that row's fields and the company context. Never invent facts about a lead (funding, news, hiring).
4. **Report**: counts per tier, the top list with reasons, and how many rows couldn't be scored for lack of data.

## Rules

- Missing data is unknown, not a mismatch; say what's missing.
- Use the `lead-prioritization-agent` skill when rows include engagement or intent signals (recent visits, demo requests), to separate fit from intent.
