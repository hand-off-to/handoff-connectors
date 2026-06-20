#!/usr/bin/env python3
"""Validate connector manifests against the JSON Schema and the catalog index."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schema" / "connector.schema.json"
CONNECTORS_DIR = ROOT / "connectors"
CATALOG_PATH = ROOT / "catalog.yaml"


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def load_yaml(path: Path) -> dict:
    with path.open() as fh:
        return yaml.safe_load(fh)


def manifest_paths() -> list[Path]:
    return sorted(p for p in CONNECTORS_DIR.rglob("*.yaml"))


def validate_data(schema: dict, data: dict) -> list[str]:
    validator = Draft202012Validator(schema)
    return [err.message for err in sorted(validator.iter_errors(data), key=str)]


def catalog_errors(catalog: dict, manifests: list[tuple[str, dict]]) -> list[str]:
    errors: list[str] = []
    entries = {e["key"]: e for e in (catalog.get("connectors") or [])}
    seen: set[str] = set()
    for relpath, manifest in manifests:
        key = manifest.get("key")
        seen.add(key)
        entry = entries.get(key)
        if entry is None:
            errors.append(f"{key}: manifest present but missing from catalog.yaml")
            continue
        if entry.get("path") != relpath:
            errors.append(f"{key}: catalog path {entry.get('path')!r} != {relpath!r}")
        for field in ("family", "version"):
            if entry.get(field) != manifest.get(field):
                errors.append(
                    f"{key}: catalog {field} {entry.get(field)!r} != manifest {manifest.get(field)!r}"
                )
    for key in entries:
        if key not in seen:
            errors.append(f"{key}: listed in catalog.yaml but no manifest found")
    return errors


def main() -> int:
    schema = load_schema()
    paths = manifest_paths()
    errors: list[str] = []
    manifests: list[tuple[str, dict]] = []
    for path in paths:
        data = load_yaml(path)
        rel = str(path.relative_to(ROOT))
        manifests.append((rel, data))
        for msg in validate_data(schema, data):
            errors.append(f"{rel}: {msg}")
    if CATALOG_PATH.exists():
        errors += catalog_errors(load_yaml(CATALOG_PATH), manifests)
    else:
        errors.append("catalog.yaml: missing")
    if errors:
        print("INVALID:")
        for err in errors:
            print(f"  - {err}")
        return 1
    print(f"OK: {len(paths)} manifest(s) valid and consistent with catalog")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
