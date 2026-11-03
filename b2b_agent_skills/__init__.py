"""B2B Agent Skills: structured, evidence-grounded AI skills for revenue teams.

from b2b_agent_skills import run_skill

result = run_skill("deal-risk-assessor", {"deal_id": "opp_1", "pillar_evidence": {...}}, provider="anthropic")
result.output["risk_band"]
"""

from .errors import ProviderError, SkillNotFoundError, SkillOutputError, SkillsError
from .evaluation import EvalReport, run_golden
from .providers import AnthropicProvider, ClaudeCodeProvider, MockProvider, OpenAIProvider, Provider, get_provider
from .registry import Skill, get_skill, list_skills
from .runner import SkillResult, run_skill

__version__ = "0.3.0"

__all__ = [
    "AnthropicProvider",
    "ClaudeCodeProvider",
    "EvalReport",
    "MockProvider",
    "OpenAIProvider",
    "Provider",
    "ProviderError",
    "Skill",
    "SkillNotFoundError",
    "SkillOutputError",
    "SkillResult",
    "SkillsError",
    "__version__",
    "get_provider",
    "get_skill",
    "list_skills",
    "run_golden",
    "run_skill",
]
