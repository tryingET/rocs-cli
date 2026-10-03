---
summary: "Schema + compatibility notes for `ontology/dist/*.json` artifacts."
read_when:
  - "When consuming rocs-cli dist artifacts from other tooling"
  - "When changing artifact JSON structure"
as_of: "2026-10-03"
---

# Dist artifacts (`ontology/dist/*.json`)

Artifacts written by rocs-cli are **offline-first** and should be:
- deterministic (same inputs → same bytes)
- additive where possible (consumers ignore unknown keys)

Notes:
- Since ROCS **0.4.7** (AK 5903), the default persisted schemas below replace those of the immutable 0.4.6 tag. This is an intentional pre-1.0 breaking simplification, not a compatibility/opt-in branch. `resolve.json` v3, `summary.json` v2 and unchanged `id_index.json` v1 are input-derived tracked projections: the same selected ontology inputs/profile produce the same bytes across clone/cache/output locations and tool-version stamps. They do not certify semantics or uniquely identify every possible input corpus.
- Runtime environment/provenance (`version`, absolute `repo`/`src_root`, checkout versus snapshot `source`, strict bindings) belongs in command/aggregate authority receipts and ordinary CLI diagnostics, not these three tracked projections. Other artifacts such as `diff.json` still contain environment fields and are outside this change. Explicit authored locator strings remain inputs; this does not rewrite absolute paths authored into manifests.
- Consumers must keep runtime authority receipts/locks untracked using their own ignore policy; the writer does not silently change Git tracking. `resolve --write-dist` still writes only its resolve artifact, not a new resolve authority receipt.
- When `ROCS_OUTPUT_ROOT` is unset, managed files retain the existing `ontology/dist/` or root-layout `dist/` location. When set, its value is the direct output directory anchored to `--repo`; every managed writer and cleanup operation uses it, while ontology source remains unchanged. This routing choice does not alter the three tracked projections' bytes; receipt `output_root` intentionally reports the configured output location. The external directory carries a persistent `.rocs-output-root.json` (`rocs-managed-output-root/1`) and must be absent, empty, or already marked for the same repo-relative path. Cleanup retains that marker and `.authority-receipt.lock`; it deletes only exact ROCS receipts, resolve/summary/index/diff/graph artifacts, and exact orphan writer temporaries. Unknown, nested, non-regular, multiply linked, substituted, or racing entries fail closed. Legacy unmarked default `dist/` cleanup remains a separate compatibility path.
- External output roots must stay strictly inside the repository, remain disjoint from the ontology source tree, avoid reserved/symlink paths, and cannot adopt nonempty unmarked directories.

## Generated consumer runtime custody
- Bootstrapped `scripts/rocs.sh` and `scripts/ci/full.sh` use only isolated system Python and the receipt digest embedded at generation time before trusted bundle code runs. The former forwards exact caller argv/stdin; the latter independently constructs only cleanup, validate, and build.
- The launcher opens `VENDORED_HASHES.json` and every listed file through no-follow descriptors, requires regular files with one link, and hashes while capturing. It writes only those bytes into an anonymous ZIP memfd, rereads the stored entries, then seals the descriptor against writes, growth, shrinkage, and further seal changes. ABI-compatible native extensions receive separately sealed and rehashed memfds.
- Cleanup, validate, and build fork without exec from that custody process. Consumer and temporary filesystem paths are never reopened after capture, so concurrent rename/replacement of `rocs.py`, imported Python modules, resources, or native extensions cannot change current-gate execution. A hardlinked receipt or listed file fails closed, and process exit releases the anonymous runtime without pathname cleanup.
- `rocs verify` applies the same regular/private-file admission rule and detects file mutation during its reads, but remains an identity/provenance check rather than a semantic or publication claim.

## Compatibility policy
- Each artifact includes `schema_version` (int).
- Backward-compatible changes: add new top-level keys or add new keys inside existing objects.
- Breaking changes: rename/remove keys, change meaning/types → bump `schema_version`.

## Files

### `resolve.json` (`schema_version: 3`)
Written by `rocs resolve --write-dist` and `rocs build`.

Notes:
- `rocs build` clears stale build artifacts (`resolve.json`, `summary.json`, `id_index.json`) before each run, so failed rebuilds do not leave prior success snapshots behind.

Top-level keys (v3):
- `schema_version` (int)
- `profile` (string|null)
- `layers` (list, sorted by name):
  - `name`, `kind`, `origin`, `source_contract`

Migration from v2: `version`, `repo`, `layers[].source` and `layers[].src_root` are removed.
Use `resolve --json` for runtime `repo`/`source`/`src_root`, and `version` or build/validate authority
receipts for the tool version. Ordinary CLI JSON/text resolution diagnostics are unchanged. Consumers of persisted
v2 files must handle the new schema deliberately; this is not an additive key-only migration.

### `summary.json` (`schema_version: 2`)
Written by `rocs build`.

Top-level keys (v2):
- `schema_version` (int)
- `profile` (string|null)
- `layers` (list of `{name, origin}`)
- `counts` (object)
- `concept_ids` (list of strings)
- `relation_ids` (list of strings)

Migration from v1: `version` and `repo` are removed; counts/IDs/layer information are retained.
Use `summary --json` for runtime location diagnostics, and `version` or authority receipts for the
tool version, not persisted summary fields.

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
- `layer_sources` (list of `{name, kind, locator_kind, origin, source, source_contract, src_root}`; optional `binding` records strict ref identity). `src_root` is an additive absolute-path diagnostic from 0.4.7; receipt schema remains 3.
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
