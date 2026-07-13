#!/usr/bin/env python3
"""Deterministically regenerate revision-6 schema and normative fixtures."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from schema_builder import write_schema
from validate_fixtures import COORDINATE_DOMAIN, DIGEST_FIELDS, domain_digest, jcs, object_digest

ROOT = Path(__file__).resolve().parent
ZERO = "sha256:" + "0" * 64
records: list[dict] = []
by_name: dict[str, dict] = {}


def raw(label: str, domain: str = "semantic-release.raw-blob.v0") -> str:
    return domain_digest(domain, label.encode())


def typed_digest(domain: str, value: object) -> str:
    return domain_digest(domain, jcs(value).encode())


def action_digest(value: object) -> str:
    return typed_digest("semantic-release.approval-action.v0", value)


def change_digest(value: object) -> str:
    return typed_digest("semantic-release.compatibility-change.v0", value)


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
ak_coord_repo = {"owner": "agent-kernel-owner", "repository_id": "agent-kernel", "canonical_locator": "local://softwareco/owned/agent-kernel", "identity_revision": 9}
canary_repo = {"owner": "consumer-owner", "repository_id": "pi-canary-consumer", "canonical_locator": "local://softwareco/pi-canary-consumer", "identity_revision": 3}
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
capsule_metadata = {"schema": "semantic-capsule-metadata.v0", "namespace": "ai-society.core", "semantic_version": "1.1.0",
    "payload_manifest_digest": d("payload_manifest"), "identity_mode": "no_capsule_archive_or_linkage_digest"}
capsule_metadata_bytes = jcs(capsule_metadata).encode()
capsule_metadata_content_digest = domain_digest("semantic-release.raw-blob.v0", capsule_metadata_bytes)
archive_manifest = add("capsule_archive_manifest", {"schema": "semantic-material-manifest.v0", "tree_role": "capsule_archive", "entries": [
    {"path": "capsule.json", "kind": "file", "mode": 420, "byte_length": len(capsule_metadata_bytes), "content_digest": capsule_metadata_content_digest}, {"path": "payload", "kind": "directory", "mode": 493},
    {"path": "payload/index.json", "kind": "file", "mode": 420, "byte_length": 17, "content_digest": raw("index-bytes")}, {"path": "payload/records", "kind": "directory", "mode": 493},
    {"path": "payload/records/core.Agent.json", "kind": "file", "mode": 420, "byte_length": 36, "content_digest": raw("record-bytes")} ]})
projection = add("payload_projection", {"schema": "semantic-payload-projection.v0", "payload_manifest_digest": d("payload_manifest"), "consumer_manifest_digest": d("consumer_material_manifest"), "projection_mode": "exact_no_extra_no_missing", "entries": [
    {"capsule_path": "payload/index.json", "consumer_path": "index.json", "mode": 420, "byte_length": 17, "content_digest": raw("index-bytes")},
    {"capsule_path": "payload/records", "consumer_path": "records", "mode": 493, "byte_length": None, "content_digest": None},
    {"capsule_path": "payload/records/core.Agent.json", "consumer_path": "records/core.Agent.json", "mode": 420, "byte_length": 36, "content_digest": raw("record-bytes")} ]})
archive_link = add("capsule_archive_linkage", {"schema": "semantic-capsule-archive-linkage.v0", "archive_manifest_digest": d("capsule_archive_manifest"), "payload_manifest_digest": d("payload_manifest"),
    "payload_root": "payload", "capsule_metadata_path": "capsule.json", "capsule_metadata": capsule_metadata,
    "capsule_metadata_content_digest": capsule_metadata_content_digest, "archive_format": "directory-v0"})

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
    "owner_policy_digest": d("owner_policy"), "owner_set_digest": d("owner_set"), "key_ids": ["root-key-5-a", "root-key-5-b"], "minimum_ledger_revision": 2, "prior_trust_root_digest": raw("trust-root-4"), "status": "active"})
new_trust_root = add("rotated_trust_root", {"schema": "semantic-trust-root.v0", "namespace": "ai-society.core", "trust_root_id": "semantic-owner-local-root", "trust_root_revision": 6,
    "owner_policy_digest": d("owner_policy"), "owner_set_digest": d("owner_set"), "key_ids": ["root-key-6-a", "root-key-6-b"], "minimum_ledger_revision": 3,
    "prior_trust_root_digest": d("trust_root"), "status": "active"})

condition = {"condition_id": "constraint-proof", "kind": "evidence_digest_equals", "expected_digest": raw("compat-evidence"), "actual_digest": raw("compat-evidence"), "expected_integer": None, "actual_integer": None, "satisfied": True}
compat_report = add("compatibility_report", {"schema": "semantic-compatibility-report.v0", "namespace": "ai-society.core", "prior_coordinate": predecessor, "candidate_version": "1.1.0",
    "compatibility_policy_digest": d("compatibility_policy"), "changes": [{"category": "addition", "semantic_id": "core.Agent", "classification": "compatible", "semver_effect": "minor", "condition_id": None}],
    "conditions": [], "classification": "compatible", "required_semver_effect": "minor", "override_digests": []})
conditional_report = add("conditional_compatibility_report", {"schema": "semantic-compatibility-report.v0", "namespace": "ai-society.core", "prior_coordinate": predecessor, "candidate_version": "1.1.0",
    "compatibility_policy_digest": d("compatibility_policy"), "changes": [{"category": "constraint_change", "semantic_id": "core.Agent", "classification": "conditionally_compatible", "semver_effect": "minor", "condition_id": "constraint-proof"}],
    "conditions": [condition], "classification": "conditionally_compatible", "required_semver_effect": "minor", "override_digests": []})
unknown_change = {"category": "other", "semantic_id": "core.Experimental", "classification": "unknown", "semver_effect": "unknown", "condition_id": None}
override_condition = {"condition_id": "override-proof", "kind": "evidence_digest_equals", "expected_digest": raw("override-evidence"),
    "actual_digest": raw("override-evidence"), "expected_integer": None, "actual_integer": None, "satisfied": True}

tombstones = add("tombstone_registry", {"schema": "semantic-tombstone-registry.v0", "namespace": "ai-society.core", "registry_revision": 3,
    "entries": [], "prior_registry_digest": raw("tombstones-2")})

capsule = add("capsule", {"schema": "semantic-release-capsule.v0", "namespace": "ai-society.core", "semantic_version": "1.1.0", "source_manifest_digest": d("source_manifest"),
    "semantic_payload_digest": raw("semantic-payload-1.1", "semantic-release.semantic-payload.v0"), "payload_manifest_digest": d("payload_manifest"), "payload_projection_digest": d("payload_projection"),
    "capsule_archive_linkage_digest": d("capsule_archive_linkage"), "compatibility_report_digest": d("compatibility_report"), "owner_policy_digest": d("owner_policy"),
    "compilation_contract_digest": raw("compilation-contract"), "required_protocol_versions": ["semantic-discovery-v0", "semantic-release-v0"], "predecessor_coordinate": predecessor,
    "tombstone_registry_digest": d("tombstone_registry")})
coordinate = add("coordinate", {"schema": "semantic-release-coordinate.v0", "namespace": "ai-society.core", "semantic_version": "1.1.0", "capsule_digest": d("capsule")})
coord_digest = d("coordinate")
ak_store_head = {"store_id": "ak-main", "canonical_store_locator": "sqlite://agent-kernel/.ak/agent-kernel.db#decision-head",
    "store_revision": 42, "store_head_digest": raw("ak-store-head-42"), "revocation_head_digest": raw("ak-revocation-head-7")}
owner_decision = add("owner_ak_decision", {"schema": "semantic-ak-decision-reference.v0", "ak_repository": ak_repo, "ak_runtime_identity": ak_tool, "ak_store_head": ak_store_head,
    "decision_id": "semantic-release-1.1.0", "decision_revision": 2, "decision_record_digest": raw("owner-decision-record-2"), "lifecycle_state": "accepted",
    "adr_reference": {"adr_id": "ADR-0053", "adr_revision": 1, "adr_digest": raw("adr-53"), "status": "accepted"}, "scope_digest": raw("semantic-owner-scope"),
    "revocation_digest": None, "superseded_by_decision_record_digest": None, "activation_target_digest": d("capsule"), "evidence_criteria_digest": d("compatibility_report"),
    "rollback_plan_digest": raw("owner-withdrawal-plan"), "stop_conditions_digest": raw("owner-stop-conditions")})
consumer_decision = add("consumer_ak_decision", {"schema": "semantic-ak-decision-reference.v0", "ak_repository": ak_repo, "ak_runtime_identity": ak_tool, "ak_store_head": ak_store_head,
    "decision_id": "consumer-canary", "decision_revision": 4, "decision_record_digest": raw("consumer-decision-record-4"), "lifecycle_state": "accepted",
    "adr_reference": {"adr_id": "ADR-0053", "adr_revision": 1, "adr_digest": raw("adr-53"), "status": "accepted"}, "scope_digest": raw("consumer-canary-scope"),
    "revocation_digest": None, "superseded_by_decision_record_digest": None, "activation_target_digest": coord_digest, "evidence_criteria_digest": raw("canary-evidence"),
    "rollback_plan_digest": raw("canary-rollback"), "stop_conditions_digest": raw("canary-stop")})
canonical_decision_context = {"canonical_store_head": ak_store_head, "current_decision_record_digest": consumer_decision["decision_record_digest"]}
release_action = {"kind": "release", "source_manifest_digest": d("source_manifest"), "candidate_capsule_digest": d("capsule"), "compatibility_report_digest": d("compatibility_report")}
release_action_digest = action_digest(release_action)
owner_approval = add("owner_approval", {"schema": "semantic-owner-approval.v0", "namespace": "ai-society.core", "owner_policy_digest": d("owner_policy"), "owner_set_digest": d("owner_set"),
    "approval_predicate_digest": d("approval_predicate"), "action": release_action, "action_digest": release_action_digest,
    "votes": [{"owner_id": "owner-a", "owner_key_id": "owner-a-key-3", "approved_action_digest": release_action_digest, "approval_proof_digest": raw("vote-release-a")},
              {"owner_id": "owner-b", "owner_key_id": "owner-b-key-2", "approved_action_digest": release_action_digest, "approval_proof_digest": raw("vote-release-b")}], "decision_reference_digest": d("owner_ak_decision")})
rotation_action = {"kind": "trust_rotation", "namespace": "ai-society.core", "old_trust_root_digest": d("trust_root"), "new_trust_root_digest": d("rotated_trust_root"),
    "owner_policy_digest": d("owner_policy"), "owner_set_digest": d("owner_set"), "approval_predicate_digest": d("approval_predicate"),
    "new_trust_root_revision": 6, "rotation_revision": 6}
rotation_action_digest = action_digest(rotation_action)
rotation_approval = add("rotation_approval", {"schema": "semantic-owner-approval.v0", "namespace": "ai-society.core", "owner_policy_digest": d("owner_policy"), "owner_set_digest": d("owner_set"),
    "approval_predicate_digest": d("approval_predicate"), "action": rotation_action, "action_digest": rotation_action_digest,
    "votes": [{"owner_id": "owner-a", "owner_key_id": "owner-a-key-3", "approved_action_digest": rotation_action_digest, "approval_proof_digest": raw("vote-rotation-a")},
              {"owner_id": "owner-b", "owner_key_id": "owner-b-key-2", "approved_action_digest": rotation_action_digest, "approval_proof_digest": raw("vote-rotation-b")}], "decision_reference_digest": d("owner_ak_decision")})
rotation = add("trust_rotation", {"schema": "semantic-trust-rotation.v0", "namespace": "ai-society.core", "old_trust_root_id": trust_root["trust_root_id"],
    "old_trust_root_revision": 5, "old_trust_root_digest": d("trust_root"), "new_trust_root_id": new_trust_root["trust_root_id"], "new_trust_root_revision": 6,
    "new_trust_root_digest": d("rotated_trust_root"), "owner_policy_digest": d("owner_policy"), "owner_set_digest": d("owner_set"),
    "approval_predicate_digest": d("approval_predicate"), "approval_digest": d("rotation_approval"), "rotation_revision": 6})
revocation_action = {"kind": "trust_revocation", "namespace": "ai-society.core", "owner_policy_digest": d("owner_policy"), "owner_set_digest": d("owner_set"),
    "approval_predicate_digest": d("approval_predicate"), "target_kind": "owner_key", "target_digest": raw("compromised-key"), "effective_ledger_revision": 3,
    "reason_digest": raw("compromise-reason"), "prior_revocation_digest": None, "revocation_revision": 1}
revocation_action_digest = action_digest(revocation_action)
revocation_approval = add("revocation_approval", {"schema": "semantic-owner-approval.v0", "namespace": "ai-society.core", "owner_policy_digest": d("owner_policy"), "owner_set_digest": d("owner_set"),
    "approval_predicate_digest": d("approval_predicate"), "action": revocation_action, "action_digest": revocation_action_digest,
    "votes": [{"owner_id": "owner-a", "owner_key_id": "owner-a-key-3", "approved_action_digest": revocation_action_digest, "approval_proof_digest": raw("vote-revocation-a")},
              {"owner_id": "owner-b", "owner_key_id": "owner-b-key-2", "approved_action_digest": revocation_action_digest, "approval_proof_digest": raw("vote-revocation-b")}], "decision_reference_digest": d("owner_ak_decision")})
revocation = add("trust_revocation", {"schema": "semantic-trust-revocation.v0", "namespace": "ai-society.core", "revocation_revision": 1,
    "target_kind": "owner_key", "target_digest": revocation_action["target_digest"], "effective_ledger_revision": 3, "reason_digest": revocation_action["reason_digest"],
    "owner_approval_digest": d("revocation_approval"), "prior_revocation_digest": None})
override_action = {"kind": "compatibility_override", "namespace": "ai-society.core", "compatibility_policy_digest": d("compatibility_policy"),
    "change": unknown_change, "change_digest": change_digest(unknown_change), "from_classification": "unknown", "from_semver_effect": "unknown",
    "to_classification": "conditionally_compatible", "semver_effect_floor": "major", "condition": override_condition}
override_action_digest = action_digest(override_action)
override_approval = add("override_approval", {"schema": "semantic-owner-approval.v0", "namespace": "ai-society.core", "owner_policy_digest": d("owner_policy"), "owner_set_digest": d("owner_set"),
    "approval_predicate_digest": d("approval_predicate"), "action": override_action, "action_digest": override_action_digest,
    "votes": [{"owner_id": "owner-a", "owner_key_id": "owner-a-key-3", "approved_action_digest": override_action_digest, "approval_proof_digest": raw("vote-override-a")},
              {"owner_id": "owner-b", "owner_key_id": "owner-b-key-2", "approved_action_digest": override_action_digest, "approval_proof_digest": raw("vote-override-b")}], "decision_reference_digest": d("owner_ak_decision")})
override = add("compatibility_override", {"schema": "semantic-compatibility-override.v0", "namespace": "ai-society.core", "compatibility_policy_digest": d("compatibility_policy"),
    "change": unknown_change, "change_digest": change_digest(unknown_change), "from_classification": "unknown", "from_semver_effect": "unknown",
    "to_classification": "conditionally_compatible", "semver_effect_floor": "major", "condition": override_condition, "owner_approval_digest": d("override_approval")})
overridden_report = add("overridden_compatibility_report", {"schema": "semantic-compatibility-report.v0", "namespace": "ai-society.core", "prior_coordinate": predecessor, "candidate_version": "2.0.0",
    "compatibility_policy_digest": d("compatibility_policy"), "changes": [unknown_change], "conditions": [], "classification": "conditionally_compatible",
    "required_semver_effect": "major", "override_digests": [d("compatibility_override")]})
build = add("build_receipt", {"schema": "semantic-build-receipt.v0", "source_manifest_digest": d("source_manifest"), "compilation_contract_digest": capsule["compilation_contract_digest"], "tool_identity": rocs_tool,
    "payload_manifest_digest": d("payload_manifest"), "payload_projection_digest": d("payload_projection"), "capsule_archive_linkage_digest": d("capsule_archive_linkage"),
    "semantic_payload_digest": capsule["semantic_payload_digest"], "compatibility_report_digest": d("compatibility_report"), "candidate_capsule_digest": d("capsule"), "reproducible": True})
prior_publication = add("prior_owner_publication", {"schema": "semantic-owner-publication.v0", "coordinate": predecessor, "transaction_digest": raw("prior-publication-transaction"),
    "owner_approval_digest": d("owner_approval"), "ledger_namespace": "ai-society.core", "ledger_revision": 1,
    "prior_publication_digest": None, "trust_root_digest": d("trust_root"), "status": "published"})
publish_tx = add("publication_transaction", {"schema": "semantic-publication-transaction.v0", "transaction_id": "publish-1.1.0", "operation": "publish", "namespace": "ai-society.core", "coordinate": coordinate,
    "owner_approval_digest": d("owner_approval"), "expected_prior_revision": 1, "expected_prior_head_digest": d("prior_owner_publication"), "replay_key_digest": raw("publish-replay-key"), "status_reason_digest": None})
publication = add("owner_publication", {"schema": "semantic-owner-publication.v0", "coordinate": coordinate, "transaction_digest": d("publication_transaction"),
    "owner_approval_digest": d("owner_approval"), "ledger_namespace": "ai-society.core", "ledger_revision": 2,
    "prior_publication_digest": d("prior_owner_publication"), "trust_root_digest": d("trust_root"), "status": "published"})
prior_publish_journal = add("prior_publication_journal", {"schema": "semantic-publication-journal.v0", "transaction_digest": raw("prior-publication-transaction"), "state": "committed",
    "resulting_record_digest": d("prior_owner_publication"), "resulting_ledger_revision": 1, "resulting_ledger_head_digest": d("prior_owner_publication"),
    "staged_blob_set_digest": raw("prior-publication-blobs"), "linearized": True, "recovery_action": "none", "prior_journal_digest": None})
publish_journal = add("publication_journal", {"schema": "semantic-publication-journal.v0", "transaction_digest": d("publication_transaction"), "state": "committed",
    "resulting_record_digest": d("owner_publication"), "resulting_ledger_revision": 2, "resulting_ledger_head_digest": d("owner_publication"),
    "staged_blob_set_digest": raw("publication-blobs"), "linearized": True, "recovery_action": "none", "prior_journal_digest": d("prior_publication_journal")})
publish_marker = add("publication_commit_marker", {"schema": "semantic-publication-commit-marker.v0", "transaction_digest": d("publication_transaction"), "journal_digest": d("publication_journal"),
    "resulting_record_digest": d("owner_publication"), "resulting_ledger_revision": 2, "resulting_ledger_head_digest": d("owner_publication"), "fsync_complete": True})

def status_approval(name: str, kind: str, operation: str, prior_digest: str, prior_status: str, reason: str, revision: int, head: str) -> dict:
    action = {"kind": kind, "operation": operation, "namespace": "ai-society.core", "owner_policy_digest": d("owner_policy"), "owner_set_digest": d("owner_set"),
        "approval_predicate_digest": d("approval_predicate"), "coordinate": coordinate, "prior_status_record_digest": prior_digest, "prior_status": prior_status,
        "reason_digest": reason, "expected_prior_revision": revision, "expected_prior_head_digest": head}
    ad = action_digest(action)
    return add(name, {"schema": "semantic-owner-approval.v0", "namespace": "ai-society.core", "owner_policy_digest": d("owner_policy"), "owner_set_digest": d("owner_set"),
        "approval_predicate_digest": d("approval_predicate"), "action": action, "action_digest": ad,
        "votes": [{"owner_id": "owner-a", "owner_key_id": "owner-a-key-3", "approved_action_digest": ad, "approval_proof_digest": raw(name + "-vote-a")},
                  {"owner_id": "owner-b", "owner_key_id": "owner-b-key-2", "approved_action_digest": ad, "approval_proof_digest": raw(name + "-vote-b")}],
        "decision_reference_digest": d("owner_ak_decision")})
withdraw_reason = raw("withdraw-reason")
withdraw_approval = status_approval("withdraw_approval", "publication_withdrawal", "withdraw", d("owner_publication"), "published", withdraw_reason, 2, d("owner_publication"))
withdraw_tx = add("withdraw_transaction", {"schema": "semantic-publication-transaction.v0", "transaction_id": "withdraw-1.1.0", "operation": "withdraw", "namespace": "ai-society.core", "coordinate": coordinate,
    "owner_approval_digest": d("withdraw_approval"), "expected_prior_revision": 2, "expected_prior_head_digest": d("owner_publication"), "replay_key_digest": raw("withdraw-replay"), "status_reason_digest": withdraw_reason})
withdrawal = add("publication_withdrawal", {"schema": "semantic-publication-status-transition.v0", "coordinate": coordinate, "from_status": "published", "to_status": "withdrawn",
    "prior_status_record_digest": d("owner_publication"), "transaction_digest": d("withdraw_transaction"), "owner_approval_digest": d("withdraw_approval"),
    "reason_digest": withdraw_reason, "ledger_revision": 3})
withdraw_journal = add("withdraw_journal", {"schema": "semantic-publication-journal.v0", "transaction_digest": d("withdraw_transaction"), "state": "committed",
    "resulting_record_digest": d("publication_withdrawal"), "resulting_ledger_revision": 3, "resulting_ledger_head_digest": d("publication_withdrawal"),
    "staged_blob_set_digest": raw("withdraw-blobs"), "linearized": True, "recovery_action": "none", "prior_journal_digest": d("publication_journal")})
withdraw_marker = add("withdraw_marker", {"schema": "semantic-publication-commit-marker.v0", "transaction_digest": d("withdraw_transaction"), "journal_digest": d("withdraw_journal"),
    "resulting_record_digest": d("publication_withdrawal"), "resulting_ledger_revision": 3, "resulting_ledger_head_digest": d("publication_withdrawal"), "fsync_complete": True})
revoke_reason = raw("revoke-reason")
revoke_approval = status_approval("revoke_approval", "publication_revocation", "revoke", d("publication_withdrawal"), "withdrawn", revoke_reason, 3, d("publication_withdrawal"))
revoke_tx = add("revoke_transaction", {"schema": "semantic-publication-transaction.v0", "transaction_id": "revoke-1.1.0", "operation": "revoke", "namespace": "ai-society.core", "coordinate": coordinate,
    "owner_approval_digest": d("revoke_approval"), "expected_prior_revision": 3, "expected_prior_head_digest": d("publication_withdrawal"), "replay_key_digest": raw("revoke-replay"), "status_reason_digest": revoke_reason})
revoked_publication = add("publication_revocation", {"schema": "semantic-publication-status-transition.v0", "coordinate": coordinate, "from_status": "withdrawn", "to_status": "revoked",
    "prior_status_record_digest": d("publication_withdrawal"), "transaction_digest": d("revoke_transaction"), "owner_approval_digest": d("revoke_approval"),
    "reason_digest": revoke_reason, "ledger_revision": 4})
revoke_journal = add("revoke_journal", {"schema": "semantic-publication-journal.v0", "transaction_digest": d("revoke_transaction"), "state": "committed",
    "resulting_record_digest": d("publication_revocation"), "resulting_ledger_revision": 4, "resulting_ledger_head_digest": d("publication_revocation"),
    "staged_blob_set_digest": raw("revoke-blobs"), "linearized": True, "recovery_action": "none", "prior_journal_digest": d("withdraw_journal")})
revoke_marker = add("revoke_marker", {"schema": "semantic-publication-commit-marker.v0", "transaction_digest": d("revoke_transaction"), "journal_digest": d("revoke_journal"),
    "resulting_record_digest": d("publication_revocation"), "resulting_ledger_revision": 4, "resulting_ledger_head_digest": d("publication_revocation"), "fsync_complete": True})

# Lifecycle endpoints resolve complete publication authority, journal, marker, and canonical-ledger chains.
major_coordinate = {"schema": "semantic-release-coordinate.v0", "namespace": "ai-society.core", "semantic_version": "2.0.0", "capsule_digest": raw("capsule-2")}
major_decision = add("major_owner_ak_decision", {**copy.deepcopy(owner_decision), "decision_id": "semantic-release-2.0.0", "decision_revision": 3,
    "decision_record_digest": raw("owner-major-decision-record-3"), "activation_target_digest": major_coordinate["capsule_digest"], "ak_decision_reference_digest": ZERO})
major_action = {"kind": "release", "source_manifest_digest": raw("major-source-manifest"), "candidate_capsule_digest": major_coordinate["capsule_digest"], "compatibility_report_digest": raw("major-compatibility-report")}
major_action_digest = action_digest(major_action)
major_approval = add("major_owner_approval", {"schema": "semantic-owner-approval.v0", "namespace": "ai-society.core", "owner_policy_digest": d("owner_policy"), "owner_set_digest": d("owner_set"),
    "approval_predicate_digest": d("approval_predicate"), "action": major_action, "action_digest": major_action_digest,
    "votes": [{"owner_id": "owner-a", "owner_key_id": "owner-a-key-3", "approved_action_digest": major_action_digest, "approval_proof_digest": raw("major-vote-a")},
              {"owner_id": "owner-b", "owner_key_id": "owner-b-key-2", "approved_action_digest": major_action_digest, "approval_proof_digest": raw("major-vote-b")}],
    "decision_reference_digest": d("major_owner_ak_decision")})
major_tx = add("major_publication_transaction", {"schema": "semantic-publication-transaction.v0", "transaction_id": "publish-2.0.0", "operation": "publish", "namespace": "ai-society.core", "coordinate": major_coordinate,
    "owner_approval_digest": d("major_owner_approval"), "expected_prior_revision": 3, "expected_prior_head_digest": d("publication_withdrawal"), "replay_key_digest": raw("major-publish-replay"), "status_reason_digest": None})
major_publication = add("major_owner_publication", {"schema": "semantic-owner-publication.v0", "coordinate": major_coordinate, "transaction_digest": d("major_publication_transaction"),
    "owner_approval_digest": d("major_owner_approval"), "ledger_namespace": "ai-society.core", "ledger_revision": 4,
    "prior_publication_digest": d("publication_withdrawal"), "trust_root_digest": d("trust_root"), "status": "published"})
major_journal = add("major_publication_journal", {"schema": "semantic-publication-journal.v0", "transaction_digest": d("major_publication_transaction"), "state": "committed",
    "resulting_record_digest": d("major_owner_publication"), "resulting_ledger_revision": 4, "resulting_ledger_head_digest": d("major_owner_publication"),
    "staged_blob_set_digest": raw("major-publication-blobs"), "linearized": True, "recovery_action": "none", "prior_journal_digest": d("withdraw_journal")})
major_marker = add("major_publication_marker", {"schema": "semantic-publication-commit-marker.v0", "transaction_digest": d("major_publication_transaction"), "journal_digest": d("major_publication_journal"),
    "resulting_record_digest": d("major_owner_publication"), "resulting_ledger_revision": 4, "resulting_ledger_head_digest": d("major_owner_publication"), "fsync_complete": True})
dep_canonical_ledger = add("deprecation_canonical_ledger", {"schema": "semantic-publication-ledger-head.v0", "namespace": "ai-society.core", "ledger_revision": 2,
    "ledger_head_digest": d("owner_publication"), "status_record_digest": d("owner_publication"), "transaction_digest": d("publication_transaction"),
    "journal_digest": d("publication_journal"), "commit_marker_digest": d("publication_commit_marker"), "prior_ledger_head_digest": publish_tx["expected_prior_head_digest"]})
rem_canonical_ledger = add("removal_canonical_ledger", {"schema": "semantic-publication-ledger-head.v0", "namespace": "ai-society.core", "ledger_revision": 4,
    "ledger_head_digest": d("major_owner_publication"), "status_record_digest": d("major_owner_publication"), "transaction_digest": d("major_publication_transaction"),
    "journal_digest": d("major_publication_journal"), "commit_marker_digest": d("major_publication_marker"), "prior_ledger_head_digest": d("publication_withdrawal")})
deprecation_ledger = add("deprecation_accepted_ledger_record", {"schema": "semantic-accepted-lifecycle-ledger-record.v0", "namespace": "ai-society.core", "ledger_revision": 2,
    "ledger_head_digest": d("owner_publication"), "coordinate": coordinate, "publication_status_record_digest": d("owner_publication"),
    "publication_transaction_digest": d("publication_transaction"), "publication_journal_digest": d("publication_journal"), "publication_commit_marker_digest": d("publication_commit_marker"),
    "owner_approval_digest": d("owner_approval"), "trust_root_digest": d("trust_root"), "canonical_ledger_digest": d("deprecation_canonical_ledger"),
    "publication_status": "published", "accepted_for_lifecycle": True})
removal_ledger = add("removal_accepted_ledger_record", {"schema": "semantic-accepted-lifecycle-ledger-record.v0", "namespace": "ai-society.core", "ledger_revision": 4,
    "ledger_head_digest": d("major_owner_publication"), "coordinate": major_coordinate, "publication_status_record_digest": d("major_owner_publication"),
    "publication_transaction_digest": d("major_publication_transaction"), "publication_journal_digest": d("major_publication_journal"), "publication_commit_marker_digest": d("major_publication_marker"),
    "owner_approval_digest": d("major_owner_approval"), "trust_root_digest": d("trust_root"), "canonical_ledger_digest": d("removal_canonical_ledger"),
    "publication_status": "published", "accepted_for_lifecycle": True})
deprecation = add("deprecation_record", {"schema": "semantic-deprecation-record.v0", "namespace": "ai-society.core", "semantic_id": "core.Legacy", "introduced_coordinate": coordinate,
    "introduced_ledger_revision": 2, "prior_lifecycle_digest": None})
removal = add("removal_record", {"schema": "semantic-removal-record.v0", "namespace": "ai-society.core", "semantic_id": "core.Legacy", "removed_coordinate": major_coordinate,
    "removed_ledger_revision": 4, "deprecation_record_digest": d("deprecation_record"), "deprecation_ledger_revision": 2, "prior_lifecycle_digest": d("deprecation_record"),
    "compatibility_policy_digest": d("compatibility_policy"), "required_interval": 2, "prior_tombstone_registry_digest": d("tombstone_registry")})
resulting_tombstones = add("resulting_tombstone_registry", {"schema": "semantic-tombstone-registry.v0", "namespace": "ai-society.core", "registry_revision": 4,
    "entries": [{"semantic_id": "core.Legacy", "reason": "removed", "origin_record_digest": d("removal_record")}], "prior_registry_digest": d("tombstone_registry")})

trust_ref = {"trust_root_id": trust_root["trust_root_id"], "trust_root_revision": trust_root["trust_root_revision"], "trust_root_digest": d("trust_root"), "publication_ledger_revision": 2,
             "publication_digest": d("owner_publication"), "local_revocation_revision": 1, "local_revocation_head_digest": d("trust_revocation")}
rollback_materialization = add("rollback_target_materialization", {"schema": "semantic-rollback-technical-receipt.v0", "issuer": {"kind": "rocs", "id": "rocs-cli"}, "receipt_kind": "materialization", "subject_digest": raw("predecessor-tree"), "coordinate": predecessor, "runtime_identity": rocs_tool, "referenced_receipt_digest": None, "outcome": "valid"})
runtime_materialization = add("runtime_target_materialization", {"schema": "semantic-rollback-technical-receipt.v0", "issuer": {"kind": "rocs", "id": "rocs-cli"}, "receipt_kind": "materialization", "subject_digest": raw("old-runtime-tree"), "coordinate": coordinate, "runtime_identity": old_runtime, "referenced_receipt_digest": None, "outcome": "valid"})
runtime_revalidation = add("runtime_target_revalidation", {"schema": "semantic-rollback-technical-receipt.v0", "issuer": {"kind": "rocs", "id": "rocs-cli"}, "receipt_kind": "runtime_revalidation", "subject_digest": raw("runtime-compatible"), "coordinate": coordinate, "runtime_identity": old_runtime, "referenced_receipt_digest": d("runtime_target_materialization"), "outcome": "valid"})
disable_contract_receipt = add("disable_contract_receipt", {"schema": "semantic-rollback-technical-receipt.v0", "issuer": {"kind": "consumer_owner", "id": "consumer-owner"}, "receipt_kind": "disable_contract", "subject_digest": raw("disable-contract-body"), "coordinate": None, "runtime_identity": rocs_tool, "referenced_receipt_digest": None, "outcome": "valid"})
disable_rehearsal = add("disable_rehearsal_receipt", {"schema": "semantic-rollback-technical-receipt.v0", "issuer": {"kind": "recovery_controller", "id": "recovery"}, "receipt_kind": "rehearsal", "subject_digest": raw("disable-rehearsal-run"), "coordinate": None, "runtime_identity": rocs_tool, "referenced_receipt_digest": d("disable_contract_receipt"), "outcome": "valid"})
recovery_rehearsal = add("recovery_rehearsal_receipt", {"schema": "semantic-rollback-technical-receipt.v0", "issuer": {"kind": "recovery_controller", "id": "recovery"}, "receipt_kind": "rehearsal", "subject_digest": raw("recovery-rehearsal-run"), "coordinate": None, "runtime_identity": recovery_tool, "referenced_receipt_digest": None, "outcome": "valid"})
recovery_health = add("recovery_health_receipt", {"schema": "semantic-rollback-technical-receipt.v0", "issuer": {"kind": "recovery_controller", "id": "recovery"}, "receipt_kind": "health", "subject_digest": raw("recovery-health-check"), "coordinate": None, "runtime_identity": recovery_tool, "referenced_receipt_digest": d("recovery_rehearsal_receipt"), "outcome": "valid"})

semantic_target = {"kind": "semantic", "semantic_action": "switch", "target_coordinate": predecessor, "runtime_action": "retain", "target_materialization_receipt_digest": d("rollback_target_materialization")}
runtime_target = {"kind": "runtime", "semantic_action": "retain", "runtime_action": "switch", "target_runtime_identity": old_runtime, "target_materialization_receipt_digest": d("runtime_target_materialization"), "runtime_revalidation_receipt_digest": d("runtime_target_revalidation")}
disable_target = {"kind": "no_prior_disable", "semantic_action": "disable", "runtime_action": "retain", "disable_contract_digest": d("disable_contract_receipt"), "rehearsal_receipt_digest": d("disable_rehearsal_receipt")}
combined_target = {"kind": "combined", "semantic_stage": semantic_target, "runtime_stage": runtime_target, "stage_order": "semantic_then_runtime"}
intent = add("consumer_intent", {"schema": "semantic-consumer-intent.v0", "consumer_repository": consumer_repo, "intent_revision": 4, "desired_coordinate": coordinate, "runtime_identity": rocs_tool,
    "requested_posture": "named_canary", "accepted_compatibility": "compatible", "rollback_target": semantic_target, "decision_reference_digest": d("consumer_ak_decision"), "trust_reference": trust_ref,
    "verifier_contract_digest": raw("verifier-contract"), "limits_digest": raw("limits")})
acceptance = add("owner_acceptance", {"schema": "semantic-owner-acceptance.v0", "consumer_intent_digest": d("consumer_intent"), "consumer_repository": consumer_repo,
    "acceptance_authority": {"kind": "consumer_owner", "id": "consumer-owner"}, "acceptance_revision": 4, "acceptance_epoch": 80, "governing_scope_digest": consumer_decision["scope_digest"], "accepted_posture": "named_canary",
    "decision_reference_digest": d("consumer_ak_decision"), "valid_through_intent_revision": 4, "activation_epoch_not_after": 100, "revoked_by_digest": None})
materialization = add("materialization_receipt", {"schema": "semantic-materialization-verification-receipt.v0", "issuer": {"kind": "rocs", "id": "rocs-cli"},
    "consumer_intent_digest": d("consumer_intent"), "owner_acceptance_digest": d("owner_acceptance"), "coordinate": coordinate, "owner_approval_digest": d("owner_approval"), "trust_reference": trust_ref,
    "runtime_identity": rocs_tool, "capsule_archive_linkage_digest": d("capsule_archive_linkage"), "payload_projection_digest": d("payload_projection"), "source_payload_manifest_digest": d("payload_manifest"),
    "expected_consumer_manifest_digest": d("consumer_material_manifest"), "actual_consumer_manifest_digest": d("consumer_material_manifest"), "consumer_repository": consumer_repo,
    "compatibility_report_digest": d("compatibility_report"), "compatibility_outcome": "compatible", "prior_receipt_digest": raw("prior-materialization"), "rollback_target": semantic_target,
    "rollback_ready": True, "verifier_contract_digest": intent["verifier_contract_digest"], "transaction_id": "materialize-4", "journal_state": "committed", "commit_marker_digest": raw("materialize-marker")})
def available_artifact(name: str, kind: str, **fields: object) -> dict:
    value = {"schema": "semantic-rollback-availability-receipt.v0", "issuer": {"kind": "recovery_controller", "id": "recovery"}, "artifact_id": name.replace("_", "-"), "artifact_kind": kind,
        "coordinate": None, "runtime_identity": None, "materialization_receipt_digest": None, "runtime_revalidation_receipt_digest": None,
        "disable_contract_digest": None, "rehearsal_receipt_digest": None, "health_receipt_digest": None, "independently_available": True, "availability_epoch": 85}
    value.update(fields); return add(name, value)
semantic_available_artifact = available_artifact("semantic_target_artifact", "semantic_target", coordinate=predecessor, materialization_receipt_digest=semantic_target["target_materialization_receipt_digest"])
runtime_available_artifact = available_artifact("runtime_target_artifact", "runtime_target", runtime_identity=old_runtime, materialization_receipt_digest=runtime_target["target_materialization_receipt_digest"], runtime_revalidation_receipt_digest=runtime_target["runtime_revalidation_receipt_digest"])
disable_available_artifact = available_artifact("disable_target_artifact", "disable_target", disable_contract_digest=disable_target["disable_contract_digest"], rehearsal_receipt_digest=disable_target["rehearsal_receipt_digest"])
recovery_available_artifact = available_artifact("recovery_runtime_artifact", "recovery_runtime", runtime_identity=recovery_tool, rehearsal_receipt_digest=d("recovery_rehearsal_receipt"), health_receipt_digest=d("recovery_health_receipt"))
def availability(name: str, target: dict, **fields: object) -> dict:
    base = {"schema": "semantic-rollback-availability-proof.v0", "consumer_intent_digest": d("consumer_intent"), "owner_acceptance_digest": d("owner_acceptance"),
        "materialization_verification_receipt_digest": d("materialization_receipt"), "availability_epoch": 85, "target_kind": target["kind"],
        "recovery_runtime_identity": recovery_tool, "recovery_runtime_available": True,
        "semantic_materialization_receipt_digest": None, "semantic_coordinate": None, "runtime_materialization_receipt_digest": None,
        "runtime_identity": None, "runtime_revalidation_receipt_digest": None, "disable_contract_digest": None, "rehearsal_receipt_digest": None,
        "semantic_target_artifact_digest": None, "runtime_target_artifact_digest": None, "disable_target_artifact_digest": None,
        "recovery_artifact_digest": d("recovery_runtime_artifact")}
    kind = target["kind"]
    if kind in {"semantic", "combined"}: base["semantic_target_artifact_digest"] = d("semantic_target_artifact")
    if kind in {"runtime", "combined"}: base["runtime_target_artifact_digest"] = d("runtime_target_artifact")
    if kind == "no_prior_disable": base["disable_target_artifact_digest"] = d("disable_target_artifact")
    base.update(fields)
    return add(name, base)

semantic_availability = availability("semantic_rollback_availability", semantic_target, semantic_materialization_receipt_digest=semantic_target["target_materialization_receipt_digest"], semantic_coordinate=predecessor)
runtime_availability = availability("runtime_rollback_availability", runtime_target, runtime_materialization_receipt_digest=runtime_target["target_materialization_receipt_digest"], runtime_identity=old_runtime, runtime_revalidation_receipt_digest=runtime_target["runtime_revalidation_receipt_digest"])
disable_availability = availability("disable_rollback_availability", disable_target, disable_contract_digest=disable_target["disable_contract_digest"], rehearsal_receipt_digest=disable_target["rehearsal_receipt_digest"])
combined_availability = availability("combined_rollback_availability", combined_target, semantic_materialization_receipt_digest=semantic_target["target_materialization_receipt_digest"], semantic_coordinate=predecessor, runtime_materialization_receipt_digest=runtime_target["target_materialization_receipt_digest"], runtime_identity=old_runtime, runtime_revalidation_receipt_digest=runtime_target["runtime_revalidation_receipt_digest"])

activation = add("activation_receipt", {"schema": "semantic-activation-receipt.v0", "issuer": {"kind": "consumer_owner", "id": "consumer-owner"}, "consumer_owner_issuer_id": "consumer-owner", "consumer_intent_digest": d("consumer_intent"), "owner_acceptance_digest": d("owner_acceptance"),
    "materialization_verification_receipt_digest": d("materialization_receipt"), "rollback_availability_proof_digest": d("semantic_rollback_availability"), "consumer_repository": consumer_repo, "coordinate": coordinate, "runtime_identity": rocs_tool, "activation_scope": "named_canary",
    "activation_revision": 1, "prior_activation_revision": None, "activation_epoch": 90, "acceptance_epoch": 80, "gate_decision_reference_digest": d("consumer_ak_decision"), "activation_target_digest": coord_digest,
    "evidence_criteria_digest": consumer_decision["evidence_criteria_digest"], "rollback_plan_digest": consumer_decision["rollback_plan_digest"], "stop_conditions_digest": consumer_decision["stop_conditions_digest"], "current_activation_head_digest": None,
    "previous_activation_receipt_digest": None, "status": "activated", "revoked_by_digest": None, "superseded_by_activation_receipt_digest": None})
active_state = {"enabled": True, "coordinate": coordinate, "runtime_identity": rocs_tool}
activation_head = {"kind": "activation", "digest": d("activation_receipt")}
generation = add("rocs_generation_receipt", {"schema": "semantic-rocs-generation-receipt.v0", "issuer": {"kind": "rocs", "id": "rocs-cli"}, "claim_scope": "generated_output_only",
    "activation_receipt_digest": d("activation_receipt"), "activation_head_revision": 1, "activation_head_digest": d("activation_receipt"),
    "coordinate": coordinate, "runtime_identity": rocs_tool, "request_digest": raw("request"), "result_digest": raw("result"),
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


def history(name: str, request: dict, result: str, after: dict, stages: list[dict], failure_stage: str | None, error_digest: str | None, supersedes: str | None) -> dict:
    return add(name, {"schema": "semantic-rollback-history-transition.v0", "rollback_request_digest": request["rollback_request_digest"], "result": result,
        "active_state_before": active_state, "active_state_after": after, "stages": stages, "failure_stage": failure_stage, "error_digest": error_digest,
        "history_head_before": activation_head, "supersedes_activation_receipt_digest": supersedes})

semantic_request = add("semantic_rollback_request", {"schema": "semantic-rollback-request.v0", "issuer": {"kind": "consumer_owner", "id": "consumer-owner"}, "active_activation_receipt_digest": d("activation_receipt"),
    "from_state": active_state, "target": semantic_target, "recovery_runtime_identity": recovery_tool, "owner_decision_reference_digest": d("consumer_ak_decision"), "precondition_digest": raw("semantic-preconditions")})
semantic_after = {"enabled": True, "coordinate": predecessor, "runtime_identity": rocs_tool}; semantic_stages = [{"stage": "semantic", "result": "completed", "error_digest": None}]
semantic_history = history("semantic_rollback_history", semantic_request, "rolled_back", semantic_after, semantic_stages, None, None, d("activation_receipt"))
semantic_receipt = add("semantic_rollback_receipt", {"schema": "semantic-rollback-receipt.v0", "issuer": {"kind": "recovery_controller", "id": "recovery"}, "rollback_request_digest": d("semantic_rollback_request"),
    "request_target_kind": "semantic", "result": "rolled_back", "stage_order": None, "active_state_before": active_state, "active_state_after": semantic_after,
    "availability_proof_digest": d("semantic_rollback_availability"), "runtime_revalidation_receipt_digest": None, "stages": semantic_stages, "failure_stage": None,
    "history_head_before": activation_head, "history_head_after": {"kind": "rollback", "digest": d("semantic_rollback_history")}, "error_digest": None,
    "supersedes_activation_receipt_digest": d("activation_receipt"), "ak_evidence_linkage_digest": d("ak_evidence_linkage"), "pi_delivery_receipt_digest": d("pi_delivery_delivered")})
runtime_request = add("runtime_rollback_request", {"schema": "semantic-rollback-request.v0", "issuer": {"kind": "consumer_owner", "id": "consumer-owner"}, "active_activation_receipt_digest": d("activation_receipt"),
    "from_state": active_state, "target": runtime_target, "recovery_runtime_identity": recovery_tool, "owner_decision_reference_digest": d("consumer_ak_decision"), "precondition_digest": raw("runtime-preconditions")})
runtime_after = {"enabled": True, "coordinate": coordinate, "runtime_identity": old_runtime}; runtime_stages = [{"stage": "runtime", "result": "completed", "error_digest": None}]
runtime_history = history("runtime_rollback_history", runtime_request, "rolled_back", runtime_after, runtime_stages, None, None, d("activation_receipt"))
runtime_receipt = add("runtime_rollback_receipt", {"schema": "semantic-rollback-receipt.v0", "issuer": {"kind": "recovery_controller", "id": "recovery"}, "rollback_request_digest": d("runtime_rollback_request"),
    "request_target_kind": "runtime", "result": "rolled_back", "stage_order": None, "active_state_before": active_state, "active_state_after": runtime_after,
    "availability_proof_digest": d("runtime_rollback_availability"), "runtime_revalidation_receipt_digest": runtime_target["runtime_revalidation_receipt_digest"], "stages": runtime_stages, "failure_stage": None,
    "history_head_before": activation_head, "history_head_after": {"kind": "rollback", "digest": d("runtime_rollback_history")}, "error_digest": None,
    "supersedes_activation_receipt_digest": d("activation_receipt"), "ak_evidence_linkage_digest": None, "pi_delivery_receipt_digest": None})
disable_request = add("disable_rollback_request", {"schema": "semantic-rollback-request.v0", "issuer": {"kind": "consumer_owner", "id": "consumer-owner"}, "active_activation_receipt_digest": d("activation_receipt"),
    "from_state": active_state, "target": disable_target, "recovery_runtime_identity": recovery_tool, "owner_decision_reference_digest": d("consumer_ak_decision"), "precondition_digest": raw("disable-preconditions")})
disable_after = {"enabled": False, "coordinate": None, "runtime_identity": rocs_tool}; disable_stages = [{"stage": "disable", "result": "completed", "error_digest": None}]
disable_history = history("disable_rollback_history", disable_request, "disabled", disable_after, disable_stages, None, None, d("activation_receipt"))
disable_receipt = add("disable_rollback_receipt", {"schema": "semantic-rollback-receipt.v0", "issuer": {"kind": "recovery_controller", "id": "recovery"}, "rollback_request_digest": d("disable_rollback_request"),
    "request_target_kind": "no_prior_disable", "result": "disabled", "stage_order": None, "active_state_before": active_state, "active_state_after": disable_after,
    "availability_proof_digest": d("disable_rollback_availability"), "runtime_revalidation_receipt_digest": None, "stages": disable_stages, "failure_stage": None,
    "history_head_before": activation_head, "history_head_after": {"kind": "disable", "digest": d("disable_rollback_history")}, "error_digest": None,
    "supersedes_activation_receipt_digest": d("activation_receipt"), "ak_evidence_linkage_digest": None, "pi_delivery_receipt_digest": None})
combined_request = add("combined_rollback_request", {"schema": "semantic-rollback-request.v0", "issuer": {"kind": "consumer_owner", "id": "consumer-owner"}, "active_activation_receipt_digest": d("activation_receipt"),
    "from_state": active_state, "target": combined_target, "recovery_runtime_identity": recovery_tool, "owner_decision_reference_digest": d("consumer_ak_decision"), "precondition_digest": raw("combined-preconditions")})
partial_error = raw("runtime-stage-error"); partial_after = semantic_after
partial_stages = [{"stage": "semantic", "result": "completed", "error_digest": None}, {"stage": "runtime", "result": "failed", "error_digest": partial_error}]
partial_history = history("combined_partial_history", combined_request, "partial_failure", partial_after, partial_stages, "runtime", partial_error, None)
partial_receipt = add("combined_partial_failure_receipt", {"schema": "semantic-rollback-receipt.v0", "issuer": {"kind": "recovery_controller", "id": "recovery"}, "rollback_request_digest": d("combined_rollback_request"),
    "request_target_kind": "combined", "result": "partial_failure", "stage_order": "semantic_then_runtime", "active_state_before": active_state, "active_state_after": partial_after,
    "availability_proof_digest": d("combined_rollback_availability"), "runtime_revalidation_receipt_digest": None, "stages": partial_stages, "failure_stage": "runtime",
    "history_head_before": activation_head, "history_head_after": {"kind": "rollback", "digest": d("combined_partial_history")}, "error_digest": partial_error,
    "supersedes_activation_receipt_digest": None, "ak_evidence_linkage_digest": None, "pi_delivery_receipt_digest": None})
failed_error = raw("semantic-stage-error")
failed_receipt = add("failed_rollback_receipt", {"schema": "semantic-rollback-receipt.v0", "issuer": {"kind": "recovery_controller", "id": "recovery"}, "rollback_request_digest": d("semantic_rollback_request"),
    "request_target_kind": "semantic", "result": "failed", "stage_order": None, "active_state_before": active_state, "active_state_after": active_state,
    "availability_proof_digest": d("semantic_rollback_availability"), "runtime_revalidation_receipt_digest": None,
    "stages": [{"stage": "semantic", "result": "failed", "error_digest": failed_error}], "failure_stage": "semantic", "history_head_before": activation_head,
    "history_head_after": activation_head, "error_digest": failed_error, "supersedes_activation_receipt_digest": None, "ak_evidence_linkage_digest": None, "pi_delivery_receipt_digest": None})
def unresolved_ref(reference_id: str, repository: dict, required_state: str) -> dict:
    return {"resolution": "unresolved_candidate", "reference_id": reference_id, "repository": repository, "ak_store_head": None,
        "task_id": None, "task_record_digest": None, "artifact_digest": None, "required_state": required_state}
def stops(rows: list[tuple[str, str]], repository: dict) -> list[dict]:
    rows = sorted(rows)
    return [{"condition_id": cid, "condition_kind": kind, "fact_reference": unresolved_ref("fact:" + cid, repository, "accepted_current"),
        "trigger_state": "unsatisfied_or_noncurrent", "required_effect": "stop_before_mutation", "resume_state": "accepted_current"} for cid, kind in rows]
ak_prerequisites = [unresolved_ref(x, ak_coord_repo, "accepted_current") for x in ["adr:0053", "decision:53", "plan:decision-53-implementation", "plan:decision-53-validation-rollout-rollback"]]
ak_evidence = [unresolved_ref(x, ak_coord_repo, "evidence_accepted_current") for x in ["accepted-decision-reference", "deterministic-rerun", "docs-strict", "node-validator", "owner-task-references", "python-validator", "rollback-rehearsal"]]
ak_stop_rows = [("stale-or-revoked-decision", "stale_or_revoked_decision"), ("store-head-drift", "store_head_drift"), ("scope-drift", "scope_drift"),
    ("missing-owner-task", "missing_owner_task"), ("attempted-owner-substitution", "owner_substitution"), ("attempted-use-as-authorization", "authorization_escalation")]
ak_coordination_contract = add("ak_coordination_task_contract", {"schema": "semantic-non-authorizing-task-contract.v0", "task_contract_id": "decision-53-ak-coordination",
    "task_id": "candidate-decision-53-ak-coordination", "task_owner_id": "agent-kernel-owner", "task_kind": "ak_coordination", "repository": ak_coord_repo, "allowed_paths": [],
    "dependencies": [], "prerequisites": ak_prerequisites, "required_evidence": ak_evidence, "rollback_owner": {"kind": "ak", "id": "agent-kernel-owner"},
    "stop_conditions": stops(ak_stop_rows, ak_coord_repo), "authority_scope": "coordination_only", "authorizes_execution": False, "authorizes_publication": False,
    "authorizes_adoption": False, "contract_status": "candidate_not_created"})
consumer_dependencies = [unresolved_ref(x, canary_repo, "completed_current") for x in ["candidate-decision-53-ak-coordination", "candidate-decision-53-rocs-implementation", "candidate-decision-53-semantic-owner-publication"]]
consumer_prerequisites = [unresolved_ref(x, canary_repo, "accepted_current") for x in ["adr:0053", "consent:pi-canary-consumer-owner", "decision:53", "plan:decision-53-implementation", "plan:decision-53-validation-rollout-rollback"]]
consumer_evidence = [unresolved_ref(x, canary_repo, "evidence_accepted_current") for x in ["activation-receipt", "canary-evidence", "consumer-intent-and-acceptance", "exact-materialization-receipt", "rollback-availability-proof", "rollback-history-and-rehearsal", "scoped-gate-decision"]]
consumer_stop_rows = [("missing-owner-consent", "missing_owner_consent"), ("target-or-recovery-unavailable", "rollback_unavailable"), ("stale-head-or-trust", "stale_trust_or_head"),
    ("projection-or-issuer-drift", "projection_or_issuer_drift"), ("failed-validator", "validator_failure"), ("unknown-or-incompatible", "compatibility_failure"),
    ("missing-rollback-rehearsal", "missing_rollback_rehearsal"), ("scope-beyond-named-canary", "canary_scope_exceeded"), ("default-or-fleet-request", "default_or_fleet_request")]
consumer_canary_contract = add("first_consumer_task_contract", {"schema": "semantic-non-authorizing-task-contract.v0", "task_contract_id": "decision-53-first-consumer-canary",
    "task_id": "candidate-decision-53-first-consumer-canary", "task_owner_id": "consumer-owner", "task_kind": "first_consumer", "repository": canary_repo,
    "allowed_paths": ["config/semantic-release/canary.json", "docs/project/semantic-release-canary-evidence.md", "scripts/ci/semantic-release-canary.sh"],
    "dependencies": consumer_dependencies, "prerequisites": consumer_prerequisites, "required_evidence": consumer_evidence,
    "rollback_owner": {"kind": "consumer_owner", "id": "consumer-owner"}, "stop_conditions": stops(consumer_stop_rows, canary_repo),
    "authority_scope": "consumer_owner_candidate_only", "authorizes_execution": False, "authorizes_publication": False, "authorizes_adoption": False, "contract_status": "candidate_not_created"})
audit = add("audit_envelope", {"schema": "semantic-audit-envelope.v0", "artifact_schema": "semantic-rollback-receipt.v0", "artifact_digest": d("semantic_rollback_receipt"), "event": "rolled_back",
    "recorded_at": "2026-07-13T12:30:45Z", "issuer": {"kind": "ak", "id": "agent-kernel"}, "audit_sequence": 9, "previous_audit_envelope_digest": raw("audit-8")})
error = add("error_envelope", {"schema": "semantic-protocol-error.v0", "code": "digest_mismatch", "stage": "validate", "retryable": False, "related_artifact_digest": d("capsule"),
    "details": [{"key": "artifact", "value": "capsule"}], "error_digest": ZERO})

links = [
    ("owner_policy", "/owner_set_digest", "owner_set"), ("owner_policy", "/approval_predicate_digest", "approval_predicate"), ("owner_policy", "/compatibility_policy_digest", "compatibility_policy"),
    ("capsule_archive_linkage", "/archive_manifest_digest", "capsule_archive_manifest"), ("payload_projection", "/payload_manifest_digest", "payload_manifest"),
    ("capsule", "/payload_projection_digest", "payload_projection"), ("capsule", "/capsule_archive_linkage_digest", "capsule_archive_linkage"), ("coordinate", "/capsule_digest", "capsule"),
    ("owner_approval", "/decision_reference_digest", "owner_ak_decision"), ("owner_approval", "/action/candidate_capsule_digest", "capsule"),
    ("trust_rotation", "/new_trust_root_digest", "rotated_trust_root"), ("trust_rotation", "/approval_digest", "rotation_approval"),
    ("trust_revocation", "/owner_approval_digest", "revocation_approval"), ("owner_publication", "/owner_approval_digest", "owner_approval"),
    ("publication_journal", "/transaction_digest", "publication_transaction"), ("publication_journal", "/resulting_record_digest", "owner_publication"),
    ("publication_commit_marker", "/journal_digest", "publication_journal"), ("publication_commit_marker", "/resulting_ledger_head_digest", "owner_publication"),
    ("consumer_intent", "/decision_reference_digest", "consumer_ak_decision"), ("owner_acceptance", "/consumer_intent_digest", "consumer_intent"),
    ("materialization_receipt", "/payload_projection_digest", "payload_projection"), ("materialization_receipt", "/expected_consumer_manifest_digest", "consumer_material_manifest"),
    ("activation_receipt", "/materialization_verification_receipt_digest", "materialization_receipt"), ("rocs_generation_receipt", "/activation_receipt_digest", "activation_receipt"),
    ("pi_delivery_delivered", "/rocs_generation_receipt_digest", "rocs_generation_receipt"), ("ak_evidence_linkage", "/pi_delivery_receipt_digest", "pi_delivery_delivered"),
    ("semantic_rollback_receipt", "/rollback_request_digest", "semantic_rollback_request"), ("audit_envelope", "/artifact_digest", "semantic_rollback_receipt")]

golden = {"protocol": "semantic-release-v0", "rfc_revision": "semantic-release-revision-v6", "canonicalization": "RFC8785 JCS after raw-token duplicate-free UTF-8 canonical-integer-only I-JSON validation",
    "digest_construction": "sha256(UTF8(domain) || 0x00 || preimage)", "raw_preimages": [
        {"name": "raw_blob_example", "domain": "semantic-release.raw-blob.v0", "preimage_utf8": "agent-source", "digest": raw("agent-source")},
        {"name": "semantic_payload_example", "domain": "semantic-release.semantic-payload.v0", "preimage_utf8": "semantic-payload-1.1", "digest": raw("semantic-payload-1.1", "semantic-release.semantic-payload.v0")}],
    "records": records, "chain_assertions": [{"record": a, "instance_path": p, "equals_record": b} for a,p,b in links]}

# Differential fixtures include accepted transitions as well as adversarial failures.
cases: list[dict] = []
insufficient = variant(owner_approval, votes=owner_approval["votes"][:1])
revoked_vote_context = {"owner_set": variant(owner_set, members=[owner_set["members"][0], {**owner_set["members"][1], "status": "revoked", "revocation_digest": raw("key-revoked")}, owner_set["members"][2]]), "predicate": predicate, "policy": owner_policy}
# Policy is rebound to the adversarial set so revocation, rather than digest drift, remains the tested failure.
revoked_vote_context["policy"] = variant(owner_policy, owner_set_digest=revoked_vote_context["owner_set"]["owner_set_digest"])
revoked_vote_subject = variant(owner_approval, owner_policy_digest=revoked_vote_context["policy"]["owner_policy_digest"], owner_set_digest=revoked_vote_context["owner_set"]["owner_set_digest"])
unanimous_predicate = variant(predicate, mode="unanimous", threshold=3)
unanimous_policy = variant(owner_policy, approval_predicate_digest=unanimous_predicate["approval_predicate_digest"])
unanimous_approval = variant(owner_approval, owner_policy_digest=unanimous_policy["owner_policy_digest"], approval_predicate_digest=unanimous_predicate["approval_predicate_digest"], votes=owner_approval["votes"] + [
    {"owner_id": "owner-c", "owner_key_id": "owner-c-key-1", "approved_action_digest": release_action_digest, "approval_proof_digest": raw("vote-release-c")}])
bad_unanimous_predicate = variant(unanimous_predicate, threshold=2)
bad_unanimous_policy = variant(owner_policy, approval_predicate_digest=bad_unanimous_predicate["approval_predicate_digest"])
bad_unanimous_approval = variant(unanimous_approval, owner_policy_digest=bad_unanimous_policy["owner_policy_digest"], approval_predicate_digest=bad_unanimous_predicate["approval_predicate_digest"])
rotation_context = {"current_root_digest": d("trust_root"), "old_root": trust_root, "new_root": new_trust_root, "approval": rotation_approval, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "revoked": []}
revocation_context = {"approval": revocation_approval, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "prior_revision": 0, "prior_head": None}
root_revocation_action = {"kind": "trust_revocation", "namespace": "ai-society.core", "owner_policy_digest": d("owner_policy"), "owner_set_digest": d("owner_set"),
    "approval_predicate_digest": d("approval_predicate"), "target_kind": "trust_root", "target_digest": d("trust_root"), "effective_ledger_revision": 4,
    "reason_digest": raw("root-revocation-reason"), "prior_revocation_digest": d("trust_revocation"), "revocation_revision": 2}
root_revocation_action_digest = action_digest(root_revocation_action)
root_revocation_approval = variant(revocation_approval, action=root_revocation_action, action_digest=root_revocation_action_digest,
    votes=[{**vote, "approved_action_digest": root_revocation_action_digest} for vote in revocation_approval["votes"]])
root_revocation = variant(revocation, revocation_revision=2, target_kind="trust_root", target_digest=d("trust_root"), effective_ledger_revision=4,
    reason_digest=root_revocation_action["reason_digest"], owner_approval_digest=root_revocation_approval["owner_approval_digest"], prior_revocation_digest=d("trust_revocation"))
root_revocation_context = {"approval": root_revocation_approval, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "prior_revision": 1, "prior_head": d("trust_revocation")}
reordered_trust_root = variant(trust_root, key_ids=list(reversed(trust_root["key_ids"])))
duplicate_trust_root_keys = variant(trust_root, key_ids=[trust_root["key_ids"][0], trust_root["key_ids"][0]])
reordered_approval = variant(owner_approval, votes=list(reversed(owner_approval["votes"])))
stale_context_owner_set = copy.deepcopy(owner_set); stale_context_owner_set["owner_set_revision"] = 9
reordered_context_owner_set = variant(owner_set, members=list(reversed(owner_set["members"])))
revocation_authority_action = {**revocation_action, "owner_policy_digest": raw("wrong-owner-policy-in-action")}
revocation_authority_action_digest = action_digest(revocation_authority_action)
revocation_authority_approval = variant(revocation_approval, action=revocation_authority_action, action_digest=revocation_authority_action_digest,
    votes=[{**vote, "approved_action_digest": revocation_authority_action_digest} for vote in revocation_approval["votes"]])
revocation_authority_record = variant(revocation, owner_approval_digest=revocation_authority_approval["owner_approval_digest"])
cases += [
    case("threshold_two_of_three_accepts", "approval_threshold", owner_approval, None, {"owner_set": owner_set, "predicate": predicate, "policy": owner_policy}),
    case("threshold_insufficient_rejected", "approval_threshold", insufficient, "approval_threshold_unsatisfied", {"owner_set": owner_set, "predicate": predicate, "policy": owner_policy}),
    case("approval_owner_policy_digest_drift_rejected", "approval_threshold", variant(owner_approval, owner_policy_digest=raw("wrong-owner-policy")), "approval_threshold_unsatisfied", {"owner_set": owner_set, "predicate": predicate, "policy": owner_policy}),
    case("approval_owner_set_digest_drift_rejected", "approval_threshold", variant(owner_approval, owner_set_digest=raw("wrong-owner-set")), "approval_threshold_unsatisfied", {"owner_set": owner_set, "predicate": predicate, "policy": owner_policy}),
    case("approval_predicate_digest_drift_rejected", "approval_threshold", variant(owner_approval, approval_predicate_digest=raw("wrong-predicate")), "approval_threshold_unsatisfied", {"owner_set": owner_set, "predicate": predicate, "policy": owner_policy}),
    case("approval_namespace_drift_rejected", "approval_threshold", variant(owner_approval, namespace="other.space"), "approval_threshold_unsatisfied", {"owner_set": owner_set, "predicate": predicate, "policy": owner_policy}),
    case("referenced_owner_set_stale_self_digest_rejected", "approval_threshold", owner_approval, "digest_mismatch", {"owner_set": stale_context_owner_set, "predicate": predicate, "policy": owner_policy}),
    case("referenced_context_order_validated_before_relation", "approval_threshold", owner_approval, "malformed_input", {"owner_set": reordered_context_owner_set, "predicate": predicate, "policy": owner_policy}),
    case("referenced_policy_expected_type_rejected", "approval_threshold", owner_approval, "malformed_input", {"owner_set": owner_set, "predicate": predicate, "policy": owner_set}),
    case("approval_vote_order_rejected_independently", "approval_threshold", reordered_approval, "malformed_input", {"owner_set": owner_set, "predicate": predicate, "policy": owner_policy}),
    case("unanimous_threshold_equals_active_owner_count", "approval_threshold", unanimous_approval, None, {"owner_set": owner_set, "predicate": unanimous_predicate, "policy": unanimous_policy}),
    case("unanimous_threshold_mismatch_rejected", "approval_threshold", bad_unanimous_approval, "approval_threshold_unsatisfied", {"owner_set": owner_set, "predicate": bad_unanimous_predicate, "policy": bad_unanimous_policy}),
    case("revoked_owner_vote_rejected", "approval_threshold", revoked_vote_subject, "trust_revoked", revoked_vote_context),
    case("trust_root_keys_require_utf8_order", "pi_variant", reordered_trust_root, "malformed_input"),
    case("trust_root_keys_require_uniqueness", "pi_variant", duplicate_trust_root_keys, "malformed_input"),
    case("valid_old_to_new_root_rotation", "trust_rotation", rotation, None, rotation_context),
    case("rotation_not_bound_to_current_root", "trust_rotation", variant(rotation, old_trust_root_digest=raw("wrong-root")), "trust_reference_stale", rotation_context),
    case("rotation_revision_not_increasing_rejected", "trust_rotation", variant(rotation, new_trust_root_revision=5), "trust_reference_stale", rotation_context),
    case("rotation_approval_action_drift_rejected", "trust_rotation", variant(rotation, approval_digest=d("owner_approval")), "trust_reference_stale", rotation_context),
    case("rotation_owner_set_binding_drift_rejected", "trust_rotation", variant(rotation, owner_set_digest=raw("wrong-owner-set")), "trust_reference_stale", rotation_context),
    case("rotation_predicate_binding_drift_rejected", "trust_rotation", variant(rotation, approval_predicate_digest=raw("wrong-predicate")), "trust_reference_stale", rotation_context),
    case("rotation_namespace_binding_drift_rejected", "trust_rotation", variant(rotation, namespace="other.space"), "trust_reference_stale", rotation_context),
    case("revoked_rotation_root_rejected", "trust_rotation", rotation, "trust_revoked", {**rotation_context, "revoked": [d("trust_root")]}),
    case("valid_trust_revocation_transition", "trust_revocation", revocation, None, revocation_context),
    case("valid_trust_root_revocation_transition", "trust_revocation", root_revocation, None, root_revocation_context),
    case("revocation_prior_head_drift_rejected", "trust_revocation", variant(revocation, prior_revocation_digest=raw("wrong-revocation-head")), "trust_reference_stale", revocation_context),
    case("revocation_revision_not_increasing_rejected", "trust_revocation", variant(revocation, revocation_revision=2), "trust_reference_stale", revocation_context),
    case("revocation_approval_action_drift_rejected", "trust_revocation", variant(revocation, owner_approval_digest=d("owner_approval")), "trust_reference_stale", revocation_context),
    case("trust_revocation_action_requires_full_authority_chain", "trust_revocation", revocation_authority_record, "trust_reference_stale", {**revocation_context, "approval": revocation_authority_approval})]
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
duplicate_conditions = variant(conditional_report, conditions=[condition, condition])
surplus_condition = copy.deepcopy(condition); surplus_condition["condition_id"] = "surplus-proof"
surplus_conditions = variant(conditional_report, conditions=[condition, surplus_condition])
shared_condition_report = variant(conditional_report, changes=[
    {"category": "constraint_change", "semantic_id": "core.Agent", "classification": "conditionally_compatible", "semver_effect": "minor", "condition_id": "constraint-proof"},
    {"category": "constraint_change", "semantic_id": "core.Other", "classification": "conditionally_compatible", "semver_effect": "minor", "condition_id": "constraint-proof"}])
lowered_override_action = {**override_action, "semver_effect_floor": "minor"}
lowered_override_action_digest = action_digest(lowered_override_action)
lowered_override_approval = variant(override_approval, action=lowered_override_action, action_digest=lowered_override_action_digest,
    votes=[{**vote, "approved_action_digest": lowered_override_action_digest} for vote in override_approval["votes"]])
lowered_override = variant(override, semver_effect_floor="minor", owner_approval_digest=lowered_override_approval["owner_approval_digest"])
lowered_report = variant(overridden_report, candidate_version="1.1.0", required_semver_effect="minor", override_digests=[lowered_override["compatibility_override_digest"]])
incomplete_override_approval = copy.deepcopy(override_approval); del incomplete_override_approval["action"]["condition"]; rehash(incomplete_override_approval)
wrong_namespace_override_approval = variant(override_approval, namespace="other.space")
wrong_namespace_override = variant(override, owner_approval_digest=wrong_namespace_override_approval["owner_approval_digest"])
wrong_namespace_override_report = variant(overridden_report, override_digests=[wrong_namespace_override["compatibility_override_digest"]])
override_context = {"policy": compat_policy, "prior_version": "1.0.0", "overrides": [override], "override_approvals": {d("override_approval"): override_approval},
    "owner_policy": owner_policy, "owner_set": owner_set, "predicate": predicate}
override_drift = variant(overridden_report, override_digests=[])
extra_tombstones = variant(resulting_tombstones, entries=resulting_tombstones["entries"] + [{"semantic_id": "core.Surplus", "reason": "removed", "origin_record_digest": raw("surplus-origin")}])
wrong_tombstone_reason = variant(resulting_tombstones, entries=[{**resulting_tombstones["entries"][0], "reason": "renamed"}])
prior_tombstones_with_entry = variant(tombstones, entries=[{"semantic_id": "core.Old", "reason": "removed", "origin_record_digest": raw("old-removal") }])
removal_after_existing_tombstone = variant(removal, prior_tombstone_registry_digest=prior_tombstones_with_entry["tombstone_registry_digest"])
dropped_prior_entry_registry = variant(resulting_tombstones, prior_registry_digest=prior_tombstones_with_entry["tombstone_registry_digest"],
    entries=[{"semantic_id": "core.Legacy", "reason": "removed", "origin_record_digest": removal_after_existing_tombstone["removal_record_digest"]}])
tombstoned_addition = variant(compat_report, changes=[{"category": "addition", "semantic_id": "core.Legacy", "classification": "compatible", "semver_effect": "minor", "condition_id": None}])
stale_deprecation_ledger = copy.deepcopy(deprecation_ledger); stale_deprecation_ledger["ledger_revision"] = 1
lifecycle_context = {"deprecation": deprecation, "policy": compat_policy, "prior_tombstones": tombstones, "resulting_tombstones": resulting_tombstones,
    "deprecation_ledger": deprecation_ledger, "removal_ledger": removal_ledger, "deprecation_publication": publication, "removal_publication": major_publication,
    "deprecation_transaction": publish_tx, "deprecation_journal": publish_journal, "deprecation_marker": publish_marker, "deprecation_approval": owner_approval,
    "deprecation_prior_status": prior_publication, "deprecation_prior_journal": prior_publish_journal, "deprecation_canonical_ledger": dep_canonical_ledger,
    "removal_transaction": major_tx, "removal_journal": major_journal, "removal_marker": major_marker, "removal_approval": major_approval,
    "removal_prior_status": withdrawal, "removal_prior_journal": withdraw_journal, "removal_canonical_ledger": rem_canonical_ledger,
    "owner_policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "trust_root": trust_root,
    "deprecation_decision": owner_decision, "removal_decision": major_decision,
    "canonical_store_head": ak_store_head, "current_deprecation_decision_record_digest": owner_decision["decision_record_digest"],
    "current_removal_decision_record_digest": major_decision["decision_record_digest"],
    "canonical_deprecation_revision": 2, "canonical_deprecation_head": d("owner_publication"), "canonical_removal_revision": 4, "canonical_removal_head": d("major_owner_publication")}
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
    case("duplicate_compatibility_condition_rejected", "compatibility", duplicate_conditions, "compatibility_rejected", {"policy": compat_policy, "prior_version": "1.0.0"}),
    case("surplus_unreferenced_condition_rejected", "compatibility", surplus_conditions, "compatibility_rejected", {"policy": compat_policy, "prior_version": "1.0.0"}),
    case("condition_reference_must_be_bijective", "compatibility", shared_condition_report, "compatibility_rejected", {"policy": compat_policy, "prior_version": "1.0.0"}),
    case("executable_owner_override_accepts", "compatibility", overridden_report, None, override_context),
    case("override_digest_omission_rejected", "compatibility", override_drift, "compatibility_rejected", override_context),
    case("override_cannot_lower_unknown_semver_floor", "compatibility", lowered_report, "compatibility_rejected", {"policy": compat_policy, "prior_version": "1.0.0", "overrides": [lowered_override], "override_approvals": {lowered_override_approval["owner_approval_digest"]: lowered_override_approval}, "owner_policy": owner_policy, "owner_set": owner_set, "predicate": predicate}),
    case("override_approval_requires_complete_override", "pi_variant", incomplete_override_approval, "malformed_input", schema_valid=False),
    case("override_approval_namespace_chain_must_match", "compatibility", wrong_namespace_override_report, "compatibility_rejected", {"policy": compat_policy, "prior_version": "1.0.0", "overrides": [wrong_namespace_override], "override_approvals": {wrong_namespace_override_approval["owner_approval_digest"]: wrong_namespace_override_approval}, "owner_policy": owner_policy, "owner_set": owner_set, "predicate": predicate}),
    case("deprecation_interval_satisfied", "lifecycle", removal, None, lifecycle_context),
    case("removal_before_interval_rejected", "lifecycle", early_removal, "lifecycle_violation", lifecycle_context),
    case("lifecycle_namespace_drift_rejected", "lifecycle", variant(removal, namespace="other.space"), "lifecycle_violation", lifecycle_context),
    case("lifecycle_prior_head_drift_rejected", "lifecycle", variant(removal, prior_lifecycle_digest=raw("wrong-lifecycle-head")), "lifecycle_violation", lifecycle_context),
    case("tombstone_registry_extra_entry_rejected", "lifecycle", removal, "lifecycle_violation", {**lifecycle_context, "resulting_tombstones": extra_tombstones}),
    case("tombstone_origin_reason_exact_binding", "lifecycle", removal, "lifecycle_violation", {**lifecycle_context, "resulting_tombstones": wrong_tombstone_reason}),
    case("tombstone_registry_must_preserve_every_prior_entry", "lifecycle", removal_after_existing_tombstone, "lifecycle_violation", {**lifecycle_context, "prior_tombstones": prior_tombstones_with_entry, "resulting_tombstones": dropped_prior_entry_registry}),
    case("lifecycle_requires_accepted_current_ledger_heads", "lifecycle", removal, "lifecycle_violation", {**lifecycle_context, "canonical_removal_head": raw("stale-lifecycle-head")}),
    case("lifecycle_referenced_ledger_self_digest_checked", "lifecycle", removal, "digest_mismatch", {**lifecycle_context, "deprecation_ledger": stale_deprecation_ledger}),
    case("tombstoned_identifier_reuse_rejected", "tombstone_reuse", reuse_report, "lifecycle_violation", {"tombstones": resulting_tombstones, "override": None}),
    case("tombstoned_identifier_cannot_return_as_addition", "tombstone_reuse", tombstoned_addition, "lifecycle_violation", {"tombstones": resulting_tombstones, "override": None}),
    case("override_cannot_legalize_identifier_reuse", "tombstone_reuse", reuse_report, "lifecycle_violation", {"tombstones": resulting_tombstones, "override": bad_override})]

stale_tx = variant(publish_tx, expected_prior_revision=0)
fork_tx = variant(publish_tx, expected_prior_head_digest=raw("fork-head"), transaction_id="fork")
version_reuse_tx = copy.deepcopy(publish_tx); version_reuse_tx["coordinate"]["capsule_digest"] = raw("different-capsule"); rehash(version_reuse_tx)
replay_tx = copy.deepcopy(publish_tx)
prepared = variant(publish_journal, state="prepared", linearized=False, recovery_action="discard_staging")
committing = variant(publish_journal, state="committing", linearized=True, recovery_action="complete_commit")
committing_marker = variant(publish_marker, journal_digest=committing["publication_journal_digest"])
withdraw_recovery = variant(withdraw_journal, state="committing", linearized=True, recovery_action="complete_commit")
withdraw_recovery_marker = variant(withdraw_marker, journal_digest=withdraw_recovery["publication_journal_digest"])
revoke_prepared = variant(revoke_journal, state="prepared", linearized=False, recovery_action="discard_staging")
aborted = variant(publish_journal, state="aborted", linearized=False, recovery_action="discard_staging")
bad_publish_reason = variant(publish_tx, status_reason_digest=raw("publish-must-not-have-reason"))
direct_revoke_approval = status_approval("direct_revoke_approval", "publication_revocation", "revoke", d("owner_publication"), "published", revoke_reason, 2, d("owner_publication"))
direct_revoke_tx = variant(revoke_tx, transaction_id="direct-revoke-1.1.0", owner_approval_digest=direct_revoke_approval["owner_approval_digest"], expected_prior_revision=2, expected_prior_head_digest=d("owner_publication"), replay_key_digest=raw("direct-revoke-replay"))
direct_revocation = variant(revoked_publication, from_status="published", prior_status_record_digest=d("owner_publication"), transaction_digest=direct_revoke_tx["publication_transaction_digest"], owner_approval_digest=direct_revoke_approval["owner_approval_digest"], ledger_revision=3)
direct_revoke_journal = variant(revoke_journal, transaction_digest=direct_revoke_tx["publication_transaction_digest"], resulting_record_digest=direct_revocation["publication_status_transition_digest"],
    resulting_ledger_revision=3, resulting_ledger_head_digest=direct_revocation["publication_status_transition_digest"], prior_journal_digest=d("publication_journal"))
direct_revoke_marker = variant(revoke_marker, transaction_digest=direct_revoke_tx["publication_transaction_digest"], journal_digest=direct_revoke_journal["publication_journal_digest"],
    resulting_record_digest=direct_revocation["publication_status_transition_digest"], resulting_ledger_revision=3, resulting_ledger_head_digest=direct_revocation["publication_status_transition_digest"])
wrong_withdraw_action = {**withdraw_approval["action"], "reason_digest": raw("wrong-approved-withdraw-reason")}
wrong_withdraw_action_digest = action_digest(wrong_withdraw_action)
wrong_withdraw_approval = variant(withdraw_approval, action=wrong_withdraw_action, action_digest=wrong_withdraw_action_digest,
    votes=[{**vote, "approved_action_digest": wrong_withdraw_action_digest} for vote in withdraw_approval["votes"]])
wrong_withdraw_tx = variant(withdraw_tx, owner_approval_digest=wrong_withdraw_approval["owner_approval_digest"])
wrong_withdrawal = variant(withdrawal, transaction_digest=wrong_withdraw_tx["publication_transaction_digest"], owner_approval_digest=wrong_withdraw_approval["owner_approval_digest"])
wrong_withdraw_journal = variant(withdraw_journal, transaction_digest=wrong_withdraw_tx["publication_transaction_digest"], resulting_record_digest=wrong_withdrawal["publication_status_transition_digest"], resulting_ledger_head_digest=wrong_withdrawal["publication_status_transition_digest"])
wrong_withdraw_marker = variant(withdraw_marker, transaction_digest=wrong_withdraw_tx["publication_transaction_digest"], journal_digest=wrong_withdraw_journal["publication_journal_digest"], resulting_record_digest=wrong_withdrawal["publication_status_transition_digest"], resulting_ledger_head_digest=wrong_withdrawal["publication_status_transition_digest"])
stale_prior_publication = copy.deepcopy(publication); stale_prior_publication["ledger_revision"] = 1
stale_recovery_result = copy.deepcopy(publication); stale_recovery_result["ledger_revision"] = 1
illegal_transition = variant(withdrawal, from_status="withdrawn", to_status="withdrawn")
bad_transition_link = variant(withdrawal, transaction_digest=raw("wrong-transaction"))
bad_publish_result = variant(publication, transaction_digest=raw("wrong-publish-transaction"))
bad_publish_journal_head = variant(publish_journal, resulting_ledger_head_digest=raw("wrong-resulting-head"))
owner_canonical_decision_context = {"canonical_store_head": ak_store_head, "current_decision_record_digest": owner_decision["decision_record_digest"]}
publish_commit_context = {"transaction": publish_tx, "journal": publish_journal, "marker": publish_marker, "approval": owner_approval, "trust_root": trust_root, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "decision": owner_decision, "expected_action": release_action, "prior_status": prior_publication, "prior_journal_digest": d("prior_publication_journal"), "prior_journal": prior_publish_journal, **owner_canonical_decision_context}
publish_before = {"revision": 1, "head": d("prior_owner_publication"), "status_record_digest": d("prior_owner_publication"), "marker": None, "staging_present": True}
publish_discarded = {"revision": 1, "head": d("prior_owner_publication"), "status_record_digest": d("prior_owner_publication"), "marker": None, "staging_present": False}
publish_completed = {"revision": 2, "head": d("owner_publication"), "status_record_digest": d("owner_publication"), "marker": committing_marker, "staging_present": False}
withdraw_before = {"revision": 2, "head": d("owner_publication"), "status_record_digest": d("owner_publication"), "marker": None, "staging_present": True}
withdraw_completed = {"revision": 3, "head": d("publication_withdrawal"), "status_record_digest": d("publication_withdrawal"), "marker": withdraw_recovery_marker, "staging_present": False}
revoke_before = {"revision": 3, "head": d("publication_withdrawal"), "status_record_digest": d("publication_withdrawal"), "marker": None, "staging_present": True}
revoke_discarded = {"revision": 3, "head": d("publication_withdrawal"), "status_record_digest": d("publication_withdrawal"), "marker": None, "staging_present": False}
cases += [
    case("publication_fresh_cas_accepts", "publication_cas", publish_tx, None, {"current_revision": 1, "current_head": d("prior_owner_publication"), "existing_replay_key": None}),
    case("publish_operation_rejects_status_reason", "publication_cas", bad_publish_reason, "lifecycle_violation", {"current_revision": 1, "current_head": d("prior_owner_publication"), "existing_replay_key": None}),
    case("publication_stale_cas_rejected", "publication_cas", stale_tx, "publication_conflict", {"current_revision": 1, "current_head": d("prior_owner_publication"), "existing_replay_key": None}),
    case("publication_idempotent_replay_returns_existing", "publication_cas", replay_tx, None, {"current_revision": 2, "current_head": d("owner_publication"), "existing_replay_key": publish_tx["replay_key_digest"], "existing_coordinate": coordinate}),
    case("publication_fork_rejected", "publication_cas", fork_tx, "publication_fork", {"current_revision": 1, "current_head": d("prior_owner_publication"), "existing_replay_key": None}),
    case("namespace_version_digest_reuse_conflicts", "version_binding", version_reuse_tx, "version_conflict", {"existing_coordinate": coordinate}),
    case("publication_result_journal_marker_bind_exactly", "publication_commit", publication, None, publish_commit_context),
    case("publication_result_transaction_drift_rejected", "publication_commit", bad_publish_result, "lifecycle_violation", publish_commit_context),
    case("publication_journal_resulting_head_drift_rejected", "publication_commit", publication, "lifecycle_violation", {**publish_commit_context, "journal": bad_publish_journal_head}),
    case("withdrawal_transition_committed", "publication_transition", withdrawal, None, {"transaction": withdraw_tx, "journal": withdraw_journal, "marker": withdraw_marker, "prior_status": publication, "prior_journal_digest": d("publication_journal"), "prior_journal": publish_journal, "approval": withdraw_approval, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "decision": owner_decision, **owner_canonical_decision_context}),
    case("withdrawn_to_revoked_transition_committed", "publication_transition", revoked_publication, None, {"transaction": revoke_tx, "journal": revoke_journal, "marker": revoke_marker, "prior_status": withdrawal, "prior_journal_digest": d("withdraw_journal"), "prior_journal": withdraw_journal, "approval": revoke_approval, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "decision": owner_decision, **owner_canonical_decision_context}),
    case("published_to_revoked_transition_committed", "publication_transition", direct_revocation, None, {"transaction": direct_revoke_tx, "journal": direct_revoke_journal, "marker": direct_revoke_marker, "prior_status": publication, "prior_journal_digest": d("publication_journal"), "prior_journal": publish_journal, "approval": direct_revoke_approval, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "decision": owner_decision, **owner_canonical_decision_context}),
    case("status_transition_link_drift_rejected", "publication_transition", bad_transition_link, "lifecycle_violation", {"transaction": withdraw_tx, "journal": withdraw_journal, "marker": withdraw_marker, "prior_status": publication, "prior_journal_digest": d("publication_journal"), "prior_journal": publish_journal, "approval": withdraw_approval, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "decision": owner_decision, **owner_canonical_decision_context}),
    case("status_transition_fabricated_prior_object_rejected", "publication_transition", withdrawal, "lifecycle_violation", {"transaction": withdraw_tx, "journal": withdraw_journal, "marker": withdraw_marker, "prior_status": variant(publication, status="published", ledger_revision=1), "prior_journal_digest": d("publication_journal"), "prior_journal": publish_journal, "approval": withdraw_approval, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "decision": owner_decision, **owner_canonical_decision_context}),
    case("status_transition_prior_journal_drift_rejected", "publication_transition", withdrawal, "lifecycle_violation", {"transaction": withdraw_tx, "journal": withdraw_journal, "marker": withdraw_marker, "prior_status": publication, "prior_journal_digest": raw("wrong-prior-journal"), "prior_journal": publish_journal, "approval": withdraw_approval, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "decision": owner_decision, **owner_canonical_decision_context}),
    case("withdraw_cannot_reuse_release_approval", "publication_transition", withdrawal, "lifecycle_violation", {"transaction": withdraw_tx, "journal": withdraw_journal, "marker": withdraw_marker, "prior_status": publication, "prior_journal_digest": d("publication_journal"), "prior_journal": publish_journal, "approval": owner_approval, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "decision": owner_decision, **owner_canonical_decision_context}),
    case("revoke_cannot_reuse_release_approval", "publication_transition", revoked_publication, "lifecycle_violation", {"transaction": revoke_tx, "journal": revoke_journal, "marker": revoke_marker, "prior_status": withdrawal, "prior_journal_digest": d("withdraw_journal"), "prior_journal": withdraw_journal, "approval": owner_approval, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "decision": owner_decision, **owner_canonical_decision_context}),
    case("withdraw_approval_binds_exact_operation_reason_and_cas", "publication_transition", wrong_withdrawal, "lifecycle_violation", {"transaction": wrong_withdraw_tx, "journal": wrong_withdraw_journal, "marker": wrong_withdraw_marker, "prior_status": publication, "prior_journal_digest": d("publication_journal"), "prior_journal": publish_journal, "approval": wrong_withdraw_approval, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "decision": owner_decision, **owner_canonical_decision_context}),
    case("publication_prior_status_context_self_digest_checked", "publication_transition", withdrawal, "digest_mismatch", {"transaction": withdraw_tx, "journal": withdraw_journal, "marker": withdraw_marker, "prior_status": stale_prior_publication, "prior_journal_digest": d("publication_journal"), "prior_journal": publish_journal, "approval": withdraw_approval, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "decision": owner_decision, **owner_canonical_decision_context}),
    case("illegal_status_self_transition", "publication_transition", illegal_transition, "lifecycle_violation", {"transaction": withdraw_tx, "journal": withdraw_journal, "marker": withdraw_marker, "prior_status": publication, "prior_journal_digest": d("publication_journal"), "prior_journal": publish_journal, "approval": withdraw_approval, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "decision": owner_decision, **owner_canonical_decision_context}, False),
    case("recovery_before_linearization_discards", "publication_recovery", prepared, None, {"before": publish_before, "after": publish_discarded, "marker": publish_marker, "transaction": publish_tx, "resulting_status": publication}),
    case("recovery_after_linearization_completes", "publication_recovery", committing, None, {"before": publish_before, "after": publish_completed, "marker": committing_marker, "transaction": publish_tx, "resulting_status": publication}),
    case("withdrawal_recovery_after_linearization_completes", "publication_recovery", withdraw_recovery, None, {"before": withdraw_before, "after": withdraw_completed, "marker": withdraw_recovery_marker, "transaction": withdraw_tx, "resulting_status": withdrawal}),
    case("revocation_recovery_before_linearization_discards", "publication_recovery", revoke_prepared, None, {"before": revoke_before, "after": revoke_discarded, "marker": revoke_marker, "transaction": revoke_tx, "resulting_status": revoked_publication}),
    case("aborted_transaction_discards_staging", "publication_recovery", aborted, None, {"before": publish_before, "after": publish_discarded, "marker": publish_marker, "transaction": publish_tx, "resulting_status": publication}),
    case("recovery_before_linearization_must_not_move_head", "publication_recovery", prepared, "recovery_needed", {"before": publish_before, "after": publish_completed, "marker": committing_marker, "transaction": publish_tx, "resulting_status": publication}),
    case("recovery_after_linearization_requires_marker", "publication_recovery", committing, "recovery_needed", {"before": publish_before, "after": {**publish_completed, "marker": None}, "marker": committing_marker, "transaction": publish_tx, "resulting_status": publication}),
    case("recovery_marker_must_match_exact_journal_and_result", "publication_recovery", committing, "recovery_needed", {"before": publish_before, "after": {**publish_completed, "marker": withdraw_marker}, "marker": withdraw_marker, "transaction": publish_tx, "resulting_status": publication}),
    case("recovery_status_record_must_match_result", "publication_recovery", committing, "recovery_needed", {"before": publish_before, "after": {**publish_completed, "status_record_digest": raw("wrong-recovered-status")}, "marker": committing_marker, "transaction": publish_tx, "resulting_status": publication}),
    case("recovery_resolves_complete_resulting_status_object", "publication_recovery", committing, "recovery_needed", {"before": publish_before, "after": publish_completed, "marker": committing_marker, "transaction": publish_tx, "resulting_status": major_publication}),
    case("recovery_result_context_self_digest_checked", "publication_recovery", committing, "digest_mismatch", {"before": publish_before, "after": publish_completed, "marker": committing_marker, "transaction": publish_tx, "resulting_status": stale_recovery_result}),
    case("committed_without_linearization_rejected", "publication_recovery", variant(publish_journal, linearized=False), "recovery_needed")]

projection_context = {"projection": projection, "capsule": capsule, "archive_linkage": archive_link, "payload_manifest": payload, "consumer_manifest": consumer_manifest, "archive_manifest": archive_manifest}
bad_projection = variant(materialization, expected_consumer_manifest_digest=raw("other-consumer-tree"))
bad_archive = variant(materialization, capsule_archive_linkage_digest=raw("other-archive"))
duplicate_destination_projection = variant(projection, entries=[projection["entries"][0], {**projection["entries"][1], "consumer_path": "index.json"}, projection["entries"][2]])
duplicate_destination_capsule = variant(capsule, payload_projection_digest=duplicate_destination_projection["payload_projection_digest"])
duplicate_destination_receipt = variant(materialization, payload_projection_digest=duplicate_destination_projection["payload_projection_digest"])
duplicate_destination_context = {**projection_context, "projection": duplicate_destination_projection, "capsule": duplicate_destination_capsule}
duplicate_source_projection = variant(projection, entries=[projection["entries"][0], {**projection["entries"][1], "capsule_path": "payload/index.json"}, projection["entries"][2]])
duplicate_source_capsule = variant(capsule, payload_projection_digest=duplicate_source_projection["payload_projection_digest"])
duplicate_source_receipt = variant(materialization, payload_projection_digest=duplicate_source_projection["payload_projection_digest"])
duplicate_source_context = {**projection_context, "projection": duplicate_source_projection, "capsule": duplicate_source_capsule}
cyclic_metadata = {**capsule_metadata, "capsule_digest": d("capsule")}
cyclic_metadata_bytes = jcs(cyclic_metadata).encode(); cyclic_metadata_content = domain_digest("semantic-release.raw-blob.v0", cyclic_metadata_bytes)
cyclic_archive_manifest = variant(archive_manifest, entries=[{**archive_manifest["entries"][0], "byte_length": len(cyclic_metadata_bytes), "content_digest": cyclic_metadata_content}, *archive_manifest["entries"][1:]])
cyclic_archive_link = variant(archive_link, archive_manifest_digest=cyclic_archive_manifest["material_manifest_digest"], capsule_metadata=cyclic_metadata, capsule_metadata_content_digest=cyclic_metadata_content)
cyclic_capsule = variant(capsule, capsule_archive_linkage_digest=cyclic_archive_link["capsule_archive_linkage_digest"])
cyclic_receipt = variant(materialization, capsule_archive_linkage_digest=cyclic_archive_link["capsule_archive_linkage_digest"])
cyclic_context = {**projection_context, "capsule": cyclic_capsule, "archive_linkage": cyclic_archive_link, "archive_manifest": cyclic_archive_manifest}
extra_archive_manifest = variant(archive_manifest, entries=archive_manifest["entries"] + [{"path": "surplus.txt", "kind": "file", "mode": 420, "byte_length": 1, "content_digest": raw("surplus") }])
extra_archive_link = variant(archive_link, archive_manifest_digest=extra_archive_manifest["material_manifest_digest"])
extra_archive_capsule = variant(capsule, capsule_archive_linkage_digest=extra_archive_link["capsule_archive_linkage_digest"])
extra_archive_receipt = variant(materialization, capsule_archive_linkage_digest=extra_archive_link["capsule_archive_linkage_digest"])
extra_archive_context = {**projection_context, "capsule": extra_archive_capsule, "archive_linkage": extra_archive_link, "archive_manifest": extra_archive_manifest}
root_as_file_entries = [{"path": "payload", "kind": "file", "mode": 420, "byte_length": 0, "content_digest": raw("payload-root-not-directory")} if x["path"] == "payload" else x for x in archive_manifest["entries"]]
root_as_file_archive_manifest = variant(archive_manifest, entries=root_as_file_entries)
root_as_file_archive_link = variant(archive_link, archive_manifest_digest=root_as_file_archive_manifest["material_manifest_digest"])
root_as_file_capsule = variant(capsule, capsule_archive_linkage_digest=root_as_file_archive_link["capsule_archive_linkage_digest"])
root_as_file_receipt = variant(materialization, capsule_archive_linkage_digest=root_as_file_archive_link["capsule_archive_linkage_digest"])
root_as_file_context = {**projection_context, "archive_manifest": root_as_file_archive_manifest, "archive_linkage": root_as_file_archive_link, "capsule": root_as_file_capsule}
utf16_manifest_order = variant(source, entries=[
    {"path": "𐀀", "kind": "file", "mode": 420, "byte_length": 1, "content_digest": raw("astral")},
    {"path": "", "kind": "file", "mode": 420, "byte_length": 1, "content_digest": raw("bmp-private") }])
cases += [
    case("exact_payload_projection_accepts", "projection", materialization, None, projection_context),
    case("consumer_tree_outside_projection_rejected", "projection", bad_projection, "projection_mismatch", projection_context),
    case("capsule_archive_link_drift_rejected", "projection", bad_archive, "projection_mismatch", projection_context),
    case("duplicate_projection_destination_rejected", "projection", duplicate_destination_receipt, "malformed_input", duplicate_destination_context),
    case("duplicate_projection_source_rejected", "projection", duplicate_source_receipt, "malformed_input", duplicate_source_context),
    case("capsule_archive_identity_cycle_rejected", "projection", cyclic_receipt, "malformed_input", cyclic_context),
    case("capsule_archive_extra_entry_rejected", "projection", extra_archive_receipt, "projection_mismatch", extra_archive_context),
    case("archive_payload_root_must_be_exact_directory_entry", "projection", root_as_file_receipt, "projection_mismatch", root_as_file_context),
    case("manifest_order_is_utf8_not_utf16", "pi_variant", utf16_manifest_order, "malformed_input")]

runtime_missing = copy.deepcopy(runtime_request); del runtime_missing["target"]["runtime_revalidation_receipt_digest"]; rehash(runtime_missing)
bad_disable_receipt = variant(disable_receipt, active_state_after={"enabled": True, "coordinate": coordinate, "runtime_identity": rocs_tool})
bad_partial = variant(partial_receipt, stages=[{"stage": "semantic", "result": "completed", "error_digest": None}, {"stage": "runtime", "result": "completed", "error_digest": None}], failure_stage=None, error_digest=None)
bad_failed_history = variant(failed_receipt, history_head_after={"kind": "rollback", "digest": raw("changed-history")})
combined_success_after = {"enabled": True, "coordinate": predecessor, "runtime_identity": old_runtime}
combined_success_stages = [{"stage": "semantic", "result": "completed", "error_digest": None}, {"stage": "runtime", "result": "completed", "error_digest": None}]
combined_success_history = history("combined_success_history", combined_request, "rolled_back", combined_success_after, combined_success_stages, None, None, d("activation_receipt"))
combined_success = variant(partial_receipt, result="rolled_back", active_state_after=combined_success_after,
    runtime_revalidation_receipt_digest=runtime_target["runtime_revalidation_receipt_digest"], stages=combined_success_stages, failure_stage=None,
    history_head_after={"kind": "rollback", "digest": d("combined_success_history")}, error_digest=None, supersedes_activation_receipt_digest=d("activation_receipt"))
bad_request_digest = variant(semantic_receipt, rollback_request_digest=raw("wrong-request"))
bad_before = variant(semantic_receipt, active_state_before={"enabled": True, "coordinate": predecessor, "runtime_identity": rocs_tool})
bad_result_target = variant(disable_receipt, result="rolled_back", history_head_after={"kind": "rollback", "digest": raw("wrong-result-head")})
bad_stage_order = variant(partial_receipt, stages=list(reversed(partial_receipt["stages"])))
bad_completed_error = variant(semantic_receipt, stages=[{"stage": "semantic", "result": "completed", "error_digest": raw("must-be-null")}])
bad_disable_runtime = variant(disable_receipt, active_state_after={"enabled": False, "coordinate": None, "runtime_identity": old_runtime})
bad_runtime_proof = variant(runtime_receipt, runtime_revalidation_receipt_digest=raw("wrong-revalidation"))
bad_partial_supersession = variant(partial_receipt, supersedes_activation_receipt_digest=d("activation_receipt"))
bad_failed_stage = variant(failed_receipt, stages=[{"stage": "semantic", "result": "not_started", "error_digest": None}], failure_stage=None, error_digest=None)
bad_failed_state = variant(failed_receipt, active_state_after={"enabled": True, "coordinate": predecessor, "runtime_identity": rocs_tool})
bad_rollback_pi_link = variant(semantic_receipt, pi_delivery_receipt_digest=raw("wrong-pi-link"))
bad_request_from_state = variant(semantic_request, from_state={"enabled": True, "coordinate": predecessor, "runtime_identity": rocs_tool})
bad_request_from_state_receipt = variant(semantic_receipt, rollback_request_digest=bad_request_from_state["rollback_request_digest"], active_state_before=bad_request_from_state["from_state"])
fabricated_before_head = variant(semantic_receipt, history_head_before={"kind": "activation", "digest": raw("fabricated-before-head")})
failed_then_completed = variant(partial_receipt, stages=[{"stage": "semantic", "result": "failed", "error_digest": raw("first-stage-failed")}, {"stage": "runtime", "result": "completed", "error_digest": None}],
    failure_stage="semantic", error_digest=raw("first-stage-failed"), active_state_after={"enabled": True, "coordinate": coordinate, "runtime_identity": old_runtime})
bad_failure_cause = variant(partial_receipt, error_digest=raw("unrelated-overall-error"))
wrong_issuer_failed = variant(failed_receipt, issuer={"kind": "rocs", "id": "rocs-cli"})
substituted_activation = variant(activation, activation_epoch=89)
wrong_semantic_available_artifact = variant(semantic_available_artifact, coordinate=coordinate)
stale_semantic_available_artifact = copy.deepcopy(semantic_available_artifact); stale_semantic_available_artifact["coordinate"] = coordinate
wrong_recovery_available_artifact = variant(recovery_available_artifact, runtime_identity=old_runtime)
technical_context = {"semantic_artifact": semantic_available_artifact, "runtime_artifact": runtime_available_artifact, "disable_artifact": disable_available_artifact,
    "recovery_artifact": recovery_available_artifact, "semantic_materialization_technical": rollback_materialization,
    "runtime_materialization_technical": runtime_materialization, "runtime_revalidation_technical": runtime_revalidation,
    "disable_contract_technical": disable_contract_receipt, "disable_rehearsal_technical": disable_rehearsal,
    "recovery_rehearsal_technical": recovery_rehearsal, "recovery_health_technical": recovery_health}
rollback_common = {"activation": activation, "decision": consumer_decision, "intent": intent, "acceptance": acceptance, "materialization": materialization, "current_activation_digest": d("activation_receipt"), "current_activation_revision": 1,
    "canonical_history_head": activation_head, **technical_context, **canonical_decision_context}
def rollback_context(request: dict, proof: dict, history_after: dict | None = None, **extra: object) -> dict:
    kind = request["target"]["kind"]
    artifacts = {"semantic_artifact": semantic_available_artifact, "runtime_artifact": runtime_available_artifact,
        "disable_artifact": disable_available_artifact, "recovery_artifact": recovery_available_artifact}
    return {**rollback_common, "request": request, "availability": proof, "activation_availability": semantic_availability, "history_after": history_after, **artifacts, **extra}
semantic_rollback_context = rollback_context(semantic_request, semantic_availability, semantic_history, ak_linkage=ak_link, pi_receipt=pi_delivered)
cases += [
    case("semantic_rollback_retains_runtime", "rollback", semantic_receipt, None, semantic_rollback_context),
    case("runtime_rollback_retains_semantic_and_revalidates", "rollback", runtime_receipt, None, rollback_context(runtime_request, runtime_availability, runtime_history)),
    case("runtime_rollback_without_revalidation_rejected", "rollback", runtime_missing, "rollback_unavailable", {"request": runtime_missing}, False),
    case("no_prior_disable_clears_semantic", "rollback", disable_receipt, None, rollback_context(disable_request, disable_availability, disable_history)),
    case("disable_that_leaves_semantic_active_rejected", "rollback", bad_disable_receipt, "history_conflict", rollback_context(disable_request, disable_availability, disable_history)),
    case("combined_partial_failure_records_stages", "rollback", partial_receipt, None, rollback_context(combined_request, combined_availability, partial_history)),
    case("combined_full_success_records_order_and_revalidation", "rollback", combined_success, None, rollback_context(combined_request, combined_availability, combined_success_history)),
    case("partial_failure_without_failed_stage_rejected", "rollback", bad_partial, "history_conflict", rollback_context(combined_request, combined_availability, partial_history)),
    case("rollback_optional_ak_pi_crosslinks_exact", "rollback", bad_rollback_pi_link, "history_conflict", semantic_rollback_context),
    case("rollback_request_digest_drift_rejected", "rollback", bad_request_digest, "history_conflict", rollback_context(semantic_request, semantic_availability, semantic_history)),
    case("rollback_request_from_activation_drift_rejected", "rollback", bad_request_from_state_receipt, "rollback_unavailable", rollback_context(bad_request_from_state, semantic_availability, semantic_history)),
    case("rollback_from_state_drift_rejected", "rollback", bad_before, "history_conflict", rollback_context(semantic_request, semantic_availability, semantic_history)),
    case("rollback_result_target_mismatch_rejected", "rollback", bad_result_target, "history_conflict", rollback_context(disable_request, disable_availability, disable_history)),
    case("combined_stage_order_drift_rejected", "rollback", bad_stage_order, "history_conflict", rollback_context(combined_request, combined_availability, partial_history)),
    case("completed_stage_error_rejected", "rollback", bad_completed_error, "history_conflict", rollback_context(semantic_request, semantic_availability, semantic_history)),
    case("disable_must_retain_runtime", "rollback", bad_disable_runtime, "history_conflict", rollback_context(disable_request, disable_availability, disable_history)),
    case("runtime_revalidation_binding_drift_rejected", "rollback", bad_runtime_proof, "rollback_unavailable", rollback_context(runtime_request, runtime_availability, runtime_history)),
    case("partial_failure_must_not_supersede_activation", "rollback", bad_partial_supersession, "history_conflict", rollback_context(combined_request, combined_availability, partial_history)),
    case("failed_rollback_preserves_state_and_typed_head", "rollback", failed_receipt, None, rollback_context(semantic_request, semantic_availability)),
    case("failed_rollback_requires_failed_stage", "rollback", bad_failed_stage, "history_conflict", rollback_context(semantic_request, semantic_availability)),
    case("failed_rollback_changed_state_rejected", "rollback", bad_failed_state, "history_conflict", rollback_context(semantic_request, semantic_availability)),
    case("failed_rollback_changed_history_rejected", "rollback", bad_failed_history, "history_conflict", rollback_context(semantic_request, semantic_availability)),
    case("rollback_requires_canonical_current_activation_object", "rollback", semantic_receipt, "rollback_unavailable", {**semantic_rollback_context, "activation": substituted_activation}),
    case("rollback_requires_concrete_target_and_recovery_availability", "rollback", semantic_receipt, "rollback_unavailable", rollback_context(semantic_request, semantic_availability, semantic_history, semantic_artifact=wrong_semantic_available_artifact)),
    case("rollback_target_artifact_self_digest_checked", "rollback", semantic_receipt, "digest_mismatch", rollback_context(semantic_request, semantic_availability, semantic_history, semantic_artifact=stale_semantic_available_artifact)),
    case("rollback_recovery_artifact_resolved_exactly", "rollback", semantic_receipt, "rollback_unavailable", rollback_context(semantic_request, semantic_availability, semantic_history, recovery_artifact=wrong_recovery_available_artifact)),
    case("rollback_before_head_must_equal_canonical_head", "rollback", fabricated_before_head, "history_conflict", rollback_context(semantic_request, semantic_availability, semantic_history)),
    case("rollback_cannot_complete_stage_after_failure", "rollback", failed_then_completed, "history_conflict", rollback_context(combined_request, combined_availability, partial_history)),
    case("rollback_error_must_equal_failed_stage_cause", "rollback", bad_failure_cause, "history_conflict", rollback_context(combined_request, combined_availability, partial_history)),
    case("rollback_history_head_must_bind_typed_transition", "rollback", semantic_receipt, "history_conflict", rollback_context(semantic_request, semantic_availability, runtime_history)),
    case("issuer_scope_checked_before_subject_rule", "rollback", wrong_issuer_failed, "issuer_scope_violation", rollback_context(semantic_request, semantic_availability))]

revoked_activation = variant(activation, revoked_by_digest=raw("activation-revocation"))
superseded_activation = variant(activation, superseded_by_activation_receipt_digest=raw("new-activation"))
bad_generation_coordinate = variant(generation, coordinate=predecessor)
bad_generation_runtime = variant(generation, runtime_identity=old_runtime)
activation_context = {"activation": activation, "intent": intent, "acceptance": acceptance, "materialization": materialization, "decision": consumer_decision,
    "current_activation_digest": d("activation_receipt"), "current_activation_revision": 1, "availability": semantic_availability, **technical_context, **canonical_decision_context}
cases += [
    case("generation_from_current_activation_accepts", "generation_activation", generation, None, activation_context),
    case("generation_coordinate_must_equal_activation", "generation_activation", bad_generation_coordinate, "activation_not_current", activation_context),
    case("generation_runtime_must_equal_activation", "generation_activation", bad_generation_runtime, "activation_not_current", activation_context),
    case("generation_from_revoked_activation_rejected", "generation_activation", generation, "activation_not_current", {**activation_context, "activation": revoked_activation}),
    case("generation_from_superseded_activation_rejected", "generation_activation", generation, "activation_not_current", {**activation_context, "activation": superseded_activation, "current_activation_digest": raw("new-activation"), "current_activation_revision": 2}),
    case("generation_from_nonhead_activation_rejected", "generation_activation", generation, "activation_not_current", {**activation_context, "current_activation_digest": raw("different-activation"), "current_activation_revision": 2}),
    case("generation_supplied_activation_must_equal_current_pointer", "generation_activation", generation, "activation_not_current", {**activation_context, "activation": substituted_activation})]

bool_satisfies_true_const = variant(source, clean_committed=1)
bool_satisfies_integer_type = variant(owner_set, owner_set_revision=True)
large_prior_semver = "90071992547409929007199254740992.0.0"
large_candidate_semver = "90071992547409929007199254740993.0.0"
large_semver_report = variant(major_report, candidate_version=large_candidate_semver)
digest_bad = copy.deepcopy(capsule); digest_bad["capsule_digest"] = raw("intentionally-wrong-digest")
invalid_date = variant(audit, recorded_at="2026-02-30T12:00:00Z")
rejected_decision = variant(consumer_decision, lifecycle_state="rejected")
revoked_decision = variant(consumer_decision, lifecycle_state="revoked", revocation_digest=raw("decision-revocation"))
superseded_decision = variant(consumer_decision, lifecycle_state="superseded")
bad_acceptance_scope = variant(acceptance, governing_scope_digest=raw("other-scope"))
self_acceptance = variant(acceptance, acceptance_authority={"kind": "rocs", "id": "rocs-cli"})
bad_activation_binding = variant(activation, stop_conditions_digest=raw("other-stop"))
stale_acceptance_context = copy.deepcopy(acceptance); stale_acceptance_context["acceptance_revision"] = 3
expired_intent_acceptance = variant(acceptance, valid_through_intent_revision=3)
low_epoch_acceptance = variant(acceptance, activation_epoch_not_after=80)
wrong_scope_acceptance = variant(acceptance, accepted_posture="materialize_only")
drifting_materialization = variant(materialization, coordinate=predecessor)
wrong_issuer_materialization = variant(materialization, issuer={"kind": "consumer_owner", "id": "consumer-owner"})
stale_store_decision = variant(consumer_decision, ak_store_head={**ak_store_head, "store_revision": 41, "store_head_digest": raw("ak-store-head-41")})
stale_revocation_locator = variant(consumer_decision, ak_store_head={**ak_store_head, "revocation_head_digest": raw("ak-revocation-head-6")})
year_zero = variant(audit, recorded_at="0000-01-01T00:00:00Z")
year_9999 = variant(audit, recorded_at="9999-12-31T23:59:59Z")
pi_delivered_missing = copy.deepcopy(pi_delivered); del pi_delivered_missing["prompt_run_digest"]; rehash(pi_delivered_missing)
pi_suppressed_leak = copy.deepcopy(pi_suppressed); pi_suppressed_leak["prompt_run_digest"] = raw("must-not-exist"); rehash(pi_suppressed_leak)
pi_failed_missing = copy.deepcopy(pi_failed); del pi_failed_missing["error_digest"]; rehash(pi_failed_missing)
authorized_coordination_contract = variant(ak_coordination_contract, authorizes_execution=True, contract_status="created")
conflated_consumer_contract = variant(consumer_canary_contract, task_contract_id=ak_coordination_contract["task_contract_id"], rollback_owner=ak_coordination_contract["rollback_owner"])
missing_consumer_path_contract = variant(consumer_canary_contract, allowed_paths=consumer_canary_contract["allowed_paths"][:-1])
substituted_task_id_contract = variant(consumer_canary_contract, task_id="candidate-other-consumer-task")
substituted_owner_contract = variant(consumer_canary_contract, task_owner_id="other-owner")
substituted_rollback_owner_contract = variant(consumer_canary_contract, rollback_owner={"kind": "consumer_owner", "id": "other-owner"})
substituted_evidence_contract = variant(consumer_canary_contract, required_evidence=consumer_canary_contract["required_evidence"][:-1])
substituted_stop_contract = variant(consumer_canary_contract, stop_conditions=consumer_canary_contract["stop_conditions"][:-1])
substituted_dependency_contract = variant(consumer_canary_contract, dependencies=consumer_canary_contract["dependencies"][:-1])
substituted_prerequisite_id_contract = variant(consumer_canary_contract, prerequisites=consumer_canary_contract["prerequisites"][:-1])
substituted_prerequisite_digest_contract = copy.deepcopy(consumer_canary_contract); substituted_prerequisite_digest_contract["prerequisites"][0]["artifact_digest"] = raw("synthetic-future-artifact"); rehash(substituted_prerequisite_digest_contract)
wrong_prerequisite_state_contract = copy.deepcopy(consumer_canary_contract); wrong_prerequisite_state_contract["prerequisites"][0]["required_state"] = "completed_current"; rehash(wrong_prerequisite_state_contract)
wrong_stop_semantic_contract = copy.deepcopy(consumer_canary_contract); wrong_stop_semantic_contract["stop_conditions"][0]["condition_kind"] = "validator_failure"; rehash(wrong_stop_semantic_contract)
cases += [
    case("non_authorizing_separate_coordination_and_consumer_contracts", "governance_contracts", ak_coordination_contract, None, {"consumer_contract": consumer_canary_contract}),
    case("ak_coordination_contract_cannot_authorize_execution", "governance_contracts", authorized_coordination_contract, "self_certification", {"consumer_contract": consumer_canary_contract}),
    case("coordination_and_consumer_tasks_cannot_be_conflated", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": conflated_consumer_contract}),
    case("first_consumer_allowed_paths_are_exact", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": missing_consumer_path_contract}),
    case("task_contract_binds_exact_task_id", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": substituted_task_id_contract}),
    case("task_contract_binds_exact_owner_id", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": substituted_owner_contract}),
    case("task_contract_binds_exact_rollback_owner_id", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": substituted_rollback_owner_contract}),
    case("task_contract_binds_exact_evidence_list", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": substituted_evidence_contract}),
    case("task_contract_binds_exact_stop_conditions", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": substituted_stop_contract}),
    case("task_contract_binds_exact_dependency_ids", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": substituted_dependency_contract}),
    case("task_contract_binds_exact_prerequisite_ids", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": substituted_prerequisite_id_contract}),
    case("task_contract_rejects_synthetic_future_artifact_digest", "governance_contracts", ak_coordination_contract, "malformed_input", {"consumer_contract": substituted_prerequisite_digest_contract}),
    case("task_contract_binds_required_reference_state", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": wrong_prerequisite_state_contract}),
    case("task_contract_machine_binds_stop_semantics", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": wrong_stop_semantic_contract}),
    case("python_integer_cannot_satisfy_boolean_const", "pi_variant", bool_satisfies_true_const, "malformed_input", schema_valid=False),
    case("python_boolean_cannot_satisfy_integer_type", "pi_variant", bool_satisfies_integer_type, "malformed_input", schema_valid=False),
    case("arbitrary_length_semver_compares_without_number_precision_loss", "compatibility", large_semver_report, None, {"policy": compat_policy, "prior_version": large_prior_semver}),
    case("embedded_digest_mismatch_is_deterministic", "digest", digest_bad, "digest_mismatch"),
    case("calendar_valid_utc_accepts", "utc", audit, None),
    case("calendar_invalid_utc_rejected", "utc", invalid_date, "malformed_input"),
    case("calendar_year_zero_rejected", "utc", year_zero, "malformed_input"),
    case("calendar_year_9999_accepts", "utc", year_9999, None),
    case("canonical_accepted_ak_decision_accepts", "ak_decision", consumer_decision, None, canonical_decision_context),
    case("ak_store_head_stale_rejected", "ak_decision", stale_store_decision, "self_certification", canonical_decision_context),
    case("ak_revocation_locator_stale_rejected", "ak_decision", stale_revocation_locator, "self_certification", canonical_decision_context),
    case("rejected_ak_decision_fails_closed", "ak_decision", rejected_decision, "self_certification", canonical_decision_context),
    case("revoked_ak_decision_fails_closed", "ak_decision", revoked_decision, "self_certification", canonical_decision_context),
    case("superseded_ak_decision_fails_closed", "ak_decision", superseded_decision, "self_certification", canonical_decision_context),
    case("acceptance_owner_scope_binding_exact", "acceptance_binding", acceptance, None, {"decision": consumer_decision, "intent": intent, **canonical_decision_context}),
    case("acceptance_scope_drift_rejected", "acceptance_binding", bad_acceptance_scope, "self_certification", {"decision": consumer_decision, "intent": intent, **canonical_decision_context}),
    case("rocs_cannot_self_certify_acceptance", "acceptance_binding", self_acceptance, "issuer_scope_violation", {"decision": consumer_decision, "intent": intent, **canonical_decision_context}),
    case("activation_decision_bindings_exact", "activation_binding", activation, None, {"decision": consumer_decision, "intent": intent, "acceptance": acceptance, "materialization": materialization, "availability": semantic_availability, **technical_context, **canonical_decision_context}),
    case("activation_stop_binding_drift_rejected", "activation_binding", bad_activation_binding, "self_certification", {"decision": consumer_decision, "intent": intent, "acceptance": acceptance, "materialization": materialization, "availability": semantic_availability, **technical_context, **canonical_decision_context}),
    case("activation_resolves_acceptance_self_digest", "activation_binding", activation, "digest_mismatch", {"decision": consumer_decision, "intent": intent, "acceptance": stale_acceptance_context, "materialization": materialization, "availability": semantic_availability, **technical_context, **canonical_decision_context}),
    case("activation_requires_valid_intent_revision", "activation_binding", activation, "self_certification", {"decision": consumer_decision, "intent": intent, "acceptance": expired_intent_acceptance, "materialization": materialization, "availability": semantic_availability, **technical_context, **canonical_decision_context}),
    case("activation_epoch_respects_acceptance_ceiling", "activation_binding", activation, "self_certification", {"decision": consumer_decision, "intent": intent, "acceptance": low_epoch_acceptance, "materialization": materialization, "availability": semantic_availability, **technical_context, **canonical_decision_context}),
    case("activation_scope_matches_intent_and_acceptance", "activation_binding", activation, "self_certification", {"decision": consumer_decision, "intent": intent, "acceptance": wrong_scope_acceptance, "materialization": materialization, "availability": semantic_availability, **technical_context, **canonical_decision_context}),
    case("activation_materialization_coordinate_runtime_chain_exact", "activation_binding", activation, "self_certification", {"decision": consumer_decision, "intent": intent, "acceptance": acceptance, "materialization": drifting_materialization, "availability": semantic_availability, **technical_context, **canonical_decision_context}),
    case("activation_context_issuer_checked_before_relation", "activation_binding", activation, "issuer_scope_violation", {"decision": consumer_decision, "intent": intent, "acceptance": acceptance, "materialization": wrong_issuer_materialization, "availability": semantic_availability, **technical_context, **canonical_decision_context}),
    case("activation_requires_current_decision_record", "activation_binding", activation, "self_certification", {"decision": stale_store_decision, "intent": intent, "acceptance": acceptance, "materialization": materialization, "availability": semantic_availability, **technical_context, **canonical_decision_context}),
    case("pi_delivered_variant_accepts", "pi_variant", pi_delivered, None),
    case("pi_suppressed_variant_accepts", "pi_variant", pi_suppressed, None),
    case("pi_failed_variant_accepts", "pi_variant", pi_failed, None),
    case("delivered_without_prompt_run_rejected", "pi_variant", pi_delivered_missing, "malformed_input", schema_valid=False),
    case("suppressed_cannot_claim_prompt_delivery", "pi_variant", pi_suppressed_leak, "malformed_input", schema_valid=False),
    case("failed_without_error_rejected", "pi_variant", pi_failed_missing, "malformed_input", schema_valid=False),
    case("ak_generation_only_linkage_accepts_without_pi", "ak_optional_pi", ak_generation_only, None),
    case("ak_delivered_linkage_requires_pi_digest", "ak_optional_pi", ak_link, None)]

# Revision-v6 adversarial closure: one direct negative for every revision-v5 false accept/finding.
def publication_chain_for(approval_value: dict, decision_value: dict, expected_action: dict) -> tuple[dict, dict]:
    tx = variant(publish_tx, owner_approval_digest=approval_value["owner_approval_digest"])
    pub = variant(publication, transaction_digest=tx["publication_transaction_digest"], owner_approval_digest=approval_value["owner_approval_digest"])
    journal = variant(publish_journal, transaction_digest=tx["publication_transaction_digest"], resulting_record_digest=pub["owner_publication_digest"], resulting_ledger_head_digest=pub["owner_publication_digest"])
    marker = variant(publish_marker, transaction_digest=tx["publication_transaction_digest"], journal_digest=journal["publication_journal_digest"], resulting_record_digest=pub["owner_publication_digest"], resulting_ledger_head_digest=pub["owner_publication_digest"])
    context = {**publish_commit_context, "transaction": tx, "journal": journal, "marker": marker, "approval": approval_value, "decision": decision_value,
        "expected_action": expected_action, "current_decision_record_digest": decision_value["decision_record_digest"]}
    return pub, context
threshold_approval = variant(owner_approval, votes=owner_approval["votes"][:1])
threshold_pub, threshold_pub_context = publication_chain_for(threshold_approval, owner_decision, release_action)
wrong_release_action = {**release_action, "compatibility_report_digest": raw("wrong-release-report")}
wrong_release_action_digest = action_digest(wrong_release_action)
wrong_release_approval = variant(owner_approval, action=wrong_release_action, action_digest=wrong_release_action_digest,
    votes=[{**v, "approved_action_digest": wrong_release_action_digest} for v in owner_approval["votes"]])
wrong_action_pub, wrong_action_pub_context = publication_chain_for(wrong_release_approval, owner_decision, release_action)
rejected_owner_decision = variant(owner_decision, lifecycle_state="rejected")
rejected_decision_approval = variant(owner_approval, decision_reference_digest=rejected_owner_decision["ak_decision_reference_digest"])
rejected_decision_pub, rejected_decision_pub_context = publication_chain_for(rejected_decision_approval, rejected_owner_decision, release_action)
withdraw_rejected_decision_context = {"transaction": withdraw_tx, "journal": withdraw_journal, "marker": withdraw_marker, "prior_status": publication,
    "prior_journal_digest": d("publication_journal"), "prior_journal": publish_journal, "approval": withdraw_approval, "policy": owner_policy,
    "owner_set": owner_set, "predicate": predicate, "decision": rejected_owner_decision, "canonical_store_head": ak_store_head,
    "current_decision_record_digest": rejected_owner_decision["decision_record_digest"]}
prior_journal_result_drift = variant(prior_publish_journal, resulting_record_digest=raw("wrong-prior-result"))
recovery_result_transaction_drift = variant(publication, transaction_digest=raw("other-recovery-transaction"))
recovery_transaction_journal = variant(committing, resulting_record_digest=recovery_result_transaction_drift["owner_publication_digest"], resulting_ledger_head_digest=recovery_result_transaction_drift["owner_publication_digest"])
recovery_transaction_marker = variant(committing_marker, journal_digest=recovery_transaction_journal["publication_journal_digest"], resulting_record_digest=recovery_result_transaction_drift["owner_publication_digest"], resulting_ledger_head_digest=recovery_result_transaction_drift["owner_publication_digest"])
recovery_transaction_after = {"revision": 2, "head": recovery_result_transaction_drift["owner_publication_digest"], "status_record_digest": recovery_result_transaction_drift["owner_publication_digest"], "marker": recovery_transaction_marker, "staging_present": False}
self_certified_dep_pub = variant(publication, transaction_digest=raw("self-certified-publication-transaction"))
self_certified_dep_canonical = variant(dep_canonical_ledger, ledger_head_digest=self_certified_dep_pub["owner_publication_digest"], status_record_digest=self_certified_dep_pub["owner_publication_digest"])
self_certified_dep_ledger = variant(deprecation_ledger, ledger_head_digest=self_certified_dep_pub["owner_publication_digest"], publication_status_record_digest=self_certified_dep_pub["owner_publication_digest"], canonical_ledger_digest=self_certified_dep_canonical["publication_ledger_head_digest"])
self_certified_lifecycle_context = {**lifecycle_context, "deprecation_publication": self_certified_dep_pub, "deprecation_ledger": self_certified_dep_ledger,
    "deprecation_canonical_ledger": self_certified_dep_canonical, "canonical_deprecation_head": self_certified_dep_pub["owner_publication_digest"]}
wrong_availability_issuer = variant(semantic_available_artifact, issuer={"kind": "rocs", "id": "rocs-cli"})
wrong_materialization_technical_issuer = variant(rollback_materialization, issuer={"kind": "consumer_owner", "id": "consumer-owner"})
wrong_materialization_technical_id = variant(rollback_materialization, issuer={"kind": "rocs", "id": "other-rocs"})
next_activation = variant(activation, activation_revision=2, prior_activation_revision=1, activation_epoch=91,
    current_activation_head_digest=d("activation_receipt"), previous_activation_receipt_digest=d("activation_receipt"))
next_activation_head_drift = variant(next_activation, current_activation_head_digest=raw("wrong-current-activation-head"))
activation_issuer_id_substitution = variant(activation, consumer_owner_issuer_id="other-consumer-owner")
activation_revision_skip = variant(activation, activation_revision=2)
activation_epoch_before_acceptance = variant(activation, activation_epoch=79)
activation_availability_drift = variant(activation, rollback_availability_proof_digest=d("runtime_rollback_availability"))
malformed_semver_subject = variant(compat_report, candidate_version="1.1.0garbage")
approval_key_drift_context = {**override_context, "override_approvals": {raw("map-key-drift"): override_approval}}
bool_current_revision_context = {"current_revision": True, "current_head": publish_tx["expected_prior_head_digest"], "existing_replay_key": None}
synthetic_resolved_dependency = copy.deepcopy(consumer_canary_contract)
synthetic_resolved_dependency["dependencies"][0] = {**synthetic_resolved_dependency["dependencies"][0], "resolution": "resolved", "ak_store_head": ak_store_head,
    "task_id": "candidate-decision-53-ak-coordination", "task_record_digest": raw("synthetic-future-task"), "artifact_digest": raw("synthetic-future-evidence")}
rehash(synthetic_resolved_dependency)
cases += [
    case("publish_requires_threshold_evaluation", "publication_commit", threshold_pub, "lifecycle_violation", threshold_pub_context),
    case("publish_requires_exact_release_action", "publication_commit", wrong_action_pub, "lifecycle_violation", wrong_action_pub_context),
    case("publish_approval_resolves_canonical_ak_decision", "publication_commit", rejected_decision_pub, "lifecycle_violation", rejected_decision_pub_context),
    case("withdraw_approval_resolves_canonical_ak_decision", "publication_transition", withdrawal, "lifecycle_violation", withdraw_rejected_decision_context),
    case("publication_prior_journal_result_revision_head_bind_prior_status", "publication_commit", publication, "lifecycle_violation", {**publish_commit_context, "prior_journal": prior_journal_result_drift, "prior_journal_digest": prior_journal_result_drift["publication_journal_digest"]}),
    case("recovery_result_transaction_binds_transaction", "publication_recovery", recovery_transaction_journal, "recovery_needed", {"before": publish_before, "after": recovery_transaction_after, "marker": recovery_transaction_marker, "transaction": publish_tx, "resulting_status": recovery_result_transaction_drift}),
    case("lifecycle_endpoint_cannot_self_certify_publication", "lifecycle", removal, "lifecycle_violation", self_certified_lifecycle_context),
    case("rollback_availability_receipt_requires_issuer", "rollback", semantic_receipt, "issuer_scope_violation", rollback_context(semantic_request, semantic_availability, semantic_history, semantic_artifact=wrong_availability_issuer)),
    case("rollback_resolves_typed_materialization_receipt_issuer", "rollback", semantic_receipt, "issuer_scope_violation", rollback_context(semantic_request, semantic_availability, semantic_history, semantic_materialization_technical=wrong_materialization_technical_issuer)),
    case("rollback_binds_technical_receipt_issuer_id", "rollback", semantic_receipt, "rollback_unavailable", rollback_context(semantic_request, semantic_availability, semantic_history, semantic_materialization_technical=wrong_materialization_technical_id)),
    case("activation_prior_plus_one_transition_accepts", "activation_binding", next_activation, None, {**activation_context, "previous_activation": activation}),
    case("activation_current_head_equals_exact_prior", "activation_binding", next_activation_head_drift, "self_certification", {**activation_context, "previous_activation": activation}),
    case("activation_binds_consumer_owner_issuer_id", "activation_binding", activation_issuer_id_substitution, "self_certification", {**activation_context}),
    case("activation_revision_requires_genesis_or_prior_plus_one", "activation_binding", activation_revision_skip, "self_certification", {**activation_context}),
    case("activation_epoch_is_monotonic_from_acceptance", "activation_binding", activation_epoch_before_acceptance, "self_certification", {**activation_context}),
    case("activation_binds_concrete_rollback_availability", "activation_binding", activation_availability_drift, "rollback_unavailable", {**activation_context}),
    case("primitive_context_integer_rejects_boolean", "publication_cas", publish_tx, "malformed_input", bool_current_revision_context),
    case("semver_subject_requires_exact_full_grammar", "pi_variant", malformed_semver_subject, "malformed_input", schema_valid=False),
    case("semver_context_requires_exact_full_grammar", "compatibility", compat_report, "malformed_input", {"policy": compat_policy, "prior_version": "1.0.0junk"}),
    case("approval_map_key_equals_value_digest", "compatibility", overridden_report, "digest_mismatch", approval_key_drift_context),
    case("unresolved_candidate_cannot_claim_synthetic_task_artifacts", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": synthetic_resolved_dependency})]

raw_json_cases = [
    {"name": "raw_duplicate_top_level_key_rejected", "raw_json": "{\"a\":1,\"a\":2}", "expected_error": "malformed_input"},
    {"name": "raw_duplicate_nested_key_rejected", "raw_json": "{\"a\":{\"b\":1,\"b\":2}}", "expected_error": "malformed_input"},
    {"name": "raw_negative_zero_rejected", "raw_json": "{\"n\":-0}", "expected_error": "malformed_input"},
    {"name": "raw_decimal_rejected", "raw_json": "{\"n\":1.0}", "expected_error": "malformed_input"},
    {"name": "raw_exponent_rejected", "raw_json": "{\"n\":1e0}", "expected_error": "malformed_input"},
    {"name": "raw_leading_zero_rejected", "raw_json": "{\"n\":01}", "expected_error": "malformed_input"},
    {"name": "raw_safe_integer_accepts", "raw_json": "{\"n\":9007199254740991}", "expected_error": None},
    {"name": "raw_proto_key_preserved_as_own_property", "raw_json": "{\"__proto__\":{\"polluted\":true}}", "required_own_keys": ["__proto__"], "expected_error": None},
]
differential = {"protocol": "semantic-release-v0", "rfc_revision": "semantic-release-revision-v6", "cases": cases, "raw_json_cases": raw_json_cases}

write_schema()
for path, value in ((ROOT / "golden-fixtures.json", golden), (ROOT / "differential-fixtures.json", differential)):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"wrote schema, {len(records)} golden records, and {len(cases)} differential cases")
