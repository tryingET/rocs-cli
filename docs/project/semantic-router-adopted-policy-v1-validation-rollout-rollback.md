---
summary: "Validation, staged rollout, evidence custody, and rollback plan for Decision 103 adopted routing-policy protocol."
read_when:
  - "Planning implementation or any owner/empirical action after Decision 103."
type: "validation_rollout_rollback"
status: "proposed"
decision_id: 103
---
# Validation, rollout, and rollback — adopted semantic-routing policy v1

## Governing posture

Decision 103 is protocol design only. Passing this packet's review does not authorize the phases below. Each phase opens only under a separate scoped task with accepted predecessor evidence.

```text
P0 protocol review
→ P1 offline verifier implementation
→ P2 semantic-owner path/publication implementation
→ P3 fresh custody, role freeze, and U/O seal
→ P4 D disclosure, policy authoring, and candidate freeze
→ P5 exact preregistration against the frozen candidate
→ P6 one-shot U/O execution, verdict, and post-execution approvals
→ P7 owner publication
→ separate consumer decision(s)
```

## P0 — protocol review

Required:

- packet hashes and aggregate exact;
- JSON schema parses and is closed;
- three mandatory review lanes accept;
- synthesis recommends `ready_for_adr`;
- Decision 103 passport is internally consistent;
- no code, policy, dataset, publication, or runtime mutation.

Rollback: replace the proposal with a new packet aggregate; preserve rejected reviews.

## P1 — ROCS offline verifier

Authorized only after accepted ADR and implementation plan. Implement schema embedding, strict I-JSON/JCS, all sixty-one digest domains, acyclic dependency-graph validation, object/invariant/complete-history validation, safe errors, fixtures, independent Node oracle, and explicit-local-file CLI verification.

Gates:

- Python and Node byte agreement;
- malformed, duplicate, noncanonical, over-budget, stale/forked history matrices;
- publish-without-pass, withdrawal, revocation, head/checkpoint fork or regression, identity drift, and proof-age failures;
- forged/redated issuer receipt; wrapper mutation of signed descriptor-anchored-no-follow/closed-environment/no-network/final-recheck assertions; invalid Ed25519 signature/key approval; circular attestation attempt; replayed custodian/reviewer approval across changed verdict outcome/metrics; replayed semantic-owner approval across changed sequence/action/reason/time; self-asserted repository authority; authority-coordinate/enclosing-approval digest cycles; absent, malformed, non-canonical, or mismatched raw Ed25519 issuer or consumption-credential bytes; partial/ambiguous acquisition-channel, single-use-store, or consumption-signing-key approval subjects; ambient-key-registry dependence; stale H1 replay after withdrawal H2; reused/expired/unconsumed challenge; wrong action/candidate/store/channel; untrusted or revoked approval; broken checkpoint chain; and checkpoint-minimum failures;
- inventory-prefix impostor or non-member, mismatched parsed Decision 102 policy/provenance/per-record source owner, closed inventory/extractor receipt drift, policy/joint/selected ID outside inventory, custody-role collision including implementer or D-author conflicts, incomplete/duplicate/unjoined B0 surface coverage or unrelated clean source digest, wrong canonical B0 coordinate, candidate→contamination→envelope back edge or any digest cycle, mismatched downstream execution-contamination attestation, attempt-envelope/environment/reservation/rollback drift or retry/rerun, activation or detached-proof bearer replay, opaque/forged channel exporter, unauthenticated evaluator/gateway, absent crash-safe reservation consumption, protected read before descriptor handoff, backdated grant, missing terminal revoke, expiry overrun, access-history reserve exhaustion, 1 MiB/16 MiB/32 MiB object boundaries, and reserved-terminal-event capacity;
- existing Decision 102 route/discovery compatibility unchanged;
- complete repository gate and reverse rollback rehearsal;
- `live_acquisition_implemented=false` mechanically observable.

Fixtures remain conspicuously synthetic. No real policy or owner path is touched.

## P2 — semantic-owner storage mechanics

Softwareco ontology owner separately accepts exact paths and implements append-only/CAS candidate/publication storage. This phase may use synthetic fixtures only.

Gates:

- owner-local task and review;
- no-follow, atomic, crash-safe append/head update;
- full history reconstruction;
- concurrent writer/fork/checkpoint-regression rejection;
- authenticated monotonic owner checkpoint and authoritative-ref observation;
- preflight reservation for one worst-case terminal withdraw/revoke event before each publish;
- withdraw/revoke, stale-H1 replay, and failed-update rehearsal;
- ROCS verifies but cannot write or approve;
- external recovery preserves prior head and immutable events.

No live publication occurs in P2.

## P3 — fresh custody, role freeze, and U/O seal

Before D disclosure:

1. semantic owner freezes the exact Softwareco source snapshot and canonical `co.software.*` inventory digest;
2. DSPx issues a closed custody policy binding exact source and license/consent authority artifacts, privacy and the complete prohibited-content set, ACL/audit, retention by artifact class, backup handling, verified deletion under every expiry/withdrawal/privacy-exposure trigger, and incident response;
3. the exact canonical role cardinalities are fixed, including one implementer and two distinct annotators; all twelve principals are pairwise distinct and all authority roles, nested exposure evidence, append-only base access history, custody ACL, and the closed role-separation receipt reconcile; the base history contains at most 254 events, reserving one event for activation and one for mandatory closure, and grants no sealed U/O read or evaluator-process start to the evaluator operator; all U/O authors, annotators, adjudicator, custodian, evaluator operator, and independent reviewer prove B0 exposure `disproven`;
4. B0-unexposed U/O authors create and seal U=600 and O=96 before D disclosure;
5. independent annotators/adjudicator complete readiness;
6. D authors independently create D=360 and freeze its digest without disclosing it to the policy author;
7. emit one custodian-signed, domain-digested custody-readiness subject/receipt binding custody policy, role/access history, inventory, sealed D digest, U/O seals, and pre-disclosure readiness—without policy/provenance, candidate, preregistration, execution, metrics, outcome, or verdict fields—and validate it against a separately supplied caller verification request that pins the custodian authority, credential, approval, trust root, and raw public key.

P3 cannot name policy/provenance bytes, a candidate, attempt envelope, execution attempt, metrics, outcome, verdict-approval subject, or verdict approval. Raw U/O stays outside Git/AK/ROCS/Pi. The controller receives only the signed readiness object including the exact base-history preimage (at most 254 events), independent caller pins, and digests. D disclosure and policy authoring remain prohibited until that authority verifies.

Stop permanently for the affected set on leakage, B0 derivation, role conflict, unlicensed/private content, annotation unreadiness, digest drift, or custody uncertainty.

## P4 — D disclosure, visible policy authoring, and candidate freeze

Only after accepted P3 evidence may policy authors receive D. They use only the frozen Softwareco ontology sources and D. Every clause alternative has exact owner provenance and contamination review. Selected IDs remain Softwareco-owned.

Gates:

- D behavior and operational dry-runs under the P1 verifier;
- candidate contamination manifest freezes the exact ten pre-attempt no-reuse surfaces and contains no candidate or attempt-envelope digest;
- policy/provenance/candidate digest freeze;
- no U/O access;
- independent semantic-owner review;
- rollback by a new candidate before U/O execution, never by rewriting D or candidate history.

D results are development evidence only.

## P5 — exact preregistration

After candidate freeze and before any U/O observation:

1. acquire one custodian-issued, non-executing, expiring single-invocation reservation; it grants no sealed-row read or process-start authority and is released or expires unused on any later validation failure;
2. construct the one-attempt envelope over the exact candidate, evaluator/runtime, U/O seals, argv/environment, pass order, that reservation, and rollback plan;
3. issue the downstream execution-contamination subject/attestation binding the candidate-contamination manifest, candidate, evaluator, and attempt-envelope digests; its `source_digest` equals the envelope digest, it cannot flow back into candidate identity, and custodian plus independent reviewer sign it under exact credentials;
4. validate a separately supplied execution-contamination verification request that pins both authorities, credentials, stage-specific approvals, trust roots, keys, subject, and attestation;
5. construct a closed preexecution-verification bundle that nests both complete caller-request preimages and exact request digests, then preregister the candidate, both contamination objects, custody/roles/base-access history, D/U/O digests, evaluator, metrics/floors, exact frozen custodian/reviewer authority coordinates, bundle, attempt envelope, and reservation;
6. after every signature, request preimage, preregistration, authority, reservation, and equality join validates, obtain one custodian-signed protected-access activation bound to that preregistration, the unchanged P3 base history, exact frozen evaluator operator, U/O seals, reservation, permissions, and expiry; its signed subject binds the activated-history and exact grant-event digests; its activated history is exactly the base history plus one terminal grant to that evaluator operator at `grant.occurred_at == subject.issued_at`, and remains at most 255 events;
7. verify the published topological dependency schedule has no back edge or cycle.

P5 acquires the non-executing reservation first, then mechanically validates the preregistration, both signed pre-execution authority objects, both complete nested independent verification-request preimages, and exact reservation/envelope joins before issuing the protected-access activation. An opaque request digest is invalid. The P3 signature approves only its candidate-free readiness subject; the P5 signatures approve only the exact execution-contamination subject. None approves future execution outcome or preregistration bytes. Reservation acquisition is coordination only and cannot read U/O or invoke the evaluator. P3 role eligibility and its base history confer no active evaluator access; only the downstream signed activation appends the sole time-bound grant, and its issuer must equal the frozen custodian while its executor must equal the frozen evaluator-operator assignment. The activation is not a bearer token and cannot itself prove who starts the process. P5 must not construct or sign a verdict-approval subject. Execution attempt, receipt, metrics, outcome, custodian verdict approval, and independent verdict approval do not yet exist.

## P6 — one-shot U/O execution, verdict, and post-execution approvals

Before process start, construct in strict order the complete authenticated-channel coordinate, a fresh evaluator challenge over that coordinate, the unsigned prospective start subject, and an independent request pinning the subject, frozen evaluator/gateway authorities, both credentials/raw keys/trust roots, allowlisted exporter algorithm/context/digest, exact activation/reservation/envelope/preregistration, process ID, and prospective deadline. The evaluator then signs that subject. On the same live channel, the pinned gateway recomputes the exporter and crash-safely records/signs reservation consumption `0 → 1` with protected handles closed before spawning. Activation or a detached signature is never a bearer token. At first U/O access, the gateway atomically records/signs a revocable-handle handoff with direct OS descriptor transfer forbidden and per-read gateway authorization mandatory; no row read is possible before that receipt.

Under that verified evaluator proof, crash-safe gateway authorization, optional/required descriptor-handoff receipt by attempt state, and current activation, at most one reserved process invocation starts for the immutable P5 preregistration against sealed U/O and frozen candidate. The custodian authorizes but remains a distinct principal from the executor. A completed invocation performs exactly two ordered internal passes, `primary` and `immediate_repeat`, over identical inputs and records both digests. A not-started attempt truthfully records zero invocations/passes; an interrupted attempt records one invocation and at most one completed pass. Both are `indeterminate`. No retry, second invocation, selective rerun, extra pass, or same-candidate repair is permitted. Policy authors/implementers receive no row outputs before immutable verdict publication.

Immediately after the raw execution receipt is fixed—or on failure, abort, indeterminate termination, or expiry—the custodian signs the protected-access closure. The closure appends exactly one terminal revoke after the activation grant and binds the exact truthful prefix. A no-start prefix may retain proof/request and the crash-safe pre-spawn launch receipt if those facts exist, but always has zero invocations, null spawn/termination/handoff/raw-receipt fields, and `never_handed_off`. A started prefix binds the custodian-observed spawn time, proves it met every reservation/challenge/channel/authorization/gateway deadline, and ends with process termination/reaping; a handed-off gateway handle must additionally be revoked/closed, with every later read rejected. It closes no later than activation expiry except for an explicit `expired` closure. No metrics, verdict subject, or verdict may be finalized until terminal history, exact branch, signer, times, process/handle termination, capacity reserve, and closure digest validate. A missing closure, terminal grant, retained process, or retained protected handle is indeterminate and stops without retry. Any `expired` or late closure forces `indeterminate` and is not publishable.

After the execution receipt, metrics, and outcome are fixed, construct the non-circular verdict-approval subject. Only then may the custodian and distinct independent reviewer sign that exact subject. No pre-execution signature may cover a post-execution value.

Evidence-validity precedence:

1. integrity/execution invalidity → `indeterminate`, stop without retry;
2. otherwise any frozen gate failure → `fail`, stop without same-candidate change;
3. otherwise all gates and independent review pass → `pass`.

Required safety/utility floors are those in Decision 102's accepted validation contract: zero false routes on 300 U null rows, zero unexpected U errors, exact O oracles, point and Wilson precision floors, at least 80% overall applicable correct-route coverage, per-stratum and holdout floors, and byte-identical repeat. Report full-precision gates and aggregate confusion matrices. A pass requires independent custody and verdict review.

A failed policy may produce a new candidate only under a new task and fresh acceptance set when required by exposure rules. The failed report remains immutable.

## P7 — semantic-owner publication

Only a reviewed `pass` verdict and a closed signed semantic-owner approval artifact whose non-circular subject binds exact owner authority, sequence, predecessor, action, candidate, verdict, reason, and time—and whose issuer/subject/purpose/validity/non-revocation/trust-root/key/signature all validate against external caller pins—permit the owner to append `publish`. Publication captures a fresh owner commit/tree, terminal head, and authenticated monotonic owner-store checkpoint and unidirectional checkpoint chain committing the head without a head/checkpoint digest cycle. Before append it reserves event and byte capacity for a terminal withdraw/revoke. ROCS independently validates complete history and only synthetic local proof shapes until live issuer/channel/challenge acquisition is separately implemented. Publication evidence does not create consumer adoption.

Withdrawal/revocation rehearsal occurs before first publish. A live owner capability remains blocked until separately implemented and reviewed; explicit local owner files may support an offline publication rehearsal but not production currentness claims.

## Consumer gates (outside Decision 103)

After P7, separate exact-consumer decisions may authorize:

### C1 no-injection shadow

- clean current owner branches and installed artifacts;
- explicit consumer consent and opt-in;
- command-only or deterministic faux-provider harness first;
- observe route/currentness and record suppression without changing prompt content;
- no added provider/model request;
- exact disable rollback and live reload proof.

### C2 prompt-projection canary

Only after C1 acceptance and recovery rehearsal. Requires separate prompt-custody, provider, cost, retry, compaction, and delivery evidence. One named canary; default off.

### C3 automatic preflight

Last and separately decided. Requires accepted semantic quality, publication currentness, consumer benefit/safety evidence, independent recovery controller, action-time owner proof, provider/model authorization, and tested startup/default rollback. A single canary cannot imply fleet rollout.

## Dogfood meanings

| Dogfood | Lawful claim |
|---|---|
| P1 synthetic verifier | protocol implementation works on synthetic fixtures |
| P2 owner-storage rehearsal | append/head/rollback mechanics work on synthetic owner data |
| P4 D run/candidate freeze | visible development policy behavior and candidate identity only |
| P5 preregistration/access rehearsal | acyclic caller-pin preimages and signed, no-read-before-validation access activation only |
| P6 U/O | authenticated evaluator start, one frozen offline acceptance attempt, mandatory access closure, and verdict only |
| P7 publication rehearsal | owner publication/currentness mechanics only |
| C1 faux-provider shadow | operational no-injection integration only |
| C2 canary | bounded delivery/behavior under named authorization |
| C3 automatic | only the exact accepted activation scope |

No dogfood level may claim a later evidence dimension.

## Global stop conditions

Stop on an unauthenticated executor, activation bearer replay, missing/late protected-access closure, terminal evaluator grant, exhausted access-history reserve, protected Decision 102 drift, B0 reuse or incomplete contamination coverage, cross-owner meaning or inventory non-member, missing custody policy, role conflict, U/O exposure, extra invocation/pass/retry/rerun, unreviewed floor change, malformed or incomplete verdict, non-pass publication, stale/forked owner head or checkpoint, replayed/redated/untrusted receipt, exhausted rollback reserve, network or provider/model surprise, dirty owner worktree used as authority, missing recovery owner, consumer substitution, automatic enablement, or restoration uncertainty.

## Evidence retention

Preserve rejected packets, failed/indeterminate reports, immutable owner events, rollback receipts, and independent reviews. Session logs and intercom are not owner authority. AK stores links/digests, never raw protected data or synthesized owner facts.
