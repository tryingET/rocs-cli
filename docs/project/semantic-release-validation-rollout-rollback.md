---
summary: "Validation, staged rollout, stop conditions, and rollback contract for Decision 53 implementation and its separately gated single canary."
read_when:
  - "Validating or rolling out Decision 53 implementation."
  - "Reviewing semantic publication, adoption, or rollback evidence."
type: "validation_rollout_rollback"
status: "accepted_plan"
---
# Validation / Rollout / Rollback — Semantic Release and Single Canary

## Scope and authority

This plan implements the safety obligations of [`../adr/2026-07-13-semantic-release-and-single-canary-adoption.md`](../adr/2026-07-13-semantic-release-and-single-canary-adoption.md) and sequences [`semantic-release-implementation-plan.md`](semantic-release-implementation-plan.md).

It authorizes validation of default-off implementation substrate after AK unblocking. Live capability provisioning, publication, consumer consent, activation, and rollback operations remain separately owned and gated. No passing test or fixture may manufacture an owner fact.

## Baseline record

Before implementation, record:

- exact Decision 53 state, ADR, plan revisions, task IDs, dependencies, and target repositories;
- exact repository commits and clean/dirty status without modifying concurrent work;
- current schema/fixture aggregate digest and authenticated shard manifests;
- current ROCS version and `uv.lock` digest;
- current Pi host/adapter identities and default-off behavior;
- absence or owner-confirmed identity of the exact consumer and recovery controller.

The prior `uv.lock` digest from Decision 52 is historical. The current reviewed release baseline must be recorded per task; it must not be silently rewritten during Decision 53 work.

## Validation gates

### V1 — Accepted packet integrity

- Deterministically regenerate only through `schema_builder.py` and `generate_fixtures.py`.
- Parse all JSON and schemas offline with no remote resolution.
- Verify all schema IDs, registries, manifests, source audits, role mappings, authority edges, digest links, shard counts, byte bounds, and aggregate digests.
- Independently run Python and Node validators.
- Reject duplicate keys, non-canonical integers, floats where forbidden, Unicode/normalization drift, omission/null ambiguity, unknown types, and unregistered authority roles.
- Preserve the accepted 54-type, 122-object, 150-authority-edge, 390-differential-case, 10-raw-case, three-shard baseline unless a separately reviewed protocol revision changes it.

### V2 — ROCS deterministic runtime

- Full unit and integration suite plus command/effect-contract parity.
- Complete-tree equality across source, payload, capsule, archive, and projection identities.
- No-follow, root escape, inode replacement, race, duplicate ID/path, invalid UTF-8, resource exhaustion, and platform/Unicode tests.
- Closed environment, fixed argv, no shell, no network, no ambient `PYTHONPATH`, no repository wrappers, and no mutable `dist/` authority.
- One bounded deadline across verification, I/O, parsing, TERM/KILL/reap, and receipt production.
- Byte caps, object/depth/edge caps, and authenticated sharding.
- Filesystem before/after comparison outside explicit disposable roots.

### V3 — Owner acquisition and currentness

For each semantic owner, AK, consumer owner, Pi, and recovery-controller input:

- prove owner-specific local capability identity and immutable terminal pin;
- prove authenticated store-read provenance, canonical head, observation epoch, and action-time freshness;
- prove trust rotation/revocation and compatibility override state are independent canonical facts;
- prove the transport collator cannot issue, replace, omit, or reinterpret owner facts;
- reject stale, revoked, superseded, cross-owner, cross-repository, and self-asserted canonical observations;
- verify live capability distribution only after the separately approved G1 review.

### V4 — State-machine and crash safety

Inject failure before and after every mutation descriptor for:

- semantic publication, withdrawal, revocation, and typed recovery;
- consumer intent, acceptance, activation, deactivation, and rollback;
- ROCS materialization and generation;
- Pi delivery/suppression/failure attestation;
- AK evidence linkage.

Prove exact predecessor/CAS behavior, immutable append-only history, replay rejection, idempotent recovery, prior-head equality, partial-failure classification, and restoration/preservation of the exact preimage.

Receipt/history roots must survive semantic/runtime replacement and remain independently readable.

### V5 — Authority separation

Adversarially prove that:

- semantic owner facts cannot be issued by ROCS, AK, Pi, consumer, or collator;
- consumer intent/acceptance/activation cannot be issued by semantic owner, ROCS, AK, Pi, or recovery controller;
- AK alone supplies canonical task/decision/evidence state;
- Pi delivery attestations do not imply adoption or influence;
- the recovery controller executes only an accepted owner request and cannot select policy;
- historical artifact integrity does not imply current authorization;
- publication does not imply adoption, adoption does not imply use, and delivery does not imply influence.

### V6 — Scope and identity

Reject:

- any consumer other than `softwareco/pi-canary-consumer` identity revision `3`;
- a missing or substituted consumer repository;
- any canary other than the one explicitly named by the operator and accepted by the consumer owner;
- any second canary or consumer;
- repository rename or canonical-locator drift;
- recovery controller identity drift or runtime-root overlap;
- activation of a revoked or superseded candidate;
- default, startup, automatic-preflight, or fleet expansion.

### V7 — Independent review and replay

Each implementation task requires independent review of its code and evidence. Before G1, G3, or G4, run fresh semantic-owner, ROCS, governance, and security/operations lanes against exact commits and artifacts. Reviewer execution failures create no outcome.

Replay must work from sanitized isolated installs with fixed local inputs and no sibling discovery. Evidence records bind exact commands, commits, digests, task IDs, owner facts, and outcomes.

## Staged rollout

### R0 — Planning and AK release

1. Commit and attach the implementation plan, validation/rollout/rollback plan, and owner-scoped cross-repo fan-out.
2. Create existing-owner execution tasks with exact repo-relative scopes and guardrails; audit their concrete IDs against the fan-out before reevaluation.
3. Link them as `post_adr_execution`.
4. Advance Decision 53 to `tasks_reevaluation_pending`.
5. Explicitly reevaluate every linked task.
6. Advance Decision 53 to `unblocked` only when the passport says ready.

This releases default-off implementation work, not production authority.

### R1 — Offline implementation

Land I1 and I2 in ROCS. Land I3–I5 only in clean owner worktrees. Keep `live_acquisition_implemented=false`, production actions unreachable, and current consumer behavior unchanged.

### R2 — Identity and owner readiness

Resolve I6. Do not substitute an existing repository for the absent exact consumer or recovery controller. Record owner consent and identity through their proper surfaces.

### R3 — Live acquisition gate

Run the fresh G1 review. If accepted, provision only the owner-specific local capabilities and prove currentness/revocation behavior in an isolated non-production environment. Changing the live-acquisition flag is its own reviewed, evidenced commit.

### R4 — Disposable vertical proof

Run G2 with disposable owner stores, semantic source, consumer, runtime roots, and recovery roots. Rehearse semantic, runtime, disable, combined, partial-failure, and no-prior rollback paths.

### R5 — Publication

Only the semantic owner may authorize G3. Publish one exact immutable release through CAS after clean-source, approval, trust/currentness, archive equality, and recovery readiness pass. Record that publication does not authorize adoption.

### R6 — One named canary

Only the exact consumer owner may issue intent, acceptance, activation, deactivation, or rollback. Activate one operator-named canary after exact locally available rollback targets and independent recovery-controller health are current. Keep all defaults and other consumers unchanged.

### R7 — Hold and closeout

Observe the canary for the owner-approved bounded window. Collect AK evidence and optional DSPx/Oracle traces without promoting them into authority. Rehearse rollback again, record learning, then either deactivate/rollback or explicitly retain the one canary. No fleet continuation follows automatically.

## Stop conditions

Stop before mutation or restore/preserve the prior state if any of the following occurs:

- packet, schema, digest, Python/Node, source-audit, manifest, registry, shard, or mutation-descriptor divergence;
- absent, stale, revoked, superseded, unpinned, cross-owner, or self-asserted authority;
- unresolved AK task/dependency/evidence/stop reference or any reference-ID inequality;
- dirty target worktree without an owner-approved isolated clean worktree;
- source/tree/archive/projection inequality;
- generation, publication, activation, or trust-head drift;
- consumer/canary/repository/recovery-controller identity mismatch;
- recovery controller unavailable, overlapping replaceable roots, or unable to use the predeclared local target;
- network, shell, wrapper, ambient environment, model, or mutable `dist/` influence;
- resource cap, deadline, teardown, crash-safety, or receipt persistence failure;
- arbitrary ontology prose entering automatic system-role context;
- any attempt to infer publication from approval, adoption from publication, use from delivery, or influence from use;
- second-consumer, second-canary, default, startup, mandatory, or fleet expansion;
- unexpected `uv.lock`, owner repository, managed `dist/`, or production-state mutation.

## Rollback

### Default-off implementation

- Revert only the bounded owner commit(s).
- Re-run the repository's pre-change gate and accepted packet validators.
- Remove only content-addressed disposable artifacts whose owner and path are verified.
- Preserve tasks, decisions, reviews, ADRs, receipts, evidence, and failed-attempt history.

### Live capability acquisition

- Revoke or disable the exact local capability pin through its issuing owner.
- Stop new acquisition before removing staged runtime material.
- Verify stale/revoked capabilities fail closed and no child process remains.
- Restore `live_acquisition_implemented=false` through reviewed code/state if the live boundary is withdrawn.

### Semantic publication

- Never rewrite or delete an immutable publication record.
- Semantic owner issues withdrawal/revocation or an accepted recovery request using the canonical prior head.
- Recovery controller executes only the typed request; ROCS verifies CAS, archive equality, and resulting head.
- Consumer activation remains separately governed; publication rollback does not silently change consumer state.

### Canary

Predeclare and locally stage, before activation:

- semantic N−1 or disable/no-prior target;
- prior runtime/package identity;
- consumer activation predecessor;
- independent recovery-controller identity and health receipt;
- exact semantic, runtime, disable, combined, and partial-failure actions.

Consumer owner selects the accepted rollback policy. Recovery controller executes it idempotently. Pi reports delivery state only. AK records evidence and task lineage only. If no prior semantic target exists, disable rather than inventing one.

### Architecture escape hatch

If owner boundaries or the one-canary architecture prove unsound, stop implementation, supersede Decision 53 and its ADR through a new reviewed decision, and retain all historical artifacts. Do not widen protocol v0 in place.

## Required completion evidence

Each task records:

- exact commit, files, task scope, and dependency IDs;
- commands and exit outcomes;
- independent review reference;
- fixture, digest, authority-edge, and owner-currentness evidence applicable to the slice;
- filesystem/network/process effect evidence;
- crash/rollback rehearsal or an explicit proof that the slice cannot mutate live state;
- preserved concurrent-work and baseline digests;
- deferred owner facts and legal next action.

The implementation program closes only after all executed tasks are complete, every live operation has its own owner authorization and evidence, rollback is rehearsed, and the KES learning artifact links back to this plan and the execution receipts.
