# HTTP API

A small authenticated API for calling skills from other services, such as a CRM webhook, n8n, Zapier, or your own backend.

## Run it

```bash
pip install "b2b-agent-skills[server,anthropic]"
export B2B_SKILLS_API_TOKEN=$(openssl rand -hex 32)
export PROVIDER=anthropic ANTHROPIC_API_KEY=sk-ant-...
b2b-skills serve --host 0.0.0.0 --port 8000
```

Or with Docker:

```bash
docker build -t b2b-agent-skills .
docker run -p 8000:8000 -e B2B_SKILLS_API_TOKEN -e PROVIDER=anthropic -e ANTHROPIC_API_KEY b2b-agent-skills
```

The server refuses to start without `B2B_SKILLS_API_TOKEN` (set `B2B_SKILLS_ALLOW_NO_AUTH=1` only for local development).

## Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | none | liveness and version |
| GET | `/v1/skills` | bearer | list skills |
| GET | `/v1/skills/{name}` | bearer | instructions and output schema |
| POST | `/v1/skills/{name}/run` | bearer | body `{"input": {...}}`; returns `{"skill", "output", "model", "usage", "latency_ms"}` |

```bash
curl -s localhost:8000/v1/skills/competitor-monitor/run \
  -H "Authorization: Bearer $B2B_SKILLS_API_TOKEN" -H 'Content-Type: application/json' \
  -d '{"input": {"competitor": "X", "signal_description": "price cut", "move_type": "pricing",
       "overlap_with_icp": 0.6, "confirmation_level": "confirmed_broad", "related_moves_last_quarter": 1}}'
```

Errors: `401` bad token, `404` unknown skill, `413` body over `B2B_SKILLS_MAX_BODY_BYTES` (default 256 KB), `422` invalid input, `502` provider error or model output that failed validation. Error bodies never include provider error text or stack traces.

## Production notes

- Put it behind TLS (a load balancer or reverse proxy). The server speaks plain HTTP.
- Add rate limiting at the proxy. Every request costs model tokens.
- Rotate `B2B_SKILLS_API_TOKEN` like any other secret. Use one token per calling service if you need to revoke them separately.
