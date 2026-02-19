---
summary: "Local + CI type checking with Astral `ty`."
read_when:
  - "When adding static typing to rocs-cli or wiring type checks into CI"
  - "When adding/editing ty configuration"
as_of: "2026-01-16"
---

# `ty` manual (rocs-cli)

## What it is
`ty` is Astral’s (Rust-based) Python type checker and language server.

This repo’s policy:
- Prefer `ty` for type checking.

## Versions
- `ty` is pinned in `scripts/tool_versions.json` (used by CI).

## Run (recommended)
Run pinned `ty` ephemerally via `uvx`:

```bash
uvx ty==$(python -c 'import json; print(json.load(open("scripts/tool_versions.json"))["ty"])') --version
uvx ty==$(python -c 'import json; print(json.load(open("scripts/tool_versions.json"))["ty"])') check src/rocs_cli
```

## Run locally
From `core/rocs-cli/`:

```bash
uvx ty==$(python -c 'import json; print(json.load(open("scripts/tool_versions.json"))["ty"])') check src/rocs_cli
```

Useful patterns:
- Print help: `uvx ty==$(python -c 'import json; print(json.load(open("scripts/tool_versions.json"))["ty"])') --help`

## Configure
`ty` reads config from `pyproject.toml` under `[tool.ty]`.

Minimal starter (example):

```toml
[tool.ty]

[tool.ty.environment]
python-version = "3.11"
```

Notes:
- Keep config minimal; add strictness only when it pays.
- Don’t bake secrets or absolute paths into config.

## CI wiring
GitLab CI runs:

```bash
uvx ty==$(python -c 'import json; print(json.load(open("scripts/tool_versions.json"))["ty"])') check src/rocs_cli
```
