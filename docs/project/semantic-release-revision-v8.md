---
summary: "Decision:53 semantic-release revision v8 externally anchored authority-proof closure and finite edge coverage."
read_when:
  - "Reviewing Decision:53 revision v8, its v7 blocker closure, or its machine evidence."
type: "revision_note"
status: "proposed"
rfc_revision: "semantic-release-revision-v8"
review_posture: "fresh_review_required"
---
# Semantic Release Revision v8

## Objective and legal posture

Revision v8 implements the architecture selected by [`semantic-release-many-of-the-greats-conflict-resolution-v8.md`](semantic-release-many-of-the-greats-conflict-resolution-v8.md) and closes every finite blocker in [`semantic-release-rereview7-synthesis-v7.md`](semantic-release-rereview7-synthesis-v7.md) and its completed governance and owner lanes. The v7 ROCS review lane was externally blocked, so no ROCS review outcome is inferred and fresh strict review remains required.

This is proposal-stage architecture evidence only. It does not accept an ADR or authorize implementation, publication, withdrawal, revocation, task creation, consumer consent, activation, a default, fleet rollout, or ontology mutation. Decision `53` remains `review_pending` until the legal membrane in the RFC closes.

## Externally Anchored Authority Proof Graph

Revision v8 replaces rule-local caller context with three closed protocol objects:

- `semantic-authority-snapshot.v0` supplies externally acquired, owner-scoped observations for semantic trust/revocation/ledgers, AK stores/decisions/tasks, consumer activation/history, and recovery-controller identity/runtime/epoch. Its digest identifies the invocation but does not certify truth, and a snapshot cannot be a candidate-issued proof node.
- `semantic-authority-proof-bundle.v0` stores every derived rule input under its recomputed artifact digest with an explicit schema, issuer, and claim scope.
- `semantic-authority-verifier-input.v0` binds the exact rule/subject, snapshot, proof bundle, anchor/node roles, expected schemas and issuers/scopes, and complete required-edge set.

One universal preflight validates raw I-JSON, closed shape, self-digests, normative order, exact subject/snapshot/bundle joins, bundle-key equality, complete node resolution, expected schema, issuer/claim scope, and complete required anchors/edges before any domain rule. Domain rules consume only resolved nodes and explicit anchors. Canonical AK, trust/revocation/ledger, activation/history, recovery, and task facts have no subject or context fallback; missing and surplus authority material both reject.

Historical integrity remains separate from current authorization. External heads and revocation observations may make an immutable historical receipt unusable without denying its historical identity.

## Exact v7 blocker closure

| Controlling v7 blocker | Revision-v8 closure | Direct rejection fixtures |
|---|---|---|
| Independent canonical AK facts were not required for every authority-bearing approval | Rotation, revocation, and compatibility-override rules resolve the approval's decision against independent AK store-head and current-record snapshot anchors; no subject default remains. | `rotation_requires_independent_ak_store_observation`; `rotation_requires_independent_ak_current_record`; `revocation_requires_independent_ak_store_observation`; `revocation_requires_independent_ak_current_record`; `override_requires_independent_ak_store_observation`; `override_requires_independent_ak_current_record` |
| Publication omitted external trust-revocation state and recovery authority joins | Publication rejects roots in the external revoked-digest set. Recovery journal controller ID, runtime identity, and epoch equal external recovery observations. | `publication_rejects_externally_revoked_trust_root`; `publication_recovery_controller_is_exact`; `publication_recovery_runtime_is_exact`; `publication_recovery_epoch_is_exact` |
| Lifecycle prior-head, activation candidate state, rollback controller, and availability epoch joins were incomplete | Lifecycle candidate predecessor equals the external lifecycle head; an activation candidate is unrevoked and unsuperseded before CAS; rollback request/proof/receipt controller and epoch equal external recovery observations. | `lifecycle_current_prior_head_is_external`; `activation_candidate_must_be_unrevoked`; `activation_candidate_must_be_unsuperseded`; `rollback_controller_equals_external_recovery_observation`; `rollback_epoch_equals_external_recovery_observation` |
| Embedded task observations were not compared with independent AK facts | Every resolved task reference's claimed and embedded-observed fields equal a separately anchored AK task snapshot observation. | `resolved_governance_reference_compares_independent_snapshot` |
| Evidence references used enclosing rather than fact owners, and one stale-head stop conflated owner surfaces | Materialization/availability/rehearsal evidence is ROCS-owned, gate evidence is AK-owned, and consumer facts remain consumer-owned. Semantic trust/ledger, AK decision/store, and consumer activation/history stops are separate exact owner-scoped facts. | `governance_evidence_reference_uses_fact_owner`; `semantic_stop_fact_has_semantic_owner`; `ak_stop_fact_has_ak_owner`; `consumer_stop_fact_has_consumer_owner` |

Those 20 direct negatives close the v7 findings. Eight additional preflight negatives cover snapshot self-digest, bundle-key equality, missing node, surplus node, expected schema, issuer/scope, required anchor, and normative order: `authority_snapshot_self_digest_is_universal`, `authority_bundle_key_equals_artifact_digest`, `authority_bundle_missing_node_fails_closed`, `authority_bundle_surplus_node_fails_closed`, `authority_node_expected_schema_is_exact`, `authority_node_issuer_scope_is_exact`, `authority_required_anchor_is_mandatory`, and `authority_preflight_order_is_normative`. Together they account exactly for the corpus increase from 234 to 262 cases; accepted cases remain 47 and expected rejections increase from 187 to 215.

## Exact finite-edge coverage

`differential-fixtures.json` carries 68 UTF-8-sorted authority-edge rows. Every row names its rule, owner surface, accepted witness, one direct drift fixture, and expected error. Both validators require exact registry identity/cardinality, require each drift to carry its edge ID and `authority_edge_drift_count: 1`, and execute the accepted witness and rejection.

| Rule | Edges | Exact edge IDs |
|---|---:|---|
| `activation_binding` | 5 | `activation.candidate-not-head`, `activation.candidate-unrevoked`, `activation.candidate-unsuperseded`, `activation.pointer-digest`, `activation.pointer-pair` |
| `compatibility` | 2 | `compatibility-override.ak-current-record`, `compatibility-override.ak-store` |
| `governance_contracts` | 12 | `governance.ak-stop-owner`, `governance.consumer-stop-owner`, `governance.evidence-owner`, `governance.independent-task-snapshot`, `governance.reference-owner`, `governance.semantic-stop-owner`, `governance.stop-condition`, `governance.stop-fact`, `governance.stop-owner`, `governance.task-record`, `governance.task-state`, `governance.task-store` |
| `lifecycle` | 5 | `lifecycle.current-ledger-head`, `lifecycle.external-prior-head`, `lifecycle.prior-head`, `lifecycle.transaction-coordinate`, `lifecycle.transaction-namespace` |
| `publication_commit` | 16 | `preflight.bundle-key`, `preflight.expected-schema`, `preflight.issuer-scope`, `preflight.missing-node`, `preflight.normative-order`, `preflight.required-anchor`, `preflight.snapshot-self-digest`, `preflight.surplus-node`, `publication.ak-current-record`, `publication.ak-store`, `publication.external-pin`, `publication.prior-journal-transaction`, `publication.trust-namespace`, `publication.trust-owner-set`, `publication.trust-policy`, `publication.trust-revocation` |
| `publication_recovery` | 5 | `recovery.controller`, `recovery.epoch`, `recovery.marker`, `recovery.result-transaction`, `recovery.runtime` |
| `rollback` | 8 | `rollback.controller`, `rollback.epoch`, `rollback.history-head`, `rollback.requester`, `rollback.target`, `rollback.technical-coordinate`, `rollback.technical-runtime`, `rollback.technical-subject` |
| `trust_revocation` | 6 | `trust-revocation.ak-current-record`, `trust-revocation.ak-store`, `trust-revocation.approval`, `trust-revocation.authority-chain`, `trust-revocation.prior-head`, `trust-revocation.revision` |
| `trust_rotation` | 9 | `trust-rotation.ak-current-record`, `trust-rotation.ak-store`, `trust-rotation.approval`, `trust-rotation.current-root`, `trust-rotation.namespace`, `trust-rotation.owner-set`, `trust-rotation.predicate`, `trust-rotation.revision`, `trust-rotation.unrevoked` |
| **Total** | **68** | **68 unique registered edges** |

## Generated packet and validation record

Revision v8 contains exactly 48 closed protocol types, 104 canonical object preimages, 2 raw preimages, 31 exact digest links, 68 authority edges, 262 differential cases (47 accepted transitions and 215 expected rejections), and 8 raw lexical cases (2 accepted and 6 expected rejections). The four new protocol types are the snapshot, context fact, proof bundle, and verifier input; the three new golden objects and three new links bind the accepted snapshot → bundle → verifier-input proof graph.

Run from the repository root:

```text
python docs/project/semantic-release-v0/generate_fixtures.py (twice) plus SHA-256 comparison
  PASS — converged byte-for-byte
  protocol.schema.json      49c0a00182f6e826474ffebc30652e259a6656f881f0ccbf23544413e3252202
  golden-fixtures.json      3490a559e234135af71e50b9c3f958402ae942e0419af432ab9d70273836c83d
  differential-fixtures.json d0906a7bccec29194f84785d4719b3769bc5b419ddd8f66c5df7a9175d8b0ad6
python docs/project/semantic-release-v0/validate_fixtures.py
  PASS — 48 types; 104 objects + 2 raw preimages; 31 links; 68 edges; 262 cases (47 accepted, 215 rejected); 8 raw cases
node docs/project/semantic-release-v0/validate_fixtures.mjs
  PASS — same independently recomputed corpus; no Python import or subprocess
node ~/ai-society/core/agent-scripts/scripts/docs-list.mjs --docs . --strict
  PASS
./scripts/ci/full.sh
  PASS
git diff --check
  PASS
```

## Coverage limits

- The finite registry proves complete execution of the 68 declared authority edges; it does not prove that no future review can identify a missing edge. Fresh strict review must assess registry completeness and owner correctness.
- Snapshot acquisition, live freshness policy, signing/key distribution, production crash behavior, and operational deployment remain later owner-authorized implementation concerns.
- Fixtures establish deterministic architecture-contract agreement, not production authorization or empirical runtime behavior.
- Candidate tasks and future evidence remain unresolved. No AK record, task, decision state, ontology, runtime source, lockfile, test tree, or commit is mutated by this documentation revision.
