---
summary: "Decision:53 semantic-release revision v9 capability-pinned owner receipts, closed rule-role manifest, and independent differential conformance."
read_when:
  - "Reviewing Decision:53 revision v9, revision-v8 rereview closure, or the machine packet."
type: "revision_note"
status: "proposed"
rfc_revision: "semantic-release-revision-v9"
review_posture: "fresh_review_required"
---
# Semantic Release Revision v9

## Objective and legal posture

Revision v9 implements contextual dominance as selected by [`semantic-release-many-of-the-greats-conflict-resolution-v9.md`](semantic-release-many-of-the-greats-conflict-resolution-v9.md) and answers the controlling [`semantic-release-rereview8-synthesis-v8.md`](semantic-release-rereview8-synthesis-v8.md) plus its completed governance, owner, and ROCS lanes.

This is proposal-stage architecture and deterministic conformance evidence only. It does not accept an ADR or authorize implementation, capability provisioning, owner-store acquisition, publication, withdrawal, revocation, task creation, consumer consent, activation, a default, fleet rollout, or ontology mutation. The checked machine configuration requires `live_acquisition_implemented=false`; live owner capability distribution, authenticated reads, and action-time operation remain later owner-authorized work. Decision `53` remains `review_pending` until the RFC membrane closes.

## Capability-pinned owner receipts

Revision v9 replaces the revision-v8 ambient observation model and generic context facts with four closed invocation objects plus one normative manifest:

- `semantic-authority-acquisition-config.v0` contains owner-specific `semantic-owner-acquisition-capability-pin.v0` objects. Each pin closes role, category, owner surface/ID, complete repository identity, acquisition contract and distribution, store ID/head/revision, typed fact/digest, freshness CAS token, and action floor.
- `semantic-authority-snapshot.v0` contains only owner-issued `semantic-owner-store-read-receipt.v0` objects. A receipt repeats its complete pin and current read. The ROCS collator is transport-only, cannot issue a receipt, and must differ from every receipt issuer.
- `semantic-authority-proof-bundle.v0` stores derived artifacts under recomputed digest keys and repeats complete owner repository identity, schema, issuer, and claim scope.
- `semantic-authority-verifier-input.v0` binds the exact subject, manifest/config/snapshot/bundle digests, action floor, receipt/node/parameter bindings, complete role set, observation set, and edge set.
- `semantic-authority-rule-role-manifest.v0` closes all 23 rules, exactly 16 authority-bearing rules, and 277 static/prefix role mappings with source, category, owner, repository, capability, schema, cardinality, and edge coverage.

Receipt fact digests and freshness tokens are independently recomputed. Receipt observation IDs equal receipt bindings, capability IDs equal configured pins, proof keys equal node bindings, and receipt/node/parameter roles are disjoint with an exact manifest-constrained union. Missing, duplicate, contradictory, recategorized, or surplus material rejects. No canonical value has a subject, proof-node, generic-context, empty-value, or validator default.

The terminal trust boundary is explicit rather than recursive: verifier configuration trusts named owner-specific local acquisition capabilities. That trust does not grant the collator any owner's issuance power. The generated packet emulates closed receipts for deterministic review; it is not evidence that live capabilities or reads exist.

## Exact revision-v8 blocker closure

| Controlling revision-v8 blocker | Revision-v9 closure | Direct rejection fixtures |
|---|---|---|
| The snapshot assembler could reassign categories or issue cross-owner facts; repository/head/revision did not constrain fact values. | Owner-specific pins and owner-issued receipts bind exact role/category/owner/repository/contract/distribution/store/fact/freshness tuples. The collator is transport-only. Pin/receipt/config/binding and action-floor joins are exact. | `authority_receipt_category_substitution_rejected`; `authority_receipt_repository_identity_is_exact`; `authority_receipt_owner_specific_pin_is_exact`; `authority_receipt_head_revision_fact_binding_is_exact`; `authority_receipt_freshness_cas_floor_is_enforced`; `authority_collator_cannot_issue_receipts`; `authority_acquisition_distribution_digest_is_exact` |
| Surplus observations/roles and contradictory duplicates could pass; generic context and generator labels acted as ambient authority. | Snapshot receipts, config pins, verifier observation IDs, and receipt/node/parameter roles have exact set closure. Duplicate/conflicting and surplus receipt/role mutations reject. Generic authority context artifacts and fixture edge/drift labels are absent. | `authority_snapshot_surplus_receipt_rejected`; `authority_snapshot_duplicate_conflicting_receipt_rejected`; `authority_verifier_surplus_role_rejected` |
| Vote proofs were opaque and not capability-authenticated. | Every approval vote resolves one voter-specific semantic-owner receipt whose owner/key/action/proof tuple equals the vote and whose pin is owner-specific. | `owner_vote_proof_requires_pinned_owner_capability` |
| Consumer acceptance currentness was incomplete. | Acceptance digest and revision equal capability-pinned current consumer-owner acceptance receipts in acceptance, activation, generation, and rollback chains. | `consumer_acceptance_must_equal_current_owner_head` |
| Publication and recovery were not anchored to canonical ledger state. | Publish/transition expected prior revision/head and prior journal equal semantic-owner publication receipts. Recovery before-state revision/head and prior journal equal canonical publication/recovery receipts. | `publication_commit_requires_canonical_publication_head`; `publication_transition_requires_canonical_publication_head`; `publication_recovery_requires_canonical_ledger_head` |
| Rollback availability/history owners conflicted and rollback-owner kind was substitutable. | ROCS owns the aggregate availability proof and semantic/runtime target availability; the consumer owner owns disable-target availability and history transitions; the recovery controller owns only recovery-runtime availability/final recovery. Task rollback owner kind and ID equal the owning surface. | `rollback_availability_proof_has_rocs_owner`; `rollback_history_transition_has_consumer_owner`; `task_contract_binds_exact_rollback_owner_kind` |
| Six authority-bearing rules were absent from finite coverage and the inventory was incomplete. | The manifest classifies all authority-bearing rules; every one has registry edges. New coverage includes acceptance, AK decision, generation, publication CAS/transition, and permanent version binding. | `consumer_acceptance_must_equal_current_owner_head`; `ak_store_head_stale_rejected`; `generation_from_nonhead_activation_rejected`; `publication_stale_cas_rejected`; `publication_fork_rejected`; `status_transition_prior_journal_drift_rejected`; `namespace_version_digest_reuse_conflicts` |
| Node ignored registry integrity and owner/cardinality/drift claims were labels. | Python and Node independently hard-pin full manifest/registry digests, validate complete owner/repository/cardinality/linkage tuples, enforce manifest↔registry bijection, execute every witness/drift, mechanically count each drift fixture once, and compare semantic case digests. | Validator-level full-tuple, bijection, linkage, cardinality, and semantic-mutation gates over all 92 rows |

The corpus adds 19 cases: one accepted permanent version-binding witness and 18 direct rejections. Existing accepted witnesses are reused where a newly registered edge already had a direct negative. The registry grows by 24 edges from 68 to 92 while preserving finite one-drift coverage.

## Complete authority registry

The 92 rows cover every authority-bearing rule:

| Rule | Edges |
|---|---:|
| `acceptance_binding` | 1 |
| `activation_binding` | 5 |
| `ak_decision` | 1 |
| `approval_threshold` | 1 |
| `compatibility` | 2 |
| `generation_activation` | 1 |
| `governance_contracts` | 13 |
| `lifecycle` | 5 |
| `publication_cas` | 2 |
| `publication_commit` | 27 |
| `publication_recovery` | 6 |
| `publication_transition` | 2 |
| `rollback` | 10 |
| `trust_revocation` | 6 |
| `trust_rotation` | 9 |
| `version_binding` | 1 |
| **Total** | **92** |

Every row carries exact owner surface, owner ID, complete repository identity, positive/drift cardinality, expected error, and a recomputed drift-link digest. The manifest edge union equals the registry exactly once. A future review may still identify a missing semantic edge, but a listed edge or role cannot silently disappear, change owner, duplicate its drift, or diverge between languages.

## Generated packet and validation record

Revision v9 contains exactly 51 closed protocol types, 106 canonical object preimages, 2 raw preimages, 34 exact digest links, 23 manifest rules, 277 role mappings, 92 authority edges, 281 differential cases (48 accepted transitions and 233 expected rejections), and 8 raw lexical cases (2 accepted and 6 expected rejections).

Deterministic regeneration was run twice from the repository root and converged byte-for-byte:

```text
protocol.schema.json       e8ac737ded6c4664f29a45ae645d923a4f1d55fdbf201ce6df5fd0332a129d4e
golden-fixtures.json       dd4810fe0f6fb42000510980a11e9f13885cd03d1ec56a2e53e0254619650e14
differential-fixtures.json fc92f040b5be583d7162591541350311e83186c015a3b734d83958e19e51dc6a
```

Both validators independently report the same corpus and authority closure:

```text
51 protocol types; 106 objects + 2 raw preimages; 34 links
23 manifest rules; 16 authority-bearing; 277 role mappings
92 full-tuple authority edges; manifest/registry bijection complete
281 cases: 48 accepted, 233 rejected; 8 raw cases: 2 accepted, 6 rejected
```

Repository gates are recorded only after they run on this exact packet; passing fixture validators does not claim live acquisition or production behavior.

## Coverage limits

- The finite registry proves execution and one-drift cardinality for the 92 declared edges; fresh strict review still owns semantic completeness and owner-correctness judgment.
- Pin and receipt fixtures prove closed deterministic contracts, not authentication infrastructure, live capability distribution, actual owner-store reads, action-time races, or production crash behavior.
- Signing/key distribution, live freshness policy, deployment, and operational rollback remain later owner-authorized implementation concerns.
- Candidate tasks and future evidence remain unresolved. No AK record, task, decision state, ontology, runtime source, lockfile, or commit is mutated by this documentation revision.
