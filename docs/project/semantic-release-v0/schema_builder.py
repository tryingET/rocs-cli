#!/usr/bin/env python3
"""Deterministically build the closed Decision 53 protocol schema."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent


def ref(name: str) -> dict[str, str]:
    return {"$ref": f"#/$defs/{name}"}


def nullable(value: dict[str, Any]) -> dict[str, Any]:
    return {"oneOf": [{"type": "null"}, value]}


def array(item: dict[str, Any], maximum: int = 100000, minimum: int = 0) -> dict[str, Any]:
    return {"type": "array", "minItems": minimum, "maxItems": maximum, "items": item}


def obj(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": required if required is not None else list(properties),
        "properties": properties,
    }


def protocol(schema: str, properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return obj({"schema": {"const": schema}, **properties}, required and ["schema", *required])


def build_schema() -> dict[str, Any]:
    d: dict[str, Any] = {}
    d["digest"] = {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}
    d["identifier"] = {"type": "string", "minLength": 1, "maxLength": 256, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:/+-]*$"}
    d["namespace"] = {"type": "string", "minLength": 3, "maxLength": 128, "pattern": "^[a-z0-9]+(?:[.-][a-z0-9]+)+$"}
    d["semver"] = {"type": "string", "minLength": 5, "maxLength": 256, "pattern": "^(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)\\.(0|[1-9][0-9]*)(?:-((?:0|[1-9][0-9]*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)(?:\\.(?:0|[1-9][0-9]*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*))*))?(?:\\+([0-9A-Za-z-]+(?:\\.[0-9A-Za-z-]+)*))?$"}
    d["safeInteger"] = {"type": "integer", "minimum": 0, "maximum": 9007199254740991}
    d["text"] = {"type": "string", "minLength": 1, "maxLength": 4096}
    d["logicalPath"] = {"type": "string", "minLength": 1, "maxLength": 4096, "pattern": "^(?!/)(?!.*(?:^|/)\\.{1,2}(?:/|$))(?!.*//)(?!.*\\\\)[^\\u0000]+$"}
    d["coordinate"] = protocol("semantic-release-coordinate.v0", {
        "namespace": ref("namespace"), "semantic_version": ref("semver"), "capsule_digest": ref("digest")})
    d["repositoryIdentity"] = obj({
        "owner": ref("identifier"), "repository_id": ref("identifier"), "canonical_locator": ref("text"), "identity_revision": ref("safeInteger")})
    d["v0ConsumerRepositoryIdentity"] = obj({
        "owner": {"const": "consumer-owner"}, "repository_id": {"const": "pi-canary-consumer"},
        "canonical_locator": {"const": "local://softwareco/pi-canary-consumer"}, "identity_revision": {"const": 3}})
    d["v0CanaryScope"] = obj({
        "consumer_repository": ref("v0ConsumerRepositoryIdentity"), "operator_canary_name": ref("identifier"), "naming_authority": {"const": "operator"},
        "canary_cardinality": {"const": 1}, "adoption_mode": {"const": "single_operator_named_canary"},
        "expansion_authority": {"const": "new_protocol_and_decision_required"}})
    d["toolIdentity"] = obj({
        "tool": ref("identifier"), "version": ref("semver"), "distribution_digest": ref("digest"), "protocol_version": {"const": "semantic-release-v0"}})
    d["issuer"] = obj({"kind": {"enum": ["semantic_owner", "consumer_owner", "rocs", "pi", "ak", "recovery_controller"]}, "id": ref("identifier")})
    d["trustReference"] = obj({
        "trust_root_id": ref("identifier"), "trust_root_revision": ref("safeInteger"), "trust_root_digest": ref("digest"),
        "publication_ledger_revision": ref("safeInteger"), "publication_digest": ref("digest"), "local_revocation_revision": ref("safeInteger"),
        "local_revocation_head_digest": nullable(ref("digest")), "trust_snapshot_digest": ref("digest")})
    d["historyHead"] = obj({"kind": {"enum": ["activation", "rollback", "disable"]}, "digest": ref("digest")})
    d["activeState"] = obj({"enabled": {"type": "boolean"}, "coordinate": nullable(ref("coordinate")), "runtime_identity": ref("toolIdentity")})
    d["fileEntry"] = obj({"path": ref("logicalPath"), "kind": {"const": "file"}, "mode": {"enum": [420, 493]}, "byte_length": ref("safeInteger"), "content_digest": ref("digest")})
    d["directoryEntry"] = obj({"path": ref("logicalPath"), "kind": {"const": "directory"}, "mode": {"const": 493}})
    d["symlinkEntry"] = obj({"path": ref("logicalPath"), "kind": {"const": "symlink"}, "mode": {"const": 511}, "target": ref("logicalPath"), "target_byte_length": ref("safeInteger"), "target_digest": ref("digest")})
    d["sourceEntry"] = {"oneOf": [ref("fileEntry"), ref("directoryEntry"), ref("symlinkEntry")]}
    d["materialEntry"] = {"oneOf": [ref("fileEntry"), ref("directoryEntry")]}
    d["sourceManifest"] = protocol("semantic-source-manifest.v0", {
        "repository": ref("repositoryIdentity"), "source_revision": ref("identifier"), "source_root": ref("logicalPath"), "clean_committed": {"const": True},
        "entries": array(ref("sourceEntry"), minimum=1), "source_manifest_digest": ref("digest")})
    d["materialManifest"] = protocol("semantic-material-manifest.v0", {
        "tree_role": {"enum": ["compiled_payload", "capsule_archive", "consumer_materialization"]}, "entries": array(ref("materialEntry"), minimum=1), "material_manifest_digest": ref("digest")})

    d["ownerMember"] = obj({"owner_id": ref("identifier"), "key_ids": array(ref("identifier"), 64, 1), "status": {"enum": ["active", "revoked"]}, "revocation_digest": nullable(ref("digest"))})
    d["ownerSet"] = protocol("semantic-owner-set.v0", {
        "namespace": ref("namespace"), "owner_set_revision": ref("safeInteger"), "members": array(ref("ownerMember"), 64, 1), "prior_owner_set_digest": nullable(ref("digest")), "owner_set_digest": ref("digest")})
    d["approvalPredicate"] = protocol("semantic-approval-predicate.v0", {
        "namespace": ref("namespace"), "predicate_revision": ref("safeInteger"), "mode": {"enum": ["threshold", "unanimous"]}, "threshold": ref("safeInteger"),
        "eligible_owner_status": {"const": "active"}, "distinct_owner_required": {"const": True}, "approval_predicate_digest": ref("digest")})
    d["ownerPolicy"] = protocol("semantic-owner-policy.v0", {
        "namespace": ref("namespace"), "policy_revision": ref("safeInteger"), "governing_scope_digest": ref("digest"), "owner_set_digest": ref("digest"),
        "approval_predicate_digest": ref("digest"), "compatibility_policy_digest": ref("digest"), "trust_bootstrap_mode": {"const": "owner_controlled_local_out_of_band"},
        "rotation_requires_old_root": {"const": True}, "revocation_fail_closed": {"const": True}, "prior_owner_policy_digest": nullable(ref("digest")), "owner_policy_digest": ref("digest")})
    d["trustRoot"] = protocol("semantic-trust-root.v0", {
        "namespace": ref("namespace"), "trust_root_id": ref("identifier"), "trust_root_revision": ref("safeInteger"), "owner_policy_digest": ref("digest"),
        "owner_set_digest": ref("digest"), "key_ids": array(ref("identifier"), 64, 1), "minimum_ledger_revision": ref("safeInteger"), "prior_trust_root_digest": nullable(ref("digest")),
        "status": {"const": "active"}, "trust_root_digest": ref("digest")})
    d["externalTrustRootPin"] = obj({
        "namespace": ref("namespace"), "trust_root_id": ref("identifier"), "trust_root_revision": ref("safeInteger"),
        "trust_root_digest": ref("digest"), "owner_policy_digest": ref("digest"), "owner_set_digest": ref("digest"),
        "revocation_revision": ref("safeInteger"), "revocation_head_digest": nullable(ref("digest"))})
    d["trustRotation"] = protocol("semantic-trust-rotation.v0", {
        "namespace": ref("namespace"), "old_trust_root_id": ref("identifier"), "old_trust_root_revision": ref("safeInteger"), "old_trust_root_digest": ref("digest"),
        "new_trust_root_id": ref("identifier"), "new_trust_root_revision": ref("safeInteger"), "new_trust_root_digest": ref("digest"), "owner_policy_digest": ref("digest"),
        "owner_set_digest": ref("digest"), "approval_predicate_digest": ref("digest"), "approval_digest": ref("digest"),
        "rotation_revision": ref("safeInteger"), "trust_rotation_digest": ref("digest")})
    d["trustRevocation"] = protocol("semantic-trust-revocation.v0", {
        "namespace": ref("namespace"), "revocation_revision": ref("safeInteger"), "target_kind": {"enum": ["owner_key", "owner_set", "owner_policy", "trust_root"]},
        "target_digest": ref("digest"), "effective_ledger_revision": ref("safeInteger"), "reason_digest": ref("digest"), "owner_approval_digest": ref("digest"),
        "prior_revocation_digest": nullable(ref("digest")), "trust_revocation_digest": ref("digest")})

    d["conditionRule"] = obj({"condition_kind": {"enum": ["evidence_digest_equals", "consumer_protocol_at_least", "deprecation_interval_at_least"]}, "required": {"const": True}})
    d["categoryRule"] = obj({"category": {"enum": ["addition", "documentation", "compatible_refinement", "deprecation", "removal", "constraint_change", "relation_change", "identifier_reuse", "other"]},
        "classification": {"enum": ["compatible", "conditionally_compatible", "breaking", "unknown"]}, "semver_effect": {"enum": ["patch", "minor", "major", "unknown"]}, "condition_rule": nullable(ref("conditionRule")), "override_allowed": {"type": "boolean"}})
    d["compatibilityPolicy"] = protocol("semantic-compatibility-policy.v0", {
        "namespace": ref("namespace"), "policy_revision": ref("safeInteger"), "category_rules": array(ref("categoryRule"), 9, 9), "severity_order": {"const": ["patch", "minor", "major", "unknown"]},
        "initial_zero_exceptions": {"const": False}, "minimum_deprecation_releases": ref("safeInteger"), "identifier_reuse_override_forbidden": {"const": True}, "prior_policy_digest": nullable(ref("digest")), "compatibility_policy_digest": ref("digest")})
    d["compatibilityCondition"] = obj({"condition_id": ref("identifier"), "kind": {"enum": ["evidence_digest_equals", "consumer_protocol_at_least", "deprecation_interval_at_least"]},
        "expected_digest": nullable(ref("digest")), "actual_digest": nullable(ref("digest")), "expected_integer": nullable(ref("safeInteger")), "actual_integer": nullable(ref("safeInteger")), "satisfied": {"type": "boolean"}})
    d["compatibilityChange"] = obj({"category": {"enum": ["addition", "documentation", "compatible_refinement", "deprecation", "removal", "constraint_change", "relation_change", "identifier_reuse", "other"]},
        "semantic_id": ref("identifier"), "classification": {"enum": ["compatible", "conditionally_compatible", "breaking", "unknown"]},
        "semver_effect": {"enum": ["patch", "minor", "major", "unknown"]}, "condition_id": nullable(ref("identifier"))})
    d["compatibilityReport"] = protocol("semantic-compatibility-report.v0", {
        "namespace": ref("namespace"), "prior_coordinate": nullable(ref("coordinate")), "candidate_version": ref("semver"), "compatibility_policy_digest": ref("digest"),
        "changes": array(ref("compatibilityChange")), "conditions": array(ref("compatibilityCondition"), 10000), "classification": {"enum": ["compatible", "conditionally_compatible", "breaking", "unknown"]},
        "required_semver_effect": {"enum": ["patch", "minor", "major", "unknown"]}, "override_digests": array(ref("digest"), 10000), "compatibility_report_digest": ref("digest")})
    d["compatibilityOverride"] = protocol("semantic-compatibility-override.v0", {
        "namespace": ref("namespace"), "compatibility_policy_digest": ref("digest"), "change": ref("compatibilityChange"), "change_digest": ref("digest"),
        "from_classification": {"enum": ["unknown", "breaking"]}, "from_semver_effect": {"enum": ["major", "unknown"]},
        "to_classification": {"enum": ["conditionally_compatible", "breaking"]}, "semver_effect_floor": {"enum": ["patch", "minor", "major"]}, "condition": ref("compatibilityCondition"),
        "owner_approval_digest": ref("digest"), "compatibility_override_digest": ref("digest")})
    d["deprecationRecord"] = protocol("semantic-deprecation-record.v0", {
        "namespace": ref("namespace"), "semantic_id": ref("identifier"), "introduced_coordinate": ref("coordinate"), "introduced_ledger_revision": ref("safeInteger"),
        "prior_lifecycle_digest": nullable(ref("digest")), "deprecation_record_digest": ref("digest")})
    d["removalRecord"] = protocol("semantic-removal-record.v0", {
        "namespace": ref("namespace"), "semantic_id": ref("identifier"), "removed_coordinate": ref("coordinate"), "removed_ledger_revision": ref("safeInteger"),
        "deprecation_record_digest": ref("digest"), "deprecation_ledger_revision": ref("safeInteger"), "prior_lifecycle_digest": ref("digest"),
        "compatibility_policy_digest": ref("digest"), "required_interval": ref("safeInteger"), "prior_tombstone_registry_digest": nullable(ref("digest")), "removal_record_digest": ref("digest")})
    d["tombstoneEntry"] = obj({"semantic_id": ref("identifier"), "reason": {"const": "removed"}, "origin_record_digest": ref("digest")})
    d["tombstoneRegistry"] = protocol("semantic-tombstone-registry.v0", {
        "namespace": ref("namespace"), "lifecycle_head_digest": ref("digest"), "registry_revision": ref("safeInteger"),
        "entries": array(ref("tombstoneEntry")), "prior_registry_digest": nullable(ref("digest")),
        "tombstone_registry_digest": ref("digest")})
    d["tombstoneHistoryDelta"] = obj({
        "authorization_kind": {"enum": ["genesis", "removal"]}, "authorization_record_digest": ref("digest"),
        "prior_lifecycle_head_digest": nullable(ref("digest")), "resulting_lifecycle_head_digest": ref("digest"),
        "added_entries": array(ref("tombstoneEntry"), 1)})
    d["tombstoneHistoryRevision"] = obj({"registry": ref("tombstoneRegistry"), "authorized_delta": ref("tombstoneHistoryDelta")})
    d["tombstoneHistoryProof"] = protocol("semantic-tombstone-history-proof.v0", {
        "issuer": obj({"kind": {"const": "semantic_owner"}, "id": {"const": "semantic-owner"}}),
        "namespace": ref("namespace"), "current_lifecycle_head_digest": ref("digest"),
        "current_registry_digest": ref("digest"), "current_registry_revision": ref("safeInteger"),
        "revisions": array(ref("tombstoneHistoryRevision"), 100000, 1),
        "semantic_tombstone_history_proof_digest": ref("digest")})
    d["publicationLedgerHead"] = protocol("semantic-publication-ledger-head.v0", {
        "namespace": ref("namespace"), "ledger_revision": ref("safeInteger"), "ledger_head_digest": ref("digest"),
        "status_record_digest": ref("digest"), "transaction_digest": ref("digest"), "journal_digest": ref("digest"),
        "commit_marker_digest": ref("digest"), "prior_ledger_head_digest": nullable(ref("digest")),
        "publication_ledger_head_digest": ref("digest")})
    d["acceptedLifecycleLedgerRecord"] = protocol("semantic-accepted-lifecycle-ledger-record.v0", {
        "namespace": ref("namespace"), "ledger_revision": ref("safeInteger"), "ledger_head_digest": ref("digest"), "coordinate": ref("coordinate"),
        "publication_status_record_digest": ref("digest"), "publication_transaction_digest": ref("digest"),
        "publication_journal_digest": ref("digest"), "publication_commit_marker_digest": ref("digest"),
        "owner_approval_digest": ref("digest"), "trust_root_digest": ref("digest"), "canonical_ledger_digest": ref("digest"),
        "publication_status": {"const": "published"}, "accepted_for_lifecycle": {"const": True},
        "accepted_lifecycle_ledger_record_digest": ref("digest")})

    d["projectionEntry"] = obj({"capsule_path": ref("logicalPath"), "consumer_path": ref("logicalPath"), "mode": {"enum": [420, 493]}, "byte_length": nullable(ref("safeInteger")), "content_digest": nullable(ref("digest"))})
    d["payloadProjection"] = protocol("semantic-payload-projection.v0", {
        "payload_manifest_digest": ref("digest"), "consumer_manifest_digest": ref("digest"), "entries": array(ref("projectionEntry"), minimum=1), "projection_mode": {"const": "exact_no_extra_no_missing"}, "payload_projection_digest": ref("digest")})
    d["capsuleMetadata"] = obj({"schema": {"const": "semantic-capsule-metadata.v0"}, "namespace": ref("namespace"), "semantic_version": ref("semver"),
        "payload_manifest_digest": ref("digest"), "identity_mode": {"const": "no_capsule_archive_or_linkage_digest"}})
    d["capsuleArchiveLinkage"] = protocol("semantic-capsule-archive-linkage.v0", {
        "archive_manifest_digest": ref("digest"), "payload_manifest_digest": ref("digest"), "payload_root": ref("logicalPath"), "capsule_metadata_path": ref("logicalPath"),
        "capsule_metadata": ref("capsuleMetadata"), "capsule_metadata_content_digest": ref("digest"),
        "archive_format": {"enum": ["tar-pax-v0", "directory-v0"]}, "capsule_archive_linkage_digest": ref("digest")})
    d["capsule"] = protocol("semantic-release-capsule.v0", {
        "namespace": ref("namespace"), "semantic_version": ref("semver"), "source_manifest_digest": ref("digest"), "semantic_payload_digest": ref("digest"),
        "payload_manifest_digest": ref("digest"), "payload_projection_digest": ref("digest"), "capsule_archive_linkage_digest": ref("digest"), "compatibility_report_digest": ref("digest"),
        "owner_policy_digest": ref("digest"), "compilation_contract_digest": ref("digest"), "required_protocol_versions": array(ref("identifier"), 64, 1),
        "predecessor_coordinate": nullable(ref("coordinate")), "lifecycle_head_digest": ref("digest"),
        "tombstone_registry_digest": ref("digest"), "tombstone_registry_revision": ref("safeInteger"),
        "capsule_digest": ref("digest")})
    d["akStoreHead"] = obj({"store_id": ref("identifier"), "canonical_store_locator": ref("text"), "store_revision": ref("safeInteger"),
        "store_head_digest": ref("digest"), "revocation_head_digest": nullable(ref("digest"))})
    d["akDecisionReference"] = protocol("semantic-ak-decision-reference.v0", {
        "ak_repository": ref("repositoryIdentity"), "ak_runtime_identity": ref("toolIdentity"), "ak_store_head": ref("akStoreHead"),
        "decision_id": ref("identifier"), "decision_revision": ref("safeInteger"), "decision_record_digest": ref("digest"),
        "lifecycle_state": {"enum": ["accepted", "rejected", "revoked", "superseded"]}, "adr_reference": obj({"adr_id": ref("identifier"), "adr_revision": ref("safeInteger"), "adr_digest": ref("digest"), "status": {"enum": ["accepted", "superseded", "revoked"]}}),
        "scope_digest": ref("digest"), "revocation_digest": nullable(ref("digest")), "superseded_by_decision_record_digest": nullable(ref("digest")),
        "activation_target_digest": ref("digest"), "evidence_criteria_digest": ref("digest"), "rollback_plan_digest": ref("digest"), "stop_conditions_digest": ref("digest"),
        "ak_decision_reference_digest": ref("digest")})
    release_action = obj({"kind": {"const": "release"}, "source_manifest_digest": ref("digest"), "candidate_capsule_digest": ref("digest"), "compatibility_report_digest": ref("digest")})
    rotation_action = obj({"kind": {"const": "trust_rotation"}, "namespace": ref("namespace"), "old_trust_root_digest": ref("digest"), "new_trust_root_digest": ref("digest"),
        "owner_policy_digest": ref("digest"), "owner_set_digest": ref("digest"), "approval_predicate_digest": ref("digest"),
        "new_trust_root_revision": ref("safeInteger"), "rotation_revision": ref("safeInteger")})
    revocation_action = obj({"kind": {"const": "trust_revocation"}, "namespace": ref("namespace"), "owner_policy_digest": ref("digest"),
        "owner_set_digest": ref("digest"), "approval_predicate_digest": ref("digest"), "target_kind": {"enum": ["owner_key", "owner_set", "owner_policy", "trust_root"]},
        "target_digest": ref("digest"), "effective_ledger_revision": ref("safeInteger"), "reason_digest": ref("digest"), "prior_revocation_digest": nullable(ref("digest")), "revocation_revision": ref("safeInteger")})
    override_action = obj({"kind": {"const": "compatibility_override"}, "namespace": ref("namespace"), "compatibility_policy_digest": ref("digest"),
        "change": ref("compatibilityChange"), "change_digest": ref("digest"), "from_classification": {"enum": ["unknown", "breaking"]},
        "from_semver_effect": {"enum": ["major", "unknown"]}, "to_classification": {"enum": ["conditionally_compatible", "breaking"]},
        "semver_effect_floor": {"enum": ["patch", "minor", "major"]}, "condition": ref("compatibilityCondition")})
    publication_action_common = {"namespace": ref("namespace"), "owner_policy_digest": ref("digest"), "owner_set_digest": ref("digest"),
        "approval_predicate_digest": ref("digest"), "coordinate": ref("coordinate"), "prior_status_record_digest": ref("digest"),
        "prior_status": {"enum": ["published", "withdrawn"]}, "reason_digest": ref("digest"), "expected_prior_revision": ref("safeInteger"),
        "expected_prior_head_digest": ref("digest")}
    withdrawal_action = obj({"kind": {"const": "publication_withdrawal"}, "operation": {"const": "withdraw"}, **publication_action_common})
    publication_revocation_action = obj({"kind": {"const": "publication_revocation"}, "operation": {"const": "revoke"}, **publication_action_common})
    d["approvalAction"] = {"oneOf": [release_action, rotation_action, revocation_action, override_action, withdrawal_action, publication_revocation_action]}
    d["approvalVote"] = obj({"owner_id": ref("identifier"), "owner_key_id": ref("identifier"), "approved_action_digest": ref("digest"), "approval_proof_digest": ref("digest")})
    d["ownerApproval"] = protocol("semantic-owner-approval.v0", {
        "namespace": ref("namespace"), "owner_policy_digest": ref("digest"), "owner_set_digest": ref("digest"), "approval_predicate_digest": ref("digest"),
        "action": ref("approvalAction"), "action_digest": ref("digest"), "votes": array(ref("approvalVote"), 64, 1),
        "decision_reference_digest": ref("digest"), "owner_approval_digest": ref("digest")})
    d["buildReceipt"] = protocol("semantic-build-receipt.v0", {
        "source_manifest_digest": ref("digest"), "compilation_contract_digest": ref("digest"), "tool_identity": ref("toolIdentity"), "payload_manifest_digest": ref("digest"),
        "payload_projection_digest": ref("digest"), "capsule_archive_linkage_digest": ref("digest"), "semantic_payload_digest": ref("digest"), "compatibility_report_digest": ref("digest"),
        "candidate_capsule_digest": ref("digest"), "reproducible": {"const": True}, "build_receipt_digest": ref("digest")})

    d["publicationTransaction"] = protocol("semantic-publication-transaction.v0", {
        "transaction_id": ref("identifier"), "operation": {"enum": ["publish", "withdraw", "revoke"]}, "namespace": ref("namespace"), "coordinate": ref("coordinate"),
        "owner_approval_digest": ref("digest"), "expected_prior_revision": ref("safeInteger"), "expected_prior_head_digest": nullable(ref("digest")), "replay_key_digest": ref("digest"),
        "status_reason_digest": nullable(ref("digest")), "publication_transaction_digest": ref("digest")})
    d["publicationJournal"] = protocol("semantic-publication-journal.v0", {
        "transaction_digest": ref("digest"), "state": {"enum": ["prepared", "committing", "committed", "aborted"]}, "resulting_record_digest": ref("digest"),
        "resulting_ledger_revision": ref("safeInteger"), "resulting_ledger_head_digest": ref("digest"), "staged_blob_set_digest": ref("digest"),
        "linearized": {"type": "boolean"}, "recovery_action": {"enum": ["discard_staging", "complete_commit", "none"]},
        "prior_journal_digest": nullable(ref("digest")), "recovery_controller_id": ref("identifier"),
        "recovery_runtime_identity": ref("toolIdentity"), "recovery_epoch": ref("safeInteger"),
        "publication_journal_digest": ref("digest")})
    d["publicationRecoveryIntentMarker"] = protocol("semantic-publication-recovery-intent-marker.v0", {
        "issuer": ref("issuer"), "transaction_digest": ref("digest"), "journal_digest": ref("digest"),
        "resulting_record_digest": ref("digest"), "resulting_ledger_revision": ref("safeInteger"),
        "resulting_ledger_head_digest": ref("digest"), "marker_semantics": {"const": "non_durable_intent_only"},
        "fsync_complete": {"const": False}, "durable_commit_marker_present": {"const": False},
        "publication_recovery_intent_marker_digest": ref("digest")})
    d["publicationCommitMarker"] = protocol("semantic-publication-commit-marker.v0", {
        "transaction_digest": ref("digest"), "journal_digest": ref("digest"), "resulting_record_digest": ref("digest"),
        "resulting_ledger_revision": ref("safeInteger"), "resulting_ledger_head_digest": ref("digest"),
        "fsync_complete": {"const": True}, "publication_commit_marker_digest": ref("digest")})
    d["ownerPublication"] = protocol("semantic-owner-publication.v0", {
        "coordinate": ref("coordinate"), "transaction_digest": ref("digest"), "owner_approval_digest": ref("digest"), "ledger_namespace": ref("namespace"), "ledger_revision": ref("safeInteger"),
        "prior_publication_digest": nullable(ref("digest")), "trust_root_digest": ref("digest"), "status": {"const": "published"}, "owner_publication_digest": ref("digest")})
    transition_common = {"coordinate": ref("coordinate"), "prior_status_record_digest": ref("digest"), "transaction_digest": ref("digest"),
        "owner_approval_digest": ref("digest"), "reason_digest": ref("digest"), "ledger_revision": ref("safeInteger"),
        "publication_status_transition_digest": ref("digest")}
    d["publicationStatusTransition"] = {"oneOf": [
        protocol("semantic-publication-status-transition.v0", {"from_status": {"const": "published"}, "to_status": {"const": "withdrawn"}, **transition_common}),
        protocol("semantic-publication-status-transition.v0", {"from_status": {"enum": ["published", "withdrawn"]}, "to_status": {"const": "revoked"}, **transition_common})]}
    d["publicationStatusRecord"] = {"oneOf": [ref("ownerPublication"), ref("publicationStatusTransition")]}
    d["publicationRecoveryState"] = obj({"revision": ref("safeInteger"), "head": ref("digest"),
        "status_record_digest": ref("digest"), "intent_marker_digest": nullable(ref("digest")),
        "durable_commit_marker_digest": nullable(ref("digest")), "staging_present": {"type": "boolean"}})
    recovery_state_common = {"semantic_owner_id": ref("identifier"), "recovery_controller_id": ref("identifier"),
        "recovery_epoch": ref("safeInteger"), "namespace": ref("namespace"), "transaction_digest": ref("digest"),
        "recovery_journal_digest": ref("digest"), "state": ref("publicationRecoveryState"),
        "publication_recovery_state_receipt_digest": ref("digest")}
    recovery_before = protocol("semantic-publication-recovery-state-receipt.v0", {
        "phase": {"const": "before"}, "issuer": obj({"kind": {"const": "semantic_owner"}, "id": ref("identifier")}),
        **recovery_state_common})
    recovery_after = protocol("semantic-publication-recovery-state-receipt.v0", {
        "phase": {"const": "after"}, "issuer": obj({"kind": {"const": "recovery_controller"}, "id": ref("identifier")}),
        **recovery_state_common})
    d["publicationRecoveryStateReceipt"] = {"oneOf": [recovery_before, recovery_after]}

    d["semanticRollbackTarget"] = obj({"kind": {"const": "semantic"}, "semantic_action": {"const": "switch"}, "target_coordinate": ref("coordinate"), "runtime_action": {"const": "retain"}, "target_materialization_receipt_digest": ref("digest")})
    d["runtimeRollbackTarget"] = obj({"kind": {"const": "runtime"}, "semantic_action": {"const": "retain"}, "runtime_action": {"const": "switch"}, "target_runtime_identity": ref("toolIdentity"), "target_materialization_receipt_digest": ref("digest"), "runtime_revalidation_receipt_digest": ref("digest")})
    d["disableRollbackTarget"] = obj({"kind": {"const": "no_prior_disable"}, "semantic_action": {"const": "disable"}, "runtime_action": {"const": "retain"}, "disable_contract_digest": ref("digest"), "rehearsal_receipt_digest": ref("digest")})
    d["combinedRollbackTarget"] = obj({"kind": {"const": "combined"}, "semantic_stage": ref("semanticRollbackTarget"), "runtime_stage": ref("runtimeRollbackTarget"), "stage_order": {"enum": ["semantic_then_runtime", "runtime_then_semantic"]}})
    d["rollbackTarget"] = {"oneOf": [ref("semanticRollbackTarget"), ref("runtimeRollbackTarget"), ref("disableRollbackTarget"), ref("combinedRollbackTarget")]}
    d["consumerIntent"] = protocol("semantic-consumer-intent.v0", {
        "consumer_repository": ref("v0ConsumerRepositoryIdentity"), "canary_scope": ref("v0CanaryScope"),
        "intent_revision": ref("safeInteger"), "desired_coordinate": ref("coordinate"), "runtime_identity": ref("toolIdentity"),
        "accepted_compatibility": {"enum": ["compatible", "conditionally_compatible"]}, "rollback_target": ref("rollbackTarget"), "decision_reference_digest": ref("digest"),
        "trust_reference": ref("trustReference"), "verifier_contract_digest": ref("digest"), "limits_digest": ref("digest"), "consumer_intent_digest": ref("digest")})
    d["ownerAcceptance"] = protocol("semantic-owner-acceptance.v0", {
        "consumer_intent_digest": ref("digest"), "consumer_repository": ref("v0ConsumerRepositoryIdentity"), "canary_scope": ref("v0CanaryScope"),
        "acceptance_authority": ref("issuer"), "acceptance_revision": ref("safeInteger"), "acceptance_epoch": ref("safeInteger"),
        "governing_scope_digest": ref("digest"), "decision_reference_digest": ref("digest"), "valid_through_intent_revision": ref("safeInteger"),
        "activation_epoch_not_after": ref("safeInteger"), "revoked_by_digest": nullable(ref("digest")), "owner_acceptance_digest": ref("digest")})
    d["materializationVerificationReceipt"] = protocol("semantic-materialization-verification-receipt.v0", {
        "issuer": ref("issuer"), "consumer_intent_digest": ref("digest"), "owner_acceptance_digest": ref("digest"), "coordinate": ref("coordinate"), "owner_approval_digest": ref("digest"),
        "trust_reference": ref("trustReference"), "runtime_identity": ref("toolIdentity"), "capsule_archive_linkage_digest": ref("digest"), "payload_projection_digest": ref("digest"),
        "source_payload_manifest_digest": ref("digest"), "expected_consumer_manifest_digest": ref("digest"), "actual_consumer_manifest_digest": ref("digest"), "consumer_repository": ref("v0ConsumerRepositoryIdentity"),
        "canary_scope": ref("v0CanaryScope"), "compatibility_report_digest": ref("digest"), "compatibility_outcome": {"enum": ["compatible", "conditionally_compatible", "breaking", "unknown"]}, "prior_receipt_digest": nullable(ref("digest")),
        "rollback_target": ref("rollbackTarget"), "rollback_ready": {"type": "boolean"}, "verifier_contract_digest": ref("digest"), "transaction_id": ref("identifier"),
        "journal_state": {"const": "committed"}, "commit_marker_digest": ref("digest"), "materialization_verification_receipt_digest": ref("digest")})
    d["activationReceipt"] = protocol("semantic-activation-receipt.v0", {
        "issuer": ref("issuer"), "consumer_owner_issuer_id": ref("identifier"), "consumer_intent_digest": ref("digest"),
        "owner_acceptance_digest": ref("digest"), "materialization_verification_receipt_digest": ref("digest"),
        "rollback_availability_proof_digest": ref("digest"), "consumer_repository": ref("v0ConsumerRepositoryIdentity"),
        "canary_scope": ref("v0CanaryScope"), "coordinate": ref("coordinate"), "runtime_identity": ref("toolIdentity"),
        "activation_revision": ref("safeInteger"), "prior_activation_revision": nullable(ref("safeInteger")),
        "activation_epoch": ref("safeInteger"), "acceptance_epoch": ref("safeInteger"),
        "gate_decision_reference_digest": ref("digest"), "activation_target_digest": ref("digest"), "evidence_criteria_digest": ref("digest"), "rollback_plan_digest": ref("digest"),
        "stop_conditions_digest": ref("digest"), "current_activation_head_digest": nullable(ref("digest")),
        "previous_activation_receipt_digest": nullable(ref("digest")), "status": {"const": "activated"}, "revoked_by_digest": nullable(ref("digest")),
        "superseded_by_activation_receipt_digest": nullable(ref("digest")), "activation_receipt_digest": ref("digest")})
    d["rocsGenerationReceipt"] = protocol("semantic-rocs-generation-receipt.v0", {
        "issuer": ref("issuer"), "claim_scope": {"const": "generated_output_only"}, "activation_receipt_digest": ref("digest"),
        "activation_head_revision": ref("safeInteger"), "activation_head_digest": ref("digest"), "coordinate": ref("coordinate"), "runtime_identity": ref("toolIdentity"),
        "request_digest": ref("digest"), "result_digest": ref("digest"), "effective_execution_digest": ref("digest"), "candidate_ids": array(ref("identifier"), 256), "pack_digests": array(ref("digest"), 256),
        "outcome": {"enum": ["matched", "ambiguous", "no_match", "not_applicable", "unavailable"]}, "rocs_generation_receipt_digest": ref("digest")})

    delivered = protocol("semantic-pi-delivery-receipt.v0", {"issuer": ref("issuer"), "claim_scope": {"const": "delivered_to_prompt_run_only"}, "rocs_generation_receipt_digest": ref("digest"),
        "delivery_outcome": {"const": "delivered"}, "prompt_run_digest": ref("digest"), "delivered_effective_execution_digest": ref("digest"), "pi_delivery_receipt_digest": ref("digest")})
    suppressed = protocol("semantic-pi-delivery-receipt.v0", {"issuer": ref("issuer"), "claim_scope": {"const": "delivery_suppressed_only"}, "rocs_generation_receipt_digest": ref("digest"),
        "delivery_outcome": {"const": "suppressed"}, "suppression_reason": {"enum": ["cancelled", "stale_result", "policy"]}, "pi_delivery_receipt_digest": ref("digest")})
    failed = protocol("semantic-pi-delivery-receipt.v0", {"issuer": ref("issuer"), "claim_scope": {"const": "delivery_failed_only"}, "rocs_generation_receipt_digest": ref("digest"),
        "delivery_outcome": {"const": "failed"}, "error_digest": ref("digest"), "pi_delivery_receipt_digest": ref("digest")})
    d["piDeliveryReceipt"] = {"oneOf": [delivered, suppressed, failed]}
    d["akEvidenceLinkage"] = protocol("semantic-ak-evidence-linkage.v0", {
        "issuer": ref("issuer"), "claim_scope": {"const": "lineage_linkage_only"}, "task_reference_digest": ref("digest"), "decision_reference_digest": ref("digest"),
        "evidence_record_digest": ref("digest"), "activation_receipt_digest": ref("digest"), "rocs_generation_receipt_digest": ref("digest"), "pi_delivery_receipt_digest": nullable(ref("digest")),
        "empirical_outcome_reference_digest": nullable(ref("digest")), "ak_evidence_linkage_digest": ref("digest")})
    d["rollbackRequest"] = protocol("semantic-rollback-request.v0", {
        "issuer": ref("issuer"), "active_activation_receipt_digest": ref("digest"), "from_state": ref("activeState"), "target": ref("rollbackTarget"), "recovery_runtime_identity": ref("toolIdentity"),
        "recovery_controller_id": ref("identifier"), "recovery_epoch": ref("safeInteger"),
        "owner_decision_reference_digest": ref("digest"), "precondition_digest": ref("digest"), "rollback_request_digest": ref("digest")})
    d["rollbackStage"] = obj({"stage": {"enum": ["semantic", "runtime", "disable"]}, "result": {"enum": ["not_started", "completed", "failed"]}, "error_digest": nullable(ref("digest"))})
    d["rollbackTechnicalReceipt"] = protocol("semantic-rollback-technical-receipt.v0", {
        "issuer": ref("issuer"), "receipt_kind": {"enum": ["materialization", "runtime_revalidation", "disable_contract", "rehearsal", "health"]},
        "subject_digest": ref("digest"), "coordinate": nullable(ref("coordinate")), "runtime_identity": nullable(ref("toolIdentity")),
        "referenced_receipt_digest": nullable(ref("digest")), "outcome": {"const": "valid"},
        "rollback_technical_receipt_digest": ref("digest")})
    d["rollbackAvailableArtifact"] = protocol("semantic-rollback-availability-receipt.v0", {
        "issuer": ref("issuer"), "artifact_id": ref("identifier"), "artifact_kind": {"enum": ["semantic_target", "runtime_target", "disable_target", "recovery_runtime"]},
        "coordinate": nullable(ref("coordinate")), "runtime_identity": nullable(ref("toolIdentity")), "materialization_receipt_digest": nullable(ref("digest")),
        "runtime_revalidation_receipt_digest": nullable(ref("digest")), "disable_contract_digest": nullable(ref("digest")), "rehearsal_receipt_digest": nullable(ref("digest")),
        "health_receipt_digest": nullable(ref("digest")), "independently_available": {"const": True}, "availability_epoch": ref("safeInteger"),
        "rollback_available_artifact_digest": ref("digest")})
    d["rollbackAvailabilityProof"] = protocol("semantic-rollback-availability-proof.v0", {
        "issuer": ref("issuer"), "consumer_intent_digest": ref("digest"), "owner_acceptance_digest": ref("digest"),
        "materialization_verification_receipt_digest": ref("digest"), "availability_epoch": ref("safeInteger"),
        "recovery_controller_id": ref("identifier"), "recovery_epoch": ref("safeInteger"),
        "target_kind": {"enum": ["semantic", "runtime", "no_prior_disable", "combined"]},
        "recovery_runtime_identity": ref("toolIdentity"), "recovery_runtime_available": {"const": True},
        "semantic_materialization_receipt_digest": nullable(ref("digest")), "semantic_coordinate": nullable(ref("coordinate")),
        "runtime_materialization_receipt_digest": nullable(ref("digest")), "runtime_identity": nullable(ref("toolIdentity")),
        "runtime_revalidation_receipt_digest": nullable(ref("digest")), "disable_contract_digest": nullable(ref("digest")),
        "rehearsal_receipt_digest": nullable(ref("digest")), "semantic_target_artifact_digest": nullable(ref("digest")),
        "runtime_target_artifact_digest": nullable(ref("digest")), "disable_target_artifact_digest": nullable(ref("digest")),
        "recovery_artifact_digest": ref("digest"), "rollback_availability_proof_digest": ref("digest")})
    d["rollbackHistoryTransition"] = protocol("semantic-rollback-history-transition.v0", {
        "issuer": ref("issuer"), "rollback_request_digest": ref("digest"), "result": {"enum": ["rolled_back", "disabled", "partial_failure"]},
        "active_state_before": ref("activeState"), "active_state_after": ref("activeState"), "stages": array(ref("rollbackStage"), 2, 1),
        "failure_stage": nullable({"enum": ["semantic", "runtime", "disable"]}), "error_digest": nullable(ref("digest")),
        "history_head_before": ref("historyHead"), "supersedes_activation_receipt_digest": nullable(ref("digest")),
        "rollback_history_transition_digest": ref("digest")})
    d["rollbackReceipt"] = protocol("semantic-rollback-receipt.v0", {
        "issuer": ref("issuer"), "recovery_controller_id": ref("identifier"), "recovery_epoch": ref("safeInteger"),
        "rollback_request_digest": ref("digest"), "request_target_kind": {"enum": ["semantic", "runtime", "no_prior_disable", "combined"]},
        "result": {"enum": ["rolled_back", "disabled", "partial_failure", "failed"]}, "stage_order": nullable({"enum": ["semantic_then_runtime", "runtime_then_semantic"]}),
        "active_state_before": ref("activeState"), "active_state_after": ref("activeState"), "availability_proof_digest": ref("digest"), "runtime_revalidation_receipt_digest": nullable(ref("digest")),
        "stages": array(ref("rollbackStage"), 2, 1), "failure_stage": nullable({"enum": ["semantic", "runtime", "disable"]}),
        "history_head_before": ref("historyHead"), "history_head_after": ref("historyHead"), "error_digest": nullable(ref("digest")),
        "supersedes_activation_receipt_digest": nullable(ref("digest")), "ak_evidence_linkage_digest": nullable(ref("digest")),
        "pi_delivery_receipt_digest": nullable(ref("digest")), "rollback_receipt_digest": ref("digest")})
    d["akTaskState"] = obj({"repository": ref("repositoryIdentity"), "ak_store_head": ref("akStoreHead"),
        "task_id": ref("identifier"), "task_record_digest": ref("digest"), "artifact_digest": ref("digest"),
        "state": {"enum": ["accepted", "completed", "evidence_accepted"]}})
    observed_task_state = ref("akTaskState")
    resolved_task_ref = obj({"resolution": {"const": "resolved"}, "reference_id": ref("identifier"),
        "repository": ref("repositoryIdentity"), "ak_store_head": ref("akStoreHead"), "task_id": ref("identifier"),
        "task_record_digest": ref("digest"), "artifact_digest": ref("digest"), "observed_canonical_state": observed_task_state,
        "required_state": {"enum": ["accepted_current", "completed_current", "evidence_accepted_current"]}})
    unresolved_task_ref = obj({"resolution": {"const": "unresolved_candidate"}, "reference_id": ref("identifier"),
        "repository": ref("repositoryIdentity"), "ak_store_head": {"type": "null"}, "task_id": {"type": "null"},
        "task_record_digest": {"type": "null"}, "artifact_digest": {"type": "null"}, "observed_canonical_state": {"type": "null"},
        "required_state": {"enum": ["accepted_current", "completed_current", "evidence_accepted_current"]}})
    d["taskArtifactReference"] = {"oneOf": [resolved_task_ref, unresolved_task_ref]}
    d["stopConditionReference"] = obj({"condition_id": ref("identifier"),
        "condition_kind": {"enum": ["stale_or_revoked_decision", "store_head_drift", "scope_drift", "missing_owner_task", "owner_substitution", "authorization_escalation", "missing_owner_consent", "rollback_unavailable", "stale_semantic_trust_or_ledger", "stale_ak_decision_or_store", "stale_consumer_activation_or_history", "projection_or_issuer_drift", "validator_failure", "compatibility_failure", "missing_rollback_rehearsal", "protocol_scope_expansion"]},
        "fact_reference": ref("taskArtifactReference"), "trigger_state": {"const": "unsatisfied_or_noncurrent"},
        "required_effect": {"const": "stop_before_mutation"}, "resume_state": {"const": "accepted_current"}})
    d["nonAuthorizingTaskContract"] = protocol("semantic-non-authorizing-task-contract.v0", {
        "task_contract_id": ref("identifier"), "task_id": ref("identifier"), "task_owner_id": ref("identifier"),
        "task_kind": {"enum": ["ak_coordination", "single_canary_consumer"]}, "repository": ref("repositoryIdentity"), "allowed_paths": array(ref("logicalPath"), 64),
        "dependencies": array(ref("taskArtifactReference"), 64), "prerequisites": array(ref("taskArtifactReference"), 64, 1),
        "required_evidence": array(ref("taskArtifactReference"), 64, 1), "rollback_owner": ref("issuer"),
        "stop_conditions": array(ref("stopConditionReference"), 64, 1), "authority_scope": {"enum": ["coordination_only", "consumer_owner_candidate_only"]},
        "authorizes_execution": {"type": "boolean"}, "authorizes_publication": {"type": "boolean"}, "authorizes_adoption": {"type": "boolean"},
        "contract_status": {"enum": ["candidate_not_created", "created"]}, "non_authorizing_task_contract_digest": ref("digest")})
    d["auditEnvelope"] = protocol("semantic-audit-envelope.v0", {
        "artifact_schema": ref("identifier"), "artifact_digest": ref("digest"), "event": ref("identifier"), "recorded_at": {"type": "string", "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"},
        "issuer": ref("issuer"), "audit_sequence": ref("safeInteger"), "previous_audit_envelope_digest": nullable(ref("digest")), "audit_envelope_digest": ref("digest")})
    d["errorDetail"] = obj({"key": ref("identifier"), "value": {"type": "string", "maxLength": 4096}})
    d["errorEnvelope"] = protocol("semantic-protocol-error.v0", {
        "code": {"enum": ["malformed_input", "unsupported_protocol", "resource_exhausted", "deadline_exceeded", "network_forbidden", "digest_mismatch", "trust_root_missing", "trust_reference_stale", "trust_revoked", "owner_approval_missing", "approval_threshold_unsatisfied", "self_certification", "publication_conflict", "version_conflict", "publication_fork", "snapshot_drift", "incomplete_tree", "projection_mismatch", "compatibility_unknown", "compatibility_rejected", "semver_violation", "lifecycle_violation", "atomic_activation_unavailable", "recovery_needed", "rollback_unavailable", "history_conflict", "activation_not_current", "issuer_scope_violation"]},
        "stage": {"enum": ["decode", "validate", "build", "approve", "publish", "materialize", "activate", "generate", "deliver", "link", "rollback", "recover"]}, "retryable": {"type": "boolean"},
        "related_artifact_digest": nullable(ref("digest")), "details": array(ref("errorDetail"), 64), "error_digest": ref("digest")})

    d["ownerVoteProofFact"] = obj({
        "owner_id": ref("identifier"), "owner_key_id": ref("identifier"), "approved_action_digest": ref("digest"),
        "approval_proof_digest": ref("digest")})
    d["lifecycleTombstoneHead"] = obj({
        "namespace": ref("namespace"), "lifecycle_head_digest": ref("digest"),
        "tombstone_registry_digest": ref("digest"), "tombstone_registry_revision": ref("safeInteger")})
    fact_value_variants = [
        obj({"kind": {"const": "null"}}),
        obj({"kind": {"const": "digest"}, "value": nullable(ref("digest"))}),
        obj({"kind": {"const": "safe_integer"}, "value": ref("safeInteger")}),
        obj({"kind": {"const": "boolean"}, "value": {"type": "boolean"}}),
        obj({"kind": {"const": "text"}, "value": ref("text")}),
        obj({"kind": {"const": "semver"}, "value": ref("semver")}),
        obj({"kind": {"const": "digest_list"}, "value": array(ref("digest"), 10000)}),
        obj({"kind": {"const": "empty_list"}}),
        obj({"kind": {"const": "empty_map"}}),
        obj({"kind": {"const": "ak_store_head"}, "value": ref("akStoreHead")}),
        obj({"kind": {"const": "external_trust_root_pin"}, "value": ref("externalTrustRootPin")}),
        obj({"kind": {"const": "approval_action"}, "value": ref("approvalAction")}),
        obj({"kind": {"const": "publication_recovery_state"}, "value": ref("publicationRecoveryState")}),
        obj({"kind": {"const": "history_head"}, "value": ref("historyHead")}),
        obj({"kind": {"const": "coordinate"}, "value": ref("coordinate")}),
        obj({"kind": {"const": "tool_identity"}, "value": ref("toolIdentity")}),
        obj({"kind": {"const": "ak_task_state"}, "value": ref("akTaskState")}),
        obj({"kind": {"const": "ak_task_state_list"}, "value": array(ref("akTaskState"), 10000)}),
        obj({"kind": {"const": "owner_vote_proof"}, "value": ref("ownerVoteProofFact")}),
        obj({"kind": {"const": "lifecycle_tombstone_head"}, "value": ref("lifecycleTombstoneHead")}),
    ]
    d["authorityFactValue"] = {"oneOf": fact_value_variants}
    authority_categories = ["semantic_trust", "semantic_revocation", "semantic_publication", "semantic_lifecycle", "semantic_vote",
        "ak_store", "ak_decision", "ak_task", "consumer_acceptance", "consumer_activation", "consumer_history", "recovery_controller"]
    owner_surfaces = ["semantic_owner", "ak", "consumer_owner", "rocs", "recovery_controller", "pi"]
    d["ownerAcquisitionPin"] = protocol("semantic-owner-acquisition-capability-pin.v0", {
        "capability_pin_id": ref("identifier"), "role": ref("identifier"), "category": {"enum": authority_categories},
        "owner_surface": {"enum": owner_surfaces}, "owner_id": ref("identifier"), "owner_repository": ref("repositoryIdentity"),
        "acquisition_contract": ref("identifier"), "acquisition_contract_digest": ref("digest"),
        "acquisition_distribution_digest": ref("digest"), "store_id": ref("identifier"), "store_head_digest": ref("digest"),
        "store_revision": ref("safeInteger"), "fact_schema": ref("identifier"), "fact_digest": ref("digest"),
        "fact_value": ref("authorityFactValue"), "freshness_cas_token_digest": ref("digest"),
        "required_action_epoch_floor": ref("safeInteger"), "acquisition_capability_digest": ref("digest"),
        "capability_pin_digest": ref("digest")})
    d["authorityAcquisitionConfig"] = protocol("semantic-authority-acquisition-config.v0", {
        "verifier_identity": ref("toolIdentity"), "collator": ref("issuer"),
        "collation_scope": {"const": "transport_only_no_receipt_issuance"},
        "required_action_epoch_floor": ref("safeInteger"), "live_acquisition_implemented": {"const": False},
        "pins": array(ref("ownerAcquisitionPin"), 10000), "authority_acquisition_config_digest": ref("digest")})
    d["ownerStoreReadReceipt"] = protocol("semantic-owner-store-read-receipt.v0", {
        "observation_id": ref("identifier"), "role": ref("identifier"), "category": {"enum": authority_categories},
        "issuer": ref("issuer"), "claim_scope": {"const": "owner_store_read_only"},
        "owner_repository": ref("repositoryIdentity"), "capability_pin_id": ref("identifier"),
        "acquisition_capability_digest": ref("digest"), "capability_pin_digest": ref("digest"),
        "acquisition_contract": ref("identifier"),
        "acquisition_contract_digest": ref("digest"), "acquisition_distribution_digest": ref("digest"),
        "store_id": ref("identifier"), "store_head_digest": ref("digest"), "store_revision": ref("safeInteger"),
        "fact_schema": ref("identifier"), "fact_digest": ref("digest"), "fact_value": ref("authorityFactValue"),
        "freshness_cas_token_digest": ref("digest"), "action_epoch": ref("safeInteger"),
        "required_action_epoch_floor": ref("safeInteger"), "owner_store_read_receipt_digest": ref("digest")})
    d["authoritySnapshot"] = protocol("semantic-authority-snapshot.v0", {
        "caller_trust_boundary": {"const": "externally_configured_owner_acquisition_pins"},
        "collator": ref("issuer"), "collation_scope": {"const": "transport_only_no_receipt_issuance"},
        "authority_acquisition_config_digest": ref("digest"), "action_epoch": ref("safeInteger"),
        "store_read_receipts": array(ref("ownerStoreReadReceipt"), 10000), "authority_snapshot_digest": ref("digest")})
    artifact_top = ["coordinate", "sourceManifest", "materialManifest", "ownerSet", "approvalPredicate", "ownerPolicy", "trustRoot", "trustRotation", "trustRevocation",
        "compatibilityPolicy", "compatibilityReport", "compatibilityOverride", "deprecationRecord", "removalRecord", "tombstoneRegistry", "tombstoneHistoryProof", "publicationLedgerHead", "acceptedLifecycleLedgerRecord", "payloadProjection", "capsuleArchiveLinkage", "capsule",
        "akDecisionReference", "ownerApproval", "buildReceipt", "publicationTransaction", "publicationJournal", "publicationRecoveryIntentMarker", "publicationCommitMarker", "publicationRecoveryStateReceipt", "ownerPublication", "publicationStatusTransition",
        "consumerIntent", "ownerAcceptance", "materializationVerificationReceipt", "activationReceipt", "rocsGenerationReceipt", "piDeliveryReceipt", "akEvidenceLinkage", "rollbackRequest", "rollbackTechnicalReceipt", "rollbackAvailableArtifact", "rollbackAvailabilityProof", "rollbackHistoryTransition", "rollbackReceipt", "nonAuthorizingTaskContract", "auditEnvelope", "errorEnvelope"]
    d["proofArtifact"] = {"oneOf": [ref(name) for name in artifact_top]}
    proof_claims = ["semantic_owner_fact", "ak_canonical_fact", "consumer_owner_fact", "rocs_technical_fact", "recovery_controller_fact", "pi_delivery_fact"]
    d["proofNode"] = obj({"bundle_key": ref("digest"), "artifact_schema": ref("identifier"), "issuer": ref("issuer"),
        "owner_repository": ref("repositoryIdentity"), "claim_scope": {"enum": proof_claims}, "artifact": ref("proofArtifact")})
    d["authorityProofBundle"] = protocol("semantic-authority-proof-bundle.v0", {
        "rule": ref("identifier"), "subject_schema": ref("identifier"), "subject_digest": ref("digest"),
        "authority_snapshot_digest": ref("digest"), "nodes": array(ref("proofNode"), 100000),
        "authority_proof_bundle_digest": ref("digest")})
    d["receiptBinding"] = obj({"role": ref("identifier"), "category": {"enum": authority_categories},
        "observation_id": ref("identifier"), "capability_pin_id": ref("identifier"),
        "owner_surface": {"enum": owner_surfaces}, "owner_id": ref("identifier"),
        "owner_repository": ref("repositoryIdentity"), "acquisition_contract": ref("identifier"),
        "acquisition_contract_digest": ref("digest"), "acquisition_distribution_digest": ref("digest"),
        "acquisition_capability_digest": ref("digest")})
    d["nodeBinding"] = obj({"role": ref("identifier"), "bundle_key": ref("digest"), "expected_schema": ref("identifier"),
        "expected_issuer_kind": {"enum": ["semantic_owner", "consumer_owner", "rocs", "pi", "ak", "recovery_controller"]},
        "expected_issuer_id": ref("identifier"), "expected_owner_repository": ref("repositoryIdentity"),
        "expected_claim_scope": {"enum": proof_claims}})
    d["ruleParameterBinding"] = obj({"role": ref("identifier"), "value": ref("authorityFactValue")})
    d["authorityRoleMapping"] = obj({
        "role": ref("identifier"), "role_prefix": nullable(ref("identifier")),
        "sources": array({"enum": ["authority_graph", "node", "parameter", "receipt", "subject"]}, 5, 1),
        "category": nullable({"enum": authority_categories}), "owner_surface": nullable({"enum": owner_surfaces}),
        "owner_id": nullable(ref("identifier")), "owner_repository": nullable(ref("repositoryIdentity")),
        "capability_pin_id": nullable(ref("identifier")), "capability_pin_prefix": nullable(ref("identifier")),
        "acquisition_contract": nullable(ref("identifier")), "acquisition_contract_digest": nullable(ref("digest")),
        "acquisition_distribution_digest": nullable(ref("digest")), "acquisition_capability_digest": nullable(ref("digest")),
        "expected_schemas": array(ref("identifier"), 8), "minimum_cardinality": ref("safeInteger"),
        "maximum_cardinality": ref("safeInteger"), "description": ref("text")})
    d["authorityOwnerTuple"] = obj({"owner_surface": {"enum": owner_surfaces}, "owner_id": ref("identifier"),
        "owner_repository": ref("repositoryIdentity")})
    d["authorityEdgeOwnership"] = obj({"kind": {"enum": ["single_owner", "multi_owner"]},
        "owners": array(ref("authorityOwnerTuple"), 1000, 1)})
    d["authorityEdgeRoleOwner"] = obj({"role": ref("identifier"), "owner": ref("authorityOwnerTuple")})
    d["authorityRoleEdgeLink"] = obj({
        "edge_id": ref("identifier"), "ownership": ref("authorityEdgeOwnership"),
        "role_owners": array(ref("authorityEdgeRoleOwner"), 1000, 1), "role_ids": array(ref("identifier"), 1000, 1),
        "edge_linkage_digest": ref("digest")})
    d["authorityRuleManifestEntry"] = obj({
        "rule": ref("identifier"), "authority_bearing": {"type": "boolean"},
        "required_roles": array(ref("identifier"), 1000), "role_mappings": array(ref("authorityRoleMapping"), 1000),
        "edge_ids": array(ref("identifier"), 1000), "role_edge_links": array(ref("authorityRoleEdgeLink"), 1000)})
    d["authorityRuleRoleManifest"] = protocol("semantic-authority-rule-role-manifest.v0", {
        "revision": {"const": "semantic-release-revision-v12"}, "rules": array(ref("authorityRuleManifestEntry"), 1000, 1),
        "authority_rule_role_manifest_digest": ref("digest")})
    d["authorityVerifierInput"] = protocol("semantic-authority-verifier-input.v0", {
        "rule": ref("identifier"), "subject_schema": ref("identifier"), "subject_digest": ref("digest"),
        "authority_rule_role_manifest_digest": ref("digest"), "authority_acquisition_config_digest": ref("digest"),
        "authority_snapshot_digest": ref("digest"), "authority_proof_bundle_digest": ref("digest"),
        "required_action_epoch_floor": ref("safeInteger"), "receipt_bindings": array(ref("receiptBinding"), 10000),
        "node_bindings": array(ref("nodeBinding"), 100000), "parameter_bindings": array(ref("ruleParameterBinding"), 100000),
        "required_observation_ids": array(ref("identifier"), 10000), "required_role_ids": array(ref("identifier"), 100000),
        "required_edge_ids": array(ref("identifier"), 10000), "authority_verifier_input_digest": ref("digest")})
    top = [*artifact_top, "ownerAcquisitionPin", "authorityAcquisitionConfig", "ownerStoreReadReceipt", "authoritySnapshot",
        "authorityRuleRoleManifest", "authorityProofBundle", "authorityVerifierInput"]
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "https://ai-society.local/rocs/semantic-release-v0/protocol.schema.json",
            "title": "Semantic Release Capsule and Consumer Adoption Protocol v0 revision 12", "oneOf": [ref(name) for name in top], "$defs": d}


def write_schema() -> None:
    (ROOT / "protocol.schema.json").write_text(json.dumps(build_schema(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    write_schema()
    print("wrote protocol.schema.json")
