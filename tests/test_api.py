"""Validated contract tests for the chemistry-formulas API."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "formulas.json"
SCHEMA = ROOT / "schemas" / "data.json"
API = ROOT / "api" / "v1"


@pytest.fixture(scope="module")
def records() -> list[dict]:
    return json.loads(DATA.read_text(encoding="utf-8"))


def test_schema(records: list[dict]) -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.validate(records, schema)


def test_minimum_dataset_and_unique_keys(records: list[dict]) -> None:
    assert len(records) >= 100
    ids = [record["id"] for record in records]
    cids = [record["pubchem_cid"] for record in records]
    assert len(ids) == len(set(ids))
    assert len(cids) == len(set(cids))


def test_no_scaffold_or_placeholder(records: list[dict]) -> None:
    for record in records:
        assert record["id"] != "chemistry-formulas"
        assert "status" not in record
        assert record["formula"].strip()
        assert record["molecular_weight"] > 0
        assert "pubchem" in record["source_url"]


def test_individual_endpoints_match_dataset(records: list[dict]) -> None:
    individual = API / "individual"
    files = sorted(individual.glob("*.json"))
    assert len(files) == len(records)
    by_id = {record["id"]: record for record in records}
    for file in files:
        assert file.stem in by_id
        assert json.loads(file.read_text(encoding="utf-8")) == by_id[file.stem]


def test_public_data_matches_source(records: list[dict]) -> None:
    public = json.loads((API / "data.json").read_text(encoding="utf-8"))
    assert public == records


def test_search_index_and_meta(records: list[dict]) -> None:
    index = json.loads((API / "search-index.json").read_text(encoding="utf-8"))
    meta = json.loads((API / "meta.json").read_text(encoding="utf-8"))
    assert index["count"] == len(records)
    assert set(index["byId"]) == {record["id"] for record in records}
    assert meta["recordCount"] == len(records)
    assert meta["status"] == "healthy"
    assert "PubChem" in meta["source"]
