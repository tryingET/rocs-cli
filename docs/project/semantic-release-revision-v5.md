---
summary: "Decision:53 semantic-release revision v5 executable closure of rereview-v4 blockers."
read_when:
  - "Reviewing Decision:53 revision v5 or its machine evidence."
type: "revision_note"
status: "proposed"
rfc_revision: "semantic-release-revision-v5"
review_posture: "fresh_review_required"
---
# Semantic Release Revision v5

## Objective and legal posture

This revision closes the finite blocker list in [`semantic-release-rereview4-synthesis-v4.md`](semantic-release-rereview4-synthesis-v4.md) and its three lane memos with closed shapes, independent context validation, and adversarial fixtures. It does not authorize an ADR, implementation, publication, withdrawal, revocation, adoption, activation, task creation, default, fleet rollout, or ontology mutation. Decision `53` remains subject to fresh strict review and the RFC membrane.

## Exact closure map

| v4 finding | Machine closure | Adversarial fixtures |
|---|---|---|
| Withdraw/revoke reused release approval | Added closed `publication_withdrawal` and `publication_revocation` actions. Each repeats namespace, policy/set/predicate, coordinate, complete prior status reference, operation, reason, expected revision/head, and passes the owner threshold. | `withdraw_cannot_reuse_release_approval`, `revoke_cannot_reuse_release_approval`, `withdraw_approval_binds_exact_operation_reason_and_cas` |
| Trust-revocation action lacked full authority | Trust-revocation actions now repeat namespace and exact policy/set/predicate digests in addition to every target/prior/reason/revision field. | `trust_revocation_action_requires_full_authority_chain` |
| Referenced contexts were trusted relationally | Both validators run `expected_context`/`expectedContext` and nested-shape helpers before relational rules: I-JSON, closed schema, expected type, self-digest, ordering, issuer, then expected reference. | `referenced_owner_set_stale_self_digest_rejected`, `referenced_policy_expected_type_rejected`, `referenced_context_order_validated_before_relation`, `publication_prior_status_context_self_digest_checked`, `recovery_result_context_self_digest_checked`, `activation_resolves_acceptance_self_digest`, `activation_context_issuer_checked_before_relation`, `lifecycle_referenced_ledger_self_digest_checked`, `rollback_target_artifact_self_digest_checked` |
| Activation legality did not resolve its chain | Activation resolves intent, acceptance, materialization, and current AK decision; repository, coordinate, runtime, posture/scope, decision, rollback, valid intent revision, epoch ceiling, revocation, issuer, and committed/rollback-ready state bind exactly. Generation and rollback reuse the same chain check. | `activation_requires_valid_intent_revision`, `activation_epoch_respects_acceptance_ceiling`, `activation_scope_matches_intent_and_acceptance`, `activation_materialization_coordinate_runtime_chain_exact`, `activation_requires_current_decision_record` |
| Prior/result publication status remained opaque | Transitions resolve the complete prior status and prior journal objects. Recovery resolves transaction, snapshots, marker, and complete resulting publication/status object. | `publication_prior_status_context_self_digest_checked`, `recovery_resolves_complete_resulting_status_object`, `recovery_result_context_self_digest_checked` |
| Lifecycle used unresolved revision integers | Added `semantic-accepted-lifecycle-ledger-record.v0`; deprecation/removal endpoints resolve complete published status objects and canonical accepted revision/head/coordinate facts. | `lifecycle_requires_accepted_current_ledger_heads`, `lifecycle_referenced_ledger_self_digest_checked` |
| Rollback availability used opaque digests | Added `semantic-rollback-available-artifact.v0`; availability resolves applicable target artifacts and a separately healthy/rehearsed recovery runtime, with exact proof references. | `rollback_requires_concrete_target_and_recovery_availability`, `rollback_target_artifact_self_digest_checked`, `rollback_recovery_artifact_resolved_exactly` |
| Python bool/int equality divergence | Schema `const` and `enum` equality is recursively JSON-type-exact; integer checks continue to reject booleans. | `python_integer_cannot_satisfy_boolean_const`, `python_boolean_cannot_satisfy_integer_type` |
| Node large SemVer precision loss | SemVer core integers remain strings and compare by digit length then ASCII bytes; no `Number` conversion occurs. | `arbitrary_length_semver_compares_without_number_precision_loss` |
| Archive root kind was unchecked | The archive payload-root entry must equal the exact `0755` directory row in addition to no-extra equality. | `archive_payload_root_must_be_exact_directory_entry` |
| Trust-root keys lacked set ordering | Both validators require trust-root key IDs to be UTF-8 sorted and unique. | `trust_root_keys_require_utf8_order`, `trust_root_keys_require_uniqueness` |
| Candidate task semantics were substitutable | Task contracts now bind exact contract/task/owner/rollback-owner IDs, dependencies, prerequisite IDs and artifact digests, repositories/paths, evidence, stop conditions, authority, and candidate status. | `task_contract_binds_exact_task_id`, `task_contract_binds_exact_owner_id`, `task_contract_binds_exact_rollback_owner_id`, `task_contract_binds_exact_evidence_list`, `task_contract_binds_exact_stop_conditions`, `task_contract_binds_exact_dependency_ids`, `task_contract_binds_exact_prerequisite_ids`, `task_contract_binds_exact_prerequisite_digests` |

## Generated packet

Revision v5 contains 42 closed protocol types, 86 canonical object preimages, 2 raw preimages, 28 exact digest links, 185 differential cases, and 8 raw lexical cases. The two validators independently recompute schema closure, canonical preimages, digests, links, raw-token rules, context validation, ordering, and domain transitions. Generated JSON is emitted only by `schema_builder.py` and `generate_fixtures.py`.

## Validation record

Run from the repository root:

```text
python docs/project/semantic-release-v0/validate_fixtures.py
  PASS — 42 types; 86 objects; 28 links; 185 differential cases (44 accepted, 141 rejected); 8 raw cases
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

These are architecture-fixture and repository-gate results only. They establish neither implementation nor production behavior.
