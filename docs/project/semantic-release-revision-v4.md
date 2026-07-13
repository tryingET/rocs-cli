---
summary: "Decision:53 semantic-release revision v4 executable closure of rereview-v3 blockers."
read_when:
  - "Reviewing Decision:53 revision v4 or its machine evidence."
type: "revision_note"
status: "proposed"
rfc_revision: "semantic-release-revision-v4"
review_posture: "fresh_review_required"
---
# Semantic Release Revision v4

## Objective and legal posture

This revision closes the finite blocker list in [`semantic-release-rereview3-synthesis-v3.md`](semantic-release-rereview3-synthesis-v3.md) with closed shapes, independent executable checks, and adversarial fixtures. It does not authorize an ADR, implementation, publication, adoption, activation, task creation, default, fleet rollout, or ontology mutation. Decision `53` remains subject to fresh strict review and the membrane in the RFC.

## Blocker-to-implementation map

| Rereview-v3 blocker | Executable closure | Adversarial evidence |
|---|---|---|
| Owner policy/set/predicate/namespace equality | Approval evaluation resolves one exact namespace → policy → owner set/predicate chain; threshold checks no longer accept digest drift. | `approval_owner_policy_digest_drift_rejected`, `approval_owner_set_digest_drift_rejected`, `approval_predicate_digest_drift_rejected`, `approval_namespace_drift_rejected` |
| Rotation equality | Rotation and complete typed approval repeat namespace, policy, owner set, predicate, old/new roots, and revisions; both roots resolve the same authority chain. | `rotation_owner_set_binding_drift_rejected`, `rotation_predicate_binding_drift_rejected`, `rotation_namespace_binding_drift_rejected` |
| Condition bijection | Condition references are cardinality-preserving: one required condition per change and one change per condition. | `condition_reference_must_be_bijective`, plus duplicate/missing/surplus condition cases |
| Non-lowering, completely approved override | The approval action contains the full embedded override. A known floor cannot decrease and `unknown` has a fail-closed `major` floor. | `override_cannot_lower_unknown_semver_floor`, `override_approval_requires_complete_override`, `override_approval_namespace_chain_must_match` |
| Lifecycle/tombstone/no reuse | Lifecycle heads, namespace, coordinates, revisions, interval, and prior registry bind exactly. The result is exactly the prior entries plus one exact origin/reason; any tombstoned ID is barred under every category. | `tombstone_registry_extra_entry_rejected`, `tombstone_origin_reason_exact_binding`, `tombstone_registry_must_preserve_every_prior_entry`, `tombstoned_identifier_cannot_return_as_addition` |
| Publication prior status/journal/recovery | Status transitions resolve the complete prior status and canonical prior journal. Recovery resolves exact resulting status and commit-marker objects, not presence booleans. | `status_transition_fabricated_prior_object_rejected`, `status_transition_prior_journal_drift_rejected`, `recovery_marker_must_match_exact_journal_and_result`, `recovery_status_record_must_match_result` |
| Canonical rollback activation and concrete availability | Request activation object/digest/revision equal the canonical current pointer. `semantic-rollback-availability-proof.v0` resolves concrete semantic/runtime materializations, revalidation/disable facts, and recovery runtime. | `rollback_requires_canonical_current_activation_object`, `rollback_requires_concrete_target_and_recovery_availability` |
| Rollback causality, stage monotonicity, history | At most one failed stage is followed only by `not_started`; receipt failure stage/error equals the stage cause. Changed heads resolve `semantic-rollback-history-transition.v0`; before-head equals the canonical current head. | `rollback_cannot_complete_stage_after_failure`, `rollback_error_must_equal_failed_stage_cause`, `rollback_history_head_must_bind_typed_transition`, `rollback_before_head_must_equal_canonical_head` |
| Exact archive equality | Archive paths equal metadata + payload root + every prefixed payload entry, with no extras. | `capsule_archive_extra_entry_rejected` |
| Activation/current pointer equality | Generation validates the supplied activation object's self-digest and revision against the current pointer before coordinate/runtime use. | `generation_supplied_activation_must_equal_current_pointer` |
| Issuer checks on all subjects | Every structurally valid golden or differential subject runs issuer-scope validation before its domain rule, including expected rejections. | `issuer_scope_checked_before_subject_rule` and the ROCS acceptance substitution case |
| Node own-property/prototype safety | Raw objects use null prototypes; required/extra/self-digest/ref/pointer checks use own-property operations. | raw `raw_proto_key_preserved_as_own_property` |
| UTF-8 manifest ordering | Node manifest tuple ordering uses UTF-8 bytes; JCS object-key ordering remains normative UTF-16. | `manifest_order_is_utf8_not_utf16` |
| Concrete AK/first-consumer contracts | `semantic-non-authorizing-task-contract.v0` and RFC section 14 define distinct repositories, exact allowed paths, evidence, rollback owners, stop conditions, and false authorization flags. | `ak_coordination_contract_cannot_authorize_execution`, `coordination_and_consumer_tasks_cannot_be_conflated`, `first_consumer_allowed_paths_are_exact` |

## Generated packet

Revision v4 contains 40 closed protocol types, 75 canonical object preimages, 2 raw preimages, 28 exact digest links, 150 differential cases, and 8 raw lexical cases. The two validators independently recompute schema closure, canonical preimages, digests, links, raw-token rules, ordering, and domain transitions. Generated JSON is emitted only by `schema_builder.py` and `generate_fixtures.py`.

## Validation record

Run from the repository root:

```text
python docs/project/semantic-release-v0/validate_fixtures.py
  PASS — 40 types; 75 objects; 28 links; 150 differential cases (43 accepted, 107 rejected); 8 raw cases
node docs/project/semantic-release-v0/validate_fixtures.mjs
  PASS — same independently recomputed corpus
node ~/ai-society/core/agent-scripts/scripts/docs-list.mjs --docs . --strict
  PASS
second generate_fixtures.py run plus git diff comparison
  PASS — generated artifacts converged byte-for-byte
git diff --check
  PASS
```

These are architecture-fixture results only. They do not establish implementation or production behavior.
