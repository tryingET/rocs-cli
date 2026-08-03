---
summary: "RFC separating immutable semantic policy, custody/execution enforcement, canonical evaluation state, and reused semantic-release publication authority."
read_when:
  - "Reviewing Decision 104 or planning a successor to Decision 103."
type: "rfc"
status: "proposed"
decision_id: 104
---
# RFC — Semantic evaluation custody broker v1

## Status and authority

Proposed for Decision 104 strict convergence. This RFC grants no implementation or live-effect authority. If accepted through a superseding ADR, it replaces Decision 103's combined evaluation proof graph; it does not rewrite Decision 103 history or rehabilitate rejected commit `70d3645`.

## Decision

Adopt four explicit authority boundaries:

```text
immutable semantic policy
        │ policy coordinate
        ▼
custody/execution broker ── observed receipts ──► canonical evaluation machine
                                                     │ fixed verdict
                                                     ▼
                                      existing semantic-release publication/currentness
```

The first three boundaries are defined here. Publication/currentness is delegated to the accepted Decision 53 semantic-release machinery and is not duplicated.

## 1. Immutable semantic-policy protocol

A policy coordinate is immutable data owned by the semantic owner. It contains only:

- semantic-owner identity and repository coordinate;
- policy, provenance, inventory-source, and inventory digests;
- deterministic policy/provenance/inventory extraction coordinates;
- selectable ontology IDs and semantic-binding receipt;
- candidate identifier and digest;
- an optional owner approval over exactly those immutable bytes.

It contains no dataset, participant, contamination, reservation, process, descriptor/handle, lease, access-history, execution, verdict, publication, currentness, consumer, Pi, provider/model, or automatic-preflight field.

A signature over this coordinate proves issuer intent over bytes. It grants no dataset access, process-start right, or publication/currentness status.

## 2. Custody/execution broker

### Ownership

The broker, canonical execution journal, and unique verdict register are owned by `softwareco/owned/dspx`. The semantic owner, ROCS verifier, AK, evaluator process, independent reviewer, consumer, and Pi are not broker authorities. The independent reviewer owns judgment/approval but cannot append or rewrite broker state; DSPx may append a verdict only after exact custodian and independent-review approvals validate.

### Broker state

The broker is the sole authority for mutable execution facts:

- reservation state and compare-and-swap generation;
- authenticated principal/channel binding;
- lease issuance, expiry, and revocation;
- opaque protected-access handles;
- process start observation and single-start enforcement;
- process exit/reaping observation;
- handle closure and read denial after expiry/closure;
- terminal cleanup state.

The authoritative state is a linearizable append/CAS journal and canonical head, not a caller-signed JSON assertion. Every committed operation follows `state-machine.json`, carries an expected generation, and increments generation exactly once. A mismatch returns `state_conflict` and changes nothing.

A transition ID is bound to the complete authenticated request digest, actor/channel coordinate, command, parameters, and expected generation. Request handling order is fixed: authenticate actor and bound request; look up transition ID; return the prior result only when every bound field is equal; reject unequal reuse as `state_conflict`; then compare generation and execute a new operation. This prevents idempotent receipt lookup from leaking or rebinding another actor's result.

### Linearization points

Every operation and guard is enumerated in `state-machine.json`. Important boundaries are:

| Operation | Linearization point | Required postcondition |
|---|---|---|
| `allocate_and_seal_execution_journal` (global store machine) | one broker-owner transaction over global generation, both claim maps, sealed-record namespace, and new execution journal | derived journal ID and stable attempt identity enter insert-only maps; one immutable sealed record and generation-zero journal event are created atomically; receipt is emitted only after commit |
| `reserve` | durable CAS `sealed → reserved` | one reservation ID, generation incremented |
| `authorize` | durable CAS `reserved → authorized` | caller-pinned evaluator/gateway identities and deadlines fixed |
| `start_commit` | durable CAS while still `authorized`, before supervisor handoff | reservation consumed exactly once; later start rejects |
| `claim_spawn_intent` | sole durable `unclaimed → claimed` supervisor CAS | one persistent supervisor worker may issue one spawn syscall into the precreated containment; claimed intent is never retried after crash |
| `record_spawn_observed | record_spawn_failure` | durable supervisor disposition | stable process identity recorded, or absence proved; ambiguity remains non-terminal and blocks closure/verdict |
| `open_handle` | durable handle record before first protected read | opaque handle bound to process, lease, seals, expiry |
| `begin_read` | derive the exactly framed `read_id`, enforce ceilings, increment sequence, and atomically add ID to in-flight | journal allocation verifies; evaluator/channel/process/handle/lease/seals/clocks validate; ID absent from in-flight/consumed; max+1 is `resource_exhausted` before effects |
| `finish_or_cancel_read` | durable spool acknowledgement/cancellation before atomically moving that ID from in-flight to consumed | one protected-store read populates one immutable spool slot; retries expose the same bytes/marker under the same read ID and never perform another protected read |
| `expire_lease_* | invalidate_lease_epoch | revoke_lease_owner | revoke_lease_gateway` | durable lease terminalization and read-admission barrier | no new read; cleanup begins under either accepted clock expiry or independent owner/gateway authority |
| `mark_* | revoke_handle | close_handle | terminate | reap` | corresponding durable journal operation | terminal reason blocks further handle/pass/receipt progress; no handle closes with an in-flight read; supervisor observations bind the stored process identity |
| `close_*` | durable terminal cleanup CAS | no live handle, in-flight read, readable lease, or unreaped process |
| `fix_verdict` | immutable verdict-register append after fresh `closed` proof | one verdict coordinate; no state reopening |

The broker may sign receipts only after the corresponding operation commits. A receipt describes observed committed behavior; it neither causes nor substitutes for that behavior.

### Opaque handles

Protected bytes never cross as raw OS descriptors or durable bearer capabilities. An opaque handle:

- is unguessable and store-backed;
- is bound to one reservation, process identity, lease generation, and exact dataset seals;
- requires broker authorization on every read;
- expires at the earliest applicable deadline;
- derives globally collision-resistant read IDs using the exact framed algorithm below; each ID owns one durable broker spool slot and at most one protected-store read; it remains in-flight until caller acknowledgement or broker cancellation, then moves permanently to consumed; expiry/revocation admits no new read and `closed` requires in-flight empty and no readable spool capability;
- cannot be serialized into policy, verdict, Git, AK, logs, or retained fixtures.

### Actor, clock, supervisor, and crash rules

A broker session uses one reviewed mechanism: mutually authenticated TLS with a caller-pinned exporter, or local Unix peer credentials plus fresh challenge and Ed25519 proof of possession. The session binds the complete repository/commit/tree/principal/role/credential/key/root coordinate and a nonce. Principal text, UID, PID, or a copied signature alone is insufficient.

Before allocation, a closed broker-global config from a trusted DSPx configuration descriptor independently pins owner, store, empty sparse-Merkle root, and numeric ceilings. The allocation command also carries a DSPx descriptor-derived protected-catalog coordinate whose owner/store/dataset-seals fields must equal the subject, and an explicit contamination coordinate recomputed from bounded source bytes plus a source anchor. Caller digest assertions for either coordinate are invalid. `state-machine.json`'s global operation requires the live authenticated actor, request owner/store, and subject owner/store to equal those pins; self-pinning is impossible. `allocate_and_seal_execution_journal` derives the journal ID and validates two exact 256-level nonmembership-to-inclusion updates: `journal_id → sealed_subject_digest` and stable `attempt_identity_digest → journal_id`. The attempt identity is the closed JCS projection of policy, evaluator, dataset seals, contamination coordinate, and evaluation plan; channel, gateway, and resource ceilings cannot create a second attempt.

One DSPx transaction writes all reachable SMT nodes, both new roots, the unique sealed record, the generation-zero execution journal event, transition replay index, sequence, and global generation. Any failure writes none of them. The sealed record is derived inside the transaction from the subject, journal ID, transition envelope, and committed generation/sequence; it cannot be caller-selected or renewed. The post-commit receipt may retain the historical post-roots, but they are not treated as permanently current. A later descriptor-anchored read generates two fixed-depth membership witnesses from the same current persistent-node snapshot. Allocation B after A therefore changes only A's renewable read-time witnesses, never A's immutable record or initial state. Duplicate claim, wrong owner/store/subject, crash replay, and max+1 reject without partial effects.

The exact journal-ID preimage is the bytes in this order: fixed hex `726f63732d73656d616e7469632d6576616c756174696f6e2d6a6f75726e616c2d69642d763100`; uint32-big-endian byte length of canonical strict-UTF-8 `broker_store_id`; those identifier bytes; uint64-big-endian global journal sequence. The output is `sha256:` plus lowercase SHA-256 hex.

The exact read-ID preimage is: fixed hex `726f63732d73656d616e7469632d6576616c756174696f6e2d726561642d69642d763100`; uint32-big-endian byte length plus strict-UTF-8 broker-store ID; uint32-big-endian byte length plus strict-UTF-8 execution-journal ID; uint64-big-endian next-read sequence. The output has the same `sha256:` form. Length framing and fixed-width sequence make tuple encoding injective before hashing.

The pre-allocation sealed subject is one closed RFC 8785 JCS object with exactly: schema `semantic-evaluation-sealed-subject.v1`; broker-store ID; broker-owner, policy, evaluator, gateway, channel, process-request, dataset-seals, contamination-coordinate, and evaluation-plan digests; `max_reads`; and `max_in_flight_reads`. Its required `attempt_identity_digest` is recomputed from closed object schema `semantic-evaluation-attempt-identity.v1` plus exactly policy, evaluator, dataset-seals, contamination-coordinate, and evaluation-plan digests. That identity uses fixed domain hex `726f63732d73656d616e7469632d6576616c756174696f6e2d617474656d70742d6964656e746974792d763100` followed by raw RFC 8785 canonical UTF-8 object bytes. Its digest excludes any digest member and is SHA-256 over fixed domain hex `726f63732d73656d616e7469632d6576616c756174696f6e2d7365616c65642d7375626a6563742d763100` followed by the raw canonical UTF-8 object bytes; output is `sha256:` plus lowercase hex. No field is optional or inferred.

The immutable sealed record contains exactly schema `semantic-evaluation-sealed-record.v1`, nested subject/digest, derived journal ID, allocation transition ID, committed global generation/sequence, and record digest. It nests no receipt, mutable head, signature, challenge, or membership witness. The allocation receipt is post-commit evidence outside the record. This one-way shape removes digest cycles and prevents two fresh proofs from selecting two initial states.

Initial binding takes the record only as a projection derived from one consistent local DSPx read transaction. A closed caller-pin object independently supplies owner/store/canonical-descriptor anchor. `descriptor_parse_eq` validates the anchor's boot/device/inode, opens the one relative store path with beneath/no-symlink/no-cross-device semantics, verifies store UUID/owner/store before and after reading, rejects transaction drift and partial or non-I-JSON projections, enforces a 4 MiB projection ceiling, derives the exact sealed record and current global head, and generates both 256-sibling memberships from the same persistent-node transaction. Sibling index `0` is root-level/key bit 255; verification folds from sibling index 255/key bit 0 to index 0/key bit 255. Structured predicates join owner/store/anchor, record, journal/subject/attempt, generation/sequence, and both current claims. Expected pins may never be derived from the record or local bytes being checked.

`initial_state_projection` is the sole flattening rule: it maps immutable fields from the unique sealed record; no `$sealed.*` alias exists. Only after descriptor derivation, independent pins, and both current memberships pass does it instantiate broker authority, policy, evaluator, gateway, channel, process-request, dataset-seal, `max_reads`, and `max_in_flight_reads` coordinates. `reserve` adds only its exact broker-owner-issued reservation identity/epoch/deadline. `authorize` must equal every sealed coordinate and may add only the lease ID, monotonic epoch/tick bound, and authenticated UTC bound. It cannot replace evaluator, gateway, channel, process, policy, or seals.

Every later operation—including evidence receipt/pass progress, terminal marking, cleanup, and verdict append—compares its authenticated actor or broker/supervisor/I/O observation and exact reservation/channel/process/lease/handle/seal/read values to stored fields. Authentication without operation-specific equality and role guards is never authorization. Lease expiry checks the earliest failure among monotonic tick, authenticated UTC, and epoch continuity. DSPx broker-owner revocation is independent of gateway cooperation; the gateway also retains its own bounded revoke operation.

Before `start_commit`, DSPx creates an empty unique OS containment selected by a crash-stable digest. `start_commit` consumes the reservation and durably records one intent plus an unclaimed supervisor slot. `claim_spawn_intent` is the only `unclaimed → claimed` CAS; one persistent supervisor worker may issue one spawn syscall into that containment. A claimed intent is never retried after worker or supervisor crash. Recovery inspects PID-reuse-resistant handles and containment membership, records the one observed process, or terminates everything and proves the containment empty. Ambiguity cannot become `not_started` or `closed`; both closure operations require containment empty.

Reservation expiry is checked on `authorize`; it cannot be bypassed by racing the expiry operation. Lease epoch, monotonic deadline, and authenticated UTC bound are checked on authorization, start, protected reads, execution-receipt fixation, and pass progress—not only by separate expiry operations. While `authorized`, independent deadline/UTC/epoch and broker-owner/gateway revocation operations terminalize the lease; a no-start transition closes an uncommitted spawn, while a committed spawn must still receive a supervisor disposition. Reboot/epoch change invalidates admission and forces cleanup. Expiry starts the same barrier as explicit revocation.

- Crash before a committed operation leaves the prior state authoritative.
- Crash after commit and before receipt delivery permits exact-request idempotent receipt retrieval; it never re-executes the operation.
- Crash after `start_commit` cannot permit a second process start.
- Every resolved recovery path converges to `closed`; cleanup failure blocks verdict fixation.
- An indeterminate process identity, unreaped process, live handle, in-flight read, readable expired lease, or ambiguous generation is fail-closed and non-publishable.

### Canonical state proof

Receipts are insufficient for verdict fixation. At fixation, the caller supplies explicit local broker-journal bytes plus one fresh, challenge-bound fixation state proof naming the canonical store/head, generation, predecessor/head digest, complete execution-trace digest through `closed`, terminal state snapshot, broker identity/key/root, capture time/clock epoch, and signature. ROCS performs bounded descriptor-anchored reads of the explicit local store, recomputes the journal chain/head/snapshot, and requires equality with that proof and fixation-request pins. A valid old receipt, rolled-back/forked store, missing journal entry, stale fixation proof, or signer-only assertion rejects.

The fixation proof is immutable historical evidence and need not remain fresh forever. A later action-time check obtains a new challenge-bound verdict-register read proof of immutable verdict inclusion and the current canonical register head; this renewable proof is outside the verdict. If Decision 53 cannot consume that external inclusion proof without widening, integration stops for a separate successor decision.

## 3. Canonical evaluation state machine

The sole normative transition source is [`semantic-evaluation-custody-broker-v1/state-machine.json`](semantic-evaluation-custody-broker-v1/state-machine.json). Prose explains it but cannot add transitions.

```text
sealed
→ reserved
→ authorized
→ started | not_started
→ closed
→ verdict_fixed
```

### State meanings

- `sealed`: immutable policy coordinate, evaluator identity, dataset seals, contamination coordinates, and evaluation plan are fixed; no reservation or access exists.
- `reserved`: one expiring execution reservation exists; no start or protected access exists.
- `authorized`: caller pins, authenticated broker channel, exact process request, and deadlines are fixed; no process has yet been observed started.
- `started`: the broker committed zero-to-one start and observed the one process identity; protected access remains broker-mediated.
- `not_started`: a terminal no-start reason is fixed; no process or protected handle may exist.
- `closed`: reservation/lease is terminal, every handle is closed, reads are denied, and any started process is terminated and reaped.
- `verdict_fixed`: one immutable outcome references the policy coordinate, state-machine trace, broker receipts, aggregate metrics, and independent approvals.

No state is publishable. Only a separately published semantic release may reference a qualifying verdict.

### Branches

The state machine preserves eight evidence branches without encoding them as eight independently maintained schema unions:

1. no authorization/start evidence, `not_started`;
2. authorization fixed but no start commit, `not_started`;
3. start transaction authorized/consumed but no process observed, `not_started`;
4. started, zero passes, no handle/receipt, interrupted;
5. started, zero passes, handle opened, no execution receipt, interrupted;
6. started, zero passes, handle opened, execution receipt fixed, interrupted;
7. started, one primary pass, handle and receipt fixed, interrupted;
8. started, primary plus immediate-repeat pass, completed.

Branches 1–7 fix outcome `indeterminate`. Branch 8 fixes `pass` or `fail` according to frozen gates. Every branch transitions through `closed`; none can retry, rerun, repair, or reopen.

### Trace and derivation

The verifier consumes the canonical journal's ordered execution trace. Every call first passes the machine-wide closed operation envelope and transaction protocol: validate types/digests; derive and compare live actor/channel; look up transition ID; replay only an exactly equal complete envelope; reject unequal reuse; compare expected generation; evaluate all typed guards and fixed failures; then atomically append one delta event, update the replay index, apply effects/artifacts, and increment generation once. Each canonical event contains prior/new state digests plus the typed changed-field delta—not copied prior/new read sets—along with the envelope, clock coordinate, result, and event digest. It validates every operation, guard, effect, generation, invariant, and branch predicate against the machine contract, then derives:

- legal branch;
- exact nullable evidence projection;
- invocation/pass counts;
- required broker receipts;
- cleanup obligations;
- permissible verdict outcomes.

Schemas, Python/Node validators, fixture generators, and legal/illegal vectors must be generated from or mechanically checked against this table. Hand-authored branch unions may add representation constraints but cannot define behavior.

## 4. Verdict and approval

A verdict is immutable and contains:

- policy coordinate digest;
- canonical state-machine contract digest;
- pre-verdict execution-trace digest covering operations through `closed` and explicitly excluding `fix_verdict`;
- fixation-state-proof digest, broker identity, canonical head, and terminal generation;
- exact broker receipt digests;
- dataset/evaluator/contamination coordinate digests;
- aggregate execution/metric digests;
- branch and outcome;
- one non-circular approval subject;
- custodian and distinct independent-review approvals over that exact subject.

The outer verdict projection must equal the signed approval subject field-for-field for every approval-relevant coordinate, including outcome. The subject explicitly binds the descriptor-recomputed broker-receipt set, contamination coordinate, aggregate execution, metrics, frozen-gates digest, and nullable gate-evaluation digest. Branches 1–7 require `indeterminate` with no gate evaluation. Branch 8 requires a closed gate-evaluation object that deterministically derives `pass` only when every frozen gate passes and `fail` otherwise; a caller-selected pass/fail boolean is invalid. `state-machine.json` closes the approval, approval-subject, fixation-state-proof, pass-observation, and verdict-bundle objects and assigns a safe failure kind to every known predicate. `fix_verdict` validates one exact bundle, requires the actor to equal the DSPx broker owner, and atomically create-if-absent appends `execution_journal_id → verdict_digest` in the DSPx global verdict register with the execution-journal fix event. There is no subject-selected verdict-register authority or journal/register crash gap. Credentials, public keys, trust roots, purpose, validity, revocation, caller pins, and complete authority coordinates are explicit inputs and exact joins. Deriving an expected pin from the credential being checked is forbidden.

Contamination coordinates are derived from explicit source preimages or broker-sealed coordinates. A caller-provided digest map is not independent evidence.

`fix_verdict` binds the immutable verdict bytes, pre-verdict execution-trace digest, fresh-at-fixation state proof, and exact approvals. The post-commit verdict-append receipt references the verdict digest but is not nested in the verdict or pre-verdict trace. This unidirectional boundary prevents a verdict/trace/receipt digest cycle. Later current verification uses a renewable verdict-register read proof outside the immutable verdict.

## 5. Publication and currentness

Decision 104 introduces no publication history, owner head, checkpoint, challenge-consumption store, acquisition receipt, currentness proof, consumer adoption, or runtime-use object.

A future semantic release may reference the immutable policy coordinate and qualifying verdict through Decision 53's existing owner publication/currentness machinery. The semantic owner still owns publication/withdrawal/revocation; publication does not authorize adoption or runtime use.

If Decision 53 cannot represent the two references without widening its accepted protocol, a separate narrowly scoped Decision 53 successor is required. Evaluation objects must not duplicate that machinery as a shortcut.

## 6. Authority matrix

| Fact/action | Sole authority |
|---|---|
| ontology meaning, inventory, policy bytes and approval | semantic owner |
| D/U/O custody, reservation, leases, handles, process lifecycle, cleanup | `softwareco/owned/dspx` broker owner |
| canonical execution journal/head and unique verdict-register append | `softwareco/owned/dspx`, gated by exact independent approval |
| deterministic policy/journal/state-proof/verdict verification | `core/rocs-cli` |
| independent verdict judgment/approval | independent reviewer, distinct from custodian/evaluator/semantic owner |
| task/decision/evidence lineage | AK |
| publication/currentness | semantic owner through semantic-release authority |
| adoption/rollback | exact future consumer owner |
| delivery/runtime attestation | future Pi owner |

Joining facts does not transfer issuance authority.

## 7. Failure model and precedence

Closed safe errors are ordered so equivalent hostile inputs classify identically independent of map insertion order:

1. `invalid_input`
2. `resource_exhausted`
3. `state_conflict`
4. `authority_invalid`
5. `signature_invalid`
6. `transition_invalid`
7. `lifecycle_incomplete`
8. `evidence_mismatch`
9. `outcome_invalid`

Validators collect evidence internally but expose only the highest-precedence safe kind and bounded coordinates. Raw object values, paths, keys, environment, broker tokens, and exceptions never enter normal output.

## 8. Resource and implementation boundaries

Each verification has one aggregate budget object across parsing, graph/trace, Git/source inspection, signatures, subprocesses, and output. Shared objects are charged once by content/object identity. Preflight metadata checks precede body reads. Max and max+1 vectors exist for every dimension. The v1 machine fixes the architecture ceilings in `verification_limits`: 4 MiB descriptor projection; depth 64; 256 object keys; 33,000 array items/events; 16 KiB per canonical event; 540,672,000 trace bytes; 64 KiB sealed record and credential; 1 MiB revocation source each; 32 signature checks; zero verifier subprocesses; 64 KiB normal output; and 600 seconds. Allocation max is 16,384; protected-read max is 8,192; at most 64 reads are in flight. The longest successful execution is bounded by `17 + 4×8192 = 32785` committed events. Implementations may choose lower deployment limits but may not raise them without a successor review.

Implementation slices must keep policy parsing, broker runtime, state-machine evaluation, semantic-release integration, and CLI boundaries in separate modules/tasks. No implementation module may exceed 500 lines or require explanation through another authority domain.

## 9. Supersession and migration

If accepted, a superseding ADR shall:

1. retire Decision 103 R2–R4 and its combined graph as implementation authority;
2. preserve Decision 103 history and rejected evidence;
3. assess Decision 103 R0/R1 schema/digest primitives individually for pure-policy reuse rather than inheriting them wholesale;
4. keep all P2–P7 real effects blocked until owner-specific broker and policy decisions exist;
5. require a separately reviewed implementation plan and owner-scoped tasks;
6. keep Decision 98 B0 permanently frozen and prohibited.

## Alternatives rejected

- another refinement of the combined signed proof graph;
- signatures as proof of process/store/descriptor behavior;
- caller-constructible evidence tokens;
- eight hand-maintained branch unions as the behavioral source of truth;
- publication/currentness duplicated inside evaluation;
- retrying the failed transcendent phase without a known lawful recovery checkpoint;
- treating green tests or synthetic fixtures as architecture acceptance.
