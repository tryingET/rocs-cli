---
summary: "Local + CI type checking with Astral `ty`."
read_when:
  - "When adding static typing to rocs-cli or wiring type checks into CI"
  - "When adding/editing ty configuration"
as_of: "2026-01-12"
---

# `ty` manual (rocs-cli)

## What it is
`ty` is Astral’s (Rust-based) Python type checker and language server.

This repo’s policy:
- Prefer `ty` for type checking.

## Versions
- `ty` is currently `0.0.11` (pinned in examples).

## Install (recommended)
Pin the tool so CI/local are consistent:

```bash
uv tool install ty==0.0.11
ty --version
```

Alternative (ephemeral, slower): run without installing globally:

```bash
uvx ty --version
uvx ty check
```

## Run locally
From `core/rocs-cli/`:

```bash
ty check
```

Useful patterns:
- Check only the package: `ty check src/rocs_cli`
- Print help: `ty --help`

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

## CI wiring (intent)
Add a CI job that runs:

```bash
ty check
```
