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

- Run `/ontology-preflight disable-development` when available or reload the extension generation.
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
