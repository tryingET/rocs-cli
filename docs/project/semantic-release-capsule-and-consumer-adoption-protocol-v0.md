---
summary: "Cross-owner RFC for immutable semantic release publication, consumer materialization and activation, bounded evidence, and independent rollback."
read_when:
  - "Defining production semantic identity for ROCS consumers."
  - "Reviewing the production dependency of decision:52."
type: "rfc"
status: "proposed"
decision: "53"
rfc_revision: "semantic-release-revision-v1"
review_posture: "fresh_review_required"
---

# RFC — Semantic Release Capsule and Consumer Adoption Protocol v0

## 1. Status and legal effect

This revision answers the first strict review synthesis for decision `53`. It is a proposal-stage protocol packet, not an ADR, owner approval, implementation plan, publication, adoption, activation, default decision, fleet decision, or ontology mutation.

Normative machine artifacts are:

- [`semantic-release-v0/protocol.schema.json`](semantic-release-v0/protocol.schema.json) — closed Draft 2020-12 shapes;
- [`semantic-release-v0/invariants.md`](semantic-release-v0/invariants.md) — deterministic cross-field, authority, transaction, and retention rules;
- [`semantic-release-v0/golden-fixtures.json`](semantic-release-v0/golden-fixtures.json) and [`differential-fixtures.json`](semantic-release-v0/differential-fixtures.json) — canonical examples and counterexamples;
- [`semantic-release-v0/validate_fixtures.py`](semantic-release-v0/validate_fixtures.py) — stdlib-only independent fixture validator.

The schema controls shape, invariants control cross-field behavior, and this RFC controls owner/governance boundaries. A conflict or unavailable required fact fails closed. Fixtures are evidence only and have no authorization effect.

Normative terms **MUST**, **MUST NOT**, **REQUIRED**, **SHOULD**, and **MAY** use RFC 2119 meanings.

## 2. Problem and decision requested

A wrapper, mutable `dist/`, manifest version, ROCS package version, CI gate, or vendored runtime cannot prove which governed semantic generation a consumer requested, had independently accepted, materialized, activated, received in a prompt run, or retained for rollback.

The required supply chain is:

```text
owner-authored source
-> deterministic build
-> owner approval
-> CAS publication
-> consumer intent
-> consumer-owner acceptance
-> ROCS materialization verification
-> separately gated activation
-> ROCS generation
-> Pi delivery
-> AK evidence linkage
-> independent rollback
```

Decision `53` is asked only to accept this target architecture and machine-contract basis for later planning. It is not asked to authorize any step in that chain.

## 3. Owner boundaries

| Canonical fact | Source owner |
|---|---|
| Namespace, ontology meaning, owner policy/set, compatibility policy, tombstones, release approval, trust root, publication ledger | semantic namespace owner, initially `core/ontology-kernel` and its named semantic owners |
| Deterministic compilation, manifests, build receipt, offline verification, staging, ROCS generation receipt | `core/rocs-cli` |
| Repository desired state, acceptance scope, activation/default/fleet decisions, rollback decision | consumer owner with canonical AK decision references |
| Tasks, decisions, lineage, evidence record and linkage | Agent Kernel |
| Prompt-run delivery | Pi adapter owner |
| Interpretation/influence/behavior analysis | DSPx/Oracle or another accepted empirical-analysis owner |

ROCS builds and verifies but **MUST NOT** issue a semantic release, accept consumer intent, or activate a default. AK references owner and ROCS facts but **MUST NOT** store or reissue ontology bytes. Pi proves delivery only. A consumer **MUST NOT** bootstrap owner authority from its own copy of a capsule, intent, or receipt.

## 4. Normative release coordinate and identity separation

The sole production selector term is `semantic_release_coordinate`. It is the closed object:

```json
{
  "schema": "semantic-release-coordinate.v0",
  "namespace": "ai-society.core",
  "semantic_version": "1.1.0",
  "capsule_digest": "sha256:<64 lowercase hex>"
}
```

The namespace is lowercase dotted/hyphenated ASCII and the version follows the closed SemVer subset in the schema. Build metadata is forbidden. The coordinate does not identify source, publication authority, ROCS executable bytes, consumer intent, or activation; those are separate digest-bound facts.

A namespace ledger permanently binds `(namespace, semantic_version)` to at most one `capsule_digest`. Identical replay is idempotent. A different digest for an existing pair is `version_conflict`, including after withdrawal or revocation. String forms such as `X.Y.Z+sha256:...` are nonnormative and MUST NOT be accepted as coordinates.

Digest domains, JCS preimages, exact self-digest omissions, raw-blob identity, and timestamp separation are normative in `invariants.md`. In particular:

- source manifest, semantic payload, material manifest, capsule, owner approval/publication, build, consumer intent, verification, activation, evidence, and rollback all have distinct domains;
- ROCS tool identity is bound by build/consumer/verification receipts and is excluded from capsule identity;
- timestamps exist only in separately hashed audit envelopes and cannot be mutable omitted receipt fields.

## 5. Source, build, and capsule

### 5.1 Source eligibility

A candidate release MUST derive from one clean committed immutable source revision under the owner repository identity and declared source root. Its source manifest is a complete sorted tree of paths, kinds, significant modes, byte lengths, domain-separated raw-byte digests, and bounded relative symlinks. Uncommitted content, unlisted files, submodules, traversal, normalization collisions, archive duplicates, and special files fail closed.

The release process MUST produce separate complete manifests for source, compiled payload, capsule archive where used, and consumer materialization. Complete-tree equality rejects both missing and extra entries.

### 5.2 Deterministic build receipt

ROCS emits `semantic-build-receipt.v0`, binding:

- exact source manifest and compilation contract;
- independently pinned ROCS tool distribution and protocol version;
- compiled payload manifest and semantic payload digest;
- compatibility report;
- final candidate capsule digest;
- reproducibility result.

A build receipt claims deterministic construction only. It is not owner approval or publication.

### 5.3 Capsule

`semantic-release-capsule.v0` binds namespace/version, source and semantic payload identities, compiled material, owner and compilation policies, compatibility report, required protocol versions, predecessor coordinate, and permanent tombstone registry. Its digest omits only `capsule_digest` and retains every nested digest.

The predecessor is the immediately prior accepted active coordinate in the namespace publication ledger. Genesis alone has no predecessor. A capsule is immutable; corrections require a new version and digest.

## 6. Owner issuance and local trust

### 6.1 Owner approval

The semantic owner MUST maintain on its own surface an immutable revision of:

- namespace authority and governing scope;
- owner set and authorized key IDs;
- approval predicate (unanimous or exact threshold policy);
- compatibility and SemVer policy;
- trust-root bootstrap/rotation/revocation policy;
- namespace publication ledger.

`semantic-owner-approval.v0` binds that policy/set, exact clean source manifest, candidate capsule, compatibility report, owner decision, and unique votes. Every vote binds the same candidate digest. The approval predicate is evaluated from the pinned policy rather than trusted from the artifact. ROCS, AK, Pi, and consumer votes cannot substitute for semantic-owner approval.

### 6.2 Unsigned local v0 trust chain

Signing infrastructure remains outside v0, but trust is not circular. The accepted chain is:

```text
external owner-controlled local trust-root pin
-> immutable owner policy/set
-> exact owner approval
-> append-only owner publication
-> release coordinate
-> capsule
-> complete manifests and blobs
```

The trust root is provisioned and updated by an owner-controlled local process independent of the capsule and consumer. Pins include root ID/revision/digest and a minimum publication-ledger revision. Rotation binds old and new roots under owner policy. Withdrawal and revocation append records without changing prior bytes.

Offline verification MAY use a complete cached chain only when it meets all pins and local revocation state. Missing, inaccessible, stale, withdrawn, or revoked references fail closed. v0 cannot defend a host where both the owner-controlled trust-root store and verifier are compromised; it does prevent a capsule or consumer from self-certifying under an untrusted local copy.

## 7. Atomic owner publication

`semantic-owner-publication.v0` is the owner ledger record. Publication MUST:

1. acquire the namespace ledger lock;
2. compare `expected_prior_revision` and prior head digest;
3. verify coordinate/capsule/approval/source/compatibility/predecessor/trust bindings;
4. stage complete immutable blobs and record privately on the same filesystem;
5. fsync content, directories, and journal;
6. compare-and-swap one durable ledger head;
7. append/fsync the commit marker.

The durable head compare-and-swap is the linearization point. Revision increments by one. A stale head is `publication_conflict`; a reused version with another digest is `version_conflict`; neither mutates state. Digest-equal replay returns the existing publication.

The journal records `prepared`, `committing`, and `committed`. Recovery before the linearization point discards private staging; recovery after it idempotently completes the durable record/marker. If locking, same-filesystem atomic replacement, fsync, or deterministic recovery is unavailable, the publisher performs no mutation. Withdrawal/revocation append new records; publication history is never rewritten.

## 8. Compatibility policy

Compatibility is semantic-owner policy compiled and checked deterministically by ROCS against the ledger predecessor. `semantic-compatibility-report.v0` contains an exhaustive, sorted, unique change set with categories:

```text
addition | documentation | compatible_refinement | deprecation |
removal | rename | constraint_change | relation_change |
identifier_reuse | other
```

The report classifies the release:

```text
compatible | conditionally_compatible | breaking | unknown
```

`unknown` always fails publication/adoption. Conditional compatibility requires machine predicates and exact evidence digests; missing or false evidence fails. Overall SemVer effect is the maximum policy effect and the candidate version MUST satisfy it. Owner-approved overrides are separate digest-bound approvals, cannot legalize identifier reuse, and cannot weaken a prohibited SemVer effect.

Deprecation is append-only. Removal requires the policy's prior deprecation interval. Removed and renamed IDs enter a permanent tombstone registry, and tombstoned IDs MUST NOT be reused. `identifier_reuse` is always breaking. Owner policy, not ROCS or consumer preference, owns these classifications.

## 9. Consumer adoption chain

### 9.1 Consumer intent

`semantic-consumer-intent.v0` is consumer-owned desired state. It binds stable repository identity/revision, exact release coordinate, independent runtime/tool identity, requested posture, accepted compatibility class, rollback target, accepted consumer decision, external trust reference, fixed verifier contract, and resource limits.

A repository rename updates owner-issued identity revision without changing repository ID. A fork receives a new ID. Fleet reporting aggregates per-repository facts and never replaces them.

Intent is neither technical proof nor consent to activate.

### 9.2 Separate owner acceptance

`semantic-owner-acceptance.v0` binds the exact intent, repository, consumer-owner acceptance authority, revision, governing scope, accepted posture, accepted decision, validity revision, monotonic owner activation-epoch expiry, and revocation link. The acceptance issuer MUST be the governing consumer owner, not ROCS, Pi, AK as a tool, or the semantic producer. Missing, stale, inaccessible, expired, rejected, or revoked decisions fail closed. Wall-clock observations remain separately hashed audit envelopes.

Acceptance authorizes only its explicit posture and scope. It does not prove bytes and does not activate them.

### 9.3 Materialization and verification

ROCS emits `semantic-materialization-verification-receipt.v0`, deliberately not an “adoption receipt.” It binds exact intent/acceptance, coordinate, owner approval/publication trust chain, runtime pin, expected and actual complete manifests, repository identity, compatibility policy/report, prior receipt, already available rollback target, verifier contract, journal state, and durable commit marker.

ROCS MUST privately stage, fully verify, fsync, atomically replace one materialized-generation pointer, append the receipt outside replaceable roots, and write the durable marker under one lock/journal protocol. Recovery either completes the receipt/marker after pointer replacement or restores the exact prior pointer. Same-digest replay is idempotent; conflicting intent revision fails. Unsupported atomicity causes no mutation.

The receipt claims exact materialization and verification only. It is never owner consent, activation, default authority, or evidence of model use.

### 9.4 Separate activation

`semantic-activation-receipt.v0` requires a fresh, unexpired owner acceptance, committed materialization receipt, exact coordinate/runtime, accepted gate decision, named scope, activation revision, owner-controlled monotonic activation epoch, prior activation, and status/supersession links. Its issuer is the consumer owner.

The following gates are independent:

1. named canary activation;
2. explicit-search default;
3. automatic-preflight default;
4. startup orientation;
5. fleet rollout.

Each expansion requires its own accepted owner/AK gate, evidence criteria, bounded scope, stop conditions, rollback rehearsal, and activation receipt. Passing one gate never authorizes the next.

## 10. Evidence truth and issuer claims

The protocol separates four non-interchangeable records:

| Artifact | Required issuer | Maximum claim |
|---|---|---|
| `semantic-rocs-generation-receipt.v0` | ROCS | exact request/result/effective execution, selected IDs/packs, and generated outcome |
| `semantic-pi-delivery-receipt.v0` | Pi | exact ROCS output was delivered/bound to one prompt-run digest |
| `semantic-ak-evidence-linkage.v0` | AK | canonical task/decision/evidence lineage links those receipts |
| empirical outcome reference | DSPx/Oracle owner | separately defined behavior/interpretation evidence |

ROCS `matched` does not prove prompt delivery. Pi delivery does not prove the model read, interpreted, obeyed, or was influenced by content. AK linkage does not make session logs canonical and does not absorb owner facts. Any material-influence claim requires separate empirical-owner evidence.

Issuer kind and fixed `claim_scope` are schema-bound and enforced by invariants. An out-of-scope issuer fails with `issuer_scope_violation`.

## 11. Rollback and recovery

`semantic-rollback-request.v0` binds the active activation, exact from/target semantic and runtime identities, target materialization receipt, independently pinned recovery controller, owner decision, and preconditions. `semantic-rollback-receipt.v0` binds success/failure, resulting active state, availability proof, immutable history heads, error, and superseded activation.

Rollback axes are independent and MUST be rehearsed independently:

- **semantic:** release N to an already materialized trusted predecessor while runtime stays fixed;
- **runtime:** runtime R to an already materialized prior runtime while semantic N stays fixed, followed by compatibility/materialization revalidation;
- **no prior generation:** disable to the exact pre-adoption behavior;
- **combined/partial failure:** explicit staged recovery under the independent controller with failure receipts.

Targets MUST be locally available before activation. If the active runtime is broken, the recovery controller and target remain usable outside its root. Missing target, recovery runtime, or disable path fails before mutation with `rollback_unavailable`.

Rollback uses the same lock/journal/fsync/atomic-pointer discipline as materialization. It never rewrites publications, activations, receipts, or audit history. Failure preserves the prior active state and records a non-null error. Success appends a distinct history head.

## 12. History, audit, and failure behavior

Publications, approvals, intents, acceptances, materialization/activation/evidence/rollback receipts, errors, revocations, and audit envelopes are immutable and append-only outside replaceable semantic/runtime roots. Supersession and revocation are links, not edits.

Audit time belongs only in `semantic-audit-envelope.v0`, which binds artifact digest, event, issuer, sequence, prior envelope, and strict UTC timestamp under its own digest. Re-observation creates another envelope.

Retention is consumer/namespace lifetime plus at least seven years. Garbage collection traces every ledger head, active and rollback target, receipt, audit envelope, revocation, and legal hold before deleting unreferenced blobs. Namespace/version bindings and tombstones are permanent.

Errors use `semantic-protocol-error.v0` and deterministic precedence from `invariants.md`. Validation is offline/no-network with bounded input, manifests, nesting, and deadlines. Required failures include malformed input, stale/revoked trust, self-certification, version/publication conflict, snapshot drift, incomplete tree, compatibility unknown/rejected, unavailable atomic activation, recovery needed, rollback unavailable, history conflict, and issuer-scope violation.

## 13. Decision 52/53 membrane and proof posture

Decision `52` accepted a development-only discovery architecture. Its fixtures, vertical slice, Pi wiring, and evidence cannot satisfy semantic release issuance, trust, publication, consumer acceptance, activation, defaults, or fleet gates.

A representative producer/consumer/rollback vertical slice under this protocol is **evidence only**. Contrary to the original RFC wording, one slice does not authorize even a canary. Canary activation requires its own accepted gate after lawful Decision-53 implementation and validation authority exists.

Before implementation can be considered, decision `53` still requires:

1. fresh strict review closure over this exact RFC revision and machine packet;
2. an accepted ADR;
3. separate post-ADR implementation and validation/rollout/rollback plans;
4. owner-scoped fan-out/tasks and consent artifacts;
5. reevaluation of the concrete production dependency;
6. authoritative AK `unblocked` state.

This document supplies none of those later authorizations.

## 14. Candidate post-ADR fan-out — not authorized

If and only if the membrane above later closes, a Decision-53-specific fan-out candidate would keep work with its owners:

| Lane | Candidate responsibility | Required consent/evidence | Rollback owner / stop conditions |
|---|---|---|---|
| Semantic owner | adopt namespace issuance/compatibility/trust policy; produce clean candidate and publication ledger | owner decision, clean source, approval predicate, CAS/recovery proof | semantic owner; stop on unknown compatibility, trust ambiguity, conflict, dirty source |
| ROCS | implement closed schemas, deterministic build/verification, transactions, receipts/errors | cross-language/schema fixtures, complete-tree and crash differential evidence | ROCS owner; stop on nondeterminism, incomplete tree, unsupported atomicity |
| AK/consumer | canonical intent/acceptance/gates, repository identity, history links | accepted scoped decisions and immutable evidence links | consumer owner; stop on stale/revoked decision or unavailable rollback |
| Pi | bind validated ROCS output to prompt run without overclaim | delivery fixture and cancellation/stale-result evidence | Pi owner; stop on identity drift or delivery ambiguity |
| DSPx/Oracle | optional empirical behavior analysis | separately owned outcome contract | empirical owner; no influence claim without evidence |

Each lane would require an owner-scoped task with allowed paths, required evidence, rollback owner, and stop conditions. This table is sequencing guidance only; it creates no task or authority.

## 15. Non-goals

- online registry or network-dependent validation;
- automatic upgrades or fleet rollout;
- signing/key infrastructure beyond the externally pinned local v0 trust root;
- model interpretation or correctness attestation;
- implementation authorization;
- ontology mutation, including `core.AgentExperience`;
- modification of the ontology-kernel worktree;
- treating Decision `52`, fixtures, or one vertical slice as production authority.

## 16. Options rejected

- **Mutable latest semantic state:** no replay, uniqueness, or rollback identity.
- **String coordinate with SemVer build metadata:** ambiguous grammar and identity semantics.
- **Tool version as semantic identity:** conflates executable and meaning.
- **ROCS or consumer self-approval:** violates owner boundaries.
- **AK stores ontology bytes:** absorbs semantic-owner facts.
- **One adoption/use receipt:** conflates consent, bytes, activation, generation, delivery, lineage, and influence.
- **Mutable omitted timestamps:** permits receipt metadata rewriting.
- **Rollback assertion without pre-materialized targets:** fails when the active runtime is broken.

The proposed capsule/publication, intent/acceptance, verification/activation, split evidence, and independent rollback chain joins owner facts without merging them.
