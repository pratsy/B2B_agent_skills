"""HubSpot CRM connector (CRM v3 API, private app access token).

Setup: in HubSpot, Settings -> Integrations -> Private Apps -> create an app with
scopes crm.objects.deals.read, crm.objects.deals.write, crm.objects.companies.read,
crm.schemas.deals.write (only for `b2b-skills hubspot setup`). Put the token in
HUBSPOT_ACCESS_TOKEN.

Reads (deals, their companies) are direct. Writes (updating deal properties)
never happen here directly from a playbook: playbooks propose changes into
gtm/pending/, and `b2b-skills approve` applies them.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any

from ..errors import SkillsError

BASE_URL = "https://api.hubapi.com"
DEAL_PROPERTIES = [
    "dealname",
    "amount",
    "dealstage",
    "pipeline",
    "closedate",
    "createdate",
    "hs_lastmodifieddate",
    "notes_last_updated",
    "hs_v2_date_entered_current_stage",
    "hs_is_closed",
    "hs_is_closed_won",
]

# Custom deal properties the playbooks write back (created by `b2b-skills hubspot setup`).
WRITEBACK_PROPERTIES = [
    {"name": "b2b_risk_band", "label": "Deal risk band (b2b-agent-skills)", "type": "string", "fieldType": "text"},
    {"name": "b2b_meddpicc_score", "label": "MEDDPICC score /24 (b2b-agent-skills)", "type": "number", "fieldType": "number"},
    {"name": "b2b_next_action", "label": "Next action (b2b-agent-skills)", "type": "string", "fieldType": "textarea"},
    {"name": "b2b_last_review", "label": "Last reviewed (b2b-agent-skills)", "type": "date", "fieldType": "date"},
]

Transport = Callable[[str, str, dict[str, str], bytes | None], tuple[int, bytes]]


def _urllib_transport(method: str, url: str, headers: dict[str, str], body: bytes | None) -> tuple[int, bytes]:
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


class HubSpot:
    def __init__(self, token: str | None = None, *, base_url: str = BASE_URL, transport: Transport | None = None):
        self.token = token or os.getenv("HUBSPOT_ACCESS_TOKEN")
        if not self.token:
            raise SkillsError("set HUBSPOT_ACCESS_TOKEN (a HubSpot private app token) to use the HubSpot connector")
        self.base_url = base_url.rstrip("/")
        self._transport = transport or _urllib_transport

    def _request(self, method: str, path: str, payload: Any = None) -> Any:
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json", "Accept": "application/json"}
        body = json.dumps(payload).encode() if payload is not None else None
        status, raw = self._transport(method, self.base_url + path, headers, body)
        data = json.loads(raw or b"{}") if raw else {}
        if status >= 400:
            message = data.get("message") if isinstance(data, dict) else raw[:200].decode("utf-8", "replace")
            raise SkillsError(f"HubSpot {method} {path} failed ({status}): {message}")
        return data

    def open_deals(self, limit: int = 200) -> list[dict[str, Any]]:
        """Open deals with their properties and associated company names, newest activity first."""
        deals: list[dict[str, Any]] = []
        after: str | None = None
        while len(deals) < limit:
            payload: dict[str, Any] = {
                "filterGroups": [{"filters": [{"propertyName": "hs_is_closed", "operator": "NEQ", "value": "true"}]}],
                "properties": DEAL_PROPERTIES,
                "sorts": [{"propertyName": "hs_lastmodifieddate", "direction": "DESCENDING"}],
                "limit": min(100, limit - len(deals)),
            }
            if after:
                payload["after"] = after
            page = self._request("POST", "/crm/v3/objects/deals/search", payload)
            deals += page.get("results", [])
            after = page.get("paging", {}).get("next", {}).get("after")
            if not after:
                break
        companies = self._deal_companies([d["id"] for d in deals])
        return [self._normalize(d, companies.get(d["id"], "")) for d in deals]

    def _deal_companies(self, deal_ids: list[str]) -> dict[str, str]:
        if not deal_ids:
            return {}
        links = self._request("POST", "/crm/v4/associations/deals/companies/batch/read", {"inputs": [{"id": i} for i in deal_ids]})
        deal_to_company = {r["from"]["id"]: r["to"][0]["toObjectId"] for r in links.get("results", []) if r.get("to")}
        if not deal_to_company:
            return {}
        names = self._request(
            "POST",
            "/crm/v3/objects/companies/batch/read",
            {"inputs": [{"id": str(c)} for c in set(deal_to_company.values())], "properties": ["name", "domain"]},
        )
        by_id = {c["id"]: c.get("properties", {}).get("name", "") for c in names.get("results", [])}
        return {d: by_id.get(str(c), "") for d, c in deal_to_company.items()}

    @staticmethod
    def _normalize(deal: dict[str, Any], company: str) -> dict[str, Any]:
        p = deal.get("properties", {})
        entered = p.get("hs_v2_date_entered_current_stage")
        days_in_stage = None
        if entered:
            try:
                days_in_stage = (_dt.datetime.now(_dt.timezone.utc) - _dt.datetime.fromisoformat(entered.replace("Z", "+00:00"))).days
            except ValueError:
                days_in_stage = None
        return {
            "deal_id": deal["id"],
            "deal_name": p.get("dealname") or f"deal {deal['id']}",
            "company": company,
            "amount": p.get("amount"),
            "stage": p.get("dealstage"),
            "close_date": (p.get("closedate") or "")[:10],
            "last_activity": (p.get("notes_last_updated") or p.get("hs_lastmodifieddate") or "")[:10],
            "days_in_stage": days_in_stage,
            "source": "hubspot",
        }

    def update_deal(self, deal_id: str, properties: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = self._request("PATCH", f"/crm/v3/objects/deals/{deal_id}", {"properties": properties})
        return result

    def ensure_writeback_properties(self) -> list[str]:
        """Create the b2b_* deal properties if they don't exist. Returns the names created."""
        existing = {p["name"] for p in self._request("GET", "/crm/v3/properties/deals").get("results", [])}
        created = []
        for prop in WRITEBACK_PROPERTIES:
            if prop["name"] not in existing:
                self._request("POST", "/crm/v3/properties/deals", {**prop, "groupName": "dealinformation"})
                created.append(prop["name"])
        return created
