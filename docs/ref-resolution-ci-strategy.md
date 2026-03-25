---
summary: "Decision note for ROCS ref-resolution policy after removing legacy GitLab fallback."
read_when:
  - "When deciding how ROCS resolves refs without GitLab"
  - "When standardizing local, hook, or Pi-driven validation around --resolve-refs"
---

# ROCS ref-resolution strategy (workspace-only)

## Decision
ROCS no longer supports legacy `<gitlab:...@ref>` locators or remote archive fallback.

Ref resolution is now **workspace-only**:
- supported locator form: `<repo:...@ref>`
- supported resolution source: local workspace clone
- strictness remains explicit via `--workspace-ref-mode strict|loose`
- caller policy remains profile-driven via `scripts/ci/full.sh`

## Why
GitLab is no longer a reliable dependency for ROCS workflows.
Keeping a dead or flaky remote fallback creates slow failures, ambiguous provenance, and unnecessary operational complexity.

Removing it entirely makes ROCS:
- more deterministic
- easier to explain
- truly offline-first
- compatible with local gates such as Pi runners or git hooks

## Policy split
Keep the hybrid contract:
- `rocs-cli` owns mechanics
  - parse `<repo:...@ref>` locators
  - resolve from workspace
  - enforce strict vs loose workspace matching
  - fail clearly on missing local dependencies
- callers own execution policy
  - whether `--resolve-refs` is required
  - whether a run is local-dev, branch-ci, or main-strict
  - how to wire the shared wrapper into Pi or hook-based workflows

## Contract table

| Context | Canonical caller contract | `--resolve-refs` | Workspace ref mode default | Failure behavior |
|---|---|---:|---|---|
| Local dev | `ROCS_CI_PROFILE=local-dev` | Off by default; enabled with `ROCS_LOCAL_RESOLVE_REFS=1` | `loose` by default; flips to `strict` when local ref resolution is explicitly enabled | Default mode stays fast and offline. Strict opt-in fails on missing workspace deps or ref mismatch. |
| Branch gate | `ROCS_CI_PROFILE=branch-ci` | Required | `strict` | Fail closed on unresolved refs or ref mismatch. |
| Main/protected gate | `ROCS_CI_PROFILE=main-strict` | Required | `strict` | Fail closed always. |

## Operational guidance
- Set `ROCS_WORKSPACE_ROOT=~/ai-society` (or your equivalent workspace root).
- Migrate any legacy `<gitlab:...>` manifest entries to `<repo:...>`.
- Use `scripts/ci/full.sh` as the canonical shared gate surface.
- The shipped bootstrap/audit contract uses `.githooks/pre-push` + `scripts/ci/full.sh`.
- Invoke that wrapper from:
  - checked-in git hooks (for example pre-push)
  - Pi tasks/runners
  - other local automation

## Minimal migration plan
1. Replace any legacy `<gitlab:...@ref>` locators with `<repo:...@ref>`.
2. Ensure dependency repos exist under the configured workspace root.
3. Keep `scripts/ci/full.sh` as the shared policy wrapper.
4. Prefer local gate wiring over remote CI assumptions.

## Rollback
Rollback is not recommended.
If a repo still depends on legacy locators, migrate the manifest rather than reintroducing remote fallback.
