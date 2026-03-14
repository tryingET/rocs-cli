---
summary: "Decision note for ROCS ref-resolution policy across local dev, branch CI, and protected/main CI."
read_when:
  - "When deciding where ROCS ref-resolution policy should live"
  - "When local runs hit legacy GitLab fallback timeouts"
  - "When standardizing template consumer CI behavior around --resolve-refs"
---

# ROCS ref-resolution CI strategy (10,000ft)

## Problem statement
ROCS is intentionally offline-first, but many template consumers currently call `rocs build/validate --resolve-refs` unconditionally in CI wrappers.

That preserves provenance on strict paths, but it also means local or lightly-provisioned environments can fall through to legacy GitLab archive fetches when workspace/cache are incomplete. When that happens, operators see slow timeouts or confusing failures even though their real intent was usually one of two very different modes:

1. **authoritative verification** — refs must resolve, fail closed, provenance matters
2. **local/dev iteration** — stay usable, predictable, and explicit about what is and is not being checked

The policy question is therefore not whether refs matter. They do. The question is **where the strictness contract should live** so that mainline CI stays authoritative without making local work brittle.

## Options considered

| Option | Primary policy location | Pros | Cons | Verdict |
|---|---|---|---|---|
| A — caller policy only | Consumer CI scripts decide when to pass `--resolve-refs` | Minimal `rocs-cli` churn; preserves current mechanics | Easy drift across repos; timeout/failure semantics become inconsistent; every consumer must reinvent the contract | Rejected as sole solution |
| B — `rocs-cli` policy mode | Add first-class CLI strictness mode (`required`, `best-effort`, etc.) | One central surface; easier to reason about inside the CLI | Duplicates or muddies the meaning of `--resolve-refs`; adds migration/compat burden; CLI still cannot infer repo-specific CI intent cleanly | Rejected for now |
| C — hybrid | `rocs-cli` owns mechanics; caller profiles own execution policy | Keeps CLI explicit and small; avoids policy drift; maps cleanly to local/branch/main workflows | Requires template/bootstrap alignment so consumers actually use the shared profile contract | **Recommended** |

## Recommendation
**Choose Option C — hybrid.**

### Why this is the right split
`rocs-cli` already has the right low-level behavior surface:
- `--resolve-refs` is explicit
- resolution order is deterministic: workspace → cache → legacy GitLab fetch
- `<repo:...@ref>` stays local-first
- `<gitlab:...@ref>` remains compatibility-only
- strict vs loose workspace matching is already exposed via `--workspace-ref-mode`
- errors are already actionable (`not_found`, `auth`, `network`, ref mismatch details)

What is missing is not another CLI semantic layer. What is missing is a **stable caller-side contract** that says when strict resolution is mandatory and what timeout envelope applies.

That contract already exists in embryo via `scripts/ci/full.sh`:
- `ROCS_CI_PROFILE=local-dev`
- `ROCS_CI_PROFILE=branch-ci`
- `ROCS_CI_PROFILE=main-strict`

The right move is to standardize that contract, make it canonical for templates/bootstraps, and avoid inventing a second policy model inside the CLI.

## Authoritative contract table

> **Important:** timeout values only matter when a legacy `<gitlab:...@ref>` locator reaches remote fallback. The preferred `<repo:...@ref>` path should remain workspace/cache local and deterministic.

| Context | Canonical caller contract | `--resolve-refs` | Timeout / retry contract | Failure behavior | Expected locator stance |
|---|---|---:|---|---|---|
| Local dev | `ROCS_CI_PROFILE=local-dev` | **Off by default**; enabled only with `ROCS_LOCAL_RESOLVE_REFS=1` | None by default. If a developer explicitly opts into ref resolution, use CLI/env defaults unless overridden. | Default mode stays usable and offline-first. When strict local ref checks are explicitly enabled, fail fast on missing workspace/cache or strict ref mismatch. | Prefer `<repo:...@ref>`; avoid depending on remote fallback for normal local work. |
| Branch CI | `ROCS_CI_PROFILE=branch-ci` | **Required** | `ROCS_GITLAB_TIMEOUT_S=30`, `ROCS_GITLAB_RETRIES=3` | Fail closed on unresolved refs, auth errors, not-found, or timeout. Catch dependency/config drift before merge. | Prefer `<repo:...@ref>`; allow legacy `<gitlab:...>` only as compatibility path. |
| Protected / main CI | `ROCS_CI_PROFILE=main-strict` | **Required** | `ROCS_GITLAB_TIMEOUT_S=60`, `ROCS_GITLAB_RETRIES=3` | Fail closed always. This is the authoritative provenance gate and must not silently degrade to best-effort behavior. | Prefer `<repo:...@ref>`; legacy `<gitlab:...>` remains temporary compatibility only. |

## Policy implications

### 1) Refs remain essential where they matter most
Protected/main CI should continue to require successful ref resolution. No weakening of provenance or traceability is recommended.

### 2) Local usability is preserved by making strictness explicit
Local operators should not be forced into slow remote fallbacks just because a wrapper always adds `--resolve-refs`. Instead, local strictness is an explicit choice.

### 3) The CLI should stay mechanics-focused, not environment-guessing
The CLI should keep owning:
- how refs resolve
- what counts as workspace/cache/gitlab
- how strict workspace matching behaves
- how failures are classified

Caller scripts should own:
- which workflow is being run
- whether strict resolution is mandatory
- timeout and retry envelopes for that workflow

### 4) Branch and main differ operationally, not semantically
Both branch CI and protected/main CI should be fail-closed on ref resolution. The difference is operational tolerance, not correctness standard:
- branch CI gets a tighter timeout envelope to keep feedback loops reasonable
- main CI gets a slightly wider envelope because it is the authoritative gate

## Minimal implementation plan

### Phase 1 — make the policy contract canonical
1. Treat `scripts/ci/full.sh` as the canonical template-side entrypoint.
2. Document `ROCS_CI_PROFILE=local-dev|branch-ci|main-strict` as the standard caller contract.
3. Point README/template docs to this design note so consumers do not recreate policy ad hoc.

### Phase 2 — migrate template consumers
1. Update bootstrap/template emitters to call `scripts/ci/full.sh` instead of hardcoding:
   - `rocs build --resolve-refs`
   - `rocs validate --resolve-refs`
   - `scripts/bootstrap-repo.sh` is the first in-repo emitter aligned to this contract and now converges generated CI wrapper surfaces on rerun; remaining external templates should follow the same pattern.
2. Use:
   - `branch-ci` for ordinary CI pipelines
   - `main-strict` for protected/mainline gates
3. Keep `local-dev` as the default operator-facing mode.

### Phase 3 — finish locator migration
1. Audit manifests still using legacy `<gitlab:...@ref>` locators.
2. Migrate active repos to `<repo:...@ref>` where workspace layout is authoritative.
3. Keep legacy GitLab fetch only as a compatibility escape hatch during migration.

## Consumer migration impact
- **Required for layered repos:** set `ROCS_WORKSPACE_ROOT` (recommended: `~/ai-society`).
- **Required for templates/bootstraps:** stop encoding policy by always passing `--resolve-refs` directly.
- **Recommended for manifests:** prefer `<repo:...@ref>` over `<gitlab:...@ref>`.
- **Net effect:** local runs become explicitly usable, while branch/main CI remain strict and deterministic.

## Rollback plan
If a consumer repo cannot adopt the shared profile wrapper immediately:
1. keep its current strict invocation temporarily,
2. preserve legacy `<gitlab:...>` locators where still necessary,
3. migrate that consumer once workspace-local dependencies and CI profile wiring are in place.

Rollback should be treated as temporary compatibility, not a new steady-state policy.
