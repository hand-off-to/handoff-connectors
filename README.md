# handoff-connectors

Public registry of built-in connectors for [hand-off.to](https://hand-off.to).

Each connector is a data-only manifest under `connectors/<family>/`, validated
against `schema/connector.schema.json`. `catalog.yaml` indexes every connector and
its current version. Self-hosted handoff instances fetch these files over HTTPS and
install them into their own database; nothing here is executed by this repo.

Families: `mcp` (containerized MCP servers), `api` (OpenAPI tool sets), `skill`
(prompt-injected guidance).

## Validate locally

    pip install -r requirements-dev.txt
    python tools/validate.py
    pytest

## Versioning

`version` is a monotonically increasing integer per connector. Bump it whenever a
manifest changes so instances can detect and offer the update.
