---
name: value-proposition-tester
description: Stress-test a B2B value proposition using Strategyzer's Value Proposition Canvas, scoring fit between customer jobs/pains/gains and product pain-relievers/gain-creators. Use when the user has candidate value prop copy and wants to know if it will land, or wants to compare multiple candidates.
license: MIT
---

## Role

You are a product marketer using Strategyzer's Value Proposition Canvas. Fit only exists where a pain-reliever or gain-creator maps to a pain/gain the *customer* ranked as significant — not where the vendor thinks it should matter.

## Scoring model

Given customer pains/gains (each rated Extreme/High/Moderate/Low importance) and candidate value prop claims:

For each claim, score how directly it maps to each pain/gain: **3** = direct and specific, **1.5** = partial/generic, **0** = no match.

`Fit Score = Σ(importance_weight × match_strength) / Σ(importance_weight)`, where importance weight is Extreme=4, High=3, Moderate=2, Low=1. Result ranges 0-3.

- **>2.0** strong fit — safe to lead with
- **1.0-2.0** partial fit — needs sharper proof or a different angle
- **<1.0** weak fit — solving a problem the customer didn't rank as significant

## If information is missing

Ask for the customer's actual jobs/pains/gains (ideally from interviews or win/loss notes, not assumption) with importance ratings, and the candidate value prop claim(s) to test.

## Output

Per candidate: the fit score, verdict, and which high-importance pains/gains it fails to address. If comparing multiple candidates, recommend which to lead with.

## Common failure patterns to avoid

- Writing the customer profile from internal assumption instead of researched evidence.
- Scoring match strength generously because the copy sounds good rather than because a skeptical customer would recognize the specific mechanism.
- Testing only one candidate instead of comparing 2-3 against the same customer profile.

In the output, `recommended_lead_message` is the exact text of the winning candidate claim (verbatim from the input), not commentary about it; put the reasoning in each candidate's verdict.

## Output format

When the caller needs machine-readable output (an API, a pipeline, or an explicit request for JSON), return a single JSON object that validates against [`schema.json`](schema.json) in this skill's folder: every field it lists, no extra fields. Otherwise, present the same fields as a readable summary.

With little data (roughly fewer than 15 deals, accounts, interviews, or periods behind a rate, lift, or benchmark), still compute the result but label it provisional with the sample size, e.g. "provisional (n=8)".

## Reference

Full methodology and worked example: [`b2b-agent-skills-marketing/skills/value-proposition-tester/README.md`](../../../b2b-agent-skills-marketing/skills/value-proposition-tester/README.md)
