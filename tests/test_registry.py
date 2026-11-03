"""Every skill is complete, consistent across surfaces, and its schema is usable."""

import json
import pathlib
import subprocess
import sys

import pytest
from jsonschema import Draft202012Validator

from b2b_agent_skills import get_skill, list_skills
from b2b_agent_skills.errors import SkillNotFoundError
from b2b_agent_skills.registry import normalize_name

ROOT = pathlib.Path(__file__).resolve().parents[1]
PACK_SLUGS = sorted(p.parent.name for p in ROOT.glob("b2b-agent-skills-*/skills/*/README.md"))


def test_45_skills_documented_and_packaged():
    assert len(PACK_SLUGS) == 45
    assert list_skills() == PACK_SLUGS


@pytest.mark.parametrize("slug", PACK_SLUGS)
def test_skill_is_complete(slug):
    skill = get_skill(slug)
    assert skill.name == slug, "SKILL.md frontmatter name must match its folder"
    assert len(skill.description) > 40
    assert "Use when" in skill.description, "description must say when to use the skill (Claude Code uses it to auto-invoke)"
    assert skill.instructions
    assert "schema.json" in skill.instructions, "SKILL.md must point at its output schema"


@pytest.mark.parametrize("slug", PACK_SLUGS)
def test_schema_is_valid_strict_and_matches_its_example(slug):
    schema = get_skill(slug).schema
    Draft202012Validator.check_schema(schema)
    assert schema["type"] == "object" and schema["required"]
    # The README's own worked example must satisfy the generated schema.
    example = schema["examples"][0]
    assert not list(Draft202012Validator(schema).iter_errors(example))

    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "object":
                assert node.get("additionalProperties") is False, f"{slug}: structured outputs need additionalProperties: false"
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(get_skill(slug).output_schema)


def test_output_schema_strips_annotations():
    out = get_skill("deal-risk-assessor").output_schema
    assert not {"$schema", "title", "description", "examples"} & set(out)


def test_schemas_are_in_sync_with_readmes():
    result = subprocess.run([sys.executable, "scripts/generate_schemas.py", "--check"], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_name_normalization_and_unknown_skill():
    assert normalize_name("Deal_Risk_Assessor") == "deal-risk-assessor"
    assert get_skill("deal_risk_assessor").name == "deal-risk-assessor"
    with pytest.raises(SkillNotFoundError, match="deal-risk-assessor"):
        get_skill("deal-risk")


def test_plugin_manifests_are_valid_json_and_point_at_skills():
    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    marketplace = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    for path in plugin["skills"]:
        assert (ROOT / path).is_dir()
    assert plugin["version"] == __import__("b2b_agent_skills").__version__
    assert marketplace["plugins"][0]["name"] == plugin["name"]
