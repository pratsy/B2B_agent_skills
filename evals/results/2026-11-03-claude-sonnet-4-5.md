# Golden eval run: 2026-11-03, Claude Sonnet 4.5 via Claude Code

- **Command:** `b2b-skills eval --provider claude-code --concurrency 4` (Claude subscription, no API key)
- **Model:** `claude-sonnet-4-5-20250929`
- **Result:** 59/60 cases (98%) across all 45 skills
- **Follow-up:** the one failure (`account-plan-generator` / `big-cold-still-wins`, sorting by warmth instead of priority score) was fixed in its SKILL.md. Both ranking skills then passed 3 of 3 repeat runs.

History on the same day while the skills were being fixed: 32/60 → 58/60 → 59/60. See CHANGELOG for what changed.

**59/60 cases passed (98%)**

| Skill | Case | Result | Assertions | Notes |
|---|---|---|---|---|
| `abm-account-priority-ranker` | reachable-but-small | ✅ | 4/4 |  |
| `abm-account-priority-ranker` | valuable-but-cold | ✅ | 3/3 |  |
| `account-plan-generator` | relationship-beats-size | ✅ | 5/5 |  |
| `account-plan-generator` | big-cold-still-wins | ❌ | 2/3 | whitespace_ranked[0].business_unit: expected 'Finance', got 'Support' |
| `account-priority-matrix-builder` | invest-in-fintech | ✅ | 3/3 |  |
| `ad-copy-variant-generator` | three-structures-and-sample-size | ✅ | 6/6 |  |
| `attribution-model-reviewer` | middle-touch-channel | ✅ | 6/6 |  |
| `audience-segmentation-optimizer` | meridian-full-icp-match | ✅ | 7/7 |  |
| `brand-perception-monitor` | known-not-chosen | ✅ | 3/3 |  |
| `brand-positioning-synthesizer` | winnable-segment-over-big-segment | ✅ | 4/4 |  |
| `campaign-performance-diagnostician` | volume-not-conversion | ✅ | 4/4 |  |
| `champion-advocacy-builder` | confirmed-mobilizer | ✅ | 7/7 |  |
| `champion-advocacy-builder` | friendly-talker | ✅ | 2/2 |  |
| `competitive-differentiation-coach` | tier1-matches-priority | ✅ | 3/3 |  |
| `competitive-differentiation-coach` | priority-beats-tier | ✅ | 2/2 |  |
| `competitor-monitor` | overlapping-product-launch | ✅ | 3/3 |  |
| `competitor-monitor` | unconfirmed-rumor | ✅ | 2/2 |  |
| `competitor-signal-clusterer` | accelerating-plg-theme | ✅ | 6/6 |  |
| `content-gap-analysis-agent` | cfo-has-nothing | ✅ | 4/4 |  |
| `crm-data-cleaner` | stale-zero-amount-deal | ✅ | 6/6 |  |
| `crm-data-cleaner` | old-closed-record | ✅ | 2/2 |  |
| `customer-journey-friction-audit` | form-beats-pricing-page | ✅ | 3/3 |  |
| `deal-committee-readiness-coach` | prep-needed | ✅ | 4/4 |  |
| `deal-committee-readiness-coach` | not-ready | ✅ | 3/3 |  |
| `deal-risk-assessor` | strong-pain-unconfirmed-eb | ✅ | 8/8 |  |
| `discovery-question-generator` | spin-sequence | ✅ | 4/4 |  |
| `executive-briefing-builder` | cfo-budget-approval | ✅ | 4/4 |  |
| `executive-sponsor-identifier` | authority-over-engagement | ✅ | 5/5 |  |
| `forecast-bias-detector` | consistent-sandbagger | ✅ | 5/5 |  |
| `forecast-bias-detector` | noisy-not-biased | ✅ | 2/2 |  |
| `forecast-confidence-model` | qualified-but-stalled | ✅ | 5/5 |  |
| `forecast-confidence-model` | stalled-past-3x | ✅ | 2/2 |  |
| `icp-refinement-agent` | revops-assumption-contradicted | ✅ | 4/4 |  |
| `landing-page-copy-optimizer` | message-mismatch-first | ✅ | 3/3 |  |
| `lead-prioritization-agent` | high-fit-demo-request | ✅ | 4/4 |  |
| `lead-prioritization-agent` | high-fit-no-engagement | ✅ | 4/4 |  |
| `lifecycle-email-optimizer` | open-layer-failure | ✅ | 6/6 |  |
| `market-shift-monitor` | regulatory-structural | ✅ | 2/2 |  |
| `market-shift-monitor` | single-data-point-noise | ✅ | 2/2 |  |
| `market-sizing-modeler` | top-down-bottom-up-divergence | ✅ | 6/6 |  |
| `market-trend-signal-reporter` | derivative-coverage | ✅ | 4/4 |  |
| `market-trend-signal-reporter` | confirmed-trend | ✅ | 2/2 |  |
| `messaging-clarity-auditor` | generic-headline | ✅ | 3/3 |  |
| `multi-threading-plan-builder` | brokered-before-cold | ✅ | 4/4 |  |
| `negotiation-readiness-coach` | lead-with-high-ratio | ✅ | 4/4 |  |
| `nurture-sequence-architect` | engagement-branched | ✅ | 3/3 |  |
| `objection-response-coach` | ambiguous-budget | ✅ | 3/3 |  |
| `objection-response-coach` | value-gap-confirmed | ✅ | 3/3 |  |
| `persona-insight-extractor` | frequency-threshold | ✅ | 4/4 |  |
| `pipeline-health-monitor` | marginal-coverage-broken-stage | ✅ | 7/7 |  |
| `pricing-justification-builder` | roi-below-one | ✅ | 5/5 |  |
| `pricing-justification-builder` | unsourced-improvement | ✅ | 3/3 |  |
| `renewal-risk-scorer` | champion-departed-usage-decline | ✅ | 5/5 |  |
| `sales-handoff-quality-auditor` | placeholder-and-missing | ✅ | 6/6 |  |
| `stakeholder-map-builder` | assumed-eb | ✅ | 4/4 |  |
| `stakeholder-map-builder` | single-threaded | ✅ | 2/2 |  |
| `strategic-account-priority-ranker` | reference-beats-revenue | ✅ | 4/4 |  |
| `territory-prioritization-agent` | big-cold-vs-small-warm | ✅ | 5/5 |  |
| `value-proposition-tester` | specific-beats-generic | ✅ | 3/3 |  |
| `win-loss-theme-clusterer` | decisive-beats-frequent | ✅ | 6/6 |  |
