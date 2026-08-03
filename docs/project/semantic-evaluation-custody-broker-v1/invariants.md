---
summary: "Normative invariants and threat model for the separated semantic policy, custody broker, and canonical evaluation state machine."
read_when:
  - "Implementing or reviewing Decision 104 contracts."
type: "specification"
status: "proposed"
decision_id: 104
---
# Semantic evaluation custody broker v1 — invariants and threat model

## Normative source

`state-machine.json` is the sole behavioral transition authority. This file defines cross-boundary invariants and threat responses. If prose implies an additional transition, the prose is invalid.

## Policy invariants

1. Policy coordinates are immutable and semantic-owner issued.
2. Policy bytes contain no custody, process, lease, handle, execution, verdict, publication/currentness, consumer, or runtime state.
3. Inventory membership and source retention are verified from explicit local preimages; prefix form or a digest string alone is not ownership evidence.
4. Correcting any policy-coordinate byte creates a new identifier and digest.
5. Policy approval grants no broker capability.

## Broker invariants

1. `softwareco/owned/dspx` owns the broker store, canonical execution journal/head, protected store, and unique verdict register.
2. The canonical journal/store head—not receipts—is authoritative for mutable custody/execution state.
3. Every committed operation is one linearizable append/CAS over an expected generation and increments generation once; conflict changes nothing.
4. A transition ID is bound to the complete authenticated request digest, actor/channel, command, parameters, and expected generation. Equal replay returns the prior result; unequal reuse rejects without disclosing it.
5. One reservation can commit at most one `start_commit` operation.
6. The broker precreates one empty crash-stable containment, records `start_commit`, and then permits exactly one durable `claim_spawn_intent` CAS before one spawn syscall. A claimed intent is never retried after crash. Recovery records one stable observed identity or empties the containment; ambiguity cannot close or fix a verdict.
7. A protected handle is opaque, lease-/process-/clock-epoch-bound, non-serializable, and checked on every read.
8. Independent global config pins DSPx owner/store, empty sparse-Merkle root, and ceilings. One `allocate_and_seal_execution_journal` transaction validates two exact depth-256 updates—derived journal→sealed-subject and stable attempt-identity→journal—and atomically writes all reachable nodes, both roots, the immutable sealed record, generation-zero execution journal, replay index, sequence, and generation. The record nests no receipt or current head. Descriptor-anchored binding joins independent owner/store/anchor pins and generates both current memberships from one persistent-node snapshot. A later allocation renews only those read-time witnesses, never the record or initial state. Every read ID uses its separately fixed hex domain, length-framed store/journal IDs, and uint64-big-endian increasing sequence; admission creates one durable spool slot and permits at most one protected-store read. Acknowledgement requires the live evaluator actor and live authenticated channel to equal the stored actor/channel and persisted acknowledgement fields; owner cancellation requires null acknowledgement fields. Either terminal transition moves the ID permanently to consumed; retries expose only the same spool bytes/marker. Revocation/expiry closes admission; `closed` requires the in-flight set empty and no readable spool.
9. A started process is terminated and reaped before `closed`.
10. Every opened handle is revoked and closed before `closed`.
11. `closed` is monotonic; no reservation, lease, handle, read, or process state can reopen.
12. Receipts are emitted only after commit and identify the committed generation/transition; signatures do not replace state.
13. Verdict fixation requires explicit local canonical-journal bytes and a fresh challenge-bound fixation state proof equal to the recomputed head/trace/snapshot; receipt signatures alone are insufficient. Later action-time verification uses a renewable verdict-register inclusion/head proof outside the verdict.
14. Broker authentication binds actual live actor/channel/key possession and stable process/supervisor identity to complete caller-pinned authority material; declared actor, UID, PID, or principal text is insufficient.
15. The broker-created immutable sealed record recomputes exact attempt identity, subject, and record digests. Initial binding derives that exact record plus current head/memberships from one bounded trusted-descriptor snapshot, joins independently supplied owner/store/anchor pins, then uses only `initial_state_projection`; no flat alias is lawful and no expected pin may be derived from an object under validation. `reserve` and `authorize` may add reservation/lease bounds but compare every overlapping request field to the sealed values; they cannot replace them.
16. Every operation joins its authenticated actor or broker/supervisor/I/O observation authority and exact reservation/channel/process/lease/handle/seal/read values to stored fields as applicable. Authentication without operation-specific equality/role guards is not authorization.
17. Reservation epoch/deadline is checked by authorization. Lease monotonic deadline, authenticated UTC bound, and epoch are checked by authorization, start, read, execution-receipt, and pass-progress operations, so an expiry CAS race cannot advance work. While `authorized` or `started`, either clock failure or independent broker-owner/gateway revocation terminalizes the lease, closes admission, and permits owner cleanup without gateway cooperation.
18. Global journal hard max is 16,384; protected-read max is 8,192; in-flight max is 64; event/generation max is 33,000. Each allocation and read-spool transition verifies constant-depth 256-sibling updates. The longest successful path uses `17 + 4×8192 = 32785` events. Exact max is legal; max+1 returns `resource_exhausted` before any root/sequence/generation/set/spool effect.
19. Every operation uses the closed envelope and transaction protocol before its table guards: live actor/channel derivation, exact transition lookup, expected-generation comparison, fixed failure selection, one atomic delta event/effect commit, one generation increment, and post-commit receipt persistence.
20. Canonical events contain changed-field deltas plus prior/new state digests, not copied prior/new read sets. The terminal read index is enumerated at most once, so trace size is linear in operation count.
21. `fix_verdict` validates closed approval, authority-preimage, approval-subject, fixation-proof, frozen-gate, and verdict-bundle contracts. The subject binds exact receipts, contamination, aggregates, metrics, and gates; branch 8 pass/fail is derived, never caller-selected. The operation atomically commits the execution-journal fix plus create-if-absent DSPx register entry under the broker owner; the sealed subject cannot select a register authority.

## Evaluation invariants

1. The full state vector begins at `initial_state` and follows only contract operations, guards, and effects with generations increasing by one.
2. Every path resolves to `closed` before `verdict_fixed`; unresolved supervisor ambiguity has no transition to either state.
3. Exactly one of the eight branch predicates matches.
4. Invocation count is zero for `not_started`, one for `started`; retry, rerun, extra pass, repair, or branch escalation rejects.
5. Once `terminal_reason` is non-null, no handle, read, execution-receipt, or pass-progress operation is legal; only lease/read/process/handle cleanup may advance.
6. Completed passes are exactly 0, 1, or ordered 2 as defined by the matching branch.
7. Branches 1–7 are `indeterminate`; branch 8 alone may be `pass | fail`.
8. The outer verdict and signed approval subject are field-for-field equal across all approval-relevant coordinates and outcome.
9. Custodian and independent reviewer are distinct from each other, evaluator, and semantic owner.
10. Credential, key, trust-root, purpose, validity, revocation, authority coordinate, and caller-pin joins are complete and externally supplied.
11. Contamination claims are derived from explicit preimages or broker-sealed coordinates, never a caller assertion map.
12. Error selection follows the contract's fixed precedence and never mapping insertion order.
13. The verdict's execution-trace digest ends at `closed` and excludes `fix_verdict`; the verdict-append receipt is post-commit and outside both verdict and execution trace.
14. The broker owner appends one verdict only after exact custodian and distinct independent-review approvals; ROCS verifies but cannot append, judge, or rewrite.

## Publication/currentness invariants

1. Evaluation produces no publication/currentness state.
2. Semantic-owner publication/withdrawal/revocation uses a separately accepted semantic-release authority surface.
3. Publication references immutable policy/verdict coordinates; it cannot rewrite them.
4. Publication does not authorize consumer adoption or runtime use.
5. No Decision 104 artifact changes `live_acquisition_implemented=false`.

## Threat matrix

| Threat | Required defense | Required negative proof |
|---|---|---|
| forged support/evidence token | re-derive authority from explicit preimages and broker state; no public constructor as proof | caller-constructed lookalike rejects |
| double start / retry | consumed reservation, precreated containment, one durable spawn-intent claim, no retry after claim | concurrent start/claim attempts yield one commit; crash recovery observes one process or empties containment without a second spawn |
| transition-ID collision/replay | ID binds complete authenticated request; equal replay only | unequal actor/request/generation reuse rejects without receipt disclosure |
| stale or forked history | expected generation, explicit local journal bytes, canonical head, and fresh challenge-bound state proof | old receipt or rolled-back/forked/missing journal entry rejects |
| actor substitution | live-channel authentication plus operation-specific joins to stored actor/channel/process/lease/handle/seal pins | authenticated wrong actor or same signature with changed repo/commit/tree/principal/role/key rejects |
| global allocator self-pinning | global config pins DSPx owner/store; actor and request must equal both; claim binds one sealed subject | authenticated stranger naming itself, wrong store, duplicate claim, or different sealed subject rejects |
| repeated/selectively changed attempt | stable attempt identity excludes session/channel/resource variation and has one sparse-map claim | changing gateway/channel/maxima cannot allocate another journal for same policy/evaluator/dataset/plan |
| allocation/seal substitution | atomic broker-created record plus descriptor-derived current memberships and independent owner/store/anchor pins | caller-created record, self-pinned store, wrong descriptor, absent claim, malformed path, or later-root substitution rejects |
| sealed-coordinate substitution | explicit sealed-input digest initializes immutable evaluator/gateway/channel/process/seal fields | later well-formed authorization cannot replace any sealed coordinate |
| signed false behavior | receipt accepted only against matching committed broker transition | valid signature without state entry rejects |
| descriptor/handle leakage | opaque per-read broker handle, no raw descriptor transfer | serialized/copied/expired/revoked handle cannot read |
| allocation/read interleaving | atomic allocation+sealed record, renewable read-time memberships, exact read framing, and durable one-read spool slots | later allocation cannot change an earlier initial state; duplicate allocation/read, second protected-store read, cross-channel finish, and readable spool after `closed` reject |
| crash window | closed transaction protocol, exact-envelope replay, spawn claim/containment, durable read spool, atomic verdict register append | fault injection at every boundary never permits re-execution, second spawn/read, partial verdict, or live post-close access |
| spawn ambiguity / PID reuse | crash-stable supervisor identity and explicit committed/observed/failed operations | ambiguous or recycled identity cannot close or fix verdict |
| false cleanup observation | termination/reap operations require supervisor observations equal to stored process identity/request | canonical journal cannot mark a live/unrelated process reaped |
| incomplete cleanup | close guard requires reaping, handle closure, denied reads | verdict fixation rejects every retained process/handle/lease |
| compromised/unavailable gateway | separate broker-owner revocation/cleanup operations | owner can terminalize lease and close without gateway cooperation |
| approval replay | exact subject/outcome/coordinate join | changed outer verdict with old approval rejects |
| verdict/trace digest cycle | pre-verdict trace ends at closed; append receipt is outside verdict | including fix event/receipt in verdict preimage rejects |
| stale immutable fixation proof | fixation proof is historical; later current check uses renewable external register proof | publication/action-time check cannot demand a new digest inside immutable verdict |
| split expiry clocks / CAS race | authorization and every pre-terminal progress operation check applicable reservation/lease monotonic, UTC, and epoch bounds; authorized/started expiry operations terminalize lease | racing expiry cannot authorize, start, record receipt/pass, or admit read after any bound fails |
| contamination self-assertion | explicit source or broker-seal derivation | invented digest coordinate rejects |
| hostile input escape | total pre-validation and closed safe errors | malformed map/list/path/encoding never raises raw exception |
| resource amplification | 4 MiB descriptor projection; 16,384 journals; 8,192 reads; 64 in flight; 33,000 events; fixed-depth claim/spool paths; delta-only events; pre-effect `resource_exhausted` | allocation/binding/spool work is fixed-depth; trace is linear rather than copied-state quadratic; exact maxima pass and max+1 has no partial effect |
| representation drift | generated/checksummed vectors from one state table | schema/Python/Node/fixture transition-set mismatch fails gate |
| publication duplication | reuse semantic-release machinery | evaluation packet containing owner-history/currentness objects rejects |

## Resource posture

Each implementation plan must name exact byte, object, transition, signature, subprocess, output, and deadline ceilings. One verification budget is shared across all sub-operations. Deduplicated work is charged once; no ceiling is per-branch or per-join unless explicitly justified and reviewed.

## B0 prohibition

Decision 98 B0 prompts, labels, corpus, evaluator, outputs, rows, scenarios, templates, aliases, scores, floors, and acceptance coordinates remain prohibited as policy, D/U/O, evaluator, fixture, regression, or execution sources. No successor decision may reinterpret, relabel, tune, rerun, or rehabilitate them.
