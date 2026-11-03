# Playbooks

Playbooks chain skills into the jobs a founder actually does. Each one takes the material you already have, uses code for anything that's math, and returns a one-page answer saved to your workspace.

Run them from the CLI (inside a workspace from `b2b-skills init`), from Claude Code (the plugin includes them as skills), or over MCP.

## call-debrief

**"I just had a call. What now?"**

```bash
b2b-skills playbook call-debrief --notes acme-call.txt --subject "Acme Logistics"
```

- **Input:** a transcript or notes (`.txt`, `.md`, `.vtt`, `.srt`, or a JSON export), a file or a folder.
- **Steps:** extracts the inputs for `deal-risk-assessor`, `stakeholder-map-builder`, and (if the buyer raised one) `objection-response-coach`, keeping only facts it can quote from your notes. Runs the three skills in parallel, then writes the report.
- **Output:** Verdict (MEDDPICC /24, risk band, forecast call), Next 3 actions, Missing evidence (with the question to ask), Stakeholders, Objection, Draft follow-up email. Appended to `gtm/deals/<deal>.md` with the raw notes, so later reviews re-score from primary evidence.

## find-icp

**"Who should we really sell to?"**

```bash
b2b-skills playbook find-icp --customers accounts.csv --notes interviews/
```

- **Input:** an account list with an outcome column (won/lost, customer/prospect) and attribute columns (industry, employees, country, buyer title, technologies), and/or customer interview notes.
- **Steps:** attribute lift (share among best accounts ÷ share among all) is computed in code. Interviews go through `persona-insight-extractor`; `icp-refinement-agent` interprets the exact lift numbers.
- **Output:** a brief (Who to sell to, Buying trigger, Who to avoid, Evidence, Confidence, Proposed ICP) in `gtm/icp.md`, and `gtm/icp.proposed.json`. Use `--apply` to write `gtm/icp.json` directly.

## score-list

**"Who do I contact this week?"**

```bash
b2b-skills playbook score-list --csv apollo-export.csv --top 50
```

- **Input:** any lead or account CSV. Common headers are recognized ("Company Name", "# Employees", "Job Title", "HQ Country"…); fix the rest with `--map industry="Company Vertical"`.
- **Steps:** every row is scored against `gtm/icp.json` in code (industry 30, size 25, title 25, geography 10, technology 10; missing data is left out, not counted against the row; excluded titles or industries score 0). The model then writes a why-now and an opening line for the top rows, using only that row's fields and your company context.
- **Output:** `gtm/lists/<name>-scored.csv` (your columns plus fit score, tier, reasons, why, opening line) and `gtm/lists/<name>.md`. Tiers: A 80+, B 60-79, C 40-59, skip, unknown. `--no-angles` skips the model entirely.

`gtm/icp.json` format:

```json
{
  "industries": ["fintech", "financial services"],
  "employee_range": [50, 500],
  "geographies": ["US", "Canada"],
  "titles": ["vp sales", "revenue operations", "cro"],
  "technologies": ["salesforce", "hubspot"],
  "exclude": {"titles": ["intern"], "industries": ["government"]}
}
```

## monday-review

**"Which deals need me this week?"**

```bash
b2b-skills playbook monday-review --hubspot --slack
b2b-skills playbook monday-review --csv pipeline.csv
```

- **Input:** open deals from HubSpot, or a pipeline CSV (deal name, amount, stage, close date, last activity).
- **Steps:** code flags each deal (close date passed, 14+ days without activity, 45+ days in stage, no debrief notes on file). Deals with notes in `gtm/deals/` are re-scored with `deal-risk-assessor` from the raw notes. Priority is computed in code, and the report has to follow it: overdue, silent deals come first.
- **Output:** This week's focus, Deals at risk, No evidence on file, Pipeline snapshot, in `gtm/reviews/<date>.md`. With `--hubspot`, risk band, MEDDPICC score, and next action are **proposed** as CRM updates; nothing is written until you approve.

## Approvals

```bash
b2b-skills pending            # what's waiting
b2b-skills approve all        # or an id; --dry-run to preview
b2b-skills reject <id>
```

Approved and rejected changes move to `gtm/applied/` and `gtm/rejected/`, so there's an audit trail.

## Evals

```bash
b2b-skills eval --playbooks --provider claude-code --concurrency 4
```

Playbook evals live in `evals/playbooks/`. They include cases that fail if a report invents evidence, proof points, or statistics, or contradicts the computed priority order.
