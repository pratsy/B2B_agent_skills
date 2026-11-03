"""Exception types raised by the SDK."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .runner import SkillResult


class SkillsError(Exception):
    """Base class for every error raised by b2b_agent_skills."""


class SkillNotFoundError(SkillsError, LookupError):
    def __init__(self, name: str, available: list[str] | None = None):
        self.name = name
        hint = ""
        if available:
            close = [s for s in available if name.split("-")[0] in s][:5]
            hint = f" Did you mean one of: {', '.join(close)}?" if close else " Run `b2b-skills list` to see all skills."
        super().__init__(f"Unknown skill '{name}'.{hint}")


class ProviderError(SkillsError):
    """The model provider failed, refused, or returned an unusable response."""

    def __init__(self, message: str, *, stop_reason: str | None = None, details: Any = None):
        super().__init__(message)
        self.stop_reason = stop_reason
        self.details = details


class SkillOutputError(SkillsError):
    """The model's output could not be parsed or did not match the skill's schema."""

    def __init__(self, message: str, result: SkillResult):
        super().__init__(message)
        self.result = result
