---
summary: "Post-ADR cross-repo implementation plan for decision:52 deterministic ROCS discovery and gated Pi semantic preflight."
read_when:
  - "Implementing decision:52 after ADR recording."
  - "Creating or reviewing decision:52 execution tasks."
type: "implementation_plan"
status: "accepted_plan"
---
# Implementation Plan — Deterministic Semantic Discovery and Pi Preflight

## Authority

- AK decision: `52`
- ADR: `docs/adr/2026-07-12-deterministic-semantic-discovery-and-pi-preflight.md`
- Production dependency: decision `53`

This plan authorizes only the development-safe architecture accepted by decision `52`. Production semantic release/adoption and default changes remain blocked.

## Execution sequence

### I1 — ROCS fixture and canonicalization substrate

Owner: `core/rocs-cli`

- Add importable schema loading/validation for the accepted Draft 2020-12 bundle without network resolution.
- Add RFC 8785-compatible integer-only canonicalization and domain hashing.
- Turn golden/differential artifacts into executable Python conformance tests.
- Preserve existing intelligence/transaction digest behavior unless explicitly migrated by separate tests.

Gate: Python reproduces every committed valid digest and rejects every schema/invariant-invalid fixture.

### I2 — ROCS corpus snapshot and discovery core

Owner: `core/rocs-cli`

- Implement quiescent two-pass corpus capture.
- Implement `rocs-lexical-v0` exactly.
- Implement request/result/error/capability models.
- Enforce resource, platform, Unicode, environment, and no-cache behavior.

Gate: pure unit/metamorphic tests pass with no repository or managed `dist/` mutation.

### I3 — ROCS CLI and bound pack

Owner: `core/rocs-cli`

- Add `discover-capabilities`.
- Add `discover --request-json -` and explicit interactive file input.
- Add snapshot/document preconditions and identity output to bound pack mode.
- Register parser/effect contracts and JSON errors.
- Preserve unbound interactive pack compatibility and all existing command behavior.

Gate: parser/contracts remain closed and full ROCS test suite passes.

### I4 — Pi host capability identity

Owner: Pi runtime / `softwareco/contrib/pi-mono`.

- Add immutable host-supplied extension capability identity required by the companion RFC.
- Cover package/version/API/capability values and lifecycle consistency.
- Do not allow repository/environment override.

Gate: host canary proves capability identity through startup/reload/new/resume/fork and unsupported hosts disable the adapter visibly.

### I5 — Pi runner, protocol, and inspect migration path

Owner: `pi-ontology-workflows`.

- Add TypeScript validators and digest verification over accepted fixtures.
- Add prepared-runtime schema, raw-byte verification, atomic staging, and immutable descriptor.
- Add closed subprocess environment, process-group timeout, stream caps, and total error mapping.
- Add gated ROCS discovery and bound-pack port methods.
- Preserve default TypeScript search outside the development gate.

Gate: hostile wrapper/environment/fixture tests fail closed; gated search performs no build or managed `dist/` writes.

### I6 — Pi prompt-run lifecycle and TUI dogfood

Owner: `pi-ontology-workflows`.

- Add generation-scoped readiness state.
- Add idle-only, expiring TUI development confirmation.
- Add prompt-run structural rendering and complete TUI outcome readback.
- Add unauthenticated advisory availability event without requiring startup-context consumer adoption.
- Add reload/new/resume/fork/shutdown/timeout/stale-completion tests.

Gate: automatic behavior remains disabled by default; all lifecycle and hostile-marker tests pass.

### I7 — Isolated cross-repo vertical slice

Owners: ROCS + Pi extension + disposable consumer.

Prove offline with sanitized environment:

1. prepared development runtime identity;
2. immutable development snapshot;
3. deterministic ordinary-language candidates;
4. ambiguity with no selection;
5. bound exact-ID pack;
6. visible timeout/unavailable behavior;
7. hostile ontology prose excluded from system role;
8. replayable request/result/pack digests;
9. no repository/managed-dist mutation;
10. disable-to-current rollback.

This slice is development evidence only.

## Deferred work

Blocked by decision `53` and separate evidence gates:

- adopted production runtime;
- semantic release coordinate;
- consumer dependency intent and adoption/use receipts;
- explicit search default cutover;
- automatic preflight default;
- startup orientation default;
- fleet rollout or mandatory enforcement.

## Task decomposition rule

Create one owner-scoped AK task per I1–I7 slice. Link every task to decision `52` as `post_adr_execution`. Tasks may be combined only when one owner can preserve the same validation and rollback boundary.
