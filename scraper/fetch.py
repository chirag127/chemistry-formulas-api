"""Fetch compound formulas and identifiers from PubChem PUG REST.

Run from the repository root:
    python scraper/fetch.py

The raw response is normalised into data/formulas.json. Individual endpoint
files and the search index are generated separately by scripts/build_api.py.
"""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

from compounds import COMPOUNDS

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PUG_URL = (
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/property/"
    "MolecularFormula,MolecularWeight,IUPACName,ConnectivitySMILES/JSON"
)
SOURCE = "PubChem PUG REST (National Library of Medicine)"
SOURCE_HOME = "https://pubchem.ncbi.nlm.nih.gov/"
REQUEST_DELAY_SECONDS = 0.26


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug


def fetch_record(session: requests.Session, name: str, category: str) -> dict | None:
    url = PUG_URL.format(name=quote(name))
    response = session.get(url, timeout=30)
    if response.status_code == 404:
        print(f"missing: {name}", file=sys.stderr)
        return None
    response.raise_for_status()
    properties = response.json().get("PropertyTable", {}).get("Properties", [])
    if not properties:
        print(f"empty: {name}", file=sys.stderr)
        return None

    item = properties[0]
    cid = item.get("CID")
    formula = item.get("MolecularFormula")
    weight = item.get("MolecularWeight")
    if not cid or not formula or not weight:
        print(f"incomplete: {name}", file=sys.stderr)
        return None

    return {
        "id": slugify(name),
        "name": name,
        "formula": formula,
        "molecular_weight": float(weight),
        "iupac_name": item.get("IUPACName") or None,
        "smiles": item.get("ConnectivitySMILES") or item.get("CanonicalSMILES") or None,
        "pubchem_cid": int(cid),
        "category": category,
        "source": SOURCE,
        "source_url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}",
    }


def main() -> int:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "ORIZ.IN chemistry-formulas-api/1.0 (+https://oriz.in/)",
            "Accept": "application/json",
        }
    )
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    records: list[dict] = []
    seen_ids: set[str] = set()
    missing: list[str] = []

    for index, entry in enumerate(COMPOUNDS, start=1):
        name = entry["name"]
        try:
            record = fetch_record(session, name, entry["category"])
        except requests.RequestException as exc:
            print(f"request failed for {name}: {exc}", file=sys.stderr)
            missing.append(name)
            continue
        if record is None:
            missing.append(name)
        elif record["id"] in seen_ids:
            print(f"duplicate id skipped: {name}", file=sys.stderr)
            missing.append(name)
        else:
            seen_ids.add(record["id"])
            records.append(record)
        if index < len(COMPOUNDS):
            time.sleep(REQUEST_DELAY_SECONDS)

    if len(records) < 80:
        print(
            f"Only {len(records)} records fetched; expected at least 80. Aborting.",
            file=sys.stderr,
        )
        return 1

    records.sort(key=lambda item: item["name"].casefold())
    (DATA_DIR / "formulas.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (DATA_DIR / "source.json").write_text(
        json.dumps(
            {
                "source": SOURCE,
                "sourceHome": SOURCE_HOME,
                "retrievedAt": datetime.now(timezone.utc).isoformat(),
                "requested": len(COMPOUNDS),
                "returned": len(records),
                "missing": missing,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(records)} records to {DATA_DIR / 'formulas.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
