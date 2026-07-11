---
summary: "Stable AK-native bootstrap for rocs-cli sessions."
read_when:
  - "You are starting or resuming rocs-cli work."
type: "reference"
---

# Next Session Prompt

Continue in `~/ai-society/core/rocs-cli`.

## Read first

1. `AGENTS.md`
2. `README.md`
3. `docs/project/vision.md`
4. `docs/project/product-posture.md`

## Read live state

```bash
ak strategy list --repo .
ak wave list --repo .
ak task ready --repo .
ak direction check --repo . --machine
```

AK is the live direction, task, decision, and evidence authority. This handoff is a stable bootstrap, not a queue or status mirror. Do not use archived SG/TG/OP files as current direction and do not run `ak direction import` for routine reconciliation.

## Operating boundaries

- Keep the CLI deterministic, offline-first, and small.
- Preserve workspace-only reference resolution; do not reintroduce remote fallback.
- ROCS and ontology owners define controlled semantic meaning. This CLI validates and transports it; it does not invent it.
- Use an exact AK task and its scope when one is supplied. If no task is ready, do not manufacture work from archived plans.

## Validation

```bash
uv run python -m unittest discover -s tests -p 'test_*.py' -q
node ~/ai-society/core/agent-scripts/scripts/docs-list.mjs --docs . --strict
ak direction check --repo . --machine
git diff --check
```
