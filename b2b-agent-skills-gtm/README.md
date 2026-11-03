# B2B Agent Skills — GTM

Open-source AI playbooks for strategic go-to-market intelligence, competitive awareness, and account prioritization.

## Coverage

- market research
- competitor monitoring
- account prioritization
- strategic account planning
- signal interpretation
- opportunity sizing
- product-market fit measurement

## Featured skills

- competitor-monitor
- win-loss-theme-clusterer
- market-sizing-modeler
- market-trend-signal-reporter
- strategic-account-priority-ranker
- account-priority-matrix-builder
- market-shift-monitor
- competitor-signal-clusterer
- pmf-survey-analyzer

## Standard skill format

Every skill in this library follows the same operational structure — see [`memory/skill-template.md`](../memory/skill-template.md):

- when to use it, in concrete situations
- the named methodology it operationalizes (see below)
- an explicit scoring model or decision rubric, not a narrative description
- an input schema and a fully worked example with real numbers
- an output JSON schema so the skill can be wired into a pipeline, not just pasted as a prompt

## Named methodologies used in this pack

- **TAM/SAM/SOM sizing, reconciled top-down and bottom-up** — `market-sizing-modeler`
- **Sean Ellis 40% product-market-fit test, segmented** — `pmf-survey-analyzer`
- **Frequency/decisiveness/win-rate-delta theme scoring** — `win-loss-theme-clusterer`
- **Move-type taxonomy with overlap/confirmation/pattern materiality scoring** — `competitor-monitor`
- **Strategic-theme clustering with trajectory (accelerating/stable/fading) scoring** — `competitor-signal-clusterer`
- **PESTEL-style categorization with breadth/velocity/durability scoring** — `market-shift-monitor`
- **Signal-to-noise trend confirmation** (independent sources, corroboration types, multi-period) — `market-trend-signal-reporter`
- **Cross-functional value/effort 2x2** — `account-priority-matrix-builder`
- **Multi-criteria strategic value scoring beyond revenue** (reference-ability, market influence, expansion optionality) — `strategic-account-priority-ranker`

Several of these skills look similar to account-scoring skills in the sales and marketing packs — see the comparison table in [`account-priority-matrix-builder`](skills/account-priority-matrix-builder/README.md#how-this-differs-from-similar-sounding-skills) for how they differ by organizational level and decision they answer.

## Research basis

This repo is also informed by public GTM strategy, account prioritization, competitor intelligence, and market research practice, as general background.

## Public source base

- McKinsey Growth & Sales — https://www.mckinsey.com/capabilities/growth-marketing-and-sales
- Gartner Strategy and Market Intelligence resources — https://www.gartner.com/en
- Forrester Research — https://www.forrester.com/
- Salesforce Blog — https://www.salesforce.com/blog/
- HubSpot Blog — https://blog.hubspot.com/
- 6sense and Demandbase public market and ABM intelligence content
- Public competitor intelligence and market research frameworks used in SaaS GTM teams

This repo synthesizes public GTM strategy and market monitoring practice into reusable AI playbooks for strategic intelligence and account prioritization.

## Structure

- `skills/` — GTM-specific agent playbooks

## Focus

This repo helps GTM teams use AI to improve market intelligence and sharper strategic decision-making grounded in practical B2B growth and GTM strategy frameworks.
