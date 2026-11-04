# GTM checkup

An honest scorecard of your go-to-market in about five minutes. Start here.

```bash
b2b-skills checkup yourcompany.com --docs ./gtm-files --provider claude-code
```

It works from three kinds of input, and the more you give it, the less it has to guess: your answers to ten questions, the documents you already have, and your website.

## What it asks

Ten questions, any of which you can skip:

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

To answer them once in a file instead: `--answers answers.json` (`{"q1": "...", "q2": "..."}`) or a text file with lines like `q2: Mid-market fintech...`.

## Point it at your documents

`--docs` takes files or folders. Each file is recognized by what's in it, not its name:

| You have | It reads it as | What it computes, in code |
|---|---|---|
| a CRM deal export (HubSpot, Pipedrive, Salesforce CSV/XLSX) | deal export | win rate on closed deals, median deal size and sales cycle, lost reasons, won deals by source; open pipeline and how many deals are overdue or silent |
| a lead sheet (Apollo, Clay, LinkedIn, your own spreadsheet) | lead sheet | lead-source mix, top industries, titles, company sizes |
| a customer list with won/lost or customer/prospect | customer list | which attributes are over-represented among customers (lift), and which never convert |
| Sean Ellis survey responses | PMF survey | the very-disappointed share, then the full `pmf-survey-analyzer` |
| call notes, transcripts, win/loss interviews, pricing docs (TXT, MD, VTT, SRT, DOCX, HTML) | notes | used as text |
| your pitch deck (PPTX, or PDF with `pip install 'b2b-agent-skills[docs-reader]'`) | deck | used as text |

Numbers from spreadsheets are computed in code and written as plain sentences ("Win rate on closed deals: 9 of 31 (29%)."), so the model quotes them and can't invent them. Where a document and an answer disagree, the document wins. Every score says which file it came from, and the report lists what was read and what was skipped. Try it on the sample files: `b2b-skills checkup --docs examples/demo/docs --no-questions`.

Documents alone are enough for a GTM score: answers and documents are both your side of the story.

## What it scores

| Area | Owner | Scored from | Method |
|---|---|---|---|
| ICP | CMO | your answers, customer list, deal export, + what your site says | `gtm-founder-diagnostic`, `gtm-website-audit` |
| Product-market fit | Strategy | your answers, customer call notes, a Sean Ellis survey | `gtm-founder-diagnostic`, `pmf-survey-analyzer` |
| Positioning & messaging | CMO | your website | Dunford components, swap test, message clarity rubric |
| Proof | CMO | your website | customer evidence, quantified results, credibility |
| Demand & channels | Growth | your answers, lead sheet, deal sources | repeatable channel, source mix, beyond the founder's network |
| Pricing & value | Strategy | your answers, deal sizes, pricing notes | value-based pricing, deal size vs. motion, discount discipline |
| Sales motion | Head of Sales | your answers, deal export (win rate, cycle) | defined process, qualification, known win rate and cycle |
| Pipeline & RevOps | RevOps | your answers, deal export (open deals) | coverage vs. win rate, CRM, next steps |

## How it stays honest

- **Every point is quoted.** A point from your answers quotes your words, a point from a document quotes the document, and a point from your site quotes the page. Code checks that every quote is really there; points it can't verify are removed.
- **Unknown is not zero.** A question you skipped leaves that criterion out instead of counting it as a failure. An area with nothing to go on is shown as unknown, with what would unlock it.
- **One fact can't make an area strong.** An area scored from a single answered criterion, or entirely from one call note or deck, is labeled provisional and capped at 60.
- **No GTM score from a website alone.** With only a website you get a *website score*, clearly labeled. The GTM score needs your answers or documents for at least three areas.
- **Code does the math.** Rubric points, area scores, the overall score, and the order of fixes are computed in code. Suggested fixes come from the skills' outputs and can't contain numbers that aren't in your answers, your documents, or on your site (a number must appear whole, with its "$" and its unit).

## What you get

- a score and finding per area, with who owns it on a GTM team
- the biggest risk, in one sentence
- the **top 3 fixes** for your weakest areas, each with the next command or playbook
- "unlock the rest": what to answer or upload to score the unknown areas
- the evidence behind every score

Inside a workspace (`b2b-skills init`), it's saved to `gtm/checkups/<date>.md`, so you can re-run it monthly and watch the score move.

## Options

| Flag | What it does |
|---|---|
| `--answers FILE` | answers to the 10 questions (JSON or `qN:` lines) instead of asking |
| `--docs PATH ...` | files or folders: deal exports, lead sheets, customer lists, surveys, notes, decks |
| `--website-only` | skip the questions (website score only) |
| `--text FILE` | homepage text from a file, for sites that render with JavaScript |
| `--survey FILE` | Sean Ellis PMF survey responses (CSV); also detected in `--docs` |
| `--pipeline FILE` | open deals export (CSV); also detected in `--docs` |
| `--competitor NAME` | a main competitor, for the swap test (repeatable) |
| `--brief` | print the scorecard and fixes only (the saved report keeps the evidence) |
| `--json` | the full result as JSON |

In Claude Code, ask "run a GTM checkup on my company": the `checkup` skill in the plugin asks the same questions, reads the files you point to, and builds the same scorecard.
