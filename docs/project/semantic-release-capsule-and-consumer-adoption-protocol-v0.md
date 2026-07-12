---
summary: "Cross-owner RFC for immutable semantic release publication, consumer materialization and activation, bounded evidence, and independent rollback."
read_when:
  - "Defining production semantic identity for ROCS consumers."
  - "Reviewing the production dependency of decision:52."
type: "rfc"
status: "proposed"
decision: "53"
rfc_revision: "semantic-release-revision-v2"
review_posture: "fresh_review_required"
---

# RFC — Semantic Release Capsule and Consumer Adoption Protocol v0

## 1. Status and legal effect

This revision answers every blocker in the controlling rereview synthesis v1 for decision `53`. It is a proposal-stage protocol packet submitted for fresh strict review, not an ADR, owner approval, implementation plan, publication, adoption, activation, default decision, fleet decision, or ontology mutation.

Normative machine artifacts are:

- [`semantic-release-v0/protocol.schema.json`](semantic-release-v0/protocol.schema.json) — closed Draft 2020-12 shapes;
- [`semantic-release-v0/invariants.md`](semantic-release-v0/invariants.md) — deterministic cross-field, authority, transaction, and retention rules;
- [`semantic-release-v0/golden-fixtures.json`](semantic-release-v0/golden-fixtures.json) and [`differential-fixtures.json`](semantic-release-v0/differential-fixtures.json) — canonical examples and counterexamples;
- [`semantic-release-v0/validate_fixtures.py`](semantic-release-v0/validate_fixtures.py) — stdlib-only Python fixture validator;
- [`semantic-release-v0/validate_fixtures.mjs`](semantic-release-v0/validate_fixtures.mjs) — genuinely independent Node verifier that imports no Python generator/validator and independently recomputes JCS, digests, links, schema closure, and adversarial invariants;
- [`semantic-release-v0/generate_fixtures.py`](semantic-release-v0/generate_fixtures.py) and [`schema_builder.py`](semantic-release-v0/schema_builder.py) — deterministic schema/fixture regeneration.

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

`semantic-release-capsule.v0` binds namespace/version, source and semantic payload identities, compiled payload manifest, exact payload projection, capsule archive linkage, owner and compilation policies, executable compatibility report, required protocol versions, predecessor coordinate, and permanent tombstone registry. `semantic-capsule-archive-linkage.v0` binds the complete archive manifest, payload root, metadata path, archive format, and payload manifest. `semantic-payload-projection.v0` is the complete no-extra/no-missing mapping from capsule payload paths to consumer material paths, including mode, length, and content digest. The capsule digest omits only `capsule_digest` and retains every nested digest.

The predecessor is the immediately prior accepted active coordinate in the namespace publication ledger. Genesis alone has no predecessor. A capsule is immutable; corrections require a new version and digest.

## 6. Owner issuance and local trust

### 6.1 Owner approval

The semantic owner MUST maintain closed, immutable `semantic-owner-policy.v0`, `semantic-owner-set.v0`, `semantic-approval-predicate.v0`, `semantic-compatibility-policy.v0`, `semantic-trust-root.v0`, `semantic-trust-rotation.v0`, `semantic-trust-revocation.v0`, and namespace-ledger records on its own surface. The policy binds governing scope, exact set/predicate/policy digests, prior policy, old-root-authorized rotation, and fail-closed revocation.

The owner set pins each member's authorized key IDs and active/revoked state. `threshold` counts distinct eligible active owners and requires the exact threshold integer; `unanimous` requires every active owner. Multiple keys never multiply one owner's vote. A revoked vote fails as `trust_revoked`; an unauthorized, duplicate, or insufficient set fails as `approval_threshold_unsatisfied`.

`semantic-owner-approval.v0` binds that policy/set/predicate, exact clean source manifest, candidate capsule, compatibility report, canonical AK decision reference, and unique votes. Every vote binds the same candidate digest. The predicate is recomputed rather than trusted from the artifact. ROCS, AK, Pi, and consumer votes cannot substitute for semantic-owner approval.

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

Publication is an executable four-object protocol: `semantic-publication-transaction.v0`, `semantic-publication-journal.v0`, `semantic-owner-publication.v0`, and `semantic-publication-commit-marker.v0`. A transaction binds operation, coordinate, approval, expected prior revision/head, replay key, and status reason. Publication MUST acquire the namespace lock, verify all bindings, privately stage complete immutable blobs/record, fsync content/directories/journal, CAS one durable ledger head, and append/fsync its commit marker.

The durable head CAS is the linearization point. A stale revision is `publication_conflict`; a divergent expected head is `publication_fork`; reused version/different digest is `version_conflict`. None mutates state. Same coordinate/replay key is idempotent and returns the existing publication.

The closed journal combinations are prepared/not-linearized/discard, committing/linearized/complete, committed/linearized/none, and aborted/not-linearized/discard. Recovery before linearization discards staging; recovery after it completes record/marker idempotently. Impossible combinations return `recovery_needed`.

`semantic-publication-status-transition.v0` admits only published→withdrawn, published→revoked, and withdrawn→revoked. Every transition binds an operation-matching transaction, committed journal, commit marker, prior status, approval, reason, and next ledger revision. Revoked is terminal; history and version bindings are never rewritten.

## 8. Compatibility policy

Compatibility is a closed executable semantic-owner policy checked deterministically by ROCS against the ledger predecessor. `semantic-compatibility-policy.v0` contains exactly one sorted rule for every category, fixing classification, SemVer effect, typed condition operator, override permission, severity order, deprecation interval, zero-major posture, and permanent identifier-reuse prohibition. `semantic-compatibility-report.v0` contains an exhaustive, sorted, unique change set with categories:

```text
addition | documentation | compatible_refinement | deprecation |
removal | rename | constraint_change | relation_change |
identifier_reuse | other
```

The report classifies the release:

```text
compatible | conditionally_compatible | breaking | unknown
```

`unknown` always fails publication/adoption. Conditions execute one of `evidence_digest_equals`, `consumer_protocol_at_least`, or `deprecation_interval_at_least` over typed operands; `satisfied` is recomputed. Missing, false, duplicate, or ill-typed evidence fails. Overall SemVer effect is the maximum and the candidate version MUST satisfy the exact patch/minor/major relation. `semantic-compatibility-override.v0` is separately digest/owner-approval bound and cannot legalize identifier reuse, bypass lifecycle, erase conditions, or weaken a SemVer floor.

`semantic-deprecation-record.v0` and `semantic-removal-record.v0` make lifecycle executable. Removal binds the exact prior deprecation and accepted-ledger interval. Removed and renamed IDs enter append-only `semantic-tombstone-registry.v0`; tombstoned IDs MUST NOT be reused, including after withdrawal/revocation or override. Owner policy, not ROCS or consumer preference, owns these classifications.

## 9. Consumer adoption chain

### 9.1 Consumer intent

`semantic-consumer-intent.v0` is consumer-owned desired state. It binds stable repository identity/revision, exact release coordinate, independent runtime/tool identity, requested posture, accepted compatibility class, discriminated rollback target, canonical `semantic-ak-decision-reference.v0`, external trust reference, fixed verifier contract, and resource limits. The AK reference binds AK repository/runtime identity, decision ID/revision/lifecycle, accepted ADR identity/revision/digest, scope, revocation, and exact activation target/evidence criteria/rollback plan/stop conditions.

A repository rename updates owner-issued identity revision without changing repository ID. A fork receives a new ID. Fleet reporting aggregates per-repository facts and never replaces them.

Intent is neither technical proof nor consent to activate.

### 9.2 Separate owner acceptance

`semantic-owner-acceptance.v0` binds the exact intent, repository, consumer-owner acceptance authority, revision, governing scope, accepted posture, accepted decision, validity revision, monotonic owner activation-epoch expiry, and revocation link. The acceptance issuer MUST be the governing consumer owner, not ROCS, Pi, AK as a tool, or the semantic producer. Missing, stale, inaccessible, expired, rejected, or revoked decisions fail closed. Wall-clock observations remain separately hashed audit envelopes.

Acceptance authorizes only its explicit posture and scope. It does not prove bytes and does not activate them.

### 9.3 Materialization and verification

ROCS emits `semantic-materialization-verification-receipt.v0`, deliberately not an “adoption receipt.” It binds exact intent/acceptance, coordinate, owner approval/publication trust chain, runtime pin, capsule archive linkage, payload projection, source payload manifest, expected and actual complete consumer manifests, repository identity, compatibility report, prior receipt, already available discriminated rollback target, verifier contract, journal state, and durable commit marker. Capsule payload → projection → expected consumer manifest → actual complete tree equality is mandatory; `projection_mismatch` precedes mutation.

ROCS MUST privately stage, fully verify, fsync, atomically replace one materialized-generation pointer, append the receipt outside replaceable roots, and write the durable marker under one lock/journal protocol. Recovery either completes the receipt/marker after pointer replacement or restores the exact prior pointer. Same-digest replay is idempotent; conflicting intent revision fails. Unsupported atomicity causes no mutation.

The receipt claims exact materialization and verification only. It is never owner consent, activation, default authority, or evidence of model use.

### 9.4 Separate activation

`semantic-activation-receipt.v0` requires a fresh, unexpired owner acceptance, committed materialization receipt, exact coordinate/runtime, accepted canonical AK gate decision, named scope, activation revision, owner-controlled monotonic activation epoch, prior activation, and revocation/supersession links. Its target, evidence criteria, rollback plan, and stop-condition digests MUST exactly equal the canonical AK decision. Its issuer is the consumer owner.

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
| `semantic-pi-delivery-receipt.v0` | Pi | discriminated delivered/suppressed/failed outcome; only delivered binds a prompt run |
| `semantic-ak-evidence-linkage.v0` | AK | canonical task/decision/evidence lineage links generation and optional Pi delivery |
| empirical outcome reference | DSPx/Oracle owner | separately defined behavior/interpretation evidence |

Generation is permitted only from the current `activated`, unrevoked, unsuperseded activation head; otherwise it fails `activation_not_current`. ROCS `matched` does not prove prompt delivery. Pi `delivered` requires prompt-run and exact effective-execution digests; `suppressed` requires a closed reason and forbids delivery fields; `failed` requires an error and forbids delivery fields. AK linkage MAY omit Pi only for generation-only lineage. No variant proves model reading, interpretation, obedience, influence, or correctness.

Issuer kind and fixed `claim_scope` are schema-bound and enforced by invariants. An out-of-scope issuer fails with `issuer_scope_violation`.

## 11. Rollback and recovery

`semantic-rollback-request.v0` binds the active activation, typed before-state, a closed axis-discriminated target, independently pinned recovery controller, canonical owner decision, and preconditions. Semantic targets switch coordinate and retain runtime; runtime targets retain semantics, switch runtime, and require runtime revalidation; no-prior targets bind tested disable/rehearsal; combined targets embed ordered semantic/runtime stages. `semantic-rollback-receipt.v0` binds result, typed before/after state, per-stage results/errors, availability proof, typed history heads, overall error, and superseded activation.

Rollback axes are independent and MUST be rehearsed independently:

- **semantic:** release N to an already materialized trusted predecessor while runtime stays fixed;
- **runtime:** runtime R to an already materialized prior runtime while semantic N stays fixed, followed by compatibility/materialization revalidation;
- **no prior generation:** disable to the exact pre-adoption behavior;
- **combined/partial failure:** explicit staged recovery under the independent controller with failure receipts.

Targets MUST be locally available before activation. If the active runtime is broken, the recovery controller and target remain usable outside its root. Missing target, recovery runtime, or disable path fails before mutation with `rollback_unavailable`.

Rollback uses the same lock/journal/fsync/atomic-pointer discipline as materialization. It never rewrites publications, activations, receipts, or audit history. Failure preserves byte-equal active state and exactly unchanged typed history head with a non-null error. Combined partial failure records completed and failed stages, resulting partial state, errors, and a new typed rollback head. Success appends a distinct typed rollback/disable head.

## 12. History, audit, and failure behavior

Publications, approvals, intents, acceptances, materialization/activation/evidence/rollback receipts, errors, revocations, and audit envelopes are immutable and append-only outside replaceable semantic/runtime roots. Supersession and revocation are links, not edits.

Audit time belongs only in `semantic-audit-envelope.v0`, which binds artifact digest, event, issuer, sequence, prior envelope, and strict UTC timestamp under its own digest. UTC is parsed and Gregorian-calendar round-tripped outside JSON Schema's annotation-only format; impossible dates fail `malformed_input`. Re-observation creates another envelope.

Retention is consumer/namespace lifetime plus at least seven years. Garbage collection traces every ledger head, active and rollback target, receipt, audit envelope, revocation, and legal hold before deleting unreferenced blobs. Namespace/version bindings and tombstones are permanent.

Errors use `semantic-protocol-error.v0` and deterministic precedence from `invariants.md`: decode/I-JSON, schema, `digest_mismatch`, authority/trust, compatibility/lifecycle, projection/tree, mutation, then rollback availability. Validation is offline/no-network with bounded input, manifests, nesting, and deadlines. Required failures include malformed input, digest mismatch, stale/revoked trust, threshold failure, self-certification, version/publication/fork conflict, snapshot/projection/incomplete tree, compatibility/SemVer/lifecycle rejection, unavailable atomic activation, recovery needed, stale activation, rollback unavailable, history conflict, and issuer-scope violation.

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
| AK coordination | maintain canonical decision/task/evidence lineage and owner handoffs without issuing semantic or consumer facts | accepted scoped references and immutable lineage links | AK owner; stop on stale/revoked decision, scope drift, or attempted owner substitution |
| Consumer owner | issue intent/acceptance/gates for a named repository and preserve rollback/history | accepted scoped decision, exact projection verification, activation and rollback evidence | consumer owner; stop on unavailable rollback, stale trust, or binding drift |
| Pi | bind validated ROCS output to delivered/suppressed/failed run outcome without overclaim | three delivery variants and cancellation/stale-result evidence | Pi owner; stop on identity drift or delivery ambiguity |
| DSPx/Oracle | optional empirical behavior analysis | separately owned outcome contract | empirical owner; no influence claim without evidence |

The named first consumer candidate is `softwareco/pi-canary-consumer`, limited to one operator-named canary and represented by a future consumer-owner task contract whose allowed paths, required receipts, exact activation target/evidence/rollback/stop bindings, and stop conditions must be accepted after the membrane closes. The candidate is non-authorizing: it creates no repository consent, task, canary, default, or implementation authority.

Each lane would require its own owner-scoped task. AK coordination and consumer-owner issuance MUST remain separate tasks/owners; neither may fan out the other's authority. This table is sequencing guidance only.

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
