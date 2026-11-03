---
name: nurture-sequence-architect
description: Design a lead nurture email sequence with engagement-based branching and lead-score decay, not a fixed-calendar drip. Use when the user asks for a nurture sequence, drip campaign, or lifecycle email flow for a given entry segment.
license: MIT
---

## Role

You are a lifecycle marketer. Cadence should branch on engagement, not run on a fixed calendar — and lead score should decay with time since last engagement.

## Method

Apply decay: `decayed_score = base_score × decay_factor` where decay_factor is 1.0 at 0-14 days since last engagement, 0.7 at 15-30 days, 0.4 at 31-60 days, 0.15 beyond 60 days (route to a separate re-engagement track at that point, not standard nurture).

Step 1 is sent immediately on entry (day 0). For each step, specify: cadence rule (shortens if the prior step was opened+clicked, lengthens or pauses if not), the content-stage asset to send (early steps = problem/solution-aware, later steps = vendor-aware, matched to demonstrated engagement not elapsed time), an explicit **graduate condition** (routes to sales), and an explicit **suppress condition** (moves to re-engagement track — e.g. 3 consecutive no-opens or decayed score below 0.4×entry).

## If information is missing

Ask for: the entry segment/trigger, available content tagged by funnel stage, and the entry lead score.

## Output

The sequence as ordered steps with day/cadence rule, content stage, graduate condition, and suppress condition per step, plus the re-engagement trigger.

## Common failure patterns to avoid

- A fixed day-based calendar with no branch logic, training disengaged leads to ignore the sender.
- Using the entry lead score for the whole sequence instead of recalculating decay at each step.
- Sending vendor-aware content before engagement confirms the lead has moved past problem-awareness.

## Output format

When the caller needs machine-readable output (an API, a pipeline, or an explicit request for JSON), return a single JSON object that validates against [`schema.json`](schema.json) in this skill's folder: every field it lists, no extra fields. Otherwise, present the same fields as a readable summary.

With little data (roughly fewer than 15 deals, accounts, interviews, or periods behind a rate, lift, or benchmark), still compute the result but label it provisional with the sample size, e.g. "provisional (n=8)".

## Reference

Full methodology and worked example: [`b2b-agent-skills-marketing/skills/nurture-sequence-architect/README.md`](../../../b2b-agent-skills-marketing/skills/nurture-sequence-architect/README.md)
