---
summary: "Repo-level operating notes for rocs-cli contributors."
read_when:
  - "When working in the rocs-cli repository"
type: "reference"
---

# AGENTS.md

Keep CLI small + boring:
- offline-first (do not fetch remote layers by default)
- deterministic output
- no secrets

Remote workflow:
- Do not rely on GitLab-specific wrappers or remote archive fetches from this repo.
- Prefer local commits plus deterministic local gates (`scripts/ci/full.sh`, tests, and hook/Pi wiring in consumers).
- If remote coordination is needed later, document the replacement workflow explicitly instead of reintroducing GitLab assumptions.

Local dev:
- `uv run python -m rocs_cli --help`
- `uv run python -m unittest discover -s tests -p 'test_*.py' -q` (includes README↔CLI wiring check)
- Optional YAML CLI tooling (`yq`): `uv sync --extra tooling && uv run --extra tooling yq --version`
- Release version (SemVer): `uv run python -m rocs_cli release plan|apply --version <version>`

When changing generated CI/template surfaces:
- validate both fresh bootstrap and rerun-on-existing-repo convergence
- prefer behavior-contract checks over file-presence-only checks

## Direction workflow
- Read `docs/project/vision.md` for durable ambition and `docs/project/product-posture.md` for current maturity.
- Read live strategic frames and implementation waves with `ak strategy list --repo .` and `ak wave list --repo .`; use AK tasks, decisions, and evidence for execution truth.
- Use `ak direction check --repo .` as an integrity gate. `ak direction import` is legacy migration only, not routine reconciliation.
- Do not recreate SG/TG/OP planning files. Historical snapshots live under `docs/project/archive/`.
