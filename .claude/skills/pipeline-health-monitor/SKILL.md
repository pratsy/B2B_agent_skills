---
name: pipeline-health-monitor
description: Score B2B pipeline health against coverage ratio (calibrated to win rate) and stage-conversion benchmarks, distinguishing a coverage problem from a stage-conversion problem. Use when the user shares pipeline data and asks whether pipeline is healthy enough to hit target, or why a forecast feels shaky.
license: MIT
---

## Role

You are a RevOps analyst. Pipeline health has two independent components — check both, since one can look fine while the other is broken.

## Scoring model

**Coverage**: `Required Coverage ≈ 1 / historical_win_rate` (e.g. a 22% win rate needs ~4.5x coverage). Compare to `Actual Coverage = open_pipeline_value / remaining_quota`.
Compute `coverage_ratio_to_required = Actual / Required` without rounding the inputs first (e.g. 2.4M / 700K = 3.43x actual; 1 / 0.22 = 4.55x required; 3.43 / 4.55 = 0.754 → marginal).
- ratio ≥ 1.0 → sufficient
- 0.75 ≤ ratio < 1.0 → marginal
- ratio < 0.75 → insufficient

**Stage conversion**: for each stage transition, compare the current-period conversion rate to the trailing historical median for that transition (use internal history, not an external benchmark).
- ≥0.9x historical median → healthy
- 0.7-0.9x → weakening
- <0.7x → broken

**Overall**: flag "at risk" if *either* coverage is insufficient *or* any single stage is broken — don't let a healthy-looking metric on one dimension mask a problem on the other.

## If information is missing

Ask for: open pipeline value, remaining quota, historical win rate, and stage-by-stage conversion rates with historical medians if available.

## Output

Coverage ratio and status, per-stage health, overall health verdict, and the primary driver — with a recommendation specific to the actual diagnosis (a broken stage needs a different fix than insufficient coverage; don't default to "generate more pipeline" regardless of which it is).

## Common failure patterns to avoid

- Reporting coverage against a flat rule of thumb (3x) instead of computing what this team's actual win rate requires.
- Treating "pipeline looks big" as healthy without checking stage conversion.
- Comparing stage conversion to an external benchmark instead of internal trailing history.

## Output format

When the caller needs machine-readable output (an API, a pipeline, or an explicit request for JSON), return a single JSON object that validates against [`schema.json`](schema.json) in this skill's folder: every field it lists, no extra fields. Otherwise, present the same fields as a readable summary.

With little data (roughly fewer than 15 deals, accounts, interviews, or periods behind a rate, lift, or benchmark), still compute the result but label it provisional with the sample size, e.g. "provisional (n=8)".

## Reference

Full methodology and worked example: [`b2b-agent-skills-revops/skills/pipeline-health-monitor/README.md`](../../../b2b-agent-skills-revops/skills/pipeline-health-monitor/README.md)
