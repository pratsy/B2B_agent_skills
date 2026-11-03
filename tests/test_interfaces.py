"""CLI, MCP server, and HTTP server."""

import asyncio
import json

import pytest

from b2b_agent_skills import MockProvider
from b2b_agent_skills.cli import main


def test_cli_list_and_show(capsys):
    assert main(["list"]) == 0
    assert len(capsys.readouterr().out.split()) == 45
    assert main(["show", "deal-risk-assessor", "--schema"]) == 0
    assert json.loads(capsys.readouterr().out)["title"] == "deal-risk-assessor"


def test_cli_run_and_unknown_skill(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("PROVIDER", raising=False)
    path = tmp_path / "in.json"
    path.write_text('{"deal_id": "opp_1"}')
    assert main(["run", "deal-risk-assessor", "-i", str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["deal_id"] == "opp_5521"
    assert main(["run", "not-a-skill"]) == 1
    assert "Unknown skill" in capsys.readouterr().err


def test_cli_eval_writes_reports(tmp_path, capsys):
    report = tmp_path / "r.json"
    code = main(["eval", "--provider", "mock", "--skill", "renewal-risk-scorer", "--json", str(report), "--min-pass-rate", "1"])
    assert code == 0
    assert json.loads(report.read_text())["pass_rate"] == 1.0


def test_mcp_server_exposes_tools_and_prompts(monkeypatch):
    pytest.importorskip("mcp")
    monkeypatch.delenv("PROVIDER", raising=False)
    from b2b_agent_skills.mcp_server import build_server

    server = build_server()
    tools = {t.name for t in asyncio.run(server.list_tools())}
    assert tools == {"list_skills", "get_skill"}, "run_skill must only appear when a real provider is configured"
    prompts = asyncio.run(server.list_prompts())
    assert len(prompts) == 45
    rendered = asyncio.run(server.get_prompt("deal-risk-assessor", {"input_json": '{"deal_id": "opp_9"}'}))
    text = rendered.messages[0].content.text
    assert "MEDDPICC" in text and "opp_9" in text


def test_mcp_server_adds_run_skill_with_a_real_provider(monkeypatch):
    pytest.importorskip("mcp")
    monkeypatch.setenv("PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-used")
    from b2b_agent_skills.mcp_server import build_server

    tools = {t.name for t in asyncio.run(build_server().list_tools())}
    assert "run_skill" in tools


def test_http_server_requires_auth_and_runs_skills():
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from b2b_agent_skills.server import create_app

    client = TestClient(create_app(token="s3cret", provider=MockProvider()))
    assert client.get("/health").status_code == 200
    assert client.get("/v1/skills").status_code == 401
    assert client.get("/v1/skills", headers={"Authorization": "Bearer wrong"}).status_code == 401

    auth = {"Authorization": "Bearer s3cret"}
    assert len(client.get("/v1/skills", headers=auth).json()) == 45
    assert client.get("/v1/skills/nope", headers=auth).status_code == 404
    res = client.post("/v1/skills/pipeline-health-monitor/run", headers=auth, json={"input": {"open_pipeline_value": 1}})
    assert res.status_code == 200 and res.json()["output"]["overall_health"] == "at risk"
    big = {"input": {"blob": "x" * 300_000}}
    assert client.post("/v1/skills/pipeline-health-monitor/run", headers=auth, json=big).status_code == 413


def test_http_server_refuses_to_start_without_a_token(monkeypatch):
    pytest.importorskip("fastapi")
    from b2b_agent_skills.server import create_app

    monkeypatch.delenv("B2B_SKILLS_API_TOKEN", raising=False)
    monkeypatch.delenv("B2B_SKILLS_ALLOW_NO_AUTH", raising=False)
    with pytest.raises(RuntimeError, match="B2B_SKILLS_API_TOKEN"):
        create_app(provider=MockProvider())
