---
summary: "Cross-owner RFC for immutable semantic release publication, consumer materialization and activation, bounded evidence, and independent rollback."
read_when:
  - "Defining production semantic identity for ROCS consumers."
  - "Reviewing the production dependency of decision:52."
type: "rfc"
status: "proposed"
decision: "53"
rfc_revision: "semantic-release-revision-v9"
review_posture: "fresh_review_required"
---

# RFC — Semantic Release Capsule and Consumer Adoption Protocol v0

## 1. Status and legal effect

This revision answers the controlling [`semantic-release-rereview8-synthesis-v8.md`](semantic-release-rereview8-synthesis-v8.md) and its completed governance, owner, and ROCS lanes under the contextual-dominance architecture selected by [`semantic-release-many-of-the-greats-conflict-resolution-v9.md`](semantic-release-many-of-the-greats-conflict-resolution-v9.md). This is a proposal-stage protocol packet submitted for fresh strict review, not an ADR, owner approval, implementation plan, live capability deployment, publication, adoption, activation, default decision, fleet decision, or ontology mutation. Live capability provisioning, owner-store receipt acquisition, and action-time operation are explicitly unimplemented.

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

### 3.1 Capability-Pinned Owner-Receipt Authority Proof Graph

Every invocation supplies one closed `semantic-authority-acquisition-config.v0`, `semantic-authority-verifier-input.v0`, `semantic-authority-snapshot.v0`, and `semantic-authority-proof-bundle.v0`. The normative `semantic-authority-rule-role-manifest.v0` covers all 23 rules and classifies the 16 authority-bearing rules. It fixes every receipt, proof-node, and parameter role; exact role prefix/cardinality; category; owner surface and ID; stable repository identity; capability pin; expected schema; and registry edge set. The verifier input binds that manifest digest and the exact active role set. The manifest is reviewable completeness evidence, not an owner fact and not authorization.

The acquisition config terminates proof recursion in explicit, owner-specific local trust. Each `semantic-owner-acquisition-capability-pin.v0` binds one role to its category, owner surface/ID, complete repository identity, acquisition contract and distribution digests, store ID/head/revision, typed fact value/digest, freshness CAS token, and action-time epoch floor. `live_acquisition_implemented` is normatively `false` in this proposal packet: no owner capability is provisioned and no live store read is claimed.

The snapshot contains only `semantic-owner-store-read-receipt.v0` objects. Each receipt is issued by the pinned owner—not by the candidate, verifier, or collator—and repeats the complete capability, repository, store head/revision, fact, freshness token, action epoch, and floor. The collator is transport-only under `transport_only_no_receipt_issuance`; its identity must differ from every receipt issuer. Receipt fact digests and freshness/CAS tokens are independently recomputed, action epoch must meet the configured floor, and pin/receipt/binding fields agree exactly. Semantic trust/revocation/publication/lifecycle and vote facts, AK store/decision/task facts, consumer acceptance/activation/history facts, and recovery-controller facts retain separate owner categories. Category, owner, repository, pin, contract, distribution, head/revision, fact, or freshness substitution fails `issuer_scope_violation`.

The proof bundle contains every derived artifact under a key equal to its independently recomputed digest. Its nodes repeat complete owner repository identity in addition to schema, issuer, and claim scope. Parameter bindings make non-artifact values explicit rather than synthesizing generic authority context facts. Receipt, node, and parameter role sets are pairwise disjoint and their union equals both the verifier's required-role set and the manifest's exact cardinalities. Observation IDs equal receipt bindings; capability IDs equal configured pins; bundle keys equal node bindings. Missing, duplicate, contradictory, or surplus receipts, pins, roles, or nodes fail closed.

One universal preflight runs before every domain rule: raw duplicate-free canonical-integer I-JSON; closed schema; self-digests and normative order; exact manifest/config/snapshot/bundle/subject joins; full required-edge equality; pin-to-owner-receipt provenance, store/fact/freshness recomputation, and collator separation; exact receipt/node/parameter closure; proof-node digest, schema, owner repository, issuer, and claim scope; and dynamic vote/task closure. Domain rules receive only those resolved values. They **MUST NOT** derive canonical store/current records, trust/revocation/publication/lifecycle heads, consumer acceptance/activation/history heads, recovery controller/runtime/epoch, votes, or task state from a subject, another proof node, a generic context object, or a caller default.

The generated authority-edge registry contains exactly 92 UTF-8-sorted full tuples. Every tuple binds edge ID, rule, description, owner surface/ID/repository, one accepted fixture, exact positive cardinality, one drift fixture, exact drift cardinality, expected error, and a recomputed linkage digest. Manifest edge IDs and registry rows are a bijection. Python and Node independently require the same hard-pinned full-tuple registry and manifest digests, recompute owner/cardinality/linkage fields, execute both fixtures, count drift-fixture use mechanically, and prove that accepted and drift semantic case digests differ; they do not trust fixture-supplied edge or drift-count labels. Historical receipt integrity and current authorization remain distinct: an immutable old receipt may remain valid history while its currentness token or owner head makes it unusable for a new action.

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

The namespace is lowercase dotted/hyphenated ASCII. The version must match the complete SemVer 2.0.0 grammar, including exact prerelease and build productions, with no prefix/trailing acceptance; precedence ignores build metadata exactly as SemVer requires while the ledger binds the complete version token. The coordinate does not identify source, publication authority, ROCS executable bytes, consumer intent, or activation; those are separate digest-bound facts.

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

`semantic-release-capsule.v0` binds namespace/version, source and semantic payload identities, compiled payload manifest, exact payload projection, capsule archive linkage, owner/compilation policies, executable compatibility report, protocol versions, predecessor, and tombstones. Archive identity is acyclic: capsule → linkage → archive manifest plus closed metadata that excludes capsule/archive/linkage digests. The metadata raw JCS digest/length equal its archive entry. Projection source and destination paths are separately unique and their sets equal all payload and consumer entries, yielding a complete no-extra/no-missing bijection with mode/length/content equality. The archive set is exactly metadata, an exact `0755` directory entry at payload root, and prefixed payload entries; a file/symlink root or any extra entry rejects. The capsule digest omits only `capsule_digest` and retains every nested digest.

The predecessor is the immediately prior accepted active coordinate in the namespace publication ledger. Genesis alone has no predecessor. A capsule is immutable; corrections require a new version and digest.

## 6. Owner issuance and local trust

### 6.1 Owner approval

The semantic owner MUST maintain closed, immutable `semantic-owner-policy.v0`, `semantic-owner-set.v0`, `semantic-approval-predicate.v0`, `semantic-compatibility-policy.v0`, `semantic-trust-root.v0`, `semantic-trust-rotation.v0`, `semantic-trust-revocation.v0`, and namespace-ledger records on its own surface. The policy binds governing scope, exact set/predicate/policy digests, prior policy, old-root-authorized rotation, and fail-closed revocation.

The owner set pins each member's keys and active/revoked state. `threshold` counts distinct eligible active owners and lies within the active count; `unanimous` requires every active owner **and** `threshold` equal that count. Multiple keys never multiply an owner. Revoked vote is `trust_revoked`; unauthorized, duplicate, insufficient, or unanimous-threshold drift is `approval_threshold_unsatisfied`.

`semantic-owner-approval.v0` binds one exactly equal namespace/policy/set/predicate chain, canonical AK decision, and one closed typed action (`release`, `trust_rotation`, `trust_revocation`, `compatibility_override`, `publication_withdrawal`, or `publication_revocation`). The action digest is recomputed and every vote binds it. Rotation/trust-revocation actions repeat exact namespace/policy/set/predicate/root/target/prior-head/revision facts; withdrawal/publication-revocation actions repeat coordinate, prior status/digest, operation, reason, and expected revision/head; release repeats clean source/capsule/report; override repeats exact change/effect/condition. The predicate is recomputed. ROCS, AK, Pi, and consumer votes cannot substitute for semantic-owner approval.

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

The trust root is provisioned and updated by an owner-controlled local process independent of the capsule and consumer. The external canonical pin is an independently supplied closed fact binding namespace, root ID/revision/digest, owner-policy digest, and owner-set digest; none may default from the publication, approval, trust-root object, capsule, or consumer claim. Consumer trust references additionally bind the minimum publication-ledger revision and externally observed revocation revision/head. Rotation, revocation, and compatibility-override approvals resolve their canonical AK decision only against capability-pinned AK owner-store receipts; neither store heads nor current-record digests may default from the approval or decision reference. Every approval vote additionally resolves an owner-specific vote-proof receipt under that voter’s pinned capability; an opaque vote digest or collator-issued proof cannot authorize. Rotation binds old and new roots under owner policy. Withdrawal and revocation append records without changing prior bytes.

Offline verification MAY use a complete cached chain only when it meets all pins and local revocation state. Missing, inaccessible, stale, withdrawn, or revoked references fail closed. v0 cannot defend a host where both the owner-controlled trust-root store and verifier are compromised; it does prevent a capsule or consumer from self-certifying under an untrusted local copy.

## 7. Atomic owner publication

Publication is an executable acyclic four-object protocol: transaction → resulting publication/status record → journal → commit marker. A transaction binds operation, coordinate, approval, expected prior revision/head, replay key, and status reason. Publication MUST acquire the namespace lock, verify all bindings, privately stage complete immutable blobs/record, fsync content/directories/journal, CAS one durable ledger head, and append/fsync its commit marker.

The durable head CAS is the linearization point. A stale revision is `publication_conflict`; a divergent expected head is `publication_fork`; reused version/different digest is `version_conflict`. None mutates state. Same coordinate/replay key is idempotent and returns the existing publication.

The closed journal combinations are prepared/not-linearized/discard, committing/linearized/complete, committed/linearized/none, and aborted/not-linearized/discard. Recovery before linearization discards staging; recovery after it completes record/marker idempotently. The journal recovery-controller ID, recovery-runtime identity, and recovery epoch equal capability-pinned recovery-controller receipts, and the resulting status transaction equals the journal transaction. Publish/withdraw/revoke expected prior revision/head and prior-journal digest also equal the semantic owner’s canonical publication receipts; recovery before-state revision/head and prior journal equal the corresponding owner receipts. Impossible combinations return `recovery_needed`.

Withdraw and publication-revocation transactions require their own threshold-satisfied operation-specific owner approval; a release approval is never reusable. `semantic-publication-status-transition.v0` admits only published→withdrawn, published→revoked, and withdrawn→revoked. A resulting record binds transaction/prior status without backward journal/marker links; journal and marker each bind that exact transition digest as resulting head/revision. The shared publication-authority helper resolves the owner policy, set, predicate, trust root, independent external canonical pin and revocation state, canonical current AK decision, exact operation action, and recomputed threshold for publish, withdraw, and revoke. A root present in the externally observed revoked-digest set rejects. Namespace/policy/set/root facts join exactly. The prior status object and prior journal are schema/self-digest/order validated and joined by exact result digest, revision, head, and transaction facts; the prior journal transaction equals the prior status transaction. Lifecycle endpoints additionally require transaction coordinate and namespace to equal the exact publication coordinate and ledger namespace. Recovery resolves the complete resulting status object and validates concrete before/after revision, head, full resulting status object, exact marker object and all its journal/result fields, and staging effects, not only journal enums or marker-presence booleans. Revoked is terminal; history and version bindings are never rewritten.

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

`unknown` always fails publication/adoption. Conditions execute one of `evidence_digest_equals`, `consumer_protocol_at_least`, or `deprecation_interval_at_least` over typed operands; `satisfied` is recomputed. Missing, false, duplicate, or ill-typed evidence fails. Overall SemVer effect is the maximum and arbitrary-length SemVer integers compare as digit strings without bounded-number conversion; the candidate version MUST satisfy the exact patch/minor/major relation. A patch effect requires equal major/minor and a strictly greater patch integer; moving only from prerelease to release (or between prereleases) at the same patch integer is insufficient. Condition IDs form a cardinality-preserving exact reference bijection: every required condition is present and each is referenced by exactly one change; duplicate, shared, and surplus unreferenced conditions reject. `semantic-compatibility-override.v0` embeds and independently digests the exact change, executes a typed true condition, binds a typed owner approval repeating the complete override, preserves at least the source SemVer floor (`unknown` fails closed at `major`), and must appear exactly once in the report's used override set; it cannot legalize identifier reuse, bypass lifecycle, erase conditions, or weaken a SemVer floor.

`semantic-deprecation-record.v0` and `semantic-removal-record.v0` make lifecycle executable. Removal binds the exact prior deprecation and accepted-ledger interval. Both endpoints resolve self-digested accepted lifecycle ledger records, complete published status objects, owner authority and decision chains, transactions, prior status/journal joins, committed journals, fsynced markers, trust roots, and externally observed canonical ledger and lifecycle heads. A candidate lifecycle predecessor must equal the external current lifecycle head; no endpoint or wrapper may supply that canonical default. An accepted-lifecycle wrapper cannot certify any one of those facts itself. Removed and renamed IDs enter append-only `semantic-tombstone-registry.v0`, whose result is exactly every prior entry plus one exact reason/origin and no extras; tombstoned IDs MUST NOT return under any category, including after withdrawal/revocation or override. Owner policy, not ROCS or consumer preference, owns these classifications.

## 9. Consumer adoption chain

### 9.1 Consumer intent

`semantic-consumer-intent.v0` is consumer-owned desired state. It binds stable repository identity/revision, exact release coordinate, independent runtime/tool identity, requested posture, accepted compatibility class, discriminated rollback target, canonical `semantic-ak-decision-reference.v0`, external trust reference, fixed verifier contract, and resource limits. The AK reference binds AK repository/runtime identity, decision ID/revision/lifecycle, accepted ADR identity/revision/digest, scope, revocation, and exact activation target/evidence criteria/rollback plan/stop conditions.

The AK reference includes its canonical store locator, store revision/head, revocation head, decision record, and supersession link; all equal mandatory capability-pinned current AK store receipts supplied to validation. Authority helpers MUST receive both the canonical store head and canonical current decision-record digest and MUST NOT default either from the subject reference. A repository rename updates owner-issued identity revision without changing repository ID. A fork receives a new ID. Fleet reporting aggregates per-repository facts and never replaces them.

Intent is neither technical proof nor consent to activate.

### 9.2 Separate owner acceptance

`semantic-owner-acceptance.v0` binds the exact intent, repository, consumer-owner acceptance authority, revision, governing scope, accepted posture, accepted decision, validity revision, monotonic owner activation-epoch expiry, and revocation link. Its digest and revision MUST equal capability-pinned current consumer-owner acceptance receipts before acceptance, activation, generation, or rollback can authorize. The acceptance issuer MUST be the governing consumer owner, not ROCS, Pi, AK as a tool, or the semantic producer. Missing, stale, inaccessible, expired, rejected, or revoked decisions fail closed. Wall-clock observations remain separately hashed audit envelopes.

Acceptance authorizes only its explicit posture and scope. It does not prove bytes and does not activate them.

### 9.3 Materialization and verification

ROCS emits `semantic-materialization-verification-receipt.v0`, deliberately not an “adoption receipt.” It binds exact intent/acceptance, coordinate, owner approval/publication trust chain, runtime pin, capsule archive linkage, payload projection, source payload manifest, expected and actual complete consumer manifests, repository identity, compatibility report, prior receipt, already available discriminated rollback target, verifier contract, journal state, and durable commit marker. Capsule payload → projection → expected consumer manifest → actual complete tree equality is mandatory; `projection_mismatch` precedes mutation.

ROCS MUST privately stage, fully verify, fsync, atomically replace one materialized-generation pointer, append the receipt outside replaceable roots, and write the durable marker under one lock/journal protocol. Recovery either completes the receipt/marker after pointer replacement or restores the exact prior pointer. Same-digest replay is idempotent; conflicting intent revision fails. Unsupported atomicity causes no mutation.

The receipt claims exact materialization and verification only. It is never owner consent, activation, default authority, or evidence of model use.

### 9.4 Separate activation

`semantic-activation-receipt.v0` resolves the complete intent → unrevoked acceptance → committed rollback-ready materialization → current decision chain. Repository, coordinate, runtime, posture/scope, decision, rollback, valid intent revision, and epoch ceiling bind exactly. It requires a fresh, unexpired owner acceptance whose digest/revision equal the current consumer-owner acceptance receipts, committed materialization receipt, exact coordinate/runtime, accepted canonical AK gate decision, named scope, activation revision, owner-controlled monotonic activation epoch, prior activation, and revocation/supersession links. Its target, evidence criteria, rollback plan, and stop-condition digests MUST exactly equal the canonical AK decision. Its issuer is the consumer owner. Genesis is legal only at revision 1 when canonical pointer digest/revision and prior receipt digest/revision are all null. Every successor resolves a prior receipt whose digest/revision equal the independently read canonical current activation pointer, uses prior revision plus one, and strictly increases epoch. Python and Node normalize absent versus explicit-null previous context identically. The new receipt must itself be `activated`, unrevoked, and unsuperseded; it is validated as a candidate against the prior pointer and MAY become head by CAS only after all validation succeeds.

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

Generation is permitted only when its activation digest/revision equal the current `activated`, unrevoked, unsuperseded activation head and its coordinate/runtime equal that activation byte-for-byte; otherwise it fails `activation_not_current`. ROCS `matched` does not prove prompt delivery. Pi `delivered` requires prompt-run and exact effective-execution digests; `suppressed` requires a closed reason and forbids delivery fields; `failed` requires an error and forbids delivery fields. AK linkage MAY omit Pi only for generation-only lineage. No variant proves model reading, interpretation, obedience, influence, or correctness.

Every derived referenced object is resolved from the digest-indexed proof bundle and every canonical fact from an owner-issued receipt under the externally supplied acquisition configuration. Universal preflight checks I-JSON, closed schema, self-digest, UTF-8 ordering, exact manifest/config/snapshot closure, owner pin/receipt provenance and freshness, exact bundle key, owner repository, expected schema, issuer, and claim scope before its domain rule, including for expected-rejection subjects. An out-of-scope issuer fails with `issuer_scope_violation`; no canonical fact has a subject or context fallback.

## 11. Rollback and recovery

`semantic-rollback-request.v0` binds the current activation, a requester kind/ID exactly equal to the activated repository's consumer owner, an enabled before-state whose coordinate/runtime equal it, a closed axis target, independently pinned recovery controller distinct from active runtime, current canonical owner decision, and preconditions. Its target equals the rollback target in the activated intent and materialization, not merely a same-kind availability proof. Semantic targets switch coordinate and retain runtime; runtime targets retain semantics, switch runtime, and require runtime revalidation; no-prior targets bind tested disable/rehearsal; combined targets embed ordered semantic/runtime stages. ROCS issues `semantic-rollback-availability-proof.v0`. It resolves issuer-bound `semantic-rollback-availability-receipt.v0` objects with non-substitutable ownership: ROCS issues semantic/runtime target availability, the consumer owner issues disable-target availability and every changed `semantic-rollback-history-transition.v0`, and the recovery controller issues only its recovery-runtime availability and final recovery receipt. The objects bind exact coordinate/runtime/materialization/revalidation/disable/rehearsal plus recovery health and independent availability. Every referenced materialization, runtime-revalidation, disable-contract, rehearsal, and health digest resolves to an issuer-scoped `semantic-rollback-technical-receipt.v0`; each binds its exact semantic/runtime/contract subject digest and exact applicable coordinate/runtime. A semantic predecessor receipt must be compatible with and bind the retained activated runtime. The availability wrapper cannot mint its own evidence. `semantic-rollback-receipt.v0` binds result, typed before/after state, monotone per-stage results/errors, exact failed-stage causality, availability proof, typed history heads, overall error, superseded activation, and the exact recovery-controller ID/epoch repeated by the request and availability proof. Controller ID, runtime identity, and epoch equal capability-pinned recovery-controller receipts. Every changed head resolves to `semantic-rollback-history-transition.v0` repeating the canonical before-head, request, states, stages, cause, and supersession.

Rollback axes are independent and MUST be rehearsed independently:

- **semantic:** release N to an already materialized trusted predecessor while runtime stays fixed;
- **runtime:** runtime R to an already materialized prior runtime while semantic N stays fixed, followed by compatibility/materialization revalidation;
- **no prior generation:** disable to the exact pre-adoption behavior;
- **combined/partial failure:** explicit staged recovery under the independent controller with failure receipts.

Targets MUST be locally available before activation. If the active runtime is broken, the recovery controller and target remain usable outside its root. Missing target, recovery runtime, or disable path fails before mutation with `rollback_unavailable`.

Receipt request/target/before-state bind exactly. Complete unique stages equal target order; failed stages alone have errors; after-state is recomputed from completed stages. Failure preserves state/head and never supersedes; partial combined failure has completed+failed stages, recomputed state/new rollback head, and never supersedes; success completes all stages, has no error, appends the correct rollback/disable head, and supersedes exactly the active activation. Disable retains runtime; runtime completion binds exact revalidation. Optional AK/Pi links are jointly absent or exact and activation-bound.

## 12. History, audit, and failure behavior

Publications, approvals, intents, acceptances, materialization/activation/evidence/rollback receipts, errors, revocations, and audit envelopes are immutable and append-only outside replaceable semantic/runtime roots. Supersession and revocation are links, not edits.

Audit time belongs only in `semantic-audit-envelope.v0`, which binds artifact digest, event, issuer, sequence, prior envelope, and strict UTC timestamp under its own digest. UTC is parsed and Gregorian-calendar round-tripped outside JSON Schema's annotation-only format; impossible dates fail `malformed_input`. Re-observation creates another envelope.

Retention is consumer/namespace lifetime plus at least seven years. Garbage collection traces every ledger head, active and rollback target, receipt, audit envelope, revocation, and legal hold before deleting unreferenced blobs. Namespace/version bindings and tombstones are permanent.

Errors use `semantic-protocol-error.v0` and deterministic precedence from `invariants.md`. Both validators inspect raw JSON tokens before object construction: duplicate keys at any depth and any number token outside canonical nonnegative safe-integer grammar reject. UTC accepts only real years `0001..9999`. Precedence is decode/I-JSON, schema, `digest_mismatch`, authority/trust, compatibility/lifecycle, projection/tree, mutation, then rollback availability. Validation is offline/no-network with bounded input, manifests, nesting, and deadlines. Required failures include malformed input, digest mismatch, stale/revoked trust, threshold failure, self-certification, version/publication/fork conflict, snapshot/projection/incomplete tree, compatibility/SemVer/lifecycle rejection, unavailable atomic activation, recovery needed, stale activation, rollback unavailable, history conflict, and issuer-scope violation.

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

Revision v9 closes the revision-v8 rereview blockers in machine architecture evidence: owner-specific acquisition pins and owner-issued store-read receipts replace ambient observations; vote, consumer-acceptance, publication/recovery, rollback, and rollback-history owner/currentness joins are exact; a complete rule-role manifest is bijective with the 92-edge full-tuple registry; and independent Python/Node validators derive closure and mutation cardinality rather than trusting labels. The machine config still states `live_acquisition_implemented=false`. This document supplies none of the later authorizations.

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

The two concrete candidate task contracts below are deliberately separate and **not created or authorized** by this RFC:

| Contract | Repository and allowed paths | Required receipts/evidence | Rollback owner | Stop conditions |
|---|---|---|---|---|
| `decision-53-ak-coordination` | `softwareco/owned/agent-kernel`; `allowed_paths=[]` (canonical AK records only; no worktree mutation) | exact candidate task ID `candidate-decision-53-ak-coordination`, owner/rollback-owner `agent-kernel-owner`, paired typed Decision-53/ADR and implementation/validation-plan prerequisite references; exact immutable dependency/evidence references for Python, Node, docs-strict, deterministic rerun, and rollback rehearsal; `semantic-ak-evidence-linkage.v0` only after its referenced facts exist | AK owner may revoke/supersede coordination references; it cannot withdraw a semantic release or consumer acceptance | stop on stale/revoked/superseded decision, store-head or scope drift, missing owner task, attempted semantic issuance, attempted consumer consent, or any request to treat coordination as authorization |
| `decision-53-first-consumer-canary` | `softwareco/pi-canary-consumer`; only `config/semantic-release/canary.json`, `scripts/ci/semantic-release-canary.sh`, and `docs/project/semantic-release-canary-evidence.md` | exact candidate task ID `candidate-decision-53-first-consumer-canary`, owner/rollback-owner `consumer-owner`, exact dependencies on AK coordination, ROCS implementation, and semantic-owner publication tasks; paired typed Decision-53/ADR/plan/owner-consent prerequisite references; consumer intent and consumer-owner acceptance; exact capsule/archive/projection and materialization receipt; separately accepted canary gate with exact activation-target/evidence/rollback/stop digests; concrete rollback-availability proof, activation receipt, typed rollback history/rehearsal, and bounded canary evidence | repository consumer owner owns deactivation/rollback and may revoke acceptance; semantic owner separately owns withdrawal/revocation | stop before mutation on absent repository-owner consent, unavailable target or recovery runtime, stale trust/AK/activation head, projection or issuer drift, failed validators, unknown/incompatible outcome, missing rollback rehearsal, scope beyond one operator-named canary, or any default/fleet request |

Every prerequisite, dependency, and evidence item is one closed paired reference. A resolved reference carries stable repository identity, claimed canonical AK store head, task ID and record digest, artifact digest, required `accepted_current`, `completed_current`, or `evidence_accepted_current` state, and a separate observed-canonical-state object repeating repository, AK head, task ID/digest, artifact digest, and observed state. That embedded observation must itself occur exactly once in the capability-pinned `canonical_task_states` AK owner-store receipt; claimed, embedded-observed, and receipt facts must agree exactly and the observed state must satisfy the required state. Because these tasks and future artifacts do not exist, this packet uses `unresolved_candidate` references with all store/task/artifact digest fields null; it does not fabricate future digests. Every unresolved reference is assigned to the repository that owns that specific fact (AK, ROCS, semantic owner, or consumer), not to the enclosing task repository. Every RFC stop is a closed condition kind with an exact condition-ID/fact-ID/repository triple and a typed fact reference, `unsatisfied_or_noncurrent` trigger, mandatory `stop_before_mutation` effect, and `accepted_current` resume state. Cross-owner evidence references use the repository that owns the evidence fact: ROCS owns materialization, availability, and rehearsal evidence; AK owns gate-decision evidence; the consumer owns intent/acceptance, activation, canary, and rollback-history evidence. Semantic trust/ledger, AK decision/store, and consumer activation/history stop facts are separate owner-scoped conditions rather than one conflated stale-head condition. The consumer contract additionally machine-binds a stop on any default or fleet request.

The first-consumer posture is exactly one operator-named canary. The AK coordination contract may link owner facts but MUST NOT issue them. The consumer-owner contract may issue repository intent/acceptance/gates but MUST NOT publish semantic facts or use AK linkage as consent. A later authority must create each task separately, preserve these exact task/owner/rollback-owner IDs, repository/path bounds, paired typed dependency/prerequisite/evidence references, and machine stop-condition references, and obtain owner acceptance after the Decision-53 membrane closes. This candidate creates no task, repository consent, implementation authority, canary, default, or rollout authority.

## 15. Non-goals

- online registry or network-dependent validation;
- claiming live owner-capability provisioning or owner-store receipt acquisition in this proposal packet;
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
