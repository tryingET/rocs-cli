---
summary: "Normative deterministic, authority, transaction, evidence, and rollback invariants for Semantic Release Protocol v0."
read_when:
  - "Implementing or independently reviewing decision:53 machine contracts."
type: "specification"
status: "proposed"
rfc_revision: "semantic-release-revision-v1"
---

# Semantic Release Protocol v0 — Normative Invariants

The sibling [`protocol.schema.json`](protocol.schema.json) owns structural validation. This document owns cross-object and operational constraints that Draft 2020-12 cannot express portably. Both MUST pass. A conflict fails closed; this file controls cross-field semantics, the schema controls shape, and the RFC controls owner/governance boundaries. Examples and fixtures never grant authority.

## 1. Input and canonical JSON

1. Inputs MUST be duplicate-key-free UTF-8 JSON. A decoder MUST reject a BOM, malformed UTF-8, duplicate object names at any depth, lone surrogates, noncharacters, and trailing data.
2. Inputs MUST be integer-only I-JSON. Floats, exponent notation, negative zero, NaN, infinities, and integers outside `0..9007199254740991` are invalid. Booleans are not integers.
3. Every string MUST be Unicode NFC. Protocol names, identifiers, digests, versions, modes, and namespaces are ASCII where their schema patterns require it.
4. JCS means RFC 8785 canonicalization after the restrictions above. Object keys sort by UTF-16 code units; arrays retain their normative order; no insignificant whitespace is emitted.
5. Schema `minLength` and `maxLength` count Unicode code points. An implementation MUST also enforce the same numeric ceiling in UTF-8 bytes. Aggregate limits are: JSON artifact 16 MiB, manifest 100,000 entries/256 MiB described bytes unless a smaller owner policy applies, nesting depth 64, and processing deadline supplied by the caller but at most 300 seconds.
6. Unknown fields, unknown enum values, unsupported protocol versions, network access, or unavailable required references fail closed. Validation is offline; no validator may fetch a schema, trust root, publication, decision, blob, or receipt.
7. Every set-valued array is duplicate-free and in its specified order. Protocol-version strings, candidate IDs, pack digests, deprecations, removals, tombstones, and error-detail keys sort by UTF-8 bytes. Approval votes sort by `(owner_id UTF-8, owner_key_id UTF-8)`. Compatibility conditions sort by condition ID; change rows and manifests use their rules below. Arrays with no stated set/order semantics retain authored order and MUST NOT be treated as sets.

## 2. Digest construction and omissions

A protocol digest is:

```text
"sha256:" + lowercase_hex(SHA-256(UTF8(domain) || 0x00 || preimage))
```

For JSON objects, `preimage` is JCS bytes after removing exactly the listed top-level self-digest key. The omitted key is absent, never present as `null`. All nested digests remain. A digest-bearing object MUST contain its recomputed digest. The coordinate has no self-digest; its coordinate digest is computed when needed over the complete coordinate with no omission.

| Object/blob | Domain | Omitted key |
|---|---|---|
| raw source or material bytes | `semantic-release.raw-blob.v0` | none; preimage is raw bytes |
| semantic payload bytes | `semantic-release.semantic-payload.v0` | none; preimage is raw bytes |
| coordinate | `semantic-release.coordinate.v0` | none |
| source manifest | `semantic-release.source-manifest.v0` | `source_manifest_digest` |
| material manifest | `semantic-release.material-manifest.v0` | `material_manifest_digest` |
| compatibility report | `semantic-release.compatibility-report.v0` | `compatibility_report_digest` |
| capsule | `semantic-release.capsule.v0` | `capsule_digest` |
| owner approval | `semantic-release.owner-approval.v0` | `owner_approval_digest` |
| owner publication | `semantic-release.owner-publication.v0` | `owner_publication_digest` |
| build receipt | `semantic-release.build-receipt.v0` | `build_receipt_digest` |
| consumer intent | `semantic-release.consumer-intent.v0` | `consumer_intent_digest` |
| owner acceptance | `semantic-release.owner-acceptance.v0` | `owner_acceptance_digest` |
| materialization verification | `semantic-release.materialization-verification.v0` | `materialization_verification_receipt_digest` |
| activation | `semantic-release.activation.v0` | `activation_receipt_digest` |
| ROCS generation | `semantic-release.rocs-generation.v0` | `rocs_generation_receipt_digest` |
| Pi delivery | `semantic-release.pi-delivery.v0` | `pi_delivery_receipt_digest` |
| AK evidence linkage | `semantic-release.ak-evidence-linkage.v0` | `ak_evidence_linkage_digest` |
| rollback request | `semantic-release.rollback-request.v0` | `rollback_request_digest` |
| rollback receipt | `semantic-release.rollback-receipt.v0` | `rollback_receipt_digest` |
| audit envelope | `semantic-release.audit-envelope.v0` | `audit_envelope_digest` |
| error envelope | `semantic-release.error.v0` | `error_digest` |

A timestamp is forbidden in every artifact except `semantic-audit-envelope.v0`. Audit metadata is immutable because the envelope has its own digest and binds the artifact digest. Re-recording an observation creates a new append-only envelope; it never edits an old envelope or the bound artifact.

## 3. Paths, manifests, and complete trees

1. Logical paths are relative NFC POSIX paths. They contain no empty, `.` or `..` component, backslash, NUL, absolute prefix, drive prefix, or normalization collision. Path comparison and sorting use UTF-8 bytes.
2. Entries sort strictly by `(path UTF-8 bytes, kind)` and paths are unique. Every parent directory except the declared root is listed. No two entries may differ only by Unicode normalization or platform case folding; such a tree is not portable and is rejected.
3. Source manifests may contain regular files, directories, and relative symlinks that remain within `source_root`. Symlink target bytes are UTF-8 NFC, and `target_byte_length`/`target_digest` bind those bytes. Source manifests reject submodules, sockets, devices, FIFOs, hard-link ambiguity, and uncommitted or ignored additions. `clean_committed=true` is verified against the exact immutable source revision, not trusted as an assertion.
4. Material manifests contain only directories and regular files. Archive duplicate names, links, special files, traversal paths, sparse ambiguity, and metadata-dependent content are rejected. Modes are significant: `0644` (420), `0755` (493), directories `0755`.
5. File `byte_length` is the length of raw bytes. `content_digest` uses the raw-blob domain above, not a bare SHA-256. Directory entries have no byte digest.
6. Complete-tree equality means identical sorted `(path, kind, mode, byte_length/content_digest)` tuples. The verifier walks without following links and rejects every unlisted or missing entry. Expected and actual manifest digests alone are insufficient unless both complete manifests are available and independently recomputed.
7. Source, compiled payload, capsule archive, staged materialization, and active materialization are distinct roots and manifests. The capsule binds generated material; the build receipt, not the capsule, binds the ROCS tool identity.

## 4. Owner issuance and trust chain

1. The semantic namespace owner maintains, on its own surface, an immutable owner-policy revision, owner set, approval predicate, compatibility policy, trust-root policy, and namespace ledger. ROCS may build and verify; ROCS, a consumer, Pi, and AK MUST NOT issue a semantic release.
2. Every vote binds the exact candidate capsule digest, and all votes in an approval MUST equal `candidate_capsule_digest`. Voter IDs/keys are unique, authorized by the pinned owner set, and satisfy the immutable predicate. Approval binds exact source and compatibility report digests. Its accepted owner decision MUST be accessible, digest-equal, accepted, in scope, and not revoked.
3. An unsigned local v0 publication is trusted only through an external owner-controlled local trust root provisioned independently of the capsule and consumer. Required chain:

```text
pinned trust root revision/digest
-> owner set and policy
-> exact owner approval
-> CAS publication ledger record
-> coordinate
-> capsule
-> manifests/blobs
```

A capsule, build receipt, intent, or consumer copy cannot bootstrap its own trust root.
4. Trust-root bootstrap/update/rotation requires the owner-controlled out-of-band process. A verifier pins a minimum root and publication-ledger revision. Older, missing, inaccessible, withdrawn, or revoked references fail with `trust_root_missing`, `trust_reference_stale`, or `trust_revoked`; cached last-known-good data may be used offline only when it meets those pins and is not locally revoked.
5. Rotation records bind old and new roots under owner policy. Revocation and withdrawal append records; they do not delete or rewrite publication history. v0 does not protect a host whose owner-controlled trust-root store and verifier are both compromised.

## 5. Namespace/version CAS publication ledger

1. A namespace has one append-only linear ledger. Its key `(namespace, semantic_version)` is permanently bound to at most one capsule digest. Identical replay is idempotent and returns the existing publication. Any different digest is `version_conflict`, even after withdrawal or revocation.
2. A publication has `ledger_namespace == coordinate.namespace`, `ledger_revision == expected_prior_revision + 1`, and `prior_publication_digest` equal to the current head (or null only at revision 1 with expected revision 0). The capsule namespace/version/digest, approval candidate digest, source/report bindings, and predecessor all match.
3. The predecessor is the immediately prior accepted active coordinate in this namespace, not merely the greatest SemVer. Genesis uses null. Forks, skipped heads, stale expected revisions, inconsistent predecessor, or same-version reuse fail without mutation.
4. Publication stages candidate blobs and the ledger record privately, verifies all digests and authority, fsyncs blobs/directories/journal, then performs one same-filesystem compare-and-swap head replacement. That durable head CAS is the linearization point.
5. The journal states are `prepared`, `committing`, `committed`. Recovery before the linearization point removes private staging; recovery after it completes durable record/commit-marker writes idempotently. A conflict never overwrites the winner. If same-filesystem atomic replacement, exclusive locking, fsync, or reliable recovery is unavailable, publication performs no mutation and returns `atomic_activation_unavailable` or `recovery_needed`.

## 6. Compatibility policy

1. Compatibility is computed deterministically against the ledger predecessor under the capsule-bound owner policy revision/digest. Every semantic change is classified exactly once. Change rows sort by `(semantic_id UTF-8, category UTF-8)` and are unique. Conditions sort by `condition_id`; IDs are unique. Deprecations, removals, and tombstones are separately unique and UTF-8 sorted.
2. Policy categories are exhaustive: addition, documentation, compatible refinement, deprecation, removal, rename, constraint change, relation change, identifier reuse, and other. `identifier_reuse` always yields `breaking`; an unclassifiable `other` yields `unknown` unless an owner override approved under the same policy resolves it.
3. Overall severity is the maximum required effect. `unknown` propagates. Conditional compatibility requires one or more machine conditions and each condition's exact evidence digest. Missing or false evidence fails adoption as `compatibility_rejected`; unknown fails as `compatibility_unknown`.
4. The candidate SemVer MUST satisfy the required effect: patch for patch-only, at least minor for minor, and major for major/breaking. Initial `0.y.z` exceptions exist only if explicitly encoded in the bound policy; they are not implicit. Version regression is rejected.
5. Deprecation is append-only state. Removal requires a prior deprecation and the policy's minimum release interval. Every removed/renamed ID enters the permanent tombstone registry. Tombstoned IDs are never reused. A policy override is a separate owner approval digest, cannot resolve identifier reuse, and cannot permit a lower SemVer effect than owner policy allows.

## 7. Consumer intent, acceptance, and materialization

1. Consumer desired state belongs to the consumer owner. A valid chain is exact consumer intent -> separate consumer-owner acceptance -> ROCS materialization/verification -> separate activation gate. Intent and technical verification never imply acceptance or activation.
2. `acceptance_authority.kind` MUST be `consumer_owner`; its identity MUST match the repository's governing owner. The decision is digest-bound, accepted, in scope, not stale/revoked, and independent of ROCS/Pi. The accepted posture equals the requested posture and cannot exceed governing scope. `valid_through_intent_revision >= intent_revision`; a non-null revocation blocks use. The consumer owner maintains a monotonic integer activation epoch outside ROCS. An activation is unexpired only when its bound `activation_epoch <= activation_epoch_not_after`; epoch regression or an inaccessible current owner epoch fails closed. Wall-clock observations remain audit envelopes, not acceptance identity.
3. Repository identity is stable across locator rename through owner-issued `identity_revision`; a fork receives a new `repository_id`. Fleet aggregation is a set of per-repository receipts and never replaces them with one fleet self-assertion.
4. Materialization requires the exact intent, acceptance, publication/trust chain, capsule and blobs, complete expected manifest, independent runtime pin, compatibility policy/report/evidence, repository identity, prior receipt, rollback target, fixed verifier contract/limits, and an already materialized rollback target (or tested no-prior disable path).
5. `issuer.kind` for materialization is `rocs`; it claims deterministic bytes and checks only. `expected_manifest_digest == actual_manifest_digest`, complete trees equal, compatibility is neither breaking nor unknown, and rollback readiness is independently verified. The receipt is not adoption consent.
6. Materialization uses an exclusive consumer lock and private same-filesystem staging. It verifies before mutation, fsyncs content and journal, atomically replaces one active-generation pointer, fsyncs the parent, appends the receipt outside replaceable roots, then writes/fsyncs the commit marker. The pointer replacement is activation of materialized bytes only, not a governance activation.
7. Journal recovery is deterministic and idempotent. Before pointer replacement, discard staging. After pointer replacement but before the durable receipt/marker, complete those records from the journal or restore the exact previous pointer; never report success without a durable marker. Digest-equal replay is idempotent; a different transaction at the same intent revision is `history_conflict`. Unsupported atomicity causes no mutation.

## 8. Activation and default membrane

1. Activation requires a fresh, unexpired, unrevoked owner acceptance and committed materialization receipt. `issuer.kind` is `consumer_owner`; activation scope equals the independently accepted gate and may not exceed intent posture. Its owner-controlled monotonic `activation_epoch` is within the acceptance bound and is never inferred from an audit timestamp.
2. The gates are separate and ordered only by explicit owner policy: `named_canary`, `explicit_search_default`, `automatic_preflight_default`, `startup_orientation`, and `fleet`. Every expansion requires its own accepted owner/AK decision, evidence criteria, named scope, rollback proof, stop conditions, and activation receipt. No prior gate automatically authorizes a later one.
3. One producer/consumer vertical slice is evidence only. It never authorizes canary activation, defaults, fleet rollout, implementation, publication, or ontology mutation.
4. Decision `52` and its evidence are development-only. They cannot satisfy release, trust, adoption, activation, default, or fleet gates. Decision `53` itself requires lawful strict-review closure, accepted ADR, separate implementation and validation/rollout/rollback plans, owner-scoped fan-out/tasks, reevaluation, and AK `unblocked` before any implementation task can be authorized. This v0 packet does not provide those facts.
5. Missing, stale, inaccessible, rejected, or revoked owner/AK references fail closed. Session logs and fixture files are noncanonical and have no authorization effect.

## 9. Evidence and issuer claim scopes

1. ROCS generation, Pi delivery, AK linkage, and empirical analysis are four facts. They MUST NOT be merged or inferred from one another.
2. ROCS generation requires `issuer.kind=rocs`, claim `generated_output_only`, and binds exact activation, coordinate, runtime, caller request, result, effective execution, candidate IDs, and pack digests. Arrays are duplicate-free and UTF-8 sorted. `matched` means deterministic generation only.
3. Pi delivery requires `issuer.kind=pi`, claim `delivered_to_prompt_run_only`, and binds the exact ROCS receipt, prompt-run digest, and delivered effective-execution digest. It proves delivery/binding, not reading, interpretation, influence, or correctness.
4. AK linkage requires `issuer.kind=ak`, claim `lineage_linkage_only`, and binds task, decision, canonical AK evidence record, activation, ROCS, and Pi receipts. AK references owner/ROCS/Pi facts; it does not absorb ontology bytes or reissue their claims.
5. DSPx/Oracle empirical outcome is optional and externally owned. If present, only its digest is linked. No protocol receipt may claim model interpretation or material influence without that owner's separate evidence contract.

## 10. Rollback and immutable history

1. Semantic and runtime rollback are independent axes. Semantic rollback changes N to an already materialized predecessor while holding runtime fixed. Runtime rollback changes the independently pinned tool while holding semantic N fixed and reruns compatibility/materialization verification. Combined recovery executes explicit stages and records partial failure; neither axis is inferred from the other.
2. A first generation uses `no_prior_disable`: restore the exact pre-adoption behavior and leave no semantic coordinate active. This path must be rehearsed before activation. Every non-null semantic rollback target and runtime target is already locally materialized, complete-tree verified, trusted, and usable by a recovery controller independent of the active runtime.
3. A rollback request binds the active receipt, exact from/target coordinates and runtimes, owner decision, preconditions, target materialization receipt, and recovery runtime. Missing target or recovery capability fails before mutation with `rollback_unavailable`.
4. Rollback uses the same lock/journal/fsync/atomic-pointer protocol as materialization. A success receipt binds availability proof and distinct before/after history heads. A failure receipt has `result=failed`, non-null error digest, unchanged active state/history head, and recoverable journal state. Success has null error and appends history.
5. Receipts, publications, audit envelopes, revocations, failures, and supersession links are append-only and stored outside replaceable materialization/runtime roots. Rollback never deletes or edits history. Minimum retention is the namespace/consumer lifetime plus seven years; owner policy may extend it. GC may delete unreferenced blobs only after tracing every ledger head, coordinate, active/rollback target, receipt, audit envelope, revocation, and legal hold. Tombstones and identity/version bindings are permanent.

## 11. Failure precedence

Decode/I-JSON errors precede schema errors; schema errors precede digest mismatch; authority/trust precede compatibility; compatibility precedes staging; complete-tree verification precedes pointer mutation; rollback availability precedes rollback mutation. A single deterministic primary error is returned, with sorted detail keys. Required mappings include:

- malformed/duplicate/non-I-JSON/unknown field -> `malformed_input`;
- unavailable network dependency -> `network_forbidden`;
- stale/revoked trust -> `trust_reference_stale` / `trust_revoked`;
- owner or consumer self-approval -> `self_certification`;
- stale CAS -> `publication_conflict`; reused version/different digest -> `version_conflict`;
- missing/unlisted tree entry -> `incomplete_tree`; changed expected snapshot -> `snapshot_drift`;
- unknown policy result -> `compatibility_unknown`;
- unavailable atomic primitive -> `atomic_activation_unavailable`;
- interrupted transaction needing owner action -> `recovery_needed`;
- absent predecessor/recovery runtime/disable path -> `rollback_unavailable`;
- issuer outside the scopes above -> `issuer_scope_violation`.
