# Chemistry Formulas API

Free, static JSON API of **111 chemical compounds** with molecular formulas, molecular weights, IUPAC names, SMILES, PubChem identifiers, and teaching categories.

- **Live API:** https://chirag127.github.io/chemistry-formulas-api/api/v1/data.json
- **Interactive docs:** https://chirag127.github.io/chemistry-formulas-api/
- **Contract:** [openapi.yaml](./openapi.yaml)
- **Repo:** https://github.com/chirag127/chemistry-formulas-api

No authentication, no rate limit, no server. The JSON files live in Git and are served by GitHub Pages.

## Endpoints

| Method | URL | Description |
| --- | --- | --- |
| `GET` | `/api/v1/data.json` | All compound records |
| `GET` | `/api/v1/individual/{id}.json` | One compound, for example `/api/v1/individual/ethanol.json` |
| `GET` | `/api/v1/search-index.json` | Compact id/name/formula/category index |
| `GET` | `/api/v1/meta.json` | Count, source, retrieval date, schema version, license |

Base URL:

```text
https://chirag127.github.io/chemistry-formulas-api
```

## Record shape

```json
{
  "id": "ethanol",
  "name": "Ethanol",
  "formula": "C2H6O",
  "molecular_weight": 46.07,
  "iupac_name": "ethanol",
  "smiles": "CCO",
  "pubchem_cid": 702,
  "category": "organic",
  "source": "PubChem PUG REST (National Library of Medicine)",
  "source_url": "https://pubchem.ncbi.nlm.nih.gov/compound/702"
}
```

| Field | Meaning |
| --- | --- |
| `id` | Stable URL-safe identifier |
| `formula` | Molecular formula as reported by PubChem |
| `molecular_weight` | Molecular weight in g/mol |
| `iupac_name` | PubChem IUPAC name, where available |
| `smiles` | Connectivity SMILES, where available |
| `pubchem_cid` | PubChem compound identifier |
| `category` | Editorial teaching category: organic, inorganic, element, acid, base, salt, oxide, biomolecule |
| `source_url` | Direct PubChem compound page |

## Examples

```bash
curl https://chirag127.github.io/chemistry-formulas-api/api/v1/individual/ethanol.json
```

```javascript
const response = await fetch(
  'https://chirag127.github.io/chemistry-formulas-api/api/v1/data.json',
);
const compounds = await response.json();
const acids = compounds.filter((compound) => compound.category === 'acid');
```

## Data source and refresh

The dataset is resolved from [PubChem PUG REST](https://pubchem.ncbi.nlm.nih.gov/rest/pug/), operated by the U.S. National Library of Medicine. The canonical compound list is in [`scraper/compounds.py`](./scraper/compounds.py); chemistry categories are editorial.

```bash
python -m pip install -r requirements.txt
python scraper/fetch.py
python scripts/build_api.py
python -m pytest -q
```

`scraper/fetch.py` writes the raw normalised data to `data/formulas.json`. `scripts/build_api.py` generates the public endpoints, individual files, search index, metadata, and JSON Schema. Never hand-edit generated `api/` files.

A GitHub Actions workflow refreshes the data on a manual dispatch and a monthly schedule. If PubChem is unavailable, the workflow fails without replacing the last known good data.

## Project layout

```text
scraper/compounds.py      Canonical source list and categories
scraper/fetch.py          PubChem fetch and normalisation
scripts/build_api.py      Generates api/v1, schemas, index, and meta
scripts/validate.py       Standalone validation
tests/test_api.py         Pytest suite
data/                     Normalised source data
api/v1/                   Public static endpoints
schemas/                  JSON Schema
website/index.html        Human-readable API documentation
openapi.yaml              OpenAPI 3.1 contract
```

## Tests

```bash
python -m pytest -q
python scripts/validate.py
```

The tests check the JSON Schema, minimum record count, unique ids and PubChem CIDs, positive molecular weights, non-empty formulas, individual endpoint consistency, search index, and metadata count.

## License

Code is MIT. Compound data is retrieved from PubChem; see the [PubChem terms and policies](https://pubchem.ncbi.nlm.nih.gov/docs/legal-notices) and the source page for each record. The repository does not claim ownership of PubChem records.
