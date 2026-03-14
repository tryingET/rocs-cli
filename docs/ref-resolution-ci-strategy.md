---
summary: "Policy contract for ROCS local-first ref resolution across local/mainline workflows, with legacy GitLab fetch kept only for compatibility."
read_when:
  - "When deciding how ROCS refs should resolve in a local-first workspace"
  - "When CI fails because legacy GitLab fallback was reached unexpectedly"
  - "When defining local/mainline workflow policy for layered ontology repos"
---

# ROCS ref-resolution CI strategy (10,000ft)

## Decision
**Local-first refs are now the default policy.**

- Prefer `<repo:...@ref>` locators that resolve from the local workspace.
- Keep `rocs-cli` offline-first and deterministic.
- Keep `--resolve-refs` explicit.
- Retain legacy `<gitlab:...@ref>` support only as a compatibility path.
- Put environment/profile intent in caller scripts (`local-dev`, `main-strict`).

This keeps normal operator work local and deterministic while preserving a narrow escape hatch for older manifests that still depend on GitLab archive fetches.

## Locator stance

| Locator | Meaning | Network | Recommendation |
|---|---|---:|---|
| `<repo:...@ref>` | workspace-relative repo dependency | no | **default** |
| `<gitlab:...@ref>` | legacy forge-coupled dependency | optional | compatibility only |

## Contract table (authoritative behavior)

| Context | `--resolve-refs` | Expected locator | Failure behavior |
|---|---:|---|---|
| Local dev | yes for layered repos | `<repo:...@ref>` | Fail if local dependency repo is missing or ref-mismatched; no hidden remote fallback. |
| Mainline/full gate | yes | `<repo:...@ref>` | Fail closed always. Workspace/ref correctness is mandatory gate. |
| Legacy compatibility run | yes | `<gitlab:...@ref>` | Workspace/cache first; GitLab fetch allowed only when explicitly configured. |

## Operational semantics to preserve

1. `--resolve-refs` stays opt-in and explicit.
2. With `--resolve-refs`, source precedence remains:
   1) workspace clone
   2) cache
   3) legacy GitLab fetch (legacy locators only)
3. `repo:` locators bind by workspace layout, not forge origin.
4. Strict/mainline paths must not pass without ref resolution success.
5. Errors must remain actionable (missing local repo, ref mismatch, auth, not_found, timeout).

## Minimal implementation plan

### Phase 1 (now)
1. Support `<repo:...@ref>` locators in `rocs-cli`.
2. Update bootstrap/templates to emit local-first repo locators.
3. Standardize workspace-root defaults around `~/ai-society`.
4. Keep legacy `<gitlab:...>` behavior for compatibility only.

### Phase 2 (follow-on)
1. Migrate active repos from legacy `<gitlab:...>` locators to `<repo:...>`.
2. Remove or downgrade forge-specific CI/template assumptions.
3. Revisit whether GitLab fetch should remain at all.

## Consumer migration impact

- **Required:** layered repos should set `ROCS_WORKSPACE_ROOT` (recommended: `~/ai-society`).
- **Recommended:** new manifests should use `<repo:...@ref>`.
- **Net effect:** local runs stop depending on forge env vars for normal work.

## Rollback plan

If a repo still needs remote archive fallback, keep or temporarily restore legacy `<gitlab:...>` locators for that manifest while the workspace-local dependency layout is being fixed.
