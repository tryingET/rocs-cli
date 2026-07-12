---
summary: "Changelog for rocs-cli."
read_when:
  - "Preparing a release or reviewing user-visible changes."
---

# Changelog

## [Unreleased]

### Removed
- **Breaking (Wave 6):** removed `.gitlab-ci.yml`, the `rocs_cli.gitlab_ci` helper API, and its GitLab include-rewriting tests. Local gates have sole authority; no compatibility shims remain.
- **Breaking (Wave 1):** removed `audit-fleet.py`, `open-remediation-batch.sh`, `run-fleet-audit-nightly.py`, `run-fleet-audit-nightly.sh`, `bootstrap-repo.sh`, `vendor-to.sh`, `bump_version.py`, `bench.py`, and `gen_bench_repo.py`; there are no compatibility shims.
- **Breaking (Wave 1):** removed their script-specific tests. Scheduler assets now invoke `rocs fleet run`.

### Added
- Decision-52 development substrate: immutable two-pass semantic corpus capture, exact `rocs-lexical-v0` discovery, `discover-capabilities`, closed `discover` invocation identity, and snapshot/document-bound exact-ID pack output. Production adoption and defaults remain blocked by decision 53.
- Wave 4 proposal-only constitutional rule foundry with strict digest-bound candidates, a closed deterministic predicate DSL, challenge/differential/mutation evaluation, and a stable multi-objective fleet repair Pareto frontier. It cannot activate rules, certify validity, suppress findings, select/apply bids, execute generated code, or mutate ontology/fleet state.
- Wave 3 deterministic semantic transactions with strict digest-bound prepare/simulate/apply/verify/rollback contracts, separate operator approval, owner/ref boundaries, same-filesystem staging, content-addressed receipts, and byte-exact compensation/rollback. Only `transaction apply` mutates ontology files; no shell/model/network execution is introduced.
- Wave 2 optional intelligence membrane: deterministic content-addressed context capsules, strict proposal validation, externally approved schema-1 ontology-operation plan compilation, and an authority-free adapter protocol. No model/network is required and compilation performs no ontology mutation.
- Closed first-class CLI operations for fleet observe/plan/apply/run, repository bootstrap/converge, vendor, release plan/apply, verify/cleanup/doctor, benchmark, and generator.
- Schema-2 pinned self-contained consumer lock and isolated acceptance fixture.

### Changed
- Wave 8 decomposes CLI handlers, validation support, and the monolithic CLI compatibility tests into focused size-bounded modules while preserving parser, output, exit, filesystem, console, and private-name compatibility.
- **Breaking (Wave 7):** `rocs contracts` schema 3 removes `mutates` without a shim and declares executable, closed filesystem-effect conditions, runtime facts, required authority artifacts, and normalized global error exits for every operation.
- **Breaking (Wave 6):** `ontology_repo` bootstrap now manages root `manifest.yaml` and `src/system4d.yaml`, never a nested `ontology/` tree. Generated gates verify the complete bundled lock before importing code and execute it with `python -S`; `local-dev` is path-only while `main-strict` and `branch-ci` resolve local refs strictly.
- **Breaking (Wave 5):** transaction simulation and apply now reject permission-mode drift as well as byte drift, and receipt roots must be direct siblings of the ontology root so every pending journal can be reconciled under one bounded transaction lock before mutation.
- Wave 5 verifies staged postimages against receipt-bound bytes and modes before generation exchange, verifies successful receipts immediately, restores exact modes during rollback, and recovers pending apply or rollback journals before a distinct transaction proceeds.
- **Breaking:** remediation apply now requires schema-version 2 scorecards with policy/evidence SHA-256 digests and rejects any input that differs from a fresh deterministic fleet audit.
- **Breaking:** fleet policies now reject non-boolean or unknown capabilities, duplicate normalized repository paths, and repository paths outside the workspace.
- **Breaking:** fleet auditing now requires complete, schema-exact SHA-256 vendored manifests and verifies every covered regular file; empty, malformed, incomplete, traversal, symlink, and unexpected package-file cases fail closed.
- Vendoring now builds a complete sibling staging tree under an exclusive lock and atomically publishes it with rollback to the prior tree on publication failure.
- Nightly stale-artifact cleanup now verifies containment beneath the resolved artifact root before deletion.
- **Breaking:** the CI wrapper now rejects non-repository roots, missing manifests, root paths, and cleanup targets that are symlinks or resolve outside `ROCS_REPO`.
- Bootstrap now builds and verifies a complete sibling stage, publishes it with a same-filesystem atomic rename, and restores the prior tree on every injected late failure.
- Added an importable versioned closed capability registry used by bootstrap, fleet audit validation, and remediation policy logic; unknown classes and capabilities fail closed.
- Hardened ROCS manifest layer parsing so each layer must declare exactly one of `path` or `ref`.

### Fixed
- Repository and generated FCOS gate commands use frozen dependency resolution, so deterministic validation no longer normalizes the intentional `uv.lock` snapshot as a side effect.
- `rocs vendor` rejects targets that overlap the source package tree, preventing recursive self-copy behavior.
- Authority receipt lock handling no longer triggers a `return`-in-`finally` warning during compilation.
