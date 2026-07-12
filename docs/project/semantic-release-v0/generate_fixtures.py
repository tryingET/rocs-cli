#!/usr/bin/env python3
"""Deterministically regenerate revision-2 schema and normative fixtures."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from schema_builder import write_schema
from validate_fixtures import COORDINATE_DOMAIN, DIGEST_FIELDS, domain_digest, object_digest

ROOT = Path(__file__).resolve().parent
ZERO = "sha256:" + "0" * 64
records: list[dict] = []
by_name: dict[str, dict] = {}


def raw(label: str, domain: str = "semantic-release.raw-blob.v0") -> str:
    return domain_digest(domain, label.encode())


def add(name: str, instance: dict) -> dict:
    if instance["schema"] == "semantic-release-coordinate.v0":
        domain, omitted = COORDINATE_DOMAIN, None
    else:
        domain, omitted = DIGEST_FIELDS[instance["schema"]]
        instance[omitted] = ZERO
    canonical, digest = object_digest(instance, domain, omitted)
    if omitted:
        instance[omitted] = digest
    record = {"name": name, "domain": domain, "omitted_field": omitted, "canonical_preimage": canonical, "digest": digest, "instance": instance}
    records.append(record)
    by_name[name] = record
    return instance


def d(name: str) -> str:
    return by_name[name]["digest"]


def rehash(instance: dict) -> None:
    domain, omitted = DIGEST_FIELDS[instance["schema"]]
    instance[omitted] = ZERO
    _, instance[omitted] = object_digest(instance, domain, omitted)


def variant(base: dict, **changes: object) -> dict:
    value = copy.deepcopy(base)
    value.update(changes)
    rehash(value)
    return value


def case(name: str, rule: str, subject: dict, expected_error: str | None, context: dict | None = None, schema_valid: bool = True) -> dict:
    return {"name": name, "rule": rule, "schema_valid": schema_valid, "expected_error": expected_error, "subject": subject, "context": context or {}}


owner_repo = {"owner": "semantic-owner", "repository_id": "ontology-kernel", "canonical_locator": "local://core/ontology-kernel", "identity_revision": 1}
consumer_repo = {"owner": "consumer-owner", "repository_id": "pi-canary-consumer", "canonical_locator": "local://softwareco/pi-canary-consumer", "identity_revision": 3}
ak_repo = {"owner": "agent-kernel-owner", "repository_id": "agent-kernel", "canonical_locator": "local://softwareco/owned/agent-kernel", "identity_revision": 9}
rocs_tool = {"tool": "rocs-cli", "version": "1.4.0", "distribution_digest": raw("rocs-1.4"), "protocol_version": "semantic-release-v0"}
old_runtime = {"tool": "rocs-cli", "version": "1.3.2", "distribution_digest": raw("rocs-1.3.2"), "protocol_version": "semantic-release-v0"}
ak_tool = {"tool": "agent-kernel", "version": "0.9.0", "distribution_digest": raw("ak-0.9"), "protocol_version": "semantic-release-v0"}
recovery_tool = {"tool": "semantic-recovery-controller", "version": "1.0.0", "distribution_digest": raw("recovery-1"), "protocol_version": "semantic-release-v0"}
predecessor = {"schema": "semantic-release-coordinate.v0", "namespace": "ai-society.core", "semantic_version": "1.0.0", "capsule_digest": raw("capsule-1.0")}

source = add("source_manifest", {"schema": "semantic-source-manifest.v0", "repository": owner_repo, "source_revision": "0123456789abcdef0123456789abcdef01234567", "source_root": "ontology", "clean_committed": True,
    "entries": [{"path": "concepts", "kind": "directory", "mode": 493}, {"path": "concepts/agent.yaml", "kind": "file", "mode": 420, "byte_length": 28, "content_digest": raw("agent-source")},
                {"path": "manifest.yaml", "kind": "file", "mode": 420, "byte_length": 16, "content_digest": raw("manifest-source")} ]})
payload = add("payload_manifest", {"schema": "semantic-material-manifest.v0", "tree_role": "compiled_payload", "entries": [
    {"path": "index.json", "kind": "file", "mode": 420, "byte_length": 17, "content_digest": raw("index-bytes")}, {"path": "records", "kind": "directory", "mode": 493},
    {"path": "records/core.Agent.json", "kind": "file", "mode": 420, "byte_length": 36, "content_digest": raw("record-bytes")} ]})
consumer_manifest = add("consumer_material_manifest", {"schema": "semantic-material-manifest.v0", "tree_role": "consumer_materialization", "entries": copy.deepcopy(payload["entries"])})
archive_manifest = add("capsule_archive_manifest", {"schema": "semantic-material-manifest.v0", "tree_role": "capsule_archive", "entries": [
    {"path": "capsule.json", "kind": "file", "mode": 420, "byte_length": 512, "content_digest": raw("capsule-metadata")}, {"path": "payload", "kind": "directory", "mode": 493},
    {"path": "payload/index.json", "kind": "file", "mode": 420, "byte_length": 17, "content_digest": raw("index-bytes")}, {"path": "payload/records", "kind": "directory", "mode": 493},
    {"path": "payload/records/core.Agent.json", "kind": "file", "mode": 420, "byte_length": 36, "content_digest": raw("record-bytes")} ]})
projection = add("payload_projection", {"schema": "semantic-payload-projection.v0", "payload_manifest_digest": d("payload_manifest"), "consumer_manifest_digest": d("consumer_material_manifest"), "projection_mode": "exact_no_extra_no_missing", "entries": [
    {"capsule_path": "payload/index.json", "consumer_path": "index.json", "mode": 420, "byte_length": 17, "content_digest": raw("index-bytes")},
    {"capsule_path": "payload/records", "consumer_path": "records", "mode": 493, "byte_length": None, "content_digest": None},
    {"capsule_path": "payload/records/core.Agent.json", "consumer_path": "records/core.Agent.json", "mode": 420, "byte_length": 36, "content_digest": raw("record-bytes")} ]})
archive_link = add("capsule_archive_linkage", {"schema": "semantic-capsule-archive-linkage.v0", "archive_manifest_digest": d("capsule_archive_manifest"), "payload_manifest_digest": d("payload_manifest"),
    "payload_root": "payload", "capsule_metadata_path": "capsule.json", "archive_format": "directory-v0"})

category_rules = [
    ("addition", "compatible", "minor", None, True), ("compatible_refinement", "compatible", "patch", None, True),
    ("constraint_change", "conditionally_compatible", "minor", "evidence_digest_equals", True), ("deprecation", "compatible", "minor", None, True),
    ("documentation", "compatible", "patch", None, True), ("identifier_reuse", "breaking", "major", None, False),
    ("other", "unknown", "unknown", None, True), ("relation_change", "conditionally_compatible", "minor", "consumer_protocol_at_least", True),
    ("removal", "breaking", "major", "deprecation_interval_at_least", False), ("rename", "breaking", "major", "deprecation_interval_at_least", False)]
compat_policy = add("compatibility_policy", {"schema": "semantic-compatibility-policy.v0", "namespace": "ai-society.core", "policy_revision": 7,
    "category_rules": [{"category": a, "classification": b, "semver_effect": c, "condition_rule": None if k is None else {"condition_kind": k, "required": True}, "override_allowed": o} for a,b,c,k,o in category_rules],
    "severity_order": ["patch", "minor", "major", "unknown"], "initial_zero_exceptions": False, "minimum_deprecation_releases": 2, "identifier_reuse_override_forbidden": True, "prior_policy_digest": raw("compat-policy-6")})
owner_set = add("owner_set", {"schema": "semantic-owner-set.v0", "namespace": "ai-society.core", "owner_set_revision": 8, "members": [
    {"owner_id": "owner-a", "key_ids": ["owner-a-key-3"], "status": "active", "revocation_digest": None},
    {"owner_id": "owner-b", "key_ids": ["owner-b-key-2"], "status": "active", "revocation_digest": None},
    {"owner_id": "owner-c", "key_ids": ["owner-c-key-1"], "status": "active", "revocation_digest": None}], "prior_owner_set_digest": raw("owner-set-7")})
predicate = add("approval_predicate", {"schema": "semantic-approval-predicate.v0", "namespace": "ai-society.core", "predicate_revision": 3, "mode": "threshold", "threshold": 2,
    "eligible_owner_status": "active", "distinct_owner_required": True})
owner_policy = add("owner_policy", {"schema": "semantic-owner-policy.v0", "namespace": "ai-society.core", "policy_revision": 12, "governing_scope_digest": raw("namespace-scope"),
    "owner_set_digest": d("owner_set"), "approval_predicate_digest": d("approval_predicate"), "compatibility_policy_digest": d("compatibility_policy"), "trust_bootstrap_mode": "owner_controlled_local_out_of_band",
    "rotation_requires_old_root": True, "revocation_fail_closed": True, "prior_owner_policy_digest": raw("owner-policy-11")})
trust_root = add("trust_root", {"schema": "semantic-trust-root.v0", "namespace": "ai-society.core", "trust_root_id": "semantic-owner-local-root", "trust_root_revision": 5,
    "owner_policy_digest": d("owner_policy"), "owner_set_digest": d("owner_set"), "key_ids": ["root-key-5"], "minimum_ledger_revision": 2, "prior_trust_root_digest": raw("trust-root-4"), "status": "active"})
rotated_root_stub = raw("trust-root-6")
rotation = add("trust_rotation", {"schema": "semantic-trust-rotation.v0", "namespace": "ai-society.core", "old_trust_root_digest": d("trust_root"), "new_trust_root_digest": rotated_root_stub,
    "owner_policy_digest": d("owner_policy"), "approval_digest": raw("rotation-approval"), "rotation_revision": 6})
revocation = add("trust_revocation", {"schema": "semantic-trust-revocation.v0", "namespace": "ai-society.core", "target_kind": "owner_key", "target_digest": raw("compromised-key"),
    "effective_ledger_revision": 3, "reason_digest": raw("compromise-reason"), "owner_approval_digest": raw("revocation-approval"), "prior_revocation_digest": None})

condition = {"condition_id": "constraint-proof", "kind": "evidence_digest_equals", "expected_digest": raw("compat-evidence"), "actual_digest": raw("compat-evidence"), "expected_integer": None, "actual_integer": None, "satisfied": True}
compat_report = add("compatibility_report", {"schema": "semantic-compatibility-report.v0", "namespace": "ai-society.core", "prior_coordinate": predecessor, "candidate_version": "1.1.0",
    "compatibility_policy_digest": d("compatibility_policy"), "changes": [{"category": "addition", "semantic_id": "core.Agent", "classification": "compatible", "semver_effect": "minor", "condition_id": None}],
    "conditions": [], "classification": "compatible", "required_semver_effect": "minor", "override_digest": None})
conditional_report = add("conditional_compatibility_report", {"schema": "semantic-compatibility-report.v0", "namespace": "ai-society.core", "prior_coordinate": predecessor, "candidate_version": "1.1.0",
    "compatibility_policy_digest": d("compatibility_policy"), "changes": [{"category": "constraint_change", "semantic_id": "core.Agent", "classification": "conditionally_compatible", "semver_effect": "minor", "condition_id": "constraint-proof"}],
    "conditions": [condition], "classification": "conditionally_compatible", "required_semver_effect": "minor", "override_digest": None})
override = add("compatibility_override", {"schema": "semantic-compatibility-override.v0", "namespace": "ai-society.core", "compatibility_policy_digest": d("compatibility_policy"), "change_digest": raw("other-change"),
    "from_classification": "unknown", "to_classification": "conditionally_compatible", "semver_effect_floor": "major", "condition": condition, "owner_approval_digest": raw("override-owner-approval")})

tombstones = add("tombstone_registry", {"schema": "semantic-tombstone-registry.v0", "namespace": "ai-society.core", "registry_revision": 4,
    "entries": [{"semantic_id": "core.Legacy", "reason": "removed", "origin_record_digest": raw("legacy-removal")}], "prior_registry_digest": raw("tombstones-3")})

capsule = add("capsule", {"schema": "semantic-release-capsule.v0", "namespace": "ai-society.core", "semantic_version": "1.1.0", "source_manifest_digest": d("source_manifest"),
    "semantic_payload_digest": raw("semantic-payload-1.1", "semantic-release.semantic-payload.v0"), "payload_manifest_digest": d("payload_manifest"), "payload_projection_digest": d("payload_projection"),
    "capsule_archive_linkage_digest": d("capsule_archive_linkage"), "compatibility_report_digest": d("compatibility_report"), "owner_policy_digest": d("owner_policy"),
    "compilation_contract_digest": raw("compilation-contract"), "required_protocol_versions": ["semantic-discovery-v0", "semantic-release-v0"], "predecessor_coordinate": predecessor,
    "tombstone_registry_digest": d("tombstone_registry")})
coordinate = add("coordinate", {"schema": "semantic-release-coordinate.v0", "namespace": "ai-society.core", "semantic_version": "1.1.0", "capsule_digest": d("capsule")})
coord_digest = d("coordinate")
owner_decision = add("owner_ak_decision", {"schema": "semantic-ak-decision-reference.v0", "ak_repository": ak_repo, "ak_runtime_identity": ak_tool, "decision_id": "semantic-release-1.1.0", "decision_revision": 2,
    "lifecycle_state": "accepted", "adr_reference": {"adr_id": "ADR-0053", "adr_revision": 1, "adr_digest": raw("adr-53"), "status": "accepted"}, "scope_digest": raw("semantic-owner-scope"),
    "revocation_digest": None, "activation_target_digest": d("capsule"), "evidence_criteria_digest": d("compatibility_report"), "rollback_plan_digest": raw("owner-withdrawal-plan"), "stop_conditions_digest": raw("owner-stop-conditions")})
consumer_decision = add("consumer_ak_decision", {"schema": "semantic-ak-decision-reference.v0", "ak_repository": ak_repo, "ak_runtime_identity": ak_tool, "decision_id": "consumer-canary", "decision_revision": 4,
    "lifecycle_state": "accepted", "adr_reference": {"adr_id": "ADR-0053", "adr_revision": 1, "adr_digest": raw("adr-53"), "status": "accepted"}, "scope_digest": raw("consumer-canary-scope"),
    "revocation_digest": None, "activation_target_digest": coord_digest, "evidence_criteria_digest": raw("canary-evidence"), "rollback_plan_digest": raw("canary-rollback"), "stop_conditions_digest": raw("canary-stop")})
owner_approval = add("owner_approval", {"schema": "semantic-owner-approval.v0", "namespace": "ai-society.core", "owner_policy_digest": d("owner_policy"), "owner_set_digest": d("owner_set"),
    "approval_predicate_digest": d("approval_predicate"), "source_manifest_digest": d("source_manifest"), "candidate_capsule_digest": d("capsule"), "compatibility_report_digest": d("compatibility_report"),
    "votes": [{"owner_id": "owner-a", "owner_key_id": "owner-a-key-3", "approved_candidate_digest": d("capsule"), "approval_proof_digest": raw("vote-a")},
              {"owner_id": "owner-b", "owner_key_id": "owner-b-key-2", "approved_candidate_digest": d("capsule"), "approval_proof_digest": raw("vote-b")}], "decision_reference_digest": d("owner_ak_decision")})
build = add("build_receipt", {"schema": "semantic-build-receipt.v0", "source_manifest_digest": d("source_manifest"), "compilation_contract_digest": capsule["compilation_contract_digest"], "tool_identity": rocs_tool,
    "payload_manifest_digest": d("payload_manifest"), "payload_projection_digest": d("payload_projection"), "capsule_archive_linkage_digest": d("capsule_archive_linkage"),
    "semantic_payload_digest": capsule["semantic_payload_digest"], "compatibility_report_digest": d("compatibility_report"), "candidate_capsule_digest": d("capsule"), "reproducible": True})
publication = add("owner_publication", {"schema": "semantic-owner-publication.v0", "coordinate": coordinate, "owner_approval_digest": d("owner_approval"), "ledger_namespace": "ai-society.core", "ledger_revision": 2,
    "prior_publication_digest": raw("publication-1"), "trust_root_digest": d("trust_root"), "status": "published"})
publish_tx = add("publication_transaction", {"schema": "semantic-publication-transaction.v0", "transaction_id": "publish-1.1.0", "operation": "publish", "namespace": "ai-society.core", "coordinate": coordinate,
    "owner_approval_digest": d("owner_approval"), "expected_prior_revision": 1, "expected_prior_head_digest": raw("publication-1"), "replay_key_digest": raw("publish-replay-key"), "status_reason_digest": None})
publish_journal = add("publication_journal", {"schema": "semantic-publication-journal.v0", "transaction_digest": d("publication_transaction"), "state": "committed", "staged_record_digest": d("owner_publication"),
    "staged_blob_set_digest": raw("publication-blobs"), "linearized": True, "recovery_action": "none", "prior_journal_digest": raw("journal-prepared")})
publish_marker = add("publication_commit_marker", {"schema": "semantic-publication-commit-marker.v0", "transaction_digest": d("publication_transaction"), "journal_digest": d("publication_journal"),
    "ledger_revision": 2, "ledger_head_digest": d("owner_publication"), "fsync_complete": True})

withdraw_tx = add("withdraw_transaction", {"schema": "semantic-publication-transaction.v0", "transaction_id": "withdraw-1.1.0", "operation": "withdraw", "namespace": "ai-society.core", "coordinate": coordinate,
    "owner_approval_digest": d("owner_approval"), "expected_prior_revision": 2, "expected_prior_head_digest": d("owner_publication"), "replay_key_digest": raw("withdraw-replay"), "status_reason_digest": raw("withdraw-reason")})
withdraw_journal = add("withdraw_journal", {"schema": "semantic-publication-journal.v0", "transaction_digest": d("withdraw_transaction"), "state": "committed", "staged_record_digest": raw("withdraw-transition-staged"),
    "staged_blob_set_digest": raw("withdraw-blobs"), "linearized": True, "recovery_action": "none", "prior_journal_digest": d("publication_journal")})
withdraw_marker = add("withdraw_marker", {"schema": "semantic-publication-commit-marker.v0", "transaction_digest": d("withdraw_transaction"), "journal_digest": d("withdraw_journal"), "ledger_revision": 3,
    "ledger_head_digest": raw("withdraw-head"), "fsync_complete": True})
withdrawal = add("publication_withdrawal", {"schema": "semantic-publication-status-transition.v0", "coordinate": coordinate, "from_status": "published", "to_status": "withdrawn",
    "prior_status_record_digest": d("owner_publication"), "transaction_digest": d("withdraw_transaction"), "journal_digest": d("withdraw_journal"), "commit_marker_digest": d("withdraw_marker"),
    "owner_approval_digest": d("owner_approval"), "reason_digest": raw("withdraw-reason"), "ledger_revision": 3})
revoke_tx = add("revoke_transaction", {"schema": "semantic-publication-transaction.v0", "transaction_id": "revoke-1.1.0", "operation": "revoke", "namespace": "ai-society.core", "coordinate": coordinate,
    "owner_approval_digest": d("owner_approval"), "expected_prior_revision": 3, "expected_prior_head_digest": d("publication_withdrawal"), "replay_key_digest": raw("revoke-replay"), "status_reason_digest": raw("revoke-reason")})
revoke_journal = add("revoke_journal", {"schema": "semantic-publication-journal.v0", "transaction_digest": d("revoke_transaction"), "state": "committed", "staged_record_digest": raw("revoke-transition-staged"),
    "staged_blob_set_digest": raw("revoke-blobs"), "linearized": True, "recovery_action": "none", "prior_journal_digest": d("withdraw_journal")})
revoke_marker = add("revoke_marker", {"schema": "semantic-publication-commit-marker.v0", "transaction_digest": d("revoke_transaction"), "journal_digest": d("revoke_journal"), "ledger_revision": 4,
    "ledger_head_digest": raw("revoke-head"), "fsync_complete": True})
revoked_publication = add("publication_revocation", {"schema": "semantic-publication-status-transition.v0", "coordinate": coordinate, "from_status": "withdrawn", "to_status": "revoked",
    "prior_status_record_digest": d("publication_withdrawal"), "transaction_digest": d("revoke_transaction"), "journal_digest": d("revoke_journal"), "commit_marker_digest": d("revoke_marker"),
    "owner_approval_digest": d("owner_approval"), "reason_digest": raw("revoke-reason"), "ledger_revision": 4})

# Lifecycle artifacts use a later major coordinate and preserve permanent tombstones.
major_coordinate = {"schema": "semantic-release-coordinate.v0", "namespace": "ai-society.core", "semantic_version": "2.0.0", "capsule_digest": raw("capsule-2")}
deprecation = add("deprecation_record", {"schema": "semantic-deprecation-record.v0", "namespace": "ai-society.core", "semantic_id": "core.Legacy", "introduced_coordinate": coordinate,
    "introduced_ledger_revision": 2, "prior_lifecycle_digest": None})
removal = add("removal_record", {"schema": "semantic-removal-record.v0", "namespace": "ai-society.core", "semantic_id": "core.Legacy", "removed_coordinate": major_coordinate,
    "removed_ledger_revision": 4, "deprecation_record_digest": d("deprecation_record"), "deprecation_ledger_revision": 2, "required_interval": 2, "tombstone_digest": raw("legacy-tombstone")})

trust_ref = {"trust_root_id": trust_root["trust_root_id"], "trust_root_revision": trust_root["trust_root_revision"], "trust_root_digest": d("trust_root"), "publication_ledger_revision": 2,
             "publication_digest": d("owner_publication"), "local_revocation_head_digest": d("trust_revocation")}
semantic_target = {"kind": "semantic", "semantic_action": "switch", "target_coordinate": predecessor, "runtime_action": "retain", "target_materialization_receipt_digest": raw("predecessor-materialization")}
runtime_target = {"kind": "runtime", "semantic_action": "retain", "runtime_action": "switch", "target_runtime_identity": old_runtime, "target_materialization_receipt_digest": raw("old-runtime-materialization"), "runtime_revalidation_receipt_digest": raw("runtime-revalidation")}
disable_target = {"kind": "no_prior_disable", "semantic_action": "disable", "runtime_action": "retain", "disable_contract_digest": raw("disable-contract"), "rehearsal_receipt_digest": raw("disable-rehearsal")}
combined_target = {"kind": "combined", "semantic_stage": semantic_target, "runtime_stage": runtime_target, "stage_order": "semantic_then_runtime"}
intent = add("consumer_intent", {"schema": "semantic-consumer-intent.v0", "consumer_repository": consumer_repo, "intent_revision": 4, "desired_coordinate": coordinate, "runtime_identity": rocs_tool,
    "requested_posture": "named_canary", "accepted_compatibility": "compatible", "rollback_target": semantic_target, "decision_reference_digest": d("consumer_ak_decision"), "trust_reference": trust_ref,
    "verifier_contract_digest": raw("verifier-contract"), "limits_digest": raw("limits")})
acceptance = add("owner_acceptance", {"schema": "semantic-owner-acceptance.v0", "consumer_intent_digest": d("consumer_intent"), "consumer_repository": consumer_repo,
    "acceptance_authority": {"kind": "consumer_owner", "id": "consumer-owner"}, "acceptance_revision": 4, "governing_scope_digest": consumer_decision["scope_digest"], "accepted_posture": "named_canary",
    "decision_reference_digest": d("consumer_ak_decision"), "valid_through_intent_revision": 4, "activation_epoch_not_after": 100, "revoked_by_digest": None})
materialization = add("materialization_receipt", {"schema": "semantic-materialization-verification-receipt.v0", "issuer": {"kind": "rocs", "id": "rocs-cli"},
    "consumer_intent_digest": d("consumer_intent"), "owner_acceptance_digest": d("owner_acceptance"), "coordinate": coordinate, "owner_approval_digest": d("owner_approval"), "trust_reference": trust_ref,
    "runtime_identity": rocs_tool, "capsule_archive_linkage_digest": d("capsule_archive_linkage"), "payload_projection_digest": d("payload_projection"), "source_payload_manifest_digest": d("payload_manifest"),
    "expected_consumer_manifest_digest": d("consumer_material_manifest"), "actual_consumer_manifest_digest": d("consumer_material_manifest"), "consumer_repository": consumer_repo,
    "compatibility_report_digest": d("compatibility_report"), "compatibility_outcome": "compatible", "prior_receipt_digest": raw("prior-materialization"), "rollback_target": semantic_target,
    "rollback_ready": True, "verifier_contract_digest": intent["verifier_contract_digest"], "transaction_id": "materialize-4", "journal_state": "committed", "commit_marker_digest": raw("materialize-marker")})
activation = add("activation_receipt", {"schema": "semantic-activation-receipt.v0", "issuer": {"kind": "consumer_owner", "id": "consumer-owner"}, "owner_acceptance_digest": d("owner_acceptance"),
    "materialization_verification_receipt_digest": d("materialization_receipt"), "consumer_repository": consumer_repo, "coordinate": coordinate, "runtime_identity": rocs_tool, "activation_scope": "named_canary",
    "activation_revision": 1, "activation_epoch": 90, "gate_decision_reference_digest": d("consumer_ak_decision"), "activation_target_digest": coord_digest,
    "evidence_criteria_digest": consumer_decision["evidence_criteria_digest"], "rollback_plan_digest": consumer_decision["rollback_plan_digest"], "stop_conditions_digest": consumer_decision["stop_conditions_digest"],
    "previous_activation_receipt_digest": None, "status": "activated", "revoked_by_digest": None, "superseded_by_activation_receipt_digest": None})
generation = add("rocs_generation_receipt", {"schema": "semantic-rocs-generation-receipt.v0", "issuer": {"kind": "rocs", "id": "rocs-cli"}, "claim_scope": "generated_output_only",
    "activation_receipt_digest": d("activation_receipt"), "coordinate": coordinate, "runtime_identity": rocs_tool, "request_digest": raw("request"), "result_digest": raw("result"),
    "effective_execution_digest": raw("execution"), "candidate_ids": ["core.Agent"], "pack_digests": [raw("pack")], "outcome": "matched"})
pi_delivered = add("pi_delivery_delivered", {"schema": "semantic-pi-delivery-receipt.v0", "issuer": {"kind": "pi", "id": "pi-adapter"}, "claim_scope": "delivered_to_prompt_run_only",
    "rocs_generation_receipt_digest": d("rocs_generation_receipt"), "delivery_outcome": "delivered", "prompt_run_digest": raw("prompt-run"), "delivered_effective_execution_digest": generation["effective_execution_digest"]})
pi_suppressed = add("pi_delivery_suppressed", {"schema": "semantic-pi-delivery-receipt.v0", "issuer": {"kind": "pi", "id": "pi-adapter"}, "claim_scope": "delivery_suppressed_only",
    "rocs_generation_receipt_digest": d("rocs_generation_receipt"), "delivery_outcome": "suppressed", "suppression_reason": "stale_result"})
pi_failed = add("pi_delivery_failed", {"schema": "semantic-pi-delivery-receipt.v0", "issuer": {"kind": "pi", "id": "pi-adapter"}, "claim_scope": "delivery_failed_only",
    "rocs_generation_receipt_digest": d("rocs_generation_receipt"), "delivery_outcome": "failed", "error_digest": raw("pi-delivery-error")})
ak_link = add("ak_evidence_linkage", {"schema": "semantic-ak-evidence-linkage.v0", "issuer": {"kind": "ak", "id": "agent-kernel"}, "claim_scope": "lineage_linkage_only",
    "task_reference_digest": raw("ak-task"), "decision_reference_digest": d("consumer_ak_decision"), "evidence_record_digest": raw("ak-evidence"), "activation_receipt_digest": d("activation_receipt"),
    "rocs_generation_receipt_digest": d("rocs_generation_receipt"), "pi_delivery_receipt_digest": d("pi_delivery_delivered"), "empirical_outcome_reference_digest": None})
ak_generation_only = add("ak_generation_only_linkage", {"schema": "semantic-ak-evidence-linkage.v0", "issuer": {"kind": "ak", "id": "agent-kernel"}, "claim_scope": "lineage_linkage_only",
    "task_reference_digest": raw("ak-task-generation"), "decision_reference_digest": d("consumer_ak_decision"), "evidence_record_digest": raw("ak-evidence-generation"), "activation_receipt_digest": d("activation_receipt"),
    "rocs_generation_receipt_digest": d("rocs_generation_receipt"), "pi_delivery_receipt_digest": None, "empirical_outcome_reference_digest": None})

active_state = {"enabled": True, "coordinate": coordinate, "runtime_identity": rocs_tool}
semantic_request = add("semantic_rollback_request", {"schema": "semantic-rollback-request.v0", "issuer": {"kind": "consumer_owner", "id": "consumer-owner"}, "active_activation_receipt_digest": d("activation_receipt"),
    "from_state": active_state, "target": semantic_target, "recovery_runtime_identity": recovery_tool, "owner_decision_reference_digest": d("consumer_ak_decision"), "precondition_digest": raw("semantic-preconditions")})
semantic_receipt = add("semantic_rollback_receipt", {"schema": "semantic-rollback-receipt.v0", "issuer": {"kind": "recovery_controller", "id": "recovery"}, "rollback_request_digest": d("semantic_rollback_request"),
    "result": "rolled_back", "active_state_before": active_state, "active_state_after": {"enabled": True, "coordinate": predecessor, "runtime_identity": rocs_tool}, "availability_proof_digest": raw("semantic-available"),
    "stages": [{"stage": "semantic", "result": "completed", "error_digest": None}], "history_head_before": {"kind": "activation", "digest": d("activation_receipt")},
    "history_head_after": {"kind": "rollback", "digest": raw("semantic-history-after")}, "error_digest": None, "supersedes_activation_receipt_digest": d("activation_receipt")})
runtime_request = add("runtime_rollback_request", {"schema": "semantic-rollback-request.v0", "issuer": {"kind": "consumer_owner", "id": "consumer-owner"}, "active_activation_receipt_digest": d("activation_receipt"),
    "from_state": active_state, "target": runtime_target, "recovery_runtime_identity": recovery_tool, "owner_decision_reference_digest": d("consumer_ak_decision"), "precondition_digest": raw("runtime-preconditions")})
runtime_receipt = add("runtime_rollback_receipt", {"schema": "semantic-rollback-receipt.v0", "issuer": {"kind": "recovery_controller", "id": "recovery"}, "rollback_request_digest": d("runtime_rollback_request"),
    "result": "rolled_back", "active_state_before": active_state, "active_state_after": {"enabled": True, "coordinate": coordinate, "runtime_identity": old_runtime}, "availability_proof_digest": runtime_target["runtime_revalidation_receipt_digest"],
    "stages": [{"stage": "runtime", "result": "completed", "error_digest": None}], "history_head_before": {"kind": "activation", "digest": d("activation_receipt")},
    "history_head_after": {"kind": "rollback", "digest": raw("runtime-history-after")}, "error_digest": None, "supersedes_activation_receipt_digest": d("activation_receipt")})
disable_request = add("disable_rollback_request", {"schema": "semantic-rollback-request.v0", "issuer": {"kind": "consumer_owner", "id": "consumer-owner"}, "active_activation_receipt_digest": d("activation_receipt"),
    "from_state": active_state, "target": disable_target, "recovery_runtime_identity": recovery_tool, "owner_decision_reference_digest": d("consumer_ak_decision"), "precondition_digest": raw("disable-preconditions")})
disable_receipt = add("disable_rollback_receipt", {"schema": "semantic-rollback-receipt.v0", "issuer": {"kind": "recovery_controller", "id": "recovery"}, "rollback_request_digest": d("disable_rollback_request"),
    "result": "disabled", "active_state_before": active_state, "active_state_after": {"enabled": False, "coordinate": None, "runtime_identity": rocs_tool}, "availability_proof_digest": disable_target["rehearsal_receipt_digest"],
    "stages": [{"stage": "disable", "result": "completed", "error_digest": None}], "history_head_before": {"kind": "activation", "digest": d("activation_receipt")},
    "history_head_after": {"kind": "disable", "digest": raw("disable-history-after")}, "error_digest": None, "supersedes_activation_receipt_digest": d("activation_receipt")})
combined_request = add("combined_rollback_request", {"schema": "semantic-rollback-request.v0", "issuer": {"kind": "consumer_owner", "id": "consumer-owner"}, "active_activation_receipt_digest": d("activation_receipt"),
    "from_state": active_state, "target": combined_target, "recovery_runtime_identity": recovery_tool, "owner_decision_reference_digest": d("consumer_ak_decision"), "precondition_digest": raw("combined-preconditions")})
partial_receipt = add("combined_partial_failure_receipt", {"schema": "semantic-rollback-receipt.v0", "issuer": {"kind": "recovery_controller", "id": "recovery"}, "rollback_request_digest": d("combined_rollback_request"),
    "result": "partial_failure", "active_state_before": active_state, "active_state_after": {"enabled": True, "coordinate": predecessor, "runtime_identity": rocs_tool}, "availability_proof_digest": raw("partial-availability"),
    "stages": [{"stage": "semantic", "result": "completed", "error_digest": None}, {"stage": "runtime", "result": "failed", "error_digest": raw("runtime-stage-error")}],
    "history_head_before": {"kind": "activation", "digest": d("activation_receipt")}, "history_head_after": {"kind": "rollback", "digest": raw("partial-history-after")},
    "error_digest": raw("combined-partial-error"), "supersedes_activation_receipt_digest": d("activation_receipt")})
failed_receipt = add("failed_rollback_receipt", {"schema": "semantic-rollback-receipt.v0", "issuer": {"kind": "recovery_controller", "id": "recovery"}, "rollback_request_digest": d("semantic_rollback_request"),
    "result": "failed", "active_state_before": active_state, "active_state_after": active_state, "availability_proof_digest": raw("failed-availability"),
    "stages": [{"stage": "semantic", "result": "failed", "error_digest": raw("semantic-stage-error")}], "history_head_before": {"kind": "activation", "digest": d("activation_receipt")},
    "history_head_after": {"kind": "activation", "digest": d("activation_receipt")}, "error_digest": raw("rollback-error"), "supersedes_activation_receipt_digest": None})
audit = add("audit_envelope", {"schema": "semantic-audit-envelope.v0", "artifact_schema": "semantic-rollback-receipt.v0", "artifact_digest": d("semantic_rollback_receipt"), "event": "rolled_back",
    "recorded_at": "2026-07-13T12:30:45Z", "issuer": {"kind": "ak", "id": "agent-kernel"}, "audit_sequence": 9, "previous_audit_envelope_digest": raw("audit-8")})
error = add("error_envelope", {"schema": "semantic-protocol-error.v0", "code": "digest_mismatch", "stage": "validate", "retryable": False, "related_artifact_digest": d("capsule"),
    "details": [{"key": "artifact", "value": "capsule"}], "error_digest": ZERO})

links = [
    ("owner_policy", "/owner_set_digest", "owner_set"), ("owner_policy", "/approval_predicate_digest", "approval_predicate"), ("owner_policy", "/compatibility_policy_digest", "compatibility_policy"),
    ("capsule_archive_linkage", "/archive_manifest_digest", "capsule_archive_manifest"), ("payload_projection", "/payload_manifest_digest", "payload_manifest"),
    ("capsule", "/payload_projection_digest", "payload_projection"), ("capsule", "/capsule_archive_linkage_digest", "capsule_archive_linkage"), ("coordinate", "/capsule_digest", "capsule"),
    ("owner_approval", "/decision_reference_digest", "owner_ak_decision"), ("owner_publication", "/owner_approval_digest", "owner_approval"),
    ("publication_journal", "/transaction_digest", "publication_transaction"), ("publication_commit_marker", "/journal_digest", "publication_journal"), ("publication_commit_marker", "/ledger_head_digest", "owner_publication"),
    ("consumer_intent", "/decision_reference_digest", "consumer_ak_decision"), ("owner_acceptance", "/consumer_intent_digest", "consumer_intent"),
    ("materialization_receipt", "/payload_projection_digest", "payload_projection"), ("materialization_receipt", "/expected_consumer_manifest_digest", "consumer_material_manifest"),
    ("activation_receipt", "/materialization_verification_receipt_digest", "materialization_receipt"), ("rocs_generation_receipt", "/activation_receipt_digest", "activation_receipt"),
    ("pi_delivery_delivered", "/rocs_generation_receipt_digest", "rocs_generation_receipt"), ("ak_evidence_linkage", "/pi_delivery_receipt_digest", "pi_delivery_delivered"),
    ("semantic_rollback_receipt", "/rollback_request_digest", "semantic_rollback_request"), ("audit_envelope", "/artifact_digest", "semantic_rollback_receipt")]

golden = {"protocol": "semantic-release-v0", "rfc_revision": "semantic-release-revision-v2", "canonicalization": "RFC8785 JCS after duplicate-free UTF-8 integer-only I-JSON validation",
    "digest_construction": "sha256(UTF8(domain) || 0x00 || preimage)", "raw_preimages": [
        {"name": "raw_blob_example", "domain": "semantic-release.raw-blob.v0", "preimage_utf8": "agent-source", "digest": raw("agent-source")},
        {"name": "semantic_payload_example", "domain": "semantic-release.semantic-payload.v0", "preimage_utf8": "semantic-payload-1.1", "digest": raw("semantic-payload-1.1", "semantic-release.semantic-payload.v0")}],
    "records": records, "chain_assertions": [{"record": a, "instance_path": p, "equals_record": b} for a,p,b in links]}

# Differential fixtures include accepted transitions as well as adversarial failures.
cases: list[dict] = []
insufficient = variant(owner_approval, votes=owner_approval["votes"][:1])
revoked_vote_context = {"owner_set": variant(owner_set, members=[owner_set["members"][0], {**owner_set["members"][1], "status": "revoked", "revocation_digest": raw("key-revoked")}, owner_set["members"][2]]), "predicate": predicate}
cases += [
    case("threshold_two_of_three_accepts", "approval_threshold", owner_approval, None, {"owner_set": owner_set, "predicate": predicate}),
    case("threshold_insufficient_rejected", "approval_threshold", insufficient, "approval_threshold_unsatisfied", {"owner_set": owner_set, "predicate": predicate}),
    case("revoked_owner_vote_rejected", "approval_threshold", owner_approval, "trust_revoked", revoked_vote_context),
    case("valid_old_to_new_root_rotation", "trust_rotation", rotation, None, {"current_root_digest": d("trust_root"), "revoked": []}),
    case("rotation_not_bound_to_current_root", "trust_rotation", variant(rotation, old_trust_root_digest=raw("wrong-root")), "trust_reference_stale", {"current_root_digest": d("trust_root"), "revoked": []}),
    case("revoked_rotation_root_rejected", "trust_rotation", rotation, "trust_revoked", {"current_root_digest": d("trust_root"), "revoked": [d("trust_root")]})]
false_condition = copy.deepcopy(conditional_report); false_condition["conditions"][0]["actual_digest"] = raw("wrong-evidence"); false_condition["conditions"][0]["satisfied"] = False; rehash(false_condition)
missing_condition = variant(conditional_report, conditions=[])
protocol_condition = {"condition_id": "protocol-floor", "kind": "consumer_protocol_at_least", "expected_digest": None, "actual_digest": None, "expected_integer": 1, "actual_integer": 2, "satisfied": True}
protocol_report = variant(conditional_report, changes=[{"category": "relation_change", "semantic_id": "core.Agent", "classification": "conditionally_compatible", "semver_effect": "minor", "condition_id": "protocol-floor"}], conditions=[protocol_condition])
interval_condition = {"condition_id": "deprecation-floor", "kind": "deprecation_interval_at_least", "expected_digest": None, "actual_digest": None, "expected_integer": 2, "actual_integer": 2, "satisfied": True}
major_report = variant(compat_report, candidate_version="2.0.0", changes=[{"category": "removal", "semantic_id": "core.Legacy", "classification": "breaking", "semver_effect": "major", "condition_id": "deprecation-floor"}], conditions=[interval_condition], classification="breaking", required_semver_effect="major")
interval_report = copy.deepcopy(major_report)
bad_policy_rules = copy.deepcopy(compat_policy["category_rules"]); bad_policy_rules[-1] = copy.deepcopy(bad_policy_rules[0])
bad_compat_policy = variant(compat_policy, category_rules=bad_policy_rules)
patch_minor = variant(compat_report, candidate_version="1.0.1")
minor_for_major = variant(major_report, candidate_version="1.2.0")
early_removal = variant(removal, removed_ledger_revision=3)
reuse_report = variant(major_report, changes=[{"category": "identifier_reuse", "semantic_id": "core.Legacy", "classification": "breaking", "semver_effect": "major", "condition_id": None}])
bad_override = variant(override, change_digest=raw("identifier-reuse"))
cases += [
    case("minor_bump_satisfies_addition", "compatibility", compat_report, None, {"policy": compat_policy, "prior_version": "1.0.0"}),
    case("patch_bump_rejects_minor_effect", "compatibility", patch_minor, "semver_violation", {"policy": compat_policy, "prior_version": "1.0.0"}),
    case("major_bump_satisfies_breaking", "compatibility", major_report, None, {"policy": compat_policy, "prior_version": "1.1.0"}),
    case("minor_bump_rejects_major_effect", "compatibility", minor_for_major, "semver_violation", {"policy": compat_policy, "prior_version": "1.1.0"}),
    case("compatibility_policy_exact_categories", "compatibility_policy", compat_policy, None),
    case("compatibility_policy_duplicate_missing_category", "compatibility_policy", bad_compat_policy, "compatibility_rejected"),
    case("conditional_evidence_executes_true", "compatibility", conditional_report, None, {"policy": compat_policy, "prior_version": "1.0.0"}),
    case("consumer_protocol_floor_executes_true", "compatibility", protocol_report, None, {"policy": compat_policy, "prior_version": "1.0.0"}),
    case("deprecation_interval_condition_executes_true", "compatibility", interval_report, None, {"policy": compat_policy, "prior_version": "1.1.0"}),
    case("conditional_evidence_missing", "compatibility", missing_condition, "compatibility_rejected", {"policy": compat_policy, "prior_version": "1.0.0"}),
    case("conditional_evidence_false", "compatibility", false_condition, "compatibility_rejected", {"policy": compat_policy, "prior_version": "1.0.0"}),
    case("deprecation_interval_satisfied", "lifecycle", removal, None, {"deprecation": deprecation, "minimum": 2}),
    case("removal_before_interval_rejected", "lifecycle", early_removal, "lifecycle_violation", {"deprecation": deprecation, "minimum": 2}),
    case("tombstoned_identifier_reuse_rejected", "tombstone_reuse", reuse_report, "lifecycle_violation", {"tombstones": tombstones, "override": None}),
    case("override_cannot_legalize_identifier_reuse", "tombstone_reuse", reuse_report, "lifecycle_violation", {"tombstones": tombstones, "override": bad_override})]

stale_tx = variant(publish_tx, expected_prior_revision=0)
fork_tx = variant(publish_tx, expected_prior_head_digest=raw("fork-head"), transaction_id="fork")
version_reuse_tx = copy.deepcopy(publish_tx); version_reuse_tx["coordinate"]["capsule_digest"] = raw("different-capsule"); rehash(version_reuse_tx)
replay_tx = copy.deepcopy(publish_tx)
prepared = variant(publish_journal, state="prepared", linearized=False, recovery_action="discard_staging")
committing = variant(publish_journal, state="committing", linearized=True, recovery_action="complete_commit")
withdraw_recovery = variant(withdraw_journal, state="committing", linearized=True, recovery_action="complete_commit")
revoke_prepared = variant(revoke_journal, state="prepared", linearized=False, recovery_action="discard_staging")
aborted = variant(publish_journal, state="aborted", linearized=False, recovery_action="discard_staging")
bad_publish_reason = variant(publish_tx, status_reason_digest=raw("publish-must-not-have-reason"))
direct_revoke_tx = variant(revoke_tx, transaction_id="direct-revoke-1.1.0", expected_prior_revision=2, expected_prior_head_digest=d("owner_publication"), replay_key_digest=raw("direct-revoke-replay"))
direct_revoke_journal = variant(revoke_journal, transaction_digest=direct_revoke_tx["publication_transaction_digest"], prior_journal_digest=d("publication_journal"))
direct_revoke_marker = variant(revoke_marker, transaction_digest=direct_revoke_tx["publication_transaction_digest"], journal_digest=direct_revoke_journal["publication_journal_digest"], ledger_revision=3)
direct_revocation = variant(revoked_publication, from_status="published", prior_status_record_digest=d("owner_publication"), transaction_digest=direct_revoke_tx["publication_transaction_digest"], journal_digest=direct_revoke_journal["publication_journal_digest"], commit_marker_digest=direct_revoke_marker["publication_commit_marker_digest"], ledger_revision=3)
illegal_transition = variant(withdrawal, from_status="withdrawn", to_status="withdrawn")
bad_transition_link = variant(withdrawal, transaction_digest=raw("wrong-transaction"))
cases += [
    case("publication_fresh_cas_accepts", "publication_cas", publish_tx, None, {"current_revision": 1, "current_head": raw("publication-1"), "existing_replay_key": None}),
    case("publish_operation_rejects_status_reason", "publication_cas", bad_publish_reason, "lifecycle_violation", {"current_revision": 1, "current_head": raw("publication-1"), "existing_replay_key": None}),
    case("publication_stale_cas_rejected", "publication_cas", stale_tx, "publication_conflict", {"current_revision": 1, "current_head": raw("publication-1"), "existing_replay_key": None}),
    case("publication_idempotent_replay_returns_existing", "publication_cas", replay_tx, None, {"current_revision": 2, "current_head": d("owner_publication"), "existing_replay_key": publish_tx["replay_key_digest"], "existing_coordinate": coordinate}),
    case("publication_fork_rejected", "publication_cas", fork_tx, "publication_fork", {"current_revision": 1, "current_head": raw("publication-1"), "existing_replay_key": None}),
    case("namespace_version_digest_reuse_conflicts", "version_binding", version_reuse_tx, "version_conflict", {"existing_coordinate": coordinate}),
    case("withdrawal_transition_committed", "publication_transition", withdrawal, None, {"transaction": withdraw_tx, "journal": withdraw_journal, "marker": withdraw_marker}),
    case("withdrawn_to_revoked_transition_committed", "publication_transition", revoked_publication, None, {"transaction": revoke_tx, "journal": revoke_journal, "marker": revoke_marker}),
    case("published_to_revoked_transition_committed", "publication_transition", direct_revocation, None, {"transaction": direct_revoke_tx, "journal": direct_revoke_journal, "marker": direct_revoke_marker}),
    case("status_transition_link_drift_rejected", "publication_transition", bad_transition_link, "lifecycle_violation", {"transaction": withdraw_tx, "journal": withdraw_journal, "marker": withdraw_marker}),
    case("illegal_status_self_transition", "publication_transition", illegal_transition, "lifecycle_violation", {"transaction": withdraw_tx, "journal": withdraw_journal, "marker": withdraw_marker}, False),
    case("recovery_before_linearization_discards", "publication_recovery", prepared, None),
    case("recovery_after_linearization_completes", "publication_recovery", committing, None),
    case("withdrawal_recovery_after_linearization_completes", "publication_recovery", withdraw_recovery, None),
    case("revocation_recovery_before_linearization_discards", "publication_recovery", revoke_prepared, None),
    case("aborted_transaction_discards_staging", "publication_recovery", aborted, None),
    case("committed_without_linearization_rejected", "publication_recovery", variant(publish_journal, linearized=False), "recovery_needed")]

bad_projection = variant(materialization, expected_consumer_manifest_digest=raw("other-consumer-tree"))
bad_archive = variant(materialization, capsule_archive_linkage_digest=raw("other-archive"))
cases += [
    case("exact_payload_projection_accepts", "projection", materialization, None, {"projection": projection, "capsule": capsule, "archive_linkage": archive_link, "payload_manifest": payload, "consumer_manifest": consumer_manifest, "archive_manifest": archive_manifest}),
    case("consumer_tree_outside_projection_rejected", "projection", bad_projection, "projection_mismatch", {"projection": projection, "capsule": capsule, "archive_linkage": archive_link, "payload_manifest": payload, "consumer_manifest": consumer_manifest, "archive_manifest": archive_manifest}),
    case("capsule_archive_link_drift_rejected", "projection", bad_archive, "projection_mismatch", {"projection": projection, "capsule": capsule, "archive_linkage": archive_link, "payload_manifest": payload, "consumer_manifest": consumer_manifest, "archive_manifest": archive_manifest})]

runtime_missing = copy.deepcopy(runtime_request); del runtime_missing["target"]["runtime_revalidation_receipt_digest"]; rehash(runtime_missing)
bad_disable_receipt = variant(disable_receipt, active_state_after={"enabled": True, "coordinate": coordinate, "runtime_identity": rocs_tool})
bad_partial = variant(partial_receipt, stages=[{"stage": "semantic", "result": "completed", "error_digest": None}, {"stage": "runtime", "result": "completed", "error_digest": None}])
bad_failed_history = variant(failed_receipt, history_head_after={"kind": "rollback", "digest": raw("changed-history")})
cases += [
    case("semantic_rollback_retains_runtime", "rollback", semantic_receipt, None, {"request": semantic_request}),
    case("runtime_rollback_retains_semantic_and_revalidates", "rollback", runtime_receipt, None, {"request": runtime_request}),
    case("runtime_rollback_without_revalidation_rejected", "rollback", runtime_missing, "rollback_unavailable", {"request": runtime_missing}, False),
    case("no_prior_disable_clears_semantic", "rollback", disable_receipt, None, {"request": disable_request}),
    case("disable_that_leaves_semantic_active_rejected", "rollback", bad_disable_receipt, "history_conflict", {"request": disable_request}),
    case("combined_partial_failure_records_stages", "rollback", partial_receipt, None, {"request": combined_request}),
    case("partial_failure_without_failed_stage_rejected", "rollback", bad_partial, "history_conflict", {"request": combined_request}),
    case("failed_rollback_preserves_state_and_typed_head", "rollback", failed_receipt, None, {"request": semantic_request}),
    case("failed_rollback_changed_history_rejected", "rollback", bad_failed_history, "history_conflict", {"request": semantic_request})]

revoked_activation = variant(activation, revoked_by_digest=raw("activation-revocation"))
superseded_activation = variant(activation, superseded_by_activation_receipt_digest=raw("new-activation"))
cases += [
    case("generation_from_current_activation_accepts", "generation_activation", generation, None, {"activation": activation, "current_activation_digest": d("activation_receipt")}),
    case("generation_from_revoked_activation_rejected", "generation_activation", generation, "activation_not_current", {"activation": revoked_activation, "current_activation_digest": d("activation_receipt")}),
    case("generation_from_superseded_activation_rejected", "generation_activation", generation, "activation_not_current", {"activation": superseded_activation, "current_activation_digest": raw("new-activation")}),
    case("generation_from_nonhead_activation_rejected", "generation_activation", generation, "activation_not_current", {"activation": activation, "current_activation_digest": raw("different-activation")})]

digest_bad = copy.deepcopy(capsule); digest_bad["capsule_digest"] = raw("intentionally-wrong-digest")
invalid_date = variant(audit, recorded_at="2026-02-30T12:00:00Z")
rejected_decision = variant(consumer_decision, lifecycle_state="rejected")
revoked_decision = variant(consumer_decision, lifecycle_state="revoked", revocation_digest=raw("decision-revocation"))
superseded_decision = variant(consumer_decision, lifecycle_state="superseded")
bad_acceptance_scope = variant(acceptance, governing_scope_digest=raw("other-scope"))
self_acceptance = variant(acceptance, acceptance_authority={"kind": "rocs", "id": "rocs-cli"})
bad_activation_binding = variant(activation, stop_conditions_digest=raw("other-stop"))
pi_delivered_missing = copy.deepcopy(pi_delivered); del pi_delivered_missing["prompt_run_digest"]; rehash(pi_delivered_missing)
pi_suppressed_leak = copy.deepcopy(pi_suppressed); pi_suppressed_leak["prompt_run_digest"] = raw("must-not-exist"); rehash(pi_suppressed_leak)
pi_failed_missing = copy.deepcopy(pi_failed); del pi_failed_missing["error_digest"]; rehash(pi_failed_missing)
cases += [
    case("embedded_digest_mismatch_is_deterministic", "digest", digest_bad, "digest_mismatch"),
    case("calendar_valid_utc_accepts", "utc", audit, None),
    case("calendar_invalid_utc_rejected", "utc", invalid_date, "malformed_input"),
    case("canonical_accepted_ak_decision_accepts", "ak_decision", consumer_decision, None),
    case("rejected_ak_decision_fails_closed", "ak_decision", rejected_decision, "self_certification"),
    case("revoked_ak_decision_fails_closed", "ak_decision", revoked_decision, "self_certification"),
    case("superseded_ak_decision_fails_closed", "ak_decision", superseded_decision, "self_certification"),
    case("acceptance_owner_scope_binding_exact", "acceptance_binding", acceptance, None, {"decision": consumer_decision}),
    case("acceptance_scope_drift_rejected", "acceptance_binding", bad_acceptance_scope, "self_certification", {"decision": consumer_decision}),
    case("rocs_cannot_self_certify_acceptance", "acceptance_binding", self_acceptance, "self_certification", {"decision": consumer_decision}),
    case("activation_decision_bindings_exact", "activation_binding", activation, None, {"decision": consumer_decision}),
    case("activation_stop_binding_drift_rejected", "activation_binding", bad_activation_binding, "self_certification", {"decision": consumer_decision}),
    case("pi_delivered_variant_accepts", "pi_variant", pi_delivered, None),
    case("pi_suppressed_variant_accepts", "pi_variant", pi_suppressed, None),
    case("pi_failed_variant_accepts", "pi_variant", pi_failed, None),
    case("delivered_without_prompt_run_rejected", "pi_variant", pi_delivered_missing, "malformed_input", schema_valid=False),
    case("suppressed_cannot_claim_prompt_delivery", "pi_variant", pi_suppressed_leak, "malformed_input", schema_valid=False),
    case("failed_without_error_rejected", "pi_variant", pi_failed_missing, "malformed_input", schema_valid=False),
    case("ak_generation_only_linkage_accepts_without_pi", "ak_optional_pi", ak_generation_only, None),
    case("ak_delivered_linkage_requires_pi_digest", "ak_optional_pi", ak_link, None)]

differential = {"protocol": "semantic-release-v0", "rfc_revision": "semantic-release-revision-v2", "cases": cases}

write_schema()
for path, value in ((ROOT / "golden-fixtures.json", golden), (ROOT / "differential-fixtures.json", differential)):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"wrote schema, {len(records)} golden records, and {len(cases)} differential cases")
