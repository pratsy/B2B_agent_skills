# Python SDK & CLI

## Run a skill

```python
from b2b_agent_skills import run_skill

result = run_skill(
    "forecast-confidence-model",
    {
        "deal_id": "opp_5521",
        "meddpicc_score": 20,
        "current_stage": "negotiation",
        "days_in_current_stage": 34,
        "historical_median_days_in_stage": {"negotiation": 18},
        "rep_trailing_commit_accuracy": 0.55,
    },
    provider="anthropic",
)

result.output["forecast_category"]  # "best case"
result.usage  # {"input_tokens": ..., "output_tokens": ..., "cache_read_input_tokens": ...}
```

`input` can be a dict or a path to a JSON file. Skill names accept dashes or underscores.

## What `run_skill` guarantees

1. The prompt is the skill's `SKILL.md` instructions plus its output contract (the system prompt, cached across calls) and your input (the user message).
2. Providers with structured outputs are constrained to the skill's JSON Schema: Claude via `output_config.format`, OpenAI via `response_format`. The `claude-code` provider has no constrained decoding: the model writes its working, then a final JSON block, and steps 3-4 enforce the schema.
3. The response is parsed (tolerating markdown fences) and validated against the schema.
4. If it's invalid, the call is retried once with the validation errors as feedback.
5. If it's still invalid, `SkillOutputError` is raised. The result, including the raw text, is attached as `e.result`. Pass `raise_on_invalid=False` to get the result back with `valid=False` instead.

Refusals and truncation raise `ProviderError` with `stop_reason` set. On Claude models that support it, server-side refusal fallbacks are enabled by default (`ANTHROPIC_FALLBACKS=off` disables them).

## Choose a provider

```python
from b2b_agent_skills import AnthropicProvider, ClaudeCodeProvider, OpenAIProvider, MockProvider

run_skill(name, data, provider=AnthropicProvider(model="claude-sonnet-5-5", effort="low"))
run_skill(name, data, provider=OpenAIProvider(model="gpt-4o"))
run_skill(name, data, provider=ClaudeCodeProvider(model="opus"))  # no API key: your Claude Code login
run_skill(name, data, provider=MockProvider())  # offline, returns the README example
```

Or set `PROVIDER` and omit the argument. To add another backend, subclass `Provider` and implement `complete(system=..., user=..., schema=..., skill=...) -> Completion`.

## Inspect skills

```python
from b2b_agent_skills import list_skills, get_skill

skill = get_skill("market-sizing-modeler")
skill.description  # when to use it
skill.instructions  # the methodology
skill.output_schema  # JSON Schema, ready to send to a provider
skill.example_output  # the README's worked-example output
```

## CLI reference

```text
b2b-skills list [-v]
b2b-skills show <skill> [--schema]
b2b-skills run <skill> [-i input.json | -i -] [--provider P] [--model M] [--full]
# P = mock | claude-code | anthropic | openai
b2b-skills eval [--skill S ...] [--provider P] [--model M] [--concurrency N] [--json out.json] [--markdown out.md] [--min-pass-rate 0.8]
b2b-skills mcp [--transport stdio|streamable-http|sse]
b2b-skills serve [--host H] [--port N]
```
