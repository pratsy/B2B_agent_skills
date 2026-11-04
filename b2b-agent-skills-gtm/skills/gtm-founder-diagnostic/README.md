# GTM Founder Diagnostic

Score an early-stage B2B company's go-to-market from the founder's own answers to ten questions: ICP, product-market fit, demand and channels, pricing, sales motion, and pipeline. It's the conversation a fractional CMO or VP Sales has in their first meeting, scored on explicit rubrics and quoting the founder's words, so the gaps are specific, not "work on your GTM".

## When to use this

- A founder wants an honest read on their GTM before hiring a first sales or marketing person, raising, or changing strategy.
- As the core of a GTM checkup, together with a website audit and whatever data the company has.
- Quarterly, to see whether the GTM is getting more repeatable.

## Methodology

Ten questions cover what decides early-stage GTM: who buys and why, whether they stay, where demand comes from, how pricing captures value, how deals are run, and whether the pipeline can hit the target. Each area has three criteria scored on fixed values. A criterion is **answered** only if the evidence field quotes the founder's answer, even when the score is 0 ("we don't track win rate" is an answer). An area with no answered criteria is **unknown**, not 0: a missing answer is a gap in the data, not proof of a gap in the company.

The ten questions:

1. What stage are you at, and how many paying customers do you have?
2. Who are your best customers, and why did they buy?
3. Who churned or never converted, and why?
4. Where do your leads and customers come from today?
5. What happens from first conversation to signed deal, and who sells?
6. Roughly what's your win rate and sales cycle?
7. How do you price, what's a typical deal size, and how often do you discount?
8. Are customers staying and expanding? How do you know they'd miss you?
9. What's in your open pipeline versus this quarter's target?
10. What's your biggest GTM headache right now?

## Scoring model

```
ICP (0-100)
  best_customer_pattern        0 / 20 / 40   a consistent profile across best customers (type, size, role)
  buying_trigger_known         0 / 15 / 30   a specific reason or event that made them buy
  loss_reasons_known           0 / 15 / 30   knows why others churned or didn't buy

Product-market fit (0-100)
  retention                    0 / 20 / 40   customers stay and expand, with evidence
  pull_signals                 0 / 15 / 30   inbound demand, referrals, customers asking for more
  must_have_evidence           0 / 15 / 30   evidence users would be upset without it

Demand & channels (0-100)
  repeatable_channel           0 / 20 / 40   at least one channel that reliably produces qualified leads
  source_mix_known             0 / 15 / 30   knows where leads come from, ideally with numbers
  beyond_founder_network       0 / 15 / 30   not dependent only on the founder's network

Pricing & value (0-100)
  value_based                  0 / 15 / 30   price tied to the customer's value or ROI
  deal_size_fits_motion        0 / 15 / 30   deal size can pay for how the deal is sold
  discount_discipline          0 / 20 / 40   rarely discounts, or only in exchange for something

Sales motion (0-100)
  defined_process              0 / 15 / 30   clear steps from first call to signature
  qualification                0 / 15 / 30   qualifies on pain, decision maker, budget, timing
  metrics_known                0 / 20 / 40   knows win rate and cycle length

Pipeline & RevOps (0-100)
  coverage                     0 / 20 / 40   open pipeline covers the target given the win rate (about 1 / win rate)
  tracked_in_crm               0 / 15 / 30   deals live in a CRM, not memory or spreadsheets
  next_steps_on_deals          0 / 15 / 30   deals have dated next steps and a regular review

Area score = points from answered criteria ÷ the max of the answered criteria × 100
(unanswered criteria don't count for or against the founder)
If only one criterion in an area is answered, the area is provisional and capped at 60:
one fact can't make an area strong
Bands: 80-100 strong · 60-79 decent · 40-59 weak · <40 missing · no answered criteria = unknown
```

### Documents as evidence

When the founder shares documents, they answer criteria just as the questions do, and often better: a CRM export's win rate beats "maybe a third". Evidence may quote the answers or any document word for word. Spreadsheets arrive as sentences computed in code ("Lead source: Referral 41 of 60 (68%)"), so quote those sentences and never recompute or extrapolate them. Where a document and an answer disagree, score the document and say so in the fix. A document can answer a criterion even if the founder skipped the question; a document that doesn't mention a criterion leaves it unanswered. A lead sheet or deal list kept in a spreadsheet is evidence for `source_mix_known` or `metrics_known`, but not for `tracked_in_crm` unless it says it came from a CRM.

## Inputs

| Field | Type | Example |
|---|---|---|
| `answers` | object | question number → the founder's answer, e.g. `{"q2": "Mid-market fintech RevOps leads; they bought after a bad forecast miss"}` |
| `stage` | string | `"first customers"`, `"repeatable"`, `"scaling"` (optional; from q1) |
| `documents` | array | files the founder shared, each `{"name", "kind", "text"}`: lead sheets, deal exports, customer lists, call notes, decks. Spreadsheets arrive already summarized in code, e.g. `{"name": "deals.csv", "kind": "deal export", "text": "Win rate on closed deals: 9 of 31 (29%)."}` (optional) |

## Worked example

A seed-stage founder answers: 12 paying customers; best customers are "mid-market fintech companies, the VP Sales buys after a forecast miss in front of the board"; churned "two agencies who never set it up"; leads come "mostly from my network and a few LinkedIn posts"; "I run every call, no set process"; win rate "no idea, maybe a third", cycle "about 6 weeks"; price "$500/month flat, I discount for almost everyone"; "11 of 12 renewed"; pipeline "maybe $40K, target is $60K this quarter".

- **ICP 85**: consistent pattern (40, "mid-market fintech companies"), trigger known (30, "after a forecast miss in front of the board"), loss reason partly known (15, "two agencies who never set it up").
- **Product-market fit 55**: strong retention (40, "11 of 12 renewed"); pull and must-have evidence answered but weak (15, 0).
- **Demand & channels 15**: no repeatable channel (0, "mostly from my network"), source mix roughly known (15), dependent on the founder network (0).
- **Pricing 15**: flat price not tied to value (0, "$500/month flat"), small deal size for a founder-run 6-week cycle (15), discounts for almost everyone (0).
- **Sales motion 29**: no defined process (0, "I run every call, no set process"), metrics roughly known (20, "maybe a third", "about 6 weeks"); qualification wasn't described, so it's left out: 20 of 70 answered points.
- **Pipeline 0**: $40K against $60K with about a one-third win rate needs about $180K (0, "maybe $40K, target is $60K"); CRM and next steps weren't described, so they're left out.

Read: strong ICP and retention, so there is a product people keep. The GTM risk is demand and pricing: growth depends on the founder's network, and constant discounting on a low price means every deal costs more founder time than it returns.

## Common failure patterns

- Scoring 0 for unanswered questions: that hides missing data as failure. No quote means unanswered.
- Rewarding confident answers without specifics ("we know our customers well") as if they were evidence.
- Ignoring arithmetic the founder gives: pipeline against target and win rate settles coverage.

## Output schema

```json
{
  "stage": "first customers",
  "icp": {"score": 85, "fix": "write the ICP down and use it to disqualify", "items": [{"criterion": "best_customer_pattern", "points": 40, "max": 40, "evidence": "mid-market fintech companies"}, {"criterion": "loss_reasons_known", "points": 15, "max": 30, "evidence": "two agencies who never set it up"}]},
  "pmf": {"score": 55, "fix": "ask churned and active users the Sean Ellis question", "items": [{"criterion": "retention", "points": 40, "max": 40, "evidence": "11 of 12 renewed"}]},
  "demand": {"score": 15, "fix": "test one channel beyond your network for 30 days", "items": [{"criterion": "repeatable_channel", "points": 0, "max": 40, "evidence": "mostly from my network"}]},
  "pricing": {"score": 15, "fix": "stop default discounting; tie price to the cost of a forecast miss", "items": [{"criterion": "discount_discipline", "points": 0, "max": 40, "evidence": "I discount for almost everyone"}]},
  "sales_motion": {"score": 29, "fix": "write down your stages and qualification questions", "items": [{"criterion": "defined_process", "points": 0, "max": 30, "evidence": "I run every call, no set process"}]},
  "pipeline": {"score": 0, "fix": "build roughly 3x pipeline coverage before the quarter ends", "items": [{"criterion": "coverage", "points": 0, "max": 40, "evidence": "maybe $40K, target is $60K"}]},
  "biggest_risk": "growth depends on the founder's network and discounted, low-priced deals"
}
```

## Recommended prompt

> You are a fractional GTM leader running a first diagnostic with an early-stage B2B founder. Score their answers on the six rubrics above using only the listed values. Every answered criterion must quote the founder's words in evidence, even when it scores 0; leave unanswered criteria with empty evidence. Give one concrete fix per area grounded in their answers, and name the biggest risk. Return JSON matching the schema above.

## Grounded in

The questions follow the standard first-meeting diagnostic used by fractional GTM leaders. The areas map to this library's methods: ICP to `icp-refinement-agent`, PMF to `pmf-survey-analyzer` (Sean Ellis), pricing to `pricing-justification-builder`, sales motion to MEDDPICC (`deal-risk-assessor`), and pipeline coverage to `pipeline-health-monitor` (coverage of about 1 / win rate).

See [sources-and-frameworks.md](../../sources-and-frameworks.md) for the pack's general reference list.
