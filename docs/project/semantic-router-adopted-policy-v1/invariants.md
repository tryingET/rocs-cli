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
- sorted Softwareco-owned selectable IDs;
- independent contamination-manifest digest;
- candidate digest.

The owner commit must contain the exact policy/provenance/source bytes named by provenance. A candidate is immutable. Correcting any byte creates a new candidate ID and digest.

Candidate paths are canonical root-relative POSIX paths: no absolute path, empty segment, `.`, `..`, backslash, NUL, symlink traversal, or alias. Later capture inherits Decision 102's descriptor and Git object-database safety requirements.

## 5. Evaluation verdict

A verdict binds one candidate digest, evaluator commit/tree/tool digest, preregistration digest, D/U/O dataset digests, contamination manifest, execution receipt digest, metrics digest, outcome, and exact authority coordinates for both custodian approval and independent verdict review. Each authority coordinate binds repository ID, Git commit/tree, and approval/review artifact digest. The custodian is exactly `softwareco/owned/dspx` unless a pre-data reviewed packet revision names another owner. Custodian and independent-review repository IDs must differ from the policy owner and policy-author repositories; a self-issued approval is invalid.

`outcome` is exactly `pass | fail | indeterminate`. Precedence is:

1. evidence-integrity or execution-validity defect → `indeterminate`;
2. otherwise any semantic, utility, operational, compatibility, or review gate failure → `fail`;
3. otherwise every frozen gate and independent review passes → `pass`.

Only `pass` may be referenced by a `publish` event. A later discovery of leakage or integrity loss requires an owner `revoke` event; the old verdict is not rewritten.

Raw U/O prompts, labels, and row outputs are not protocol members and must not enter ROCS, Git, or AK.

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

For sequence `n > 1`, `previous_event_digest` equals the digest of sequence `n-1`. The candidate digest is stable across a withdrawal/revocation event targeting that publication. `publish` requires a pass verdict. `withdraw` is a reversible lifecycle choice only through a new publish event. `revoke` marks the target unsafe; republishing the same candidate digest is forbidden.

There is no mutable `latest` release. The only mutable owner-store pointer is a compare-and-swap head record whose immutable value names the complete history digest and terminal event sequence/digest. History is authoritative only when every supplied event verifies, the history digest verifies, and the observed head matches that same complete history and terminal event.

Concurrent fork, sequence gap, predecessor mismatch, missing event, duplicate sequence, or head regression is `invalid_owner_history`.

## 7. Owner head and local read receipt

An owner head binds owner, namespace, terminal sequence/digest, owner repository commit/tree, publication-history path/digest, and head digest. Its `publication_history_digest` equals the nested history object's digest.

A bounded read receipt binds:

- caller-pinned acquisition capability ID, Git commit/tree, and trusted approval-artifact digest;
- exact owner repository identity;
- no-follow local capture identity;
- observed commit/tree and head bytes/digest;
- complete publication-history digest and byte count;
- UTC `capture_started_at` and `capture_finished_at`, exact clock-source ID, clock-source approval digest, and bounded uncertainty in milliseconds;
- closed environment, no-network assertion, and stable final recheck;
- the separate read-receipt digest.

The read-receipt digest prevents any field from being re-dated without changing receipt identity. A verifier accepts a receipt only when its capability coordinate and approval digest exactly equal caller-pinned trusted values and its clock-source ID and approval digest exactly equal separately caller-pinned trusted clock values. The receipt's `clock_uncertainty_ms` must not exceed the caller-pinned maximum. `capture_finished_at` must be no earlier than `capture_started_at`; clock rollback, leap/uncertainty outside that bound, or an untrusted clock source fails closed.

Decision 103 defines the shape, not a live acquisition capability. Until a later task implements and independently verifies owner-specific acquisition, currentness cannot pass.

## 8. Action-time currentness proof

A currentness proof binds candidate, pass verdict, the complete publication history, owner head, and read receipt. `observed_at` must byte-equal the receipt's `capture_finished_at`; it is not an independently chosen timestamp. It is valid only when:

1. all digests and object schemas validate;
2. owner/repository/namespace values are equal throughout;
3. every event and the complete history digest verify to the observed head;
4. the history's final event equals the head's terminal sequence/digest and targets the candidate;
5. the terminal action is `publish`;
6. no later withdrawal or revocation exists under the observed head;
7. candidate owner commit/tree and policy/provenance bytes match;
8. capture identity remained stable through final recheck;
9. caller-required maximum proof age is positive, bounded, and measured from immutable `capture_finished_at` against the verifier's trusted current UTC clock without rollback or uncertainty;
10. the expected acquisition capability coordinate and approval digest are caller-pinned and exact;
11. the expected clock-source ID, clock-source approval digest, and maximum uncertainty are separately caller-pinned and exact/bounded;
12. the consumer obtains this fresh capture immediately before its separately authorized action.

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
| one JSON object | 1,048,576 bytes |
| publication log | 16,777,216 bytes |
| publication events | 10,000 |
| selectable IDs | 2,000 |
| path bytes | 1,024 |
| string bytes | 65,536 |
| collection items | 50,000 |
| parser depth | 32 |

Exhaustion is `resource_exhausted`. Safe errors contain only closed kind, protocol coordinate, and optional bounded numeric limit; they contain no path, query, policy text, exception, environment, or secret.

## 11. Rollback

Before consumer activation, rollback is disablement plus preservation of candidate/verdict/publication history. After a future activation, the consumer owner may return to a separately current prior candidate only with its own accepted rollback plan and independent recovery controller. Withdrawal or revocation never rewrites consumer or owner history.

## 12. Stop conditions

Stop on ownership ambiguity, B0 derivation, U/O exposure, non-pass publication, mutable history, stale or self-issued currentness, owner-head fork, unbounded capture, network dependence, consumer substitution, provider/model activity, or inability to restore/disable without deleting evidence.
