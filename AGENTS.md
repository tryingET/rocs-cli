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
- Bump version (SemVer): `uv run python scripts/bump_version.py --bump patch|minor|major [--preid rc] [--sync-vendored]`

When changing generated CI/template surfaces:
- validate both fresh bootstrap and rerun-on-existing-repo convergence
- prefer behavior-contract checks over file-presence-only checks
