---
summary: "Normative revision-2 authority, compatibility, transaction, projection, evidence, and rollback invariants for Semantic Release Protocol v0."
read_when:
  - "Implementing or independently reviewing decision:53 machine contracts."
type: "specification"
status: "proposed"
rfc_revision: "semantic-release-revision-v2"
---

# Semantic Release Protocol v0 — Normative Invariants

[`protocol.schema.json`](protocol.schema.json) owns closed shape; this file owns cross-object and operational behavior; the Decision-53 RFC owns governance boundaries. All three must agree. Missing facts, unavailable references, unknown values, conflicts, or disagreement fail closed. Fixtures prove examples only and grant no authority.

## 1. Canonical input and digest rules

1. Input is duplicate-key-free UTF-8 JSON without BOM or trailing data. Reject malformed UTF-8, lone surrogates, Unicode noncharacters, non-NFC strings, floats, exponent numbers, negative zero, booleans used as integers, and integers outside `0..9007199254740991`.
2. JCS is RFC 8785 after those I-JSON restrictions. Object keys sort by UTF-16 code units. Arrays retain normative order. Strings and `minLength`/`maxLength` count Unicode code points and must also fit the same UTF-8 byte ceiling.
3. Protocol digests are `"sha256:" + lowercase_hex(SHA-256(UTF8(domain) || 0x00 || preimage))`. JSON preimages are JCS after removing exactly the top-level self-digest field. The coordinate digest uses the complete coordinate. Raw blob and semantic payload preimages are unmodified bytes.
4. The domain is `semantic-release.<name>.v0`, where `<name>` is the hyphenated object name in `validate_fixtures.py` and `validate_fixtures.mjs`. Raw bytes use `semantic-release.raw-blob.v0`; semantic payload bytes use `semantic-release.semantic-payload.v0`; coordinates use `semantic-release.coordinate.v0`.
5. Every nested digest remains in the preimage. A missing or unequal embedded digest returns `digest_mismatch` after decode/schema checks and before authority checks. No other failure may mask a digest mismatch at that precedence.
6. Aggregate limits remain 16 MiB per JSON artifact, 100,000 manifest entries, 256 MiB described bytes, nesting depth 64, and caller deadline at most 300 seconds unless a closed owner policy is stricter. Validation is offline and performs no fetch.
7. Every set-valued array is duplicate-free and UTF-8 sorted. Manifest entries sort by `(path UTF-8, kind)`; votes by `(owner_id UTF-8, owner_key_id UTF-8)`; change rows by `(semantic_id UTF-8, category UTF-8)`.

## 2. Trees, capsule archive, and exact projection

1. Logical paths are relative NFC POSIX paths with no empty, `.`, `..`, backslash, NUL, drive, traversal, case-fold collision, or normalization collision. Every non-root parent directory is listed.
2. Source manifests admit regular files, directories, and bounded relative symlinks. They reject submodules, special files, hard-link ambiguity, uncommitted content, ignored additions, and source-revision drift. `clean_committed=true` is independently verified.
3. Material manifests admit only directories and regular files with significant modes `0644`, `0755`, and directory `0755`. Complete-tree verification rejects every missing, extra, duplicate, linked, sparse-ambiguous, or metadata-dependent entry.
4. `semantic-capsule-archive-linkage.v0` binds the complete archive manifest, compiled payload manifest, exact payload root, capsule metadata path, and archive format. Archive metadata is not allowed to alter payload identity.
5. `semantic-payload-projection.v0` is the complete allow-list from capsule paths to consumer paths. Each row binds path, mode, byte length, and content digest; directory rows use null length/digest. `projection_mode=exact_no_extra_no_missing` means the projection is total and bijective over payload entries and consumer entries.
6. A materialization receipt must simultaneously equal the capsule's projection and archive-linkage digests, the projection's payload and consumer manifest digests, and the independently recomputed actual consumer tree. Any omitted, extra, remapped, or changed entry, or archive-link drift, returns `projection_mismatch` before pointer mutation.
7. Source, payload, capsule archive, staged consumer tree, and active consumer tree are distinct roots. ROCS tool identity is bound by build/materialization receipts, not capsule identity.

## 3. Closed semantic-owner authority and trust

1. The semantic owner maintains immutable `semantic-owner-set.v0`, `semantic-approval-predicate.v0`, `semantic-compatibility-policy.v0`, `semantic-owner-policy.v0`, `semantic-trust-root.v0`, rotation, revocation, approval, and publication records on the owner surface.
2. The owner policy binds exact governing scope, owner set, approval predicate, compatibility policy, owner-controlled out-of-band trust bootstrap mode, prior policy, mandatory old-root rotation, and fail-closed revocation behavior. A consumer, ROCS, Pi, or AK cannot replace or mint these objects.
3. Owner-set members and key IDs are closed and unique. A vote is eligible only when its owner is active, its key is in that member's pinned key set, and its candidate digest equals the approval candidate. One owner counts once even if multiple keys vote.
4. `threshold` requires at least the exact integer `threshold` of distinct eligible active owners. `unanimous` requires every active member and sets `threshold` to that active-member count. Revoked owners/keys return `trust_revoked`; absent, duplicate, or insufficient eligible owners return `approval_threshold_unsatisfied`.
5. Owner approval binds policy, set, predicate, clean source, capsule, compatibility report, unique votes, and a canonical accepted AK decision reference. The predicate is recomputed; the approval's existence is not itself proof that the predicate passed.
6. The local trust chain is external owner-controlled root pin → owner policy/set/predicate → approval → publication → coordinate → capsule → manifests/blobs. A capsule, consumer copy, build receipt, AK record, or Pi receipt cannot bootstrap the root.
7. Rotation must bind the currently active old root, new root, owner policy, approval, and increasing revision. A stale old root returns `trust_reference_stale`; a revoked old root returns `trust_revoked`.
8. Revocations are append-only records with target kind, exact target digest, effective ledger revision, reason, owner approval, and prior revocation head. Locally known revocation wins over cached trust. Missing or stale local revocation state fails closed.
9. Offline cached trust is usable only if root revision, ledger revision, and local revocation head meet the external pins. v0 does not claim protection when both the owner-controlled root store and verifier are compromised.

## 4. Executable compatibility, SemVer, and lifecycle

1. `semantic-compatibility-policy.v0` contains exactly one UTF-8-sorted rule for each of the ten closed categories. Each rule fixes classification, SemVer effect, optional typed condition kind, and override permission. Policy severity is `patch < minor < major < unknown`; zero-major exceptions are absent unless explicitly enabled (v0 fixtures disable them).
2. Conditions are data, not prose. The three v0 operators are:
   - `evidence_digest_equals`: both digest operands are non-null and equal;
   - `consumer_protocol_at_least`: both integer operands are non-null and actual ≥ expected;
   - `deprecation_interval_at_least`: both integer operands are non-null and actual ≥ expected.
   `satisfied` must equal recomputation. Missing, duplicate, false, ill-typed, or unreferenced required conditions return `compatibility_rejected`.
3. Every change is classified once under the bound policy. Overall classification/effect is the maximum. `unknown` returns `compatibility_unknown`. `identifier_reuse` is always breaking/major and never overrideable.
4. For prior `A.B.C`, patch requires the same major/minor and a greater patch; minor requires a greater minor in the same major or a greater major; major requires a greater major. Regression, equality, prerelease weakening, or an insufficient bump returns `semver_violation`.
5. An override is a separately digested owner object bound to policy, exact change, condition, effect floor, and owner approval. It may resolve allowed `other`/unknown cases only as policy permits. It cannot legalize identifier reuse, erase a required condition, lower a SemVer floor, or bypass lifecycle state.
6. Deprecation records are append-only and bind semantic ID, coordinate, ledger revision, and prior lifecycle head. Removal binds the exact deprecation, removal coordinate/revision, policy interval, and tombstone. The elapsed accepted-ledger revisions must be at least the policy minimum; otherwise `lifecycle_violation`.
7. Removed or renamed IDs enter the permanent sorted tombstone registry. Registry revisions append to their prior digest. A tombstoned identifier is never reused, including after withdrawal/revocation or under an override.

## 5. Publication transaction and status machine

1. One namespace has one append-only ledger. `(namespace, semantic_version)` binds permanently to one capsule digest. Same coordinate plus same replay key is idempotent and returns the existing record; a different capsule at that version is `version_conflict` forever.
2. `semantic-publication-transaction.v0` binds operation, coordinate, owner approval, expected prior revision/head, replay key, and status reason. `publish` has null reason; `withdraw`/`revoke` require a reason.
3. Before mutation, the publisher checks lock ownership, exact namespace, version uniqueness, current revision/head, predecessor, trust, approval, policy, source, capsule, projection/archive, and compatibility. Wrong revision is `publication_conflict`; same revision with another expected head is `publication_fork`. Neither mutates state.
4. The journal states are:
   - `prepared`, not linearized, recovery `discard_staging`;
   - `committing`, linearized, recovery `complete_commit`;
   - `committed`, linearized, recovery `none`;
   - `aborted`, not linearized, recovery `discard_staging`.
   Any impossible state/action combination returns `recovery_needed`.
5. Publication privately stages immutable blobs and record, fsyncs content/directories/journal, then performs one same-filesystem CAS of the durable ledger head. That CAS is the sole linearization point. The commit marker then binds transaction, committed journal, resulting revision/head, and completed fsync.
6. Recovery before linearization discards private staging without history mutation. Recovery after linearization idempotently completes journal/record/marker. A loser never overwrites a winner. Unsupported lock, atomic replace, same-filesystem placement, fsync, or recovery performs no mutation.
7. Status is append-only. Legal transitions are `published → withdrawn`, `published → revoked`, and `withdrawn → revoked`; revoked is terminal. Each transition binds its operation-matching transaction, committed/linearized journal, commit marker, prior status record, owner approval, reason, and next ledger revision. Status history never rewrites publication bytes or frees a version.

## 6. Canonical AK decision membrane and consumer chain

1. Every protocol decision uses `semantic-ak-decision-reference.v0`, never an arbitrary digest-only decision assertion. It binds stable AK repository identity/revision, pinned AK runtime distribution, decision ID/revision, lifecycle state, accepted ADR ID/revision/digest/status, scope digest, revocation, and exact activation target, evidence criteria, rollback plan, and stop conditions.
2. A usable reference is `lifecycle_state=accepted`, accepted ADR, unrevoked, unsuperseded, accessible, and exact for its owner scope. Rejected, revoked, superseded, stale, inaccessible, wrong-repository, wrong-runtime, or binding-drift references fail closed. AK records lineage; they do not become semantic-owner or consumer-owner authority.
3. Consumer intent binds stable consumer repository identity/revision, coordinate, runtime, posture, compatibility acceptance, discriminated rollback target, canonical decision, trust reference, verifier contract, and limits. Rename increments identity revision; a fork gets a new repository ID.
4. Owner acceptance is separately issued by the repository's consumer owner. It binds exact intent, owner, governing scope, posture, canonical decision, intent validity, monotonic activation-epoch ceiling, and revocation. ROCS/Pi/AK cannot self-certify acceptance.
5. Materialization requires that chain plus exact capsule/archive/projection, complete trees, compatibility, runtime, rollback readiness, transaction/journal/marker, and prior receipt. It atomically replaces only the materialized-generation pointer. Its issuer is ROCS and its claim is technical verification only.
6. Activation is a separate consumer-owner receipt. It binds acceptance/materialization, target coordinate/runtime, scope, epoch, canonical gate decision, and the decision's exact activation target/evidence/rollback/stop digests. Every expansion gate requires a new accepted decision and activation receipt.

## 7. Generation, Pi delivery, and AK linkage

1. ROCS generation is legal only from the current activation head whose receipt is `activated`, unrevoked, and unsuperseded. Receipt coordinate/runtime must equal that activation. A historical, deactivated, revoked, superseded, or non-head activation returns `activation_not_current` before generation.
2. ROCS generation issuer/claim is `rocs/generated_output_only`. Candidate IDs and pack digests are sorted/unique. `matched` proves deterministic generation only.
3. Pi delivery is a closed discriminated union:
   - `delivered` uses `delivered_to_prompt_run_only` and requires prompt-run and delivered-execution digests;
   - `suppressed` uses `delivery_suppressed_only`, requires a closed suppression reason, and forbids prompt/delivered fields;
   - `failed` uses `delivery_failed_only`, requires an error digest, and forbids prompt/delivered fields.
4. Pi issuer is `pi`. Only `delivered` proves binding to a prompt run; none proves reading, interpretation, influence, or correctness.
5. AK evidence linkage binds canonical task, decision, evidence, activation, and ROCS generation. Pi receipt is optional specifically for generation-only lineage; when delivery is claimed it must bind the exact Pi receipt. Empirical outcome remains optional and separately owned.

## 8. Axis-discriminated rollback and immutable typed history

1. Rollback targets are a closed union:
   - `semantic`: switch to an already materialized coordinate while runtime action is exactly `retain`;
   - `runtime`: semantic action is exactly `retain`, switch runtime, and bind target materialization plus mandatory runtime revalidation receipt;
   - `no_prior_disable`: disable semantics, retain runtime, and bind tested disable contract/rehearsal;
   - `combined`: embed exact semantic and runtime stages and an explicit stage order.
2. Requests bind active activation, typed before-state, discriminated target, independent recovery runtime, accepted owner decision, and verified preconditions. Missing target/revalidation/recovery/disable proof returns `rollback_unavailable` before mutation.
3. Receipts bind typed before/after states, stage results/errors, availability, typed history heads (`activation|rollback|disable` plus digest), overall error, and supersession. Stage order equals the combined request.
4. Semantic success changes only coordinate. Runtime success changes only runtime and proves revalidation. Disable success yields `enabled=false`, null coordinate, retained runtime, and a typed `disable` history head.
5. Combined partial failure has at least one completed and one failed stage, non-null stage/overall errors, an after-state matching completed stages, and a new rollback history head. It never reports full success.
6. Failed rollback has a failed stage, non-null error, byte-for-byte unchanged active state, and exactly unchanged typed history head. It does not supersede activation. Any changed state/history is `history_conflict`.
7. Successful rollback has null error and a distinct typed history head. Rollback uses lock/journal/fsync/atomic-pointer discipline and appends history outside replaceable semantic/runtime roots. It never edits publication, activation, prior receipts, or audit history.

## 9. Audit, retention, and failure precedence

1. Timestamps occur only in `semantic-audit-envelope.v0`. `recorded_at` must match `YYYY-MM-DDTHH:MM:SSZ` and be a real Gregorian calendar date/time. Validators must parse and round-trip UTC outside JSON Schema's annotation-only `format`; `2026-02-30T12:00:00Z` is invalid.
2. Audit envelopes bind artifact schema/digest, event, issuer, sequence, prior envelope, and self-digest. Re-observation appends another envelope.
3. Retention is namespace/consumer lifetime plus at least seven years. GC traces every ledger/status/revocation head, coordinate, capsule/archive/projection, active/rollback target, receipt, audit envelope, legal hold, and typed history head. Version bindings and tombstones are permanent.
4. Deterministic precedence is decode/I-JSON → schema → `digest_mismatch` → authority/trust → compatibility/lifecycle → staging/projection/tree → pointer mutation → rollback availability/mutation. Details sort by key.
5. Required errors include all closed codes in the schema. In particular stale CAS is `publication_conflict`, divergent head is `publication_fork`, version reuse is `version_conflict`, invalid executable conditions are `compatibility_rejected`, invalid dates are `malformed_input`, and stale activation is `activation_not_current`.

## 10. Legal membrane

This packet is proposal-stage architecture evidence only. It is not an ADR, implementation authorization, release approval, publication, consumer consent, activation, default, fleet rollout, ontology mutation, or owner task. Decision 52 remains development-only. Decision 53 still requires strict review closure, accepted ADR, separately authorized implementation and validation/rollout/rollback plans, owner-scoped coordination, and authoritative AK unblocking before implementation.
