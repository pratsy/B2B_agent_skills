# B2B Agent Skills

[![CI](https://github.com/pratsy/B2B_agent_skills/actions/workflows/ci.yml/badge.svg)](https://github.com/pratsy/B2B_agent_skills/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/b2b-agent-skills)](https://pypi.org/project/b2b-agent-skills/)
[![Python](https://img.shields.io/pypi/pyversions/b2b-agent-skills)](https://pypi.org/project/b2b-agent-skills/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Your AI GTM team, before you can hire one.** An open-source tool for early-stage B2B founders across sales, marketing, GTM, and RevOps. It works from what you already have (your answers, your website, call notes, lead lists, your CRM) and does the go-to-market work with tested methods instead of generic AI advice.

It runs on your Claude subscription through Claude Code, with no API key needed, or on the Anthropic or OpenAI APIs.

![Demo: running GTM playbooks](docs/assets/demo.gif)

## Start with a GTM checkup

```bash
pip install b2b-agent-skills
b2b-skills checkup yourcompany.com --provider claude-code
```

Answer 10 quick questions (about 3 minutes) and get an honest scorecard of your go-to-market:

| Area | Owner | What it tells you |
|---|---|---|
| ICP | CMO | do you know exactly who buys, and does your site say so? |
| Product-market fit | Strategy | do customers stay, and would they miss you? |
| Positioning & messaging | CMO | is your story specific, differentiated, and clear? |
| Proof | CMO | do you back your claims? |
| Demand & channels | Growth | is there a repeatable way to get leads? |
| Pricing & value | Strategy | does your price capture value? |
| Sales motion | Head of Sales | are deals run on a process and evidence? |
| Pipeline & RevOps | RevOps | can the pipeline hit the target? |

You get a score per area with the evidence behind it (your words or your site, quoted), the biggest risk, the **top 3 fixes** with the next step for each, and what would unlock any area it can't judge yet. Unknown is never scored as zero. Add a PMF survey (`--survey`) or a pipeline export (`--pipeline`) to go deeper. Re-run it monthly to see the score move.

## Your GTM team

Each role owns a set of methods: 48 skills in all, every one a named methodology with an explicit scoring model.

| Role | What it does for you | Methods it uses |
|---|---|---|
| **CMO** | positioning, messaging, ICP, campaigns, lifecycle, content | Dunford positioning, message clarity rubric, ICP lift, value-prop canvas, ABM tiers |
| **Head of Sales** | discovery, deal risk, objections, stakeholders, negotiation, pricing | SPIN, MEDDPICC, LAER, BATNA, ROI justification |
| **RevOps lead** | pipeline health, forecasting, CRM hygiene, attribution, handoffs | coverage vs. win rate, forecast bias, data-quality scoring, model sensitivity |
| **Strategy advisor** | product-market fit, market size, competitors, win/loss | Sean Ellis 40% test, TAM/SAM/SOM, signal materiality, theme impact |

## Playbooks

When the checkup finds a problem, a playbook fixes it. Run `b2b-skills init my-gtm --website yourcompany.com` first to get a workspace that remembers your company, deals, and every run. Each takes material you already have and returns a one-page answer, saved to your workspace.

| Team | Playbook | Your question | You give it | You get |
|---|---|---|---|---|
| Marketing | **fix-my-message** | "Why isn't our homepage or outbound landing?" | your website, win/loss notes | positioning statement, claim-by-claim scores, rewritten headline, 3 outbound angles, the proof you still need |
| Marketing · GTM | **find-icp** | "Who should we really sell to?" | won/lost account list, interview notes | ICP brief with exact lift numbers, buying trigger, who to avoid, proposed `icp.json` |
| Sales · SDR | **score-list** | "Who do I contact this week?" | a lead CSV (Apollo, Clay, HubSpot, LinkedIn) | every row scored against your ICP; why-now and an opening line for the top 50 |
| Sales | **call-debrief** | "I just had a call. What now?" | a transcript or notes | verdict (MEDDPICC /24), next 3 actions, missing evidence, draft follow-up email |
| RevOps · founder | **monday-review** | "Which deals need attention this week?" | HubSpot, or a pipeline CSV | this week's focus, deals at risk, deals with no evidence; CRM updates proposed for approval |

```bash
b2b-skills playbook find-icp --customers accounts.csv --notes interviews/
b2b-skills playbook score-list --csv leads.csv
b2b-skills playbook call-debrief --notes call.txt
b2b-skills playbook monday-review --hubspot --slack
```

All five also run inside Claude Code through the plugin, and over MCP.

## More jobs, by team

Beyond the playbooks, any of the 48 skills runs directly on notes, JSON, or a CSV:

| Team | Jobs | Example |
|---|---|---|
| **Marketing** | positioning (Dunford), messaging clarity, landing page message-match, value-prop testing, ad variants with test sample size, nurture sequences, content gaps, campaign diagnosis, ABM tiers | `b2b-skills run landing-page-copy-optimizer --notes page-and-ad.txt` |
| **Product · founder** | GTM diagnostic, website audit, product-market fit from a Sean Ellis survey, market sizing (TAM/SAM/SOM), market and competitor signals | `b2b-skills run pmf-survey-analyzer --csv survey.csv` |
| **Sales** | discovery questions (SPIN), objection handling, stakeholder maps, multi-threading plans, negotiation prep, pricing/ROI justification, renewal risk | `b2b-skills run objection-response-coach --notes call.txt` |
| **RevOps** | pipeline health, forecast category and bias, CRM data quality, attribution model sensitivity, handoff quality | `b2b-skills batch crm-data-cleaner opportunities.csv -o cleanup.csv` |

`b2b-skills list --stage early` shows the skills that work with little data; the rest are labeled for when you have a team and history.

## How it stays trustworthy

- **Evidence or nothing.** Facts pulled from your notes must quote them word for word, and the quotes are checked in code. Anything that can't be verified is dropped and turned into a question for you. Reports may not invent proof points, statistics, or social proof, and evals fail if they do.
- **Code does the math.** ICP fit, attribute lift, pipeline flags, and priority order are computed in Python: exact, instant, repeatable. The model does the judgment and the writing.
- **You approve every outside change.** CRM updates wait in `gtm/pending/` until you run `b2b-skills approve`. Emails are drafted, never sent.
- **Tested against real models.** 64 golden cases cover all 48 skills, and the playbooks have their own evals, including anti-hallucination cases. Latest full run on Claude Sonnet 4.5: 65/68 (96%), with the one playbook failure fixed and re-verified ([evals/results/](evals/results/)).
- **Honest about small samples.** Results built on a handful of deals are labeled "provisional (n=8)".

## Your workspace

```
my-gtm/
  company.md                 what you sell, to whom, against whom (added to every run)
  CLAUDE.md                  rules for an agent working here (Claude Code reads it)
  gtm/
    icp.json                 your ICP, used to score lists
    deals/<deal>.md          every debrief, with the raw notes
    inbox/                   drop call transcripts here; `b2b-skills inbox` debriefs them
    lists/  reviews/         scored lists, weekly reviews
    pending/                 proposed CRM changes waiting for approval
    outcomes.csv             won/lost outcomes (`b2b-skills outcome`)
    runs/                    a log of every run
  .github/workflows/gtm-weekly.yml   optional: every Monday, debrief the inbox and review the pipeline
```

Everything is plain files: readable, editable, and versioned in git. Open the folder in Claude Code and it becomes an agent that works with all of it.

## Connect your tools

| Tool | How |
|---|---|
| **HubSpot** | `HUBSPOT_ACCESS_TOKEN` (private app). `b2b-skills hubspot setup` adds the write-back fields; `monday-review --hubspot` reads deals and proposes updates |
| **Call recorders** (Fathom, Granola, Gong, Otter, Zoom) | drop or forward transcripts into `gtm/inbox/`, or POST them to the webhook `POST /v1/playbooks/call-debrief/run` |
| **Slack** | `SLACK_WEBHOOK_URL`, then `--slack` on `inbox` and `monday-review` |
| **Lead lists** (Apollo, Clay, LinkedIn exports) | `score-list --csv`; common column names are recognized, `--map field=Column` for the rest |
| **Claude Desktop, Cursor** | `b2b-skills mcp` as an MCP server ([guide](docs/mcp.md)) |

## Under the hood: 48 skills

The playbooks and jobs above are built on 48 skills, each a named methodology with an explicit scoring model and a JSON Schema output: MEDDPICC deal risk, SPIN discovery, Dunford positioning, Sean Ellis PMF test, TAM/SAM/SOM, forecast bias, and more.

| Pack | Covers | Skills |
|---|---|---|
| [Sales](b2b-agent-skills-sales/) | deal risk, forecast category, stakeholder maps, discovery, objections, negotiation, pricing/ROI, renewals | 17 |
| [Marketing](b2b-agent-skills-marketing/) | ICP refinement, segmentation, positioning, messaging clarity, campaign diagnostics, ABM, lifecycle, content gaps | 15 |
| [RevOps](b2b-agent-skills-revops/) | pipeline health, forecast bias, CRM data quality, attribution, handoff quality | 5 |
| [GTM](b2b-agent-skills-gtm/) | GTM diagnostic, website audit, market sizing, PMF survey analysis, competitor and market signals, strategic accounts, win/loss themes | 11 |

From Python: `run_skill("pipeline-health-monitor", data, provider="anthropic")` ([SDK guide](docs/sdk.md)). Over HTTP: `b2b-skills serve` ([API guide](docs/http-api.md)).

Full documentation: **https://pratsy.github.io/B2B_agent_skills/**

## Contributing

The most useful contributions right now are real-world playbook feedback, more golden eval cases, and fixes to skill methodology. See [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md). Report security issues privately ([SECURITY.md](SECURITY.md)).

## License

[MIT](LICENSE)
