import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import validate  # noqa: E402

SCHEMA = json.loads(
    (Path(__file__).resolve().parent.parent / "schema" / "connector.schema.json").read_text()
)

VALID_MCP = {
    "key": "github-mcp",
    "family": "mcp",
    "version": 1,
    "name": "GitHub MCP",
    "type": "mcp_stdio_container",
    "status": "active",
    "definition": {
        "runtime": "handoff-mcp-runtime",
        "command": "docker",
        "args": ["run", "-i", "--rm", "ghcr.io/github/github-mcp-server"],
        "env_names": ["GITHUB_PERSONAL_ACCESS_TOKEN"],
        "inputs": [{"name": "github_org", "label": "Github Org", "default": ""}],
        "instruction_template": "scoped to {{github_org}}",
        "doc_url": "https://example.com/docs",
    },
}

VALID_SKILL = {
    "key": "example-skill",
    "family": "skill",
    "version": 1,
    "name": "Example Skill",
    "type": "skill_prompt",
    "status": "active",
    "definition": {"instructions": "Be helpful.", "inputs": [], "doc_url": "https://example.com/docs"},
}


def test_valid_mcp_manifest_passes():
    assert validate.validate_data(SCHEMA, VALID_MCP) == []


def test_valid_skill_manifest_passes():
    assert validate.validate_data(SCHEMA, VALID_SKILL) == []


def test_bad_key_pattern_fails():
    bad = {**VALID_MCP, "key": "GitHub MCP"}
    assert validate.validate_data(SCHEMA, bad)


def test_missing_required_field_fails():
    bad = {k: v for k, v in VALID_MCP.items() if k != "version"}
    assert validate.validate_data(SCHEMA, bad)


def test_mcp_with_api_type_fails():
    bad = {**VALID_MCP, "type": "api_openapi"}
    assert validate.validate_data(SCHEMA, bad)


def test_skill_without_instructions_fails():
    bad = {**VALID_SKILL, "definition": {"inputs": []}}
    assert validate.validate_data(SCHEMA, bad)


def test_catalog_mismatch_version_reported():
    catalog = {"connectors": [{"key": "github-mcp", "family": "mcp", "version": 2, "path": "connectors/mcp/github.yaml"}]}
    manifests = [("connectors/mcp/github.yaml", VALID_MCP)]  # version 1
    errs = validate.catalog_errors(catalog, manifests)
    assert any("version" in e for e in errs)


def test_catalog_missing_entry_reported():
    catalog = {"connectors": []}
    manifests = [("connectors/mcp/github.yaml", VALID_MCP)]
    errs = validate.catalog_errors(catalog, manifests)
    assert any("github-mcp" in e for e in errs)


def test_catalog_orphan_entry_reported():
    catalog = {"connectors": [{"key": "ghost", "family": "mcp", "version": 1, "path": "connectors/mcp/ghost.yaml"}]}
    errs = validate.catalog_errors(catalog, [])
    assert any("ghost" in e for e in errs)


def test_repo_is_valid_end_to_end():
    assert validate.main() == 0


def test_missing_doc_url_fails():
    bad = {**VALID_MCP, "definition": {k: v for k, v in VALID_MCP["definition"].items() if k != "doc_url"}}
    assert validate.validate_data(SCHEMA, bad)


def test_input_description_accepted():
    ok = {
        **VALID_MCP,
        "definition": {
            **VALID_MCP["definition"],
            "inputs": [{"name": "github_org", "label": "Organization", "description": "The org.", "required": True, "default": ""}],
        },
    }
    assert validate.validate_data(SCHEMA, ok) == []


def test_credential_descriptor_accepted():
    ok = {
        **VALID_MCP,
        "definition": {
            **VALID_MCP["definition"],
            "credential": {"label": "GitHub token", "description": "A PAT.", "required": True},
        },
    }
    assert validate.validate_data(SCHEMA, ok) == []
