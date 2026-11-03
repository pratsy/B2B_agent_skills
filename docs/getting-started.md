# Getting started

## 1. Install

```bash
pip install "b2b-agent-skills[anthropic]"     # Claude
pip install "b2b-agent-skills[openai]"        # OpenAI
pip install "b2b-agent-skills[all]"           # every provider + MCP + HTTP server
```

Python 3.10+. The core package depends only on `jsonschema`. Providers and servers are optional extras.

## 2. Run a GTM checkup

```bash
b2b-skills checkup yourcompany.com --provider claude-code
```

Ten quick questions plus your website give you a scorecard across ICP, product-market fit, positioning, proof, demand, pricing, sales motion, and pipeline, with the top 3 fixes. See [GTM checkup](checkup.md).

## 3. Try it offline

The `mock` provider returns each skill's documented worked-example output, so you can explore without an API key:

```bash
b2b-skills list -v                         # all 48 skills, with when to use each
b2b-skills show pipeline-health-monitor    # methodology and output fields
b2b-skills run pipeline-health-monitor -i examples/fixtures/renewal_input.json
```

## 4. Run it for real

**No API key: use your Claude subscription.** If you have [Claude Code](https://code.claude.com) installed and logged in (Pro, Max, Team, or Enterprise), the `claude-code` provider runs skills through it:

```bash
b2b-skills run pipeline-health-monitor -i examples/fixtures/pipeline_input.json --provider claude-code
```

Each call is an isolated `claude -p` run with tools disabled and your project settings not loaded. Usage counts against your subscription's limits.

**With an API key** (structured outputs, prompt caching, production use):

```bash
export ANTHROPIC_API_KEY=sk-ant-...
cat > pipeline.json <<'EOF'
{
  "open_pipeline_value": 2400000,
  "remaining_quota": 700000,
  "historical_win_rate": 0.22,
  "stage_conversion_rates": [
    {"transition": "discovery_to_proposal", "current_rate": 0.28, "historical_median": 0.45}
  ]
}
EOF
b2b-skills run pipeline-health-monitor -i pipeline.json --provider anthropic
```

Each skill's page in the [catalog](skills.md) lists the inputs it expects. Send only the fields it needs: everything in the input is sent to the model provider (see [Security](https://github.com/pratsy/B2B_agent_skills/blob/main/SECURITY.md)).

## 5. Configure

| Variable | Default | Purpose |
|---|---|---|
| `PROVIDER` | `mock` | `mock`, `claude-code`, `anthropic`, or `openai` |
| `CLAUDE_CODE_MODEL` | `sonnet` | model alias or ID for the `claude-code` provider |
| `ANTHROPIC_MODEL` | `claude-opus-5-5` | any Claude model ID |
| `ANTHROPIC_EFFORT` | model default | `low` … `max`. Lower is cheaper and faster |
| `ANTHROPIC_FALLBACKS` | on | `off` disables server-side refusal fallbacks |
| `OPENAI_MODEL` | `gpt-4o-mini` | any OpenAI chat model |

`b2b-skills` reads a `.env` file if `python-dotenv` is installed (`pip install "b2b-agent-skills[dotenv]"`).
