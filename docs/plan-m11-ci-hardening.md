---
summary: "Historical M11 plan kept for provenance; superseded by workspace-only ref resolution and local gate policy."
read_when:
  - "When tracing why older ROCS docs mention GitLab archive fetching"
  - "When comparing the old M11 hardening plan to the current workspace-only design"
---

# Historical M11 plan: rocs-cli hardening (token + refs)

Source issue: `ai-society/core/rocs-cli#1` (“M11 Proposal: ROCS CI hardening (token + refs)”).

## Status
This document is **historical**.

The current ROCS design no longer uses GitLab archive fetching or remote fallback:
- ref locators are workspace-only via `<repo:...@ref>`
- legacy `<gitlab:...@ref>` locators are rejected
- local gates run through `scripts/ci/full.sh`

Read these current docs first:
- `README.md`
- `docs/ref-resolution-ci-strategy.md`
- `docs/artifacts.md`

The remainder of this file is preserved as an archival implementation plan from the pre-workspace-only design.

## Outcome (restated)
- `rocs validate/lint/build/diff` deterministic for same inputs (define “same inputs” below).
- No network activity unless `--resolve-refs` is set.
- GitLab archive handling hardened: no path traversal; reject symlinks/hardlinks; stream downloads with limits.
- CI runs tests on Python 3.11–3.13; ruff gate exists.

## What is affected (code + downstream)

**Primary code paths**
- Ref resolution + offline-first guard: `src/rocs_cli/layers.py`
- GitLab archive download/extract + caching: `src/rocs_cli/gitlab.py`, `src/rocs_cli/cache.py`
- CLI output contracts + exit codes + JSON/text parity: `src/rocs_cli/cli.py`
- CI: `.gitlab-ci.yml`, `pyproject.toml` (ruff config)

**Downstream consumers**
- Vendored copies of rocs-cli under `*/tools/rocs-cli` (e.g. `core/ontology-kernel/tools/rocs-cli`, `holdingco/projects/rocs-dogfood/tools/rocs-cli`, templates under `holdingco/holdingco-templates/**/tools/rocs-cli`).
- CI templates calling rocs via `uvx -n --from ./tools/rocs-cli rocs ...` (e.g. `holdingco/governance-kernel/docs/dev/rocs-multilayer-template/**/gitlab/ci/rocs.yml`).

## Known gaps vs M11 acceptance (as-is)
- `src/rocs_cli/gitlab.py` downloads archives via `r.read()` (non-streaming; no size limit).
- `src/rocs_cli/gitlab.py` uses `tarfile.extractall()` (path traversal is checked, but symlink/hardlink safety is not enforced; extraction is still unsafe for untrusted tarballs).
- `src/rocs_cli/cli.py:cmd_diff` fetches the GitLab baseline archive unconditionally; it does not require `--resolve-refs` even though it may perform network I/O.
- Dist artifacts include non-deterministic fields (e.g. `generated_at`, absolute paths like `repo` / `baseline_repo`); decide whether these are “inputs” that matter for determinism.

## Decisions required (blockers if unclear)
1) **Determinism definition**
   - Option A (strict): `ontology/dist/*` byte-identical across machines for same repo content + flags.
   - Option B (pragmatic): semantic determinism (sorted ids, stable findings), but allow non-deterministic metadata fields.
2) **GitLab ref policy (cache correctness)**
   - Are branch refs allowed? If yes, caching a branch name can become stale and break determinism.
   - Proposed: allow tags + commit SHAs by default; require an explicit flag to allow branches.
3) **Download limits**
   - Max archive bytes (default + override env var).
   - Timeout and retry policy (especially in CI).
4) **Exit-code taxonomy + compatibility**
   - Today exit code `2` is used for “action needed but not a crash” in multiple commands (normalize/diff/pack).
   - Decide a stable mapping that doesn’t break existing automation.
5) **JSON schema for failures**
  - Define minimal `error` envelope for `--json` commands (and how to represent network/config/internal errors).

## Expert consult checklist (roles + questions)

**Security reviewer (tar + filesystem)**
- Confirm extraction rules: reject symlink/hardlink/device nodes; enforce path containment; enforce max file bytes; handle long paths safely.
- Confirm whether we should also reject “pax headers” / unusual tar types (recommended: reject non-regular files).

**GitLab API / ops**
- Confirm archive endpoint behavior with `CI_JOB_TOKEN` and cross-project access.
- Confirm expected HTTP statuses for auth failures (401 vs 403) and rate-limit behavior.
- Confirm whether server supports `Range` or reliable `Content-Length` for `.tar.gz` downloads.

**CLI UX / automation**
- Standardize on `--json` (single machine-output knob).
- Decide error contract: stable exit codes + stable error “kind” for machine consumers.

**CI maintainer**
- Decide ruff posture: `ruff check` only vs also `ruff format` enforcement.
- Confirm Python 3.13 image availability and job time impact.

## Consent discussion outline (S3)
1) Present scope + decisions required (above).
2) Confirm invariants:
   - offline-first default
   - secure handling of untrusted archives
   - deterministic outputs (as defined)
3) Gather objections (reasoned, specific).
4) Integrate objections into plan (or narrow scope).
5) Record consent in issue `#1` with:
   - decision summary
   - accepted tradeoffs
   - next actions + owners

## Implementation plan (single plan for implementation crew)

Work is tracked as slices in GitLab: `#2`–`#6`. This plan orders them for lowest-risk integration.

### Phase 0: align on decisions (blocking)
- Pick determinism definition (strict vs pragmatic).
- Pick ref policy (tags+sha only vs allow branches).
- Pick archive size limits + retry rules.
- Pick exit-code taxonomy + JSON error envelope.

### Phase 1: scaffold + CI (Issue #2 + #6)
- Add CI matrix for 3.11–3.13 in `.gitlab-ci.yml`.
- Add `ruff` configuration in `pyproject.toml` and run `ruff check` in CI.
- Add a small doc section in `README.md`:
  - how to run tests and ruff locally
  - what the CI gates are
- Add/extend tests to lock down:
  - CLI output shapes in JSON mode (at least one “happy path” per command that supports JSON)
  - exit codes for known outcomes (`validate` fail=1, `normalize` changes-needed=2, etc.)

### Phase 2: GitLab fetch/extract hardening (Issue #4)
- Replace `tarfile.extractall()` with a safe extraction routine:
  - validate each member path stays under extract root
  - reject symlinks/hardlinks and any non-regular file types
  - write files with explicit size caps (defense-in-depth)
- Stream download to disk with a max-bytes cap (and fail with an actionable error if exceeded).
- Make cache writes atomic and corruption-resistant:
  - write to temp dir
  - add a completion marker (e.g. `.rocs_ok`)
  - rename/replace atomically
  - (optional) lock per cache key to avoid concurrent writes
- Add tests with malicious tar fixtures (no network): traversal, symlink, hardlink, oversized.

### Phase 3: offline-first + failure mode hardening (Issue #3)
- Ensure `--only path` never triggers ref resolution (tests).
- Ensure any operation that can fetch remote content requires `--resolve-refs`:
  - specifically include `rocs diff --baseline <gitlab:...@...>` (baseline fetch must be gated).
- Improve error messages for missing base url/token and HTTP failures (status + hint).

### Phase 4: error model + exit codes + JSON parity (Issue #5)
- Introduce a small typed error layer (or a normalized exception wrapper) so:
  - default mode prints clean messages (no traceback)
  - `--debug` prints traceback
  - exit codes are stable and documented
  - JSON mode includes a stable `{ok:false, error:{kind,message,details?}}` envelope
- Extend/adjust tests for:
  - exit codes for config/network/validation/internal cases
  - JSON output parity for the supported commands

### Phase 5: update downstream vendoring (follow-on, outside M11 if needed)
- Update vendored `tools/rocs-cli` copies in template repos and active repos.
- Run template CI (`gitlab/ci/rocs.yml`) against at least one multilayer repo using `<gitlab:...@...>` refs.

## Definition of done (for M11 #1)
- All slices `#2`–`#6` moved out of `state::triage` and merged (or explicitly dropped with rationale).
- CI green across Python 3.11–3.13 + ruff.
- Documented:
  - determinism definition and scope
  - ref policy
  - archive safety constraints + limits
  - exit-code taxonomy + JSON error envelope
