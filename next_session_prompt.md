---
summary: "Workspace-only ROCS ref resolution after removing legacy GitLab support."
read_when:
  - "When deciding ROCS ref-resolution policy for template consumers"
  - "When wiring local gates through Pi or git hooks"
---

# Next Session Prompt — ROCS ref resolution (workspace-only)

## Session trigger
Start from the new invariant: ROCS resolves refs from the local workspace only.

## Objective
Keep refs essential on strict paths while avoiding any GitLab dependency.

## Invariants
- Keep `--resolve-refs`.
- Keep strict provenance on branch/main gates.
- Do not reintroduce remote archive fallback.
- Prefer local wrapper / Pi / hook integration over remote CI assumptions.

## Current decision
- Supported locator form: `<repo:...@ref>`
- Unsupported legacy form: `<gitlab:...@ref>`
- Canonical caller contract: `scripts/ci/full.sh`
- Strictness profiles:
  - `local-dev`
  - `branch-ci`
  - `main-strict`

## Read-first allowlist
1. `AGENTS.md`
2. `README.md`
3. `docs/ref-resolution-ci-strategy.md`
4. `src/rocs_cli/cli.py`
5. `src/rocs_cli/layers.py`
6. `src/rocs_cli/authority.py`
7. `tests/test_workspace_resolution.py`
8. `tests/test_cli.py`

## Validation baseline
- `uv run python -m unittest discover -s tests -p 'test_*.py' -q`

## Checkpoint fields
- Decision chosen: Workspace-only ref resolution with hybrid caller-profile policy.
- Why this option: GitLab is gone; local workspace resolution is deterministic, offline-first, and compatible with Pi/hook-driven gates.
- Files changed: `src/rocs_cli/layers.py`, `src/rocs_cli/cli.py`, `src/rocs_cli/env.py`, `src/rocs_cli/authority.py`, `src/rocs_cli/cache.py`, `scripts/ci/full.sh`, `README.md`, `docs/ref-resolution-ci-strategy.md`, `docs/artifacts.md`, `tests/test_workspace_resolution.py`, `tests/test_cli.py`, `AGENTS.md`, `next_session_prompt.md`.
- Tests run/results: `uv run python -m unittest discover -s tests -p 'test_*.py' -q` ✅ (`Ran 106 tests`); `node ~/ai-society/core/agent-scripts/scripts/docs-list.mjs --docs . --strict` ✅.
- Consumer migration impact: manifests must use `<repo:...>` locators and local gates should call `scripts/ci/full.sh` from Pi or hooks.
- Rollback plan: not recommended; migrate remaining manifests instead of restoring remote fallback.
