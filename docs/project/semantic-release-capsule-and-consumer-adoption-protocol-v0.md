---
summary: "Cross-owner RFC for immutable semantic release publication, consumer materialization and activation, bounded evidence, and independent rollback."
read_when:
  - "Defining production semantic identity for ROCS consumers."
  - "Reviewing the production dependency of decision:52."
type: "rfc"
status: "proposed"
decision: "53"
rfc_revision: "semantic-release-revision-v4"
review_posture: "fresh_review_required"
---

# RFC — Semantic Release Capsule and Consumer Adoption Protocol v0

## 1. Status and legal effect

This revision answers the finite closure blockers in the controlling [`semantic-release-rereview3-synthesis-v3.md`](semantic-release-rereview3-synthesis-v3.md) for decision `53`. It is a proposal-stage protocol packet submitted for fresh strict review, not an ADR, owner approval, implementation plan, publication, adoption, activation, default decision, fleet decision, or ontology mutation.

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

`semantic-release-capsule.v0` binds namespace/version, source and semantic payload identities, compiled payload manifest, exact payload projection, capsule archive linkage, owner/compilation policies, executable compatibility report, protocol versions, predecessor, and tombstones. Archive identity is acyclic: capsule → linkage → archive manifest plus closed metadata that excludes capsule/archive/linkage digests. The metadata raw JCS digest/length equal its archive entry. Projection source and destination paths are separately unique and their sets equal all payload and consumer entries, yielding a complete no-extra/no-missing bijection with mode/length/content equality. The archive set is exactly metadata, payload root, and prefixed payload entries; extra archive entries reject. The capsule digest omits only `capsule_digest` and retains every nested digest.

The predecessor is the immediately prior accepted active coordinate in the namespace publication ledger. Genesis alone has no predecessor. A capsule is immutable; corrections require a new version and digest.

## 6. Owner issuance and local trust

### 6.1 Owner approval

The semantic owner MUST maintain closed, immutable `semantic-owner-policy.v0`, `semantic-owner-set.v0`, `semantic-approval-predicate.v0`, `semantic-compatibility-policy.v0`, `semantic-trust-root.v0`, `semantic-trust-rotation.v0`, `semantic-trust-revocation.v0`, and namespace-ledger records on its own surface. The policy binds governing scope, exact set/predicate/policy digests, prior policy, old-root-authorized rotation, and fail-closed revocation.

The owner set pins each member's keys and active/revoked state. `threshold` counts distinct eligible active owners and lies within the active count; `unanimous` requires every active owner **and** `threshold` equal that count. Multiple keys never multiply an owner. Revoked vote is `trust_revoked`; unauthorized, duplicate, insufficient, or unanimous-threshold drift is `approval_threshold_unsatisfied`.

`semantic-owner-approval.v0` binds one exactly equal namespace/policy/set/predicate chain, canonical AK decision, and one closed typed action (`release`, `trust_rotation`, `trust_revocation`, or `compatibility_override`). The action digest is recomputed and every vote binds it. Rotation/revocation actions repeat exact namespace/policy/set/predicate/root/target/prior-head/revision facts; release repeats clean source/capsule/report; override repeats exact change/effect/condition. The predicate is recomputed. ROCS, AK, Pi, and consumer votes cannot substitute for semantic-owner approval.

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

Publication is an executable acyclic four-object protocol: transaction → resulting publication/status record → journal → commit marker. A transaction binds operation, coordinate, approval, expected prior revision/head, replay key, and status reason. Publication MUST acquire the namespace lock, verify all bindings, privately stage complete immutable blobs/record, fsync content/directories/journal, CAS one durable ledger head, and append/fsync its commit marker.

The durable head CAS is the linearization point. A stale revision is `publication_conflict`; a divergent expected head is `publication_fork`; reused version/different digest is `version_conflict`. None mutates state. Same coordinate/replay key is idempotent and returns the existing publication.

The closed journal combinations are prepared/not-linearized/discard, committing/linearized/complete, committed/linearized/none, and aborted/not-linearized/discard. Recovery before linearization discards staging; recovery after it completes record/marker idempotently. Impossible combinations return `recovery_needed`.

`semantic-publication-status-transition.v0` admits only published→withdrawn, published→revoked, and withdrawn→revoked. A resulting record binds transaction/prior status without backward journal/marker links; journal and marker each bind that exact transition digest as resulting head/revision. The prior status object and prior journal head are resolved exactly. Recovery validates concrete before/after revision, head, full resulting status object, exact marker object and all its journal/result fields, and staging effects, not only journal enums or marker-presence booleans. Revoked is terminal; history and version bindings are never rewritten.

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

`unknown` always fails publication/adoption. Conditions execute one of `evidence_digest_equals`, `consumer_protocol_at_least`, or `deprecation_interval_at_least` over typed operands; `satisfied` is recomputed. Missing, false, duplicate, or ill-typed evidence fails. Overall SemVer effect is the maximum and the candidate version MUST satisfy the exact patch/minor/major relation. Condition IDs form a cardinality-preserving exact reference bijection: every required condition is present and each is referenced by exactly one change; duplicate, shared, and surplus unreferenced conditions reject. `semantic-compatibility-override.v0` embeds and independently digests the exact change, executes a typed true condition, binds a typed owner approval repeating the complete override, preserves at least the source SemVer floor (`unknown` fails closed at `major`), and must appear exactly once in the report's used override set; it cannot legalize identifier reuse, bypass lifecycle, erase conditions, or weaken a SemVer floor.

`semantic-deprecation-record.v0` and `semantic-removal-record.v0` make lifecycle executable. Removal binds the exact prior deprecation and accepted-ledger interval. Removed and renamed IDs enter append-only `semantic-tombstone-registry.v0`, whose result is exactly every prior entry plus one exact reason/origin and no extras; tombstoned IDs MUST NOT return under any category, including after withdrawal/revocation or override. Owner policy, not ROCS or consumer preference, owns these classifications.

## 9. Consumer adoption chain

### 9.1 Consumer intent

`semantic-consumer-intent.v0` is consumer-owned desired state. It binds stable repository identity/revision, exact release coordinate, independent runtime/tool identity, requested posture, accepted compatibility class, discriminated rollback target, canonical `semantic-ak-decision-reference.v0`, external trust reference, fixed verifier contract, and resource limits. The AK reference binds AK repository/runtime identity, decision ID/revision/lifecycle, accepted ADR identity/revision/digest, scope, revocation, and exact activation target/evidence criteria/rollback plan/stop conditions.

The AK reference includes its canonical store locator, store revision/head, revocation head, decision record, and supersession link; all equal an independent current-store read. A repository rename updates owner-issued identity revision without changing repository ID. A fork receives a new ID. Fleet reporting aggregates per-repository facts and never replaces them.

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

Generation is permitted only when its activation digest/revision equal the current `activated`, unrevoked, unsuperseded activation head and its coordinate/runtime equal that activation byte-for-byte; otherwise it fails `activation_not_current`. ROCS `matched` does not prove prompt delivery. Pi `delivered` requires prompt-run and exact effective-execution digests; `suppressed` requires a closed reason and forbids delivery fields; `failed` requires an error and forbids delivery fields. AK linkage MAY omit Pi only for generation-only lineage. No variant proves model reading, interpretation, obedience, influence, or correctness.

Issuer kind and fixed `claim_scope` are schema-bound and enforced for every structurally valid subject before its domain rule, including expected-rejection subjects. An out-of-scope issuer fails with `issuer_scope_violation`.

## 11. Rollback and recovery

`semantic-rollback-request.v0` binds the current activation, an enabled before-state whose coordinate/runtime equal it, a closed axis target, independently pinned recovery controller distinct from active runtime, current canonical owner decision, and preconditions. Semantic targets switch coordinate and retain runtime; runtime targets retain semantics, switch runtime, and require runtime revalidation; no-prior targets bind tested disable/rehearsal; combined targets embed ordered semantic/runtime stages. `semantic-rollback-availability-proof.v0` resolves the concrete target materialization/revalidation/disable facts, canonical activation, and usable recovery runtime. `semantic-rollback-receipt.v0` binds result, typed before/after state, monotone per-stage results/errors, exact failed-stage causality, availability proof, typed history heads, overall error, and superseded activation. Every changed head resolves to `semantic-rollback-history-transition.v0` repeating the canonical before-head, request, states, stages, cause, and supersession.

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

The two concrete candidate task contracts below are deliberately separate and **not created or authorized** by this RFC:

| Contract | Repository and allowed paths | Required receipts/evidence | Rollback owner | Stop conditions |
|---|---|---|---|---|
| `decision-53-ak-coordination` | `softwareco/owned/agent-kernel`; `allowed_paths=[]` (canonical AK records only; no worktree mutation) | current accepted Decision-53/ADR reference; immutable references to each owner task and consent; evidence records for Python, Node, docs-strict, deterministic rerun, and rollback rehearsal; `semantic-ak-evidence-linkage.v0` only after its referenced facts exist | AK owner may revoke/supersede coordination references; it cannot withdraw a semantic release or consumer acceptance | stop on stale/revoked/superseded decision, store-head or scope drift, missing owner task, attempted semantic issuance, attempted consumer consent, or any request to treat coordination as authorization |
| `decision-53-first-consumer-canary` | `softwareco/pi-canary-consumer`; only `config/semantic-release/canary.json`, `scripts/ci/semantic-release-canary.sh`, and `docs/project/semantic-release-canary-evidence.md` | consumer intent and consumer-owner acceptance; exact capsule/archive/projection and materialization receipt; separately accepted canary gate with exact activation-target/evidence/rollback/stop digests; concrete rollback-availability proof, activation receipt, typed rollback history/rehearsal, and bounded canary evidence | repository consumer owner owns deactivation/rollback and may revoke acceptance; semantic owner separately owns withdrawal/revocation | stop before mutation on absent repository-owner consent, unavailable target or recovery runtime, stale trust/AK/activation head, projection or issuer drift, failed validators, unknown/incompatible outcome, missing rollback rehearsal, scope beyond one operator-named canary, or any default/fleet request |

The first-consumer posture is exactly one operator-named canary. The AK coordination contract may link owner facts but MUST NOT issue them. The consumer-owner contract may issue repository intent/acceptance/gates but MUST NOT publish semantic facts or use AK linkage as consent. A later authority must create each task separately, preserve these repository/path bounds and stop conditions, and obtain owner acceptance after the Decision-53 membrane closes. This candidate creates no task, repository consent, implementation authority, canary, default, or rollout authority.

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
