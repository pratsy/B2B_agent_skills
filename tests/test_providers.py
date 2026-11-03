"""Provider request shapes, checked against fake SDK clients (no network)."""

import json
from types import SimpleNamespace

import pytest

from b2b_agent_skills import get_skill
from b2b_agent_skills.errors import ProviderError
from b2b_agent_skills.providers import AnthropicProvider, OpenAIProvider, _strict_compatible, get_provider


class FakeAnthropic:
    def __init__(self, response):
        self.calls = []
        outer = self

        class _Messages:
            def create(self, **kw):
                outer.calls.append(("messages", kw))
                return response

        class _Beta:
            messages = _Messages()

        self.messages = _Messages()
        self.beta = _Beta()


def _anthropic_response(text, stop_reason="end_turn"):
    return SimpleNamespace(
        content=[SimpleNamespace(type="thinking", thinking=""), SimpleNamespace(type="text", text=text)],
        stop_reason=stop_reason,
        stop_details=SimpleNamespace(category="cyber"),
        model="claude-opus-5-5",
        usage=SimpleNamespace(input_tokens=100, output_tokens=50, cache_read_input_tokens=80, cache_creation_input_tokens=0),
    )


SCHEMA = get_skill("pricing-justification-builder").output_schema


def test_anthropic_uses_structured_outputs_caching_and_fallbacks(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_FALLBACKS", raising=False)
    fake = FakeAnthropic(_anthropic_response('{"ok": true}'))
    provider = AnthropicProvider(client=fake)
    completion = provider.complete(system="SYS", user="USER", schema=SCHEMA, skill="pricing-justification-builder")

    _, kw = fake.calls[0]
    assert kw["model"] == "claude-opus-5-5"
    assert kw["output_config"]["format"] == {"type": "json_schema", "schema": SCHEMA}
    assert kw["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert kw["betas"] == ["server-side-fallback-2026-07-01"] and kw["fallbacks"] == "default"
    assert kw["max_tokens"] >= 16000
    assert completion.text == '{"ok": true}'
    assert completion.usage["cache_read_input_tokens"] == 80


def test_anthropic_fallbacks_can_be_disabled_and_skip_unsupported_models(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_FALLBACKS", "off")
    fake = FakeAnthropic(_anthropic_response("{}"))
    AnthropicProvider(client=fake).complete(system="s", user="u", schema=None, skill="x")
    assert "fallbacks" not in fake.calls[0][1]

    monkeypatch.delenv("ANTHROPIC_FALLBACKS")
    fake = FakeAnthropic(_anthropic_response("{}"))
    AnthropicProvider(model="claude-haiku-5-5", client=fake).complete(system="s", user="u", schema=None, skill="x")
    assert "fallbacks" not in fake.calls[0][1]


@pytest.mark.parametrize("stop_reason", ["refusal", "max_tokens"])
def test_anthropic_refusal_and_truncation_raise(stop_reason):
    provider = AnthropicProvider(client=FakeAnthropic(_anthropic_response("", stop_reason=stop_reason)))
    with pytest.raises(ProviderError) as exc:
        provider.complete(system="s", user="u", schema=None, skill="x")
    assert exc.value.stop_reason == stop_reason


def test_openai_uses_json_schema_response_format():
    calls = []
    response = SimpleNamespace(
        model="gpt-4o-mini",
        choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content=json.dumps({"a": 1}), refusal=None))],
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=3),
    )
    fake = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: calls.append(kw) or response)))
    completion = OpenAIProvider(client=fake).complete(system="s", user="u", schema=SCHEMA, skill="pricing-justification-builder")
    fmt = calls[0]["response_format"]
    assert fmt["type"] == "json_schema"
    assert fmt["json_schema"]["name"] == "pricing_justification_builder"
    assert fmt["json_schema"]["strict"] is True
    assert calls[0]["messages"][0] == {"role": "system", "content": "s"}
    assert completion.usage == {"input_tokens": 10, "output_tokens": 3}


def test_strict_compatibility_detection():
    assert _strict_compatible(SCHEMA)
    loose = {"type": "object", "properties": {"a": {"type": "string"}}, "required": [], "additionalProperties": False}
    assert not _strict_compatible(loose)


def test_get_provider_defaults_to_mock_and_rejects_unknown(monkeypatch):
    monkeypatch.delenv("PROVIDER", raising=False)
    assert get_provider().name == "mock"
    with pytest.raises(ValueError, match="Unknown provider"):
        get_provider("nope")


def _fake_claude(tmp_path, payload, exit_code=0):
    """A stand-in `claude` binary that records its argv/stdin and prints a canned result."""
    script = tmp_path / "claude"
    log = tmp_path / "calls.jsonl"
    script.write_text(
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        f"open({str(log)!r}, 'a').write(json.dumps({{'argv': sys.argv[1:], 'stdin': sys.stdin.read()}}) + '\\n')\n"
        f"print({json.dumps(json.dumps(payload))})\n"
        f"sys.exit({exit_code})\n"
    )
    script.chmod(0o755)
    return script, log


def test_claude_code_provider_runs_isolated_print_mode(tmp_path):
    from b2b_agent_skills.providers import ClaudeCodeProvider

    payload = {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "result": '```json\n{"a": 1}\n```',
        "usage": {"input_tokens": 3, "output_tokens": 9, "cache_read_input_tokens": 0},
        "modelUsage": {"claude-haiku-x": {"outputTokens": 1}, "claude-sonnet-x": {"outputTokens": 9}},
    }
    binary, log = _fake_claude(tmp_path, payload)
    completion = ClaudeCodeProvider(binary=str(binary)).complete(system="SYSTEM", user="USER", schema=SCHEMA, skill="x")

    call = json.loads(log.read_text().splitlines()[0])
    argv = call["argv"]
    assert argv[:3] == ["-p", "--output-format", "json"]
    assert argv[argv.index("--system-prompt") + 1] == "SYSTEM"
    assert argv[argv.index("--tools") + 1] == ""
    assert argv[argv.index("--setting-sources") + 1] == ""
    assert "--strict-mcp-config" in argv
    assert argv[argv.index("--model") + 1] == "sonnet"
    assert call["stdin"] == "USER"
    assert completion.text == '```json\n{"a": 1}\n```'
    assert completion.model == "claude-sonnet-x"
    assert completion.usage["output_tokens"] == 9


def test_claude_code_provider_surfaces_errors(tmp_path):
    from b2b_agent_skills.providers import ClaudeCodeProvider

    binary, _ = _fake_claude(tmp_path, {"type": "result", "subtype": "error_during_execution", "is_error": True, "result": "not logged in"})
    with pytest.raises(ProviderError, match="not logged in"):
        ClaudeCodeProvider(binary=str(binary)).complete(system="s", user="u", schema=None, skill="x")

    bad = tmp_path / "bad"
    bad.write_text("#!/bin/sh\necho 'boom' >&2\nexit 3\n")
    bad.chmod(0o755)
    with pytest.raises(ProviderError, match="exit 3"):
        ClaudeCodeProvider(binary=str(bad)).complete(system="s", user="u", schema=None, skill="x")


def test_claude_code_provider_requires_the_cli(monkeypatch):
    from b2b_agent_skills.providers import ClaudeCodeProvider

    monkeypatch.delenv("CLAUDE_CODE_BIN", raising=False)
    monkeypatch.setenv("PATH", "/nonexistent")
    with pytest.raises(ProviderError, match="CLI not found"):
        ClaudeCodeProvider()
