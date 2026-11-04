# GTM Website Audit

Score how well a startup's website does its go-to-market job on four dimensions: does it say who it's for (ICP clarity), does it position the product against a real alternative (positioning), could a competitor say the same thing (differentiation), and does it back its claims (proof). Every point awarded must quote the site, so the score reflects what a buyer actually reads, not what the founder meant.

## When to use this

- Before a launch, a fundraise, or an outbound push: the homepage is the first thing every prospect and investor sees.
- When the site gets traffic but few demo requests, and you need to know which part of the story is missing.
- As the first step of a GTM checkup, when the website is the only data you have.

## Methodology

The rubrics operationalize April Dunford's positioning components (*Obviously Awesome*, 2019): target customer, competitive alternative, unique attributes, value, and market category. They add a differentiation "swap test" (could a named competitor put their logo on this headline?) and a proof check (customer evidence, quantified results, third-party credibility). Each criterion is scored on a fixed scale with partial credit, and **any non-zero score must cite a verbatim quote from the page**. A criterion with no supporting text scores 0.

## Scoring model

```
ICP clarity (0-100)
  target_customer_named     0 / 15 / 30   company type, industry, or size the product is for
  buyer_role_named          0 / 10 / 20   the role that buys or uses it
  problem_or_trigger_named  0 / 15 / 30   a specific pain or event, not a generic benefit
  focus_or_exclusion        0 / 10 / 20   narrows the audience (a segment focus, or who it's not for)

Positioning (0-100)
  category_clear            0 / 10 / 20   a category a buyer would recognize
  alternative_addressed     0 / 10 / 20   the status quo or a competitor it replaces
  unique_attributes_stated  0 / 10 / 20   what the product has that alternatives don't
  value_concrete            0 / 10 / 20   an outcome, not a feature
  value_tied_to_customer    0 / 10 / 20   the outcome is for the named customer

Differentiation (0-100)
  swap_test                 0 / 20 / 40   0 = any competitor could say the headline; 40 = only this product could
  differentiators_specific  0 / 15 / 30   a mechanism or capability, not adjectives
  differentiators_provable  0 / 15 / 30   each differentiator is backed on the page

Proof (0-100)
  customer_evidence         0 / 15 / 30   logos, named customers, testimonials
  quantified_results        0 / 20 / 40   numbers from customers (time saved, % improved)
  third_party_credibility   0 / 15 / 30   case studies, reviews, security/compliance, press

Area score = sum of its criteria (partial credit allowed only at the listed values).
Bands: 80-100 strong · 60-79 decent · 40-59 weak · <40 missing
```

## Inputs

| Field | Type | Example |
|---|---|---|
| `website` | string | `"northwind.example"` |
| `page_text` | string | the visible text of the homepage (and pricing/about pages if available) |
| `known_competitors` | list[string] | `["Clari", "spreadsheets"]`, used for the swap test |

## Worked example

Homepage headline "The all-in-one revenue platform", subhead "Our platform empowers revenue teams to unlock their full potential with AI-powered insights", features "Real-time CRM sync · Explainable AI risk scoring · No-code rule builder · 15-minute setup", no customer logos or numbers.

- **ICP clarity 10/100**: "empowers revenue teams" names a buyer group loosely (buyer_role_named 10/20). No company type or size (0), "unlock their full potential" is not a problem or trigger (0), and nothing narrows the audience (0) → **10**.
- **Positioning 30/100**: category "revenue platform" is vague (10/20, "The all-in-one revenue platform"); unique attributes stated (20/20, "Explainable AI risk scoring"); no alternative, no concrete value, no value tied to a customer (0) → **30**.
- **Differentiation 30/100**: swap test fails on the headline (0); "Explainable AI risk scoring" and "15-minute setup" are specific mechanisms (30/30); nothing proves them (0) → **30**.
- **Proof 0/100**: no logos, numbers, or case studies → **0**.

Read: the page names features but not the customer, the problem, or the alternative, and proves nothing. The first fix is a headline that names who it's for and what it replaces; the second is one customer result.

## Common failure patterns

- Scoring what the founder meant instead of what the page says: a criterion without a quote scores 0.
- Giving the swap test partial credit because the product is genuinely different: the test is about the *words*. If a competitor could publish the same headline, it fails.
- Counting adjectives ("powerful", "seamless", "AI-powered") as specific differentiators.
- Treating a logo bar of famous-but-unrelated companies as strong proof for a niche B2B product.

## Output schema

```json
{
  "website": "northwind.example",
  "headline": "The all-in-one revenue platform",
  "icp_clarity": {"score": 10, "items": [{"criterion": "buyer_role_named", "points": 10, "max": 20, "evidence": "empowers revenue teams"}, {"criterion": "target_customer_named", "points": 0, "max": 30, "evidence": ""}]},
  "positioning": {"score": 30, "items": [{"criterion": "category_clear", "points": 10, "max": 20, "evidence": "The all-in-one revenue platform"}, {"criterion": "unique_attributes_stated", "points": 20, "max": 20, "evidence": "Explainable AI risk scoring"}]},
  "differentiation": {"score": 30, "items": [{"criterion": "swap_test", "points": 0, "max": 40, "evidence": ""}, {"criterion": "differentiators_specific", "points": 30, "max": 30, "evidence": "Explainable AI risk scoring"}]},
  "proof": {"score": 0, "items": [{"criterion": "quantified_results", "points": 0, "max": 40, "evidence": ""}]},
  "biggest_gap": "the page never says who it's for or what it replaces"
}
```

## Recommended prompt

> You are a B2B product marketer auditing a startup's website. Score four areas with the rubric above: ICP clarity, positioning (Dunford's components), differentiation (swap test, specificity, provability), and proof. Use only the listed point values. Every non-zero criterion must quote the page verbatim; with no supporting text, score 0. Name the biggest gap in one sentence. Return JSON matching the schema above.

## Grounded in

April Dunford, *Obviously Awesome* (2019): the five components of positioning. The swap test is a common messaging check (would the claim still be true with a competitor's name on it?), also used in `messaging-clarity-auditor`.

See [sources-and-frameworks.md](../../sources-and-frameworks.md) for the pack's general reference list.
