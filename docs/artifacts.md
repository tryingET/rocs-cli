---
summary: "Schema + compatibility notes for `ontology/dist/*.json` artifacts."
read_when:
  - "When consuming rocs-cli dist artifacts from other tooling"
  - "When changing artifact JSON structure"
as_of: "2026-01-16"
---

# Dist artifacts (`ontology/dist/*.json`)

Artifacts written by rocs-cli are **offline-first** and should be:
- deterministic (same inputs → same bytes)
- additive where possible (consumers ignore unknown keys)

Notes:
- Some fields are absolute paths (e.g. `repo`, `src_root`, `baseline_repo`) and are not intended to be stable across machines.

## Compatibility policy
- Each artifact includes `schema_version` (int).
- Backward-compatible changes: add new top-level keys or add new keys inside existing objects.
- Breaking changes: rename/remove keys, change meaning/types → bump `schema_version`.

## Files

### `resolve.json` (`schema_version: 1`)
Written by `rocs resolve --write-dist` and `rocs build`.

Top-level keys (v1):
- `schema_version` (int)
- `version` (string; rocs-cli version)
- `repo` (string; repo root path used for this run)
- `profile` (string|null)
- `layers` (list):
  - `name`, `kind`, `origin`, `source`, `src_root`, `cache_repo_root`

### `summary.json` (`schema_version: 1`)
Written by `rocs build`.

Top-level keys (v1):
- `schema_version` (int)
- `version` (string; rocs-cli version)
- `repo` (string)
- `profile` (string|null)
- `layers` (list of `{name, origin}`)
- `counts` (object)
- `concept_ids` (list of strings)
- `relation_ids` (list of strings)

### `id_index.json` (`schema_version: 1`)
Written by `rocs build`.

Top-level keys (v1):
- `schema_version` (int)
- `items` (list of objects; see `src/rocs_cli/id_index.py`)

### `diff.json` (`schema_version: 1`)
Written by `rocs diff`.

Top-level keys (v1):
- `schema_version` (int)
- `version` (string; rocs-cli version)
- `repo` (string)
- `profile` (string|null)
- `baseline` (string)
- `baseline_repo` (string)
- `diff` (object)
- `breaking` (object)
