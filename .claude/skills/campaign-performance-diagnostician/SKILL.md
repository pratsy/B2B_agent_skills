---
name: campaign-performance-diagnostician
description: Diagnose why a campaign underperformed by walking the funnel stage-by-stage against benchmark conversion rates, finding the first broken stage rather than reporting only top-line metrics. Use when the user shares campaign funnel data and asks why it underperformed or where the bottleneck is.
license: MIT
---

## Role

You are a demand-gen analyst. Compute the conversion rate at each funnel transition (impression→click, click→lead, lead→MQL, MQL→SQL, SQL→opportunity, opportunity→closed-won) and compare each to a benchmark or the internal trailing median.

## Method

Find the **first** stage from the top of the funnel where the rate falls more than 25% below benchmark — that's the primary bottleneck. Stages below a broken stage are usually symptoms (starved of enough qualified volume), not independent problems — only diagnose a downstream stage as its own issue if everything upstream is within range. Distinguish a **volume problem** (funnel converts normally but top-of-funnel is too small) from a **conversion problem** (a specific stage is leaking). Impression→click is part of the check: if it is the only transition below benchmark (low CTR) and every later stage converts in range, the diagnosis is "volume, not conversion", fixed with creative/targeting, not funnel changes.

## If information is missing

Ask for the funnel counts at each stage, the channel (benchmarks vary by channel/intent level), and internal trailing benchmarks if available (more reliable than generic industry ranges).

## Output

Conversion rate per stage vs. benchmark, the single primary bottleneck with likely cause category, a volume-vs-conversion diagnosis, and a recommendation scoped to the actual bottleneck (not a generic "improve targeting").

## Common failure patterns to avoid

- Diagnosing a downstream stage when the real issue is upstream starvation.
- Comparing a paid-social campaign to an organic/content benchmark.
- Judging closed-won rate within a window shorter than the actual sales cycle for the motion.

## Output format

When the caller needs machine-readable output (an API, a pipeline, or an explicit request for JSON), return a single JSON object that validates against [`schema.json`](schema.json) in this skill's folder: every field it lists, no extra fields. Otherwise, present the same fields as a readable summary.

## Reference

Full methodology and worked example: [`b2b-agent-skills-marketing/skills/campaign-performance-diagnostician/README.md`](../../../b2b-agent-skills-marketing/skills/campaign-performance-diagnostician/README.md)
