"""Standalone validation for CI and local checks."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parent.parent
records = json.loads((ROOT / "data" / "formulas.json").read_text(encoding="utf-8"))
schema = json.loads((ROOT / "schemas" / "data.json").read_text(encoding="utf-8"))
index = json.loads((ROOT / "api" / "v1" / "search-index.json").read_text(encoding="utf-8"))
meta = json.loads((ROOT / "api" / "v1" / "meta.json").read_text(encoding="utf-8"))

errors: list[str] = []
try:
    jsonschema.validate(records, schema)
except jsonschema.ValidationError as exc:
    errors.append(f"schema: {exc.message}")

if len(records) < 100:
    errors.append(f"record count {len(records)} is below 100")
if len({record["id"] for record in records}) != len(records):
    errors.append("duplicate ids")
if len({record["pubchem_cid"] for record in records}) != len(records):
    errors.append("duplicate PubChem CIDs")
if index.get("count") != len(records):
    errors.append("search index count mismatch")
if meta.get("recordCount") != len(records):
    errors.append("meta count mismatch")
if meta.get("status") != "healthy":
    errors.append("meta status is not healthy")

if errors:
    print("\n".join(f"ERROR: {error}" for error in errors))
    sys.exit(1)
print(f"validated {len(records)} records")
