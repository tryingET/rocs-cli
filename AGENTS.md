# AGENTS.md

Keep CLI small + boring:
- offline-first (do not fetch remote layers by default)
- deterministic output
- no secrets

Local dev:
- `uv run --with pyyaml --with rich python -m rocs_cli --help`
- `uv run python -m unittest discover -s tests -p 'test_*.py' -q` (includes README↔CLI wiring check)
- Bump version (SemVer): `uv run python scripts/bump_version.py --bump patch|minor|major [--preid rc] [--sync-vendored]`
