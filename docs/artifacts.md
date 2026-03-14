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

### `authority-receipt.json` (`schema_version: 2`)
Aggregate authority/provenance artifact written by `rocs build` and `rocs validate` when the repo has an `ontology/` root.

Notes:
- standalone command runs rewrite the aggregate to the current command and prune stale per-command receipts from previous standalone runs
- wrapper-driven multi-step runs (for example `scripts/ci/full.sh`) set `ROCS_AUTHORITY_AGGREGATE=1`, so the aggregate preserves both `validate` and `build` receipts for that run series

Purpose:
- preserve command-by-command authority evidence instead of overwriting the last writer
- make run authority/provenance explicit for local-dev vs strict ref-resolving workflows
- expose which source satisfied each layer (`path|workspace|cache|gitlab`)
- make legacy GitLab fallback visible to CI/archive consumers

Top-level keys (v2):
- `schema_version` (int)
- `version` (string; rocs-cli version)
- `repo` (string)
- `last_command` (`build|validate`)
- `command_files` (object mapping command → `authority-receipt.<command>.json`)
- `commands` (object mapping command → per-command receipt payload)

### `authority-receipt.<command>.json` (`schema_version: 2`)
Per-command authority/provenance artifact for `build` / `validate`.

Top-level keys (v2):
- `schema_version` (int)
- `version` (string; rocs-cli version)
- `command` (`build|validate`)
- `ok` (bool)
- `repo` (string)
- `profile` (string|null)
- `ci_profile` (string|null; from `ROCS_CI_PROFILE` when set)
- `authority_mode` (`local_only|no_ref_layers|best_effort_workspace_loose|strict_ref_resolution|error`)
- `authoritative` (bool; true only for `strict_ref_resolution`)
- `resolve_refs_requested` (bool)
- `workspace_ref_mode` (`strict|loose`)
- `ref_layers_present` (bool)
- `ref_layer_count` (int)
- `loose_workspace_ref_layers_used` (int)
- `layer_sources` (list of `{name, kind, locator_kind, origin, source}`)
- `locator_kinds_present` (sorted list)
- `legacy_gitlab_fallback_used` (bool)
- `result` (object, optional; currently validation finding counts)
- `error` (object, optional; normalized `kind`/`message`/`details` when artifact was emitted on handled command failure)

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
