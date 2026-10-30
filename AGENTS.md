# chemistry-formulas-api — agent guide

Static JSON API for chemical compound formulas, sourced from PubChem and served by GitHub Pages.

## Commands

```bash
python -m pip install -r requirements.txt
python scraper/fetch.py
python scripts/build_api.py
python -m pytest -q
python scripts/validate.py
```

Windows local interpreter: `py` works in place of `python`.

## Rules

- **Do not hand-edit generated files.** `api/v1/data.json`, `api/v1/individual/*`, `api/v1/search-index.json`, `api/v1/meta.json`, `data/index.json`, `data/schema.json`, and `schemas/data.json` are generated.
- **Canonical source list:** `scraper/compounds.py`. Add a compound there; keep the name resolvable by PubChem, and choose a category from `organic`, `inorganic`, `element`, `acid`, `base`, `salt`, `oxide`, or `biomolecule`.
- **Never invent chemical data.** If PubChem returns no record, omit the compound and report it in `data/source.json`; do not fill a placeholder.
- **Source and license:** cite PubChem and keep `source_url` on every record. Code is MIT; data remains subject to PubChem/NLM terms.
- **Preserve last-known-good data on failure.** The fetch script writes only after a successful run; do not commit partial downloads.
- **Tests before commit:** `python -m pytest -q` and `python scripts/validate.py`.
- **No secrets** in files, issues, logs, or commit messages.
- **Git:** main branch, conventional commits, no force-push. The update workflow commits generated data back to main.
- **Refresh cadence:** manual or monthly workflow dispatch. PubChem content can change; review new or changed records before publishing.
- **Endpoints:** keep `openapi.yaml`, README, and website in sync with the generated `api/v1` paths.

## Data shape

Required fields: `id`, `name`, `formula`, `molecular_weight`, `iupac_name`, `smiles`, `pubchem_cid`, `category`, `source`, `source_url`. `id` is lowercase kebab-case; CIDs and ids are unique; molecular weight is positive; formulas are non-empty.
