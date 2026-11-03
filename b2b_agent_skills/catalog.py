"""Which skills fit which company stage.

early  works with little or no history: a few calls, a lead list, a homepage
growth needs some history: roughly 20+ closed deals or an active customer base
scale  needs a team and quarters of CRM history (multiple reps, forecast cycles)
"""

from __future__ import annotations

STAGES = ("early", "growth", "scale")

_GROWTH = {
    "abm-account-priority-ranker",
    "account-plan-generator",
    "brand-perception-monitor",
    "campaign-performance-diagnostician",
    "competitor-signal-clusterer",
    "customer-journey-friction-audit",
    "icp-refinement-agent",
    "lifecycle-email-optimizer",
    "renewal-risk-scorer",
    "win-loss-theme-clusterer",
}
_SCALE = {
    "account-priority-matrix-builder",
    "attribution-model-reviewer",
    "crm-data-cleaner",
    "deal-committee-readiness-coach",
    "forecast-bias-detector",
    "forecast-confidence-model",
    "pipeline-health-monitor",
    "strategic-account-priority-ranker",
    "territory-prioritization-agent",
}


def stage_of(skill: str) -> str:
    if skill in _SCALE:
        return "scale"
    if skill in _GROWTH:
        return "growth"
    return "early"
