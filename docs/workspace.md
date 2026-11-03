# Workspace and connectors

## Create a workspace

```bash
b2b-skills init my-gtm --website yourcompany.com
```

`init` reads your website, drafts answers to ten questions (what you sell, buyers, target companies, buying trigger, alternatives, differentiators, proof points, pricing, sales motion), and lets you confirm or edit each one. Sections drafted from the website are marked *(from website, verify)*. Unknowns stay empty rather than guessed.

It creates:

| Path | What it's for |
|---|---|
| `company.md` | Your company context. Added to every skill and playbook call so output is specific to you. Background only: never treated as evidence about a deal |
| `CLAUDE.md` | Operating rules for an agent in this folder: use the methodology skills, quote evidence, draft but never send, ask before changing anything outside the folder |
| `.mcp.json` | Connects Claude Code to the b2b-agent-skills MCP server |
| `gtm/deals/`, `gtm/accounts/` | Per-deal and per-account notes; debriefs are appended, never rewritten |
| `gtm/inbox/` | Drop call transcripts here; `b2b-skills inbox` debriefs each one and moves it to `processed/` |
| `gtm/pending/` | Proposed CRM changes waiting for your approval |
| `gtm/outcomes.csv` | Won/lost outcomes (`b2b-skills outcome "Acme" won --value 48000`) |
| `gtm/runs/` | One line per run: what ran, on what, with which model |
| `.github/workflows/gtm-weekly.yml` | Optional weekly automation (below) |

## Use it as an agent in Claude Code

```bash
cd my-gtm && claude
```

With the plugin installed (`/plugin marketplace add pratsy/skills-AI`, then `/plugin install b2b-agent-skills@b2b-agent-skills`), Claude Code reads `CLAUDE.md` and `company.md` and has every skill and playbook. Ask in plain language: *"debrief the Acme call in gtm/inbox"*, *"who should I contact from leads.csv?"*, *"what needs my attention this week?"*

## HubSpot

1. In HubSpot: Settings → Integrations → Private Apps → create an app with scopes `crm.objects.deals.read`, `crm.objects.deals.write`, `crm.objects.companies.read`, and `crm.schemas.deals.write`.
2. `export HUBSPOT_ACCESS_TOKEN=...`
3. `b2b-skills hubspot setup` creates four deal properties the review writes to: `b2b_risk_band`, `b2b_meddpicc_score`, `b2b_next_action`, `b2b_last_review`.
4. `b2b-skills hubspot deals` lists open deals; `b2b-skills playbook monday-review --hubspot` reviews them and proposes updates; `b2b-skills approve all` applies them.

The connector follows HubSpot's CRM v3 API. It's tested against a simulated API, not yet against a live portal; please report anything that doesn't match your account.

## Call transcripts

Any recorder that can export or forward text works (Fathom, Granola, Gong, Otter, Zoom, Google Meet):

- **Folder:** save or sync transcripts into `gtm/inbox/`, named after the deal (`acme-logistics-2026-11-03.vtt`), then run `b2b-skills inbox`.
- **Webhook:** run `b2b-skills serve` with `B2B_WORKSPACE` set, and have Zapier/Make or the recorder's webhook POST `{"notes": "...", "subject": "Acme"}` to `/v1/playbooks/call-debrief/run` with your bearer token.

## Slack

Create an incoming webhook, `export SLACK_WEBHOOK_URL=...`, and add `--slack` to `b2b-skills inbox` or `monday-review`.

## Run it every Monday

`init` writes `.github/workflows/gtm-weekly.yml`. Push the workspace to a private GitHub repo and add secrets:

- `CLAUDE_CODE_OAUTH_TOKEN` (from `claude setup-token`; runs on your Claude subscription)
- optional: `HUBSPOT_ACCESS_TOKEN`, `SLACK_WEBHOOK_URL`

Every Monday at 07:00 UTC it debriefs new transcripts, runs the pipeline review, posts to Slack, and commits the updated notes. CRM updates are only proposed; approve them locally.
