# rocs-cli

Minimal ROCS CLI for ai-society.

Commands:
- `rocs summary --repo .`
- `rocs validate --repo .`
- `rocs pack <ont_id> --repo .`
- `rocs build --repo .`

Scope (MVP):
- Validate ROCS repo structure + ontology front matter schema.
- Build local artifacts into `ontology/dist/` (offline; does not fetch remote layers yet).

