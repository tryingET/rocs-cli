---
summary: "10,000ft alignment for ROCS ref-resolution behavior in local/main CI (refs are essential)."
read_when:
  - "When deciding ROCS CI strategy for template consumers"
  - "When resolving timeout/fallback behavior around --resolve-refs"
---

# Next Session Prompt — ROCS CI Strategy (10,000ft)

## Session trigger
Start with architecture and policy, not patch-first coding.

## Objective
Define a stable CI strategy for ROCS ref resolution where:
- refs remain essential on authoritative CI paths,
- local/dev runs stay usable,
- behavior is explicit and deterministic.

## Non-goals
- Do not remove `--resolve-refs` capability.
- Do not weaken provenance/traceability requirements for mainline CI.

## Context discovered
1. `rocs-cli` is offline-first by default.
2. Many consumer templates call `rocs build/validate --resolve-refs` unconditionally in `scripts/ci/full.sh`.
3. With `--resolve-refs`, workspace/cache are tried first; GitLab network fetch is fallback.
4. In local environments with incomplete workspace/cache, GitLab fallback can timeout and fail runs.
5. Operator intent from infra migration session: **refs are essential** (especially on main CI).

## Key question to answer
Should this policy live primarily in:
- caller CI scripts (profile/env policy),
- rocs-cli flags/modes,
- or both (recommended likely outcome)?

## Candidate strategy options

### Option A — Caller policy only
- Keep rocs-cli behavior unchanged.
- Consumers choose when to pass `--resolve-refs`.
- Pros: minimal core churn.
- Cons: policy drift across repos.

### Option B — rocs-cli policy mode
- Add first-class mode/flag for ref strictness (e.g. `required|best-effort` semantics).
- Pros: consistent behavior surface.
- Cons: CLI complexity + migration effort.

### Option C — Hybrid (likely best)
- Keep `--resolve-refs` as-is.
- Add a small rocs-cli policy switch or clear env contract for CI intent.
- Update templates to use explicit CI profiles (`strict-main` vs `local-dev`) while preserving strict refs on main.

## Deliverables for this session
1. A short design note under `docs/` comparing A/B/C with recommendation.
2. Explicit contract table:
   - local dev
   - branch CI
   - protected/main CI
   including expected `--resolve-refs`, timeout, and failure behavior.
3. If changes are approved, a minimal implementation plan with migration steps for template consumers.

## Read-first allowlist
1. `AGENTS.md`
2. `README.md`
3. `docs/ref-resolution-ci-strategy.md`
4. `src/rocs_cli/cli.py`
5. `src/rocs_cli/layers.py`
6. `src/rocs_cli/gitlab.py`
7. `tests/test_workspace_resolution.py`
8. `tests/test_gitlab_hardening.py`

## Validation baseline
- `uv run python -m unittest discover -s tests -p 'test_*.py' -q`
- Add/adjust tests for any new CLI semantics before implementation.

## Checkpoint fields (fill before commit)
- Decision chosen: Option C — hybrid caller-profile policy with `rocs-cli` mechanics unchanged.
- Why this option: It preserves authoritative ref resolution on branch/main CI, keeps local runs usable by default, and avoids inventing a second strictness model inside the CLI.
- Files changed: `scripts/ci/full.sh`, `README.md`, `docs/ref-resolution-ci-strategy.md`, `tests/test_workspace_resolution.py`, `next_session_prompt.md`.
- Tests run/results: `uv run python -m unittest tests.test_workspace_resolution -q` ✅; `uv run python -m unittest discover -s tests -p 'test_*.py' -q` ✅ (`Ran 118 tests`).
- Consumer migration impact: Template consumers should keep calling `scripts/ci/full.sh` via `ROCS_CI_PROFILE`; branch/main now default workspace matching to `strict`, while local-dev stays offline-first unless `ROCS_LOCAL_RESOLVE_REFS=1`.
- Rollback plan: Revert the wrapper/profile-default change in `scripts/ci/full.sh` and fall back to explicit per-consumer `ROCS_WORKSPACE_REF_MODE` overrides if any downstream repo depends on loose workspace matching in CI.
