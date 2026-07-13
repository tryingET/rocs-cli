---
summary: "Decision:53 semantic-release revision v6 executable closure of rereview-v5 blockers."
read_when:
  - "Reviewing Decision:53 revision v6 or its machine evidence."
type: "revision_note"
status: "proposed"
rfc_revision: "semantic-release-revision-v6"
review_posture: "fresh_review_required"
---
# Semantic Release Revision v6

## Objective and legal posture

This revision closes every finding in [`semantic-release-rereview5-synthesis-v5.md`](semantic-release-rereview5-synthesis-v5.md) and its governance, owner, and ROCS lane memos. It remains proposal-stage architecture evidence. It does not authorize an ADR, implementation, publication, withdrawal, revocation, task creation, consumer consent, activation, default, fleet rollout, or ontology mutation. Decision `53` remains `review_pending` and requires fresh strict review.

## Exact closure and negative-fixture map

| v5 finding | Machine closure | Direct negative fixtures |
|---|---|---|
| Publish authority could bypass threshold/release action; operation approvals did not resolve canonical AK decisions | One publication-authority helper resolves and validates owner policy/set/predicate, current canonical AK decision, exact typed action, action digest, votes, and recomputed threshold for publish/withdraw/revoke. | `publish_requires_threshold_evaluation`; `publish_requires_exact_release_action`; `publish_approval_resolves_canonical_ak_decision`; `withdraw_approval_resolves_canonical_ak_decision`; existing `withdraw_cannot_reuse_release_approval`; `revoke_cannot_reuse_release_approval` |
| Prior journal/status and recovery result/transaction joins were incomplete | Prior journal result digest, revision, and head equal the complete prior status and CAS transaction state. Recovery requires the complete resulting status object's transaction to equal the recovered transaction. | `publication_prior_journal_result_revision_head_bind_prior_status`; `recovery_result_transaction_binds_transaction` |
| Lifecycle accepted endpoints self-certified | Each endpoint now resolves the publication status, transaction, complete authority/decision chain, prior status/journal, committed journal, fsynced marker, trust root, accepted wrapper, and self-digested canonical ledger head. | `lifecycle_endpoint_cannot_self_certify_publication`; existing `lifecycle_requires_accepted_current_ledger_heads`; `lifecycle_referenced_ledger_self_digest_checked` |
| Rollback availability was self-minted | Availability artifacts are issuer-bound `semantic-rollback-availability-receipt.v0` objects. Every materialization, runtime-revalidation, disable-contract, rehearsal, and health reference resolves to an issuer-scoped typed technical receipt and exact subject chain. | `rollback_availability_receipt_requires_issuer`; `rollback_resolves_typed_materialization_receipt_issuer`; `rollback_binds_technical_receipt_issuer_id`; existing target/recovery drift and self-digest fixtures |
| Activation omitted concrete rollback, issuer ID, and continuity | Activation binds consumer-owner issuer ID, intent, acceptance/acceptance epoch, materialization, concrete availability proof, decision, genesis-or-prior+1 revision, exact current/prior head, and monotonic bounded epoch. | `activation_binds_consumer_owner_issuer_id`; `activation_revision_requires_genesis_or_prior_plus_one`; `activation_current_head_equals_exact_prior`; `activation_epoch_is_monotonic_from_acceptance`; `activation_binds_concrete_rollback_availability` |
| Primitive contexts diverged; SemVer was prefix-accepted; approval-map key drift passed | Bare context integers are bool-safe and bounded in both validators; complete anchored SemVer 2.0.0 grammar and precedence are independently implemented; approval-map key must equal the resolved approval self-digest. | `primitive_context_integer_rejects_boolean`; `semver_subject_requires_exact_full_grammar`; `semver_context_requires_exact_full_grammar`; `approval_map_key_equals_value_digest`; existing bool/large-SemVer fixtures |
| Task IDs/digests were unpaired placeholders; dependencies/evidence/stops were labels | Arrays are replaced by closed paired typed references. Resolved references carry repository, AK store head, task record, artifact digest, and required current state. Future candidates are explicitly unresolved with null store/task/artifact fields. Every RFC stop has typed fact, trigger, stop-before-mutation effect, and resume state, including default/fleet escalation. | `task_contract_binds_exact_dependency_ids`; `task_contract_binds_exact_prerequisite_ids`; `task_contract_rejects_synthetic_future_artifact_digest`; `task_contract_binds_required_reference_state`; `task_contract_binds_exact_evidence_list`; `task_contract_binds_exact_stop_conditions`; `task_contract_machine_binds_stop_semantics`; `unresolved_candidate_cannot_claim_synthetic_task_artifacts` |

## Generated packet

Revision v6 contains 44 closed protocol types, 101 canonical object preimages, 2 raw preimages, 28 exact digest links, 208 differential cases, and 8 raw lexical cases. Python and Node independently validate schema closure, primitive contexts, full SemVer, canonical preimages, digests, references, authority chains, lifecycle, activation, rollback, and governance contracts. `schema_builder.py` and `generate_fixtures.py` are the only generated-JSON writers and run offline.

## Validation record

Run from the repository root:

```text
python docs/project/semantic-release-v0/validate_fixtures.py
  PASS — 44 types; 101 objects; 28 links; 208 differential cases (45 accepted, 163 rejected); 8 raw cases
node docs/project/semantic-release-v0/validate_fixtures.mjs
  PASS — same independently recomputed corpus
python docs/project/semantic-release-v0/generate_fixtures.py (twice) plus SHA-256 comparison
  PASS — generated artifacts converge byte-for-byte
node ~/ai-society/core/agent-scripts/scripts/docs-list.mjs --docs . --strict
  PASS
./scripts/ci/full.sh
  PASS
git diff --check
  PASS
```

## Residual risks

- v0 still uses externally pinned local trust roots; signing/key-distribution infrastructure remains out of scope.
- Fixtures and validators establish architecture-contract consistency, not filesystem crash behavior or production authorization.
- All candidate task and future evidence references deliberately remain unresolved; a later authorized owner must resolve them against canonical AK state without changing required semantics.
