---
summary: "Active handoff for the current rocs-cli tactical wave after direction-to-execution repair."
read_when:
  - "You are starting the next rocs-cli session"
  - "You need the truthful next operating wave and authoritative task IDs"
---

# Session Status — bootstrap/audit helper convergence

## Status
The previous workspace-only ref-resolution wave is complete on the current branch.
This repo now has explicit direction docs and an active operating wave backed by authoritative AK tasks.

## Start here
1. `AGENTS.md`
2. `README.md`
3. `docs/project/vision.md`
4. `docs/project/strategic_goals.md`
5. `docs/project/tactical_goals.md`
6. `docs/project/operating_plan.md`
7. `docs/ref-resolution-ci-strategy.md`
8. Inspect AK tasks `#363` and `#364` from `softwareco/owned/agent-kernel` via `./scripts/ak-v2.sh task show <id>`

## Active goal stack
- Strategic goal: eliminate contract drift in downstream fleet helper surfaces
- Tactical goal: remove the remaining bootstrap/audit helper drift with shared, directly tested seams
- Active AK tasks:
  - `#363` Modularize bootstrap CI-include remediation into directly unit-tested Python helpers
  - `#364` Extract shared FCOS gate contract helpers to eliminate bootstrap/audit drift

## Objective
Finish the shared-helper convergence wave without expanding into non-active docs/operator backlog.

## Invariants
- Keep the CLI small, boring, deterministic, and offline-first.
- Keep workspace-only `<repo:...@ref>` resolution; do not reintroduce remote fallback.
- Keep `scripts/ci/full.sh` as the canonical local gate wrapper.
- When generated/template surfaces change, validate both fresh bootstrap and rerun-on-existing convergence.

## Validation baseline
- `uv run python -m unittest discover -s tests -p 'test_*.py' -q`
- `node ~/ai-society/core/agent-scripts/scripts/docs-list.mjs --docs . --strict`

## Checkpoint fields
- Previous wave closed: stale AK task `#329` should be treated as completed work, not new backlog.
- Direction source of truth: `docs/project/vision.md`, `docs/project/strategic_goals.md`, `docs/project/tactical_goals.md`, `docs/project/operating_plan.md`.
- Active execution source of truth: AK tasks `#363` and `#364`.
- Intentionally deferred until after this wave: broader docs/operator cleanup for the stabilized local-gate contract.
