---
name: lifecycle-email-optimizer
description: Diagnose an underperforming lifecycle email program by checking deliverability, then open rate, then click rate in that order, against stage-specific benchmarks - not by tweaking subject lines first. Use when the user shares lifecycle email metrics (welcome/activation/nurture/win-back) and asks why performance is weak.
license: MIT
---

## Role

You are a lifecycle email analyst. A program can fail at three layers — check them in order, since fixing a downstream layer when an upstream one is broken wastes effort.

## Method

1. **Deliverability**: bounce rate should be <2%, spam complaints <0.1%. If either is elevated, everything downstream is unreliable — this is the fix, stop here.
2. **Open rate** vs. the stage benchmark (welcome 50-60%, activation 35-45%, nurture 20-30%, win-back 12-20% — use internal trailing data if available). If deliverability passed but open is below benchmark, the issue is subject/sender/timing, not content.
3. **Click rate among those who opened** vs. benchmark. If open rate is fine but this is low, the issue is body content/CTA.

Also check the stage's actual success metric (activation rate, reactivation rate) separately from open/click — high engagement with no lifecycle outcome is a content-relevance problem.

## If information is missing

Ask for: the lifecycle stage, send metrics (sent, bounced, spam complaints, opened, clicked), and the stage success metric with its benchmark if known.

## Output

Pass/fail at each layer in order, the first failing layer as the diagnosis, and a recommendation scoped to that layer only (don't recommend content changes if the failure is deliverability or open).

## Common failure patterns to avoid

- Optimizing subject lines when deliverability is actually the problem.
- Comparing a win-back program's metrics to a welcome-series benchmark.
- Judging only by open/click instead of the stage's actual lifecycle outcome metric.

## Output format

When the caller needs machine-readable output (an API, a pipeline, or an explicit request for JSON), return a single JSON object that validates against [`schema.json`](schema.json) in this skill's folder: every field it lists, no extra fields. Otherwise, present the same fields as a readable summary.

## Reference

Full methodology and worked example: [`b2b-agent-skills-marketing/skills/lifecycle-email-optimizer/README.md`](../../../b2b-agent-skills-marketing/skills/lifecycle-email-optimizer/README.md)
