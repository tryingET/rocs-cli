---
summary: "Normative invariants for Softwareco routing-policy release, verdict, publication, and currentness objects."
read_when:
  - "Implementing or independently validating Decision 103 protocol objects."
type: "specification"
status: "proposed"
decision_id: 103
---
# Adopted semantic-routing policy v1 invariants

## 1. Scope

These invariants govern protocol objects defined by `protocol.schema.json`. They do not authorize policy authoring, evaluation, publication, acquisition, consumer adoption, or runtime use.

The first policy owner is exactly:

```text
owner_company = softwareco
owner_repository_id = softwareco/ontology
jurisdiction = softwareco-owned ontology IDs only
```

Core ontology references remain dependencies. No core-owned ontology ID may appear in `selectable_ontology_ids` in v1.

## 2. Canonical data

All protocol objects are UTF-8 I-JSON with duplicate keys rejected, integer values only where the schema declares integers, and no byte-order mark. Canonical bytes use RFC 8785 JCS. Every digest string is lowercase `sha256:` plus 64 hexadecimal digits.

Arrays declared `sorted-set` below are duplicate-free and sorted by UTF-8 bytes of their JCS scalar or tuple key. Validators reject rather than repair non-canonical input.

## 3. Digest domains

For canonical object bytes `J` excluding the object's own digest member:

```text
candidate_digest = SHA256("rocs-semantic-policy-candidate-v1\0" || J)
verdict_digest = SHA256("rocs-semantic-policy-verdict-v1\0" || J)
publication_event_digest = SHA256("rocs-semantic-policy-publication-event-v1\0" || J)
publication_history_digest = SHA256("rocs-semantic-policy-publication-history-v1\0" || J)
owner_head_digest = SHA256("rocs-semantic-policy-owner-head-v1\0" || J)
read_receipt_digest = SHA256("rocs-semantic-policy-owner-read-receipt-v1\0" || J)
currentness_proof_digest = SHA256("rocs-semantic-policy-currentness-v1\0" || J)
custody_policy_digest = SHA256("rocs-semantic-policy-custody-policy-v1\0" || J)
contamination_manifest_digest = SHA256("rocs-semantic-policy-contamination-v1\0" || J)
preregistration_digest = SHA256("rocs-semantic-policy-preregistration-v1\0" || J)
execution_attempt_digest = SHA256("rocs-semantic-policy-execution-attempt-v1\0" || J)
approval_artifact_digest = SHA256("rocs-semantic-policy-approval-artifact-v1\0" || J)
issuer_trust_digest = SHA256("rocs-semantic-policy-issuer-trust-v1\0" || J)
caller_challenge_digest = SHA256("rocs-semantic-policy-caller-challenge-v1\0" || J)
owner_checkpoint_digest = SHA256("rocs-semantic-policy-owner-checkpoint-v1\0" || J)
```

No digest is interchangeable with Decision 102 route, discovery, policy, provenance, or result digests.

## 4. Candidate release

A candidate release binds exactly:

- owner company and repository ID;
- owner Git commit and tree;
- root-relative policy and provenance paths;
- Decision 102 policy and provenance digests;
- route protocol/schema/algorithm coordinates;
- frozen ontology snapshot digest;
- exact root-relative Softwareco inventory path and inventory digest at that snapshot;
- sorted Softwareco-owned selectable IDs using their canonical `co.software.*` identifiers;
- independent contamination-manifest digest;
- candidate digest.

Every selectable ID must be a member of the exact frozen inventory object. The `co.software.*` lexical form is necessary but never sufficient authority. Prefix inference, an absent inventory member, a `core.*` ID, or a relabeled/copied core meaning is invalid.

The owner commit must contain the exact policy/provenance/source bytes named by provenance. A candidate is immutable. Correcting any byte creates a new candidate ID and digest.

Candidate paths are canonical root-relative POSIX paths: no absolute path, empty segment, `.`, `..`, backslash, NUL, symlink traversal, or alias. Later capture inherits Decision 102's descriptor and Git object-database safety requirements.

## 5. Evaluation custody, preregistration, and verdict

A closed custody policy is issued by the named custodian and binds its authenticated principal coordinate, lawful source basis, privacy class, prohibited-content set, ACLs, audit log, retention periods by artifact class, backup controls, deletion triggers and verification, exposure retirement, and incident-response reference. Dataset creation cannot begin until that policy is approved and digest-fixed.

A closed contamination manifest names the immutable Decision 98 deny coordinates exactly: preregistration commit, failed-run commit, lock digest, prompt-set digest, and report digest. Its coverage is exactly policy, D, U, O, evaluator, fixtures, floors, templates, aliases, regression inputs, and execution coordinate. Every coverage row binds source bytes, deterministic overlap receipt, independent derivation review, and `no_reuse`. Opaque or incomplete coverage is invalid.

A preregistration binds the custody and contamination digests, frozen inventory and dataset seals, evaluator, floors, one-attempt envelope, custodian acceptance, and authenticated role assignments. Every role assignment binds principal/repository/commit/tree/artifact coordinates, exact role, access rights, timestamp, and B0 exposure evidence. U/O authors, annotators, adjudicator, custodian, evaluator operator, and independent verdict reviewer must be B0 exposure `disproven`; policy and D authors may be exposed but may never receive sealed U/O access.

Role separation is mechanical: the custodian principal differs from the independent reviewer; policy author differs from U author, O author, annotators, adjudicator, custodian, evaluator operator, and independent reviewer; U/O authors differ from implementers and policy authors; annotators differ from each other, authors, policy authors, evaluator operator, and adjudicator; the adjudicator differs from all authors/annotators/policy authors; no principal receives both policy bytes and sealed U/O rows before verdict fixation. Repository difference alone is insufficient.

One immutable attempt envelope permits exactly one process invocation. That invocation performs exactly two ordered internal passes—`primary`, then `immediate_repeat`—over the same candidate, preregistration, sealed rows, and execution coordinate. Their input-coordinate, row-receipt, and result-byte digests must be equal as required by the determinism oracle. Process retry, selective row rerun, additional pass, same-candidate repair, or a second invocation after observation is forbidden and maps through the frozen outcome precedence.

A verdict nests and binds the exact custody policy, preregistration, contamination manifest, and execution attempt plus evaluator commit/tree/tool digest, D/U/O dataset digests, execution receipt digest, metrics digest, outcome, and exact authority coordinates for both custodian approval and independent verdict review. Every nested digest equals the corresponding verdict field. Each authority coordinate binds authenticated principal ID, role, repository ID, Git commit/tree, and approval/review artifact digest. The custodian is exactly `softwareco/owned/dspx` unless a pre-data reviewed packet revision names another owner. Custodian and independent-review principals must differ from each other, the policy owner, policy authors, and evaluator operator; a self-issued approval is invalid.

`outcome` is exactly `pass | fail | indeterminate`. Precedence is:

1. evidence-integrity or execution-validity defect → `indeterminate`;
2. otherwise any semantic, utility, operational, compatibility, or review gate failure → `fail`;
3. otherwise every frozen gate and independent review passes → `pass`.

Only `pass` may be referenced by a `publish` event. A later discovery of leakage or integrity loss requires an owner `revoke` event; the old verdict is not rewritten.

Raw U/O prompts, labels, and row outputs are not protocol members and must not enter ROCS, Git, Pi, session summaries, or AK. Only digests, role/custody receipts, and aggregate verdicts may cross the custodian boundary.

## 6. Publication event chain

An owner publication history is one closed `semantic-routing-policy-publication-history.v1` object encoded as RFC 8785 JCS. It contains `owner`, a non-empty `events` array in ascending sequence order, and `history_digest`. The history digest uses its separate domain over the object without `history_digest`; no JSONL, concatenated-record, mutable-index, or filesystem enumeration is normative.

Every event binds:

- owner and namespace;
- monotonically increasing positive `sequence`;
- `previous_event_digest` (`null` only at sequence 1);
- action `publish | withdraw | revoke`;
- candidate and verdict digests;
- owner approval reference;
- reason code;
- issued-at UTC instant;
- event digest.

For sequence `n > 1`, `previous_event_digest` equals the digest of sequence `n-1`. The candidate digest is stable across a withdrawal/revocation event targeting that publication. `publish` requires a pass verdict. `withdraw` is a reversible lifecycle choice only through a new publish event. `revoke` marks the target unsafe; republishing the same candidate digest is forbidden. A `publish` event may use at most sequence 9,999, reserving sequence 10,000 for a terminal `withdraw` or `revoke`; owner storage must also preflight byte capacity for that reserved event before accepting a publish.

There is no mutable `latest` release. The only mutable owner-store pointer is an authenticated compare-and-swap checkpoint on one owner-issued authoritative ref. Each checkpoint names the exact head, complete history, owner commit/tree, monotonically increasing checkpoint sequence, and predecessor checkpoint digest. History is authoritative only when every supplied event verifies, the history digest verifies, and the authenticated current checkpoint matches that same complete history and terminal event.

Concurrent fork, sequence gap, predecessor mismatch, missing event, duplicate sequence, checkpoint fork/regression, a history longer than the checkpoint, or insufficient reserved append bytes is `invalid_owner_history`. An old otherwise-valid publish head H1 is not current after authenticated checkpoint H2 records withdrawal or revocation.

## 7. Owner head, trust bundle, challenge, and local read receipt

An owner head binds owner, namespace, terminal sequence/digest, owner repository commit/tree, publication-history path/digest, owner-store ID, authoritative ref, monotonic checkpoint sequence/digest, and head digest. Its `publication_history_digest` equals the nested history object's digest; its checkpoint values equal the authenticated owner checkpoint.

Approval artifacts are closed objects, not opaque references. Each binds authenticated issuer coordinate, subject digest, purpose, validity interval, non-revocation state, and artifact digest. An issuer-trust bundle binds the expected issuer, trust root, and exact acquisition-capability, clock-source, and owner-channel approval objects.

Before every read, the caller creates a fresh, single-use challenge binding candidate digest, intended action, owner-store ID, authoritative ref, prior/minimum checkpoint, issuance/expiry, and challenge digest. The acquisition capability must echo that exact challenge in its issuer-attested receipt. Reuse across candidate, action, store, checkpoint, or expiry is invalid.

A bounded read receipt binds:

- the complete issuer-trust bundle and authenticated issuer attestation;
- the exact fresh caller challenge and its intended action;
- caller-pinned acquisition capability ID, Git commit/tree, and closed approval artifact;
- exact owner repository, owner-store, authoritative-ref, and trusted-channel identities;
- authenticated monotonic owner checkpoint and predecessor relation;
- no-follow local capture identity;
- observed commit/tree and exact head/history bytes and digests;
- UTC `capture_started_at` and `capture_finished_at`, exact clock-source approval, and bounded uncertainty;
- closed environment, no-network assertion, and stable final recheck;
- the separate read-receipt digest.

A digest alone does not authenticate a redated receipt. A verifier accepts only an issuer-attested receipt whose trust root, closed approvals, challenge, expected receipt digest, channel/store identity, checkpoint, and issuer coordinate exactly equal caller-pinned values. Recomputing timestamps or the receipt digest without the trusted issuer attestation fails. `capture_finished_at` must be no earlier than `capture_started_at`; challenge expiry, replay, clock rollback, excessive uncertainty, or an untrusted source fails closed.

Decision 103 defines these shapes, not a live acquisition capability or trust root. Until a later owner task implements and independently verifies the issuer, channel, monotonic checkpoint, single-use challenge store, and acquisition capability, currentness cannot pass.

## 8. Action-time currentness proof

A currentness proof binds candidate, pass verdict, the complete publication history, owner head, authenticated owner checkpoint, caller challenge, issuer-trust bundle, and read receipt. `observed_at` must byte-equal the receipt's `capture_finished_at`; it is not an independently chosen timestamp. It is valid only when:

1. all schemas and all fifteen digest domains validate;
2. candidate digest equals verdict candidate, attempt candidate, publication-event candidate, challenge candidate, and proof candidate;
3. verdict digest equals the terminal event verdict; verdict candidate/inventory/contamination/custody/preregistration/attempt fields equal their nested object digests;
4. owner/repository/namespace values equal candidate, every event, history, head, checkpoint, receipt, trust bundle, and proof;
5. candidate owner commit/tree equal the bytes verified from its policy/provenance/inventory paths; head/checkpoint/receipt observed commit/tree equal each other and the authenticated authoritative-ref observation;
6. every event and complete history digest verify; history digest equals head, checkpoint, receipt, and proof history values;
7. terminal event sequence/digest equals history terminal, head terminal, and checkpoint head; checkpoint sequence/digest equals receipt and the proof's expected checkpoint and is not below caller minimum;
8. checkpoint predecessor relation extends the caller-pinned prior checkpoint, and the authenticated capability proves it read the current owner-store ref rather than caller-supplied old bytes;
9. terminal action is `publish` and no later withdrawal/revocation exists under the authenticated current checkpoint;
10. issuer trust, approval subjects/purposes/validity/non-revocation, challenge, intended action, expected receipt digest, channel/store identity, and issuer attestation equal caller pins;
11. capture identity remained stable through final recheck;
12. proof age is positive, bounded, and measured from issuer-attested `capture_finished_at` against the trusted current clock; uncertainty is within the caller pin;
13. challenge was unused, unexpired, and consumed for exactly this receipt/action;
14. the consumer obtains this fresh capture immediately before its separately authorized action.

Clock uncertainty, stale cache, missing capability, owner mismatch, withdrawn/revoked terminal state, or changed snapshot is an error, never abstention.

## 9. Authority non-transfer

- Semantic owner issues candidate approval and publication events.
- DSPx or another named independent custodian issues the sealed evaluation verdict.
- ROCS validates objects and bytes.
- AK links decision/task/evidence identifiers.
- A future consumer owner independently adopts and activates.
- Pi may later attest bounded delivery.

No participant may synthesize another owner's missing fact. Joining valid facts does not transfer issuance authority.

## 10. Resource bounds

Protocol parsers enforce before trusted allocation:

| Resource | Maximum |
|---|---:|
| one non-history JSON object | 1,048,576 bytes |
| one complete publication-history object | 16,777,216 bytes |
| publication events | 10,000; publish at most 9,999 |
| selectable IDs | 2,000 |
| path bytes | 1,024 |
| string bytes | 65,536 |
| collection items | 50,000 |
| parser depth | 32 |
| participants | 64 |
| contamination coverage rows | 11 |
| attempt process invocations | exactly 1 |
| internal attempt passes | exactly 2 |

The history object is the sole 1 MiB exception and remains capped at 16 MiB. Before accepting any publish, the owner store reserves enough event-count and byte capacity for at least one worst-case terminal withdraw/revoke event; otherwise publish fails before mutation. Exhaustion is `resource_exhausted`. Safe errors contain only closed kind, protocol coordinate, and optional bounded numeric limit; they contain no path, query, policy text, exception, environment, or secret.

## 11. Rollback

Before consumer activation, rollback is disablement plus preservation of candidate/verdict/publication history. After a future activation, the consumer owner may return to a separately current prior candidate only with its own accepted rollback plan and independent recovery controller. Withdrawal or revocation never rewrites consumer or owner history.

## 12. Stop conditions

Stop on ownership ambiguity, selectable ID absent from the frozen owner inventory, B0 derivation or incomplete deny-surface coverage, missing or conflicting custody policy, participant role conflict, U/O exposure, an extra process invocation/pass/rerun, non-pass publication, mutable history, stale or self-issued currentness, owner-head fork, unbounded capture, network dependence, consumer substitution, provider/model activity, or inability to restore/disable without deleting evidence.
