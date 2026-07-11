---
summary: "Changelog for rocs-cli."
read_when:
  - "Preparing a release or reviewing user-visible changes."
---

# Changelog

## [Unreleased]

### Removed
- **Breaking (Wave 1):** removed `audit-fleet.py`, `open-remediation-batch.sh`, `run-fleet-audit-nightly.py`, `run-fleet-audit-nightly.sh`, `bootstrap-repo.sh`, `vendor-to.sh`, `bump_version.py`, `bench.py`, and `gen_bench_repo.py`; there are no compatibility shims.
- **Breaking (Wave 1):** removed their script-specific tests. Scheduler assets now invoke `rocs fleet run`.

### Added
- Wave 4 proposal-only constitutional rule foundry with strict digest-bound candidates, a closed deterministic predicate DSL, challenge/differential/mutation evaluation, and a stable multi-objective fleet repair Pareto frontier. It cannot activate rules, certify validity, suppress findings, select/apply bids, execute generated code, or mutate ontology/fleet state.
- Wave 3 deterministic semantic transactions with strict digest-bound prepare/simulate/apply/verify/rollback contracts, separate operator approval, owner/ref boundaries, same-filesystem staging, content-addressed receipts, and byte-exact compensation/rollback. Only `transaction apply` mutates ontology files; no shell/model/network execution is introduced.
- Wave 2 optional intelligence membrane: deterministic content-addressed context capsules, strict proposal validation, externally approved schema-1 ontology-operation plan compilation, and an authority-free adapter protocol. No model/network is required and compilation performs no ontology mutation.
- Closed first-class CLI operations for fleet observe/plan/apply/run, repository bootstrap/converge, vendor, release plan/apply, verify/cleanup/doctor, benchmark, and generator.
- Schema-2 pinned self-contained consumer lock and isolated acceptance fixture.

### Changed
- **Breaking:** remediation apply now requires schema-version 2 scorecards with policy/evidence SHA-256 digests and rejects any input that differs from a fresh deterministic fleet audit.
- **Breaking:** fleet policies now reject non-boolean or unknown capabilities, duplicate normalized repository paths, and repository paths outside the workspace.
- **Breaking:** fleet auditing now requires complete, schema-exact SHA-256 vendored manifests and verifies every covered regular file; empty, malformed, incomplete, traversal, symlink, and unexpected package-file cases fail closed.
- Vendoring now builds a complete sibling staging tree under an exclusive lock and atomically publishes it with rollback to the prior tree on publication failure.
- Nightly stale-artifact cleanup now verifies containment beneath the resolved artifact root before deletion.
- **Breaking:** the CI wrapper now rejects non-repository roots, missing manifests, root paths, and cleanup targets that are symlinks or resolve outside `ROCS_REPO`.
- Bootstrap now builds and verifies a complete sibling stage, publishes it with a same-filesystem atomic rename, and restores the prior tree on every injected late failure.
- Added an importable versioned closed capability registry used by bootstrap, fleet audit validation, and remediation policy logic; unknown classes and capabilities fail closed.
- Hardened ROCS manifest layer parsing so each layer must declare exactly one of `path` or `ref`.
- Made bootstrap CI include wiring structural: `.gitlab-ci.yml` is now merged as YAML and invalid CI YAML fails closed instead of being text-spliced.
- Made fleet CI-gate auditing semantic: parsed CI YAML/script nodes are inspected, comment-only markers no longer count as contract evidence, and `ROCS_CI_PROFILE` must be bound in the same script context as the wrapper call.
- Switched GitLab ref-cache keys to an injective encoding while preserving reads from complete legacy cache entries.

### Fixed
- `rocs vendor` rejects targets that overlap the source package tree, preventing recursive self-copy behavior.
- Authority receipt lock handling no longer triggers a `return`-in-`finally` warning during compilation.
