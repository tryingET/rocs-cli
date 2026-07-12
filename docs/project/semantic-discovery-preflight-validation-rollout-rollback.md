---
summary: "Post-ADR validation, development rollout, and rollback contract for decision:52."
read_when:
  - "Validating or rolling out decision:52 implementation."
  - "Checking rollback and non-authorization boundaries for semantic preflight."
type: "validation_rollout_rollback"
status: "accepted_plan"
---
# Validation / Rollout / Rollback — Semantic Discovery and Pi Preflight

## Scope

This plan covers development-only implementation under decision `52`. It does not authorize production adoption or defaults.

## Validation gates

### Protocol

- Parse every JSON/JSON-Schema artifact offline.
- Run Draft 2020-12 validation in Python and TypeScript.
- Recompute every JCS preimage and domain digest independently.
- Verify valid, schema-invalid, invariant-invalid, malformed/error, omission, normalization, ordering, metamorphic, prepared-runtime, and byte-boundary cases.
- Fail if producer and verifier disagree on bytes, digest, outcome, pointer tuple, or invariant.

### ROCS

- Full existing unit suite.
- Parser/command-contract parity.
- Cache-disabled filesystem-invariance test.
- Snapshot race, symlink, root escape, duplicate path/ID, invalid UTF-8, unsupported Unicode/platform, and resource-exhaustion tests.
- Bound-pack snapshot/document mismatch tests.
- No network/model/shell callback execution.
- Preserve `uv.lock` SHA-256 `2faf5bc9a99011b4eeb7c99f3464ee6bdd6f720173c954a4264f246cdb5272f9` unless a separately reviewed dependency decision changes it.

### Pi host

- Host capability identity on supported version.
- Unsupported/missing/forged capability facts disable preflight.
- Startup, reload, new, resume, fork, and shutdown canaries.
- Headless/RPC cannot enable development mode.

### Pi adapter

- Complete TypeScript fixture parity.
- Hostile repository wrapper never executes.
- Prepared-runtime raw bytes, permissions, symlink, atomic publication, and drift tests.
- One 750 ms end-to-end timeout including teardown.
- Streaming cap and total error projection tests.
- Marker forgery/load-order/provider-hook tests.
- Prompt-run scope and TUI readback tests.
- Existing default search remains unchanged outside the gate.

### Vertical slice

- Sanitized environment, no network, no ambient `PYTHONPATH`, no implicit dotenv.
- Disposable consumer only.
- Byte-for-byte before/after repository and managed `dist/` comparison.
- Independent replay from recorded request and identities.

## Development rollout

1. Land ROCS fixture substrate and core behind no automatic consumer path.
2. Land host capability identity.
3. Land Pi adapter disabled by default.
4. Install local package and `/reload` only after package checks.
5. Enable one TUI generation with explicit confirmation.
6. Run the disposable vertical slice.
7. Record AK evidence for each owner task.
8. Disable the session gate after proof.

No rollout to other consumers follows automatically.

## Stop conditions

Stop and fail the active task if:

- schema or digest parity diverges;
- discovery/pack sees generation drift;
- any repository wrapper or inherited environment affects automatic execution;
- arbitrary ontology prose reaches the system-role block;
- session replacement leaves a child process or stale result;
- default search changes outside the explicit gate;
- repository, managed `dist/`, or `uv.lock` changes unexpectedly;
- decision `53` production facts are implied or implemented by convenience.

## Rollback

### ROCS development code

- Revert the bounded owner commit(s).
- Confirm existing 153+ current suite baseline and command contracts.
- Remove only new external development caches after verifying their path and ownership.

### Pi host capability

- Revert the capability-field commit.
- Adapter detects absence and remains disabled.

### Pi adapter

- Run `/ontology-preflight disable` or reload the extension generation.
- Remove the staged content-addressed runtime.
- Restore the prior package commit/version.
- Verify current TypeScript search and startup behavior.

### Evidence and AK

- Do not delete decisions, reviews, ADR, tasks, receipts, or evidence.
- Failed tasks remain historical; open reframed tasks if needed.
- Supersede the ADR only through a new decision if the architecture itself is rejected.

## Production rollback

Not owned here. Decision `53` must define semantic N→N−1/no-prior fallback, runtime/package rollback, adoption receipt handling, and default/fleet rollback before production work.

## Completion evidence

Each task records:

- exact commits/files;
- executable commands and outcomes;
- fixture/digest evidence;
- filesystem-effect evidence;
- rollback rehearsal or justified non-destructive proof;
- explicit deferred owner facts.

Decision `52` may become execution-unblocked only after these plans are attached and all linked post-ADR tasks are explicitly reevaluated.

## Development vertical proof — I7

The isolated development slice is recorded by:

- replay script: [`tests/verify_semantic_preflight_vertical.mjs`](../../tests/verify_semantic_preflight_vertical.mjs);
- closed receipt: [`artifacts/semantic-preflight/decision52-i7-receipt.json`](../../artifacts/semantic-preflight/decision52-i7-receipt.json);
- receipt contract test: [`tests/test_semantic_preflight_vertical_receipt.py`](../../tests/test_semantic_preflight_vertical_receipt.py).

The proof ran from a sanitized `env -i` process with explicit Node, TS loader, package root, and previously verified content-addressed runtime coordinates. It demonstrated:

- explicit TUI confirmation and development-only host capabilities;
- one matched prompt-run discovery with structural metadata only in system role;
- prompt-local exact-ID snapshot/document-bound pack retrieval;
- no inherited `PYTHONPATH`, runner override, shell, network requirement, or sibling runner discovery;
- byte-identical consumer files before/after and no managed `dist/` creation;
- synchronous grant invalidation at shutdown;
- `adopted_runtime=false`, preserving the decision-`53` production membrane.

Replay requires an already prepared and verified development runtime:

```bash
RUNTIME_ROOT=<extension-cache/runtime-sha256>
PACKAGE_ROOT=~/ai-society/softwareco/owned/pi-extensions/packages/pi-ontology-workflows

env -i HOME=/tmp/decision52-home PATH=/usr/bin:/bin LANG=C.UTF-8 LC_ALL=C.UTF-8 \
  /usr/bin/node --import "$PACKAGE_ROOT/node_modules/tsx/dist/loader.mjs" \
  tests/verify_semantic_preflight_vertical.mjs \
  --runtime-root "$RUNTIME_ROOT" \
  --package-root "$PACKAGE_ROOT" \
  --output artifacts/semantic-preflight/decision52-i7-receipt.json
```

The checked receipt binds ROCS commit `ddbfa70b29c5805c859d32abc3265278cc6ce0d2`, Pi host commit `5be4473cc156eb03d0069cc6770f1b95ea9eac97`, and Pi adapter correction commit `5719669cf4476f5f33cc9ac082b2de3af6940dd2`. It is development evidence only, not semantic release, runtime adoption, or fleet authorization.
