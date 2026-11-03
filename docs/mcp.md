# MCP server

Expose all 45 skills to any [MCP](https://modelcontextprotocol.io) client: Claude Desktop, Claude Code, Cursor, and others.

```bash
pip install "b2b-agent-skills[mcp]"
b2b-skills mcp                                  # stdio (local clients)
b2b-skills mcp --transport streamable-http      # remote / shared deployments
```

## What the server exposes

| Kind | Name | Notes |
|---|---|---|
| Tool | `list_skills` | every skill with its "use when" description |
| Tool | `get_skill` | a skill's instructions and output JSON Schema; the client's model then applies it |
| Tool | `run_skill` | only when `PROVIDER` is `claude-code`, `anthropic`, or `openai`; runs server-side and returns validated JSON |
| Prompt | one per skill, e.g. `deal-risk-assessor` | argument `input_json`; renders the full instructions plus your data |

Without a configured provider, nothing leaves your machine except through your MCP client's own model.

## Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "b2b-agent-skills": {
      "command": "b2b-skills",
      "args": ["mcp"]
    }
  }
}
```

If `b2b-skills` isn't on the PATH Claude Desktop sees, use the absolute path from `which b2b-skills`.

## Claude Code

```bash
claude mcp add b2b-agent-skills -- b2b-skills mcp
```

(In Claude Code the [plugin](claude-code.md) is usually simpler. Use MCP if you want server-side `run_skill`.)

## Cursor

`.cursor/mcp.json`:

```json
{ "mcpServers": { "b2b-agent-skills": { "command": "b2b-skills", "args": ["mcp"] } } }
```
