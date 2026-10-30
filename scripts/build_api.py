"""Build the static chemistry-formulas API from the canonical dataset."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "formulas.json"
SOURCE = ROOT / "data" / "source.json"
API = ROOT / "api" / "v1"
INDIVIDUAL = API / "individual"
SCHEMAS = ROOT / "schemas"
REQUIRED = (
    "id",
    "name",
    "formula",
    "molecular_weight",
    "iupac_name",
    "smiles",
    "pubchem_cid",
    "category",
    "source",
    "source_url",
)
CATEGORIES = {"organic", "inorganic", "element", "acid", "base", "salt", "oxide", "biomolecule"}
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def load_records() -> list[dict]:
    records = json.loads(DATA.read_text(encoding="utf-8"))
    if not isinstance(records, list) or len(records) < 80:
        raise SystemExit(f"Expected at least 80 records in {DATA}")
    seen_ids: set[str] = set()
    seen_cids: set[int] = set()
    for record in records:
        missing = [field for field in REQUIRED if field not in record]
        if missing:
            raise SystemExit(f"{record.get('id', '?')}: missing fields {missing}")
        if not ID_PATTERN.fullmatch(record["id"]):
            raise SystemExit(f"invalid id: {record['id']}")
        if record["id"] in seen_ids:
            raise SystemExit(f"duplicate id: {record['id']}")
        if record["pubchem_cid"] in seen_cids:
            raise SystemExit(f"duplicate PubChem CID: {record['pubchem_cid']}")
        if not record["formula"].strip():
            raise SystemExit(f"{record['id']}: empty formula")
        if not isinstance(record["molecular_weight"], (int, float)) or record["molecular_weight"] <= 0:
            raise SystemExit(f"{record['id']}: invalid molecular weight")
        if record["category"] not in CATEGORIES:
            raise SystemExit(f"{record['id']}: invalid category")
        seen_ids.add(record["id"])
        seen_cids.add(record["pubchem_cid"])
    return sorted(records, key=lambda item: item["name"].casefold())


def schema() -> dict:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://chirag127.github.io/chemistry-formulas-api/schemas/data.json",
        "title": "Chemistry Formulas",
        "type": "array",
        "minItems": 80,
        "items": {
            "type": "object",
            "additionalProperties": False,
            "required": list(REQUIRED),
            "properties": {
                "id": {"type": "string", "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$"},
                "name": {"type": "string", "minLength": 2},
                "formula": {"type": "string", "minLength": 1},
                "molecular_weight": {"type": "number", "exclusiveMinimum": 0},
                "iupac_name": {"type": ["string", "null"]},
                "smiles": {"type": ["string", "null"]},
                "pubchem_cid": {"type": "integer", "minimum": 1},
                "category": {"type": "string", "enum": sorted(CATEGORIES)},
                "source": {"type": "string", "minLength": 2},
                "source_url": {"type": "string", "format": "uri"},
            },
        },
    }


def main() -> None:
    records = load_records()
    source = json.loads(SOURCE.read_text(encoding="utf-8")) if SOURCE.exists() else {}
    now = datetime.now(timezone.utc).isoformat()

    API.mkdir(parents=True, exist_ok=True)
    INDIVIDUAL.mkdir(parents=True, exist_ok=True)
    SCHEMAS.mkdir(parents=True, exist_ok=True)
    for existing in INDIVIDUAL.glob("*.json"):
        existing.unlink()

    (API / "data.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (DATA.parent / "index.json").write_text(
        json.dumps(
            [
                {
                    "id": item["id"],
                    "name": item["name"],
                    "formula": item["formula"],
                    "category": item["category"],
                }
                for item in records
            ],
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    for record in records:
        (INDIVIDUAL / f"{record['id']}.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    (API / "search-index.json").write_text(
        json.dumps(
            {
                "count": len(records),
                "searchableFields": ["name", "formula", "iupac_name", "category", "smiles"],
                "byId": {
                    record["id"]: {
                        "id": record["id"],
                        "name": record["name"],
                        "formula": record["formula"],
                        "category": record["category"],
                    }
                    for record in records
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (API / "meta.json").write_text(
        json.dumps(
            {
                "status": "healthy",
                "lastUpdated": now,
                "sourceUpdatedAt": source.get("retrievedAt"),
                "retrievedAt": source.get("retrievedAt"),
                "recordCount": len(records),
                "version": "1.0.0",
                "schemaVersion": "1.0.0",
                "source": source.get("source", "PubChem PUG REST (National Library of Medicine)"),
                "sourceHome": source.get("sourceHome", "https://pubchem.ncbi.nlm.nih.gov/"),
                "license": "Code: MIT; data: PubChem/NLM terms",
                "updateCadence": "manual",
                "fields": list(REQUIRED),
                "missingFromSource": source.get("missing", []),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (SCHEMAS / "data.json").write_text(
        json.dumps(schema(), indent=2) + "\n", encoding="utf-8"
    )
    (DATA.parent / "schema.json").write_text(
        json.dumps(schema(), indent=2) + "\n", encoding="utf-8"
    )
    print(f"Built {len(records)} records, {len(records)} individual endpoints")


if __name__ == "__main__":
    main()
