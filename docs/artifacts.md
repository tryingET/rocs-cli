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
- When `ROCS_OUTPUT_ROOT` is unset, managed files retain the existing `ontology/dist/` or root-layout `dist/` location and bytes. When set, its value is the direct output directory anchored to `--repo`; every managed writer and cleanup operation uses it, while ontology source remains unchanged. The external directory carries a persistent `.rocs-output-root.json` (`rocs-managed-output-root/1`) and must be absent, empty, or already marked for the same repo-relative path. Cleanup removes only owned artifact files and retains this marker directory so it never performs an inode-ambiguous pathname deletion.
- External output roots must stay strictly inside the repository, remain disjoint from the ontology source tree, avoid reserved/symlink paths, and cannot adopt nonempty unmarked directories.

## Generated consumer runtime custody
- A bootstrapped `scripts/ci/full.sh` uses only isolated system Python and the receipt digest embedded at generation time before trusted bundle code runs.
- The launcher opens `VENDORED_HASHES.json` and every listed file through no-follow descriptors, requires regular files with one link, and hashes while capturing. It writes only those bytes into an anonymous ZIP memfd, rereads the stored entries, then seals the descriptor against writes, growth, shrinkage, and further seal changes. ABI-compatible native extensions receive separately sealed and rehashed memfds.
- Cleanup, validate, and build fork without exec from that custody process. Consumer and temporary filesystem paths are never reopened after capture, so concurrent rename/replacement of `rocs.py`, imported Python modules, resources, or native extensions cannot change current-gate execution. A hardlinked receipt or listed file fails closed, and process exit releases the anonymous runtime without pathname cleanup.
- `rocs verify` applies the same regular/private-file admission rule and detects file mutation during its reads, but remains an identity/provenance check rather than a semantic or publication claim.

## Compatibility policy
- Each artifact includes `schema_version` (int).
- Backward-compatible changes: add new top-level keys or add new keys inside existing objects.
- Breaking changes: rename/remove keys, change meaning/types → bump `schema_version`.

## Files

### `resolve.json` (`schema_version: 2`)
Written by `rocs resolve --write-dist` and `rocs build`.

Notes:
- `rocs build` clears stale build artifacts (`resolve.json`, `summary.json`, `id_index.json`) before each run, so failed rebuilds do not leave prior success snapshots behind.

Top-level keys (v2):
- `schema_version` (int)
- `version` (string; rocs-cli version)
- `repo` (string; repo root path used for this run)
- `profile` (string|null)
- `layers` (list):
  - `name`, `kind`, `origin`, `source`, `src_root`

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

### `authority-receipt.json` (`schema_version: 3`)
Aggregate authority/provenance artifact written by `rocs build` and `rocs validate` when the repo has an `ontology/` root.

Notes:
- standalone command runs rewrite the aggregate to the current command and prune stale per-command receipts from previous standalone runs
- wrapper-driven multi-step runs (for example `scripts/ci/full.sh`) set `ROCS_AUTHORITY_AGGREGATE=1`, so the aggregate preserves both `validate` and `build` receipts for that run series

Purpose:
- preserve command-by-command authority evidence instead of overwriting the last writer
- make run authority/provenance explicit for local-dev vs strict ref-resolving workflows
- expose which source satisfied each layer (`path|workspace`)

Top-level keys (v3):
- `schema_version` (int)
- `version` (string; rocs-cli version)
- `repo` (string)
- `last_command` (`build|validate`)
- `command_files` (object mapping command → `authority-receipt.<command>.json`)
- `commands` (object mapping command → per-command receipt payload)
- `output_root` (string, optional; repo-relative managed output directory when `ROCS_OUTPUT_ROOT` is active)

### `authority-receipt.<command>.json` (`schema_version: 3`)
Per-command authority/provenance artifact for `build` / `validate`.

Top-level keys (v3):
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
- `output_root` (string, optional; repo-relative managed output directory when `ROCS_OUTPUT_ROOT` is active)
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
