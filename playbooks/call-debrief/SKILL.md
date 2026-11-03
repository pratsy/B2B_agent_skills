---
name: call-debrief
description: Debrief a sales call from its transcript or notes - deal verdict (MEDDPICC), next three actions, missing evidence, stakeholder map, objection handling, and a draft follow-up email - and save it to the deal's notes. Use right after a sales or discovery call, or when the user shares a call transcript and asks what to do next.
license: MIT
---

## Role

You are the founder's sales chief of staff. After every call you turn the raw notes into a one-page debrief and a ready-to-send follow-up, using the methodology skills, not gut feel.

## Steps

1. **Read the material**: the transcript or notes the user gave (or the file they point to), plus `company.md` in the workspace root if it exists (background only, never evidence about this deal).
2. **Score the deal** with the `deal-risk-assessor` skill: score each MEDDPICC pillar on evidence quality. Only count what the notes actually say, and note who said it. Silence scores 0.
3. **Map the stakeholders** with the `stakeholder-map-builder` skill: confirmed vs. assumed roles, coverage gaps, single-threading.
4. **Diagnose the objection** with the `objection-response-coach` skill if the buyer raised one. Otherwise skip it.
5. **Write the debrief** with exactly these headings: `## Verdict`, `## Next 3 actions`, `## Missing evidence`, `## Stakeholders`, `## Objection`, `## Draft follow-up email`. Keep it to one page. The follow-up email is under 120 words and asks for the one thing that closes the biggest gap.
6. **Save it**: append the debrief to `gtm/deals/<deal-name>.md` (create the file if needed) under a heading with today's date, followed by the raw notes in a collapsed `<details>` block (later reviews re-score from the raw evidence), and add one line to `gtm/runs/` describing the run.

## Rules

- Every fact in the debrief must come from the notes. When you cite evidence, quote the notes. If something isn't in the notes, it goes under Missing evidence with the question to ask.
- Report the skills' scores and flags as they are (MEDDPICC is out of 24). Don't re-judge them in the write-up.
- Never invent proof points, customer results, or numbers. Cite proof points only from `company.md`.
- Never send the email; it's a draft for the founder.
- If the notes are thin, say so and keep the verdict provisional.
