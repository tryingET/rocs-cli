---
summary: "Validation, staged rollout, and rollback plan for Decision 104's separated policy/broker/state-machine architecture."
read_when:
  - "Reviewing or planning any Decision 104 implementation slice."
type: "validation_rollout_rollback"
status: "proposed"
decision_id: 104
---
# Validation, rollout, and rollback — semantic evaluation custody broker v1

## Current gate

Design and strict review only. No runtime implementation, real policy, D/U/O, broker, process, publication, currentness, consumer, Pi/provider/model, prompt projection, or automatic-preflight effect is authorized.

## Validation order

### V0 — packet integrity

- validate front matter and links;
- parse `state-machine.json` as duplicate-key-rejecting I-JSON;
- recompute every manifest byte length/SHA-256 and the packet aggregate;
- require the working diff to match the exact design-task scope.

### V1 — model constructibility

A small independent checker shall:

- validate the canonical global-store allocator plus unique execution states, operations, fields, branch predicates, exact identifier derivations, and error kinds;
- implement the closed guard/effect predicate language and reject unknown fields/operators;
- prove stable attempt identity; atomic allocation+record+journal creation; both command-local depth-256 nonmembership/inclusion updates; both descriptor-derived current memberships; fixed sibling ordering/work; typed global config/caller pins/local head/record/receipt predicates; exact initial projection; identifier framing; machine-wide transition lookup/expected-generation/delta commit; conditional invariants; and read IDs moving absent → durable one-read spool → consumed once;
- enumerate the complete bounded state-vector space for each frozen fixture size from `initial_state` to `verdict_fixed`;
- prove every verdict path includes `closed` immediately before fixation and unresolved supervisor ambiguity cannot reach either state;
- prove exactly one of eight structured branch predicates matches each closed state and derive its allowed outcomes;
- generate illegal operation, failed guard, skipped-state, transition-ID collision, stale-generation, retry, rerun, reopen, read/close race, and ambiguous-branch vectors.
- prove allocation A creates one immutable initial record atomically, then allocation B may advance both roots before A's first readback; A renews only descriptor-derived current memberships while its record/initial state remain byte-identical;
- prove the 4 MiB descriptor projection, numeric 16,384 global-journal max, 8,192 protected-read max, 64 in-flight max, 33,000 event max, and safe-integer clock ceilings; the longest successful path is exactly `17 + 4×8192 = 32785` operations, and exact maxima pass while max+1 returns `resource_exhausted` before any root/sequence/generation/set/spool effect.

The model is reviewed before any serialized protocol object.

### V2 — pure-policy conformance

- independently re-evaluate which Decision 103 R0/R1 canonicalization, digest, signature, inventory, and source-binding mechanics remain pure-policy compatible;
- reject inherited custody/execution/publication fields;
- verify Python and Node independently recompute canonical bytes and digests;
- use hash-manifested conspicuously synthetic fixtures only.

### V3 — broker model and fault proof

First use an in-memory reference model solely as an oracle; then implement a real local broker/journal/verdict register in owner repository `softwareco/owned/dspx`. For both:

- linearizability-check concurrent global journal allocation, reservation, authorization, start-commit, supervisor disposition, handle, derived read-admission/completion, cleanup, state-read, and verdict-append histories;
- inject crashes before/after each durable write and external supervisor/process/handle/read effect;
- prove exactly one allocation+seal, exact-envelope idempotent lookup, unequal transition-ID reuse rejection, one spawn-intent claim and one spawn syscall, no retry after claim, one protected-store read per durable spool slot, expiry/revocation denial, read-barrier drain/cancel, containment emptiness, reaping, handle closure, and convergence to `closed`;
- prove ambiguous spawn disposition cannot close or fix a verdict and stable supervisor identity resists PID reuse;
- authenticate actual test actors/channels/key possession rather than trusting declared identity fields;
- independently read explicit local journal bytes and verify fresh challenge-bound fixation state proofs; old receipts over rolled-back/forked/missing state reject;
- after verdict append, verify renewable challenge-bound verdict-register inclusion/head proofs outside the immutable verdict;
- hit every resource max/max+1 boundary.

Passing the reference model does not authorize or substitute for a real broker.

### V4 — generated evaluator parity

Generate or mechanically derive transition vectors, nullable evidence projections, and branch/outcome matrices from `state-machine.json`. Python and independent Node implementations must agree byte-for-byte while sharing no validator implementation or derived expected booleans.

Adversarial cases include:

- forged evidence/support constructor;
- outer verdict versus signed-subject drift;
- every authority/credential/key/root/purpose/caller-pin substitution;
- global allocator self-pinning, wrong DSPx owner/store/descriptor anchor, caller-created sealed record, duplicate journal or stable-attempt claim, channel/gateway/maxima variation over the same attempt identity, later root advancement after an earlier atomic record, changed sealed subject, malformed 256-sibling update/membership proof, and typed global-config/caller-pin/local-head/record/receipt mismatch;
- caller-invented contamination coordinates;
- map-order permutation;
- malformed mapping/list/path/encoding types;
- stale/forked generations and duplicate transition IDs;
- equal versus unequal transition-ID replay and cross-actor receipt disclosure;
- valid old receipt against rolled-back/forked/missing canonical journal state;
- stale state-read challenge, head, clock epoch, or terminal snapshot;
- fresh-at-fixation versus renewable action-time proof boundary;
- authenticated wrong actor/channel/process/lease/handle/seal on every protected operation;
- replacement of any immutable sealed evaluator/gateway/channel/process/policy/dataset coordinate at reserve/authorize or later;
- authorization/start/receipt/pass/read CAS races against reservation or lease monotonic/UTC/epoch expiry and owner/gateway revocation;
- unauthorized reserve/reject/abort/evidence/pass/terminal/cleanup/verdict operation;
- read-ID collision/reuse across journals plus duplicate/cross-read/cross-channel terminal disposition using distinct transition IDs;
- ambiguous variable-length identifier framing, changed domain byte, changed uint32 length, changed uint64 endianness/sequence;
- numeric global 16,384, read 8,192, in-flight 64, and event 33,000 exact max/max+1 with no partial root/generation/sequence/set/spool effect;
- spawn ambiguity/PID reuse and every read-begin/close/revoke/expiry race;
- crash after spawn claim before/after the sole spawn syscall, containment cleanup, crash before/after spool population and acknowledgement, and proof that retry never performs a second external effect;
- journal/register crash points, attacker-selected register authority, approval identity overlap, old approval with changed outcome, stale fixation proof, and every declared safe failure precedence combination;
- delta-event trace growth at max reads, proving no prior read set is copied into each event;
- every crash point, retained process/handle/lease, late cleanup, retry/rerun/repair;
- all legal and illegal branch/outcome combinations;
- every aggregate resource boundary.

### V5 — semantic-release integration

Use Decision 53's synthetic/default-off publication/currentness implementation only if a reviewed compatibility adapter can reference policy/verdict coordinates without widening Decision 53 semantics. Otherwise stop for a separate successor decision. Do not duplicate owner history, checkpoint, challenge, acquisition, or consumer machinery.

### V6 — synthetic end-to-end dogfood

In fresh private temporary stores and repositories:

1. construct a synthetic immutable policy coordinate;
2. drive every legal state-machine branch through a real local DSPx broker/journal implementation;
3. independently inspect the atomic allocation+sealed-record+generation-zero-journal transaction, stable attempt identity, both command-local sparse-map updates, independent owner/store/descriptor pins, descriptor-derived current memberships, typed record/receipt/local-head predicates, exact initial projection, and framed journal/read derivations; force allocation B before A's first readback and prove only A's memberships renew; then observe envelope/replay/generation/delta events, sealed evaluator/gateway/channel/process/seal pins, reservation/lease bounds, spawn containment/claim/process identity, one-read spool lifecycle, reaping, handle state, and cleanup;
4. challenge and verify a fresh fixation state proof, fix only permissible verdicts through the DSPx verdict register with exact independent approval, then verify a separately renewable register inclusion/head proof;
5. optionally reference a qualifying synthetic verdict through the existing default-off semantic-release verifier;
6. replay every illegal transition and fault point;
7. retain digest-addressed public receipts and logs with no handles, protected bytes, private keys, secrets, or B0 material.

Dogfood proves only synthetic mechanics.

### V7 — independent acceptance and rollback rehearsal

Require independent lanes for state-machine constructibility, broker security/linearizability, authority boundaries, and adversarial implementation. Green unit tests are implementation evidence only.

In clean isolated clones/workspaces, revert each accepted implementation slice in reverse exact-commit order and run the full applicable suite after every revert. Final trees must equal the recorded bases byte-for-byte.

## Rollout sequence

```text
accepted packet + superseding ADR
→ accepted implementation plan
→ pure-policy substrate task
→ reference state-model task in `core/rocs-cli`
→ real local broker/journal/verdict-register task in `softwareco/owned/dspx`
→ deterministic journal/state-proof/verdict verifier task in `core/rocs-cli`
→ default-off semantic-release adapter task if compatible
→ independent synthetic dogfood task
```

Each arrow requires an accepted predecessor commit/tree, one active owner, exact allowed/forbidden paths, fresh review, deterministic evidence, and rollback proof. No later task absorbs an unresolved finding.

Real policy or D/U/O, owner publication, consumer adoption, Pi/runtime integration, provider/model activity, prompt projection, automatic preflight, and fleet rollout remain separate later decisions.

## Stop conditions

Stop on:

- packet/manifest drift;
- a transition represented outside the canonical contract;
- any claim that a signature enforces runtime behavior;
- ambiguous linearization point or crash disposition;
- raw descriptor or durable bearer-handle transfer;
- cleanup that can reach verdict fixation while process/handle/lease remains live;
- incomplete caller pins or self-issued authority;
- verdict/journal/register ownership not bound to `softwareco/owned/dspx` or deterministic verification not bound to `core/rocs-cli`;
- valid receipt accepted without an equal fresh-at-fixation canonical-journal state proof, or later current verification requiring a new digest inside the immutable verdict instead of a renewable external register proof;
- transition-ID replay not bound to the complete authenticated request;
- any operation bypassing the closed envelope/transaction protocol, repeating implicit generation effects, or returning a receipt before the journal/replay-index transaction commits;
- spawn after a claimed intent is retried, closure without empty containment, a second protected-store read for one spool slot, or transport retry interpreted as a new protected read;
- verdict authority selected by the sealed subject, approval/fixation objects outside closed contracts, or non-atomic journal/register fixation;
- post-close bytes deliverable from an admitted read, cross-journal/within-journal read-ID collision/reuse, duplicate/cross-read/channel completion, or authorization/start/receipt/pass/read after applicable monotonic/UTC/epoch expiry;
- allocator absent from canonical machine, allocation and sealed-record creation not one transaction, actor/request not equal pinned DSPx owner/store, same stable attempt allocating twice under session/resource changes, caller pins not structurally consumed, derived record/head not equal descriptor bytes, historical roots treated as permanently current, sparse update/membership or projection underdefined, non-injective encoding, nonnumeric ceiling, unknown predicate operator/failure, O(journal-count) proof, copied-state quadratic trace, or max+1 partial effect;
- authenticated operation actor/request not joined to immutable sealed owner/evaluator/gateway/channel/process/policy/seal pins and stored reservation/lease/handle/read coordinates;
- broker-owner revocation or cleanup requiring cooperation from an unavailable/compromised gateway;
- termination/reap journal operation without equal supervisor observation of the stored process identity;
- Python/Node/model disagreement;
- fixture oracle not independently derived;
- unsafe/raw exception or order-dependent error kind;
- resource-budget uncertainty;
- missing independent review;
- any live or owner effect outside the exact task.

## Rollback

Before implementation, rollback is deletion/revert of the unaccepted Decision 104 packet while preserving Decision 103 history and failed evidence.

After default-off synthetic implementation, rollback removes Decision 104 components by exact reverse commits and leaves all live-effect flags false. It cannot withdraw/revoke publication or alter consumer state because none is authorized.

A future real broker rollback is controlled by `softwareco/owned/dspx` and must first force all reservations/leases/handles/processes to `closed`, terminally deliver/cancel every broker-issued read ID, prove denied reads against a fresh broker/register proof, and preserve immutable journal/verdict receipts. A software revert is never a substitute for terminal custody cleanup.
