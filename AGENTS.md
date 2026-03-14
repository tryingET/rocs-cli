# AGENTS.md

Keep CLI small + boring:
- offline-first (do not fetch remote layers by default)
- deterministic output
- no secrets

GitLab / issues:
- Self-hosted GitLab (nas): use `gl-nas` wrapper (python-gitlab CLI) to view/update issues/MRs, e.g.
  - `gl-nas -- project get --id ai-society/core/rocs-cli`
  - `gl-nas -- project-issue get --project-id 15 --iid 1`
- Git over HTTP (clone/fetch/push): use `gl-nas-git -- <git args...>` (non-interactive; avoids username/token prompts).
- Reference: `holdingco/governance-kernel/docs/dev/gitlab-access.md`.

Local dev:
- `uv run python -m rocs_cli --help`
- `uv run python -m unittest discover -s tests -p 'test_*.py' -q` (includes README↔CLI wiring check)
- Optional YAML CLI tooling (`yq`): `uv sync --extra tooling && uv run --extra tooling yq --version`
- Bump version (SemVer): `uv run python scripts/bump_version.py --bump patch|minor|major [--preid rc] [--sync-vendored]`
