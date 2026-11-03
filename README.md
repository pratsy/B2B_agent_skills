# B2B Agent Skills

[![CI](https://github.com/pratsy/skills-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/pratsy/skills-AI/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/b2b-agent-skills)](https://pypi.org/project/b2b-agent-skills/)
[![Python](https://img.shields.io/pypi/pyversions/b2b-agent-skills)](https://pypi.org/project/b2b-agent-skills/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**An open-source GTM workspace for early-stage B2B teams: sales, marketing, and RevOps.** Point it at what you already have (call notes, your website, lead lists, a customer list, your CRM) and it does the go-to-market work with tested methods instead of generic AI advice.

It runs on your Claude subscription through Claude Code, with no API key needed, or on the Anthropic or OpenAI APIs.

![Demo: running GTM playbooks](docs/assets/demo.gif)

## Start in five minutes

```bash
pip install b2b-agent-skills
b2b-skills init my-gtm --website yourcompany.com     # drafts company.md from your site, asks 10 questions
cd my-gtm
b2b-skills playbook fix-my-message --website yourcompany.com --notes win-loss.md --provider claude-code
```

## Playbooks

Each playbook takes material you already have and returns a one-page answer, saved to your workspace.

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

Beyond the playbooks, any of the 46 skills runs directly on notes, JSON, or a CSV:

| Team | Jobs | Example |
|---|---|---|
| **Marketing** | positioning (Dunford), messaging clarity, landing page message-match, value-prop testing, ad variants with test sample size, nurture sequences, content gaps, campaign diagnosis, ABM tiers | `b2b-skills run landing-page-copy-optimizer --notes page-and-ad.txt` |
| **Product · founder** | product-market fit from a Sean Ellis survey, market sizing (TAM/SAM/SOM), market and competitor signals | `b2b-skills run pmf-survey-analyzer --csv survey.csv` |
| **Sales** | discovery questions (SPIN), objection handling, stakeholder maps, multi-threading plans, negotiation prep, pricing/ROI justification, renewal risk | `b2b-skills run objection-response-coach --notes call.txt` |
| **RevOps** | pipeline health, forecast category and bias, CRM data quality, attribution model sensitivity, handoff quality | `b2b-skills batch crm-data-cleaner opportunities.csv -o cleanup.csv` |

`b2b-skills list --stage early` shows the skills that work with little data; the rest are labeled for when you have a team and history.

## How it stays trustworthy

- **Evidence or nothing.** Facts pulled from your notes must quote them word for word, and the quotes are checked in code. Anything that can't be verified is dropped and turned into a question for you. Reports may not invent proof points, statistics, or social proof, and evals fail if they do.
- **Code does the math.** ICP fit, attribute lift, pipeline flags, and priority order are computed in Python: exact, instant, repeatable. The model does the judgment and the writing.
- **You approve every outside change.** CRM updates wait in `gtm/pending/` until you run `b2b-skills approve`. Emails are drafted, never sent.
- **Tested against real models.** 62 golden cases cover all 46 skills, and the playbooks have their own evals, including anti-hallucination cases. Latest full run on Claude Sonnet 4.5: 65/68 (96%), with the one playbook failure fixed and re-verified ([evals/results/](evals/results/)).
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

## Under the hood: 46 skills

The playbooks and jobs above are built on 46 skills, each a named methodology with an explicit scoring model and a JSON Schema output: MEDDPICC deal risk, SPIN discovery, Dunford positioning, Sean Ellis PMF test, TAM/SAM/SOM, forecast bias, and more.

| Pack | Covers | Skills |
|---|---|---|
| [Sales](b2b-agent-skills-sales/) | deal risk, forecast category, stakeholder maps, discovery, objections, negotiation, pricing/ROI, renewals | 17 |
| [Marketing](b2b-agent-skills-marketing/) | ICP refinement, segmentation, positioning, messaging clarity, campaign diagnostics, ABM, lifecycle, content gaps | 15 |
| [RevOps](b2b-agent-skills-revops/) | pipeline health, forecast bias, CRM data quality, attribution, handoff quality | 5 |
| [GTM](b2b-agent-skills-gtm/) | market sizing, PMF survey analysis, competitor and market signals, strategic accounts, win/loss themes | 9 |

From Python: `run_skill("pipeline-health-monitor", data, provider="anthropic")` ([SDK guide](docs/sdk.md)). Over HTTP: `b2b-skills serve` ([API guide](docs/http-api.md)).

Full documentation: **https://pratsy.github.io/skills-AI/**

## Contributing

The most useful contributions right now are real-world playbook feedback, more golden eval cases, and fixes to skill methodology. See [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md). Report security issues privately ([SECURITY.md](SECURITY.md)).

## License

[MIT](LICENSE)
