# B2B Agent Skills

**An open-source GTM workspace for founder-led sales.** Connect your call notes, lead lists, and CRM, and it does the go-to-market work with tested methods: debriefs calls, finds your real ICP, ranks your lead list, and runs your Monday pipeline review. Runs on your Claude subscription (no API key) or on the Anthropic or OpenAI APIs.

![Demo: scoring a deal with deal-risk-assessor](assets/demo.gif)

```bash
pip install b2b-agent-skills
b2b-skills run deal-risk-assessor -i deal.json --provider claude-code   # your Claude login, no API key
b2b-skills run deal-risk-assessor -i deal.json --provider anthropic     # or an API key
```

```json
{
  "deal_id": "opp_5521",
  "pillar_scores": {"metrics": 3, "economic_buyer": 1, "paper_process": 0, "...": "..."},
  "total_score": 14,
  "risk_band": "moderate-high",
  "single_point_of_failure": ["economic_buyer"],
  "forecast_recommendation": "Best Case at most, not Commit",
  "priority_action": "get a direct economic-buyer conversation to confirm decision process and paper process"
}
```

## Why it's different

- **Methodology, not vibes.** Every skill has a named framework, a scoring formula, and the failure patterns it guards against. Scores come from evidence quality, not rep confidence.
- **A contract you can build on.** Every skill has a JSON Schema. Providers that support structured outputs (Claude, OpenAI) are constrained to it, and every response is validated before you get it.
- **Tested answers.** Golden evals check that a model applying a skill gets the *right answer* on the worked example (e.g. MEDDPICC totals 14/24 and flags the economic buyer), not just valid JSON.
- **One definition, every surface.** The same skill folder powers the Claude Code plugin, the MCP server, the Python SDK and CLI, and the HTTP API.

## Pick your surface

| You want to… | Use |
|---|---|
| Ask Claude Code to score a deal, size a market, or audit messaging | [Claude Code plugin](claude-code.md) |
| Use the skills from Claude Desktop, Cursor, or any MCP client | [MCP server](mcp.md) |
| Call skills from Python, a notebook, or a cron job | [Python SDK & CLI](sdk.md) |
| Call skills from another service (CRM webhook, n8n, Zapier) | [HTTP API](http-api.md) |

Start with the [playbooks](playbooks.md) and set up your [workspace](workspace.md). Browse the [skill catalog](skills.md) for the 46 skills underneath.
