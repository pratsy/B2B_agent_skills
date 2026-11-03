# Sales Handoff Quality Auditor

Score the completeness of context transferred at a handoff point (SDR→AE, AE→Customer Success/Implementation) against an explicit required-field checklist, and correlate handoff quality with downstream outcomes — instead of a subjective "handoffs feel sloppy" complaint.

## When to use this

- Deals stall or accounts churn early post-sale, and you suspect information loss at a handoff, not a product or fit problem.
- SDRs and AEs (or AEs and CS) disagree about whose responsibility a dropped detail was.
- You want evidence, not anecdote, before mandating a new handoff process or template.

## Methodology

Define the required context fields for each handoff type — these should reflect what the *receiving* role actually needs to be effective immediately, not everything the sending role happens to know:

**SDR → AE handoff**, typical required fields: qualification evidence (BANT/MEDDPICC basics gathered), stated pain in the buyer's words, known stakeholders and roles, objections already raised, competitive context if mentioned, timeline/urgency signal.

**AE → CS/Implementation handoff**, typical required fields: promises made during the sales cycle (explicit or implied), success criteria the buyer defined, key stakeholders and their roles (see [`stakeholder-map-builder`](../../../b2b-agent-skills-sales/skills/stakeholder-map-builder/README.md)), known risks or reservations raised pre-close, technical requirements or constraints discussed.

## Scoring model

```
Handoff Completeness Score (0-100) = (required fields present with substantive content / total required fields) x 100

"Present with substantive content" excludes placeholder text (e.g. "n/a", "tbd", a single generic word) -
count only fields with information the receiving role could actually act on.

Handoff Quality Band:
  90-100  Excellent
  70-89   Adequate - minor gaps
  50-69   Poor - likely to cause early friction
  <50     Failed handoff - receiving role is starting effectively blind
```

**Outcome correlation** (run periodically, not per-handoff): compare Handoff Completeness Score distribution against downstream outcomes (SDR→AE: SQL-to-opportunity conversion; AE→CS: 90-day churn or time-to-value) to confirm which specific missing fields actually predict downstream problems, rather than assuming all fields matter equally.

## Inputs

| Field | Type | Example |
|---|---|---|
| `handoff_type` | enum | `sdr_to_ae \| ae_to_cs` |
| `handoff_fields` | list[{field, content}] | the actual handoff notes/fields as submitted |
| `required_fields` | list[string] | the checklist for this handoff type |

## Worked example

AE → CS handoff for a closed-won deal. Required fields: promises made, success criteria, stakeholders, pre-close risks, technical requirements (5 fields).

Submitted: promises made = "n/a" (placeholder, doesn't count); success criteria = "reduce forecast variance by 20% within 2 quarters, per CFO" (substantive); stakeholders = "J. Alvarez (EB), M. Chen (champion)" (substantive); pre-close risks = missing entirely; technical requirements = "Salesforce integration required, SSO via Okta" (substantive).

```
Handoff Completeness = 3 substantive of 5 required = 60% → Poor band
```

Missing/placeholder fields flagged specifically: "promises made" (placeholder only) and "pre-close risks" (missing). Recommendation: CS should not begin onboarding without first getting these two fields directly from the AE — starting implementation without knowing what was promised or what risks were raised pre-close is the specific pattern most likely to produce an early-churn surprise.

## Common failure patterns

- Scoring a field as complete because it's non-empty, without checking for placeholder/non-substantive content ("n/a," "will follow up") — this significantly overstates real handoff quality.
- Auditing handoffs individually without periodically checking which specific missing fields actually correlate with downstream problems — not all fields carry equal risk, and treating them as equal wastes enforcement effort on low-impact gaps.
- Defining the required-field checklist from the sending role's perspective ("what I usually write down") instead of the receiving role's actual needs.
- Auditing only at handoff time and never re-checking whether process changes (new template, new training) actually moved the completeness score over time.

## Output schema

```json
{
  "handoff_type": "ae_to_cs",
  "fields_scored": [
    {"field": "promises_made", "status": "placeholder_only"},
    {"field": "success_criteria", "status": "substantive"},
    {"field": "stakeholders", "status": "substantive"},
    {"field": "pre_close_risks", "status": "missing"},
    {"field": "technical_requirements", "status": "substantive"}
  ],
  "completeness_score": 60,
  "quality_band": "poor",
  "critical_gaps": ["promises_made", "pre_close_risks"],
  "recommended_action": "CS should get promises_made and pre_close_risks directly from the AE before onboarding kickoff"
}
```

## Recommended prompt

> You are a RevOps process analyst. Given the handoff type, required fields checklist, and submitted handoff content below, score each field as substantive, placeholder_only, or missing (placeholder content like "n/a" or "tbd" does not count as substantive). Compute Handoff Completeness Score = substantive fields / total required fields x 100, and assign a quality band. List the critical gaps specifically and recommend what the receiving role should get before proceeding. Return JSON matching the schema above.

## Grounded in

Handoff-quality auditing as practiced in RevOps process governance, scored against a receiving-role-defined required-field checklist so completeness reflects what the next team actually needs, not what the sending team happens to record.

See [sources-and-frameworks.md](../../sources-and-frameworks.md) for the pack's general reference list.
