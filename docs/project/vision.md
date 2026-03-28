---
summary: "Vision and hard scope boundaries for rocs-cli."
read_when:
  - "You need the stable purpose and scope boundary for this repo"
  - "You are refreshing strategy, tactics, or the active operating wave"
type: "reference"
---

# Vision

## Purpose
Keep `rocs-cli` the small, boring, offline-first ROCS toolchain for AI Society:
- deterministic ontology validation/build behavior
- workspace-only ref resolution for layered repos
- low-friction local gate/bootstrap/audit helpers for downstream consumers

## Hard scope boundaries
- Do **not** reintroduce remote archive fallback or GitLab-dependent ref resolution.
- Do **not** grow a second planning authority beside repo docs + authoritative AK tasks.
- Do **not** chase speculative feature expansion while current CLI/fleet contract surfaces still need convergence or hardening.

## Repo archetype
`rocs-cli` is a **hybrid repo with coding dominance**.

Evidence:
- coding surfaces: `src/rocs_cli/`, `tests/`, `pyproject.toml`
- contract/governance surfaces: `README.md`, `docs/*.md`, `scripts/bootstrap-repo.sh`, `scripts/audit-fleet.py`, `scripts/open-remediation-batch.sh`, `scripts/run-fleet-audit-nightly.py`
- operator contract emphasis in `AGENTS.md` and `next_session_prompt.md`

## Durable outcomes
1. ROCS mechanics stay deterministic, offline-first, and easy to explain.
2. Downstream repos can adopt the local gate/bootstrap/audit surfaces without hidden drift.
3. Repo-local direction stays truthful: strategy -> tactics -> operating slices -> authoritative AK tasks.

## Evidence used for this vision refresh
- `AGENTS.md`
- `README.md`
- `next_session_prompt.md` (previous wave closure)
- recent repo-local AK tasks (`#329`, `#363`, `#364`)
- recent commits focused on workspace-only ref resolution plus bootstrap/audit hardening
