"""Model providers.

A provider takes a system prompt (the skill's instructions), a user message
(the input data), and the skill's output JSON Schema, and returns the model's
raw text. Providers that support structured outputs constrain the response to
the schema; the runner validates the result either way.

Select a provider with ``PROVIDER=mock|anthropic|openai`` or pass an instance
to ``run_skill(provider=...)``. Implement :class:`Provider` to add your own.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

from .errors import ProviderError

DEFAULT_MAX_TOKENS = 16000


@dataclass
class Completion:
    text: str
    model: str
    stop_reason: str | None = None
    usage: dict[str, int] = field(default_factory=dict)


class Provider:
    """Interface every provider implements."""

    name = "base"

    def complete(self, *, system: str, user: str, schema: dict[str, Any] | None, skill: str) -> Completion:
        raise NotImplementedError


class MockProvider(Provider):
    """Deterministic, offline provider for tests, CI, and demos.

    Returns the skill's documented worked-example output (from its README), so
    the whole pipeline - prompt build, parse, schema validation, golden
    assertions - runs without a network call or API key.
    """

    name = "mock"

    def __init__(self, response: Any = None):
        self._response = response

    def complete(self, *, system: str, user: str, schema: dict[str, Any] | None, skill: str) -> Completion:
        if self._response is not None:
            payload = self._response
        else:
            from .registry import get_skill

            payload = get_skill(skill).example_output or {}
        text = payload if isinstance(payload, str) else json.dumps(payload)
        return Completion(text=text, model="mock", stop_reason="end_turn")


# Models that accept server-side refusal fallbacks (`fallbacks: "default"`).
_FALLBACK_MODELS = {"claude-fable-5-1", "claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5"}
_FALLBACK_BETA = "server-side-fallback-2026-07-01"


class AnthropicProvider(Provider):
    """Claude via the Anthropic Messages API, with structured outputs.

    Environment:
      ANTHROPIC_API_KEY (or any credential the anthropic SDK resolves)
      ANTHROPIC_MODEL      default ``claude-opus-5-5``
      ANTHROPIC_EFFORT     optional: low | medium | high | xhigh | max
      ANTHROPIC_FALLBACKS  ``off`` to disable server-side refusal fallbacks
    """

    name = "anthropic"

    def __init__(self, model: str | None = None, *, effort: str | None = None, max_tokens: int = DEFAULT_MAX_TOKENS, client: Any = None):
        if client is None:
            try:
                import anthropic
            except ImportError as e:
                raise ProviderError("Install the Anthropic extra: pip install 'b2b-agent-skills[anthropic]'") from e
            client = anthropic.Anthropic()
        self._client = client
        self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-opus-5-5")
        self.effort = effort or os.getenv("ANTHROPIC_EFFORT") or None
        self.max_tokens = max_tokens
        self.fallbacks = os.getenv("ANTHROPIC_FALLBACKS", "default").lower() != "off" and self.model in _FALLBACK_MODELS

    def complete(self, *, system: str, user: str, schema: dict[str, Any] | None, skill: str) -> Completion:
        output_config: dict[str, Any] = {}
        if schema:
            output_config["format"] = {"type": "json_schema", "schema": schema}
        if self.effort:
            output_config["effort"] = self.effort

        params: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            # The skill instructions are identical across calls - cache them.
            "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            "messages": [{"role": "user", "content": user}],
        }
        if output_config:
            params["output_config"] = output_config

        if self.fallbacks:
            response = self._client.beta.messages.create(betas=[_FALLBACK_BETA], fallbacks="default", **params)
        else:
            response = self._client.messages.create(**params)

        stop_reason = getattr(response, "stop_reason", None)
        if stop_reason == "refusal":
            details = getattr(response, "stop_details", None)
            raise ProviderError(
                f"Model declined the request (category: {getattr(details, 'category', None)})", stop_reason=stop_reason, details=details
            )
        if stop_reason == "max_tokens":
            raise ProviderError(f"Output truncated at max_tokens={self.max_tokens}; raise max_tokens", stop_reason=stop_reason)

        text = "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
        usage_obj = getattr(response, "usage", None)
        usage = {
            k: getattr(usage_obj, k)
            for k in ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")
            if isinstance(getattr(usage_obj, k, None), int)
        }
        return Completion(text=text, model=str(getattr(response, "model", None) or self.model), stop_reason=stop_reason, usage=usage)


def _strict_compatible(schema: Any) -> bool:
    """OpenAI strict mode needs every property required on every object."""
    if isinstance(schema, dict):
        if schema.get("type") == "object":
            props = schema.get("properties", {})
            if set(schema.get("required", [])) != set(props) or schema.get("additionalProperties") is not False:
                return False
        return all(_strict_compatible(v) for v in schema.values())
    if isinstance(schema, list):
        return all(_strict_compatible(v) for v in schema)
    return True


class OpenAIProvider(Provider):
    """OpenAI Chat Completions with JSON Schema response format.

    Environment: OPENAI_API_KEY, OPENAI_MODEL (default ``gpt-4o-mini``).
    """

    name = "openai"

    def __init__(self, model: str | None = None, *, max_tokens: int = DEFAULT_MAX_TOKENS, client: Any = None):
        if client is None:
            try:
                from openai import OpenAI
            except ImportError as e:
                raise ProviderError("Install the OpenAI extra: pip install 'b2b-agent-skills[openai]'") from e
            client = OpenAI()
        self._client = client
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.max_tokens = max_tokens

    def complete(self, *, system: str, user: str, schema: dict[str, Any] | None, skill: str) -> Completion:
        params: dict[str, Any] = {
            "model": self.model,
            "max_completion_tokens": self.max_tokens,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }
        if schema:
            params["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": skill.replace("-", "_"), "schema": schema, "strict": _strict_compatible(schema)},
            }
        response = self._client.chat.completions.create(**params)
        choice = response.choices[0]
        if getattr(choice.message, "refusal", None):
            raise ProviderError(f"Model declined the request: {choice.message.refusal}", stop_reason="refusal")
        if choice.finish_reason == "length":
            raise ProviderError(f"Output truncated at max_completion_tokens={self.max_tokens}", stop_reason="length")
        usage_obj = getattr(response, "usage", None)
        usage = {}
        if usage_obj is not None:
            usage = {"input_tokens": usage_obj.prompt_tokens, "output_tokens": usage_obj.completion_tokens}
        return Completion(text=choice.message.content or "", model=response.model, stop_reason=choice.finish_reason, usage=usage)


class ClaudeCodeProvider(Provider):
    """Claude through the local Claude Code CLI (``claude -p``): no API key needed.

    Uses whatever the CLI is logged in with, including a Claude Pro/Max
    subscription. Each call is an isolated, tool-less ``claude -p`` run: the
    skill's instructions are the system prompt, user/project settings and MCP
    servers are not loaded, and the input is sent on stdin. The CLI has no
    schema-constrained decoding, so the runner's parse-validate-retry loop does
    the enforcing.

    Environment:
      CLAUDE_CODE_BIN      path to the ``claude`` binary (default: found on PATH)
      CLAUDE_CODE_MODEL    model alias or ID, e.g. ``sonnet`` or ``opus`` (default ``sonnet``)
      CLAUDE_CODE_TIMEOUT  seconds per call (default 600)
    """

    name = "claude-code"

    def __init__(self, model: str | None = None, *, binary: str | None = None, timeout: float | None = None):
        import shutil

        found = binary or os.getenv("CLAUDE_CODE_BIN") or shutil.which("claude")
        if not found:
            raise ProviderError("Claude Code CLI not found. Install it (https://code.claude.com) and run `claude` once to log in.")
        self.binary: str = found
        self.model = model or os.getenv("CLAUDE_CODE_MODEL") or "sonnet"
        self.timeout = timeout or float(os.getenv("CLAUDE_CODE_TIMEOUT", "600"))

    def complete(self, *, system: str, user: str, schema: dict[str, Any] | None, skill: str) -> Completion:
        import subprocess
        import tempfile

        cmd = [
            self.binary,
            "-p",
            "--output-format",
            "json",
            "--system-prompt",
            system,
            "--tools",
            "",
            "--setting-sources",
            "",
            "--strict-mcp-config",
        ]
        cmd += ["--model", self.model]
        with tempfile.TemporaryDirectory() as cwd:  # keep the repo's CLAUDE.md and skills out of the call
            try:
                proc = subprocess.run(cmd, input=user, capture_output=True, text=True, timeout=self.timeout, cwd=cwd)
            except subprocess.TimeoutExpired as e:
                raise ProviderError(f"claude -p timed out after {self.timeout:.0f}s") from e
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError as e:
            detail = (proc.stderr or proc.stdout).strip()[:500]
            raise ProviderError(f"claude -p failed (exit {proc.returncode}): {detail}") from e
        if payload.get("is_error") or payload.get("subtype") != "success":
            raise ProviderError(f"claude -p returned an error: {str(payload.get('result') or payload.get('subtype'))[:500]}")

        usage_raw = payload.get("usage") or {}
        usage = {
            k: usage_raw[k]
            for k in ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")
            if isinstance(usage_raw.get(k), int)
        }
        per_model = payload.get("modelUsage") or {}
        model = max(per_model, key=lambda m: per_model[m].get("outputTokens", 0)) if per_model else self.model
        return Completion(
            text=str(payload.get("result", "")),
            model=model,
            stop_reason="end_turn",
            usage=usage,
        )


PROVIDERS: dict[str, type[Provider]] = {
    "mock": MockProvider,
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "claude-code": ClaudeCodeProvider,
}


def get_provider(name: str | None = None, **kwargs: Any) -> Provider:
    """Build a provider by name, defaulting to the ``PROVIDER`` env var (then ``mock``)."""
    name = (name or os.getenv("PROVIDER") or "mock").lower()
    cls = PROVIDERS.get(name)
    if cls is None:
        raise ValueError(f"Unknown provider '{name}'. Supported: {', '.join(PROVIDERS)}")
    return cls(**kwargs)
