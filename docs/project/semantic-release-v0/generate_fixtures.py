#!/usr/bin/env python3
"""Deterministically regenerate revision-12 owner-receipt authority-graph schema and normative fixtures."""

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
rocs_repo = {"owner": "rocs-owner", "repository_id": "rocs-cli", "canonical_locator": "local://core/rocs-cli", "identity_revision": 4}
pi_repo = {"owner": "pi-owner", "repository_id": "pi-adapter", "canonical_locator": "local://softwareco/pi-adapter", "identity_revision": 1}
canary_repo = {"owner": "consumer-owner", "repository_id": "pi-canary-consumer", "canonical_locator": "local://softwareco/pi-canary-consumer", "identity_revision": 3}
consumer_repo = {"owner": "consumer-owner", "repository_id": "pi-canary-consumer", "canonical_locator": "local://softwareco/pi-canary-consumer", "identity_revision": 3}
canary_scope = {"consumer_repository": copy.deepcopy(consumer_repo), "operator_canary_name": "operator-canary-alpha", "naming_authority": "operator",
    "canary_cardinality": 1, "adoption_mode": "single_operator_named_canary",
    "expansion_authority": "new_protocol_and_decision_required"}
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
    ("removal", "breaking", "major", "deprecation_interval_at_least", False)]
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
external_trust_root_pin = {"namespace": "ai-society.core", "trust_root_id": trust_root["trust_root_id"],
    "trust_root_revision": trust_root["trust_root_revision"], "trust_root_digest": d("trust_root"),
    "owner_policy_digest": d("owner_policy"), "owner_set_digest": d("owner_set"),
    "revocation_revision": 1, "revocation_head_digest": d("trust_revocation") if "trust_revocation" in by_name else None}
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

prior_tombstones = add("tombstone_registry_genesis", {"schema": "semantic-tombstone-registry.v0", "namespace": "ai-society.core",
    "lifecycle_head_digest": raw("lifecycle-head-genesis"), "registry_revision": 1, "entries": [], "prior_registry_digest": None})
tombstones = add("tombstone_registry", {"schema": "semantic-tombstone-registry.v0", "namespace": "ai-society.core",
    "lifecycle_head_digest": raw("lifecycle-head-2"), "registry_revision": 2,
    "entries": [{"semantic_id": "core.Old", "reason": "removed", "origin_record_digest": raw("old-removal-record")}],
    "prior_registry_digest": d("tombstone_registry_genesis")})
tombstone_history = add("tombstone_history_proof", {"schema": "semantic-tombstone-history-proof.v0",
    "issuer": {"kind": "semantic_owner", "id": "semantic-owner"}, "namespace": "ai-society.core",
    "current_lifecycle_head_digest": tombstones["lifecycle_head_digest"],
    "current_registry_digest": d("tombstone_registry"), "current_registry_revision": tombstones["registry_revision"],
    "revisions": [
        {"registry": copy.deepcopy(prior_tombstones), "authorized_delta": {"authorization_kind": "genesis",
            "authorization_record_digest": raw("tombstone-genesis-authorization"), "prior_lifecycle_head_digest": None,
            "resulting_lifecycle_head_digest": prior_tombstones["lifecycle_head_digest"], "added_entries": []}},
        {"registry": copy.deepcopy(tombstones), "authorized_delta": {"authorization_kind": "removal",
            "authorization_record_digest": tombstones["entries"][0]["origin_record_digest"],
            "prior_lifecycle_head_digest": prior_tombstones["lifecycle_head_digest"],
            "resulting_lifecycle_head_digest": tombstones["lifecycle_head_digest"],
            "added_entries": copy.deepcopy(tombstones["entries"])}}]})

capsule = add("capsule", {"schema": "semantic-release-capsule.v0", "namespace": "ai-society.core", "semantic_version": "1.1.0", "source_manifest_digest": d("source_manifest"),
    "semantic_payload_digest": raw("semantic-payload-1.1", "semantic-release.semantic-payload.v0"), "payload_manifest_digest": d("payload_manifest"), "payload_projection_digest": d("payload_projection"),
    "capsule_archive_linkage_digest": d("capsule_archive_linkage"), "compatibility_report_digest": d("compatibility_report"), "owner_policy_digest": d("owner_policy"),
    "compilation_contract_digest": raw("compilation-contract"), "required_protocol_versions": ["semantic-discovery-v0", "semantic-release-v0"], "predecessor_coordinate": predecessor,
    "lifecycle_head_digest": tombstones["lifecycle_head_digest"], "tombstone_registry_digest": d("tombstone_registry"),
    "tombstone_registry_revision": tombstones["registry_revision"]})
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
external_trust_root_pin["revocation_head_digest"] = d("trust_revocation")
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
    "staged_blob_set_digest": raw("prior-publication-blobs"), "linearized": True, "recovery_action": "none", "prior_journal_digest": None,
    "recovery_controller_id": "recovery", "recovery_runtime_identity": recovery_tool, "recovery_epoch": 85})
publish_journal = add("publication_journal", {"schema": "semantic-publication-journal.v0", "transaction_digest": d("publication_transaction"), "state": "committed",
    "resulting_record_digest": d("owner_publication"), "resulting_ledger_revision": 2, "resulting_ledger_head_digest": d("owner_publication"),
    "staged_blob_set_digest": raw("publication-blobs"), "linearized": True, "recovery_action": "none", "prior_journal_digest": d("prior_publication_journal"),
    "recovery_controller_id": "recovery", "recovery_runtime_identity": recovery_tool, "recovery_epoch": 85})
publish_marker = add("publication_commit_marker", {"schema": "semantic-publication-commit-marker.v0", "transaction_digest": d("publication_transaction"), "journal_digest": d("publication_journal"),
    "resulting_record_digest": d("owner_publication"), "resulting_ledger_revision": 2, "resulting_ledger_head_digest": d("owner_publication"), "fsync_complete": True})
publish_recovery_intent = add("publication_recovery_intent_marker", {"schema": "semantic-publication-recovery-intent-marker.v0",
    "issuer": {"kind": "recovery_controller", "id": "recovery"}, "transaction_digest": d("publication_transaction"),
    "journal_digest": d("publication_journal"), "resulting_record_digest": d("owner_publication"),
    "resulting_ledger_revision": 2, "resulting_ledger_head_digest": d("owner_publication"),
    "marker_semantics": "non_durable_intent_only", "fsync_complete": False, "durable_commit_marker_present": False})

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
    "staged_blob_set_digest": raw("withdraw-blobs"), "linearized": True, "recovery_action": "none", "prior_journal_digest": d("publication_journal"),
    "recovery_controller_id": "recovery", "recovery_runtime_identity": recovery_tool, "recovery_epoch": 85})
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
    "staged_blob_set_digest": raw("revoke-blobs"), "linearized": True, "recovery_action": "none", "prior_journal_digest": d("withdraw_journal"),
    "recovery_controller_id": "recovery", "recovery_runtime_identity": recovery_tool, "recovery_epoch": 85})
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
    "staged_blob_set_digest": raw("major-publication-blobs"), "linearized": True, "recovery_action": "none", "prior_journal_digest": d("withdraw_journal"),
    "recovery_controller_id": "recovery", "recovery_runtime_identity": recovery_tool, "recovery_epoch": 85})
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
resulting_entries = copy.deepcopy(tombstones["entries"]) + [
    {"semantic_id": "core.Legacy", "reason": "removed", "origin_record_digest": d("removal_record")}]
resulting_entries.sort(key=lambda row: row["semantic_id"].encode())
resulting_tombstones = add("resulting_tombstone_registry", {"schema": "semantic-tombstone-registry.v0", "namespace": "ai-society.core",
    "lifecycle_head_digest": d("removal_record"), "registry_revision": 3,
    "entries": resulting_entries, "prior_registry_digest": d("tombstone_registry")})
resulting_tombstone_history = add("resulting_tombstone_history_proof", {"schema": "semantic-tombstone-history-proof.v0",
    "issuer": {"kind": "semantic_owner", "id": "semantic-owner"}, "namespace": "ai-society.core",
    "current_lifecycle_head_digest": resulting_tombstones["lifecycle_head_digest"],
    "current_registry_digest": d("resulting_tombstone_registry"),
    "current_registry_revision": resulting_tombstones["registry_revision"],
    "revisions": copy.deepcopy(tombstone_history["revisions"]) + [
        {"registry": copy.deepcopy(resulting_tombstones), "authorized_delta": {"authorization_kind": "removal",
            "authorization_record_digest": d("removal_record"),
            "prior_lifecycle_head_digest": tombstones["lifecycle_head_digest"],
            "resulting_lifecycle_head_digest": resulting_tombstones["lifecycle_head_digest"],
            "added_entries": [{"semantic_id": "core.Legacy", "reason": "removed", "origin_record_digest": d("removal_record")} ]}}]})
projection_lifecycle_tombstone_head = {"namespace": "ai-society.core", "lifecycle_head_digest": tombstones["lifecycle_head_digest"],
    "tombstone_registry_digest": d("tombstone_registry"), "tombstone_registry_revision": tombstones["registry_revision"]}
reuse_lifecycle_tombstone_head = {"namespace": "ai-society.core", "lifecycle_head_digest": d("removal_record"),
    "tombstone_registry_digest": d("resulting_tombstone_registry"), "tombstone_registry_revision": resulting_tombstones["registry_revision"]}

trust_ref = {"trust_root_id": trust_root["trust_root_id"], "trust_root_revision": trust_root["trust_root_revision"], "trust_root_digest": d("trust_root"), "publication_ledger_revision": 2,
             "publication_digest": d("owner_publication"), "local_revocation_revision": 1, "local_revocation_head_digest": d("trust_revocation"),
             "trust_snapshot_digest": raw("semantic-trust-snapshot-1")}
rollback_materialization = add("rollback_target_materialization", {"schema": "semantic-rollback-technical-receipt.v0", "issuer": {"kind": "rocs", "id": "rocs-cli"}, "receipt_kind": "materialization", "subject_digest": predecessor["capsule_digest"], "coordinate": predecessor, "runtime_identity": rocs_tool, "referenced_receipt_digest": None, "outcome": "valid"})
runtime_materialization = add("runtime_target_materialization", {"schema": "semantic-rollback-technical-receipt.v0", "issuer": {"kind": "rocs", "id": "rocs-cli"}, "receipt_kind": "materialization", "subject_digest": old_runtime["distribution_digest"], "coordinate": coordinate, "runtime_identity": old_runtime, "referenced_receipt_digest": None, "outcome": "valid"})
runtime_revalidation = add("runtime_target_revalidation", {"schema": "semantic-rollback-technical-receipt.v0", "issuer": {"kind": "rocs", "id": "rocs-cli"}, "receipt_kind": "runtime_revalidation", "subject_digest": coordinate["capsule_digest"], "coordinate": coordinate, "runtime_identity": old_runtime, "referenced_receipt_digest": d("runtime_target_materialization"), "outcome": "valid"})
disable_contract_receipt = add("disable_contract_receipt", {"schema": "semantic-rollback-technical-receipt.v0", "issuer": {"kind": "consumer_owner", "id": "consumer-owner"}, "receipt_kind": "disable_contract", "subject_digest": consumer_decision["rollback_plan_digest"], "coordinate": None, "runtime_identity": rocs_tool, "referenced_receipt_digest": None, "outcome": "valid"})
disable_rehearsal = add("disable_rehearsal_receipt", {"schema": "semantic-rollback-technical-receipt.v0", "issuer": {"kind": "recovery_controller", "id": "recovery"}, "receipt_kind": "rehearsal", "subject_digest": d("disable_contract_receipt"), "coordinate": None, "runtime_identity": rocs_tool, "referenced_receipt_digest": d("disable_contract_receipt"), "outcome": "valid"})
recovery_rehearsal = add("recovery_rehearsal_receipt", {"schema": "semantic-rollback-technical-receipt.v0", "issuer": {"kind": "recovery_controller", "id": "recovery"}, "receipt_kind": "rehearsal", "subject_digest": recovery_tool["distribution_digest"], "coordinate": None, "runtime_identity": recovery_tool, "referenced_receipt_digest": None, "outcome": "valid"})
recovery_health = add("recovery_health_receipt", {"schema": "semantic-rollback-technical-receipt.v0", "issuer": {"kind": "recovery_controller", "id": "recovery"}, "receipt_kind": "health", "subject_digest": recovery_tool["distribution_digest"], "coordinate": None, "runtime_identity": recovery_tool, "referenced_receipt_digest": d("recovery_rehearsal_receipt"), "outcome": "valid"})

semantic_target = {"kind": "semantic", "semantic_action": "switch", "target_coordinate": predecessor, "runtime_action": "retain", "target_materialization_receipt_digest": d("rollback_target_materialization")}
runtime_target = {"kind": "runtime", "semantic_action": "retain", "runtime_action": "switch", "target_runtime_identity": old_runtime, "target_materialization_receipt_digest": d("runtime_target_materialization"), "runtime_revalidation_receipt_digest": d("runtime_target_revalidation")}
disable_target = {"kind": "no_prior_disable", "semantic_action": "disable", "runtime_action": "retain", "disable_contract_digest": d("disable_contract_receipt"), "rehearsal_receipt_digest": d("disable_rehearsal_receipt")}
combined_target = {"kind": "combined", "semantic_stage": semantic_target, "runtime_stage": runtime_target, "stage_order": "semantic_then_runtime"}
intent = add("consumer_intent", {"schema": "semantic-consumer-intent.v0", "consumer_repository": consumer_repo, "canary_scope": canary_scope, "intent_revision": 4, "desired_coordinate": coordinate, "runtime_identity": rocs_tool,
    "accepted_compatibility": "compatible", "rollback_target": semantic_target, "decision_reference_digest": d("consumer_ak_decision"), "trust_reference": trust_ref,
    "verifier_contract_digest": raw("verifier-contract"), "limits_digest": raw("limits")})
acceptance = add("owner_acceptance", {"schema": "semantic-owner-acceptance.v0", "consumer_intent_digest": d("consumer_intent"), "consumer_repository": consumer_repo, "canary_scope": canary_scope,
    "acceptance_authority": {"kind": "consumer_owner", "id": "consumer-owner"}, "acceptance_revision": 4, "acceptance_epoch": 80, "governing_scope_digest": consumer_decision["scope_digest"],
    "decision_reference_digest": d("consumer_ak_decision"), "valid_through_intent_revision": 4, "activation_epoch_not_after": 100, "revoked_by_digest": None})
materialization = add("materialization_receipt", {"schema": "semantic-materialization-verification-receipt.v0", "issuer": {"kind": "rocs", "id": "rocs-cli"},
    "consumer_intent_digest": d("consumer_intent"), "owner_acceptance_digest": d("owner_acceptance"), "coordinate": coordinate, "owner_approval_digest": d("owner_approval"), "trust_reference": trust_ref,
    "runtime_identity": rocs_tool, "capsule_archive_linkage_digest": d("capsule_archive_linkage"), "payload_projection_digest": d("payload_projection"), "source_payload_manifest_digest": d("payload_manifest"),
    "expected_consumer_manifest_digest": d("consumer_material_manifest"), "actual_consumer_manifest_digest": d("consumer_material_manifest"), "consumer_repository": consumer_repo,
    "canary_scope": canary_scope, "compatibility_report_digest": d("compatibility_report"), "compatibility_outcome": "compatible", "prior_receipt_digest": raw("prior-materialization"), "rollback_target": semantic_target,
    "rollback_ready": True, "verifier_contract_digest": intent["verifier_contract_digest"], "transaction_id": "materialize-4", "journal_state": "committed", "commit_marker_digest": raw("materialize-marker")})
def available_artifact(name: str, kind: str, **fields: object) -> dict:
    issuer = {"semantic_target": {"kind": "rocs", "id": "rocs-cli"}, "runtime_target": {"kind": "rocs", "id": "rocs-cli"},
        "disable_target": {"kind": "consumer_owner", "id": "consumer-owner"}, "recovery_runtime": {"kind": "recovery_controller", "id": "recovery"}}[kind]
    value = {"schema": "semantic-rollback-availability-receipt.v0", "issuer": issuer, "artifact_id": name.replace("_", "-"), "artifact_kind": kind,
        "coordinate": None, "runtime_identity": None, "materialization_receipt_digest": None, "runtime_revalidation_receipt_digest": None,
        "disable_contract_digest": None, "rehearsal_receipt_digest": None, "health_receipt_digest": None, "independently_available": True, "availability_epoch": 85}
    value.update(fields); return add(name, value)
semantic_available_artifact = available_artifact("semantic_target_artifact", "semantic_target", coordinate=predecessor, materialization_receipt_digest=semantic_target["target_materialization_receipt_digest"])
runtime_available_artifact = available_artifact("runtime_target_artifact", "runtime_target", runtime_identity=old_runtime, materialization_receipt_digest=runtime_target["target_materialization_receipt_digest"], runtime_revalidation_receipt_digest=runtime_target["runtime_revalidation_receipt_digest"])
disable_available_artifact = available_artifact("disable_target_artifact", "disable_target", disable_contract_digest=disable_target["disable_contract_digest"], rehearsal_receipt_digest=disable_target["rehearsal_receipt_digest"])
recovery_available_artifact = available_artifact("recovery_runtime_artifact", "recovery_runtime", runtime_identity=recovery_tool, rehearsal_receipt_digest=d("recovery_rehearsal_receipt"), health_receipt_digest=d("recovery_health_receipt"))
def availability(name: str, target: dict, **fields: object) -> dict:
    base = {"schema": "semantic-rollback-availability-proof.v0", "issuer": {"kind": "rocs", "id": "rocs-cli"}, "consumer_intent_digest": d("consumer_intent"), "owner_acceptance_digest": d("owner_acceptance"),
        "materialization_verification_receipt_digest": d("materialization_receipt"), "availability_epoch": 85,
        "recovery_controller_id": "recovery", "recovery_epoch": 85, "target_kind": target["kind"],
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
    "materialization_verification_receipt_digest": d("materialization_receipt"), "rollback_availability_proof_digest": d("semantic_rollback_availability"), "consumer_repository": consumer_repo, "canary_scope": canary_scope, "coordinate": coordinate, "runtime_identity": rocs_tool,
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
    return add(name, {"schema": "semantic-rollback-history-transition.v0", "issuer": {"kind": "consumer_owner", "id": "consumer-owner"}, "rollback_request_digest": request["rollback_request_digest"], "result": result,
        "active_state_before": active_state, "active_state_after": after, "stages": stages, "failure_stage": failure_stage, "error_digest": error_digest,
        "history_head_before": activation_head, "supersedes_activation_receipt_digest": supersedes})

semantic_request = add("semantic_rollback_request", {"schema": "semantic-rollback-request.v0", "issuer": {"kind": "consumer_owner", "id": "consumer-owner"}, "active_activation_receipt_digest": d("activation_receipt"),
    "from_state": active_state, "target": semantic_target, "recovery_runtime_identity": recovery_tool, "recovery_controller_id": "recovery", "recovery_epoch": 85, "owner_decision_reference_digest": d("consumer_ak_decision"), "precondition_digest": raw("semantic-preconditions")})
semantic_after = {"enabled": True, "coordinate": predecessor, "runtime_identity": rocs_tool}; semantic_stages = [{"stage": "semantic", "result": "completed", "error_digest": None}]
semantic_history = history("semantic_rollback_history", semantic_request, "rolled_back", semantic_after, semantic_stages, None, None, d("activation_receipt"))
semantic_receipt = add("semantic_rollback_receipt", {"schema": "semantic-rollback-receipt.v0", "issuer": {"kind": "recovery_controller", "id": "recovery"},
    "recovery_controller_id": "recovery", "recovery_epoch": 85, "rollback_request_digest": d("semantic_rollback_request"),
    "request_target_kind": "semantic", "result": "rolled_back", "stage_order": None, "active_state_before": active_state, "active_state_after": semantic_after,
    "availability_proof_digest": d("semantic_rollback_availability"), "runtime_revalidation_receipt_digest": None, "stages": semantic_stages, "failure_stage": None,
    "history_head_before": activation_head, "history_head_after": {"kind": "rollback", "digest": d("semantic_rollback_history")}, "error_digest": None,
    "supersedes_activation_receipt_digest": d("activation_receipt"), "ak_evidence_linkage_digest": d("ak_evidence_linkage"), "pi_delivery_receipt_digest": d("pi_delivery_delivered")})
runtime_request = add("runtime_rollback_request", {"schema": "semantic-rollback-request.v0", "issuer": {"kind": "consumer_owner", "id": "consumer-owner"}, "active_activation_receipt_digest": d("activation_receipt"),
    "from_state": active_state, "target": runtime_target, "recovery_runtime_identity": recovery_tool, "recovery_controller_id": "recovery", "recovery_epoch": 85, "owner_decision_reference_digest": d("consumer_ak_decision"), "precondition_digest": raw("runtime-preconditions")})
runtime_after = {"enabled": True, "coordinate": coordinate, "runtime_identity": old_runtime}; runtime_stages = [{"stage": "runtime", "result": "completed", "error_digest": None}]
runtime_history = history("runtime_rollback_history", runtime_request, "rolled_back", runtime_after, runtime_stages, None, None, d("activation_receipt"))
runtime_receipt = add("runtime_rollback_receipt", {"schema": "semantic-rollback-receipt.v0", "issuer": {"kind": "recovery_controller", "id": "recovery"},
    "recovery_controller_id": "recovery", "recovery_epoch": 85, "rollback_request_digest": d("runtime_rollback_request"),
    "request_target_kind": "runtime", "result": "rolled_back", "stage_order": None, "active_state_before": active_state, "active_state_after": runtime_after,
    "availability_proof_digest": d("runtime_rollback_availability"), "runtime_revalidation_receipt_digest": runtime_target["runtime_revalidation_receipt_digest"], "stages": runtime_stages, "failure_stage": None,
    "history_head_before": activation_head, "history_head_after": {"kind": "rollback", "digest": d("runtime_rollback_history")}, "error_digest": None,
    "supersedes_activation_receipt_digest": d("activation_receipt"), "ak_evidence_linkage_digest": None, "pi_delivery_receipt_digest": None})
disable_request = add("disable_rollback_request", {"schema": "semantic-rollback-request.v0", "issuer": {"kind": "consumer_owner", "id": "consumer-owner"}, "active_activation_receipt_digest": d("activation_receipt"),
    "from_state": active_state, "target": disable_target, "recovery_runtime_identity": recovery_tool, "recovery_controller_id": "recovery", "recovery_epoch": 85, "owner_decision_reference_digest": d("consumer_ak_decision"), "precondition_digest": raw("disable-preconditions")})
disable_after = {"enabled": False, "coordinate": None, "runtime_identity": rocs_tool}; disable_stages = [{"stage": "disable", "result": "completed", "error_digest": None}]
disable_history = history("disable_rollback_history", disable_request, "disabled", disable_after, disable_stages, None, None, d("activation_receipt"))
disable_receipt = add("disable_rollback_receipt", {"schema": "semantic-rollback-receipt.v0", "issuer": {"kind": "recovery_controller", "id": "recovery"},
    "recovery_controller_id": "recovery", "recovery_epoch": 85, "rollback_request_digest": d("disable_rollback_request"),
    "request_target_kind": "no_prior_disable", "result": "disabled", "stage_order": None, "active_state_before": active_state, "active_state_after": disable_after,
    "availability_proof_digest": d("disable_rollback_availability"), "runtime_revalidation_receipt_digest": None, "stages": disable_stages, "failure_stage": None,
    "history_head_before": activation_head, "history_head_after": {"kind": "disable", "digest": d("disable_rollback_history")}, "error_digest": None,
    "supersedes_activation_receipt_digest": d("activation_receipt"), "ak_evidence_linkage_digest": None, "pi_delivery_receipt_digest": None})
combined_request = add("combined_rollback_request", {"schema": "semantic-rollback-request.v0", "issuer": {"kind": "consumer_owner", "id": "consumer-owner"}, "active_activation_receipt_digest": d("activation_receipt"),
    "from_state": active_state, "target": combined_target, "recovery_runtime_identity": recovery_tool, "recovery_controller_id": "recovery", "recovery_epoch": 85, "owner_decision_reference_digest": d("consumer_ak_decision"), "precondition_digest": raw("combined-preconditions")})
partial_error = raw("runtime-stage-error"); partial_after = semantic_after
partial_stages = [{"stage": "semantic", "result": "completed", "error_digest": None}, {"stage": "runtime", "result": "failed", "error_digest": partial_error}]
partial_history = history("combined_partial_history", combined_request, "partial_failure", partial_after, partial_stages, "runtime", partial_error, None)
partial_receipt = add("combined_partial_failure_receipt", {"schema": "semantic-rollback-receipt.v0", "issuer": {"kind": "recovery_controller", "id": "recovery"},
    "recovery_controller_id": "recovery", "recovery_epoch": 85, "rollback_request_digest": d("combined_rollback_request"),
    "request_target_kind": "combined", "result": "partial_failure", "stage_order": "semantic_then_runtime", "active_state_before": active_state, "active_state_after": partial_after,
    "availability_proof_digest": d("combined_rollback_availability"), "runtime_revalidation_receipt_digest": None, "stages": partial_stages, "failure_stage": "runtime",
    "history_head_before": activation_head, "history_head_after": {"kind": "rollback", "digest": d("combined_partial_history")}, "error_digest": partial_error,
    "supersedes_activation_receipt_digest": None, "ak_evidence_linkage_digest": None, "pi_delivery_receipt_digest": None})
failed_error = raw("semantic-stage-error")
failed_receipt = add("failed_rollback_receipt", {"schema": "semantic-rollback-receipt.v0", "issuer": {"kind": "recovery_controller", "id": "recovery"},
    "recovery_controller_id": "recovery", "recovery_epoch": 85, "rollback_request_digest": d("semantic_rollback_request"),
    "request_target_kind": "semantic", "result": "failed", "stage_order": None, "active_state_before": active_state, "active_state_after": active_state,
    "availability_proof_digest": d("semantic_rollback_availability"), "runtime_revalidation_receipt_digest": None,
    "stages": [{"stage": "semantic", "result": "failed", "error_digest": failed_error}], "failure_stage": "semantic", "history_head_before": activation_head,
    "history_head_after": activation_head, "error_digest": failed_error, "supersedes_activation_receipt_digest": None, "ak_evidence_linkage_digest": None, "pi_delivery_receipt_digest": None})
def unresolved_ref(reference_id: str, repository: dict, required_state: str) -> dict:
    return {"resolution": "unresolved_candidate", "reference_id": reference_id, "repository": repository, "ak_store_head": None,
        "task_id": None, "task_record_digest": None, "artifact_digest": None, "observed_canonical_state": None, "required_state": required_state}
def stops(rows: list[tuple[str, str, dict]]) -> list[dict]:
    rows = sorted(rows)
    return [{"condition_id": cid, "condition_kind": kind, "fact_reference": unresolved_ref("fact:" + cid, repository, "accepted_current"),
        "trigger_state": "unsatisfied_or_noncurrent", "required_effect": "stop_before_mutation", "resume_state": "accepted_current"} for cid, kind, repository in rows]
ak_prerequisites = [unresolved_ref(x, ak_coord_repo, "accepted_current") for x in ["adr:0053", "decision:53", "plan:decision-53-implementation", "plan:decision-53-validation-rollout-rollback"]]
ak_evidence_repositories = {
    "accepted-decision-reference": ak_coord_repo, "deterministic-rerun": rocs_repo, "docs-strict": rocs_repo,
    "node-validator": rocs_repo, "owner-task-references": ak_coord_repo, "python-validator": rocs_repo,
    "rollback-rehearsal": rocs_repo}
ak_evidence = [unresolved_ref(x, ak_evidence_repositories[x], "evidence_accepted_current") for x in sorted(ak_evidence_repositories)]
ak_stop_rows = [("stale-or-revoked-decision", "stale_or_revoked_decision", ak_coord_repo), ("store-head-drift", "store_head_drift", ak_coord_repo),
    ("scope-drift", "scope_drift", ak_coord_repo), ("missing-owner-task", "missing_owner_task", ak_coord_repo),
    ("attempted-owner-substitution", "owner_substitution", ak_coord_repo), ("attempted-use-as-authorization", "authorization_escalation", ak_coord_repo)]
ak_coordination_contract = add("ak_coordination_task_contract", {"schema": "semantic-non-authorizing-task-contract.v0", "task_contract_id": "decision-53-ak-coordination",
    "task_id": "candidate-decision-53-ak-coordination", "task_owner_id": "agent-kernel-owner", "task_kind": "ak_coordination", "repository": ak_coord_repo, "allowed_paths": [],
    "dependencies": [], "prerequisites": ak_prerequisites, "required_evidence": ak_evidence, "rollback_owner": {"kind": "ak", "id": "agent-kernel-owner"},
    "stop_conditions": stops(ak_stop_rows), "authority_scope": "coordination_only", "authorizes_execution": False, "authorizes_publication": False,
    "authorizes_adoption": False, "contract_status": "candidate_not_created"})
consumer_dependency_repositories = {"candidate-decision-53-ak-coordination": ak_coord_repo, "candidate-decision-53-rocs-implementation": rocs_repo,
    "candidate-decision-53-semantic-owner-publication": owner_repo}
consumer_dependencies = [unresolved_ref(x, consumer_dependency_repositories[x], "completed_current") for x in sorted(consumer_dependency_repositories)]
consumer_prerequisite_repositories = {"adr:0053": ak_coord_repo, "consent:pi-canary-consumer-owner": canary_repo, "decision:53": ak_coord_repo,
    "plan:decision-53-implementation": ak_coord_repo, "plan:decision-53-validation-rollout-rollback": ak_coord_repo}
consumer_prerequisites = [unresolved_ref(x, consumer_prerequisite_repositories[x], "accepted_current") for x in sorted(consumer_prerequisite_repositories)]
consumer_evidence_repositories = {
    "activation-receipt": canary_repo, "canary-evidence": canary_repo, "consumer-intent-and-acceptance": canary_repo,
    "exact-materialization-receipt": rocs_repo, "rollback-availability-proof": rocs_repo,
    "rollback-history": canary_repo, "rollback-rehearsal": rocs_repo, "scoped-gate-decision": ak_coord_repo,
}
consumer_evidence = [unresolved_ref(x, consumer_evidence_repositories[x], "evidence_accepted_current") for x in sorted(consumer_evidence_repositories)]
consumer_stop_rows = [("missing-owner-consent", "missing_owner_consent", canary_repo), ("target-or-recovery-unavailable", "rollback_unavailable", canary_repo),
    ("stale-semantic-trust-or-ledger", "stale_semantic_trust_or_ledger", owner_repo),
    ("stale-ak-decision-or-store", "stale_ak_decision_or_store", ak_coord_repo),
    ("stale-consumer-activation-or-history", "stale_consumer_activation_or_history", canary_repo),
    ("projection-or-issuer-drift", "projection_or_issuer_drift", rocs_repo),
    ("failed-validator", "validator_failure", rocs_repo), ("unknown-or-incompatible", "compatibility_failure", owner_repo),
    ("missing-rollback-rehearsal", "missing_rollback_rehearsal", rocs_repo),
    ("protocol-scope-expansion", "protocol_scope_expansion", canary_repo)]
consumer_canary_contract = add("single_canary_consumer_task_contract", {"schema": "semantic-non-authorizing-task-contract.v0", "task_contract_id": "decision-53-single-canary-consumer",
    "task_id": "candidate-decision-53-single-canary-consumer", "task_owner_id": "consumer-owner", "task_kind": "single_canary_consumer", "repository": canary_repo,
    "allowed_paths": ["config/semantic-release/canary.json", "docs/project/semantic-release-canary-evidence.md", "scripts/ci/semantic-release-canary.sh"],
    "dependencies": consumer_dependencies, "prerequisites": consumer_prerequisites, "required_evidence": consumer_evidence,
    "rollback_owner": {"kind": "consumer_owner", "id": "consumer-owner"}, "stop_conditions": stops(consumer_stop_rows),
    "authority_scope": "consumer_owner_candidate_only", "authorizes_execution": False, "authorizes_publication": False, "authorizes_adoption": False, "contract_status": "candidate_not_created"})
audit = add("audit_envelope", {"schema": "semantic-audit-envelope.v0", "artifact_schema": "semantic-rollback-receipt.v0", "artifact_digest": d("semantic_rollback_receipt"), "event": "rolled_back",
    "recorded_at": "2026-07-13T12:30:45Z", "issuer": {"kind": "ak", "id": "agent-kernel"}, "audit_sequence": 9, "previous_audit_envelope_digest": raw("audit-8")})
error = add("error_envelope", {"schema": "semantic-protocol-error.v0", "code": "digest_mismatch", "stage": "validate", "retryable": False, "related_artifact_digest": d("capsule"),
    "details": [{"key": "artifact", "value": "capsule"}], "error_digest": ZERO})

# Explicit owner-read facts. Cases merge the exact rule-specific tuple before authority wrapping;
# no canonical value is synthesized by the wrapper.
owner_ak_authority_facts = {"canonical_store_head": ak_store_head,
    "current_decision_record_digest": owner_decision["decision_record_digest"]}
consumer_ak_authority_facts = {"canonical_store_head": ak_store_head,
    "current_decision_record_digest": consumer_decision["decision_record_digest"]}
trust_authority_facts = {"canonical_trust_root_digest": trust_root["trust_root_digest"],
    "canonical_trust_revocation_revision": revocation["revocation_revision"],
    "canonical_trust_revocation_head": revocation["trust_revocation_digest"], "revoked_trust_digests": []}
publication_authority_facts = {"canonical_publication_revision": publication["ledger_revision"],
    "canonical_publication_head": publication["owner_publication_digest"]}
acceptance_authority_facts = {"current_acceptance_digest": acceptance["owner_acceptance_digest"],
    "current_acceptance_revision": acceptance["acceptance_revision"], **trust_authority_facts, **publication_authority_facts}
recovery_authority_facts = {"canonical_recovery_controller_id": "recovery",
    "canonical_recovery_runtime_identity": recovery_tool, "canonical_recovery_epoch": 85}
activation_authority_facts = {**acceptance_authority_facts, **recovery_authority_facts}

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

golden = {"protocol": "semantic-release-v0", "rfc_revision": "semantic-release-revision-v12", "canonicalization": "RFC8785 JCS after raw-token duplicate-free UTF-8 canonical-integer-only I-JSON validation",
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
rotation_context = {"current_root_digest": d("trust_root"), "old_root": trust_root, "new_root": new_trust_root, "approval": rotation_approval, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "revoked": [], "decision": owner_decision, **owner_ak_authority_facts}
revocation_context = {"approval": revocation_approval, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "prior_revision": 0, "prior_head": None, "decision": owner_decision, **owner_ak_authority_facts}
root_revocation_action = {"kind": "trust_revocation", "namespace": "ai-society.core", "owner_policy_digest": d("owner_policy"), "owner_set_digest": d("owner_set"),
    "approval_predicate_digest": d("approval_predicate"), "target_kind": "trust_root", "target_digest": d("trust_root"), "effective_ledger_revision": 4,
    "reason_digest": raw("root-revocation-reason"), "prior_revocation_digest": d("trust_revocation"), "revocation_revision": 2}
root_revocation_action_digest = action_digest(root_revocation_action)
root_revocation_approval = variant(revocation_approval, action=root_revocation_action, action_digest=root_revocation_action_digest,
    votes=[{**vote, "approved_action_digest": root_revocation_action_digest} for vote in revocation_approval["votes"]])
root_revocation = variant(revocation, revocation_revision=2, target_kind="trust_root", target_digest=d("trust_root"), effective_ledger_revision=4,
    reason_digest=root_revocation_action["reason_digest"], owner_approval_digest=root_revocation_approval["owner_approval_digest"], prior_revocation_digest=d("trust_revocation"))
root_revocation_context = {"approval": root_revocation_approval, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "prior_revision": 1, "prior_head": d("trust_revocation"), "decision": owner_decision, **owner_ak_authority_facts}
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
compatibility_non_override_context = {"policy": compat_policy, "overrides": [], "override_approvals": {},
    "owner_policy": None, "owner_set": None, "predicate": None, "decision": None, **owner_ak_authority_facts}
override_context = {**compatibility_non_override_context, "prior_version": "1.0.0", "overrides": [override], "override_approvals": {d("override_approval"): override_approval},
    "owner_policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "decision": owner_decision,
    "canonical_store_head": ak_store_head, "current_decision_record_digest": owner_decision["decision_record_digest"]}
override_drift = variant(overridden_report, override_digests=[])
extra_tombstones = variant(resulting_tombstones, entries=resulting_tombstones["entries"] + [{"semantic_id": "core.Surplus", "reason": "removed", "origin_record_digest": raw("surplus-origin")}])
wrong_origin_entries = copy.deepcopy(resulting_tombstones["entries"])
next(row for row in wrong_origin_entries if row["semantic_id"] == "core.Legacy")["origin_record_digest"] = raw("wrong-tombstone-origin")
wrong_tombstone_origin = variant(resulting_tombstones, entries=wrong_origin_entries)
dropped_cumulative_entries = [copy.deepcopy(row) for row in resulting_tombstones["entries"] if row["semantic_id"] != "core.Old"]
dropped_cumulative_registry = variant(resulting_tombstones, entries=dropped_cumulative_entries)
dropped_cumulative_history = variant(resulting_tombstone_history,
    current_registry_digest=dropped_cumulative_registry["tombstone_registry_digest"],
    revisions=[*copy.deepcopy(resulting_tombstone_history["revisions"][:-1]),
        {**copy.deepcopy(resulting_tombstone_history["revisions"][-1]), "registry": dropped_cumulative_registry}])
changed_cumulative_entries = copy.deepcopy(resulting_tombstones["entries"])
next(row for row in changed_cumulative_entries if row["semantic_id"] == "core.Old")["origin_record_digest"] = raw("changed-old-origin")
changed_cumulative_registry = variant(resulting_tombstones, entries=changed_cumulative_entries)
changed_cumulative_history = variant(resulting_tombstone_history,
    current_registry_digest=changed_cumulative_registry["tombstone_registry_digest"],
    revisions=[*copy.deepcopy(resulting_tombstone_history["revisions"][:-1]),
        {**copy.deepcopy(resulting_tombstone_history["revisions"][-1]), "registry": changed_cumulative_registry}])
truncated_tombstone_history = variant(resulting_tombstone_history,
    revisions=copy.deepcopy(resulting_tombstone_history["revisions"][1:]))
restart_registry = variant(tombstones, prior_registry_digest=None)
restart_revisions = copy.deepcopy(resulting_tombstone_history["revisions"])
restart_revisions[1]["registry"] = restart_registry
restart_tombstone_history = variant(resulting_tombstone_history, revisions=restart_revisions)
dropped_revision_tombstone_history = variant(resulting_tombstone_history,
    revisions=[copy.deepcopy(resulting_tombstone_history["revisions"][0]), copy.deepcopy(resulting_tombstone_history["revisions"][-1])])
wrong_link_registry = variant(resulting_tombstones, prior_registry_digest=raw("wrong-tombstone-prior-link"))
wrong_link_revisions = copy.deepcopy(resulting_tombstone_history["revisions"])
wrong_link_revisions[-1]["registry"] = wrong_link_registry
wrong_link_tombstone_history = variant(resulting_tombstone_history,
    current_registry_digest=wrong_link_registry["tombstone_registry_digest"], revisions=wrong_link_revisions)
unauthorized_delta_revisions = copy.deepcopy(resulting_tombstone_history["revisions"])
unauthorized_delta_revisions[-1]["authorized_delta"]["authorization_record_digest"] = raw("unauthorized-tombstone-delta")
unauthorized_delta_history = variant(resulting_tombstone_history, revisions=unauthorized_delta_revisions)
tombstoned_addition = variant(compat_report, changes=[{"category": "addition", "semantic_id": "core.Legacy", "classification": "compatible", "semver_effect": "minor", "condition_id": None}])
reuse_namespace_drift_head = {**reuse_lifecycle_tombstone_head, "namespace": "other.space"}
reuse_lifecycle_drift_head = {**reuse_lifecycle_tombstone_head, "lifecycle_head_digest": raw("wrong-lifecycle-current-head")}
reuse_revision_drift_head = {**reuse_lifecycle_tombstone_head, "tombstone_registry_revision": resulting_tombstones["registry_revision"] - 1}
def lifecycle_tombstone_head_for(registry: dict) -> dict:
    return {"namespace": registry["namespace"], "lifecycle_head_digest": registry["lifecycle_head_digest"],
        "tombstone_registry_digest": registry["tombstone_registry_digest"], "tombstone_registry_revision": registry["registry_revision"]}
stale_deprecation_ledger = copy.deepcopy(deprecation_ledger); stale_deprecation_ledger["ledger_revision"] = 1
lifecycle_context = {"deprecation": deprecation, "policy": compat_policy, "resulting_tombstones": resulting_tombstones,
    "tombstone_history": resulting_tombstone_history,
    "deprecation_ledger": deprecation_ledger, "removal_ledger": removal_ledger, "deprecation_publication": publication, "removal_publication": major_publication,
    "deprecation_transaction": publish_tx, "deprecation_journal": publish_journal, "deprecation_marker": publish_marker, "deprecation_approval": owner_approval,
    "deprecation_prior_status": prior_publication, "deprecation_prior_journal": prior_publish_journal, "deprecation_canonical_ledger": dep_canonical_ledger,
    "removal_transaction": major_tx, "removal_journal": major_journal, "removal_marker": major_marker, "removal_approval": major_approval,
    "removal_prior_status": withdrawal, "removal_prior_journal": withdraw_journal, "removal_canonical_ledger": rem_canonical_ledger,
    "owner_policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "trust_root": trust_root, "external_trust_root_pin": external_trust_root_pin,
    "deprecation_decision": owner_decision, "removal_decision": major_decision,
    "canonical_store_head": ak_store_head, "current_deprecation_decision_record_digest": owner_decision["decision_record_digest"],
    "current_removal_decision_record_digest": major_decision["decision_record_digest"],
    "canonical_deprecation_revision": 2, "canonical_deprecation_head": d("owner_publication"), "canonical_removal_revision": 4, "canonical_removal_head": d("major_owner_publication"),
    "deprecation_prior_head": deprecation["prior_lifecycle_digest"], "current_lifecycle_head": deprecation["deprecation_record_digest"],
    **trust_authority_facts}
cases += [
    case("minor_bump_satisfies_addition", "compatibility", compat_report, None, {**compatibility_non_override_context, "prior_version": "1.0.0"}),
    case("patch_bump_rejects_minor_effect", "compatibility", patch_minor, "semver_violation", {**compatibility_non_override_context, "prior_version": "1.0.0"}),
    case("major_bump_satisfies_breaking", "compatibility", major_report, None, {**compatibility_non_override_context, "prior_version": "1.1.0"}),
    case("minor_bump_rejects_major_effect", "compatibility", minor_for_major, "semver_violation", {**compatibility_non_override_context, "prior_version": "1.1.0"}),
    case("compatibility_policy_exact_categories", "compatibility_policy", compat_policy, None),
    case("compatibility_policy_duplicate_missing_category", "compatibility_policy", bad_compat_policy, "compatibility_rejected"),
    case("conditional_evidence_executes_true", "compatibility", conditional_report, None, {**compatibility_non_override_context, "prior_version": "1.0.0"}),
    case("consumer_protocol_floor_executes_true", "compatibility", protocol_report, None, {**compatibility_non_override_context, "prior_version": "1.0.0"}),
    case("deprecation_interval_condition_executes_true", "compatibility", interval_report, None, {**compatibility_non_override_context, "prior_version": "1.1.0"}),
    case("conditional_evidence_missing", "compatibility", missing_condition, "compatibility_rejected", {**compatibility_non_override_context, "prior_version": "1.0.0"}),
    case("conditional_evidence_false", "compatibility", false_condition, "compatibility_rejected", {**compatibility_non_override_context, "prior_version": "1.0.0"}),
    case("duplicate_compatibility_condition_rejected", "compatibility", duplicate_conditions, "compatibility_rejected", {**compatibility_non_override_context, "prior_version": "1.0.0"}),
    case("surplus_unreferenced_condition_rejected", "compatibility", surplus_conditions, "compatibility_rejected", {**compatibility_non_override_context, "prior_version": "1.0.0"}),
    case("condition_reference_must_be_bijective", "compatibility", shared_condition_report, "compatibility_rejected", {**compatibility_non_override_context, "prior_version": "1.0.0"}),
    case("executable_owner_override_accepts", "compatibility", overridden_report, None, override_context),
    case("override_digest_omission_rejected", "compatibility", override_drift, "compatibility_rejected", override_context),
    case("override_cannot_lower_unknown_semver_floor", "compatibility", lowered_report, "compatibility_rejected", {**compatibility_non_override_context, "prior_version": "1.0.0", "overrides": [lowered_override], "override_approvals": {lowered_override_approval["owner_approval_digest"]: lowered_override_approval}, "owner_policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "decision": owner_decision, "canonical_store_head": ak_store_head, "current_decision_record_digest": owner_decision["decision_record_digest"]}),
    case("override_approval_requires_complete_override", "pi_variant", incomplete_override_approval, "malformed_input", schema_valid=False),
    case("override_approval_namespace_chain_must_match", "compatibility", wrong_namespace_override_report, "compatibility_rejected", {**compatibility_non_override_context, "prior_version": "1.0.0", "overrides": [wrong_namespace_override], "override_approvals": {wrong_namespace_override_approval["owner_approval_digest"]: wrong_namespace_override_approval}, "owner_policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "decision": owner_decision, "canonical_store_head": ak_store_head, "current_decision_record_digest": owner_decision["decision_record_digest"]}),
    case("deprecation_interval_satisfied", "lifecycle", removal, None, lifecycle_context),
    case("removal_before_interval_rejected", "lifecycle", early_removal, "lifecycle_violation", lifecycle_context),
    case("lifecycle_namespace_drift_rejected", "lifecycle", variant(removal, namespace="other.space"), "lifecycle_violation", lifecycle_context),
    case("lifecycle_prior_head_drift_rejected", "lifecycle", variant(removal, prior_lifecycle_digest=raw("wrong-lifecycle-head")), "lifecycle_violation", lifecycle_context),
    case("tombstone_registry_extra_entry_rejected", "lifecycle", removal, "lifecycle_violation", {**lifecycle_context, "resulting_tombstones": extra_tombstones}),
    case("tombstone_origin_exact_binding", "lifecycle", removal, "lifecycle_violation", {**lifecycle_context, "resulting_tombstones": wrong_tombstone_origin}),
    case("tombstone_history_cumulative_entries_are_permanent", "lifecycle", removal, "lifecycle_violation",
        {**lifecycle_context, "resulting_tombstones": dropped_cumulative_registry, "tombstone_history": dropped_cumulative_history}),
    case("lifecycle_requires_accepted_current_ledger_heads", "lifecycle", removal, "lifecycle_violation", {**lifecycle_context, "canonical_removal_head": raw("stale-lifecycle-head")}),
    case("lifecycle_referenced_ledger_self_digest_checked", "lifecycle", removal, "digest_mismatch", {**lifecycle_context, "deprecation_ledger": stale_deprecation_ledger}),
    case("non_tombstoned_identifier_accepts", "tombstone_reuse", compat_report, None,
        {"tombstones": resulting_tombstones, "tombstone_history": resulting_tombstone_history, "override": None, "canonical_lifecycle_tombstone_head": reuse_lifecycle_tombstone_head}),
    case("tombstoned_identifier_reuse_rejected", "tombstone_reuse", reuse_report, "lifecycle_violation",
        {"tombstones": resulting_tombstones, "tombstone_history": resulting_tombstone_history, "override": None, "canonical_lifecycle_tombstone_head": reuse_lifecycle_tombstone_head}),
    case("tombstoned_identifier_cannot_return_as_addition", "tombstone_reuse", tombstoned_addition, "lifecycle_violation",
        {"tombstones": resulting_tombstones, "tombstone_history": resulting_tombstone_history, "override": None, "canonical_lifecycle_tombstone_head": reuse_lifecycle_tombstone_head}),
    case("override_cannot_legalize_identifier_reuse", "tombstone_reuse", reuse_report, "lifecycle_violation",
        {"tombstones": resulting_tombstones, "tombstone_history": resulting_tombstone_history, "override": bad_override, "canonical_lifecycle_tombstone_head": reuse_lifecycle_tombstone_head}),
    case("tombstone_reuse_stale_registry_rejected", "tombstone_reuse", compat_report, "lifecycle_violation",
        {"tombstones": resulting_tombstones, "tombstone_history": resulting_tombstone_history, "override": None, "canonical_lifecycle_tombstone_head": projection_lifecycle_tombstone_head}),
    case("tombstone_registry_semantic_owner_substitution_rejected", "tombstone_reuse", compat_report, "issuer_scope_violation",
        {"tombstones": resulting_tombstones, "tombstone_history": resulting_tombstone_history, "override": None, "canonical_lifecycle_tombstone_head": reuse_lifecycle_tombstone_head}),
    case("tombstone_reuse_namespace_currentness_rejected", "tombstone_reuse", compat_report, "lifecycle_violation",
        {"tombstones": resulting_tombstones, "tombstone_history": resulting_tombstone_history, "override": None, "canonical_lifecycle_tombstone_head": reuse_namespace_drift_head}),
    case("tombstone_reuse_lifecycle_head_currentness_rejected", "tombstone_reuse", compat_report, "lifecycle_violation",
        {"tombstones": resulting_tombstones, "tombstone_history": resulting_tombstone_history, "override": None, "canonical_lifecycle_tombstone_head": reuse_lifecycle_drift_head}),
    case("tombstone_reuse_registry_revision_currentness_rejected", "tombstone_reuse", compat_report, "lifecycle_violation",
        {"tombstones": resulting_tombstones, "tombstone_history": resulting_tombstone_history, "override": None, "canonical_lifecycle_tombstone_head": reuse_revision_drift_head}),
    case("tombstone_history_truncation_rejected", "tombstone_reuse", compat_report, "lifecycle_violation",
        {"tombstones": resulting_tombstones, "tombstone_history": truncated_tombstone_history, "override": None, "canonical_lifecycle_tombstone_head": reuse_lifecycle_tombstone_head}),
    case("tombstone_history_restart_rejected", "tombstone_reuse", compat_report, "lifecycle_violation",
        {"tombstones": resulting_tombstones, "tombstone_history": restart_tombstone_history, "override": None, "canonical_lifecycle_tombstone_head": reuse_lifecycle_tombstone_head}),
    case("tombstone_history_dropped_revision_rejected", "tombstone_reuse", compat_report, "lifecycle_violation",
        {"tombstones": resulting_tombstones, "tombstone_history": dropped_revision_tombstone_history, "override": None, "canonical_lifecycle_tombstone_head": reuse_lifecycle_tombstone_head}),
    case("tombstone_history_exact_digest_links_required", "tombstone_reuse", compat_report, "lifecycle_violation",
        {"tombstones": wrong_link_registry, "tombstone_history": wrong_link_tombstone_history, "override": None,
         "canonical_lifecycle_tombstone_head": lifecycle_tombstone_head_for(wrong_link_registry)}),
    case("tombstone_history_authorized_delta_required", "tombstone_reuse", compat_report, "lifecycle_violation",
        {"tombstones": resulting_tombstones, "tombstone_history": unauthorized_delta_history, "override": None, "canonical_lifecycle_tombstone_head": reuse_lifecycle_tombstone_head}),
    case("tombstone_history_dropped_cumulative_entry_rejected", "tombstone_reuse", compat_report, "lifecycle_violation",
        {"tombstones": dropped_cumulative_registry, "tombstone_history": dropped_cumulative_history, "override": None,
         "canonical_lifecycle_tombstone_head": lifecycle_tombstone_head_for(dropped_cumulative_registry)}),
    case("tombstone_history_changed_cumulative_entry_rejected", "tombstone_reuse", compat_report, "lifecycle_violation",
        {"tombstones": changed_cumulative_registry, "tombstone_history": changed_cumulative_history, "override": None,
         "canonical_lifecycle_tombstone_head": lifecycle_tombstone_head_for(changed_cumulative_registry)})]

stale_tx = variant(publish_tx, expected_prior_revision=0)
fork_tx = variant(publish_tx, expected_prior_head_digest=raw("fork-head"), transaction_id="fork")
version_reuse_tx = copy.deepcopy(publish_tx); version_reuse_tx["coordinate"]["capsule_digest"] = raw("different-capsule"); rehash(version_reuse_tx)
replay_tx = copy.deepcopy(publish_tx)
prepared = variant(publish_journal, state="prepared", linearized=False, recovery_action="discard_staging")
prepared_intent = variant(publish_recovery_intent, journal_digest=prepared["publication_journal_digest"])
committing = variant(publish_journal, state="committing", linearized=True, recovery_action="complete_commit")
committing_intent = variant(publish_recovery_intent, journal_digest=committing["publication_journal_digest"])
committing_marker = variant(publish_marker, journal_digest=committing["publication_journal_digest"])
withdraw_recovery = variant(withdraw_journal, state="committing", linearized=True, recovery_action="complete_commit")
withdraw_recovery_intent = variant(publish_recovery_intent, transaction_digest=d("withdraw_transaction"),
    journal_digest=withdraw_recovery["publication_journal_digest"], resulting_record_digest=d("publication_withdrawal"),
    resulting_ledger_revision=3, resulting_ledger_head_digest=d("publication_withdrawal"))
withdraw_recovery_marker = variant(withdraw_marker, journal_digest=withdraw_recovery["publication_journal_digest"])
revoke_prepared = variant(revoke_journal, state="prepared", linearized=False, recovery_action="discard_staging")
revoke_prepared_intent = variant(publish_recovery_intent, transaction_digest=d("revoke_transaction"),
    journal_digest=revoke_prepared["publication_journal_digest"], resulting_record_digest=d("publication_revocation"),
    resulting_ledger_revision=4, resulting_ledger_head_digest=d("publication_revocation"))
aborted = variant(publish_journal, state="aborted", linearized=False, recovery_action="discard_staging")
aborted_intent = variant(publish_recovery_intent, journal_digest=aborted["publication_journal_digest"])
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
owner_canonical_decision_context = {"canonical_store_head": ak_store_head, "current_decision_record_digest": owner_decision["decision_record_digest"],
    "trust_root": trust_root, "external_trust_root_pin": external_trust_root_pin, **trust_authority_facts,
    "canonical_publication_revision": publication["ledger_revision"], "canonical_publication_head": publication["owner_publication_digest"],
    "canonical_publication_journal_head": publish_journal["publication_journal_digest"]}
publish_commit_context = {"transaction": publish_tx, "journal": publish_journal, "marker": publish_marker, "approval": owner_approval, "trust_root": trust_root, "external_trust_root_pin": external_trust_root_pin, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "decision": owner_decision, "expected_action": release_action, "prior_status": prior_publication, "prior_journal_digest": d("prior_publication_journal"), "prior_journal": prior_publish_journal, **owner_canonical_decision_context,
    **trust_authority_facts, "canonical_publication_revision": prior_publication["ledger_revision"],
    "canonical_publication_head": prior_publication["owner_publication_digest"],
    "canonical_publication_journal_head": prior_publish_journal["publication_journal_digest"]}
def recovery_state(intent_marker: dict, revision: int, head: str, status_digest: str, *, staging: bool,
        durable_marker: dict | None = None) -> dict:
    return {"revision": revision, "head": head, "status_record_digest": status_digest,
        "intent_marker_digest": intent_marker["publication_recovery_intent_marker_digest"] if staging else None,
        "durable_commit_marker_digest": None if durable_marker is None else durable_marker["publication_commit_marker_digest"],
        "staging_present": staging}


def recovery_state_receipt(name: str, phase: str, state: dict, journal: dict, transaction: dict) -> dict:
    issuer = {"kind": "semantic_owner", "id": "semantic-owner"} if phase == "before" else {"kind": "recovery_controller", "id": "recovery"}
    return add(name, {"schema": "semantic-publication-recovery-state-receipt.v0", "phase": phase, "issuer": issuer,
        "semantic_owner_id": "semantic-owner", "recovery_controller_id": "recovery", "recovery_epoch": 85,
        "namespace": transaction["namespace"], "transaction_digest": transaction["publication_transaction_digest"],
        "recovery_journal_digest": journal["publication_journal_digest"], "state": state})

publish_prepared_before_state = recovery_state(prepared_intent, 1, d("prior_owner_publication"), d("prior_owner_publication"), staging=True)
publish_prepared_after_state = recovery_state(prepared_intent, 1, d("prior_owner_publication"), d("prior_owner_publication"), staging=False)
publish_committing_before_state = recovery_state(committing_intent, 1, d("prior_owner_publication"), d("prior_owner_publication"), staging=True)
publish_committing_after_state = recovery_state(committing_intent, 2, d("owner_publication"), d("owner_publication"), staging=False, durable_marker=committing_marker)
withdraw_before_state = recovery_state(withdraw_recovery_intent, 2, d("owner_publication"), d("owner_publication"), staging=True)
withdraw_after_state = recovery_state(withdraw_recovery_intent, 3, d("publication_withdrawal"), d("publication_withdrawal"), staging=False, durable_marker=withdraw_recovery_marker)
revoke_before_state = recovery_state(revoke_prepared_intent, 3, d("publication_withdrawal"), d("publication_withdrawal"), staging=True)
revoke_after_state = recovery_state(revoke_prepared_intent, 3, d("publication_withdrawal"), d("publication_withdrawal"), staging=False)
aborted_before_state = recovery_state(aborted_intent, 1, d("prior_owner_publication"), d("prior_owner_publication"), staging=True)
aborted_after_state = recovery_state(aborted_intent, 1, d("prior_owner_publication"), d("prior_owner_publication"), staging=False)

publish_prepared_before = recovery_state_receipt("publish_prepared_before_state_receipt", "before", publish_prepared_before_state, prepared, publish_tx)
publish_prepared_after = recovery_state_receipt("publish_prepared_after_state_receipt", "after", publish_prepared_after_state, prepared, publish_tx)
publish_committing_before = recovery_state_receipt("publish_committing_before_state_receipt", "before", publish_committing_before_state, committing, publish_tx)
publish_committing_after = recovery_state_receipt("publish_committing_after_state_receipt", "after", publish_committing_after_state, committing, publish_tx)
withdraw_before = recovery_state_receipt("withdraw_before_state_receipt", "before", withdraw_before_state, withdraw_recovery, withdraw_tx)
withdraw_completed = recovery_state_receipt("withdraw_after_state_receipt", "after", withdraw_after_state, withdraw_recovery, withdraw_tx)
revoke_before = recovery_state_receipt("revoke_before_state_receipt", "before", revoke_before_state, revoke_prepared, revoke_tx)
revoke_discarded = recovery_state_receipt("revoke_after_state_receipt", "after", revoke_after_state, revoke_prepared, revoke_tx)
aborted_before = recovery_state_receipt("aborted_before_state_receipt", "before", aborted_before_state, aborted, publish_tx)
aborted_after = recovery_state_receipt("aborted_after_state_receipt", "after", aborted_after_state, aborted, publish_tx)


def recovery_context(subject_journal: dict, before: dict, after: dict, intent_marker: dict,
        marker: dict | None, transaction: dict, resulting_status: dict, prior_status: dict, prior_journal: dict,
        approval: dict, expected_action: dict, decision: dict = owner_decision) -> dict:
    prior_status_digest = prior_status.get("owner_publication_digest", prior_status.get("publication_status_transition_digest"))
    result_digest = resulting_status.get("owner_publication_digest", resulting_status.get("publication_status_transition_digest"))
    if prior_status_digest is None or result_digest is None: raise ValueError("recovery status lacks a protocol digest")
    before_state = before["state"]
    return {"before": before, "after": after, "intent_marker": intent_marker, "marker": marker,
        "transaction": transaction, "resulting_status": resulting_status, "prior_status": prior_status,
        "prior_journal": prior_journal, "approval": approval, "expected_action": expected_action,
        "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "decision": decision,
        "trust_root": trust_root, "external_trust_root_pin": external_trust_root_pin,
        "canonical_store_head": ak_store_head, "current_decision_record_digest": decision["decision_record_digest"],
        **trust_authority_facts, "canonical_publication_revision": before_state["revision"],
        "canonical_publication_head": before_state["head"], "canonical_publication_status_digest": prior_status_digest,
        "canonical_publication_journal_head": prior_journal["publication_journal_digest"],
        "canonical_recovery_journal_head": subject_journal["publication_journal_digest"],
        "canonical_recovery_transaction_digest": transaction["publication_transaction_digest"],
        "canonical_recovery_resulting_revision": subject_journal["resulting_ledger_revision"],
        "canonical_recovery_resulting_head": subject_journal["resulting_ledger_head_digest"],
        "canonical_recovery_resulting_status_digest": result_digest,
        "canonical_recovery_controller_id": "recovery", "canonical_recovery_runtime_identity": recovery_tool,
        "canonical_recovery_epoch": 85}

publish_prepared_context = recovery_context(prepared, publish_prepared_before, publish_prepared_after, prepared_intent, None,
    publish_tx, publication, prior_publication, prior_publish_journal, owner_approval, release_action)
publish_recovery_context = recovery_context(committing, publish_committing_before, publish_committing_after, committing_intent,
    committing_marker, publish_tx, publication, prior_publication, prior_publish_journal, owner_approval, release_action)
withdraw_recovery_context = recovery_context(withdraw_recovery, withdraw_before, withdraw_completed, withdraw_recovery_intent,
    withdraw_recovery_marker, withdraw_tx, withdrawal, publication, publish_journal, withdraw_approval, withdraw_approval["action"])
revoke_recovery_context = recovery_context(revoke_prepared, revoke_before, revoke_discarded, revoke_prepared_intent, None,
    revoke_tx, revoked_publication, withdrawal, withdraw_journal, revoke_approval, revoke_approval["action"])
aborted_recovery_context = recovery_context(aborted, aborted_before, aborted_after, aborted_intent, None,
    publish_tx, publication, prior_publication, prior_publish_journal, owner_approval, release_action)
prepared_durable_marker = variant(publish_marker, journal_digest=prepared["publication_journal_digest"])
fsynced_intent_descriptor = variant(prepared_intent, fsync_complete=True)
wrong_owner_intent_descriptor = variant(prepared_intent, issuer={"kind": "semantic_owner", "id": "semantic-owner"})
before_as_controller_receipt = variant(publish_committing_before, phase="after", issuer={"kind": "recovery_controller", "id": "recovery"})
after_as_semantic_owner_receipt = variant(publish_committing_after, phase="before", issuer={"kind": "semantic_owner", "id": "semantic-owner"})
recovery_namespace_drift_before = variant(publish_committing_before, namespace="other.space")
recovery_insufficient_approval = variant(owner_approval, votes=owner_approval["votes"][:1])
recovery_wrong_trust_root = variant(trust_root, owner_policy_digest=raw("recovery-wrong-trust-policy"))
recovery_rejected_decision = variant(owner_decision, lifecycle_state="rejected")
cases += [
    case("publication_fresh_cas_accepts", "publication_cas", publish_tx, None, {"current_revision": 1, "current_head": d("prior_owner_publication"), "existing_replay_key": None, "existing_coordinate": None, "existing_operation": None}),
    case("publish_operation_rejects_status_reason", "publication_cas", bad_publish_reason, "lifecycle_violation", {"current_revision": 1, "current_head": d("prior_owner_publication"), "existing_replay_key": None, "existing_coordinate": None, "existing_operation": None}),
    case("publication_stale_cas_rejected", "publication_cas", stale_tx, "publication_conflict", {"current_revision": 1, "current_head": d("prior_owner_publication"), "existing_replay_key": None, "existing_coordinate": None, "existing_operation": None}),
    case("publication_idempotent_replay_returns_existing", "publication_cas", replay_tx, None, {"current_revision": 2, "current_head": d("owner_publication"), "existing_replay_key": publish_tx["replay_key_digest"], "existing_coordinate": coordinate, "existing_operation": "publish"}),
    case("publication_fork_rejected", "publication_cas", fork_tx, "publication_fork", {"current_revision": 1, "current_head": d("prior_owner_publication"), "existing_replay_key": None, "existing_coordinate": None, "existing_operation": None}),
    case("namespace_version_digest_reuse_conflicts", "version_binding", version_reuse_tx, "version_conflict", {"existing_coordinate": coordinate}),
    case("publication_result_journal_marker_bind_exactly", "publication_commit", publication, None, publish_commit_context),
    case("publication_result_transaction_drift_rejected", "publication_commit", bad_publish_result, "lifecycle_violation", publish_commit_context),
    case("publication_journal_resulting_head_drift_rejected", "publication_commit", publication, "lifecycle_violation", {**publish_commit_context, "journal": bad_publish_journal_head}),
    case("withdrawal_transition_committed", "publication_transition", withdrawal, None, {"transaction": withdraw_tx, "journal": withdraw_journal, "marker": withdraw_marker, "prior_status": publication, "prior_journal_digest": d("publication_journal"), "prior_journal": publish_journal, "approval": withdraw_approval, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "decision": owner_decision, **owner_canonical_decision_context}),
    case("withdrawn_to_revoked_transition_committed", "publication_transition", revoked_publication, None, {"transaction": revoke_tx, "journal": revoke_journal, "marker": revoke_marker, "prior_status": withdrawal, "prior_journal_digest": d("withdraw_journal"), "prior_journal": withdraw_journal, "approval": revoke_approval, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "decision": owner_decision, **owner_canonical_decision_context, "canonical_publication_revision": withdrawal["ledger_revision"], "canonical_publication_head": withdrawal["publication_status_transition_digest"], "canonical_publication_journal_head": withdraw_journal["publication_journal_digest"]}),
    case("published_to_revoked_transition_committed", "publication_transition", direct_revocation, None, {"transaction": direct_revoke_tx, "journal": direct_revoke_journal, "marker": direct_revoke_marker, "prior_status": publication, "prior_journal_digest": d("publication_journal"), "prior_journal": publish_journal, "approval": direct_revoke_approval, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "decision": owner_decision, **owner_canonical_decision_context}),
    case("status_transition_link_drift_rejected", "publication_transition", bad_transition_link, "lifecycle_violation", {"transaction": withdraw_tx, "journal": withdraw_journal, "marker": withdraw_marker, "prior_status": publication, "prior_journal_digest": d("publication_journal"), "prior_journal": publish_journal, "approval": withdraw_approval, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "decision": owner_decision, **owner_canonical_decision_context}),
    case("status_transition_fabricated_prior_object_rejected", "publication_transition", withdrawal, "lifecycle_violation", {"transaction": withdraw_tx, "journal": withdraw_journal, "marker": withdraw_marker, "prior_status": variant(publication, status="published", ledger_revision=1), "prior_journal_digest": d("publication_journal"), "prior_journal": publish_journal, "approval": withdraw_approval, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "decision": owner_decision, **owner_canonical_decision_context}),
    case("status_transition_prior_journal_drift_rejected", "publication_transition", withdrawal, "lifecycle_violation", {"transaction": withdraw_tx, "journal": withdraw_journal, "marker": withdraw_marker, "prior_status": publication, "prior_journal_digest": raw("wrong-prior-journal"), "prior_journal": publish_journal, "approval": withdraw_approval, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "decision": owner_decision, **owner_canonical_decision_context}),
    case("withdraw_cannot_reuse_release_approval", "publication_transition", withdrawal, "lifecycle_violation", {"transaction": withdraw_tx, "journal": withdraw_journal, "marker": withdraw_marker, "prior_status": publication, "prior_journal_digest": d("publication_journal"), "prior_journal": publish_journal, "approval": owner_approval, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "decision": owner_decision, **owner_canonical_decision_context}),
    case("revoke_cannot_reuse_release_approval", "publication_transition", revoked_publication, "lifecycle_violation", {"transaction": revoke_tx, "journal": revoke_journal, "marker": revoke_marker, "prior_status": withdrawal, "prior_journal_digest": d("withdraw_journal"), "prior_journal": withdraw_journal, "approval": owner_approval, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "decision": owner_decision, **owner_canonical_decision_context, "canonical_publication_revision": withdrawal["ledger_revision"], "canonical_publication_head": withdrawal["publication_status_transition_digest"], "canonical_publication_journal_head": withdraw_journal["publication_journal_digest"]}),
    case("withdraw_approval_binds_exact_operation_reason_and_cas", "publication_transition", wrong_withdrawal, "lifecycle_violation", {"transaction": wrong_withdraw_tx, "journal": wrong_withdraw_journal, "marker": wrong_withdraw_marker, "prior_status": publication, "prior_journal_digest": d("publication_journal"), "prior_journal": publish_journal, "approval": wrong_withdraw_approval, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "decision": owner_decision, **owner_canonical_decision_context}),
    case("publication_prior_status_context_self_digest_checked", "publication_transition", withdrawal, "digest_mismatch", {"transaction": withdraw_tx, "journal": withdraw_journal, "marker": withdraw_marker, "prior_status": stale_prior_publication, "prior_journal_digest": d("publication_journal"), "prior_journal": publish_journal, "approval": withdraw_approval, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "decision": owner_decision, **owner_canonical_decision_context}),
    case("illegal_status_self_transition", "publication_transition", illegal_transition, "lifecycle_violation", {"transaction": withdraw_tx, "journal": withdraw_journal, "marker": withdraw_marker, "prior_status": publication, "prior_journal_digest": d("publication_journal"), "prior_journal": publish_journal, "approval": withdraw_approval, "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "decision": owner_decision, **owner_canonical_decision_context}, False),
    case("recovery_before_linearization_discards", "publication_recovery", prepared, None, publish_prepared_context),
    case("recovery_after_linearization_completes", "publication_recovery", committing, None, publish_recovery_context),
    case("withdrawal_recovery_after_linearization_completes", "publication_recovery", withdraw_recovery, None, withdraw_recovery_context),
    case("revocation_recovery_before_linearization_discards", "publication_recovery", revoke_prepared, None, revoke_recovery_context),
    case("aborted_transaction_discards_staging", "publication_recovery", aborted, None, aborted_recovery_context),
    case("recovery_before_linearization_must_not_move_head", "publication_recovery", prepared, "recovery_needed",
        {**publish_prepared_context, "after": variant(publish_prepared_after, state=publish_committing_after_state)}),
    case("recovery_after_linearization_requires_marker", "publication_recovery", committing, "recovery_needed",
        {**publish_recovery_context, "marker": None, "after": variant(publish_committing_after,
            state={**publish_committing_after_state, "durable_commit_marker_digest": None})}),
    case("recovery_marker_must_match_exact_journal_and_result", "publication_recovery", committing, "recovery_needed",
        {**publish_recovery_context, "after": variant(publish_committing_after,
            state={**publish_committing_after_state, "durable_commit_marker_digest": withdraw_marker["publication_commit_marker_digest"]}),
         "marker": withdraw_marker}),
    case("recovery_status_record_must_match_result", "publication_recovery", committing, "recovery_needed",
        {**publish_recovery_context, "after": variant(publish_committing_after,
            state={**publish_committing_after_state, "status_record_digest": raw("wrong-recovered-status")})}),
    case("recovery_resolves_complete_resulting_status_object", "publication_recovery", committing, "recovery_needed", {**publish_recovery_context, "resulting_status": major_publication}),
    case("recovery_result_context_self_digest_checked", "publication_recovery", committing, "digest_mismatch", {**publish_recovery_context, "resulting_status": stale_recovery_result}),
    case("recovery_prelinearization_rejects_durable_marker", "publication_recovery", prepared, "recovery_needed",
        {**publish_prepared_context, "marker": prepared_durable_marker}),
    case("recovery_prelinearization_requires_intent_descriptor", "publication_recovery", prepared, "self_certification",
        {**publish_prepared_context, "intent_marker": None}),
    case("recovery_intent_descriptor_cannot_claim_fsync", "publication_recovery", prepared, "malformed_input",
        {**publish_prepared_context, "intent_marker": fsynced_intent_descriptor}),
    case("recovery_intent_descriptor_owner_is_exact", "publication_recovery", prepared, "issuer_scope_violation",
        {**publish_prepared_context, "intent_marker": wrong_owner_intent_descriptor}),
    case("recovery_before_state_is_semantic_owner_issued", "publication_recovery", committing, "issuer_scope_violation",
        {**publish_recovery_context, "before": before_as_controller_receipt}),
    case("recovery_after_state_is_controller_issued", "publication_recovery", committing, "issuer_scope_violation",
        {**publish_recovery_context, "after": after_as_semantic_owner_receipt}),
    case("recovery_state_receipt_namespace_is_exact", "publication_recovery", committing, "recovery_needed",
        {**publish_recovery_context, "before": recovery_namespace_drift_before}),
    case("publication_recovery_current_journal_receipt_is_exact", "publication_recovery", committing, "recovery_needed",
        {**publish_recovery_context, "canonical_recovery_journal_head": raw("wrong-current-recovery-journal")}),
    case("publication_recovery_transition_expectation_is_exact", "publication_recovery", committing, "recovery_needed",
        {**publish_recovery_context, "canonical_recovery_resulting_head": raw("wrong-recovery-result-expectation")}),
    case("publication_recovery_calls_threshold_authority", "publication_recovery", committing, "recovery_needed",
        {**publish_recovery_context, "approval": recovery_insufficient_approval}),
    case("publication_recovery_calls_trust_authority", "publication_recovery", committing, "recovery_needed",
        {**publish_recovery_context, "trust_root": recovery_wrong_trust_root}),
    case("publication_recovery_calls_canonical_decision_authority", "publication_recovery", committing, "recovery_needed",
        {**publish_recovery_context, "decision": recovery_rejected_decision,
         "current_decision_record_digest": recovery_rejected_decision["decision_record_digest"]}),
    case("publication_recovery_calls_exact_action_authority", "publication_recovery", committing, "recovery_needed",
        {**publish_recovery_context, "expected_action": withdraw_approval["action"]}),
    case("publication_recovery_store_snapshot_head_drift_rejected", "publication_recovery", committing, "issuer_scope_violation", publish_recovery_context),
    case("publication_recovery_store_snapshot_revision_drift_rejected", "publication_recovery", committing, "issuer_scope_violation", publish_recovery_context),
    case("publication_recovery_store_snapshot_action_epoch_drift_rejected", "publication_recovery", committing, "issuer_scope_violation", publish_recovery_context),
    case("publication_recovery_store_snapshot_repository_drift_rejected", "publication_recovery", committing, "issuer_scope_violation", publish_recovery_context),
    case("publication_journal_shape_valid_tuple_non_authorizing", "publication_journal_shape", publish_journal, None),
    case("committed_without_linearization_rejected", "publication_journal_shape", variant(publish_journal, linearized=False), "recovery_needed")]

projection_context = {"projection": projection, "capsule": capsule, "archive_linkage": archive_link, "payload_manifest": payload,
    "consumer_manifest": consumer_manifest, "archive_manifest": archive_manifest, "tombstones": tombstones,
    "tombstone_history": tombstone_history, "canonical_lifecycle_tombstone_head": projection_lifecycle_tombstone_head}
bad_projection = variant(materialization, expected_consumer_manifest_digest=raw("other-consumer-tree"))
bad_archive = variant(materialization, capsule_archive_linkage_digest=raw("other-archive"))
projection_namespace_drift_head = {**projection_lifecycle_tombstone_head, "namespace": "other.space"}
projection_lifecycle_drift_head = {**projection_lifecycle_tombstone_head, "lifecycle_head_digest": raw("projection-wrong-lifecycle-head")}
projection_revision_drift_head = {**projection_lifecycle_tombstone_head, "tombstone_registry_revision": tombstones["registry_revision"] + 1}
projection_coordinate_drift_receipt = variant(materialization, coordinate=predecessor)
projection_capsule_revision_drift = variant(capsule, tombstone_registry_revision=capsule["tombstone_registry_revision"] + 1)
projection_capsule_revision_coordinate = {"schema": "semantic-release-coordinate.v0", "namespace": projection_capsule_revision_drift["namespace"],
    "semantic_version": projection_capsule_revision_drift["semantic_version"], "capsule_digest": projection_capsule_revision_drift["capsule_digest"]}
projection_capsule_revision_receipt = variant(materialization, coordinate=projection_capsule_revision_coordinate)
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
    case("projection_stale_tombstone_registry_rejected", "projection", materialization, "projection_mismatch",
        {**projection_context, "canonical_lifecycle_tombstone_head": reuse_lifecycle_tombstone_head}),
    case("projection_capsule_semantic_owner_substitution_rejected", "projection", materialization, "issuer_scope_violation", projection_context),
    case("projection_rocs_proof_owner_substitution_rejected", "projection", materialization, "issuer_scope_violation", projection_context),
    case("projection_namespace_currentness_rejected", "projection", materialization, "projection_mismatch",
        {**projection_context, "canonical_lifecycle_tombstone_head": projection_namespace_drift_head}),
    case("projection_lifecycle_head_currentness_rejected", "projection", materialization, "projection_mismatch",
        {**projection_context, "canonical_lifecycle_tombstone_head": projection_lifecycle_drift_head}),
    case("projection_registry_revision_currentness_rejected", "projection", materialization, "projection_mismatch",
        {**projection_context, "canonical_lifecycle_tombstone_head": projection_revision_drift_head}),
    case("projection_complete_tombstone_history_required", "projection", materialization, "projection_mismatch",
        {**projection_context, "tombstone_history": variant(tombstone_history, revisions=copy.deepcopy(tombstone_history["revisions"][1:]))}),
    case("projection_materialization_coordinate_equals_capsule_coordinate", "projection", projection_coordinate_drift_receipt, "projection_mismatch", projection_context),
    case("projection_capsule_tombstone_revision_is_exact", "projection", projection_capsule_revision_receipt, "projection_mismatch",
        {**projection_context, "capsule": projection_capsule_revision_drift}),
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
    "canonical_history_head": activation_head, "previous_activation": None, "ak_linkage": None, "pi_receipt": None,
    **technical_context, **canonical_decision_context, **activation_authority_facts}
def rollback_context(request: dict, proof: dict, history_after: dict | None = None, **extra: object) -> dict:
    kind = request["target"]["kind"]
    artifacts = {"semantic_artifact": semantic_available_artifact, "runtime_artifact": runtime_available_artifact,
        "disable_artifact": disable_available_artifact, "recovery_artifact": recovery_available_artifact}
    return {**rollback_common, "request": request, "availability": proof, "activation_availability": semantic_availability, "history_after": history_after, **artifacts, **extra}
semantic_rollback_context = rollback_context(semantic_request, semantic_availability, semantic_history, ak_linkage=ak_link, pi_receipt=pi_delivered)
def bound_rollback_chain(request_value: dict, proof_value: dict, history_value: dict, receipt_value: dict) -> tuple[dict, dict, dict, dict, dict]:
    target = request_value["target"]
    bound_intent = variant(intent, rollback_target=target)
    bound_acceptance = variant(acceptance, consumer_intent_digest=bound_intent["consumer_intent_digest"])
    bound_materialization = variant(materialization, consumer_intent_digest=bound_intent["consumer_intent_digest"],
        owner_acceptance_digest=bound_acceptance["owner_acceptance_digest"], rollback_target=target)
    bound_proof = variant(proof_value, consumer_intent_digest=bound_intent["consumer_intent_digest"],
        owner_acceptance_digest=bound_acceptance["owner_acceptance_digest"],
        materialization_verification_receipt_digest=bound_materialization["materialization_verification_receipt_digest"])
    bound_activation = variant(activation, consumer_intent_digest=bound_intent["consumer_intent_digest"],
        owner_acceptance_digest=bound_acceptance["owner_acceptance_digest"],
        materialization_verification_receipt_digest=bound_materialization["materialization_verification_receipt_digest"],
        rollback_availability_proof_digest=bound_proof["rollback_availability_proof_digest"])
    bound_request = variant(request_value, active_activation_receipt_digest=bound_activation["activation_receipt_digest"])
    prior_head = {"kind": "activation", "digest": bound_activation["activation_receipt_digest"]}
    supersedes = bound_activation["activation_receipt_digest"] if history_value["supersedes_activation_receipt_digest"] is not None else None
    bound_history = variant(history_value, rollback_request_digest=bound_request["rollback_request_digest"], history_head_before=prior_head,
        supersedes_activation_receipt_digest=supersedes)
    after_kind = "disable" if target["kind"] == "no_prior_disable" else "rollback"
    bound_receipt = variant(receipt_value, rollback_request_digest=bound_request["rollback_request_digest"],
        availability_proof_digest=bound_proof["rollback_availability_proof_digest"], history_head_before=prior_head,
        history_head_after={"kind": after_kind, "digest": bound_history["rollback_history_transition_digest"]},
        supersedes_activation_receipt_digest=supersedes)
    bound_context = rollback_context(bound_request, bound_proof, bound_history, activation=bound_activation, intent=bound_intent,
        acceptance=bound_acceptance, materialization=bound_materialization, current_activation_digest=bound_activation["activation_receipt_digest"],
        canonical_history_head=prior_head, activation_availability=bound_proof,
        current_acceptance_digest=bound_acceptance["owner_acceptance_digest"],
        current_acceptance_revision=bound_acceptance["acceptance_revision"])
    return bound_request, bound_proof, bound_history, bound_receipt, bound_context

runtime_bound_request, runtime_bound_proof, runtime_bound_history, runtime_bound_receipt, runtime_bound_context = bound_rollback_chain(runtime_request, runtime_availability, runtime_history, runtime_receipt)
disable_bound_request, disable_bound_proof, disable_bound_history, disable_bound_receipt, disable_bound_context = bound_rollback_chain(disable_request, disable_availability, disable_history, disable_receipt)
partial_bound_request, combined_bound_proof, partial_bound_history, partial_bound_receipt, partial_bound_context = bound_rollback_chain(combined_request, combined_availability, partial_history, partial_receipt)
success_bound_request, success_bound_proof, success_bound_history, success_bound_receipt, success_bound_context = bound_rollback_chain(combined_request, combined_availability, combined_success_history, combined_success)
disable_contract_subject_drift = variant(disable_contract_receipt, subject_digest=raw("wrong-disable-contract-subject"))
disable_rehearsal_subject_drift = variant(disable_rehearsal, subject_digest=raw("wrong-disable-rehearsal-subject"))
disable_contract_coordinate_drift = variant(disable_contract_receipt, coordinate=coordinate)
disable_rehearsal_coordinate_drift = variant(disable_rehearsal, coordinate=coordinate)
disable_contract_runtime_drift = variant(disable_contract_receipt, runtime_identity=old_runtime)
disable_rehearsal_runtime_drift = variant(disable_rehearsal, runtime_identity=old_runtime)

cases += [
    case("semantic_rollback_retains_runtime", "rollback", semantic_receipt, None, semantic_rollback_context),
    case("runtime_rollback_retains_semantic_and_revalidates", "rollback", runtime_bound_receipt, None, runtime_bound_context),
    case("runtime_rollback_without_revalidation_rejected", "rollback", runtime_missing, "rollback_unavailable", rollback_context(runtime_missing, runtime_availability), False),
    case("no_prior_disable_clears_semantic", "rollback", disable_bound_receipt, None, disable_bound_context),
    case("disable_contract_subject_must_match_rollback_plan", "rollback", disable_bound_receipt, "rollback_unavailable",
        {**disable_bound_context, "disable_contract_technical": disable_contract_subject_drift}),
    case("disable_rehearsal_subject_must_match_contract", "rollback", disable_bound_receipt, "rollback_unavailable",
        {**disable_bound_context, "disable_rehearsal_technical": disable_rehearsal_subject_drift}),
    case("disable_contract_coordinate_must_be_null", "rollback", disable_bound_receipt, "rollback_unavailable",
        {**disable_bound_context, "disable_contract_technical": disable_contract_coordinate_drift}),
    case("disable_rehearsal_coordinate_must_be_null", "rollback", disable_bound_receipt, "rollback_unavailable",
        {**disable_bound_context, "disable_rehearsal_technical": disable_rehearsal_coordinate_drift}),
    case("disable_contract_runtime_must_match_active_runtime", "rollback", disable_bound_receipt, "rollback_unavailable",
        {**disable_bound_context, "disable_contract_technical": disable_contract_runtime_drift}),
    case("disable_rehearsal_runtime_must_match_active_runtime", "rollback", disable_bound_receipt, "rollback_unavailable",
        {**disable_bound_context, "disable_rehearsal_technical": disable_rehearsal_runtime_drift}),
    case("disable_that_leaves_semantic_active_rejected", "rollback", variant(disable_bound_receipt, active_state_after={"enabled": True, "coordinate": coordinate, "runtime_identity": rocs_tool}), "history_conflict", disable_bound_context),
    case("combined_partial_failure_records_stages", "rollback", partial_bound_receipt, None, partial_bound_context),
    case("combined_full_success_records_order_and_revalidation", "rollback", success_bound_receipt, None, success_bound_context),
    case("partial_failure_without_failed_stage_rejected", "rollback", variant(partial_bound_receipt, stages=[{"stage": "semantic", "result": "completed", "error_digest": None}, {"stage": "runtime", "result": "completed", "error_digest": None}], failure_stage=None, error_digest=None), "history_conflict", partial_bound_context),
    case("rollback_optional_ak_pi_crosslinks_exact", "rollback", bad_rollback_pi_link, "history_conflict", semantic_rollback_context),
    case("rollback_request_digest_drift_rejected", "rollback", bad_request_digest, "history_conflict", rollback_context(semantic_request, semantic_availability, semantic_history)),
    case("rollback_request_from_activation_drift_rejected", "rollback", bad_request_from_state_receipt, "rollback_unavailable", rollback_context(bad_request_from_state, semantic_availability, semantic_history)),
    case("rollback_from_state_drift_rejected", "rollback", bad_before, "history_conflict", rollback_context(semantic_request, semantic_availability, semantic_history)),
    case("rollback_result_target_mismatch_rejected", "rollback", variant(disable_bound_receipt, result="rolled_back", history_head_after={"kind": "rollback", "digest": raw("wrong-result-head")}), "history_conflict", disable_bound_context),
    case("combined_stage_order_drift_rejected", "rollback", variant(partial_bound_receipt, stages=list(reversed(partial_bound_receipt["stages"]))), "history_conflict", partial_bound_context),
    case("completed_stage_error_rejected", "rollback", bad_completed_error, "history_conflict", rollback_context(semantic_request, semantic_availability, semantic_history)),
    case("disable_must_retain_runtime", "rollback", variant(disable_bound_receipt, active_state_after={"enabled": False, "coordinate": None, "runtime_identity": old_runtime}), "history_conflict", disable_bound_context),
    case("runtime_revalidation_binding_drift_rejected", "rollback", variant(runtime_bound_receipt, runtime_revalidation_receipt_digest=raw("wrong-revalidation")), "rollback_unavailable", runtime_bound_context),
    case("partial_failure_must_not_supersede_activation", "rollback", variant(partial_bound_receipt, supersedes_activation_receipt_digest=partial_bound_context["current_activation_digest"]), "history_conflict", partial_bound_context),
    case("failed_rollback_preserves_state_and_typed_head", "rollback", failed_receipt, None, rollback_context(semantic_request, semantic_availability)),
    case("failed_rollback_requires_failed_stage", "rollback", bad_failed_stage, "history_conflict", rollback_context(semantic_request, semantic_availability)),
    case("failed_rollback_changed_state_rejected", "rollback", bad_failed_state, "history_conflict", rollback_context(semantic_request, semantic_availability)),
    case("failed_rollback_changed_history_rejected", "rollback", bad_failed_history, "history_conflict", rollback_context(semantic_request, semantic_availability)),
    case("rollback_requires_canonical_current_activation_object", "rollback", semantic_receipt, "rollback_unavailable", {**semantic_rollback_context, "activation": substituted_activation}),
    case("rollback_requires_concrete_target_and_recovery_availability", "rollback", semantic_receipt, "rollback_unavailable", rollback_context(semantic_request, semantic_availability, semantic_history, semantic_artifact=wrong_semantic_available_artifact)),
    case("rollback_target_artifact_self_digest_checked", "rollback", semantic_receipt, "digest_mismatch", rollback_context(semantic_request, semantic_availability, semantic_history, semantic_artifact=stale_semantic_available_artifact)),
    case("rollback_recovery_artifact_resolved_exactly", "rollback", semantic_receipt, "rollback_unavailable", rollback_context(semantic_request, semantic_availability, semantic_history, recovery_artifact=wrong_recovery_available_artifact)),
    case("rollback_before_head_must_equal_canonical_head", "rollback", fabricated_before_head, "history_conflict", rollback_context(semantic_request, semantic_availability, semantic_history)),
    case("rollback_cannot_complete_stage_after_failure", "rollback", variant(partial_bound_receipt, stages=[{"stage": "semantic", "result": "failed", "error_digest": raw("first-stage-failed")}, {"stage": "runtime", "result": "completed", "error_digest": None}], failure_stage="semantic", error_digest=raw("first-stage-failed"), active_state_after={"enabled": True, "coordinate": coordinate, "runtime_identity": old_runtime}), "history_conflict", partial_bound_context),
    case("rollback_error_must_equal_failed_stage_cause", "rollback", variant(partial_bound_receipt, error_digest=raw("unrelated-overall-error")), "history_conflict", partial_bound_context),
    case("rollback_history_head_must_bind_typed_transition", "rollback", semantic_receipt, "history_conflict", rollback_context(semantic_request, semantic_availability, runtime_history)),
    case("issuer_scope_checked_before_subject_rule", "rollback", wrong_issuer_failed, "issuer_scope_violation", rollback_context(semantic_request, semantic_availability))]

revoked_activation = variant(activation, revoked_by_digest=raw("activation-revocation"))
superseded_activation = variant(activation, superseded_by_activation_receipt_digest=raw("new-activation"))
bad_generation_coordinate = variant(generation, coordinate=predecessor)
bad_generation_runtime = variant(generation, runtime_identity=old_runtime)
activation_context = {"activation": activation, "intent": intent, "acceptance": acceptance, "materialization": materialization, "decision": consumer_decision,
    "current_activation_digest": d("activation_receipt"), "current_activation_revision": 1, "availability": semantic_availability,
    "activation_availability": semantic_availability, "previous_activation": None, **technical_context, **canonical_decision_context, **activation_authority_facts}
activation_binding_context = {key: copy.deepcopy(value) for key, value in activation_context.items() if key != "activation"}
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
wrong_scope_acceptance = variant(acceptance, canary_scope={**canary_scope, "operator_canary_name": "operator-canary-beta"})
other_consumer_repo = {**consumer_repo, "repository_id": "other-consumer"}
wrong_consumer_repository_acceptance = variant(acceptance, consumer_repository=other_consumer_repo,
    canary_scope={**canary_scope, "consumer_repository": other_consumer_repo})
wrong_consumer_revision_acceptance = variant(acceptance, consumer_repository={**consumer_repo, "identity_revision": 4},
    canary_scope={**canary_scope, "consumer_repository": {**consumer_repo, "identity_revision": 4}})
wrong_consumer_locator_acceptance = variant(acceptance,
    consumer_repository={**consumer_repo, "canonical_locator": "local://softwareco/other-consumer"},
    canary_scope={**canary_scope, "consumer_repository": {**consumer_repo, "canonical_locator": "local://softwareco/other-consumer"}})
wrong_canary_cardinality_acceptance = variant(acceptance, canary_scope={**canary_scope, "canary_cardinality": 2})
wrong_canary_naming_authority_acceptance = variant(acceptance, canary_scope={**canary_scope, "naming_authority": "consumer_owner"})
wrong_scope_expansion_authority_acceptance = variant(acceptance,
    canary_scope={**canary_scope, "expansion_authority": "existing_protocol_reuse"})
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
wrong_stop_semantic_contract = copy.deepcopy(consumer_canary_contract); wrong_stop_semantic_contract["stop_conditions"][0]["condition_kind"] = "protocol_scope_expansion"; rehash(wrong_stop_semantic_contract)
cases += [
    case("non_authorizing_separate_coordination_and_consumer_contracts", "governance_contracts", ak_coordination_contract, None, {"consumer_contract": consumer_canary_contract, "canonical_task_states": []}),
    case("ak_coordination_contract_cannot_authorize_execution", "governance_contracts", authorized_coordination_contract, "self_certification", {"consumer_contract": consumer_canary_contract, "canonical_task_states": []}),
    case("coordination_and_consumer_tasks_cannot_be_conflated", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": conflated_consumer_contract, "canonical_task_states": []}),
    case("single_canary_consumer_allowed_paths_are_exact", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": missing_consumer_path_contract, "canonical_task_states": []}),
    case("task_contract_binds_exact_task_id", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": substituted_task_id_contract, "canonical_task_states": []}),
    case("task_contract_binds_exact_owner_id", "governance_contracts", ak_coordination_contract, "issuer_scope_violation", {"consumer_contract": substituted_owner_contract, "canonical_task_states": []}),
    case("task_contract_binds_exact_rollback_owner_id", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": substituted_rollback_owner_contract, "canonical_task_states": []}),
    case("task_contract_binds_exact_evidence_list", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": substituted_evidence_contract, "canonical_task_states": []}),
    case("task_contract_binds_exact_stop_conditions", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": substituted_stop_contract, "canonical_task_states": []}),
    case("task_contract_binds_exact_dependency_ids", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": substituted_dependency_contract, "canonical_task_states": []}),
    case("task_contract_binds_exact_prerequisite_ids", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": substituted_prerequisite_id_contract, "canonical_task_states": []}),
    case("task_contract_rejects_synthetic_future_artifact_digest", "governance_contracts", ak_coordination_contract, "malformed_input", {"consumer_contract": substituted_prerequisite_digest_contract, "canonical_task_states": []}),
    case("task_contract_binds_required_reference_state", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": wrong_prerequisite_state_contract, "canonical_task_states": []}),
    case("task_contract_machine_binds_stop_semantics", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": wrong_stop_semantic_contract, "canonical_task_states": []}),
    case("python_integer_cannot_satisfy_boolean_const", "pi_variant", bool_satisfies_true_const, "malformed_input", schema_valid=False),
    case("python_boolean_cannot_satisfy_integer_type", "pi_variant", bool_satisfies_integer_type, "malformed_input", schema_valid=False),
    case("arbitrary_length_semver_compares_without_number_precision_loss", "compatibility", large_semver_report, None, {**compatibility_non_override_context, "prior_version": large_prior_semver}),
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
    case("acceptance_owner_scope_binding_exact", "acceptance_binding", acceptance, None, {"decision": consumer_decision, "intent": intent, **canonical_decision_context, **acceptance_authority_facts}),
    case("v0_consumer_repository_is_exact", "acceptance_binding", wrong_consumer_repository_acceptance, "malformed_input",
        {"decision": consumer_decision, "intent": intent, **canonical_decision_context, **acceptance_authority_facts}, schema_valid=False),
    case("v0_consumer_identity_revision_three_is_exact", "acceptance_binding", wrong_consumer_revision_acceptance, "malformed_input",
        {"decision": consumer_decision, "intent": intent, **canonical_decision_context, **acceptance_authority_facts}, schema_valid=False),
    case("v0_consumer_locator_is_exact", "acceptance_binding", wrong_consumer_locator_acceptance, "malformed_input",
        {"decision": consumer_decision, "intent": intent, **canonical_decision_context, **acceptance_authority_facts}, schema_valid=False),
    case("v0_canary_cardinality_is_exactly_one", "acceptance_binding", wrong_canary_cardinality_acceptance, "malformed_input",
        {"decision": consumer_decision, "intent": intent, **canonical_decision_context, **acceptance_authority_facts}, schema_valid=False),
    case("v0_canary_name_requires_operator_authority", "acceptance_binding", wrong_canary_naming_authority_acceptance, "malformed_input",
        {"decision": consumer_decision, "intent": intent, **canonical_decision_context, **acceptance_authority_facts}, schema_valid=False),
    case("v0_scope_expansion_requires_new_protocol_and_decision", "acceptance_binding", wrong_scope_expansion_authority_acceptance, "malformed_input",
        {"decision": consumer_decision, "intent": intent, **canonical_decision_context, **acceptance_authority_facts}, schema_valid=False),
    case("acceptance_scope_drift_rejected", "acceptance_binding", bad_acceptance_scope, "self_certification", {"decision": consumer_decision, "intent": intent, **canonical_decision_context, **acceptance_authority_facts}),
    case("rocs_cannot_self_certify_acceptance", "acceptance_binding", self_acceptance, "issuer_scope_violation", {"decision": consumer_decision, "intent": intent, **canonical_decision_context, **acceptance_authority_facts}),
    case("activation_decision_bindings_exact", "activation_binding", activation, None, {"decision": consumer_decision, "intent": intent, "acceptance": acceptance, "materialization": materialization, "availability": semantic_availability, **technical_context, **canonical_decision_context, **activation_authority_facts, "activation_availability": semantic_availability, "previous_activation": None, "current_activation_digest": None, "current_activation_revision": None}),
    case("activation_stop_binding_drift_rejected", "activation_binding", bad_activation_binding, "self_certification", {"decision": consumer_decision, "intent": intent, "acceptance": acceptance, "materialization": materialization, "availability": semantic_availability, **technical_context, **canonical_decision_context, **activation_authority_facts, "activation_availability": semantic_availability, "previous_activation": None, "current_activation_digest": None, "current_activation_revision": None}),
    case("activation_resolves_acceptance_self_digest", "activation_binding", activation, "digest_mismatch", {"decision": consumer_decision, "intent": intent, "acceptance": stale_acceptance_context, "materialization": materialization, "availability": semantic_availability, **technical_context, **canonical_decision_context, **activation_authority_facts, "activation_availability": semantic_availability, "previous_activation": None, "current_activation_digest": None, "current_activation_revision": None}),
    case("activation_requires_valid_intent_revision", "activation_binding", activation, "self_certification", {"decision": consumer_decision, "intent": intent, "acceptance": expired_intent_acceptance, "materialization": materialization, "availability": semantic_availability, **technical_context, **canonical_decision_context, **activation_authority_facts, "activation_availability": semantic_availability, "previous_activation": None, "current_activation_digest": None, "current_activation_revision": None}),
    case("activation_epoch_respects_acceptance_ceiling", "activation_binding", activation, "self_certification", {"decision": consumer_decision, "intent": intent, "acceptance": low_epoch_acceptance, "materialization": materialization, "availability": semantic_availability, **technical_context, **canonical_decision_context, **activation_authority_facts, "activation_availability": semantic_availability, "previous_activation": None, "current_activation_digest": None, "current_activation_revision": None}),
    case("activation_canary_scope_matches_intent_and_acceptance", "activation_binding", activation, "self_certification", {"decision": consumer_decision, "intent": intent, "acceptance": wrong_scope_acceptance, "materialization": materialization, "availability": semantic_availability, **technical_context, **canonical_decision_context, **activation_authority_facts, "activation_availability": semantic_availability, "previous_activation": None, "current_activation_digest": None, "current_activation_revision": None}),
    case("activation_materialization_coordinate_runtime_chain_exact", "activation_binding", activation, "self_certification", {"decision": consumer_decision, "intent": intent, "acceptance": acceptance, "materialization": drifting_materialization, "availability": semantic_availability, **technical_context, **canonical_decision_context, **activation_authority_facts, "activation_availability": semantic_availability, "previous_activation": None, "current_activation_digest": None, "current_activation_revision": None}),
    case("activation_context_issuer_checked_before_relation", "activation_binding", activation, "issuer_scope_violation", {"decision": consumer_decision, "intent": intent, "acceptance": acceptance, "materialization": wrong_issuer_materialization, "availability": semantic_availability, **technical_context, **canonical_decision_context, **activation_authority_facts, "activation_availability": semantic_availability, "previous_activation": None, "current_activation_digest": None, "current_activation_revision": None}),
    case("activation_requires_current_decision_record", "activation_binding", activation, "self_certification", {"decision": stale_store_decision, "intent": intent, "acceptance": acceptance, "materialization": materialization, "availability": semantic_availability, **technical_context, **canonical_decision_context, **activation_authority_facts, "activation_availability": semantic_availability, "previous_activation": None, "current_activation_digest": None, "current_activation_revision": None}),
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
    "owner_set": owner_set, "predicate": predicate, "trust_root": trust_root, "external_trust_root_pin": external_trust_root_pin,
    "decision": rejected_owner_decision, "canonical_store_head": ak_store_head,
    "current_decision_record_digest": rejected_owner_decision["decision_record_digest"], **trust_authority_facts,
    "canonical_publication_revision": publication["ledger_revision"], "canonical_publication_head": publication["owner_publication_digest"],
    "canonical_publication_journal_head": publish_journal["publication_journal_digest"]}
prior_journal_result_drift = variant(prior_publish_journal, resulting_record_digest=raw("wrong-prior-result"))
recovery_result_transaction_drift = variant(publication, transaction_digest=raw("other-recovery-transaction"))
recovery_transaction_journal = variant(committing, resulting_record_digest=recovery_result_transaction_drift["owner_publication_digest"],
    resulting_ledger_head_digest=recovery_result_transaction_drift["owner_publication_digest"])
recovery_transaction_intent = variant(committing_intent, journal_digest=recovery_transaction_journal["publication_journal_digest"],
    resulting_record_digest=recovery_result_transaction_drift["owner_publication_digest"],
    resulting_ledger_head_digest=recovery_result_transaction_drift["owner_publication_digest"])
recovery_transaction_marker = variant(committing_marker, journal_digest=recovery_transaction_journal["publication_journal_digest"],
    resulting_record_digest=recovery_result_transaction_drift["owner_publication_digest"],
    resulting_ledger_head_digest=recovery_result_transaction_drift["owner_publication_digest"])
recovery_transaction_before = variant(publish_committing_before, recovery_journal_digest=recovery_transaction_journal["publication_journal_digest"],
    state={**publish_committing_before_state, "intent_marker_digest": recovery_transaction_intent["publication_recovery_intent_marker_digest"]})
recovery_transaction_after = variant(publish_committing_after, recovery_journal_digest=recovery_transaction_journal["publication_journal_digest"],
    state={**publish_committing_after_state, "head": recovery_result_transaction_drift["owner_publication_digest"],
        "status_record_digest": recovery_result_transaction_drift["owner_publication_digest"],
        "durable_commit_marker_digest": recovery_transaction_marker["publication_commit_marker_digest"]})
recovery_transaction_context = recovery_context(recovery_transaction_journal, recovery_transaction_before,
    recovery_transaction_after, recovery_transaction_intent, recovery_transaction_marker, publish_tx,
    recovery_result_transaction_drift, prior_publication, prior_publish_journal, owner_approval, release_action)

recovery_result_coordinate_drift = variant(publication, coordinate=predecessor)
recovery_coordinate_journal = variant(committing, resulting_record_digest=recovery_result_coordinate_drift["owner_publication_digest"],
    resulting_ledger_head_digest=recovery_result_coordinate_drift["owner_publication_digest"])
recovery_coordinate_intent = variant(committing_intent, journal_digest=recovery_coordinate_journal["publication_journal_digest"],
    resulting_record_digest=recovery_result_coordinate_drift["owner_publication_digest"],
    resulting_ledger_head_digest=recovery_result_coordinate_drift["owner_publication_digest"])
recovery_coordinate_marker = variant(committing_marker, journal_digest=recovery_coordinate_journal["publication_journal_digest"],
    resulting_record_digest=recovery_result_coordinate_drift["owner_publication_digest"],
    resulting_ledger_head_digest=recovery_result_coordinate_drift["owner_publication_digest"])
recovery_coordinate_before = variant(publish_committing_before, recovery_journal_digest=recovery_coordinate_journal["publication_journal_digest"],
    state={**publish_committing_before_state, "intent_marker_digest": recovery_coordinate_intent["publication_recovery_intent_marker_digest"]})
recovery_coordinate_after = variant(publish_committing_after, recovery_journal_digest=recovery_coordinate_journal["publication_journal_digest"],
    state={**publish_committing_after_state, "head": recovery_result_coordinate_drift["owner_publication_digest"],
        "status_record_digest": recovery_result_coordinate_drift["owner_publication_digest"],
        "durable_commit_marker_digest": recovery_coordinate_marker["publication_commit_marker_digest"]})
recovery_coordinate_context = recovery_context(recovery_coordinate_journal, recovery_coordinate_before, recovery_coordinate_after,
    recovery_coordinate_intent, recovery_coordinate_marker, publish_tx, recovery_result_coordinate_drift,
    prior_publication, prior_publish_journal, owner_approval, release_action)

recovery_prior_status_drift = variant(prior_publication, transaction_digest=raw("recovery-wrong-prior-transaction"))
recovery_prior_journal_drift = variant(prior_publish_journal, resulting_ledger_revision=0)
recovery_prior_journal_subject = variant(committing, prior_journal_digest=recovery_prior_journal_drift["publication_journal_digest"])
recovery_prior_journal_intent = variant(committing_intent, journal_digest=recovery_prior_journal_subject["publication_journal_digest"])
recovery_prior_journal_marker = variant(committing_marker, journal_digest=recovery_prior_journal_subject["publication_journal_digest"])
recovery_prior_journal_before = variant(publish_committing_before,
    recovery_journal_digest=recovery_prior_journal_subject["publication_journal_digest"],
    state={**publish_committing_before_state, "intent_marker_digest": recovery_prior_journal_intent["publication_recovery_intent_marker_digest"]})
recovery_prior_journal_after = variant(publish_committing_after,
    recovery_journal_digest=recovery_prior_journal_subject["publication_journal_digest"],
    state={**publish_committing_after_state, "durable_commit_marker_digest": recovery_prior_journal_marker["publication_commit_marker_digest"]})
recovery_prior_journal_context = recovery_context(recovery_prior_journal_subject, recovery_prior_journal_before,
    recovery_prior_journal_after, recovery_prior_journal_intent, recovery_prior_journal_marker, publish_tx,
    publication, prior_publication, recovery_prior_journal_drift, owner_approval, release_action)
self_certified_dep_pub = variant(publication, transaction_digest=raw("self-certified-publication-transaction"))
self_certified_dep_canonical = variant(dep_canonical_ledger, ledger_head_digest=self_certified_dep_pub["owner_publication_digest"], status_record_digest=self_certified_dep_pub["owner_publication_digest"])
self_certified_dep_ledger = variant(deprecation_ledger, ledger_head_digest=self_certified_dep_pub["owner_publication_digest"], publication_status_record_digest=self_certified_dep_pub["owner_publication_digest"], canonical_ledger_digest=self_certified_dep_canonical["publication_ledger_head_digest"])
self_certified_lifecycle_context = {**lifecycle_context, "deprecation_publication": self_certified_dep_pub, "deprecation_ledger": self_certified_dep_ledger,
    "deprecation_canonical_ledger": self_certified_dep_canonical, "canonical_deprecation_head": self_certified_dep_pub["owner_publication_digest"]}
wrong_availability_issuer = variant(semantic_available_artifact, issuer={"kind": "recovery_controller", "id": "recovery"})
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
bool_current_revision_context = {"current_revision": True, "current_head": publish_tx["expected_prior_head_digest"], "existing_replay_key": None, "existing_coordinate": None, "existing_operation": None}
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
    case("recovery_result_transaction_binds_transaction", "publication_recovery", recovery_transaction_journal, "recovery_needed",
        recovery_transaction_context),
    case("publication_recovery_result_coordinate_join_is_exact", "publication_recovery", recovery_coordinate_journal, "recovery_needed",
        recovery_coordinate_context),
    case("publication_recovery_before_status_is_canonical", "publication_recovery", committing, "recovery_needed",
        {**publish_recovery_context, "prior_status": recovery_prior_status_drift}),
    case("publication_recovery_prior_journal_full_join_is_exact", "publication_recovery", recovery_prior_journal_subject, "recovery_needed",
        recovery_prior_journal_context),
    case("publication_recovery_null_transaction_rejected", "publication_recovery", committing, "self_certification",
        {**publish_recovery_context, "transaction": None}),
    case("publication_recovery_null_result_rejected", "publication_recovery", committing, "self_certification",
        {**publish_recovery_context, "resulting_status": None}),
    case("publication_recovery_null_marker_rejected", "publication_recovery", committing, "recovery_needed",
        {**publish_recovery_context, "marker": None}),
    case("publication_recovery_null_before_rejected", "publication_recovery", committing, "self_certification",
        {**publish_recovery_context, "before": None}),
    case("publication_recovery_null_after_rejected", "publication_recovery", committing, "self_certification",
        {**publish_recovery_context, "after": None}),
    case("lifecycle_endpoint_cannot_self_certify_publication", "lifecycle", removal, "lifecycle_violation", self_certified_lifecycle_context),
    case("rollback_availability_receipt_requires_issuer", "rollback", semantic_receipt, "issuer_scope_violation", rollback_context(semantic_request, semantic_availability, semantic_history, semantic_artifact=wrong_availability_issuer)),
    case("rollback_resolves_typed_materialization_receipt_issuer", "rollback", semantic_receipt, "issuer_scope_violation", rollback_context(semantic_request, semantic_availability, semantic_history, semantic_materialization_technical=wrong_materialization_technical_issuer)),
    case("rollback_binds_technical_receipt_issuer_id", "rollback", semantic_receipt, "issuer_scope_violation", rollback_context(semantic_request, semantic_availability, semantic_history, semantic_materialization_technical=wrong_materialization_technical_id)),
    case("activation_prior_plus_one_transition_accepts", "activation_binding", next_activation, None, {**activation_binding_context, "current_activation_digest": d("activation_receipt"), "current_activation_revision": 1, "previous_activation": activation}),
    case("activation_current_head_equals_exact_prior", "activation_binding", next_activation_head_drift, "self_certification", {**activation_binding_context, "current_activation_digest": d("activation_receipt"), "current_activation_revision": 1, "previous_activation": activation}),
    case("activation_binds_consumer_owner_issuer_id", "activation_binding", activation_issuer_id_substitution, "self_certification", {**activation_binding_context, "current_activation_digest": None, "current_activation_revision": None}),
    case("activation_revision_requires_genesis_or_prior_plus_one", "activation_binding", activation_revision_skip, "self_certification", {**activation_binding_context, "current_activation_digest": None, "current_activation_revision": None}),
    case("activation_epoch_is_monotonic_from_acceptance", "activation_binding", activation_epoch_before_acceptance, "self_certification", {**activation_binding_context, "current_activation_digest": None, "current_activation_revision": None}),
    case("activation_binds_concrete_rollback_availability", "activation_binding", activation_availability_drift, "rollback_unavailable", {**activation_binding_context, "current_activation_digest": None, "current_activation_revision": None}),
    case("primitive_context_integer_rejects_boolean", "publication_cas", publish_tx, "malformed_input", bool_current_revision_context),
    case("semver_subject_requires_exact_full_grammar", "pi_variant", malformed_semver_subject, "malformed_input", schema_valid=False),
    case("semver_context_requires_exact_full_grammar", "compatibility", compat_report, "malformed_input", {**compatibility_non_override_context, "prior_version": "1.0.0junk"}),
    case("approval_map_key_equals_value_digest", "compatibility", overridden_report, "digest_mismatch", approval_key_drift_context),
    case("unresolved_candidate_cannot_claim_synthetic_task_artifacts", "governance_contracts", ak_coordination_contract, "malformed_input", {"consumer_contract": synthetic_resolved_dependency, "canonical_task_states": []})]

# Revision-v7 direct negatives for every revision-v6 false accept.
missing_canonical_head_context = {k: v for k, v in publish_commit_context.items() if k != "canonical_store_head"}
missing_current_record_context = {k: v for k, v in publish_commit_context.items() if k != "current_decision_record_digest"}
wrong_namespace_root = variant(trust_root, namespace="other.space")
wrong_policy_root = variant(trust_root, owner_policy_digest=raw("wrong-root-policy"))
wrong_set_root = variant(trust_root, owner_set_digest=raw("wrong-root-set"))
wrong_external_pin = {**external_trust_root_pin, "trust_root_digest": raw("wrong-external-root-pin")}
prior_journal_transaction_drift = variant(prior_publish_journal, transaction_digest=raw("wrong-prior-status-transaction"))
lifecycle_coordinate_drift_tx = variant(major_tx, coordinate=coordinate)
lifecycle_namespace_drift_tx = variant(major_tx, namespace="other.space")
rollback_wrong_requester = variant(semantic_request, issuer={"kind": "consumer_owner", "id": "other-consumer-owner"})
rollback_wrong_requester_receipt = variant(semantic_receipt, rollback_request_digest=rollback_wrong_requester["rollback_request_digest"])
rollback_target_drift_request = variant(semantic_request, target=runtime_target)
rollback_target_drift_receipt = variant(semantic_receipt, rollback_request_digest=rollback_target_drift_request["rollback_request_digest"], request_target_kind="runtime")
technical_subject_drift = variant(rollback_materialization, subject_digest=raw("wrong-semantic-subject"))
technical_coordinate_drift = variant(rollback_materialization, coordinate=coordinate)
technical_runtime_drift = variant(rollback_materialization, runtime_identity=old_runtime)
patch_prerelease_only = variant(compat_report, candidate_version="1.0.1", changes=[{"category": "compatible_refinement", "semantic_id": "core.Agent", "classification": "compatible", "semver_effect": "patch", "condition_id": None}], classification="compatible", required_semver_effect="patch")
resolved_dependency_contract = copy.deepcopy(consumer_canary_contract)
resolved_row = resolved_dependency_contract["dependencies"][0]
resolved_row.update({"resolution": "resolved", "ak_store_head": ak_store_head, "task_id": resolved_row["reference_id"],
    "task_record_digest": raw("observed-task-record"), "artifact_digest": raw("observed-task-artifact")})
resolved_row["observed_canonical_state"] = {"repository": copy.deepcopy(resolved_row["repository"]), "ak_store_head": copy.deepcopy(ak_store_head),
    "task_id": resolved_row["task_id"], "task_record_digest": resolved_row["task_record_digest"], "artifact_digest": resolved_row["artifact_digest"], "state": "completed"}
rehash(resolved_dependency_contract)
resolved_head_drift_contract = copy.deepcopy(resolved_dependency_contract)
resolved_head_drift_contract["dependencies"][0]["observed_canonical_state"]["ak_store_head"]["store_revision"] = 41
rehash(resolved_head_drift_contract)
resolved_task_digest_drift_contract = copy.deepcopy(resolved_dependency_contract)
resolved_task_digest_drift_contract["dependencies"][0]["observed_canonical_state"]["task_record_digest"] = raw("different-observed-task")
rehash(resolved_task_digest_drift_contract)
resolved_state_drift_contract = copy.deepcopy(resolved_dependency_contract)
resolved_state_drift_contract["dependencies"][0]["observed_canonical_state"]["state"] = "accepted"
rehash(resolved_state_drift_contract)
wrong_dependency_repository_contract = copy.deepcopy(consumer_canary_contract)
wrong_dependency_repository_contract["dependencies"][0]["repository"] = canary_repo
rehash(wrong_dependency_repository_contract)
wrong_stop_id_contract = copy.deepcopy(consumer_canary_contract)
wrong_stop_id_contract["stop_conditions"][0]["condition_id"] = "failed-validatos"
rehash(wrong_stop_id_contract)
wrong_stop_fact_contract = copy.deepcopy(consumer_canary_contract)
wrong_stop_fact_contract["stop_conditions"][0]["fact_reference"]["reference_id"] = "fact:other-stop"
rehash(wrong_stop_fact_contract)
wrong_stop_repository_contract = copy.deepcopy(consumer_canary_contract)
wrong_stop_repository_contract["stop_conditions"][0]["fact_reference"]["repository"] = ak_coord_repo
rehash(wrong_stop_repository_contract)
cases += [
    case("canonical_ak_authority_requires_independent_store_head_fact", "publication_commit", publication, "self_certification", missing_canonical_head_context),
    case("canonical_ak_authority_requires_independent_current_record_fact", "publication_commit", publication, "self_certification", missing_current_record_context),
    case("publication_trust_root_namespace_binds_authority", "publication_commit", publication, "lifecycle_violation", {**publish_commit_context, "trust_root": wrong_namespace_root}),
    case("publication_trust_root_policy_binds_authority", "publication_commit", publication, "lifecycle_violation", {**publish_commit_context, "trust_root": wrong_policy_root}),
    case("publication_trust_root_set_binds_authority", "publication_commit", publication, "lifecycle_violation", {**publish_commit_context, "trust_root": wrong_set_root}),
    case("publication_trust_root_requires_external_canonical_pin", "publication_commit", publication, "lifecycle_violation", {**publish_commit_context, "external_trust_root_pin": wrong_external_pin}),
    case("prior_journal_transaction_equals_prior_status_transaction", "publication_commit", publication, "lifecycle_violation", {**publish_commit_context, "prior_journal": prior_journal_transaction_drift, "prior_journal_digest": prior_journal_transaction_drift["publication_journal_digest"]}),
    case("lifecycle_transaction_coordinate_is_exact", "lifecycle", removal, "lifecycle_violation", {**lifecycle_context, "removal_transaction": lifecycle_coordinate_drift_tx}),
    case("lifecycle_transaction_namespace_is_exact", "lifecycle", removal, "lifecycle_violation", {**lifecycle_context, "removal_transaction": lifecycle_namespace_drift_tx}),
    case("activation_genesis_explicit_null_previous_agrees", "activation_binding", activation, None, {"decision": consumer_decision, "intent": intent, "acceptance": acceptance, "materialization": materialization, "availability": semantic_availability, **technical_context, **canonical_decision_context, **activation_authority_facts, "activation_availability": semantic_availability, "previous_activation": None, "current_activation_digest": None, "current_activation_revision": None, "previous_activation": None}),
    case("activation_null_pointer_revision_pair_is_atomic", "activation_binding", activation, "self_certification", {"decision": consumer_decision, "intent": intent, "acceptance": acceptance, "materialization": materialization, "availability": semantic_availability, **technical_context, **canonical_decision_context, **activation_authority_facts, "activation_availability": semantic_availability, "previous_activation": None, "current_activation_digest": None, "current_activation_revision": 1, "previous_activation": None}),
    case("activation_candidate_is_not_prior_canonical_head", "activation_binding", activation, "self_certification", {"decision": consumer_decision, "intent": intent, "acceptance": acceptance, "materialization": materialization, "availability": semantic_availability, **technical_context, **canonical_decision_context, **activation_authority_facts, "activation_availability": semantic_availability, "previous_activation": None, "current_activation_digest": d("activation_receipt"), "current_activation_revision": 1, "previous_activation": None}),
    case("rollback_requester_id_equals_consumer_owner", "rollback", rollback_wrong_requester_receipt, "issuer_scope_violation", rollback_context(rollback_wrong_requester, semantic_availability, semantic_history)),
    case("rollback_request_target_equals_activated_intent_and_materialization", "rollback", rollback_target_drift_receipt, "rollback_unavailable", rollback_context(rollback_target_drift_request, runtime_availability, semantic_history)),
    case("rollback_technical_receipt_binds_exact_subject_digest", "rollback", semantic_receipt, "rollback_unavailable", rollback_context(semantic_request, semantic_availability, semantic_history, semantic_materialization_technical=technical_subject_drift)),
    case("rollback_technical_receipt_binds_exact_coordinate", "rollback", semantic_receipt, "rollback_unavailable", rollback_context(semantic_request, semantic_availability, semantic_history, semantic_materialization_technical=technical_coordinate_drift)),
    case("semantic_rollback_target_requires_runtime_compatibility", "rollback", semantic_receipt, "rollback_unavailable", rollback_context(semantic_request, semantic_availability, semantic_history, semantic_materialization_technical=technical_runtime_drift)),
    case("patch_semver_rejects_prerelease_only_movement", "compatibility", patch_prerelease_only, "semver_violation", {**compatibility_non_override_context, "prior_version": "1.0.1-alpha"}),
    case("resolved_governance_reference_observation_accepts", "governance_contracts", ak_coordination_contract, None, {"consumer_contract": resolved_dependency_contract, "canonical_task_states": [copy.deepcopy(resolved_dependency_contract["dependencies"][0]["observed_canonical_state"])]}),
    case("resolved_governance_reference_observed_head_is_exact", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": resolved_head_drift_contract, "canonical_task_states": [copy.deepcopy(resolved_head_drift_contract["dependencies"][0]["observed_canonical_state"])]}),
    case("resolved_governance_reference_observed_task_digest_is_exact", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": resolved_task_digest_drift_contract, "canonical_task_states": [copy.deepcopy(resolved_task_digest_drift_contract["dependencies"][0]["observed_canonical_state"])]}),
    case("resolved_governance_reference_observed_state_is_exact", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": resolved_state_drift_contract, "canonical_task_states": [copy.deepcopy(resolved_state_drift_contract["dependencies"][0]["observed_canonical_state"])]}),
    case("unresolved_dependency_binds_correct_owner_repository", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": wrong_dependency_repository_contract, "canonical_task_states": []}),
    case("stop_condition_id_pairs_exactly", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": wrong_stop_id_contract, "canonical_task_states": []}),
    case("stop_condition_fact_id_pairs_exactly", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": wrong_stop_fact_contract, "canonical_task_states": []}),
    case("stop_condition_repository_pairs_exactly", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": wrong_stop_repository_contract, "canonical_task_states": []})]

# Revision-v8 owner/governance closure probes.
rotation_store_drift_decision = variant(owner_decision, ak_store_head={**ak_store_head, "store_revision": 41, "store_head_digest": raw("rotation-ak-store-41")})
revocation_store_drift_decision = variant(owner_decision, ak_store_head={**ak_store_head, "store_revision": 41, "store_head_digest": raw("revocation-ak-store-41")})
override_store_drift_decision = variant(owner_decision, ak_store_head={**ak_store_head, "store_revision": 41, "store_head_digest": raw("override-ak-store-41")})
publication_trust_revoked_context = {**publish_commit_context, "revoked_trust_digests": [d("trust_root")]}
lifecycle_current_head_drift_context = {**lifecycle_context, "current_lifecycle_head": raw("wrong-current-lifecycle-head")}
revoked_activation_candidate = variant(activation, revoked_by_digest=raw("candidate-revocation"))
superseded_activation_candidate = variant(activation, superseded_by_activation_receipt_digest=raw("candidate-supersession"))
rollback_controller_drift_request = variant(semantic_request, recovery_controller_id="other-recovery")
rollback_controller_drift_receipt = variant(semantic_receipt, rollback_request_digest=rollback_controller_drift_request["rollback_request_digest"])
rollback_epoch_drift_request = variant(semantic_request, recovery_epoch=84)
rollback_epoch_drift_receipt = variant(semantic_receipt, rollback_request_digest=rollback_epoch_drift_request["rollback_request_digest"])
recovery_controller_drift_journal = variant(committing, recovery_controller_id="other-recovery")
recovery_runtime_drift_journal = variant(committing, recovery_runtime_identity=old_runtime)
recovery_epoch_drift_journal = variant(committing, recovery_epoch=84)
wrong_evidence_owner_contract = copy.deepcopy(consumer_canary_contract)
next(row for row in wrong_evidence_owner_contract["required_evidence"] if row["reference_id"] == "exact-materialization-receipt")["repository"] = canary_repo
rehash(wrong_evidence_owner_contract)
def wrong_stop_owner(kind: str, repository: dict) -> dict:
    contract = copy.deepcopy(consumer_canary_contract)
    next(row for row in contract["stop_conditions"] if row["condition_kind"] == kind)["fact_reference"]["repository"] = repository
    rehash(contract); return contract
wrong_semantic_stop_owner_contract = wrong_stop_owner("stale_semantic_trust_or_ledger", ak_coord_repo)
wrong_ak_stop_owner_contract = wrong_stop_owner("stale_ak_decision_or_store", canary_repo)
wrong_consumer_stop_owner_contract = wrong_stop_owner("stale_consumer_activation_or_history", owner_repo)

cases += [
    case("rotation_requires_independent_ak_store_observation", "trust_rotation", rotation, "trust_reference_stale", {**rotation_context, "decision": rotation_store_drift_decision}),
    case("rotation_requires_independent_ak_current_record", "trust_rotation", rotation, "trust_reference_stale", {**rotation_context, "current_decision_record_digest": raw("wrong-rotation-current-record")}),
    case("revocation_requires_independent_ak_store_observation", "trust_revocation", revocation, "trust_reference_stale", {**revocation_context, "decision": revocation_store_drift_decision}),
    case("revocation_requires_independent_ak_current_record", "trust_revocation", revocation, "trust_reference_stale", {**revocation_context, "current_decision_record_digest": raw("wrong-revocation-current-record")}),
    case("override_requires_independent_ak_store_observation", "compatibility", overridden_report, "compatibility_rejected", {**override_context, "decision": override_store_drift_decision}),
    case("override_requires_independent_ak_current_record", "compatibility", overridden_report, "compatibility_rejected", {**override_context, "current_decision_record_digest": raw("wrong-override-current-record")}),
    case("publication_rejects_externally_revoked_trust_root", "publication_commit", publication, "lifecycle_violation", publication_trust_revoked_context),
    case("lifecycle_current_prior_head_is_external", "lifecycle", removal, "lifecycle_violation", lifecycle_current_head_drift_context),
    case("activation_candidate_must_be_unrevoked", "activation_binding", revoked_activation_candidate, "self_certification", {"decision": consumer_decision, "intent": intent, "acceptance": acceptance, "materialization": materialization, "availability": semantic_availability, **technical_context, **canonical_decision_context, **activation_authority_facts, "activation_availability": semantic_availability, "previous_activation": None, "current_activation_digest": None, "current_activation_revision": None}),
    case("activation_candidate_must_be_unsuperseded", "activation_binding", superseded_activation_candidate, "self_certification", {"decision": consumer_decision, "intent": intent, "acceptance": acceptance, "materialization": materialization, "availability": semantic_availability, **technical_context, **canonical_decision_context, **activation_authority_facts, "activation_availability": semantic_availability, "previous_activation": None, "current_activation_digest": None, "current_activation_revision": None}),
    case("rollback_controller_equals_external_recovery_observation", "rollback", rollback_controller_drift_receipt, "rollback_unavailable", rollback_context(rollback_controller_drift_request, semantic_availability, semantic_history)),
    case("rollback_epoch_equals_external_recovery_observation", "rollback", rollback_epoch_drift_receipt, "rollback_unavailable", rollback_context(rollback_epoch_drift_request, semantic_availability, semantic_history)),
    case("publication_recovery_controller_is_exact", "publication_recovery", recovery_controller_drift_journal, "recovery_needed", publish_recovery_context),
    case("publication_recovery_runtime_is_exact", "publication_recovery", recovery_runtime_drift_journal, "recovery_needed", publish_recovery_context),
    case("publication_recovery_epoch_is_exact", "publication_recovery", recovery_epoch_drift_journal, "recovery_needed", publish_recovery_context),
    case("resolved_governance_reference_compares_independent_snapshot", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": resolved_dependency_contract, "canonical_task_states": [{**copy.deepcopy(resolved_dependency_contract["dependencies"][0]["observed_canonical_state"]), "artifact_digest": raw("independent-snapshot-artifact-drift")}]}),
    case("governance_evidence_reference_uses_fact_owner", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": wrong_evidence_owner_contract, "canonical_task_states": []}),
    case("semantic_stop_fact_has_semantic_owner", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": wrong_semantic_stop_owner_contract, "canonical_task_states": []}),
    case("ak_stop_fact_has_ak_owner", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": wrong_ak_stop_owner_contract, "canonical_task_states": []}),
    case("consumer_stop_fact_has_consumer_owner", "governance_contracts", ak_coordination_contract, "self_certification", {"consumer_contract": wrong_consumer_stop_owner_contract, "canonical_task_states": []}),
    case("authority_snapshot_self_digest_is_universal", "publication_commit", publication, "digest_mismatch", publish_commit_context),
    case("authority_bundle_key_equals_artifact_digest", "publication_commit", publication, "digest_mismatch", publish_commit_context),
    case("authority_bundle_missing_node_fails_closed", "publication_commit", publication, "self_certification", publish_commit_context),
    case("authority_bundle_surplus_node_fails_closed", "publication_commit", publication, "self_certification", publish_commit_context),
    case("authority_node_expected_schema_is_exact", "publication_commit", publication, "malformed_input", publish_commit_context),
    case("authority_node_issuer_scope_is_exact", "publication_commit", publication, "issuer_scope_violation", publish_commit_context),
    case("authority_required_anchor_is_mandatory", "publication_commit", publication, "self_certification",
        {key: value for key, value in publish_commit_context.items() if key != "canonical_store_head"}),
    case("authority_preflight_order_is_normative", "publication_commit", publication, "malformed_input", publish_commit_context),
]

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

# Revision-v9 direct blockers and complete authority-rule coverage.
wrong_rollback_owner_kind_contract = variant(consumer_canary_contract, rollback_owner={"kind": "rocs", "id": "consumer-owner"})
wrong_history_owner = variant(semantic_history, issuer={"kind": "recovery_controller", "id": "recovery"})
wrong_availability_proof_owner = variant(semantic_availability, issuer={"kind": "recovery_controller", "id": "recovery"})
withdrawal_context = {"transaction": withdraw_tx, "journal": withdraw_journal, "marker": withdraw_marker, "prior_status": publication,
    "prior_journal_digest": d("publication_journal"), "prior_journal": publish_journal, "approval": withdraw_approval,
    "policy": owner_policy, "owner_set": owner_set, "predicate": predicate, "decision": owner_decision, **owner_canonical_decision_context}
cases.extend([
    case("version_binding_existing_coordinate_is_stable", "version_binding", publish_tx, None, {"existing_coordinate": coordinate}),
    case("consumer_acceptance_must_equal_current_owner_head", "acceptance_binding", acceptance, "self_certification",
        {"decision": consumer_decision, "intent": intent, **canonical_decision_context, **acceptance_authority_facts, "current_acceptance_digest": raw("stale-acceptance-head"), "current_acceptance_revision": acceptance["acceptance_revision"]}),
    case("publication_commit_requires_canonical_publication_head", "publication_commit", publication, "lifecycle_violation",
        {**publish_commit_context, "canonical_publication_head": raw("wrong-canonical-publication-head")}),
    case("publication_transition_requires_canonical_publication_head", "publication_transition", withdrawal, "lifecycle_violation",
        {**withdrawal_context, "canonical_publication_head": raw("wrong-transition-canonical-head")}),
    case("publication_recovery_requires_canonical_ledger_head", "publication_recovery", committing, "recovery_needed",
        {**publish_recovery_context, "canonical_publication_head": raw("wrong-recovery-canonical-head")}),
    case("task_contract_binds_exact_rollback_owner_kind", "governance_contracts", ak_coordination_contract, "self_certification",
        {"consumer_contract": wrong_rollback_owner_kind_contract, "canonical_task_states": []}),
    case("rollback_history_transition_has_consumer_owner", "rollback", semantic_receipt, "issuer_scope_violation",
        rollback_context(semantic_request, semantic_availability, wrong_history_owner)),
    case("rollback_availability_proof_has_rocs_owner", "rollback", semantic_receipt, "issuer_scope_violation",
        rollback_context(semantic_request, wrong_availability_proof_owner, semantic_history)),
    case("owner_vote_proof_requires_pinned_owner_capability", "approval_threshold", owner_approval, "issuer_scope_violation",
        {"owner_set": owner_set, "predicate": predicate, "policy": owner_policy}),
    case("authority_receipt_category_substitution_rejected", "publication_commit", publication, "issuer_scope_violation", publish_commit_context),
    case("authority_receipt_repository_identity_is_exact", "publication_commit", publication, "issuer_scope_violation", publish_commit_context),
    case("authority_receipt_owner_specific_pin_is_exact", "publication_commit", publication, "issuer_scope_violation", publish_commit_context),
    case("authority_receipt_head_revision_fact_binding_is_exact", "publication_commit", publication, "issuer_scope_violation", publish_commit_context),
    case("authority_receipt_freshness_cas_floor_is_enforced", "publication_commit", publication, "issuer_scope_violation", publish_commit_context),
    case("authority_snapshot_surplus_receipt_rejected", "publication_commit", publication, "self_certification", publish_commit_context),
    case("authority_snapshot_duplicate_conflicting_receipt_rejected", "publication_commit", publication, "malformed_input", publish_commit_context),
    case("authority_verifier_surplus_role_rejected", "publication_commit", publication, "self_certification", publish_commit_context),
    case("authority_collator_cannot_issue_receipts", "publication_commit", publication, "issuer_scope_violation", publish_commit_context),
    case("authority_acquisition_distribution_digest_is_exact", "publication_commit", publication, "issuer_scope_violation", publish_commit_context),
    case("authority_coherent_acquisition_rewrite_rejected", "publication_commit", publication, "issuer_scope_violation", publish_commit_context),
    case("authority_coherent_owner_repository_rewrite_rejected", "publication_commit", publication, "issuer_scope_violation", publish_commit_context),
])
# Revision-v9 owner-issued store-read receipt authority graph.
# The fixture collator transports receipts but has no receipt-issuance capability.
AUTHORITY_BEARING_RULES = {
    "acceptance_binding", "activation_binding", "ak_decision", "approval_threshold", "compatibility", "generation_activation",
    "governance_contracts", "lifecycle", "projection", "publication_cas", "publication_commit", "publication_recovery",
    "publication_transition", "rollback", "tombstone_reuse", "trust_revocation", "trust_rotation", "version_binding",
}
ALL_RULES = {
    "acceptance_binding", "activation_binding", "ak_decision", "ak_optional_pi", "approval_threshold", "compatibility",
    "compatibility_policy", "digest", "generation_activation", "governance_contracts", "lifecycle", "pi_variant", "projection",
    "publication_cas", "publication_commit", "publication_journal_shape", "publication_recovery", "publication_transition", "rollback", "tombstone_reuse",
    "trust_revocation", "trust_rotation", "utc", "version_binding",
}
ROLE_CATEGORY = {
    "current_root_digest": "semantic_trust", "external_trust_root_pin": "semantic_trust", "canonical_trust_root_digest": "semantic_trust",
    "revoked": "semantic_revocation", "prior_revision": "semantic_revocation", "prior_head": "semantic_revocation",
    "canonical_trust_revocation_revision": "semantic_revocation", "canonical_trust_revocation_head": "semantic_revocation",
    "revoked_trust_digests": "semantic_revocation", "current_revision": "semantic_publication", "current_head": "semantic_publication",
    "existing_replay_key": "semantic_publication", "existing_coordinate": "semantic_publication", "existing_operation": "semantic_publication",
    "canonical_publication_revision": "semantic_publication", "canonical_publication_head": "semantic_publication",
    "canonical_publication_journal_head": "semantic_publication", "canonical_recovery_journal_head": "semantic_publication",
    "canonical_recovery_transaction_digest": "semantic_publication", "canonical_recovery_resulting_revision": "semantic_publication",
    "canonical_recovery_resulting_head": "semantic_publication", "canonical_recovery_resulting_status_digest": "semantic_publication",
    "canonical_deprecation_revision": "semantic_lifecycle", "canonical_deprecation_head": "semantic_lifecycle",
    "canonical_removal_revision": "semantic_lifecycle", "canonical_removal_head": "semantic_lifecycle",
    "deprecation_prior_head": "semantic_lifecycle", "current_lifecycle_head": "semantic_lifecycle",
    "canonical_store_head": "ak_store", "current_decision_record_digest": "ak_decision",
    "current_deprecation_decision_record_digest": "ak_decision", "current_removal_decision_record_digest": "ak_decision",
    "canonical_task_states": "ak_task", "current_acceptance_digest": "consumer_acceptance",
    "current_acceptance_revision": "consumer_acceptance", "current_activation_digest": "consumer_activation",
    "current_activation_revision": "consumer_activation", "canonical_history_head": "consumer_history",
    "canonical_recovery_controller_id": "recovery_controller", "canonical_recovery_runtime_identity": "recovery_controller",
    "canonical_recovery_epoch": "recovery_controller",
    "canonical_lifecycle_tombstone_head": "semantic_lifecycle",
    "canonical_publication_status_digest": "semantic_publication",
}
CATEGORY_PROFILE = {
    "semantic_trust": ("semantic_owner", "semantic-owner", owner_repo, "semantic-trust-store", "ontology-kernel.semantic-trust-read.v0"),
    "semantic_revocation": ("semantic_owner", "semantic-owner", owner_repo, "semantic-revocation-ledger", "ontology-kernel.semantic-revocation-read.v0"),
    "semantic_publication": ("semantic_owner", "semantic-owner", owner_repo, "semantic-publication-ledger", "ontology-kernel.semantic-publication-read.v0"),
    "semantic_lifecycle": ("semantic_owner", "semantic-owner", owner_repo, "semantic-lifecycle-ledger", "ontology-kernel.semantic-lifecycle-read.v0"),
    "ak_store": ("ak", "agent-kernel-owner", ak_repo, "ak-main", "agent-kernel.store-read.v0"),
    "ak_decision": ("ak", "agent-kernel-owner", ak_repo, "ak-main", "agent-kernel.decision-read.v0"),
    "ak_task": ("ak", "agent-kernel-owner", ak_repo, "ak-main", "agent-kernel.task-read.v0"),
    "consumer_acceptance": ("consumer_owner", "consumer-owner", consumer_repo, "consumer-acceptance", "consumer.acceptance-read.v0"),
    "consumer_activation": ("consumer_owner", "consumer-owner", consumer_repo, "consumer-activation", "consumer.activation-read.v0"),
    "consumer_history": ("consumer_owner", "consumer-owner", consumer_repo, "consumer-history", "consumer.history-read.v0"),
    "recovery_controller": ("recovery_controller", "recovery", rocs_repo, "recovery-controller", "recovery-controller.store-read.v0"),
}
FACT_SCHEMA_BY_CATEGORY = {category: f"semantic-authority-{category.replace('_', '-')}-fact.v0" for category in CATEGORY_PROFILE}
FACT_SCHEMA_BY_CATEGORY["semantic_vote"] = "semantic-owner-vote-proof-fact.v0"
COLLATOR = {"kind": "rocs", "id": "decision-53-authority-collator"}
ACTION_EPOCH = 100
ACTION_EPOCH_FLOOR = 90

RULE_SCHEMA_ROLES = {
    "approval_threshold": {"owner_set": "semantic-owner-set.v0", "predicate": "semantic-approval-predicate.v0", "policy": "semantic-owner-policy.v0"},
    "trust_rotation": {"old_root": "semantic-trust-root.v0", "new_root": "semantic-trust-root.v0", "approval": "semantic-owner-approval.v0", "policy": "semantic-owner-policy.v0", "owner_set": "semantic-owner-set.v0", "predicate": "semantic-approval-predicate.v0", "decision": "semantic-ak-decision-reference.v0"},
    "trust_revocation": {"approval": "semantic-owner-approval.v0", "policy": "semantic-owner-policy.v0", "owner_set": "semantic-owner-set.v0", "predicate": "semantic-approval-predicate.v0", "decision": "semantic-ak-decision-reference.v0"},
    "compatibility": {"policy": "semantic-compatibility-policy.v0", "owner_policy": "semantic-owner-policy.v0", "owner_set": "semantic-owner-set.v0", "predicate": "semantic-approval-predicate.v0", "decision": "semantic-ak-decision-reference.v0"},
    "lifecycle": {"deprecation": "semantic-deprecation-record.v0", "policy": "semantic-compatibility-policy.v0", "resulting_tombstones": "semantic-tombstone-registry.v0", "tombstone_history": "semantic-tombstone-history-proof.v0", "deprecation_ledger": "semantic-accepted-lifecycle-ledger-record.v0", "removal_ledger": "semantic-accepted-lifecycle-ledger-record.v0", "deprecation_publication": "semantic-owner-publication.v0", "removal_publication": "semantic-owner-publication.v0", "deprecation_transaction": "semantic-publication-transaction.v0", "removal_transaction": "semantic-publication-transaction.v0", "deprecation_journal": "semantic-publication-journal.v0", "removal_journal": "semantic-publication-journal.v0", "deprecation_marker": "semantic-publication-commit-marker.v0", "removal_marker": "semantic-publication-commit-marker.v0", "deprecation_approval": "semantic-owner-approval.v0", "removal_approval": "semantic-owner-approval.v0", "deprecation_prior_status": "semantic-owner-publication.v0", "removal_prior_status": "semantic-publication-status-transition.v0", "deprecation_prior_journal": "semantic-publication-journal.v0", "removal_prior_journal": "semantic-publication-journal.v0", "deprecation_canonical_ledger": "semantic-publication-ledger-head.v0", "removal_canonical_ledger": "semantic-publication-ledger-head.v0", "owner_policy": "semantic-owner-policy.v0", "owner_set": "semantic-owner-set.v0", "predicate": "semantic-approval-predicate.v0", "trust_root": "semantic-trust-root.v0", "deprecation_decision": "semantic-ak-decision-reference.v0", "removal_decision": "semantic-ak-decision-reference.v0"},
    "tombstone_reuse": {"tombstones": "semantic-tombstone-registry.v0", "tombstone_history": "semantic-tombstone-history-proof.v0", "override": "semantic-compatibility-override.v0"},
    "publication_commit": {"transaction": "semantic-publication-transaction.v0", "journal": "semantic-publication-journal.v0", "marker": "semantic-publication-commit-marker.v0", "approval": "semantic-owner-approval.v0", "trust_root": "semantic-trust-root.v0", "prior_journal": "semantic-publication-journal.v0", "prior_status": "semantic-owner-publication.v0", "policy": "semantic-owner-policy.v0", "owner_set": "semantic-owner-set.v0", "predicate": "semantic-approval-predicate.v0", "decision": "semantic-ak-decision-reference.v0"},
    "publication_transition": {"transaction": "semantic-publication-transaction.v0", "journal": "semantic-publication-journal.v0", "marker": "semantic-publication-commit-marker.v0", "prior_status": ("semantic-owner-publication.v0", "semantic-publication-status-transition.v0"), "approval": "semantic-owner-approval.v0", "trust_root": "semantic-trust-root.v0", "policy": "semantic-owner-policy.v0", "owner_set": "semantic-owner-set.v0", "predicate": "semantic-approval-predicate.v0", "prior_journal": "semantic-publication-journal.v0", "decision": "semantic-ak-decision-reference.v0"},
    "publication_recovery": {"transaction": "semantic-publication-transaction.v0", "resulting_status": ("semantic-owner-publication.v0", "semantic-publication-status-transition.v0"),
        "intent_marker": "semantic-publication-recovery-intent-marker.v0", "marker": "semantic-publication-commit-marker.v0",
        "before": "semantic-publication-recovery-state-receipt.v0", "after": "semantic-publication-recovery-state-receipt.v0",
        "prior_status": ("semantic-owner-publication.v0", "semantic-publication-status-transition.v0"), "prior_journal": "semantic-publication-journal.v0",
        "approval": "semantic-owner-approval.v0", "policy": "semantic-owner-policy.v0", "owner_set": "semantic-owner-set.v0",
        "predicate": "semantic-approval-predicate.v0", "decision": "semantic-ak-decision-reference.v0", "trust_root": "semantic-trust-root.v0"},
    "projection": {"projection": "semantic-payload-projection.v0", "capsule": "semantic-release-capsule.v0", "archive_linkage": "semantic-capsule-archive-linkage.v0", "payload_manifest": "semantic-material-manifest.v0", "consumer_manifest": "semantic-material-manifest.v0", "archive_manifest": "semantic-material-manifest.v0", "tombstones": "semantic-tombstone-registry.v0", "tombstone_history": "semantic-tombstone-history-proof.v0"},
    "rollback": {"request": "semantic-rollback-request.v0", "activation": "semantic-activation-receipt.v0", "decision": "semantic-ak-decision-reference.v0", "intent": "semantic-consumer-intent.v0", "acceptance": "semantic-owner-acceptance.v0", "materialization": "semantic-materialization-verification-receipt.v0", "availability": "semantic-rollback-availability-proof.v0", "activation_availability": "semantic-rollback-availability-proof.v0", "recovery_artifact": "semantic-rollback-availability-receipt.v0", "semantic_artifact": "semantic-rollback-availability-receipt.v0", "runtime_artifact": "semantic-rollback-availability-receipt.v0", "disable_artifact": "semantic-rollback-availability-receipt.v0", "history_after": "semantic-rollback-history-transition.v0", "ak_linkage": "semantic-ak-evidence-linkage.v0", "pi_receipt": "semantic-pi-delivery-receipt.v0", "previous_activation": "semantic-activation-receipt.v0", "semantic_materialization_technical": "semantic-rollback-technical-receipt.v0", "runtime_materialization_technical": "semantic-rollback-technical-receipt.v0", "runtime_revalidation_technical": "semantic-rollback-technical-receipt.v0", "disable_contract_technical": "semantic-rollback-technical-receipt.v0", "disable_rehearsal_technical": "semantic-rollback-technical-receipt.v0", "recovery_rehearsal_technical": "semantic-rollback-technical-receipt.v0", "recovery_health_technical": "semantic-rollback-technical-receipt.v0"},
    "generation_activation": {"activation": "semantic-activation-receipt.v0", "decision": "semantic-ak-decision-reference.v0", "intent": "semantic-consumer-intent.v0", "acceptance": "semantic-owner-acceptance.v0", "materialization": "semantic-materialization-verification-receipt.v0", "availability": "semantic-rollback-availability-proof.v0", "activation_availability": "semantic-rollback-availability-proof.v0", "semantic_artifact": "semantic-rollback-availability-receipt.v0", "runtime_artifact": "semantic-rollback-availability-receipt.v0", "disable_artifact": "semantic-rollback-availability-receipt.v0", "recovery_artifact": "semantic-rollback-availability-receipt.v0", "semantic_materialization_technical": "semantic-rollback-technical-receipt.v0", "runtime_materialization_technical": "semantic-rollback-technical-receipt.v0", "runtime_revalidation_technical": "semantic-rollback-technical-receipt.v0", "disable_contract_technical": "semantic-rollback-technical-receipt.v0", "disable_rehearsal_technical": "semantic-rollback-technical-receipt.v0", "recovery_rehearsal_technical": "semantic-rollback-technical-receipt.v0", "recovery_health_technical": "semantic-rollback-technical-receipt.v0", "previous_activation": "semantic-activation-receipt.v0"},
    "acceptance_binding": {"decision": "semantic-ak-decision-reference.v0", "intent": "semantic-consumer-intent.v0"},
    "activation_binding": {"decision": "semantic-ak-decision-reference.v0", "intent": "semantic-consumer-intent.v0", "acceptance": "semantic-owner-acceptance.v0", "materialization": "semantic-materialization-verification-receipt.v0", "availability": "semantic-rollback-availability-proof.v0", "activation_availability": "semantic-rollback-availability-proof.v0", "previous_activation": "semantic-activation-receipt.v0", "semantic_artifact": "semantic-rollback-availability-receipt.v0", "runtime_artifact": "semantic-rollback-availability-receipt.v0", "disable_artifact": "semantic-rollback-availability-receipt.v0", "recovery_artifact": "semantic-rollback-availability-receipt.v0", "semantic_materialization_technical": "semantic-rollback-technical-receipt.v0", "runtime_materialization_technical": "semantic-rollback-technical-receipt.v0", "runtime_revalidation_technical": "semantic-rollback-technical-receipt.v0", "disable_contract_technical": "semantic-rollback-technical-receipt.v0", "disable_rehearsal_technical": "semantic-rollback-technical-receipt.v0", "recovery_rehearsal_technical": "semantic-rollback-technical-receipt.v0", "recovery_health_technical": "semantic-rollback-technical-receipt.v0"},
    "governance_contracts": {"consumer_contract": "semantic-non-authorizing-task-contract.v0"},
    "version_binding": {"existing_coordinate": "semantic-release-coordinate.v0"},
    "publication_cas": {"existing_coordinate": "semantic-release-coordinate.v0"},
}

SEMANTIC_SCHEMAS = {"semantic-source-manifest.v0", "semantic-owner-set.v0", "semantic-approval-predicate.v0", "semantic-owner-policy.v0", "semantic-trust-root.v0", "semantic-trust-rotation.v0", "semantic-trust-revocation.v0", "semantic-compatibility-policy.v0", "semantic-compatibility-report.v0", "semantic-compatibility-override.v0", "semantic-deprecation-record.v0", "semantic-removal-record.v0", "semantic-tombstone-registry.v0", "semantic-tombstone-history-proof.v0", "semantic-publication-ledger-head.v0", "semantic-accepted-lifecycle-ledger-record.v0", "semantic-release-capsule.v0", "semantic-owner-approval.v0", "semantic-publication-transaction.v0", "semantic-publication-journal.v0", "semantic-publication-commit-marker.v0", "semantic-owner-publication.v0", "semantic-publication-status-transition.v0", "semantic-release-coordinate.v0"}
ROCS_SCHEMAS = {"semantic-material-manifest.v0", "semantic-payload-projection.v0", "semantic-capsule-archive-linkage.v0", "semantic-build-receipt.v0", "semantic-materialization-verification-receipt.v0", "semantic-rocs-generation-receipt.v0", "semantic-rollback-availability-proof.v0"}
CONSUMER_SCHEMAS = {"semantic-consumer-intent.v0", "semantic-owner-acceptance.v0", "semantic-activation-receipt.v0", "semantic-rollback-request.v0", "semantic-rollback-history-transition.v0"}
AK_SCHEMAS = {"semantic-ak-decision-reference.v0", "semantic-ak-evidence-linkage.v0"}
RECOVERY_SCHEMAS = {"semantic-rollback-receipt.v0", "semantic-publication-recovery-intent-marker.v0", "semantic-publication-recovery-state-receipt.v0"}

REQUIRED_RECEIPT_ROLES = {
    "approval_threshold": set(),
    "trust_rotation": {"current_root_digest", "revoked", "canonical_store_head", "current_decision_record_digest"},
    "trust_revocation": {"prior_revision", "prior_head", "canonical_store_head", "current_decision_record_digest"},
    "compatibility": {"canonical_store_head", "current_decision_record_digest"},
    "lifecycle": {"canonical_deprecation_head", "canonical_deprecation_revision", "canonical_removal_head", "canonical_removal_revision", "canonical_store_head", "current_deprecation_decision_record_digest", "current_removal_decision_record_digest", "deprecation_prior_head", "current_lifecycle_head", "external_trust_root_pin", "canonical_trust_root_digest", "canonical_trust_revocation_revision", "canonical_trust_revocation_head", "revoked_trust_digests"},
    "publication_commit": {"canonical_store_head", "current_decision_record_digest", "external_trust_root_pin", "canonical_trust_root_digest", "canonical_trust_revocation_revision", "canonical_trust_revocation_head", "revoked_trust_digests", "canonical_publication_revision", "canonical_publication_head", "canonical_publication_journal_head"},
    "publication_transition": {"canonical_store_head", "current_decision_record_digest", "external_trust_root_pin", "canonical_trust_root_digest", "canonical_trust_revocation_revision", "canonical_trust_revocation_head", "revoked_trust_digests", "canonical_publication_revision", "canonical_publication_head", "canonical_publication_journal_head"},
    "publication_recovery": {"canonical_recovery_controller_id", "canonical_recovery_runtime_identity", "canonical_recovery_epoch",
        "canonical_publication_revision", "canonical_publication_head", "canonical_publication_status_digest",
        "canonical_publication_journal_head", "canonical_recovery_journal_head", "canonical_recovery_transaction_digest",
        "canonical_recovery_resulting_revision", "canonical_recovery_resulting_head", "canonical_recovery_resulting_status_digest",
        "canonical_store_head", "current_decision_record_digest", "external_trust_root_pin", "canonical_trust_root_digest",
        "canonical_trust_revocation_revision", "canonical_trust_revocation_head", "revoked_trust_digests"},
    "tombstone_reuse": {"canonical_lifecycle_tombstone_head"},
    "projection": {"canonical_lifecycle_tombstone_head"},
    "publication_cas": {"current_revision", "current_head", "existing_replay_key", "existing_coordinate", "existing_operation"},
    "version_binding": {"existing_coordinate"},
    "ak_decision": {"canonical_store_head", "current_decision_record_digest"},
    "acceptance_binding": {"canonical_store_head", "current_decision_record_digest", "current_acceptance_digest", "current_acceptance_revision", "canonical_trust_root_digest", "canonical_trust_revocation_revision", "canonical_trust_revocation_head", "revoked_trust_digests", "canonical_publication_revision", "canonical_publication_head"},
    "activation_binding": {"canonical_store_head", "current_decision_record_digest", "current_acceptance_digest", "current_acceptance_revision", "current_activation_digest", "current_activation_revision", "canonical_recovery_controller_id", "canonical_recovery_runtime_identity", "canonical_recovery_epoch", "canonical_trust_root_digest", "canonical_trust_revocation_revision", "canonical_trust_revocation_head", "revoked_trust_digests", "canonical_publication_revision", "canonical_publication_head"},
    "generation_activation": {"canonical_store_head", "current_decision_record_digest", "current_acceptance_digest", "current_acceptance_revision", "current_activation_digest", "current_activation_revision", "canonical_recovery_controller_id", "canonical_recovery_runtime_identity", "canonical_recovery_epoch", "canonical_trust_root_digest", "canonical_trust_revocation_revision", "canonical_trust_revocation_head", "revoked_trust_digests", "canonical_publication_revision", "canonical_publication_head"},
    "rollback": {"canonical_store_head", "current_decision_record_digest", "current_acceptance_digest", "current_acceptance_revision", "current_activation_digest", "current_activation_revision", "canonical_history_head", "canonical_recovery_controller_id", "canonical_recovery_runtime_identity", "canonical_recovery_epoch", "canonical_trust_root_digest", "canonical_trust_revocation_revision", "canonical_trust_revocation_head", "revoked_trust_digests", "canonical_publication_revision", "canonical_publication_head"},
    "governance_contracts": {"canonical_task_states"},
}
RULE_PARAMETER_ROLES = {
    "compatibility": {"prior_version", "overrides", "override_approvals"},
    "lifecycle": set(),
    "publication_commit": {"expected_action", "prior_journal_digest"},
    "publication_transition": {"prior_journal_digest"},
    "publication_recovery": {"expected_action"},
}
NULLABLE_ARTIFACT_ROLES = {"override", "marker", "previous_activation", "history_after", "ak_linkage", "pi_receipt",
    "decision", "owner_policy", "owner_set", "predicate", "semantic_artifact", "runtime_artifact", "disable_artifact", "recovery_artifact",
    "semantic_materialization_technical", "runtime_materialization_technical", "runtime_revalidation_technical", "disable_contract_technical",
    "disable_rehearsal_technical", "recovery_rehearsal_technical", "recovery_health_technical", "request", "activation", "intent", "acceptance",
    "materialization", "availability", "activation_availability"}
VOTE_RULES = {"approval_threshold", "trust_rotation", "trust_revocation", "compatibility", "lifecycle", "publication_commit", "publication_recovery", "publication_transition"}
SUBJECT_PROFILE_BY_RULE: dict[str, dict] = {}


def value_fact(value: object) -> dict:
    if value is None: return {"kind": "null"}
    if isinstance(value, bool): return {"kind": "boolean", "value": value}
    if isinstance(value, int): return {"kind": "safe_integer", "value": value}
    if isinstance(value, str):
        if value.startswith("sha256:"): return {"kind": "digest", "value": value}
        if value.count(".") >= 2 and value[0].isdigit(): return {"kind": "semver", "value": value}
        return {"kind": "text", "value": value}
    if isinstance(value, list) and value and all(isinstance(x, dict) and set(x) == {"repository", "ak_store_head", "task_id", "task_record_digest", "artifact_digest", "state"} for x in value):
        return {"kind": "ak_task_state_list", "value": value}
    if isinstance(value, list) and all(isinstance(x, str) and x.startswith("sha256:") for x in value): return {"kind": "digest_list", "value": value}
    if isinstance(value, list) and not value: return {"kind": "empty_list"}
    if isinstance(value, dict) and not value: return {"kind": "empty_map"}
    if isinstance(value, dict):
        keys = set(value)
        if keys == {"owner_id", "owner_key_id", "approved_action_digest", "approval_proof_digest"}: return {"kind": "owner_vote_proof", "value": value}
        if keys == {"namespace", "lifecycle_head_digest", "tombstone_registry_digest", "tombstone_registry_revision"}: return {"kind": "lifecycle_tombstone_head", "value": value}
        if keys == {"store_id", "canonical_store_locator", "store_revision", "store_head_digest", "revocation_head_digest"}: return {"kind": "ak_store_head", "value": value}
        if keys == {"namespace", "trust_root_id", "trust_root_revision", "trust_root_digest", "owner_policy_digest", "owner_set_digest", "revocation_revision", "revocation_head_digest"}: return {"kind": "external_trust_root_pin", "value": value}
        if keys == {"revision", "head", "status_record_digest", "intent_marker_digest", "durable_commit_marker_digest", "staging_present"}: return {"kind": "publication_recovery_state", "value": value}
        if keys == {"kind", "digest"}: return {"kind": "history_head", "value": value}
        if value.get("schema") == "semantic-release-coordinate.v0": return {"kind": "coordinate", "value": value}
        if keys == {"tool", "version", "distribution_digest", "protocol_version"}: return {"kind": "tool_identity", "value": value}
        if keys == {"repository", "ak_store_head", "task_id", "task_record_digest", "artifact_digest", "state"}: return {"kind": "ak_task_state", "value": value}
        if "kind" in value and value["kind"] in {"release", "trust_rotation", "trust_revocation", "compatibility_override", "publication_withdrawal", "publication_revocation"}: return {"kind": "approval_action", "value": value}
    raise ValueError(f"unsupported closed authority fact/parameter: {value!r}")


def artifact_digest(value: dict) -> str:
    if value["schema"] == "semantic-release-coordinate.v0": return object_digest(value, COORDINATE_DOMAIN, None)[1]
    return value[DIGEST_FIELDS[value["schema"]][1]]


def expected_artifact_schema(rule: str, role: str, artifact: dict) -> str:
    base = role.split(":", 1)[0]
    if role.startswith("overrides:"): return "semantic-compatibility-override.v0"
    if role.startswith("override_approvals:"): return "semantic-owner-approval.v0"
    expected = RULE_SCHEMA_ROLES.get(rule, {}).get(base)
    if isinstance(expected, tuple): return artifact["schema"] if artifact["schema"] in expected else expected[0]
    return expected or artifact["schema"]


def schema_authority(rule: str, role: str, artifact: dict, schema_name: str) -> tuple[dict, str, dict]:
    if schema_name in {"semantic-publication-recovery-intent-marker.v0", "semantic-publication-recovery-state-receipt.v0"}:
        issuer = copy.deepcopy(artifact["issuer"])
    elif schema_name == "semantic-rollback-technical-receipt.v0":
        kind = {"materialization": "rocs", "runtime_revalidation": "rocs", "disable_contract": "consumer_owner", "rehearsal": "recovery_controller", "health": "recovery_controller"}[artifact["receipt_kind"]]
        issuer = {"kind": kind, "id": {"rocs": "rocs-cli", "consumer_owner": "consumer-owner", "recovery_controller": "recovery"}[kind]}
    elif schema_name == "semantic-rollback-availability-receipt.v0":
        kind = {"semantic_target": "rocs", "runtime_target": "rocs", "disable_target": "consumer_owner", "recovery_runtime": "recovery_controller"}[artifact["artifact_kind"]]
        issuer = {"kind": kind, "id": {"rocs": "rocs-cli", "consumer_owner": "consumer-owner", "recovery_controller": "recovery"}[kind]}
    elif schema_name == "semantic-non-authorizing-task-contract.v0": issuer = {"kind": "consumer_owner" if artifact["task_kind"] == "single_canary_consumer" else "ak", "id": artifact["task_owner_id"]}
    elif schema_name in SEMANTIC_SCHEMAS: issuer = {"kind": "semantic_owner", "id": "semantic-owner"}
    elif schema_name in ROCS_SCHEMAS: issuer = artifact.get("issuer", {"kind": "rocs", "id": "rocs-cli"})
    elif schema_name in CONSUMER_SCHEMAS: issuer = artifact.get("issuer", artifact.get("acceptance_authority", {"kind": "consumer_owner", "id": "consumer-owner"}))
    elif schema_name in AK_SCHEMAS: issuer = artifact.get("issuer", {"kind": "ak", "id": "agent-kernel-owner"})
    elif schema_name in RECOVERY_SCHEMAS: issuer = artifact.get("issuer", {"kind": "recovery_controller", "id": "recovery"})
    elif schema_name == "semantic-pi-delivery-receipt.v0": issuer = artifact["issuer"]
    else: issuer = artifact.get("issuer", {"kind": "rocs", "id": "rocs-cli"})
    claim = {"semantic_owner": "semantic_owner_fact", "ak": "ak_canonical_fact", "consumer_owner": "consumer_owner_fact", "rocs": "rocs_technical_fact", "recovery_controller": "recovery_controller_fact", "pi": "pi_delivery_fact"}[issuer["kind"]]
    repository = {"semantic_owner": owner_repo, "ak": ak_repo, "consumer_owner": consumer_repo, "rocs": rocs_repo, "recovery_controller": rocs_repo, "pi": pi_repo}[issuer["kind"]]
    return copy.deepcopy(issuer), claim, copy.deepcopy(repository)


def artifact_authority(rule: str, role: str, artifact: dict, expected: bool = False) -> tuple[dict, str, dict]:
    schema_name = expected_artifact_schema(rule, role, artifact) if expected else artifact["schema"]
    return schema_authority(rule, role, artifact, schema_name)


def task_state_rows(item: dict, context: dict) -> list[dict]:
    if item["rule"] != "governance_contracts": return []
    result: list[dict] = []
    for contract in (item["subject"], context.get("consumer_contract")):
        if not isinstance(contract, dict): continue
        for group in ("dependencies", "prerequisites", "required_evidence"):
            for row in contract[group]:
                if row["resolution"] == "resolved" and row["observed_canonical_state"] is not None: result.append(copy.deepcopy(row["observed_canonical_state"]))
        for row in contract["stop_conditions"]:
            fact = row["fact_reference"]
            if fact["resolution"] == "resolved" and fact["observed_canonical_state"] is not None: result.append(copy.deepcopy(fact["observed_canonical_state"]))
    result.sort(key=lambda row: (row["repository"]["repository_id"].encode(), row["task_id"].encode(), row["task_record_digest"].encode()))
    return result


MISSING_ANCHOR_NEGATIVES = {
    "authority_required_anchor_is_mandatory": {"canonical_store_head"},
    "canonical_ak_authority_requires_independent_store_head_fact": {"canonical_store_head"},
    "canonical_ak_authority_requires_independent_current_record_fact": {"current_decision_record_digest"},
}


# Revision-v12 explicit source-case authority declarations. These literals are consumed before wrapping;
# no store metadata tuple or vote proof fact is inferred from a subject, category, or canonical default.
EXPLICIT_STORE_METADATA_TUPLES = json.loads(r'''
{
  "store_tuple_000": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://core/ontology-kernel",
      "identity_revision": 1,
      "owner": "semantic-owner",
      "repository_id": "ontology-kernel"
    },
    "store_head_digest": "sha256:f7376e853e56c27f0e38186327bc7b1322f23e2c6e3ccfc147c5ee016da332fd",
    "store_id": "semantic-publication-ledger",
    "store_revision": 500
  },
  "store_tuple_001": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://core/rocs-cli",
      "identity_revision": 4,
      "owner": "rocs-owner",
      "repository_id": "rocs-cli"
    },
    "store_head_digest": "sha256:12dc0b082a4afad6243ddb38400fc20a4737ddb60a1bae91ea54ab94364c2eaa",
    "store_id": "recovery-controller",
    "store_revision": 85
  },
  "store_tuple_002": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://core/ontology-kernel",
      "identity_revision": 1,
      "owner": "semantic-owner",
      "repository_id": "ontology-kernel"
    },
    "store_head_digest": "sha256:27897da79174f3a605d6bb3381c179abab2660b8892a56a6f08b3f7899b95371",
    "store_id": "semantic-publication-ledger",
    "store_revision": 2
  },
  "store_tuple_003": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://softwareco/owned/agent-kernel",
      "identity_revision": 9,
      "owner": "agent-kernel-owner",
      "repository_id": "agent-kernel"
    },
    "store_head_digest": "sha256:e824159bfb0e4253a35b3c2abc5467554d89b0c60e370d5272f606904da25ad9",
    "store_id": "ak-main",
    "store_revision": 42
  },
  "store_tuple_004": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://core/ontology-kernel",
      "identity_revision": 1,
      "owner": "semantic-owner",
      "repository_id": "ontology-kernel"
    },
    "store_head_digest": "sha256:4786b0c13da6dc6c878a42b17b5d95af074fa1877752549938b371febdabf91f",
    "store_id": "semantic-revocation-ledger",
    "store_revision": 1
  },
  "store_tuple_005": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://core/ontology-kernel",
      "identity_revision": 1,
      "owner": "semantic-owner",
      "repository_id": "ontology-kernel"
    },
    "store_head_digest": "sha256:b38b6d6cc96a19fc6ff6af60ed56828f3814d5b15e3a54da8e008bda7d89d832",
    "store_id": "semantic-trust-store",
    "store_revision": 5
  },
  "store_tuple_006": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://softwareco/pi-canary-consumer",
      "identity_revision": 3,
      "owner": "consumer-owner",
      "repository_id": "pi-canary-consumer"
    },
    "store_head_digest": "sha256:36906c52e00647c6120f3105f7d962a03437786761a1177c4be8ee2ac5ddbc2c",
    "store_id": "consumer-acceptance",
    "store_revision": 4
  },
  "store_tuple_007": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://softwareco/pi-canary-consumer",
      "identity_revision": 3,
      "owner": "consumer-owner",
      "repository_id": "pi-canary-consumer"
    },
    "store_head_digest": "sha256:0f6d6e4eb138069bda5cad7c41cd1c09fc64fd046db26560c99c06e284067087",
    "store_id": "consumer-activation",
    "store_revision": 0
  },
  "store_tuple_008": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://softwareco/pi-canary-consumer",
      "identity_revision": 3,
      "owner": "consumer-owner",
      "repository_id": "pi-canary-consumer"
    },
    "store_head_digest": "sha256:3adc831115c27950bb251d9105fad726d5b51a3ce78ede0b2bcd0e842caaf56d",
    "store_id": "consumer-activation",
    "store_revision": 1
  },
  "store_tuple_009": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://softwareco/pi-canary-consumer",
      "identity_revision": 3,
      "owner": "consumer-owner",
      "repository_id": "pi-canary-consumer"
    },
    "store_head_digest": "sha256:0f6d6e4eb138069bda5cad7c41cd1c09fc64fd046db26560c99c06e284067087",
    "store_id": "consumer-activation",
    "store_revision": 1
  },
  "store_tuple_010": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://core/ontology-kernel",
      "identity_revision": 1,
      "owner": "semantic-owner",
      "repository_id": "ontology-kernel"
    },
    "store_head_digest": "sha256:1b4a76d45e9cd4f912674f8920bfd13e859a245ca165e8ed0e1d1f1e12b876a5",
    "store_id": "semantic-vote:owner-a",
    "store_revision": 1
  },
  "store_tuple_011": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://core/ontology-kernel",
      "identity_revision": 1,
      "owner": "semantic-owner",
      "repository_id": "ontology-kernel"
    },
    "store_head_digest": "sha256:613b2a19551179052f88ec5344a6154655854a76b21a7bd53fac587e5ecd79e7",
    "store_id": "semantic-vote:owner-b",
    "store_revision": 1
  },
  "store_tuple_012": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://core/ontology-kernel",
      "identity_revision": 1,
      "owner": "semantic-owner",
      "repository_id": "ontology-kernel"
    },
    "store_head_digest": "sha256:0db1edc6a7d8392d41bb7ebbb45cfbdb06e00fdfb6884e96dc3e2b9a518c20fa",
    "store_id": "semantic-lifecycle-ledger",
    "store_revision": 4
  },
  "store_tuple_013": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://core/ontology-kernel",
      "identity_revision": 1,
      "owner": "semantic-owner",
      "repository_id": "ontology-kernel"
    },
    "store_head_digest": "sha256:49e36b944128f9e2d23932c3ff10b01512a2ae089ab522b28abfebfea12dfeb2",
    "store_id": "semantic-publication-ledger",
    "store_revision": 1
  },
  "store_tuple_014": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://core/ontology-kernel",
      "identity_revision": 1,
      "owner": "semantic-owner",
      "repository_id": "ontology-kernel"
    },
    "store_head_digest": "sha256:5f15430d3063cc04225637f22eb48e842564990f6aede71479d22fb4661cc90a",
    "store_id": "semantic-publication-ledger",
    "store_revision": 2
  },
  "store_tuple_015": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://softwareco/pi-canary-consumer",
      "identity_revision": 3,
      "owner": "consumer-owner",
      "repository_id": "pi-canary-consumer"
    },
    "store_head_digest": "sha256:e9763fada6692bdaed20c51998d14a80a25a59968d4ad519af5836009a213029",
    "store_id": "consumer-history",
    "store_revision": 1
  },
  "store_tuple_016": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://softwareco/pi-canary-consumer",
      "identity_revision": 3,
      "owner": "consumer-owner",
      "repository_id": "pi-canary-consumer"
    },
    "store_head_digest": "sha256:022db6bd641537dbd7a0f484a7f884d5e5926b33c73ffed2f32c1ebf16b1837b",
    "store_id": "consumer-acceptance",
    "store_revision": 4
  },
  "store_tuple_017": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://softwareco/pi-canary-consumer",
      "identity_revision": 3,
      "owner": "consumer-owner",
      "repository_id": "pi-canary-consumer"
    },
    "store_head_digest": "sha256:e9763fada6692bdaed20c51998d14a80a25a59968d4ad519af5836009a213029",
    "store_id": "consumer-activation",
    "store_revision": 1
  },
  "store_tuple_018": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://softwareco/pi-canary-consumer",
      "identity_revision": 3,
      "owner": "consumer-owner",
      "repository_id": "pi-canary-consumer"
    },
    "store_head_digest": "sha256:3adc831115c27950bb251d9105fad726d5b51a3ce78ede0b2bcd0e842caaf56d",
    "store_id": "consumer-history",
    "store_revision": 1
  },
  "store_tuple_019": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://softwareco/pi-canary-consumer",
      "identity_revision": 3,
      "owner": "consumer-owner",
      "repository_id": "pi-canary-consumer"
    },
    "store_head_digest": "sha256:85963e015d1f02deb662eb4bc2fc52473f8b57406fccbd1900a8fb63ab9bb479",
    "store_id": "consumer-acceptance",
    "store_revision": 4
  },
  "store_tuple_020": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://core/ontology-kernel",
      "identity_revision": 1,
      "owner": "semantic-owner",
      "repository_id": "ontology-kernel"
    },
    "store_head_digest": "sha256:27897da79174f3a605d6bb3381c179abab2660b8892a56a6f08b3f7899b95371",
    "store_id": "semantic-lifecycle-ledger",
    "store_revision": 2
  },
  "store_tuple_021": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://core/ontology-kernel",
      "identity_revision": 1,
      "owner": "semantic-owner",
      "repository_id": "ontology-kernel"
    },
    "store_head_digest": "sha256:e607d1e2bd5e268280580ef7d9425d08447b801114ec54a86f9ab651aa954aab",
    "store_id": "semantic-lifecycle-ledger",
    "store_revision": 4
  },
  "store_tuple_022": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://softwareco/pi-canary-consumer",
      "identity_revision": 3,
      "owner": "consumer-owner",
      "repository_id": "pi-canary-consumer"
    },
    "store_head_digest": "sha256:38ab72d53558e20614d75e287858fe86842c7e53ac5c18e58536bf8e37d41fb5",
    "store_id": "consumer-history",
    "store_revision": 1
  },
  "store_tuple_023": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://softwareco/pi-canary-consumer",
      "identity_revision": 3,
      "owner": "consumer-owner",
      "repository_id": "pi-canary-consumer"
    },
    "store_head_digest": "sha256:a96079eda975c94adc0bc12c4689d4ba2b4e79e3bd472b67944ab36539fa2117",
    "store_id": "consumer-acceptance",
    "store_revision": 4
  },
  "store_tuple_024": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://softwareco/pi-canary-consumer",
      "identity_revision": 3,
      "owner": "consumer-owner",
      "repository_id": "pi-canary-consumer"
    },
    "store_head_digest": "sha256:38ab72d53558e20614d75e287858fe86842c7e53ac5c18e58536bf8e37d41fb5",
    "store_id": "consumer-activation",
    "store_revision": 1
  },
  "store_tuple_025": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://softwareco/pi-canary-consumer",
      "identity_revision": 3,
      "owner": "consumer-owner",
      "repository_id": "pi-canary-consumer"
    },
    "store_head_digest": "sha256:f4326eb28d738eeff90abf5415ca62b9a8470b1d3f20b3e84ce83e443ed61f7a",
    "store_id": "consumer-activation",
    "store_revision": 2
  },
  "store_tuple_026": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://softwareco/pi-canary-consumer",
      "identity_revision": 3,
      "owner": "consumer-owner",
      "repository_id": "pi-canary-consumer"
    },
    "store_head_digest": "sha256:72154697fa7882a1aec7dc4977b56305788a529a0f7883e11290c01a7ab51f84",
    "store_id": "consumer-activation",
    "store_revision": 2
  },
  "store_tuple_027": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://core/ontology-kernel",
      "identity_revision": 1,
      "owner": "semantic-owner",
      "repository_id": "ontology-kernel"
    },
    "store_head_digest": "sha256:f0ddb7eacf3f603dda120a3429eea3a29b078f638c5f6d2d01dad98cfdab6e3a",
    "store_id": "semantic-publication-ledger",
    "store_revision": 2
  },
  "store_tuple_028": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://core/ontology-kernel",
      "identity_revision": 1,
      "owner": "semantic-owner",
      "repository_id": "ontology-kernel"
    },
    "store_head_digest": "sha256:0521f3b4d16ab7baf1d62c9289f0eb92a0502788a5add4feff2ccfe15396c7c5",
    "store_id": "semantic-lifecycle-ledger",
    "store_revision": 2
  },
  "store_tuple_029": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://core/ontology-kernel",
      "identity_revision": 1,
      "owner": "semantic-owner",
      "repository_id": "ontology-kernel"
    },
    "store_head_digest": "sha256:bea9404f8dfb36c7cf4ad25b189dc2d5a0a3802689515829566c5ceaee732fa1",
    "store_id": "semantic-lifecycle-ledger",
    "store_revision": 4
  },
  "store_tuple_030": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://core/ontology-kernel",
      "identity_revision": 1,
      "owner": "semantic-owner",
      "repository_id": "ontology-kernel"
    },
    "store_head_digest": "sha256:49e36b944128f9e2d23932c3ff10b01512a2ae089ab522b28abfebfea12dfeb2",
    "store_id": "semantic-publication-ledger",
    "store_revision": 1
  },
  "store_tuple_031": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://core/ontology-kernel",
      "identity_revision": 1,
      "owner": "semantic-owner",
      "repository_id": "ontology-kernel"
    },
    "store_head_digest": "sha256:b163435d7c7d94df6c411fa9c6e4101e95dbbf06a0c8e583588933e68a5b1e36",
    "store_id": "semantic-publication-ledger",
    "store_revision": 1
  },
  "store_tuple_032": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://core/ontology-kernel",
      "identity_revision": 1,
      "owner": "semantic-owner",
      "repository_id": "ontology-kernel"
    },
    "store_head_digest": "sha256:396454158c7c36f1c5579c34bf368ec286d2f6e36c744d659756cee936f97345",
    "store_id": "semantic-publication-ledger",
    "store_revision": 2
  },
  "store_tuple_033": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://core/ontology-kernel",
      "identity_revision": 1,
      "owner": "semantic-owner",
      "repository_id": "ontology-kernel"
    },
    "store_head_digest": "sha256:eb67d8651ccbae0eb9d0b721759dec6b17ee832376e647c8fbe5c26a0059f0d4",
    "store_id": "semantic-publication-ledger",
    "store_revision": 3
  },
  "store_tuple_034": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://core/ontology-kernel",
      "identity_revision": 1,
      "owner": "semantic-owner",
      "repository_id": "ontology-kernel"
    },
    "store_head_digest": "sha256:29925ca0639fab5f10cb65511a964c7010dcd72c34dc9b29e887d6d2a221f5a5",
    "store_id": "semantic-publication-ledger",
    "store_revision": 2
  },
  "store_tuple_035": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://softwareco/pi-canary-consumer",
      "identity_revision": 3,
      "owner": "consumer-owner",
      "repository_id": "pi-canary-consumer"
    },
    "store_head_digest": "sha256:3fbf659e74dedb9fb9228de85d9dab08ec5a2221112af73ebd98223308cd83a6",
    "store_id": "consumer-history",
    "store_revision": 1
  },
  "store_tuple_036": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://softwareco/pi-canary-consumer",
      "identity_revision": 3,
      "owner": "consumer-owner",
      "repository_id": "pi-canary-consumer"
    },
    "store_head_digest": "sha256:06ca20c5f4094172c785fa12542cda5f69506bea62a210f4ff881777f6f8a27a",
    "store_id": "consumer-acceptance",
    "store_revision": 4
  },
  "store_tuple_037": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://softwareco/pi-canary-consumer",
      "identity_revision": 3,
      "owner": "consumer-owner",
      "repository_id": "pi-canary-consumer"
    },
    "store_head_digest": "sha256:3fbf659e74dedb9fb9228de85d9dab08ec5a2221112af73ebd98223308cd83a6",
    "store_id": "consumer-activation",
    "store_revision": 1
  },
  "store_tuple_038": {
    "action_epoch": 100,
    "owner_repository": {
      "canonical_locator": "local://core/ontology-kernel",
      "identity_revision": 1,
      "owner": "semantic-owner",
      "repository_id": "ontology-kernel"
    },
    "store_head_digest": "sha256:139a530837150a6a28dd46c8ebf84a6dca663ce0286742604be10ac4888cc389",
    "store_id": "semantic-vote:owner-c",
    "store_revision": 1
  }
}
''')
EXPLICIT_STORE_METADATA_SETS = json.loads(r'''
{
  "store_source_000": {
    "canonical_publication_head": "store_tuple_000",
    "canonical_publication_journal_head": "store_tuple_000",
    "canonical_publication_revision": "store_tuple_000",
    "canonical_publication_status_digest": "store_tuple_000",
    "canonical_recovery_controller_id": "store_tuple_001",
    "canonical_recovery_epoch": "store_tuple_001",
    "canonical_recovery_journal_head": "store_tuple_000",
    "canonical_recovery_resulting_head": "store_tuple_000",
    "canonical_recovery_resulting_revision": "store_tuple_000",
    "canonical_recovery_resulting_status_digest": "store_tuple_000",
    "canonical_recovery_runtime_identity": "store_tuple_001",
    "canonical_recovery_transaction_digest": "store_tuple_000"
  },
  "store_source_001": {
    "canonical_publication_head": "store_tuple_002",
    "canonical_publication_revision": "store_tuple_002",
    "canonical_store_head": "store_tuple_003",
    "canonical_trust_revocation_head": "store_tuple_004",
    "canonical_trust_revocation_revision": "store_tuple_004",
    "canonical_trust_root_digest": "store_tuple_005",
    "current_acceptance_digest": "store_tuple_006",
    "current_acceptance_revision": "store_tuple_006",
    "current_decision_record_digest": "store_tuple_003",
    "revoked_trust_digests": "store_tuple_004"
  },
  "store_source_002": {
    "canonical_publication_head": "store_tuple_002",
    "canonical_publication_revision": "store_tuple_002",
    "canonical_recovery_controller_id": "store_tuple_001",
    "canonical_recovery_epoch": "store_tuple_001",
    "canonical_recovery_runtime_identity": "store_tuple_001",
    "canonical_store_head": "store_tuple_003",
    "canonical_trust_revocation_head": "store_tuple_004",
    "canonical_trust_revocation_revision": "store_tuple_004",
    "canonical_trust_root_digest": "store_tuple_005",
    "current_acceptance_digest": "store_tuple_006",
    "current_acceptance_revision": "store_tuple_006",
    "current_activation_digest": "store_tuple_007",
    "current_activation_revision": "store_tuple_007",
    "current_decision_record_digest": "store_tuple_003",
    "revoked_trust_digests": "store_tuple_004"
  },
  "store_source_003": {
    "canonical_publication_head": "store_tuple_002",
    "canonical_publication_revision": "store_tuple_002",
    "canonical_recovery_controller_id": "store_tuple_001",
    "canonical_recovery_epoch": "store_tuple_001",
    "canonical_recovery_runtime_identity": "store_tuple_001",
    "canonical_store_head": "store_tuple_003",
    "canonical_trust_revocation_head": "store_tuple_004",
    "canonical_trust_revocation_revision": "store_tuple_004",
    "canonical_trust_root_digest": "store_tuple_005",
    "current_acceptance_digest": "store_tuple_006",
    "current_acceptance_revision": "store_tuple_006",
    "current_activation_digest": "store_tuple_008",
    "current_activation_revision": "store_tuple_008",
    "current_decision_record_digest": "store_tuple_003",
    "revoked_trust_digests": "store_tuple_004"
  },
  "store_source_004": {
    "canonical_publication_head": "store_tuple_002",
    "canonical_publication_revision": "store_tuple_002",
    "canonical_recovery_controller_id": "store_tuple_001",
    "canonical_recovery_epoch": "store_tuple_001",
    "canonical_recovery_runtime_identity": "store_tuple_001",
    "canonical_store_head": "store_tuple_003",
    "canonical_trust_revocation_head": "store_tuple_004",
    "canonical_trust_revocation_revision": "store_tuple_004",
    "canonical_trust_root_digest": "store_tuple_005",
    "current_acceptance_digest": "store_tuple_006",
    "current_acceptance_revision": "store_tuple_006",
    "current_activation_digest": "store_tuple_009",
    "current_activation_revision": "store_tuple_009",
    "current_decision_record_digest": "store_tuple_003",
    "revoked_trust_digests": "store_tuple_004"
  },
  "store_source_005": {
    "canonical_task_states": "store_tuple_003"
  },
  "store_source_006": {},
  "store_source_007": {
    "canonical_store_head": "store_tuple_003",
    "current_decision_record_digest": "store_tuple_003"
  },
  "store_source_008": {
    "canonical_lifecycle_tombstone_head": "store_tuple_012"
  },
  "store_source_009": {
    "canonical_publication_head": "store_tuple_013",
    "canonical_publication_journal_head": "store_tuple_014",
    "canonical_publication_revision": "store_tuple_013",
    "canonical_store_head": "store_tuple_003",
    "canonical_trust_revocation_head": "store_tuple_004",
    "canonical_trust_revocation_revision": "store_tuple_004",
    "canonical_trust_root_digest": "store_tuple_005",
    "current_decision_record_digest": "store_tuple_003",
    "external_trust_root_pin": "store_tuple_005",
    "revoked_trust_digests": "store_tuple_004"
  },
  "store_source_010": {
    "canonical_publication_head": "store_tuple_013",
    "canonical_publication_journal_head": "store_tuple_014",
    "canonical_publication_revision": "store_tuple_013",
    "canonical_trust_revocation_head": "store_tuple_004",
    "canonical_trust_revocation_revision": "store_tuple_004",
    "canonical_trust_root_digest": "store_tuple_005",
    "current_decision_record_digest": "store_tuple_003",
    "external_trust_root_pin": "store_tuple_005",
    "revoked_trust_digests": "store_tuple_004"
  },
  "store_source_011": {
    "canonical_publication_head": "store_tuple_013",
    "canonical_publication_journal_head": "store_tuple_014",
    "canonical_publication_revision": "store_tuple_013",
    "canonical_store_head": "store_tuple_003",
    "canonical_trust_revocation_head": "store_tuple_004",
    "canonical_trust_revocation_revision": "store_tuple_004",
    "canonical_trust_root_digest": "store_tuple_005",
    "external_trust_root_pin": "store_tuple_005",
    "revoked_trust_digests": "store_tuple_004"
  },
  "store_source_012": {
    "canonical_history_head": "store_tuple_015",
    "canonical_publication_head": "store_tuple_002",
    "canonical_publication_revision": "store_tuple_002",
    "canonical_recovery_controller_id": "store_tuple_001",
    "canonical_recovery_epoch": "store_tuple_001",
    "canonical_recovery_runtime_identity": "store_tuple_001",
    "canonical_store_head": "store_tuple_003",
    "canonical_trust_revocation_head": "store_tuple_004",
    "canonical_trust_revocation_revision": "store_tuple_004",
    "canonical_trust_root_digest": "store_tuple_005",
    "current_acceptance_digest": "store_tuple_016",
    "current_acceptance_revision": "store_tuple_016",
    "current_activation_digest": "store_tuple_017",
    "current_activation_revision": "store_tuple_017",
    "current_decision_record_digest": "store_tuple_003",
    "revoked_trust_digests": "store_tuple_004"
  },
  "store_source_013": {
    "canonical_history_head": "store_tuple_018",
    "canonical_publication_head": "store_tuple_002",
    "canonical_publication_revision": "store_tuple_002",
    "canonical_recovery_controller_id": "store_tuple_001",
    "canonical_recovery_epoch": "store_tuple_001",
    "canonical_recovery_runtime_identity": "store_tuple_001",
    "canonical_store_head": "store_tuple_003",
    "canonical_trust_revocation_head": "store_tuple_004",
    "canonical_trust_revocation_revision": "store_tuple_004",
    "canonical_trust_root_digest": "store_tuple_005",
    "current_acceptance_digest": "store_tuple_006",
    "current_acceptance_revision": "store_tuple_006",
    "current_activation_digest": "store_tuple_008",
    "current_activation_revision": "store_tuple_008",
    "current_decision_record_digest": "store_tuple_003",
    "revoked_trust_digests": "store_tuple_004"
  },
  "store_source_014": {
    "canonical_publication_head": "store_tuple_002",
    "canonical_publication_revision": "store_tuple_002",
    "canonical_store_head": "store_tuple_003",
    "canonical_trust_revocation_head": "store_tuple_004",
    "canonical_trust_revocation_revision": "store_tuple_004",
    "canonical_trust_root_digest": "store_tuple_005",
    "current_acceptance_digest": "store_tuple_019",
    "current_acceptance_revision": "store_tuple_019",
    "current_decision_record_digest": "store_tuple_003",
    "revoked_trust_digests": "store_tuple_004"
  },
  "store_source_015": {
    "canonical_deprecation_head": "store_tuple_020",
    "canonical_deprecation_revision": "store_tuple_020",
    "canonical_removal_head": "store_tuple_021",
    "canonical_removal_revision": "store_tuple_021",
    "canonical_store_head": "store_tuple_003",
    "canonical_trust_revocation_head": "store_tuple_004",
    "canonical_trust_revocation_revision": "store_tuple_004",
    "canonical_trust_root_digest": "store_tuple_005",
    "current_deprecation_decision_record_digest": "store_tuple_003",
    "current_lifecycle_head": "store_tuple_012",
    "current_removal_decision_record_digest": "store_tuple_003",
    "deprecation_prior_head": "store_tuple_012",
    "external_trust_root_pin": "store_tuple_005",
    "revoked_trust_digests": "store_tuple_004"
  },
  "store_source_016": {
    "canonical_history_head": "store_tuple_022",
    "canonical_publication_head": "store_tuple_002",
    "canonical_publication_revision": "store_tuple_002",
    "canonical_recovery_controller_id": "store_tuple_001",
    "canonical_recovery_epoch": "store_tuple_001",
    "canonical_recovery_runtime_identity": "store_tuple_001",
    "canonical_store_head": "store_tuple_003",
    "canonical_trust_revocation_head": "store_tuple_004",
    "canonical_trust_revocation_revision": "store_tuple_004",
    "canonical_trust_root_digest": "store_tuple_005",
    "current_acceptance_digest": "store_tuple_023",
    "current_acceptance_revision": "store_tuple_023",
    "current_activation_digest": "store_tuple_024",
    "current_activation_revision": "store_tuple_024",
    "current_decision_record_digest": "store_tuple_003",
    "revoked_trust_digests": "store_tuple_004"
  },
  "store_source_017": {
    "canonical_publication_head": "store_tuple_002",
    "canonical_publication_revision": "store_tuple_002",
    "canonical_recovery_controller_id": "store_tuple_001",
    "canonical_recovery_epoch": "store_tuple_001",
    "canonical_recovery_runtime_identity": "store_tuple_001",
    "canonical_store_head": "store_tuple_003",
    "canonical_trust_revocation_head": "store_tuple_004",
    "canonical_trust_revocation_revision": "store_tuple_004",
    "canonical_trust_root_digest": "store_tuple_005",
    "current_acceptance_digest": "store_tuple_006",
    "current_acceptance_revision": "store_tuple_006",
    "current_activation_digest": "store_tuple_025",
    "current_activation_revision": "store_tuple_025",
    "current_decision_record_digest": "store_tuple_003",
    "revoked_trust_digests": "store_tuple_004"
  },
  "store_source_018": {
    "canonical_publication_head": "store_tuple_002",
    "canonical_publication_revision": "store_tuple_002",
    "canonical_recovery_controller_id": "store_tuple_001",
    "canonical_recovery_epoch": "store_tuple_001",
    "canonical_recovery_runtime_identity": "store_tuple_001",
    "canonical_store_head": "store_tuple_003",
    "canonical_trust_revocation_head": "store_tuple_004",
    "canonical_trust_revocation_revision": "store_tuple_004",
    "canonical_trust_root_digest": "store_tuple_005",
    "current_acceptance_digest": "store_tuple_006",
    "current_acceptance_revision": "store_tuple_006",
    "current_activation_digest": "store_tuple_026",
    "current_activation_revision": "store_tuple_026",
    "current_decision_record_digest": "store_tuple_003",
    "revoked_trust_digests": "store_tuple_004"
  },
  "store_source_019": {
    "canonical_publication_head": "store_tuple_002",
    "canonical_publication_journal_head": "store_tuple_027",
    "canonical_publication_revision": "store_tuple_002",
    "canonical_store_head": "store_tuple_003",
    "canonical_trust_revocation_head": "store_tuple_004",
    "canonical_trust_revocation_revision": "store_tuple_004",
    "canonical_trust_root_digest": "store_tuple_005",
    "current_decision_record_digest": "store_tuple_003",
    "external_trust_root_pin": "store_tuple_005",
    "revoked_trust_digests": "store_tuple_004"
  },
  "store_source_020": {
    "canonical_deprecation_head": "store_tuple_028",
    "canonical_deprecation_revision": "store_tuple_028",
    "canonical_removal_head": "store_tuple_021",
    "canonical_removal_revision": "store_tuple_021",
    "canonical_store_head": "store_tuple_003",
    "canonical_trust_revocation_head": "store_tuple_004",
    "canonical_trust_revocation_revision": "store_tuple_004",
    "canonical_trust_root_digest": "store_tuple_005",
    "current_deprecation_decision_record_digest": "store_tuple_003",
    "current_lifecycle_head": "store_tuple_012",
    "current_removal_decision_record_digest": "store_tuple_003",
    "deprecation_prior_head": "store_tuple_012",
    "external_trust_root_pin": "store_tuple_005",
    "revoked_trust_digests": "store_tuple_004"
  },
  "store_source_021": {
    "canonical_deprecation_head": "store_tuple_020",
    "canonical_deprecation_revision": "store_tuple_020",
    "canonical_removal_head": "store_tuple_029",
    "canonical_removal_revision": "store_tuple_029",
    "canonical_store_head": "store_tuple_003",
    "canonical_trust_revocation_head": "store_tuple_004",
    "canonical_trust_revocation_revision": "store_tuple_004",
    "canonical_trust_root_digest": "store_tuple_005",
    "current_deprecation_decision_record_digest": "store_tuple_003",
    "current_lifecycle_head": "store_tuple_012",
    "current_removal_decision_record_digest": "store_tuple_003",
    "deprecation_prior_head": "store_tuple_012",
    "external_trust_root_pin": "store_tuple_005",
    "revoked_trust_digests": "store_tuple_004"
  },
  "store_source_022": {
    "existing_coordinate": "store_tuple_002"
  },
  "store_source_023": {
    "current_head": "store_tuple_030",
    "current_revision": "store_tuple_030",
    "existing_coordinate": "store_tuple_030",
    "existing_operation": "store_tuple_030",
    "existing_replay_key": "store_tuple_030"
  },
  "store_source_024": {
    "canonical_publication_head": "store_tuple_031",
    "canonical_publication_journal_head": "store_tuple_014",
    "canonical_publication_revision": "store_tuple_031",
    "canonical_store_head": "store_tuple_003",
    "canonical_trust_revocation_head": "store_tuple_004",
    "canonical_trust_revocation_revision": "store_tuple_004",
    "canonical_trust_root_digest": "store_tuple_005",
    "current_decision_record_digest": "store_tuple_003",
    "external_trust_root_pin": "store_tuple_005",
    "revoked_trust_digests": "store_tuple_004"
  },
  "store_source_025": {
    "current_head": "store_tuple_013",
    "current_revision": "store_tuple_013",
    "existing_coordinate": "store_tuple_013",
    "existing_operation": "store_tuple_013",
    "existing_replay_key": "store_tuple_013"
  },
  "store_source_026": {
    "current_head": "store_tuple_002",
    "current_revision": "store_tuple_002",
    "existing_coordinate": "store_tuple_002",
    "existing_operation": "store_tuple_002",
    "existing_replay_key": "store_tuple_002"
  },
  "store_source_027": {
    "canonical_publication_head": "store_tuple_032",
    "canonical_publication_journal_head": "store_tuple_027",
    "canonical_publication_revision": "store_tuple_032",
    "canonical_store_head": "store_tuple_003",
    "canonical_trust_revocation_head": "store_tuple_004",
    "canonical_trust_revocation_revision": "store_tuple_004",
    "canonical_trust_root_digest": "store_tuple_005",
    "current_decision_record_digest": "store_tuple_003",
    "external_trust_root_pin": "store_tuple_005",
    "revoked_trust_digests": "store_tuple_004"
  },
  "store_source_028": {
    "canonical_store_head": "store_tuple_003",
    "current_decision_record_digest": "store_tuple_003",
    "prior_head": "store_tuple_004",
    "prior_revision": "store_tuple_004"
  },
  "store_source_029": {
    "canonical_publication_head": "store_tuple_033",
    "canonical_publication_journal_head": "store_tuple_034",
    "canonical_publication_revision": "store_tuple_033",
    "canonical_store_head": "store_tuple_003",
    "canonical_trust_revocation_head": "store_tuple_004",
    "canonical_trust_revocation_revision": "store_tuple_004",
    "canonical_trust_root_digest": "store_tuple_005",
    "current_decision_record_digest": "store_tuple_003",
    "external_trust_root_pin": "store_tuple_005",
    "revoked_trust_digests": "store_tuple_004"
  },
  "store_source_030": {
    "canonical_store_head": "store_tuple_003",
    "current_decision_record_digest": "store_tuple_003",
    "current_root_digest": "store_tuple_005",
    "revoked": "store_tuple_004"
  },
  "store_source_031": {
    "canonical_history_head": "store_tuple_035",
    "canonical_publication_head": "store_tuple_002",
    "canonical_publication_revision": "store_tuple_002",
    "canonical_recovery_controller_id": "store_tuple_001",
    "canonical_recovery_epoch": "store_tuple_001",
    "canonical_recovery_runtime_identity": "store_tuple_001",
    "canonical_store_head": "store_tuple_003",
    "canonical_trust_revocation_head": "store_tuple_004",
    "canonical_trust_revocation_revision": "store_tuple_004",
    "canonical_trust_root_digest": "store_tuple_005",
    "current_acceptance_digest": "store_tuple_036",
    "current_acceptance_revision": "store_tuple_036",
    "current_activation_digest": "store_tuple_037",
    "current_activation_revision": "store_tuple_037",
    "current_decision_record_digest": "store_tuple_003",
    "revoked_trust_digests": "store_tuple_004"
  }
}
''')
EXPLICIT_VOTE_SOURCE_SETS = json.loads(r'''
{
  "vote_source_000": {},
  "vote_source_001": {
    "vote-proof:override_approvals:sha256:1d7cbfdede41b00970285503e5ac71bbca43d3c71eec872ba4e21f56e63b6b64:owner-a": {
      "fact": {
        "approval_proof_digest": "sha256:f0da5df238378cafd49e89cbde1460eed636dc7fe99f63733772e4aac56c20c1",
        "approved_action_digest": "sha256:3f2661f3afe4ce419e0116fa60833453d7e1b1339083fbd1aeb761ad15ed5de7",
        "owner_id": "owner-a",
        "owner_key_id": "owner-a-key-3"
      },
      "store_metadata_tuple": "store_tuple_010"
    },
    "vote-proof:override_approvals:sha256:1d7cbfdede41b00970285503e5ac71bbca43d3c71eec872ba4e21f56e63b6b64:owner-b": {
      "fact": {
        "approval_proof_digest": "sha256:cffff25d9a05bf379d92699d30a34f0b2e93a3fcd8e2fd45012357025e31e509",
        "approved_action_digest": "sha256:3f2661f3afe4ce419e0116fa60833453d7e1b1339083fbd1aeb761ad15ed5de7",
        "owner_id": "owner-b",
        "owner_key_id": "owner-b-key-2"
      },
      "store_metadata_tuple": "store_tuple_011"
    }
  },
  "vote_source_002": {
    "vote-proof:subject:owner-a": {
      "fact": {
        "approval_proof_digest": "sha256:c0d1205a6a053e3cc6aa4733e8ffd41a9d20c2a50c6a20d942aaf67ec4b6fc09",
        "approved_action_digest": "sha256:f68efe345d97675f0c885ce5421488f7b591114201576f4fbedd1c051d280e48",
        "owner_id": "owner-a",
        "owner_key_id": "owner-a-key-3"
      },
      "store_metadata_tuple": "store_tuple_010"
    },
    "vote-proof:subject:owner-b": {
      "fact": {
        "approval_proof_digest": "sha256:88810817187802f0dd0b3e7d1d6004d2696f6a7d3b3850527ae91a130b15b2d3",
        "approved_action_digest": "sha256:f68efe345d97675f0c885ce5421488f7b591114201576f4fbedd1c051d280e48",
        "owner_id": "owner-b",
        "owner_key_id": "owner-b-key-2"
      },
      "store_metadata_tuple": "store_tuple_011"
    }
  },
  "vote_source_003": {
    "vote-proof:approval:owner-a": {
      "fact": {
        "approval_proof_digest": "sha256:c0d1205a6a053e3cc6aa4733e8ffd41a9d20c2a50c6a20d942aaf67ec4b6fc09",
        "approved_action_digest": "sha256:f68efe345d97675f0c885ce5421488f7b591114201576f4fbedd1c051d280e48",
        "owner_id": "owner-a",
        "owner_key_id": "owner-a-key-3"
      },
      "store_metadata_tuple": "store_tuple_010"
    },
    "vote-proof:approval:owner-b": {
      "fact": {
        "approval_proof_digest": "sha256:88810817187802f0dd0b3e7d1d6004d2696f6a7d3b3850527ae91a130b15b2d3",
        "approved_action_digest": "sha256:f68efe345d97675f0c885ce5421488f7b591114201576f4fbedd1c051d280e48",
        "owner_id": "owner-b",
        "owner_key_id": "owner-b-key-2"
      },
      "store_metadata_tuple": "store_tuple_011"
    }
  },
  "vote_source_004": {
    "vote-proof:deprecation_approval:owner-a": {
      "fact": {
        "approval_proof_digest": "sha256:c0d1205a6a053e3cc6aa4733e8ffd41a9d20c2a50c6a20d942aaf67ec4b6fc09",
        "approved_action_digest": "sha256:f68efe345d97675f0c885ce5421488f7b591114201576f4fbedd1c051d280e48",
        "owner_id": "owner-a",
        "owner_key_id": "owner-a-key-3"
      },
      "store_metadata_tuple": "store_tuple_010"
    },
    "vote-proof:deprecation_approval:owner-b": {
      "fact": {
        "approval_proof_digest": "sha256:88810817187802f0dd0b3e7d1d6004d2696f6a7d3b3850527ae91a130b15b2d3",
        "approved_action_digest": "sha256:f68efe345d97675f0c885ce5421488f7b591114201576f4fbedd1c051d280e48",
        "owner_id": "owner-b",
        "owner_key_id": "owner-b-key-2"
      },
      "store_metadata_tuple": "store_tuple_011"
    },
    "vote-proof:removal_approval:owner-a": {
      "fact": {
        "approval_proof_digest": "sha256:c3e9b597af24ce61eef5d0cb8dd384a1604a6c35192b2962b4394ca6ee07d077",
        "approved_action_digest": "sha256:5179b5544dec9dad8df59ba74b794ddbd91ce1b78cd60ec97d8023f67e908808",
        "owner_id": "owner-a",
        "owner_key_id": "owner-a-key-3"
      },
      "store_metadata_tuple": "store_tuple_010"
    },
    "vote-proof:removal_approval:owner-b": {
      "fact": {
        "approval_proof_digest": "sha256:c587f8ac2da3a5c798355579952ec7f5bc53fad68de675c20cb349561a09f944",
        "approved_action_digest": "sha256:5179b5544dec9dad8df59ba74b794ddbd91ce1b78cd60ec97d8023f67e908808",
        "owner_id": "owner-b",
        "owner_key_id": "owner-b-key-2"
      },
      "store_metadata_tuple": "store_tuple_011"
    }
  },
  "vote_source_005": {
    "vote-proof:override_approvals:sha256:b86ad6f54616bbbf65c9b4ff99a34ccfd57cdc43e1420002e4ae9db4106a635b:owner-a": {
      "fact": {
        "approval_proof_digest": "sha256:f0da5df238378cafd49e89cbde1460eed636dc7fe99f63733772e4aac56c20c1",
        "approved_action_digest": "sha256:3f2661f3afe4ce419e0116fa60833453d7e1b1339083fbd1aeb761ad15ed5de7",
        "owner_id": "owner-a",
        "owner_key_id": "owner-a-key-3"
      },
      "store_metadata_tuple": "store_tuple_010"
    },
    "vote-proof:override_approvals:sha256:b86ad6f54616bbbf65c9b4ff99a34ccfd57cdc43e1420002e4ae9db4106a635b:owner-b": {
      "fact": {
        "approval_proof_digest": "sha256:cffff25d9a05bf379d92699d30a34f0b2e93a3fcd8e2fd45012357025e31e509",
        "approved_action_digest": "sha256:3f2661f3afe4ce419e0116fa60833453d7e1b1339083fbd1aeb761ad15ed5de7",
        "owner_id": "owner-b",
        "owner_key_id": "owner-b-key-2"
      },
      "store_metadata_tuple": "store_tuple_011"
    }
  },
  "vote_source_006": {
    "vote-proof:approval:owner-a": {
      "fact": {
        "approval_proof_digest": "sha256:9ebb96454a6c5835fbdbf5197c5a461aac583a02ed7ec390907020c0e826a3a2",
        "approved_action_digest": "sha256:170070223aabfcde5a3f274cd31979e27333f9bfde0d46a3b419b9f30408b45f",
        "owner_id": "owner-a",
        "owner_key_id": "owner-a-key-3"
      },
      "store_metadata_tuple": "store_tuple_010"
    },
    "vote-proof:approval:owner-b": {
      "fact": {
        "approval_proof_digest": "sha256:e2c9d8c4e9ffd2dc2419a27d31ad5a8d9305b13d61b28fb27e8a3d8e46cf6040",
        "approved_action_digest": "sha256:170070223aabfcde5a3f274cd31979e27333f9bfde0d46a3b419b9f30408b45f",
        "owner_id": "owner-b",
        "owner_key_id": "owner-b-key-2"
      },
      "store_metadata_tuple": "store_tuple_011"
    }
  },
  "vote_source_007": {
    "vote-proof:override_approvals:sha256:21c413976379f8a57c8aab67aa5b9493bbb5ba7982db59dad0d27df574e9df30:owner-a": {
      "fact": {
        "approval_proof_digest": "sha256:f0da5df238378cafd49e89cbde1460eed636dc7fe99f63733772e4aac56c20c1",
        "approved_action_digest": "sha256:3f2661f3afe4ce419e0116fa60833453d7e1b1339083fbd1aeb761ad15ed5de7",
        "owner_id": "owner-a",
        "owner_key_id": "owner-a-key-3"
      },
      "store_metadata_tuple": "store_tuple_010"
    },
    "vote-proof:override_approvals:sha256:21c413976379f8a57c8aab67aa5b9493bbb5ba7982db59dad0d27df574e9df30:owner-b": {
      "fact": {
        "approval_proof_digest": "sha256:cffff25d9a05bf379d92699d30a34f0b2e93a3fcd8e2fd45012357025e31e509",
        "approved_action_digest": "sha256:3f2661f3afe4ce419e0116fa60833453d7e1b1339083fbd1aeb761ad15ed5de7",
        "owner_id": "owner-b",
        "owner_key_id": "owner-b-key-2"
      },
      "store_metadata_tuple": "store_tuple_011"
    }
  },
  "vote_source_008": {
    "vote-proof:override_approvals:sha256:8e197e19664411c4bea7f07f6eaaf522a63c49b1441c40fac3bd9cb541537c58:owner-a": {
      "fact": {
        "approval_proof_digest": "sha256:f0da5df238378cafd49e89cbde1460eed636dc7fe99f63733772e4aac56c20c1",
        "approved_action_digest": "sha256:416bfd5bbd74a4ec63ee58caf11c51c3750a70a3157dc2ad2c3d38562de03b49",
        "owner_id": "owner-a",
        "owner_key_id": "owner-a-key-3"
      },
      "store_metadata_tuple": "store_tuple_010"
    },
    "vote-proof:override_approvals:sha256:8e197e19664411c4bea7f07f6eaaf522a63c49b1441c40fac3bd9cb541537c58:owner-b": {
      "fact": {
        "approval_proof_digest": "sha256:cffff25d9a05bf379d92699d30a34f0b2e93a3fcd8e2fd45012357025e31e509",
        "approved_action_digest": "sha256:416bfd5bbd74a4ec63ee58caf11c51c3750a70a3157dc2ad2c3d38562de03b49",
        "owner_id": "owner-b",
        "owner_key_id": "owner-b-key-2"
      },
      "store_metadata_tuple": "store_tuple_011"
    }
  },
  "vote_source_009": {
    "vote-proof:approval:owner-a": {
      "fact": {
        "approval_proof_digest": "sha256:c0d1205a6a053e3cc6aa4733e8ffd41a9d20c2a50c6a20d942aaf67ec4b6fc09",
        "approved_action_digest": "sha256:03be945c72e799c7bf8628bff70f41e82947e90fce9e98435fd920cd88aeb1cf",
        "owner_id": "owner-a",
        "owner_key_id": "owner-a-key-3"
      },
      "store_metadata_tuple": "store_tuple_010"
    },
    "vote-proof:approval:owner-b": {
      "fact": {
        "approval_proof_digest": "sha256:88810817187802f0dd0b3e7d1d6004d2696f6a7d3b3850527ae91a130b15b2d3",
        "approved_action_digest": "sha256:03be945c72e799c7bf8628bff70f41e82947e90fce9e98435fd920cd88aeb1cf",
        "owner_id": "owner-b",
        "owner_key_id": "owner-b-key-2"
      },
      "store_metadata_tuple": "store_tuple_011"
    }
  },
  "vote_source_010": {
    "vote-proof:approval:owner-a": {
      "fact": {
        "approval_proof_digest": "sha256:c0d1205a6a053e3cc6aa4733e8ffd41a9d20c2a50c6a20d942aaf67ec4b6fc09",
        "approved_action_digest": "sha256:f68efe345d97675f0c885ce5421488f7b591114201576f4fbedd1c051d280e48",
        "owner_id": "owner-a",
        "owner_key_id": "owner-a-key-3"
      },
      "store_metadata_tuple": "store_tuple_010"
    }
  },
  "vote_source_011": {
    "vote-proof:approval:owner-a": {
      "fact": {
        "approval_proof_digest": "sha256:ecd981005e917275299c350042d143c09ec94f972a7824dbcbea09202312663e",
        "approved_action_digest": "sha256:c84ff7e5c262e1a6065ada185d038347afef3c313a727c48cab2338ca2029858",
        "owner_id": "owner-a",
        "owner_key_id": "owner-a-key-3"
      },
      "store_metadata_tuple": "store_tuple_010"
    },
    "vote-proof:approval:owner-b": {
      "fact": {
        "approval_proof_digest": "sha256:4a2fb8a1a9a7488173de7780ba9fd49f502c044ab5ad3be7e7d3ed693a756d3c",
        "approved_action_digest": "sha256:c84ff7e5c262e1a6065ada185d038347afef3c313a727c48cab2338ca2029858",
        "owner_id": "owner-b",
        "owner_key_id": "owner-b-key-2"
      },
      "store_metadata_tuple": "store_tuple_011"
    }
  },
  "vote_source_012": {
    "vote-proof:approval:owner-a": {
      "fact": {
        "approval_proof_digest": "sha256:6a238db3e74732c43071fca9ce7cd67a0d9b1388b6869b83bc2082352eddb71b",
        "approved_action_digest": "sha256:001f88d5f5e8bf2aa9e1eb6d96b46e80673f9519891e54f429344b7cac5c2f65",
        "owner_id": "owner-a",
        "owner_key_id": "owner-a-key-3"
      },
      "store_metadata_tuple": "store_tuple_010"
    },
    "vote-proof:approval:owner-b": {
      "fact": {
        "approval_proof_digest": "sha256:4443167dfc54b2f14461ef324622862f1cd92bd81ef25fa2197248b64cd0647d",
        "approved_action_digest": "sha256:001f88d5f5e8bf2aa9e1eb6d96b46e80673f9519891e54f429344b7cac5c2f65",
        "owner_id": "owner-b",
        "owner_key_id": "owner-b-key-2"
      },
      "store_metadata_tuple": "store_tuple_011"
    }
  },
  "vote_source_013": {
    "vote-proof:approval:owner-a": {
      "fact": {
        "approval_proof_digest": "sha256:9ed4e132c544f1b9dc7ba591351b28eb0f85caa79cd67608e7d2735cc808fd49",
        "approved_action_digest": "sha256:2e0c2395f7a58f0a5c3ab59ea76a9bc5aa744dd14b90857c25b5ce48bdd798bf",
        "owner_id": "owner-a",
        "owner_key_id": "owner-a-key-3"
      },
      "store_metadata_tuple": "store_tuple_010"
    },
    "vote-proof:approval:owner-b": {
      "fact": {
        "approval_proof_digest": "sha256:4a66d94840258cae36d1eeb9bf20c90c892b6b5188bfe33b7f63192f0796b8f7",
        "approved_action_digest": "sha256:2e0c2395f7a58f0a5c3ab59ea76a9bc5aa744dd14b90857c25b5ce48bdd798bf",
        "owner_id": "owner-b",
        "owner_key_id": "owner-b-key-2"
      },
      "store_metadata_tuple": "store_tuple_011"
    }
  },
  "vote_source_014": {
    "vote-proof:subject:owner-a": {
      "fact": {
        "approval_proof_digest": "sha256:c0d1205a6a053e3cc6aa4733e8ffd41a9d20c2a50c6a20d942aaf67ec4b6fc09",
        "approved_action_digest": "sha256:f68efe345d97675f0c885ce5421488f7b591114201576f4fbedd1c051d280e48",
        "owner_id": "owner-a",
        "owner_key_id": "owner-a-key-3"
      },
      "store_metadata_tuple": "store_tuple_010"
    }
  },
  "vote_source_015": {
    "vote-proof:approval:owner-a": {
      "fact": {
        "approval_proof_digest": "sha256:6a238db3e74732c43071fca9ce7cd67a0d9b1388b6869b83bc2082352eddb71b",
        "approved_action_digest": "sha256:1b99612ffb1567c30cfd91ed30189f907fb7d47e1bf9739f6a812c7bf6ea18ec",
        "owner_id": "owner-a",
        "owner_key_id": "owner-a-key-3"
      },
      "store_metadata_tuple": "store_tuple_010"
    },
    "vote-proof:approval:owner-b": {
      "fact": {
        "approval_proof_digest": "sha256:4443167dfc54b2f14461ef324622862f1cd92bd81ef25fa2197248b64cd0647d",
        "approved_action_digest": "sha256:1b99612ffb1567c30cfd91ed30189f907fb7d47e1bf9739f6a812c7bf6ea18ec",
        "owner_id": "owner-b",
        "owner_key_id": "owner-b-key-2"
      },
      "store_metadata_tuple": "store_tuple_011"
    }
  },
  "vote_source_016": {
    "vote-proof:subject:owner-a": {
      "fact": {
        "approval_proof_digest": "sha256:c0d1205a6a053e3cc6aa4733e8ffd41a9d20c2a50c6a20d942aaf67ec4b6fc09",
        "approved_action_digest": "sha256:f68efe345d97675f0c885ce5421488f7b591114201576f4fbedd1c051d280e48",
        "owner_id": "owner-a",
        "owner_key_id": "owner-a-key-3"
      },
      "store_metadata_tuple": "store_tuple_010"
    },
    "vote-proof:subject:owner-b": {
      "fact": {
        "approval_proof_digest": "sha256:88810817187802f0dd0b3e7d1d6004d2696f6a7d3b3850527ae91a130b15b2d3",
        "approved_action_digest": "sha256:f68efe345d97675f0c885ce5421488f7b591114201576f4fbedd1c051d280e48",
        "owner_id": "owner-b",
        "owner_key_id": "owner-b-key-2"
      },
      "store_metadata_tuple": "store_tuple_011"
    },
    "vote-proof:subject:owner-c": {
      "fact": {
        "approval_proof_digest": "sha256:d9b2439b64c749d7f70f9b099d9ce95391690a351b02f725f278165bdd57531a",
        "approved_action_digest": "sha256:f68efe345d97675f0c885ce5421488f7b591114201576f4fbedd1c051d280e48",
        "owner_id": "owner-c",
        "owner_key_id": "owner-c-key-1"
      },
      "store_metadata_tuple": "store_tuple_038"
    }
  },
  "vote_source_017": {
    "vote-proof:approval:owner-a": {
      "fact": {
        "approval_proof_digest": "sha256:6a238db3e74732c43071fca9ce7cd67a0d9b1388b6869b83bc2082352eddb71b",
        "approved_action_digest": "sha256:4280b870a67396067c998db81e2ddfb27a5609adb2e9a277a5a7d7da94cf62f7",
        "owner_id": "owner-a",
        "owner_key_id": "owner-a-key-3"
      },
      "store_metadata_tuple": "store_tuple_010"
    },
    "vote-proof:approval:owner-b": {
      "fact": {
        "approval_proof_digest": "sha256:4443167dfc54b2f14461ef324622862f1cd92bd81ef25fa2197248b64cd0647d",
        "approved_action_digest": "sha256:4280b870a67396067c998db81e2ddfb27a5609adb2e9a277a5a7d7da94cf62f7",
        "owner_id": "owner-b",
        "owner_key_id": "owner-b-key-2"
      },
      "store_metadata_tuple": "store_tuple_011"
    }
  },
  "vote_source_018": {
    "vote-proof:approval:owner-a": {
      "fact": {
        "approval_proof_digest": "sha256:9ebb96454a6c5835fbdbf5197c5a461aac583a02ed7ec390907020c0e826a3a2",
        "approved_action_digest": "sha256:d3bbc397128bf538333deff66f092b9a801c5fab47291f0741737f84ed1267c0",
        "owner_id": "owner-a",
        "owner_key_id": "owner-a-key-3"
      },
      "store_metadata_tuple": "store_tuple_010"
    },
    "vote-proof:approval:owner-b": {
      "fact": {
        "approval_proof_digest": "sha256:e2c9d8c4e9ffd2dc2419a27d31ad5a8d9305b13d61b28fb27e8a3d8e46cf6040",
        "approved_action_digest": "sha256:d3bbc397128bf538333deff66f092b9a801c5fab47291f0741737f84ed1267c0",
        "owner_id": "owner-b",
        "owner_key_id": "owner-b-key-2"
      },
      "store_metadata_tuple": "store_tuple_011"
    }
  },
  "vote_source_019": {
    "vote-proof:approval:owner-a": {
      "fact": {
        "approval_proof_digest": "sha256:3366a8f872bda948d11683f17651a4a521bcd414f85fcc0b6ef50c04c377ba50",
        "approved_action_digest": "sha256:89ad7383476c82eea310bad103bf051f8614a59c0880656146d4c33e4d3a1de1",
        "owner_id": "owner-a",
        "owner_key_id": "owner-a-key-3"
      },
      "store_metadata_tuple": "store_tuple_010"
    },
    "vote-proof:approval:owner-b": {
      "fact": {
        "approval_proof_digest": "sha256:ce0e2f22e800c0ae6473f6920b16075cbf33a250310458fac6210eee1e661312",
        "approved_action_digest": "sha256:89ad7383476c82eea310bad103bf051f8614a59c0880656146d4c33e4d3a1de1",
        "owner_id": "owner-b",
        "owner_key_id": "owner-b-key-2"
      },
      "store_metadata_tuple": "store_tuple_011"
    }
  }
}
''')
EXPLICIT_CASE_SOURCE_SETS = json.loads(r'''
{
  "aborted_transaction_discards_staging": [
    "store_source_000",
    "vote_source_000"
  ],
  "acceptance_owner_scope_binding_exact": [
    "store_source_001",
    "vote_source_000"
  ],
  "acceptance_scope_drift_rejected": [
    "store_source_001",
    "vote_source_000"
  ],
  "activation_binds_concrete_rollback_availability": [
    "store_source_002",
    "vote_source_000"
  ],
  "activation_binds_consumer_owner_issuer_id": [
    "store_source_002",
    "vote_source_000"
  ],
  "activation_candidate_is_not_prior_canonical_head": [
    "store_source_003",
    "vote_source_000"
  ],
  "activation_candidate_must_be_unrevoked": [
    "store_source_002",
    "vote_source_000"
  ],
  "activation_candidate_must_be_unsuperseded": [
    "store_source_002",
    "vote_source_000"
  ],
  "activation_context_issuer_checked_before_relation": [
    "store_source_002",
    "vote_source_000"
  ],
  "activation_current_head_equals_exact_prior": [
    "store_source_003",
    "vote_source_000"
  ],
  "activation_decision_bindings_exact": [
    "store_source_002",
    "vote_source_000"
  ],
  "activation_epoch_is_monotonic_from_acceptance": [
    "store_source_002",
    "vote_source_000"
  ],
  "activation_epoch_respects_acceptance_ceiling": [
    "store_source_002",
    "vote_source_000"
  ],
  "activation_genesis_explicit_null_previous_agrees": [
    "store_source_002",
    "vote_source_000"
  ],
  "activation_materialization_coordinate_runtime_chain_exact": [
    "store_source_002",
    "vote_source_000"
  ],
  "activation_null_pointer_revision_pair_is_atomic": [
    "store_source_004",
    "vote_source_000"
  ],
  "activation_prior_plus_one_transition_accepts": [
    "store_source_003",
    "vote_source_000"
  ],
  "activation_requires_current_decision_record": [
    "store_source_002",
    "vote_source_000"
  ],
  "activation_requires_valid_intent_revision": [
    "store_source_002",
    "vote_source_000"
  ],
  "activation_resolves_acceptance_self_digest": [
    "store_source_002",
    "vote_source_000"
  ],
  "activation_revision_requires_genesis_or_prior_plus_one": [
    "store_source_002",
    "vote_source_000"
  ],
  "activation_canary_scope_matches_intent_and_acceptance": [
    "store_source_002",
    "vote_source_000"
  ],
  "activation_stop_binding_drift_rejected": [
    "store_source_002",
    "vote_source_000"
  ],
  "ak_coordination_contract_cannot_authorize_execution": [
    "store_source_005",
    "vote_source_000"
  ],
  "ak_delivered_linkage_requires_pi_digest": [
    "store_source_006",
    "vote_source_000"
  ],
  "ak_generation_only_linkage_accepts_without_pi": [
    "store_source_006",
    "vote_source_000"
  ],
  "ak_revocation_locator_stale_rejected": [
    "store_source_007",
    "vote_source_000"
  ],
  "ak_stop_fact_has_ak_owner": [
    "store_source_005",
    "vote_source_000"
  ],
  "ak_store_head_stale_rejected": [
    "store_source_007",
    "vote_source_000"
  ],
  "approval_map_key_equals_value_digest": [
    "store_source_007",
    "vote_source_001"
  ],
  "approval_namespace_drift_rejected": [
    "store_source_006",
    "vote_source_002"
  ],
  "approval_owner_policy_digest_drift_rejected": [
    "store_source_006",
    "vote_source_002"
  ],
  "approval_owner_set_digest_drift_rejected": [
    "store_source_006",
    "vote_source_002"
  ],
  "approval_predicate_digest_drift_rejected": [
    "store_source_006",
    "vote_source_002"
  ],
  "approval_vote_order_rejected_independently": [
    "store_source_006",
    "vote_source_002"
  ],
  "arbitrary_length_semver_compares_without_number_precision_loss": [
    "store_source_007",
    "vote_source_000"
  ],
  "archive_payload_root_must_be_exact_directory_entry": [
    "store_source_008",
    "vote_source_000"
  ],
  "authority_acquisition_distribution_digest_is_exact": [
    "store_source_009",
    "vote_source_003"
  ],
  "authority_bundle_key_equals_artifact_digest": [
    "store_source_009",
    "vote_source_003"
  ],
  "authority_bundle_missing_node_fails_closed": [
    "store_source_009",
    "vote_source_003"
  ],
  "authority_bundle_surplus_node_fails_closed": [
    "store_source_009",
    "vote_source_003"
  ],
  "authority_coherent_acquisition_rewrite_rejected": [
    "store_source_009",
    "vote_source_003"
  ],
  "authority_coherent_owner_repository_rewrite_rejected": [
    "store_source_009",
    "vote_source_003"
  ],
  "authority_collator_cannot_issue_receipts": [
    "store_source_009",
    "vote_source_003"
  ],
  "authority_node_expected_schema_is_exact": [
    "store_source_009",
    "vote_source_003"
  ],
  "authority_node_issuer_scope_is_exact": [
    "store_source_009",
    "vote_source_003"
  ],
  "authority_preflight_order_is_normative": [
    "store_source_009",
    "vote_source_003"
  ],
  "authority_receipt_category_substitution_rejected": [
    "store_source_009",
    "vote_source_003"
  ],
  "authority_receipt_freshness_cas_floor_is_enforced": [
    "store_source_009",
    "vote_source_003"
  ],
  "authority_receipt_head_revision_fact_binding_is_exact": [
    "store_source_009",
    "vote_source_003"
  ],
  "authority_receipt_owner_specific_pin_is_exact": [
    "store_source_009",
    "vote_source_003"
  ],
  "authority_receipt_repository_identity_is_exact": [
    "store_source_009",
    "vote_source_003"
  ],
  "authority_required_anchor_is_mandatory": [
    "store_source_010",
    "vote_source_003"
  ],
  "authority_snapshot_duplicate_conflicting_receipt_rejected": [
    "store_source_009",
    "vote_source_003"
  ],
  "authority_snapshot_self_digest_is_universal": [
    "store_source_009",
    "vote_source_003"
  ],
  "authority_snapshot_surplus_receipt_rejected": [
    "store_source_009",
    "vote_source_003"
  ],
  "authority_verifier_surplus_role_rejected": [
    "store_source_009",
    "vote_source_003"
  ],
  "calendar_invalid_utc_rejected": [
    "store_source_006",
    "vote_source_000"
  ],
  "calendar_valid_utc_accepts": [
    "store_source_006",
    "vote_source_000"
  ],
  "calendar_year_9999_accepts": [
    "store_source_006",
    "vote_source_000"
  ],
  "calendar_year_zero_rejected": [
    "store_source_006",
    "vote_source_000"
  ],
  "canonical_accepted_ak_decision_accepts": [
    "store_source_007",
    "vote_source_000"
  ],
  "canonical_ak_authority_requires_independent_current_record_fact": [
    "store_source_011",
    "vote_source_003"
  ],
  "canonical_ak_authority_requires_independent_store_head_fact": [
    "store_source_010",
    "vote_source_003"
  ],
  "capsule_archive_extra_entry_rejected": [
    "store_source_008",
    "vote_source_000"
  ],
  "capsule_archive_identity_cycle_rejected": [
    "store_source_008",
    "vote_source_000"
  ],
  "capsule_archive_link_drift_rejected": [
    "store_source_008",
    "vote_source_000"
  ],
  "combined_full_success_records_order_and_revalidation": [
    "store_source_012",
    "vote_source_000"
  ],
  "combined_partial_failure_records_stages": [
    "store_source_012",
    "vote_source_000"
  ],
  "combined_stage_order_drift_rejected": [
    "store_source_012",
    "vote_source_000"
  ],
  "committed_without_linearization_rejected": [
    "store_source_006",
    "vote_source_000"
  ],
  "compatibility_policy_duplicate_missing_category": [
    "store_source_006",
    "vote_source_000"
  ],
  "compatibility_policy_exact_categories": [
    "store_source_006",
    "vote_source_000"
  ],
  "completed_stage_error_rejected": [
    "store_source_013",
    "vote_source_000"
  ],
  "condition_reference_must_be_bijective": [
    "store_source_007",
    "vote_source_000"
  ],
  "conditional_evidence_executes_true": [
    "store_source_007",
    "vote_source_000"
  ],
  "conditional_evidence_false": [
    "store_source_007",
    "vote_source_000"
  ],
  "conditional_evidence_missing": [
    "store_source_007",
    "vote_source_000"
  ],
  "consumer_acceptance_must_equal_current_owner_head": [
    "store_source_014",
    "vote_source_000"
  ],
  "consumer_protocol_floor_executes_true": [
    "store_source_007",
    "vote_source_000"
  ],
  "consumer_stop_fact_has_consumer_owner": [
    "store_source_005",
    "vote_source_000"
  ],
  "consumer_tree_outside_projection_rejected": [
    "store_source_008",
    "vote_source_000"
  ],
  "coordination_and_consumer_tasks_cannot_be_conflated": [
    "store_source_005",
    "vote_source_000"
  ],
  "delivered_without_prompt_run_rejected": [
    "store_source_006",
    "vote_source_000"
  ],
  "deprecation_interval_condition_executes_true": [
    "store_source_007",
    "vote_source_000"
  ],
  "deprecation_interval_satisfied": [
    "store_source_015",
    "vote_source_004"
  ],
  "disable_must_retain_runtime": [
    "store_source_016",
    "vote_source_000"
  ],
  "disable_that_leaves_semantic_active_rejected": [
    "store_source_016",
    "vote_source_000"
  ],
  "duplicate_compatibility_condition_rejected": [
    "store_source_007",
    "vote_source_000"
  ],
  "duplicate_projection_destination_rejected": [
    "store_source_008",
    "vote_source_000"
  ],
  "duplicate_projection_source_rejected": [
    "store_source_008",
    "vote_source_000"
  ],
  "embedded_digest_mismatch_is_deterministic": [
    "store_source_006",
    "vote_source_000"
  ],
  "exact_payload_projection_accepts": [
    "store_source_008",
    "vote_source_000"
  ],
  "executable_owner_override_accepts": [
    "store_source_007",
    "vote_source_005"
  ],
  "failed_rollback_changed_history_rejected": [
    "store_source_013",
    "vote_source_000"
  ],
  "failed_rollback_changed_state_rejected": [
    "store_source_013",
    "vote_source_000"
  ],
  "failed_rollback_preserves_state_and_typed_head": [
    "store_source_013",
    "vote_source_000"
  ],
  "failed_rollback_requires_failed_stage": [
    "store_source_013",
    "vote_source_000"
  ],
  "failed_without_error_rejected": [
    "store_source_006",
    "vote_source_000"
  ],
  "single_canary_consumer_allowed_paths_are_exact": [
    "store_source_005",
    "vote_source_000"
  ],
  "generation_coordinate_must_equal_activation": [
    "store_source_003",
    "vote_source_000"
  ],
  "generation_from_current_activation_accepts": [
    "store_source_003",
    "vote_source_000"
  ],
  "generation_from_nonhead_activation_rejected": [
    "store_source_017",
    "vote_source_000"
  ],
  "generation_from_revoked_activation_rejected": [
    "store_source_003",
    "vote_source_000"
  ],
  "generation_from_superseded_activation_rejected": [
    "store_source_018",
    "vote_source_000"
  ],
  "generation_runtime_must_equal_activation": [
    "store_source_003",
    "vote_source_000"
  ],
  "generation_supplied_activation_must_equal_current_pointer": [
    "store_source_003",
    "vote_source_000"
  ],
  "governance_evidence_reference_uses_fact_owner": [
    "store_source_005",
    "vote_source_000"
  ],
  "illegal_status_self_transition": [
    "store_source_019",
    "vote_source_006"
  ],
  "issuer_scope_checked_before_subject_rule": [
    "store_source_013",
    "vote_source_000"
  ],
  "lifecycle_current_prior_head_is_external": [
    "store_source_015",
    "vote_source_004"
  ],
  "lifecycle_endpoint_cannot_self_certify_publication": [
    "store_source_020",
    "vote_source_004"
  ],
  "lifecycle_namespace_drift_rejected": [
    "store_source_015",
    "vote_source_004"
  ],
  "lifecycle_prior_head_drift_rejected": [
    "store_source_015",
    "vote_source_004"
  ],
  "lifecycle_referenced_ledger_self_digest_checked": [
    "store_source_015",
    "vote_source_004"
  ],
  "lifecycle_requires_accepted_current_ledger_heads": [
    "store_source_021",
    "vote_source_004"
  ],
  "lifecycle_transaction_coordinate_is_exact": [
    "store_source_015",
    "vote_source_004"
  ],
  "lifecycle_transaction_namespace_is_exact": [
    "store_source_015",
    "vote_source_004"
  ],
  "major_bump_satisfies_breaking": [
    "store_source_007",
    "vote_source_000"
  ],
  "manifest_order_is_utf8_not_utf16": [
    "store_source_006",
    "vote_source_000"
  ],
  "minor_bump_rejects_major_effect": [
    "store_source_007",
    "vote_source_000"
  ],
  "minor_bump_satisfies_addition": [
    "store_source_007",
    "vote_source_000"
  ],
  "namespace_version_digest_reuse_conflicts": [
    "store_source_022",
    "vote_source_000"
  ],
  "no_prior_disable_clears_semantic": [
    "store_source_016",
    "vote_source_000"
  ],
  "non_authorizing_separate_coordination_and_consumer_contracts": [
    "store_source_005",
    "vote_source_000"
  ],
  "non_tombstoned_identifier_accepts": [
    "store_source_008",
    "vote_source_000"
  ],
  "override_approval_namespace_chain_must_match": [
    "store_source_007",
    "vote_source_007"
  ],
  "override_approval_requires_complete_override": [
    "store_source_006",
    "vote_source_000"
  ],
  "override_cannot_legalize_identifier_reuse": [
    "store_source_008",
    "vote_source_000"
  ],
  "override_cannot_lower_unknown_semver_floor": [
    "store_source_007",
    "vote_source_008"
  ],
  "override_digest_omission_rejected": [
    "store_source_007",
    "vote_source_005"
  ],
  "override_requires_independent_ak_current_record": [
    "store_source_007",
    "vote_source_005"
  ],
  "override_requires_independent_ak_store_observation": [
    "store_source_007",
    "vote_source_005"
  ],
  "owner_vote_proof_requires_pinned_owner_capability": [
    "store_source_006",
    "vote_source_002"
  ],
  "partial_failure_must_not_supersede_activation": [
    "store_source_012",
    "vote_source_000"
  ],
  "partial_failure_without_failed_stage_rejected": [
    "store_source_012",
    "vote_source_000"
  ],
  "patch_bump_rejects_minor_effect": [
    "store_source_007",
    "vote_source_000"
  ],
  "patch_semver_rejects_prerelease_only_movement": [
    "store_source_007",
    "vote_source_000"
  ],
  "pi_delivered_variant_accepts": [
    "store_source_006",
    "vote_source_000"
  ],
  "pi_failed_variant_accepts": [
    "store_source_006",
    "vote_source_000"
  ],
  "pi_suppressed_variant_accepts": [
    "store_source_006",
    "vote_source_000"
  ],
  "primitive_context_integer_rejects_boolean": [
    "store_source_023",
    "vote_source_000"
  ],
  "prior_journal_transaction_equals_prior_status_transaction": [
    "store_source_009",
    "vote_source_003"
  ],
  "projection_capsule_semantic_owner_substitution_rejected": [
    "store_source_008",
    "vote_source_000"
  ],
  "projection_capsule_tombstone_revision_is_exact": [
    "store_source_008",
    "vote_source_000"
  ],
  "projection_lifecycle_head_currentness_rejected": [
    "store_source_008",
    "vote_source_000"
  ],
  "projection_materialization_coordinate_equals_capsule_coordinate": [
    "store_source_008",
    "vote_source_000"
  ],
  "projection_namespace_currentness_rejected": [
    "store_source_008",
    "vote_source_000"
  ],
  "projection_complete_tombstone_history_required": [
    "store_source_008",
    "vote_source_000"
  ],
  "projection_registry_revision_currentness_rejected": [
    "store_source_008",
    "vote_source_000"
  ],
  "projection_rocs_proof_owner_substitution_rejected": [
    "store_source_008",
    "vote_source_000"
  ],
  "projection_stale_tombstone_registry_rejected": [
    "store_source_008",
    "vote_source_000"
  ],
  "publication_commit_requires_canonical_publication_head": [
    "store_source_024",
    "vote_source_003"
  ],
  "publication_fork_rejected": [
    "store_source_025",
    "vote_source_000"
  ],
  "publication_fresh_cas_accepts": [
    "store_source_025",
    "vote_source_000"
  ],
  "publication_idempotent_replay_returns_existing": [
    "store_source_026",
    "vote_source_000"
  ],
  "publication_journal_resulting_head_drift_rejected": [
    "store_source_009",
    "vote_source_003"
  ],
  "publication_journal_shape_valid_tuple_non_authorizing": [
    "store_source_006",
    "vote_source_000"
  ],
  "publication_prior_journal_result_revision_head_bind_prior_status": [
    "store_source_009",
    "vote_source_003"
  ],
  "publication_prior_status_context_self_digest_checked": [
    "store_source_019",
    "vote_source_006"
  ],
  "publication_recovery_before_status_is_canonical": [
    "store_source_000",
    "vote_source_000"
  ],
  "publication_recovery_controller_is_exact": [
    "store_source_000",
    "vote_source_000"
  ],
  "publication_recovery_current_journal_receipt_is_exact": [
    "store_source_000",
    "vote_source_000"
  ],
  "publication_recovery_epoch_is_exact": [
    "store_source_000",
    "vote_source_000"
  ],
  "publication_recovery_null_after_rejected": [
    "store_source_000",
    "vote_source_000"
  ],
  "publication_recovery_null_before_rejected": [
    "store_source_000",
    "vote_source_000"
  ],
  "publication_recovery_null_marker_rejected": [
    "store_source_000",
    "vote_source_000"
  ],
  "publication_recovery_null_result_rejected": [
    "store_source_000",
    "vote_source_000"
  ],
  "publication_recovery_null_transaction_rejected": [
    "store_source_000",
    "vote_source_000"
  ],
  "publication_recovery_prior_journal_full_join_is_exact": [
    "store_source_000",
    "vote_source_000"
  ],
  "publication_recovery_requires_canonical_ledger_head": [
    "store_source_000",
    "vote_source_000"
  ],
  "publication_recovery_result_coordinate_join_is_exact": [
    "store_source_000",
    "vote_source_000"
  ],
  "publication_recovery_runtime_is_exact": [
    "store_source_000",
    "vote_source_000"
  ],
  "publication_recovery_store_snapshot_action_epoch_drift_rejected": [
    "store_source_000",
    "vote_source_000"
  ],
  "publication_recovery_store_snapshot_head_drift_rejected": [
    "store_source_000",
    "vote_source_000"
  ],
  "publication_recovery_store_snapshot_repository_drift_rejected": [
    "store_source_000",
    "vote_source_000"
  ],
  "publication_recovery_store_snapshot_revision_drift_rejected": [
    "store_source_000",
    "vote_source_000"
  ],
  "publication_recovery_transition_expectation_is_exact": [
    "store_source_000",
    "vote_source_000"
  ],
  "publication_rejects_externally_revoked_trust_root": [
    "store_source_009",
    "vote_source_003"
  ],
  "publication_result_journal_marker_bind_exactly": [
    "store_source_009",
    "vote_source_003"
  ],
  "publication_result_transaction_drift_rejected": [
    "store_source_009",
    "vote_source_003"
  ],
  "publication_stale_cas_rejected": [
    "store_source_025",
    "vote_source_000"
  ],
  "publication_transition_requires_canonical_publication_head": [
    "store_source_027",
    "vote_source_006"
  ],
  "publication_trust_root_namespace_binds_authority": [
    "store_source_009",
    "vote_source_003"
  ],
  "publication_trust_root_policy_binds_authority": [
    "store_source_009",
    "vote_source_003"
  ],
  "publication_trust_root_requires_external_canonical_pin": [
    "store_source_009",
    "vote_source_003"
  ],
  "publication_trust_root_set_binds_authority": [
    "store_source_009",
    "vote_source_003"
  ],
  "publish_approval_resolves_canonical_ak_decision": [
    "store_source_009",
    "vote_source_003"
  ],
  "publish_operation_rejects_status_reason": [
    "store_source_025",
    "vote_source_000"
  ],
  "publish_requires_exact_release_action": [
    "store_source_009",
    "vote_source_009"
  ],
  "publish_requires_threshold_evaluation": [
    "store_source_009",
    "vote_source_010"
  ],
  "published_to_revoked_transition_committed": [
    "store_source_019",
    "vote_source_011"
  ],
  "python_boolean_cannot_satisfy_integer_type": [
    "store_source_006",
    "vote_source_000"
  ],
  "python_integer_cannot_satisfy_boolean_const": [
    "store_source_006",
    "vote_source_000"
  ],
  "recovery_after_linearization_completes": [
    "store_source_000",
    "vote_source_000"
  ],
  "recovery_after_linearization_requires_marker": [
    "store_source_000",
    "vote_source_000"
  ],
  "recovery_after_state_is_controller_issued": [
    "store_source_000",
    "vote_source_000"
  ],
  "recovery_before_linearization_discards": [
    "store_source_000",
    "vote_source_000"
  ],
  "recovery_before_linearization_must_not_move_head": [
    "store_source_000",
    "vote_source_000"
  ],
  "recovery_before_state_is_semantic_owner_issued": [
    "store_source_000",
    "vote_source_000"
  ],
  "recovery_intent_descriptor_cannot_claim_fsync": [
    "store_source_000",
    "vote_source_000"
  ],
  "recovery_intent_descriptor_owner_is_exact": [
    "store_source_000",
    "vote_source_000"
  ],
  "recovery_marker_must_match_exact_journal_and_result": [
    "store_source_000",
    "vote_source_000"
  ],
  "recovery_prelinearization_rejects_durable_marker": [
    "store_source_000",
    "vote_source_000"
  ],
  "recovery_prelinearization_requires_intent_descriptor": [
    "store_source_000",
    "vote_source_000"
  ],
  "recovery_resolves_complete_resulting_status_object": [
    "store_source_000",
    "vote_source_000"
  ],
  "recovery_result_context_self_digest_checked": [
    "store_source_000",
    "vote_source_000"
  ],
  "recovery_result_transaction_binds_transaction": [
    "store_source_000",
    "vote_source_000"
  ],
  "recovery_state_receipt_namespace_is_exact": [
    "store_source_000",
    "vote_source_000"
  ],
  "recovery_status_record_must_match_result": [
    "store_source_000",
    "vote_source_000"
  ],
  "referenced_context_order_validated_before_relation": [
    "store_source_006",
    "vote_source_002"
  ],
  "referenced_owner_set_stale_self_digest_rejected": [
    "store_source_006",
    "vote_source_002"
  ],
  "referenced_policy_expected_type_rejected": [
    "store_source_006",
    "vote_source_002"
  ],
  "rejected_ak_decision_fails_closed": [
    "store_source_007",
    "vote_source_000"
  ],
  "removal_before_interval_rejected": [
    "store_source_015",
    "vote_source_004"
  ],
  "resolved_governance_reference_compares_independent_snapshot": [
    "store_source_005",
    "vote_source_000"
  ],
  "resolved_governance_reference_observation_accepts": [
    "store_source_005",
    "vote_source_000"
  ],
  "resolved_governance_reference_observed_head_is_exact": [
    "store_source_005",
    "vote_source_000"
  ],
  "resolved_governance_reference_observed_state_is_exact": [
    "store_source_005",
    "vote_source_000"
  ],
  "resolved_governance_reference_observed_task_digest_is_exact": [
    "store_source_005",
    "vote_source_000"
  ],
  "revocation_approval_action_drift_rejected": [
    "store_source_028",
    "vote_source_012"
  ],
  "revocation_prior_head_drift_rejected": [
    "store_source_028",
    "vote_source_012"
  ],
  "revocation_recovery_before_linearization_discards": [
    "store_source_000",
    "vote_source_000"
  ],
  "revocation_requires_independent_ak_current_record": [
    "store_source_028",
    "vote_source_012"
  ],
  "revocation_requires_independent_ak_store_observation": [
    "store_source_028",
    "vote_source_012"
  ],
  "revocation_revision_not_increasing_rejected": [
    "store_source_028",
    "vote_source_012"
  ],
  "revoke_cannot_reuse_release_approval": [
    "store_source_029",
    "vote_source_003"
  ],
  "revoked_ak_decision_fails_closed": [
    "store_source_007",
    "vote_source_000"
  ],
  "revoked_owner_vote_rejected": [
    "store_source_006",
    "vote_source_002"
  ],
  "revoked_rotation_root_rejected": [
    "store_source_030",
    "vote_source_013"
  ],
  "rocs_cannot_self_certify_acceptance": [
    "store_source_001",
    "vote_source_000"
  ],
  "rollback_availability_proof_has_rocs_owner": [
    "store_source_013",
    "vote_source_000"
  ],
  "rollback_availability_receipt_requires_issuer": [
    "store_source_013",
    "vote_source_000"
  ],
  "rollback_before_head_must_equal_canonical_head": [
    "store_source_013",
    "vote_source_000"
  ],
  "rollback_binds_technical_receipt_issuer_id": [
    "store_source_013",
    "vote_source_000"
  ],
  "rollback_cannot_complete_stage_after_failure": [
    "store_source_012",
    "vote_source_000"
  ],
  "rollback_controller_equals_external_recovery_observation": [
    "store_source_013",
    "vote_source_000"
  ],
  "rollback_epoch_equals_external_recovery_observation": [
    "store_source_013",
    "vote_source_000"
  ],
  "rollback_error_must_equal_failed_stage_cause": [
    "store_source_012",
    "vote_source_000"
  ],
  "rollback_from_state_drift_rejected": [
    "store_source_013",
    "vote_source_000"
  ],
  "rollback_history_head_must_bind_typed_transition": [
    "store_source_013",
    "vote_source_000"
  ],
  "rollback_history_transition_has_consumer_owner": [
    "store_source_013",
    "vote_source_000"
  ],
  "rollback_optional_ak_pi_crosslinks_exact": [
    "store_source_013",
    "vote_source_000"
  ],
  "rollback_recovery_artifact_resolved_exactly": [
    "store_source_013",
    "vote_source_000"
  ],
  "rollback_request_digest_drift_rejected": [
    "store_source_013",
    "vote_source_000"
  ],
  "rollback_request_from_activation_drift_rejected": [
    "store_source_013",
    "vote_source_000"
  ],
  "rollback_request_target_equals_activated_intent_and_materialization": [
    "store_source_013",
    "vote_source_000"
  ],
  "rollback_requester_id_equals_consumer_owner": [
    "store_source_013",
    "vote_source_000"
  ],
  "rollback_requires_canonical_current_activation_object": [
    "store_source_013",
    "vote_source_000"
  ],
  "rollback_requires_concrete_target_and_recovery_availability": [
    "store_source_013",
    "vote_source_000"
  ],
  "rollback_resolves_typed_materialization_receipt_issuer": [
    "store_source_013",
    "vote_source_000"
  ],
  "rollback_result_target_mismatch_rejected": [
    "store_source_016",
    "vote_source_000"
  ],
  "rollback_target_artifact_self_digest_checked": [
    "store_source_013",
    "vote_source_000"
  ],
  "rollback_technical_receipt_binds_exact_coordinate": [
    "store_source_013",
    "vote_source_000"
  ],
  "rollback_technical_receipt_binds_exact_subject_digest": [
    "store_source_013",
    "vote_source_000"
  ],
  "rotation_approval_action_drift_rejected": [
    "store_source_030",
    "vote_source_013"
  ],
  "rotation_namespace_binding_drift_rejected": [
    "store_source_030",
    "vote_source_013"
  ],
  "rotation_not_bound_to_current_root": [
    "store_source_030",
    "vote_source_013"
  ],
  "rotation_owner_set_binding_drift_rejected": [
    "store_source_030",
    "vote_source_013"
  ],
  "rotation_predicate_binding_drift_rejected": [
    "store_source_030",
    "vote_source_013"
  ],
  "rotation_requires_independent_ak_current_record": [
    "store_source_030",
    "vote_source_013"
  ],
  "rotation_requires_independent_ak_store_observation": [
    "store_source_030",
    "vote_source_013"
  ],
  "rotation_revision_not_increasing_rejected": [
    "store_source_030",
    "vote_source_013"
  ],
  "runtime_revalidation_binding_drift_rejected": [
    "store_source_031",
    "vote_source_000"
  ],
  "runtime_rollback_retains_semantic_and_revalidates": [
    "store_source_031",
    "vote_source_000"
  ],
  "runtime_rollback_without_revalidation_rejected": [
    "store_source_013",
    "vote_source_000"
  ],
  "semantic_rollback_retains_runtime": [
    "store_source_013",
    "vote_source_000"
  ],
  "semantic_rollback_target_requires_runtime_compatibility": [
    "store_source_013",
    "vote_source_000"
  ],
  "semantic_stop_fact_has_semantic_owner": [
    "store_source_005",
    "vote_source_000"
  ],
  "semver_context_requires_exact_full_grammar": [
    "store_source_007",
    "vote_source_000"
  ],
  "semver_subject_requires_exact_full_grammar": [
    "store_source_006",
    "vote_source_000"
  ],
  "status_transition_fabricated_prior_object_rejected": [
    "store_source_019",
    "vote_source_006"
  ],
  "status_transition_link_drift_rejected": [
    "store_source_019",
    "vote_source_006"
  ],
  "status_transition_prior_journal_drift_rejected": [
    "store_source_019",
    "vote_source_006"
  ],
  "stop_condition_fact_id_pairs_exactly": [
    "store_source_005",
    "vote_source_000"
  ],
  "stop_condition_id_pairs_exactly": [
    "store_source_005",
    "vote_source_000"
  ],
  "stop_condition_repository_pairs_exactly": [
    "store_source_005",
    "vote_source_000"
  ],
  "superseded_ak_decision_fails_closed": [
    "store_source_007",
    "vote_source_000"
  ],
  "suppressed_cannot_claim_prompt_delivery": [
    "store_source_006",
    "vote_source_000"
  ],
  "surplus_unreferenced_condition_rejected": [
    "store_source_007",
    "vote_source_000"
  ],
  "task_contract_binds_exact_dependency_ids": [
    "store_source_005",
    "vote_source_000"
  ],
  "task_contract_binds_exact_evidence_list": [
    "store_source_005",
    "vote_source_000"
  ],
  "task_contract_binds_exact_owner_id": [
    "store_source_005",
    "vote_source_000"
  ],
  "task_contract_binds_exact_prerequisite_ids": [
    "store_source_005",
    "vote_source_000"
  ],
  "task_contract_binds_exact_rollback_owner_id": [
    "store_source_005",
    "vote_source_000"
  ],
  "task_contract_binds_exact_rollback_owner_kind": [
    "store_source_005",
    "vote_source_000"
  ],
  "task_contract_binds_exact_stop_conditions": [
    "store_source_005",
    "vote_source_000"
  ],
  "task_contract_binds_exact_task_id": [
    "store_source_005",
    "vote_source_000"
  ],
  "task_contract_binds_required_reference_state": [
    "store_source_005",
    "vote_source_000"
  ],
  "task_contract_machine_binds_stop_semantics": [
    "store_source_005",
    "vote_source_000"
  ],
  "task_contract_rejects_synthetic_future_artifact_digest": [
    "store_source_005",
    "vote_source_000"
  ],
  "threshold_insufficient_rejected": [
    "store_source_006",
    "vote_source_014"
  ],
  "threshold_two_of_three_accepts": [
    "store_source_006",
    "vote_source_002"
  ],
  "tombstone_origin_reason_exact_binding": [
    "store_source_015",
    "vote_source_004"
  ],
  "tombstone_registry_extra_entry_rejected": [
    "store_source_015",
    "vote_source_004"
  ],
  "tombstone_history_cumulative_entries_are_permanent": [
    "store_source_015",
    "vote_source_004"
  ],
  "tombstone_registry_semantic_owner_substitution_rejected": [
    "store_source_008",
    "vote_source_000"
  ],
  "tombstone_history_dropped_cumulative_entry_rejected": [
    "store_source_008",
    "vote_source_000"
  ],
  "tombstone_reuse_lifecycle_head_currentness_rejected": [
    "store_source_008",
    "vote_source_000"
  ],
  "tombstone_reuse_namespace_currentness_rejected": [
    "store_source_008",
    "vote_source_000"
  ],
  "tombstone_history_truncation_rejected": [
    "store_source_008",
    "vote_source_000"
  ],
  "tombstone_reuse_registry_revision_currentness_rejected": [
    "store_source_008",
    "vote_source_000"
  ],
  "tombstone_reuse_stale_registry_rejected": [
    "store_source_008",
    "vote_source_000"
  ],
  "tombstoned_identifier_cannot_return_as_addition": [
    "store_source_008",
    "vote_source_000"
  ],
  "tombstoned_identifier_reuse_rejected": [
    "store_source_008",
    "vote_source_000"
  ],
  "trust_revocation_action_requires_full_authority_chain": [
    "store_source_028",
    "vote_source_015"
  ],
  "trust_root_keys_require_uniqueness": [
    "store_source_006",
    "vote_source_000"
  ],
  "trust_root_keys_require_utf8_order": [
    "store_source_006",
    "vote_source_000"
  ],
  "unanimous_threshold_equals_active_owner_count": [
    "store_source_006",
    "vote_source_016"
  ],
  "unanimous_threshold_mismatch_rejected": [
    "store_source_006",
    "vote_source_016"
  ],
  "unresolved_candidate_cannot_claim_synthetic_task_artifacts": [
    "store_source_005",
    "vote_source_000"
  ],
  "unresolved_dependency_binds_correct_owner_repository": [
    "store_source_005",
    "vote_source_000"
  ],
  "valid_old_to_new_root_rotation": [
    "store_source_030",
    "vote_source_013"
  ],
  "valid_trust_revocation_transition": [
    "store_source_028",
    "vote_source_012"
  ],
  "valid_trust_root_revocation_transition": [
    "store_source_028",
    "vote_source_017"
  ],
  "version_binding_existing_coordinate_is_stable": [
    "store_source_022",
    "vote_source_000"
  ],
  "withdraw_approval_binds_exact_operation_reason_and_cas": [
    "store_source_019",
    "vote_source_018"
  ],
  "withdraw_approval_resolves_canonical_ak_decision": [
    "store_source_019",
    "vote_source_006"
  ],
  "withdraw_cannot_reuse_release_approval": [
    "store_source_019",
    "vote_source_003"
  ],
  "withdrawal_recovery_after_linearization_completes": [
    "store_source_000",
    "vote_source_000"
  ],
  "withdrawal_transition_committed": [
    "store_source_019",
    "vote_source_006"
  ],
  "withdrawn_to_revoked_transition_committed": [
    "store_source_029",
    "vote_source_019"
  ]
}
''')


EXPLICIT_CASE_SOURCE_SETS["tombstone_origin_exact_binding"] = ["store_source_015", "vote_source_004"]

# Revision-v12 source declarations extend the static v11 inventory; every case remains named explicitly.
EXPLICIT_STORE_METADATA_SETS["store_source_recovery_authority_v12"] = {
    "canonical_publication_head": "store_tuple_000", "canonical_publication_journal_head": "store_tuple_000",
    "canonical_publication_revision": "store_tuple_000", "canonical_publication_status_digest": "store_tuple_000",
    "canonical_recovery_controller_id": "store_tuple_001", "canonical_recovery_epoch": "store_tuple_001",
    "canonical_recovery_journal_head": "store_tuple_000", "canonical_recovery_resulting_head": "store_tuple_000",
    "canonical_recovery_resulting_revision": "store_tuple_000", "canonical_recovery_resulting_status_digest": "store_tuple_000",
    "canonical_recovery_runtime_identity": "store_tuple_001", "canonical_recovery_transaction_digest": "store_tuple_000",
    "canonical_store_head": "store_tuple_003", "canonical_trust_revocation_head": "store_tuple_004",
    "canonical_trust_revocation_revision": "store_tuple_004", "canonical_trust_root_digest": "store_tuple_005",
    "current_decision_record_digest": "store_tuple_003", "external_trust_root_pin": "store_tuple_005",
    "revoked_trust_digests": "store_tuple_004",
}
EXPLICIT_CASE_SOURCE_SETS["recovery_before_linearization_discards"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["recovery_after_linearization_completes"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["aborted_transaction_discards_staging"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["recovery_before_linearization_must_not_move_head"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["recovery_after_linearization_requires_marker"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["recovery_marker_must_match_exact_journal_and_result"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["recovery_status_record_must_match_result"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["recovery_resolves_complete_resulting_status_object"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["recovery_result_context_self_digest_checked"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["recovery_prelinearization_rejects_durable_marker"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["recovery_prelinearization_requires_intent_descriptor"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["recovery_intent_descriptor_cannot_claim_fsync"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["recovery_intent_descriptor_owner_is_exact"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["recovery_before_state_is_semantic_owner_issued"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["recovery_after_state_is_controller_issued"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["recovery_state_receipt_namespace_is_exact"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["publication_recovery_current_journal_receipt_is_exact"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["publication_recovery_transition_expectation_is_exact"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["publication_recovery_calls_trust_authority"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["publication_recovery_calls_canonical_decision_authority"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["publication_recovery_calls_exact_action_authority"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["publication_recovery_store_snapshot_head_drift_rejected"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["publication_recovery_store_snapshot_revision_drift_rejected"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["publication_recovery_store_snapshot_action_epoch_drift_rejected"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["publication_recovery_store_snapshot_repository_drift_rejected"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["recovery_result_transaction_binds_transaction"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["publication_recovery_result_coordinate_join_is_exact"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["publication_recovery_before_status_is_canonical"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["publication_recovery_prior_journal_full_join_is_exact"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["publication_recovery_null_transaction_rejected"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["publication_recovery_null_result_rejected"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["publication_recovery_null_marker_rejected"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["publication_recovery_null_before_rejected"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["publication_recovery_null_after_rejected"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["publication_recovery_controller_is_exact"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["publication_recovery_runtime_is_exact"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["publication_recovery_epoch_is_exact"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["publication_recovery_requires_canonical_ledger_head"] = ["store_source_recovery_authority_v12", "vote_source_003"]
EXPLICIT_CASE_SOURCE_SETS["publication_recovery_calls_threshold_authority"] = ["store_source_recovery_authority_v12", "vote_source_010"]
EXPLICIT_CASE_SOURCE_SETS["withdrawal_recovery_after_linearization_completes"] = ["store_source_recovery_authority_v12", "vote_source_006"]
EXPLICIT_CASE_SOURCE_SETS["revocation_recovery_before_linearization_discards"] = ["store_source_recovery_authority_v12", "vote_source_019"]
EXPLICIT_CASE_SOURCE_SETS["v0_consumer_repository_is_exact"] = ["store_source_001", "vote_source_000"]
EXPLICIT_CASE_SOURCE_SETS["v0_consumer_identity_revision_three_is_exact"] = ["store_source_001", "vote_source_000"]
EXPLICIT_CASE_SOURCE_SETS["v0_consumer_locator_is_exact"] = ["store_source_001", "vote_source_000"]
EXPLICIT_CASE_SOURCE_SETS["v0_canary_cardinality_is_exactly_one"] = ["store_source_001", "vote_source_000"]
EXPLICIT_CASE_SOURCE_SETS["v0_canary_name_requires_operator_authority"] = ["store_source_001", "vote_source_000"]
EXPLICIT_CASE_SOURCE_SETS["v0_scope_expansion_requires_new_protocol_and_decision"] = ["store_source_001", "vote_source_000"]
EXPLICIT_CASE_SOURCE_SETS["tombstone_history_restart_rejected"] = ["store_source_008", "vote_source_000"]
EXPLICIT_CASE_SOURCE_SETS["tombstone_history_dropped_revision_rejected"] = ["store_source_008", "vote_source_000"]
EXPLICIT_CASE_SOURCE_SETS["tombstone_history_exact_digest_links_required"] = ["store_source_008", "vote_source_000"]
EXPLICIT_CASE_SOURCE_SETS["tombstone_history_authorized_delta_required"] = ["store_source_008", "vote_source_000"]
EXPLICIT_CASE_SOURCE_SETS["tombstone_history_changed_cumulative_entry_rejected"] = ["store_source_008", "vote_source_000"]
EXPLICIT_CASE_SOURCE_SETS["disable_contract_subject_must_match_rollback_plan"] = ["store_source_016", "vote_source_000"]
EXPLICIT_CASE_SOURCE_SETS["disable_rehearsal_subject_must_match_contract"] = ["store_source_016", "vote_source_000"]
EXPLICIT_CASE_SOURCE_SETS["disable_contract_coordinate_must_be_null"] = ["store_source_016", "vote_source_000"]
EXPLICIT_CASE_SOURCE_SETS["disable_rehearsal_coordinate_must_be_null"] = ["store_source_016", "vote_source_000"]
EXPLICIT_CASE_SOURCE_SETS["disable_contract_runtime_must_match_active_runtime"] = ["store_source_016", "vote_source_000"]
EXPLICIT_CASE_SOURCE_SETS["disable_rehearsal_runtime_must_match_active_runtime"] = ["store_source_016", "vote_source_000"]


REGISTERED_SOURCE_RECEIPT_MUTATIONS = json.loads(r'''
{
  "authority_coherent_owner_repository_rewrite_rejected": {
    "descriptor_edge_ids": [
      "preflight.coherent-owner-repository-rewrite"
    ],
    "expected_final_receipt_tuples": [
      {
        "action_epoch": 100,
        "fact_digest": "sha256:bb53e9a7967b27d71cdc25180496f8b9d1dccae3ada1e64486f6b644e2395fce",
        "fact_schema": "semantic-authority-semantic-trust-fact.v0",
        "fact_value": {
          "kind": "digest",
          "value": "sha256:c941b19034374280208d093c576558cf16c5ebdbd2d615d8c68b8a92a507da44"
        },
        "observation_id": "receipt:publication_commit:canonical_trust_root_digest",
        "owner_repository": {
          "canonical_locator": "local://softwareco/pi-canary-consumer",
          "identity_revision": 3,
          "owner": "consumer-owner",
          "repository_id": "pi-canary-consumer"
        },
        "receipt_kind": "store",
        "role": "canonical_trust_root_digest",
        "store_head_digest": "sha256:b38b6d6cc96a19fc6ff6af60ed56828f3814d5b15e3a54da8e008bda7d89d832",
        "store_id": "semantic-trust-store",
        "store_revision": 5,
        "vote_tuple": null
      }
    ],
    "mode": "replace",
    "mutation_id": "source-receipt-mutation:authority_coherent_owner_repository_rewrite_rejected",
    "source_receipt_tuples": [
      {
        "action_epoch": 100,
        "fact_digest": "sha256:bb53e9a7967b27d71cdc25180496f8b9d1dccae3ada1e64486f6b644e2395fce",
        "fact_schema": "semantic-authority-semantic-trust-fact.v0",
        "fact_value": {
          "kind": "digest",
          "value": "sha256:c941b19034374280208d093c576558cf16c5ebdbd2d615d8c68b8a92a507da44"
        },
        "observation_id": "receipt:publication_commit:canonical_trust_root_digest",
        "owner_repository": {
          "canonical_locator": "local://core/ontology-kernel",
          "identity_revision": 1,
          "owner": "semantic-owner",
          "repository_id": "ontology-kernel"
        },
        "receipt_kind": "store",
        "role": "canonical_trust_root_digest",
        "store_head_digest": "sha256:b38b6d6cc96a19fc6ff6af60ed56828f3814d5b15e3a54da8e008bda7d89d832",
        "store_id": "semantic-trust-store",
        "store_revision": 5,
        "vote_tuple": null
      }
    ]
  },
  "authority_receipt_freshness_cas_floor_is_enforced": {
    "descriptor_edge_ids": [
      "preflight.receipt-freshness"
    ],
    "expected_final_receipt_tuples": [
      {
        "action_epoch": 89,
        "fact_digest": "sha256:bb53e9a7967b27d71cdc25180496f8b9d1dccae3ada1e64486f6b644e2395fce",
        "fact_schema": "semantic-authority-semantic-trust-fact.v0",
        "fact_value": {
          "kind": "digest",
          "value": "sha256:c941b19034374280208d093c576558cf16c5ebdbd2d615d8c68b8a92a507da44"
        },
        "observation_id": "receipt:publication_commit:canonical_trust_root_digest",
        "owner_repository": {
          "canonical_locator": "local://core/ontology-kernel",
          "identity_revision": 1,
          "owner": "semantic-owner",
          "repository_id": "ontology-kernel"
        },
        "receipt_kind": "store",
        "role": "canonical_trust_root_digest",
        "store_head_digest": "sha256:b38b6d6cc96a19fc6ff6af60ed56828f3814d5b15e3a54da8e008bda7d89d832",
        "store_id": "semantic-trust-store",
        "store_revision": 5,
        "vote_tuple": null
      }
    ],
    "mode": "replace",
    "mutation_id": "source-receipt-mutation:authority_receipt_freshness_cas_floor_is_enforced",
    "source_receipt_tuples": [
      {
        "action_epoch": 100,
        "fact_digest": "sha256:bb53e9a7967b27d71cdc25180496f8b9d1dccae3ada1e64486f6b644e2395fce",
        "fact_schema": "semantic-authority-semantic-trust-fact.v0",
        "fact_value": {
          "kind": "digest",
          "value": "sha256:c941b19034374280208d093c576558cf16c5ebdbd2d615d8c68b8a92a507da44"
        },
        "observation_id": "receipt:publication_commit:canonical_trust_root_digest",
        "owner_repository": {
          "canonical_locator": "local://core/ontology-kernel",
          "identity_revision": 1,
          "owner": "semantic-owner",
          "repository_id": "ontology-kernel"
        },
        "receipt_kind": "store",
        "role": "canonical_trust_root_digest",
        "store_head_digest": "sha256:b38b6d6cc96a19fc6ff6af60ed56828f3814d5b15e3a54da8e008bda7d89d832",
        "store_id": "semantic-trust-store",
        "store_revision": 5,
        "vote_tuple": null
      }
    ]
  },
  "authority_receipt_head_revision_fact_binding_is_exact": {
    "descriptor_edge_ids": [
      "preflight.receipt-store-fact"
    ],
    "expected_final_receipt_tuples": [
      {
        "action_epoch": 100,
        "fact_digest": "sha256:bb53e9a7967b27d71cdc25180496f8b9d1dccae3ada1e64486f6b644e2395fce",
        "fact_schema": "semantic-authority-semantic-trust-fact.v0",
        "fact_value": {
          "kind": "digest",
          "value": "sha256:c941b19034374280208d093c576558cf16c5ebdbd2d615d8c68b8a92a507da44"
        },
        "observation_id": "receipt:publication_commit:canonical_trust_root_digest",
        "owner_repository": {
          "canonical_locator": "local://core/ontology-kernel",
          "identity_revision": 1,
          "owner": "semantic-owner",
          "repository_id": "ontology-kernel"
        },
        "receipt_kind": "store",
        "role": "canonical_trust_root_digest",
        "store_head_digest": "sha256:b38b6d6cc96a19fc6ff6af60ed56828f3814d5b15e3a54da8e008bda7d89d832",
        "store_id": "semantic-trust-store",
        "store_revision": 6,
        "vote_tuple": null
      }
    ],
    "mode": "replace",
    "mutation_id": "source-receipt-mutation:authority_receipt_head_revision_fact_binding_is_exact",
    "source_receipt_tuples": [
      {
        "action_epoch": 100,
        "fact_digest": "sha256:bb53e9a7967b27d71cdc25180496f8b9d1dccae3ada1e64486f6b644e2395fce",
        "fact_schema": "semantic-authority-semantic-trust-fact.v0",
        "fact_value": {
          "kind": "digest",
          "value": "sha256:c941b19034374280208d093c576558cf16c5ebdbd2d615d8c68b8a92a507da44"
        },
        "observation_id": "receipt:publication_commit:canonical_trust_root_digest",
        "owner_repository": {
          "canonical_locator": "local://core/ontology-kernel",
          "identity_revision": 1,
          "owner": "semantic-owner",
          "repository_id": "ontology-kernel"
        },
        "receipt_kind": "store",
        "role": "canonical_trust_root_digest",
        "store_head_digest": "sha256:b38b6d6cc96a19fc6ff6af60ed56828f3814d5b15e3a54da8e008bda7d89d832",
        "store_id": "semantic-trust-store",
        "store_revision": 5,
        "vote_tuple": null
      }
    ]
  },
  "authority_receipt_repository_identity_is_exact": {
    "descriptor_edge_ids": [
      "preflight.receipt-repository"
    ],
    "expected_final_receipt_tuples": [
      {
        "action_epoch": 100,
        "fact_digest": "sha256:bb53e9a7967b27d71cdc25180496f8b9d1dccae3ada1e64486f6b644e2395fce",
        "fact_schema": "semantic-authority-semantic-trust-fact.v0",
        "fact_value": {
          "kind": "digest",
          "value": "sha256:c941b19034374280208d093c576558cf16c5ebdbd2d615d8c68b8a92a507da44"
        },
        "observation_id": "receipt:publication_commit:canonical_trust_root_digest",
        "owner_repository": {
          "canonical_locator": "local://softwareco/pi-canary-consumer",
          "identity_revision": 3,
          "owner": "consumer-owner",
          "repository_id": "pi-canary-consumer"
        },
        "receipt_kind": "store",
        "role": "canonical_trust_root_digest",
        "store_head_digest": "sha256:b38b6d6cc96a19fc6ff6af60ed56828f3814d5b15e3a54da8e008bda7d89d832",
        "store_id": "semantic-trust-store",
        "store_revision": 5,
        "vote_tuple": null
      }
    ],
    "mode": "replace",
    "mutation_id": "source-receipt-mutation:authority_receipt_repository_identity_is_exact",
    "source_receipt_tuples": [
      {
        "action_epoch": 100,
        "fact_digest": "sha256:bb53e9a7967b27d71cdc25180496f8b9d1dccae3ada1e64486f6b644e2395fce",
        "fact_schema": "semantic-authority-semantic-trust-fact.v0",
        "fact_value": {
          "kind": "digest",
          "value": "sha256:c941b19034374280208d093c576558cf16c5ebdbd2d615d8c68b8a92a507da44"
        },
        "observation_id": "receipt:publication_commit:canonical_trust_root_digest",
        "owner_repository": {
          "canonical_locator": "local://core/ontology-kernel",
          "identity_revision": 1,
          "owner": "semantic-owner",
          "repository_id": "ontology-kernel"
        },
        "receipt_kind": "store",
        "role": "canonical_trust_root_digest",
        "store_head_digest": "sha256:b38b6d6cc96a19fc6ff6af60ed56828f3814d5b15e3a54da8e008bda7d89d832",
        "store_id": "semantic-trust-store",
        "store_revision": 5,
        "vote_tuple": null
      }
    ]
  },
  "authority_snapshot_duplicate_conflicting_receipt_rejected": {
    "descriptor_edge_ids": [
      "preflight.duplicate-receipt"
    ],
    "expected_final_receipt_tuples": [
      {
        "action_epoch": 100,
        "fact_digest": "sha256:4cfdd85d750f3b4b5be02101c6f9b9e62992151e2fccdaceafe3fd1056964157",
        "fact_schema": "semantic-authority-semantic-publication-fact.v0",
        "fact_value": {
          "kind": "digest",
          "value": "sha256:cd0a0d1b25c73e87ec042b72d866371bd22043d49cb5cad779c8169ac4fc5612"
        },
        "observation_id": "receipt:publication_commit:canonical_publication_head",
        "owner_repository": {
          "canonical_locator": "local://core/ontology-kernel",
          "identity_revision": 1,
          "owner": "semantic-owner",
          "repository_id": "ontology-kernel"
        },
        "receipt_kind": "store",
        "role": "canonical_publication_head",
        "store_head_digest": "sha256:49e36b944128f9e2d23932c3ff10b01512a2ae089ab522b28abfebfea12dfeb2",
        "store_id": "semantic-publication-ledger",
        "store_revision": 1,
        "vote_tuple": null
      }
    ],
    "mode": "add",
    "mutation_id": "source-receipt-mutation:authority_snapshot_duplicate_conflicting_receipt_rejected",
    "source_receipt_tuples": [
      {
        "action_epoch": 100,
        "fact_digest": "sha256:642e864a924dcc7794ebcf64b4e1b66d9e05f84d7f4c8c9c56f1f4dfccde649c",
        "fact_schema": "semantic-authority-semantic-publication-fact.v0",
        "fact_value": {
          "kind": "digest",
          "value": "sha256:cd0a0d1b25c73e87ec042b72d866371bd22043d49cb5cad779c8169ac4fc5612"
        },
        "observation_id": "receipt:publication_commit:canonical_publication_head",
        "owner_repository": {
          "canonical_locator": "local://core/ontology-kernel",
          "identity_revision": 1,
          "owner": "semantic-owner",
          "repository_id": "ontology-kernel"
        },
        "receipt_kind": "store",
        "role": "canonical_publication_head",
        "store_head_digest": "sha256:49e36b944128f9e2d23932c3ff10b01512a2ae089ab522b28abfebfea12dfeb2",
        "store_id": "semantic-publication-ledger",
        "store_revision": 1,
        "vote_tuple": null
      }
    ]
  },
  "authority_snapshot_surplus_receipt_rejected": {
    "descriptor_edge_ids": [
      "preflight.surplus-receipt"
    ],
    "expected_final_receipt_tuples": [
      {
        "action_epoch": 100,
        "fact_digest": "sha256:642e864a924dcc7794ebcf64b4e1b66d9e05f84d7f4c8c9c56f1f4dfccde649c",
        "fact_schema": "semantic-authority-semantic-publication-fact.v0",
        "fact_value": {
          "kind": "digest",
          "value": "sha256:cd0a0d1b25c73e87ec042b72d866371bd22043d49cb5cad779c8169ac4fc5612"
        },
        "observation_id": "receipt:publication_commit:surplus",
        "owner_repository": {
          "canonical_locator": "local://core/ontology-kernel",
          "identity_revision": 1,
          "owner": "semantic-owner",
          "repository_id": "ontology-kernel"
        },
        "receipt_kind": "store",
        "role": "surplus",
        "store_head_digest": "sha256:49e36b944128f9e2d23932c3ff10b01512a2ae089ab522b28abfebfea12dfeb2",
        "store_id": "semantic-publication-ledger",
        "store_revision": 1,
        "vote_tuple": null
      }
    ],
    "mode": "add",
    "mutation_id": "source-receipt-mutation:authority_snapshot_surplus_receipt_rejected",
    "source_receipt_tuples": [
      {
        "action_epoch": 100,
        "fact_digest": "sha256:642e864a924dcc7794ebcf64b4e1b66d9e05f84d7f4c8c9c56f1f4dfccde649c",
        "fact_schema": "semantic-authority-semantic-publication-fact.v0",
        "fact_value": {
          "kind": "digest",
          "value": "sha256:cd0a0d1b25c73e87ec042b72d866371bd22043d49cb5cad779c8169ac4fc5612"
        },
        "observation_id": "receipt:publication_commit:canonical_publication_head",
        "owner_repository": {
          "canonical_locator": "local://core/ontology-kernel",
          "identity_revision": 1,
          "owner": "semantic-owner",
          "repository_id": "ontology-kernel"
        },
        "receipt_kind": "store",
        "role": "canonical_publication_head",
        "store_head_digest": "sha256:49e36b944128f9e2d23932c3ff10b01512a2ae089ab522b28abfebfea12dfeb2",
        "store_id": "semantic-publication-ledger",
        "store_revision": 1,
        "vote_tuple": null
      }
    ]
  },
  "publication_recovery_store_snapshot_action_epoch_drift_rejected": {
    "descriptor_edge_ids": [
      "recovery.snapshot-epoch-coherence"
    ],
    "expected_final_receipt_tuples": [
      {
        "action_epoch": 101,
        "fact_digest": "sha256:642e864a924dcc7794ebcf64b4e1b66d9e05f84d7f4c8c9c56f1f4dfccde649c",
        "fact_schema": "semantic-authority-semantic-publication-fact.v0",
        "fact_value": {
          "kind": "digest",
          "value": "sha256:cd0a0d1b25c73e87ec042b72d866371bd22043d49cb5cad779c8169ac4fc5612"
        },
        "observation_id": "receipt:publication_recovery:canonical_publication_status_digest",
        "owner_repository": {
          "canonical_locator": "local://core/ontology-kernel",
          "identity_revision": 1,
          "owner": "semantic-owner",
          "repository_id": "ontology-kernel"
        },
        "receipt_kind": "store",
        "role": "canonical_publication_status_digest",
        "store_head_digest": "sha256:f7376e853e56c27f0e38186327bc7b1322f23e2c6e3ccfc147c5ee016da332fd",
        "store_id": "semantic-publication-ledger",
        "store_revision": 500,
        "vote_tuple": null
      }
    ],
    "mode": "replace",
    "mutation_id": "source-receipt-mutation:publication_recovery_store_snapshot_action_epoch_drift_rejected",
    "source_receipt_tuples": [
      {
        "action_epoch": 100,
        "fact_digest": "sha256:642e864a924dcc7794ebcf64b4e1b66d9e05f84d7f4c8c9c56f1f4dfccde649c",
        "fact_schema": "semantic-authority-semantic-publication-fact.v0",
        "fact_value": {
          "kind": "digest",
          "value": "sha256:cd0a0d1b25c73e87ec042b72d866371bd22043d49cb5cad779c8169ac4fc5612"
        },
        "observation_id": "receipt:publication_recovery:canonical_publication_status_digest",
        "owner_repository": {
          "canonical_locator": "local://core/ontology-kernel",
          "identity_revision": 1,
          "owner": "semantic-owner",
          "repository_id": "ontology-kernel"
        },
        "receipt_kind": "store",
        "role": "canonical_publication_status_digest",
        "store_head_digest": "sha256:f7376e853e56c27f0e38186327bc7b1322f23e2c6e3ccfc147c5ee016da332fd",
        "store_id": "semantic-publication-ledger",
        "store_revision": 500,
        "vote_tuple": null
      }
    ]
  },
  "publication_recovery_store_snapshot_head_drift_rejected": {
    "descriptor_edge_ids": [
      "recovery.snapshot-head-coherence"
    ],
    "expected_final_receipt_tuples": [
      {
        "action_epoch": 100,
        "fact_digest": "sha256:642e864a924dcc7794ebcf64b4e1b66d9e05f84d7f4c8c9c56f1f4dfccde649c",
        "fact_schema": "semantic-authority-semantic-publication-fact.v0",
        "fact_value": {
          "kind": "digest",
          "value": "sha256:cd0a0d1b25c73e87ec042b72d866371bd22043d49cb5cad779c8169ac4fc5612"
        },
        "observation_id": "receipt:publication_recovery:canonical_publication_status_digest",
        "owner_repository": {
          "canonical_locator": "local://core/ontology-kernel",
          "identity_revision": 1,
          "owner": "semantic-owner",
          "repository_id": "ontology-kernel"
        },
        "receipt_kind": "store",
        "role": "canonical_publication_status_digest",
        "store_head_digest": "sha256:1e858f567afb0596b019f01f7e0ad1f86da6519d45246dc7a786130c7d283e30",
        "store_id": "semantic-publication-ledger",
        "store_revision": 500,
        "vote_tuple": null
      }
    ],
    "mode": "replace",
    "mutation_id": "source-receipt-mutation:publication_recovery_store_snapshot_head_drift_rejected",
    "source_receipt_tuples": [
      {
        "action_epoch": 100,
        "fact_digest": "sha256:642e864a924dcc7794ebcf64b4e1b66d9e05f84d7f4c8c9c56f1f4dfccde649c",
        "fact_schema": "semantic-authority-semantic-publication-fact.v0",
        "fact_value": {
          "kind": "digest",
          "value": "sha256:cd0a0d1b25c73e87ec042b72d866371bd22043d49cb5cad779c8169ac4fc5612"
        },
        "observation_id": "receipt:publication_recovery:canonical_publication_status_digest",
        "owner_repository": {
          "canonical_locator": "local://core/ontology-kernel",
          "identity_revision": 1,
          "owner": "semantic-owner",
          "repository_id": "ontology-kernel"
        },
        "receipt_kind": "store",
        "role": "canonical_publication_status_digest",
        "store_head_digest": "sha256:f7376e853e56c27f0e38186327bc7b1322f23e2c6e3ccfc147c5ee016da332fd",
        "store_id": "semantic-publication-ledger",
        "store_revision": 500,
        "vote_tuple": null
      }
    ]
  },
  "publication_recovery_store_snapshot_repository_drift_rejected": {
    "descriptor_edge_ids": [
      "recovery.snapshot-repository-coherence"
    ],
    "expected_final_receipt_tuples": [
      {
        "action_epoch": 100,
        "fact_digest": "sha256:642e864a924dcc7794ebcf64b4e1b66d9e05f84d7f4c8c9c56f1f4dfccde649c",
        "fact_schema": "semantic-authority-semantic-publication-fact.v0",
        "fact_value": {
          "kind": "digest",
          "value": "sha256:cd0a0d1b25c73e87ec042b72d866371bd22043d49cb5cad779c8169ac4fc5612"
        },
        "observation_id": "receipt:publication_recovery:canonical_publication_status_digest",
        "owner_repository": {
          "canonical_locator": "local://softwareco/pi-canary-consumer",
          "identity_revision": 3,
          "owner": "consumer-owner",
          "repository_id": "pi-canary-consumer"
        },
        "receipt_kind": "store",
        "role": "canonical_publication_status_digest",
        "store_head_digest": "sha256:f7376e853e56c27f0e38186327bc7b1322f23e2c6e3ccfc147c5ee016da332fd",
        "store_id": "semantic-publication-ledger",
        "store_revision": 500,
        "vote_tuple": null
      }
    ],
    "mode": "replace",
    "mutation_id": "source-receipt-mutation:publication_recovery_store_snapshot_repository_drift_rejected",
    "source_receipt_tuples": [
      {
        "action_epoch": 100,
        "fact_digest": "sha256:642e864a924dcc7794ebcf64b4e1b66d9e05f84d7f4c8c9c56f1f4dfccde649c",
        "fact_schema": "semantic-authority-semantic-publication-fact.v0",
        "fact_value": {
          "kind": "digest",
          "value": "sha256:cd0a0d1b25c73e87ec042b72d866371bd22043d49cb5cad779c8169ac4fc5612"
        },
        "observation_id": "receipt:publication_recovery:canonical_publication_status_digest",
        "owner_repository": {
          "canonical_locator": "local://core/ontology-kernel",
          "identity_revision": 1,
          "owner": "semantic-owner",
          "repository_id": "ontology-kernel"
        },
        "receipt_kind": "store",
        "role": "canonical_publication_status_digest",
        "store_head_digest": "sha256:f7376e853e56c27f0e38186327bc7b1322f23e2c6e3ccfc147c5ee016da332fd",
        "store_id": "semantic-publication-ledger",
        "store_revision": 500,
        "vote_tuple": null
      }
    ]
  },
  "publication_recovery_store_snapshot_revision_drift_rejected": {
    "descriptor_edge_ids": [
      "recovery.snapshot-revision-coherence"
    ],
    "expected_final_receipt_tuples": [
      {
        "action_epoch": 100,
        "fact_digest": "sha256:642e864a924dcc7794ebcf64b4e1b66d9e05f84d7f4c8c9c56f1f4dfccde649c",
        "fact_schema": "semantic-authority-semantic-publication-fact.v0",
        "fact_value": {
          "kind": "digest",
          "value": "sha256:cd0a0d1b25c73e87ec042b72d866371bd22043d49cb5cad779c8169ac4fc5612"
        },
        "observation_id": "receipt:publication_recovery:canonical_publication_status_digest",
        "owner_repository": {
          "canonical_locator": "local://core/ontology-kernel",
          "identity_revision": 1,
          "owner": "semantic-owner",
          "repository_id": "ontology-kernel"
        },
        "receipt_kind": "store",
        "role": "canonical_publication_status_digest",
        "store_head_digest": "sha256:f7376e853e56c27f0e38186327bc7b1322f23e2c6e3ccfc147c5ee016da332fd",
        "store_id": "semantic-publication-ledger",
        "store_revision": 501,
        "vote_tuple": null
      }
    ],
    "mode": "replace",
    "mutation_id": "source-receipt-mutation:publication_recovery_store_snapshot_revision_drift_rejected",
    "source_receipt_tuples": [
      {
        "action_epoch": 100,
        "fact_digest": "sha256:642e864a924dcc7794ebcf64b4e1b66d9e05f84d7f4c8c9c56f1f4dfccde649c",
        "fact_schema": "semantic-authority-semantic-publication-fact.v0",
        "fact_value": {
          "kind": "digest",
          "value": "sha256:cd0a0d1b25c73e87ec042b72d866371bd22043d49cb5cad779c8169ac4fc5612"
        },
        "observation_id": "receipt:publication_recovery:canonical_publication_status_digest",
        "owner_repository": {
          "canonical_locator": "local://core/ontology-kernel",
          "identity_revision": 1,
          "owner": "semantic-owner",
          "repository_id": "ontology-kernel"
        },
        "receipt_kind": "store",
        "role": "canonical_publication_status_digest",
        "store_head_digest": "sha256:f7376e853e56c27f0e38186327bc7b1322f23e2c6e3ccfc147c5ee016da332fd",
        "store_id": "semantic-publication-ledger",
        "store_revision": 500,
        "vote_tuple": null
      }
    ]
  }
}
''')


def explicit_context(item: dict) -> dict:
    context = copy.deepcopy(item["context"])
    expected_legacy_roles = set(RULE_SCHEMA_ROLES.get(item["rule"], {})) | set(RULE_PARAMETER_ROLES.get(item["rule"], set()))
    missing = expected_legacy_roles - set(context)
    if missing: raise ValueError(f"{item['name']}: explicit legacy role missing before authority wrapping: {sorted(missing)}")
    return context


def owner_read_baseline(item: dict, context: dict) -> dict[str, object]:
    expected = set(REQUIRED_RECEIPT_ROLES.get(item["rule"], set()))
    allowed_missing = MISSING_ANCHOR_NEGATIVES.get(item["name"], set())
    missing = expected - set(context)
    if missing - allowed_missing:
        raise ValueError(f"{item['name']}: explicit owner-read fact missing before authority wrapping: {sorted(missing - allowed_missing)}")
    if missing != allowed_missing:
        raise ValueError(f"{item['name']}: dedicated missing-anchor fixture did not omit exactly {sorted(allowed_missing)}")
    return {role: copy.deepcopy(context.pop(role)) for role in sorted(expected - missing, key=str.encode)}


def explicit_source_authority(item: dict, reads: dict[str, object]) -> tuple[dict[str, dict], dict[str, dict]]:
    name = item["name"]
    if name not in EXPLICIT_CASE_SOURCE_SETS: raise ValueError(f"{name}: missing explicit source-case declaration")
    store_set_id, vote_set_id = EXPLICIT_CASE_SOURCE_SETS[name]
    if store_set_id not in EXPLICIT_STORE_METADATA_SETS or vote_set_id not in EXPLICIT_VOTE_SOURCE_SETS:
        raise ValueError(f"{name}: unknown explicit source-case set")
    store_ids = EXPLICIT_STORE_METADATA_SETS[store_set_id]
    if set(store_ids) != set(reads):
        raise ValueError(f"{name}: explicit store metadata roles disagree with source facts: {sorted(set(store_ids) ^ set(reads))}")
    store_sources: dict[str, dict] = {}
    for role, tuple_id in store_ids.items():
        if tuple_id not in EXPLICIT_STORE_METADATA_TUPLES: raise ValueError(f"{name}:{role}: missing explicit store metadata tuple")
        metadata = copy.deepcopy(EXPLICIT_STORE_METADATA_TUPLES[tuple_id])
        if set(metadata) != {"owner_repository", "store_id", "store_head_digest", "store_revision", "action_epoch"}:
            raise ValueError(f"{name}:{role}: incomplete explicit store metadata tuple")
        if metadata["action_epoch"] != ACTION_EPOCH: raise ValueError(f"{name}:{role}: explicit action epoch disagrees with invocation")
        store_sources[role] = metadata
    vote_sources: dict[str, dict] = {}
    for role, source in EXPLICIT_VOTE_SOURCE_SETS[vote_set_id].items():
        if set(source) != {"fact", "store_metadata_tuple"}: raise ValueError(f"{name}:{role}: incomplete explicit vote source")
        tuple_id = source["store_metadata_tuple"]
        if tuple_id not in EXPLICIT_STORE_METADATA_TUPLES: raise ValueError(f"{name}:{role}: missing explicit vote store tuple")
        metadata = copy.deepcopy(EXPLICIT_STORE_METADATA_TUPLES[tuple_id])
        if metadata["action_epoch"] != ACTION_EPOCH: raise ValueError(f"{name}:{role}: explicit vote action epoch disagrees with invocation")
        vote_sources[role] = {"fact": copy.deepcopy(source["fact"]), "store_metadata": metadata}
    return store_sources, vote_sources


def fact_digest(fact_schema: str, fact_value: dict) -> str:
    return typed_digest("semantic-release.authority-fact.v0", {"fact_schema": fact_schema, "fact_value": fact_value})


def freshness_token_digest(fields: dict) -> str:
    keys = ("role", "category", "owner_surface", "owner_id", "owner_repository", "acquisition_contract", "acquisition_contract_digest",
        "acquisition_distribution_digest", "store_id", "store_head_digest", "store_revision", "fact_schema", "fact_digest",
        "action_epoch", "required_action_epoch_floor")
    return typed_digest("semantic-release.owner-store-freshness-cas.v0", {key: fields[key] for key in keys})


def acquisition_profile(owner_surface: str, repository: dict, contract: str) -> tuple[str, str, str]:
    contract_digest = raw("acquisition-contract:" + contract)
    distribution_digest = raw("acquisition-distribution:" + owner_surface + ":" + repository["repository_id"] + ":" + contract)
    capability = {"owner_surface": owner_surface, "owner_repository": copy.deepcopy(repository),
        "acquisition_contract": contract, "acquisition_contract_digest": contract_digest,
        "acquisition_distribution_digest": distribution_digest}
    capability_digest = typed_digest("semantic-release.owner-acquisition-capability.v0", capability)
    return contract_digest, distribution_digest, capability_digest


def acquisition_pair(rule: str, role: str, value: object, source_metadata: dict,
        *, vote_owner_id: str | None = None) -> tuple[dict, dict, dict]:
    category = "semantic_vote" if vote_owner_id is not None else ROLE_CATEGORY[role]
    if category == "semantic_vote":
        owner_surface, owner_id, repository, store_id, contract = "semantic_owner", vote_owner_id, owner_repo, f"semantic-vote:{vote_owner_id}", "ontology-kernel.owner-vote-read.v0"
    else: owner_surface, owner_id, repository, store_id, contract = CATEGORY_PROFILE[category]
    expected_metadata_keys = {"owner_repository", "store_id", "store_head_digest", "store_revision", "action_epoch"}
    if set(source_metadata) != expected_metadata_keys: raise ValueError(f"{rule}:{role}: incomplete explicit store metadata tuple")
    if source_metadata["owner_repository"] != repository: raise ValueError(f"{rule}:{role}: explicit store repository disagrees with role owner")
    store_id, store_head, store_revision = (source_metadata["store_id"], source_metadata["store_head_digest"], source_metadata["store_revision"])
    action_epoch = source_metadata["action_epoch"]
    fact_schema = FACT_SCHEMA_BY_CATEGORY[category]; encoded = value_fact(value); digest_value = fact_digest(fact_schema, encoded)
    contract_digest, distribution_digest, capability_digest = acquisition_profile(owner_surface, repository, contract)
    common = {"role": role, "category": category, "owner_surface": owner_surface, "owner_id": owner_id, "owner_repository": copy.deepcopy(repository),
        "acquisition_contract": contract, "acquisition_contract_digest": contract_digest, "acquisition_distribution_digest": distribution_digest,
        "store_id": store_id, "store_head_digest": store_head, "store_revision": store_revision, "fact_schema": fact_schema,
        "fact_digest": digest_value, "action_epoch": action_epoch, "required_action_epoch_floor": ACTION_EPOCH_FLOOR}
    token = freshness_token_digest(common); pin_id = f"pin:{rule}:{role}"
    pin = {"schema": "semantic-owner-acquisition-capability-pin.v0", "capability_pin_id": pin_id, "role": role, "category": category,
        "owner_surface": owner_surface, "owner_id": owner_id, "owner_repository": copy.deepcopy(repository), "acquisition_contract": contract,
        "acquisition_contract_digest": contract_digest, "acquisition_distribution_digest": distribution_digest, "store_id": store_id,
        "store_head_digest": store_head, "store_revision": store_revision, "fact_schema": fact_schema, "fact_digest": digest_value,
        "fact_value": encoded, "freshness_cas_token_digest": token, "required_action_epoch_floor": ACTION_EPOCH_FLOOR,
        "acquisition_capability_digest": capability_digest, "capability_pin_digest": ZERO}
    rehash(pin)
    receipt = {"schema": "semantic-owner-store-read-receipt.v0", "observation_id": f"receipt:{rule}:{role}", "role": role,
        "category": category, "issuer": {"kind": owner_surface, "id": owner_id}, "claim_scope": "owner_store_read_only",
        "owner_repository": copy.deepcopy(repository), "capability_pin_id": pin_id, "acquisition_capability_digest": capability_digest,
        "capability_pin_digest": pin["capability_pin_digest"], "acquisition_contract": contract,
        "acquisition_contract_digest": contract_digest, "acquisition_distribution_digest": distribution_digest,
        "store_id": store_id, "store_head_digest": store_head, "store_revision": store_revision, "fact_schema": fact_schema,
        "fact_digest": digest_value, "fact_value": encoded, "freshness_cas_token_digest": token, "action_epoch": action_epoch,
        "required_action_epoch_floor": ACTION_EPOCH_FLOOR, "owner_store_read_receipt_digest": ZERO}
    rehash(receipt)
    binding = {"role": role, "category": category, "observation_id": receipt["observation_id"], "capability_pin_id": pin_id,
        "owner_surface": owner_surface, "owner_id": owner_id, "owner_repository": copy.deepcopy(repository),
        "acquisition_contract": contract, "acquisition_contract_digest": contract_digest,
        "acquisition_distribution_digest": distribution_digest, "acquisition_capability_digest": capability_digest}
    return pin, receipt, binding


def role_mapping_for_node(rule: str, role: str, schemas: str | tuple[str, ...]) -> dict:
    expected = (schemas,) if isinstance(schemas, str) else schemas
    sample_schema = expected[0]
    # Role-specific owner mapping for heterogeneous rollback objects is normative.
    fixed = {
        "semantic_artifact": ("rocs", "rocs-cli", rocs_repo), "runtime_artifact": ("rocs", "rocs-cli", rocs_repo),
        "disable_artifact": ("consumer_owner", "consumer-owner", consumer_repo), "recovery_artifact": ("recovery_controller", "recovery", rocs_repo),
        "history_after": ("consumer_owner", "consumer-owner", consumer_repo), "availability": ("rocs", "rocs-cli", rocs_repo),
        "activation_availability": ("rocs", "rocs-cli", rocs_repo), "ak_linkage": ("ak", "agent-kernel", ak_repo),
        "consumer_contract": ("consumer_owner", "consumer-owner", consumer_repo),
        "semantic_materialization_technical": ("rocs", "rocs-cli", rocs_repo),
        "runtime_materialization_technical": ("rocs", "rocs-cli", rocs_repo),
        "runtime_revalidation_technical": ("rocs", "rocs-cli", rocs_repo),
        "disable_contract_technical": ("consumer_owner", "consumer-owner", consumer_repo),
        "disable_rehearsal_technical": ("recovery_controller", "recovery", rocs_repo),
        "recovery_rehearsal_technical": ("recovery_controller", "recovery", rocs_repo),
        "recovery_health_technical": ("recovery_controller", "recovery", rocs_repo),
        "intent_marker": ("recovery_controller", "recovery", rocs_repo),
        "before": ("semantic_owner", "semantic-owner", owner_repo),
        "after": ("recovery_controller", "recovery", rocs_repo),
        "marker": ("semantic_owner", "semantic-owner", owner_repo),
    }
    if role in fixed: owner_surface, owner_id, repository = fixed[role]
    elif sample_schema in SEMANTIC_SCHEMAS: owner_surface, owner_id, repository = "semantic_owner", "semantic-owner", owner_repo
    elif sample_schema in ROCS_SCHEMAS: owner_surface, owner_id, repository = "rocs", "rocs-cli", rocs_repo
    elif sample_schema in CONSUMER_SCHEMAS: owner_surface, owner_id, repository = "consumer_owner", "consumer-owner", consumer_repo
    elif sample_schema in AK_SCHEMAS: owner_surface, owner_id, repository = "ak", "agent-kernel-owner", ak_repo
    elif sample_schema in RECOVERY_SCHEMAS: owner_surface, owner_id, repository = "recovery_controller", "recovery", rocs_repo
    elif sample_schema == "semantic-pi-delivery-receipt.v0": owner_surface, owner_id, repository = "pi", "pi-adapter", pi_repo
    else: owner_surface, owner_id, repository = "rocs", "rocs-cli", rocs_repo
    sources = ["node", "parameter"] if role in NULLABLE_ARTIFACT_ROLES else ["node"]
    return {"role": role, "role_prefix": None, "sources": sources, "category": None, "owner_surface": owner_surface,
        "owner_id": owner_id, "owner_repository": copy.deepcopy(repository), "capability_pin_id": None, "capability_pin_prefix": None,
        "acquisition_contract": None, "acquisition_contract_digest": None, "acquisition_distribution_digest": None,
        "acquisition_capability_digest": None, "expected_schemas": list(expected), "minimum_cardinality": 1, "maximum_cardinality": 1,
        "description": f"Closed {rule} proof role {role}."}


def build_authority_manifest(registry: list[dict]) -> dict:
    edges_by_rule: dict[str, list[dict]] = {}
    for edge_row in registry: edges_by_rule.setdefault(edge_row["rule"], []).append(edge_row)
    entries: list[dict] = []
    for rule in sorted(ALL_RULES, key=str.encode):
        mappings: list[dict] = []
        if rule in SUBJECT_PROFILE_BY_RULE:
            profile = SUBJECT_PROFILE_BY_RULE[rule]
            mappings.append({"role": "subject", "role_prefix": None, "sources": ["subject"], "category": None,
                "owner_surface": profile["owner_surface"], "owner_id": profile["owner_id"],
                "owner_repository": copy.deepcopy(profile["owner_repository"]), "capability_pin_id": None,
                "capability_pin_prefix": None, "acquisition_contract": None, "acquisition_contract_digest": None,
                "acquisition_distribution_digest": None, "acquisition_capability_digest": None,
                "expected_schemas": copy.deepcopy(profile["expected_schemas"]), "minimum_cardinality": 0,
                "maximum_cardinality": 0, "description": f"Mechanically owned {rule} subject edge role."})
            mappings.append({"role": "authority_graph", "role_prefix": None, "sources": ["authority_graph"],
                "category": None, "owner_surface": "rocs", "owner_id": "rocs-cli", "owner_repository": copy.deepcopy(rocs_repo),
                "capability_pin_id": None, "capability_pin_prefix": None, "acquisition_contract": None,
                "acquisition_contract_digest": None, "acquisition_distribution_digest": None,
                "acquisition_capability_digest": None, "expected_schemas": [], "minimum_cardinality": 0,
                "maximum_cardinality": 0, "description": f"Mechanically owned {rule} authority-graph edge role."})
        for role in sorted(REQUIRED_RECEIPT_ROLES.get(rule, set()), key=str.encode):
            category = ROLE_CATEGORY[role]; surface, owner_id, repository, _store, contract = CATEGORY_PROFILE[category]
            contract_digest, distribution_digest, capability_digest = acquisition_profile(surface, repository, contract)
            mappings.append({"role": role, "role_prefix": None, "sources": ["receipt"], "category": category, "owner_surface": surface,
                "owner_id": owner_id, "owner_repository": copy.deepcopy(repository), "capability_pin_id": f"pin:{rule}:{role}",
                "capability_pin_prefix": None, "acquisition_contract": contract, "acquisition_contract_digest": contract_digest,
                "acquisition_distribution_digest": distribution_digest, "acquisition_capability_digest": capability_digest,
                "expected_schemas": [FACT_SCHEMA_BY_CATEGORY[category]], "minimum_cardinality": 1,
                "maximum_cardinality": 1, "description": f"Owner-issued current {role} read receipt."})
        for role, schemas in sorted(RULE_SCHEMA_ROLES.get(rule, {}).items()):
            if role not in REQUIRED_RECEIPT_ROLES.get(rule, set()): mappings.append(role_mapping_for_node(rule, role, schemas))
        for role in sorted(RULE_PARAMETER_ROLES.get(rule, set()), key=str.encode):
            if role not in {row["role"] for row in mappings}:
                mappings.append({"role": role, "role_prefix": None, "sources": ["parameter"], "category": None, "owner_surface": "semantic_owner",
                    "owner_id": "semantic-owner", "owner_repository": copy.deepcopy(owner_repo), "capability_pin_id": None, "capability_pin_prefix": None,
                    "acquisition_contract": None, "acquisition_contract_digest": None, "acquisition_distribution_digest": None,
                    "acquisition_capability_digest": None, "expected_schemas": [], "minimum_cardinality": 1, "maximum_cardinality": 1,
                    "description": f"Closed non-authority {rule} parameter {role}."})
        if rule == "compatibility":
            mappings.extend([
                {"role": "overrides_dynamic", "role_prefix": "overrides:", "sources": ["node"], "category": None, "owner_surface": "semantic_owner", "owner_id": "semantic-owner", "owner_repository": copy.deepcopy(owner_repo), "capability_pin_id": None, "capability_pin_prefix": None, "acquisition_contract": None, "acquisition_contract_digest": None, "acquisition_distribution_digest": None, "acquisition_capability_digest": None, "expected_schemas": ["semantic-compatibility-override.v0"], "minimum_cardinality": 0, "maximum_cardinality": 10000, "description": "Each compatibility override is a distinct semantic-owner node."},
                {"role": "override_approvals_dynamic", "role_prefix": "override_approvals:", "sources": ["node"], "category": None, "owner_surface": "semantic_owner", "owner_id": "semantic-owner", "owner_repository": copy.deepcopy(owner_repo), "capability_pin_id": None, "capability_pin_prefix": None, "acquisition_contract": None, "acquisition_contract_digest": None, "acquisition_distribution_digest": None, "acquisition_capability_digest": None, "expected_schemas": ["semantic-owner-approval.v0"], "minimum_cardinality": 0, "maximum_cardinality": 10000, "description": "Each override approval is a distinct semantic-owner node."},
            ])
        if rule in VOTE_RULES:
            vote_contract = "ontology-kernel.owner-vote-read.v0"
            contract_digest, distribution_digest, capability_digest = acquisition_profile("semantic_owner", owner_repo, vote_contract)
            mappings.append({"role": "owner_vote_proofs", "role_prefix": "vote-proof:", "sources": ["receipt"], "category": "semantic_vote", "owner_surface": "semantic_owner", "owner_id": None, "owner_repository": copy.deepcopy(owner_repo), "capability_pin_id": None, "capability_pin_prefix": f"pin:{rule}:vote-proof:",
                "acquisition_contract": vote_contract, "acquisition_contract_digest": contract_digest,
                "acquisition_distribution_digest": distribution_digest, "acquisition_capability_digest": capability_digest,
                "expected_schemas": [FACT_SCHEMA_BY_CATEGORY["semantic_vote"]], "minimum_cardinality": 0, "maximum_cardinality": 256,
                "description": "Every approval vote proof is read under that vote owner's pinned capability."})
        mappings.sort(key=lambda row: row["role"].encode())
        required = sorted([row["role"] for row in mappings if row["role_prefix"] is None and row["minimum_cardinality"] == 1], key=str.encode)
        rule_edges = sorted(edges_by_rule.get(rule, []), key=lambda row: row["edge_id"].encode())
        role_edge_links = [{"edge_id": row["edge_id"], "ownership": copy.deepcopy(row["ownership"]),
            "role_owners": copy.deepcopy(row["role_owners"]), "role_ids": copy.deepcopy(row["role_ids"]),
            "edge_linkage_digest": row["edge_linkage_digest"]} for row in rule_edges]
        entries.append({"rule": rule, "authority_bearing": rule in AUTHORITY_BEARING_RULES, "required_roles": required,
            "role_mappings": mappings, "edge_ids": [row["edge_id"] for row in rule_edges], "role_edge_links": role_edge_links})
    manifest = {"schema": "semantic-authority-rule-role-manifest.v0", "revision": "semantic-release-revision-v12", "rules": entries,
        "authority_rule_role_manifest_digest": ZERO}
    rehash(manifest); return manifest


def expected_vote_sources_for_audit(rule: str, subject: dict, role_artifacts: list[tuple[str, dict]]) -> list[tuple[str, dict, str]]:
    approvals: list[tuple[str, dict]] = []
    if subject.get("schema") == "semantic-owner-approval.v0": approvals.append(("subject", subject))
    approvals.extend((role, artifact) for role, artifact in role_artifacts if artifact.get("schema") == "semantic-owner-approval.v0")
    rows: list[tuple[str, dict, str]] = []
    seen: set[str] = set()
    for approval_role, approval in approvals:
        for vote in approval["votes"]:
            role = f"vote-proof:{approval_role}:{vote['owner_id']}"
            if role in seen: raise ValueError(f"duplicate vote proof role {role}")
            seen.add(role)
            rows.append((role, {"owner_id": vote["owner_id"], "owner_key_id": vote["owner_key_id"],
                "approved_action_digest": vote["approved_action_digest"], "approval_proof_digest": vote["approval_proof_digest"]}, vote["owner_id"]))
    return sorted(rows, key=lambda row: row[0].encode())


def source_receipt_audit_tuple(receipt: dict) -> dict:
    fact_value = copy.deepcopy(receipt["fact_value"])
    return {"receipt_kind": "vote" if receipt["role"].startswith("vote-proof:") else "store",
        "observation_id": receipt["observation_id"], "role": receipt["role"],
        "owner_repository": copy.deepcopy(receipt["owner_repository"]), "store_id": receipt["store_id"],
        "store_head_digest": receipt["store_head_digest"], "store_revision": receipt["store_revision"],
        "action_epoch": receipt["action_epoch"], "fact_schema": receipt["fact_schema"],
        "fact_digest": receipt["fact_digest"], "fact_value": fact_value,
        "vote_tuple": copy.deepcopy(fact_value.get("value")) if fact_value.get("kind") == "owner_vote_proof" else None}


def audit_tuple_sort_key(row: dict) -> bytes:
    return jcs(row).encode()


def build_source_case_explicitness_audit(source_cases: list[dict], final_cases: list[dict], registry: list[dict]) -> dict:
    final_by_name = {item["name"]: item for item in final_cases}
    edge_by_id = {row["edge_id"]: row for row in registry}
    mutation_cases = set(REGISTERED_SOURCE_RECEIPT_MUTATIONS)
    if mutation_cases - set(final_by_name): raise ValueError("registered source mutation names unknown case")
    rows: list[dict] = []; registered_rows: list[dict] = []
    store_tuple_count = vote_fact_count = final_receipt_count = 0
    for item in sorted(source_cases, key=lambda row: row["name"].encode()):
        legacy = explicit_context(item); reads = owner_read_baseline(item, legacy)
        store_sources, vote_sources = explicit_source_authority(item, reads)
        source_receipts: list[dict] = []
        for role in sorted(reads, key=str.encode):
            _pin, receipt, _binding = acquisition_pair(item["rule"], role, reads[role], store_sources[role])
            source_receipts.append(source_receipt_audit_tuple(receipt)); store_tuple_count += 1
        for role, source in sorted(vote_sources.items(), key=lambda row: row[0].encode()):
            owner_id = source["fact"]["owner_id"]
            _pin, receipt, _binding = acquisition_pair(item["rule"], role, source["fact"], source["store_metadata"], vote_owner_id=owner_id)
            source_receipts.append(source_receipt_audit_tuple(receipt)); vote_fact_count += 1
        source_receipts.sort(key=audit_tuple_sort_key)
        expected_final = copy.deepcopy(source_receipts); mutation_ids: list[str] = []
        declaration = REGISTERED_SOURCE_RECEIPT_MUTATIONS.get(item["name"])
        if declaration is not None:
            if item["expected_error"] is None or set(declaration) != {"mutation_id", "mode", "descriptor_edge_ids", "source_receipt_tuples", "expected_final_receipt_tuples"}:
                raise ValueError(f"{item['name']}: malformed registered source mutation")
            if declaration["mode"] not in {"add", "replace"} or len(declaration["source_receipt_tuples"]) != len(declaration["expected_final_receipt_tuples"]):
                raise ValueError(f"{item['name']}: incomplete source/final mutation tuple pairs")
            for edge_id in declaration["descriptor_edge_ids"]:
                edge_row = edge_by_id.get(edge_id)
                if edge_row is None or edge_row["drift_fixture"] != item["name"] or not edge_row["semantic_mutations"]:
                    raise ValueError(f"{item['name']}: source mutation lacks semantic descriptor linkage {edge_id}")
            for source_tuple, final_tuple in zip(declaration["source_receipt_tuples"], declaration["expected_final_receipt_tuples"]):
                if source_tuple not in source_receipts: raise ValueError(f"{item['name']}: registered mutation source tuple was not explicit")
                if declaration["mode"] == "replace": expected_final.remove(source_tuple)
                expected_final.append(copy.deepcopy(final_tuple))
            mutation_ids.append(declaration["mutation_id"])
            registered_rows.append(copy.deepcopy(declaration) | {"case_name": item["name"]})
        expected_final.sort(key=audit_tuple_sort_key)
        final_receipts = [source_receipt_audit_tuple(receipt)
            for receipt in final_by_name[item["name"]]["context"]["authority_snapshot"]["store_read_receipts"]]
        final_receipts.sort(key=audit_tuple_sort_key)
        if final_receipts != expected_final:
            raise ValueError(f"{item['name']}: final receipt differs from explicit source/expected-final tuples")
        final_receipt_count += len(final_receipts)
        rows.append({"case_name": item["name"], "rule": item["rule"], "source_receipts": source_receipts,
            "expected_final_receipts": expected_final, "registered_mutation_ids": mutation_ids})
    registered_rows.sort(key=lambda row: row["mutation_id"].encode())
    audit = {"schema": "semantic-release-source-case-explicitness-audit.v12",
        "revision": "semantic-release-revision-v12",
        "inference_policy": "explicit_source_and_expected_final_receipts_no_silent_mismatch",
        "source_case_count": len(rows), "authority_case_count": sum(row["rule"] in AUTHORITY_BEARING_RULES for row in source_cases),
        "store_metadata_tuple_count": store_tuple_count, "vote_proof_fact_count": vote_fact_count,
        "final_receipt_count": final_receipt_count, "registered_mutation_count": len(registered_rows),
        "registered_receipt_mutations": registered_rows, "cases": rows,
        "source_case_explicitness_audit_digest": ZERO}
    preimage = {key: value for key, value in audit.items() if key != "source_case_explicitness_audit_digest"}
    audit["source_case_explicitness_audit_digest"] = typed_digest("semantic-release.source-case-explicitness-audit.v12", preimage)
    return audit


def wrap_authority_context(item: dict, edge_ids: list[str], manifest: dict) -> dict:
    legacy = explicit_context(item); reads = owner_read_baseline(item, legacy)
    store_sources, explicit_vote_sources = explicit_source_authority(item, reads)
    node_bindings: list[dict] = []; parameter_bindings: list[dict] = []; nodes_by_key: dict[str, dict] = {}; role_artifacts: list[tuple[str, dict]] = []
    def bind_node(role: str, artifact: dict) -> None:
        key = artifact_digest(artifact); expected_schema = expected_artifact_schema(item["rule"], role, artifact)
        actual_issuer, actual_claim, actual_repository = artifact_authority(item["rule"], role, artifact)
        expected_issuer, expected_claim, expected_repository = artifact_authority(item["rule"], role, artifact, expected=True)
        node = {"bundle_key": key, "artifact_schema": artifact["schema"], "issuer": actual_issuer, "owner_repository": actual_repository,
            "claim_scope": actual_claim, "artifact": artifact}
        if key in nodes_by_key and nodes_by_key[key] != node: raise ValueError(f"digest collision for proof node {role}")
        nodes_by_key[key] = node; role_artifacts.append((role, artifact))
        node_bindings.append({"role": role, "bundle_key": key, "expected_schema": expected_schema,
            "expected_issuer_kind": expected_issuer["kind"], "expected_issuer_id": expected_issuer["id"],
            "expected_owner_repository": expected_repository, "expected_claim_scope": expected_claim})
    for role, value in sorted(legacy.items()):
        if role in REQUIRED_RECEIPT_ROLES.get(item["rule"], set()): raise ValueError(f"canonical role leaked from owner reads: {role}")
        if role == "overrides":
            artifacts = value if isinstance(value, list) else []
            parameter_bindings.append({"role": role, "value": value_fact([artifact_digest(x) for x in artifacts])})
            for index, artifact in enumerate(artifacts): bind_node(f"overrides:{index:06d}", artifact)
        elif role == "override_approvals":
            artifacts = value if isinstance(value, dict) else {}
            parameter_bindings.append({"role": role, "value": value_fact(sorted(artifacts, key=str.encode))})
            for key, artifact in sorted(artifacts.items()): bind_node("override_approvals:" + key, artifact)
        elif isinstance(value, dict) and "schema" in value: bind_node(role, value)
        else: parameter_bindings.append({"role": role, "value": value_fact(value)})
    node_bindings.sort(key=lambda row: row["role"].encode()); parameter_bindings.sort(key=lambda row: row["role"].encode())

    pins: list[dict] = []; receipts: list[dict] = []; receipt_bindings: list[dict] = []
    for role in sorted(reads, key=str.encode):
        pin, receipt, binding = acquisition_pair(item["rule"], role, reads[role], store_sources[role])
        pins.append(pin); receipts.append(receipt); receipt_bindings.append(binding)
    expected_votes = ({role: {"fact": fact, "owner_id": owner_id}
        for role, fact, owner_id in expected_vote_sources_for_audit(item["rule"], item["subject"], role_artifacts)}
        if item["rule"] in VOTE_RULES else {})
    if set(explicit_vote_sources) != set(expected_votes):
        raise ValueError(f"{item['name']}: explicit vote source roles disagree with approvals: {sorted(set(explicit_vote_sources) ^ set(expected_votes))}")
    for role in sorted(explicit_vote_sources, key=str.encode):
        source, expected = explicit_vote_sources[role], expected_votes[role]
        if source["fact"] != expected["fact"]: raise ValueError(f"{item['name']}:{role}: explicit vote fact disagrees with approval")
        pin, receipt, binding = acquisition_pair(item["rule"], role, source["fact"], source["store_metadata"],
            vote_owner_id=expected["owner_id"])
        pins.append(pin); receipts.append(receipt); receipt_bindings.append(binding)
    pins.sort(key=lambda row: row["capability_pin_id"].encode()); receipts.sort(key=lambda row: row["observation_id"].encode())
    receipt_bindings.sort(key=lambda row: row["role"].encode())
    config = {"schema": "semantic-authority-acquisition-config.v0", "verifier_identity": copy.deepcopy(rocs_tool), "collator": copy.deepcopy(COLLATOR),
        "collation_scope": "transport_only_no_receipt_issuance", "required_action_epoch_floor": ACTION_EPOCH_FLOOR,
        "live_acquisition_implemented": False, "pins": pins, "authority_acquisition_config_digest": ZERO}
    rehash(config)
    snapshot = {"schema": "semantic-authority-snapshot.v0", "caller_trust_boundary": "externally_configured_owner_acquisition_pins",
        "collator": copy.deepcopy(COLLATOR), "collation_scope": "transport_only_no_receipt_issuance",
        "authority_acquisition_config_digest": config["authority_acquisition_config_digest"], "action_epoch": ACTION_EPOCH,
        "store_read_receipts": receipts, "authority_snapshot_digest": ZERO}
    rehash(snapshot)
    nodes = sorted(nodes_by_key.values(), key=lambda row: row["bundle_key"].encode()); subject_digest = artifact_digest(item["subject"])
    bundle = {"schema": "semantic-authority-proof-bundle.v0", "rule": item["rule"], "subject_schema": item["subject"]["schema"],
        "subject_digest": subject_digest, "authority_snapshot_digest": snapshot["authority_snapshot_digest"], "nodes": nodes,
        "authority_proof_bundle_digest": ZERO}
    rehash(bundle)
    active_roles = sorted([row["role"] for row in receipt_bindings] + [row["role"] for row in node_bindings] + [row["role"] for row in parameter_bindings], key=str.encode)
    verifier_input = {"schema": "semantic-authority-verifier-input.v0", "rule": item["rule"], "subject_schema": item["subject"]["schema"],
        "subject_digest": subject_digest, "authority_rule_role_manifest_digest": manifest["authority_rule_role_manifest_digest"],
        "authority_acquisition_config_digest": config["authority_acquisition_config_digest"], "authority_snapshot_digest": snapshot["authority_snapshot_digest"],
        "authority_proof_bundle_digest": bundle["authority_proof_bundle_digest"], "required_action_epoch_floor": ACTION_EPOCH_FLOOR,
        "receipt_bindings": receipt_bindings, "node_bindings": node_bindings, "parameter_bindings": parameter_bindings,
        "required_observation_ids": sorted([row["observation_id"] for row in receipt_bindings], key=str.encode),
        "required_role_ids": active_roles, "required_edge_ids": sorted(edge_ids, key=str.encode), "authority_verifier_input_digest": ZERO}
    rehash(verifier_input)
    graph = {"acquisition_config": config, "authority_snapshot": snapshot, "proof_bundle": bundle, "verifier_input": verifier_input}
    apply_graph_mutation(item, graph)
    return graph


def rehash_graph(graph: dict) -> None:
    config, snapshot, bundle, verifier = graph["acquisition_config"], graph["authority_snapshot"], graph["proof_bundle"], graph["verifier_input"]
    for pin in config["pins"]: rehash(pin)
    pin_digests = {pin["capability_pin_id"]: pin["capability_pin_digest"] for pin in config["pins"]}
    for receipt in snapshot["store_read_receipts"]:
        if receipt["capability_pin_id"] in pin_digests: receipt["capability_pin_digest"] = pin_digests[receipt["capability_pin_id"]]
        rehash(receipt)
    rehash(config)
    snapshot["authority_acquisition_config_digest"] = config["authority_acquisition_config_digest"]; rehash(snapshot)
    bundle["authority_snapshot_digest"] = snapshot["authority_snapshot_digest"]; rehash(bundle)
    verifier["authority_acquisition_config_digest"] = config["authority_acquisition_config_digest"]
    verifier["authority_snapshot_digest"] = snapshot["authority_snapshot_digest"]
    verifier["authority_proof_bundle_digest"] = bundle["authority_proof_bundle_digest"]
    rehash(verifier)


def apply_graph_mutation(item: dict, graph: dict) -> None:
    name = item["name"]; config, snapshot, bundle, verifier = graph["acquisition_config"], graph["authority_snapshot"], graph["proof_bundle"], graph["verifier_input"]
    def receipt(role: str) -> dict: return next(row for row in snapshot["store_read_receipts"] if row["role"] == role)
    def remove_receipt(role: str) -> None:
        binding = next(row for row in verifier["receipt_bindings"] if row["role"] == role)
        verifier["receipt_bindings"].remove(binding); verifier["required_observation_ids"].remove(binding["observation_id"]); verifier["required_role_ids"].remove(role)
        snapshot["store_read_receipts"] = [row for row in snapshot["store_read_receipts"] if row["observation_id"] != binding["observation_id"]]
        config["pins"] = [row for row in config["pins"] if row["capability_pin_id"] != binding["capability_pin_id"]]
    if name in {"publication_recovery_store_snapshot_head_drift_rejected", "publication_recovery_store_snapshot_revision_drift_rejected",
            "publication_recovery_store_snapshot_action_epoch_drift_rejected", "publication_recovery_store_snapshot_repository_drift_rejected"}:
        role = "canonical_publication_status_digest"
        row = receipt(role); pin = next(x for x in config["pins"] if x["capability_pin_id"] == row["capability_pin_id"])
        if name == "publication_recovery_store_snapshot_head_drift_rejected":
            row["store_head_digest"] = pin["store_head_digest"] = raw("split-recovery-store-snapshot-head")
        elif name == "publication_recovery_store_snapshot_revision_drift_rejected":
            row["store_revision"] = pin["store_revision"] = row["store_revision"] + 1
        elif name == "publication_recovery_store_snapshot_action_epoch_drift_rejected":
            row["action_epoch"] = row["action_epoch"] + 1
        else:
            row["owner_repository"] = copy.deepcopy(consumer_repo)
        token_fields = {"role": role, "category": row["category"], "owner_surface": row["issuer"]["kind"],
            "owner_id": row["issuer"]["id"], "owner_repository": row["owner_repository"],
            "acquisition_contract": row["acquisition_contract"], "acquisition_contract_digest": row["acquisition_contract_digest"],
            "acquisition_distribution_digest": row["acquisition_distribution_digest"], "store_id": row["store_id"],
            "store_head_digest": row["store_head_digest"], "store_revision": row["store_revision"],
            "fact_schema": row["fact_schema"], "fact_digest": row["fact_digest"], "action_epoch": row["action_epoch"],
            "required_action_epoch_floor": row["required_action_epoch_floor"]}
        row["freshness_cas_token_digest"] = freshness_token_digest(token_fields)
        if name != "publication_recovery_store_snapshot_repository_drift_rejected":
            pin["freshness_cas_token_digest"] = row["freshness_cas_token_digest"]
        rehash_graph(graph); return
    if name == "authority_snapshot_self_digest_is_universal":
        snapshot["action_epoch"] += 1; return
    if name == "authority_bundle_key_equals_artifact_digest":
        target = bundle["nodes"][0]; old = target["bundle_key"]; target["bundle_key"] = raw("wrong-bundle-key")
        next(row for row in verifier["node_bindings"] if row["bundle_key"] == old)["bundle_key"] = target["bundle_key"]
        bundle["nodes"].sort(key=lambda row: row["bundle_key"].encode()); rehash_graph(graph); return
    if name == "authority_bundle_missing_node_fails_closed":
        bundle["nodes"].pop(); rehash_graph(graph); return
    if name == "authority_bundle_surplus_node_fails_closed":
        artifact = copy.deepcopy(predecessor); key = artifact_digest(artifact)
        bundle["nodes"].append({"bundle_key": key, "artifact_schema": artifact["schema"], "issuer": {"kind": "semantic_owner", "id": "semantic-owner"},
            "owner_repository": copy.deepcopy(owner_repo), "claim_scope": "semantic_owner_fact", "artifact": artifact})
        bundle["nodes"].sort(key=lambda row: row["bundle_key"].encode()); rehash_graph(graph); return
    if name == "authority_node_expected_schema_is_exact":
        verifier["node_bindings"][0]["expected_schema"] = "semantic-owner-set.v0"; rehash(verifier); return
    if name == "authority_node_issuer_scope_is_exact":
        bundle["nodes"][0]["issuer"] = {"kind": "consumer_owner", "id": "consumer-owner"}; rehash_graph(graph); return
    if name in {"authority_required_anchor_is_mandatory", "canonical_ak_authority_requires_independent_store_head_fact",
            "canonical_ak_authority_requires_independent_current_record_fact"}:
        # Dedicated missing-anchor cases omit the legacy fact before wrapping; no canonical value is synthesized and removed later.
        return
    if name == "authority_preflight_order_is_normative":
        verifier["node_bindings"] = list(reversed(verifier["node_bindings"])); rehash(verifier); return
    if name == "authority_receipt_category_substitution_rejected":
        row = receipt("canonical_trust_root_digest"); row["category"] = "ak_store"
        next(x for x in verifier["receipt_bindings"] if x["role"] == row["role"])["category"] = "ak_store"; rehash_graph(graph); return
    if name == "authority_receipt_repository_identity_is_exact":
        row = receipt("canonical_trust_root_digest"); row["owner_repository"] = copy.deepcopy(consumer_repo); rehash_graph(graph); return
    if name == "authority_receipt_owner_specific_pin_is_exact":
        row = receipt("canonical_trust_root_digest"); row["capability_pin_id"] = "pin:publication_commit:canonical_store_head"; rehash_graph(graph); return
    if name == "authority_receipt_head_revision_fact_binding_is_exact":
        row = receipt("canonical_trust_root_digest"); row["store_revision"] += 1; rehash_graph(graph); return
    if name == "authority_receipt_freshness_cas_floor_is_enforced":
        row = receipt("canonical_trust_root_digest"); row["action_epoch"] = ACTION_EPOCH_FLOOR - 1; rehash_graph(graph); return
    if name == "authority_snapshot_surplus_receipt_rejected":
        row = copy.deepcopy(snapshot["store_read_receipts"][0]); row["observation_id"] = "receipt:publication_commit:surplus"; row["role"] = "surplus"
        rehash(row); snapshot["store_read_receipts"].append(row); snapshot["store_read_receipts"].sort(key=lambda x: x["observation_id"].encode()); rehash_graph(graph); return
    if name == "authority_snapshot_duplicate_conflicting_receipt_rejected":
        row = copy.deepcopy(snapshot["store_read_receipts"][0]); row["fact_digest"] = raw("conflicting-duplicate-fact"); rehash(row)
        snapshot["store_read_receipts"].append(row); snapshot["store_read_receipts"].sort(key=lambda x: x["observation_id"].encode()); rehash_graph(graph); return
    if name == "authority_verifier_surplus_role_rejected":
        verifier["parameter_bindings"].append({"role": "surplus-role", "value": value_fact(raw("surplus-role"))}); verifier["parameter_bindings"].sort(key=lambda x: x["role"].encode())
        verifier["required_role_ids"].append("surplus-role"); verifier["required_role_ids"].sort(key=str.encode); rehash(verifier); return
    if name == "authority_collator_cannot_issue_receipts":
        row = receipt("canonical_trust_root_digest"); row["issuer"] = copy.deepcopy(COLLATOR); rehash_graph(graph); return
    if name == "authority_acquisition_distribution_digest_is_exact":
        row = receipt("canonical_trust_root_digest"); row["acquisition_distribution_digest"] = raw("wrong-acquisition-distribution"); rehash_graph(graph); return
    if name in {"authority_coherent_acquisition_rewrite_rejected", "authority_coherent_owner_repository_rewrite_rejected"}:
        role = "canonical_trust_root_digest"
        row = receipt(role); pin = next(x for x in config["pins"] if x["capability_pin_id"] == row["capability_pin_id"])
        binding = next(x for x in verifier["receipt_bindings"] if x["role"] == role)
        if name == "authority_coherent_owner_repository_rewrite_rejected":
            substituted_repo = copy.deepcopy(consumer_repo)
            pin.update(owner_surface="consumer_owner", owner_id="consumer-owner", owner_repository=substituted_repo)
            row.update(issuer={"kind": "consumer_owner", "id": "consumer-owner"}, owner_repository=copy.deepcopy(substituted_repo))
            binding.update(owner_surface="consumer_owner", owner_id="consumer-owner", owner_repository=copy.deepcopy(substituted_repo))
        pin["acquisition_contract"] = row["acquisition_contract"] = binding["acquisition_contract"] = "coherent.rewritten-owner-read.v0"
        contract_digest, distribution_digest, capability_digest = acquisition_profile(pin["owner_surface"], pin["owner_repository"], pin["acquisition_contract"])
        for target in (pin, row, binding):
            target["acquisition_contract_digest"] = contract_digest
            target["acquisition_distribution_digest"] = distribution_digest
            target["acquisition_capability_digest"] = capability_digest
        token_fields = {"role": role, "category": row["category"], "owner_surface": row["issuer"]["kind"], "owner_id": row["issuer"]["id"],
            "owner_repository": row["owner_repository"], "acquisition_contract": row["acquisition_contract"],
            "acquisition_contract_digest": contract_digest, "acquisition_distribution_digest": distribution_digest,
            "store_id": row["store_id"], "store_head_digest": row["store_head_digest"], "store_revision": row["store_revision"],
            "fact_schema": row["fact_schema"], "fact_digest": row["fact_digest"], "action_epoch": row["action_epoch"],
            "required_action_epoch_floor": row["required_action_epoch_floor"]}
        pin["freshness_cas_token_digest"] = row["freshness_cas_token_digest"] = freshness_token_digest(token_fields)
        rehash_graph(graph); return
    if name in {"tombstone_registry_semantic_owner_substitution_rejected", "projection_capsule_semantic_owner_substitution_rejected", "projection_rocs_proof_owner_substitution_rejected"}:
        role = {"tombstone_registry_semantic_owner_substitution_rejected": "tombstones",
            "projection_capsule_semantic_owner_substitution_rejected": "capsule",
            "projection_rocs_proof_owner_substitution_rejected": "projection"}[name]
        binding = next(x for x in verifier["node_bindings"] if x["role"] == role)
        node = next(x for x in bundle["nodes"] if x["bundle_key"] == binding["bundle_key"])
        if name == "projection_rocs_proof_owner_substitution_rejected":
            issuer, repository, claim = {"kind": "semantic_owner", "id": "semantic-owner"}, copy.deepcopy(owner_repo), "semantic_owner_fact"
        else:
            issuer, repository, claim = {"kind": "rocs", "id": "rocs-cli"}, copy.deepcopy(rocs_repo), "rocs_technical_fact"
        node.update(issuer=issuer, owner_repository=repository, claim_scope=claim)
        binding.update(expected_issuer_kind=issuer["kind"], expected_issuer_id=issuer["id"],
            expected_owner_repository=copy.deepcopy(repository), expected_claim_scope=claim)
        rehash_graph(graph); return
    if name == "owner_vote_proof_requires_pinned_owner_capability":
        row = next(x for x in snapshot["store_read_receipts"] if x["category"] == "semantic_vote"); row["issuer"]["id"] = "semantic-owner"; rehash_graph(graph); return



def decode_fact_value(value: dict) -> object:
    if value["kind"] == "null": return None
    if value["kind"] == "empty_list": return []
    if value["kind"] == "empty_map": return {}
    return copy.deepcopy(value["value"])


def semantic_authority_view(item: dict) -> dict:
    """Flatten role-keyed authority semantics while omitting wrapper linkage metadata."""
    graph = item["context"]
    config, snapshot, bundle, verifier = (graph[key] for key in ("acquisition_config", "authority_snapshot", "proof_bundle", "verifier_input"))
    view: dict[str, object] = {"rule": item["rule"], "subject": copy.deepcopy(item["subject"]), "context": {
        "acquisition": {"verifier_identity": copy.deepcopy(config["verifier_identity"]), "collator": copy.deepcopy(config["collator"]),
            "collation_scope": config["collation_scope"], "required_action_epoch_floor": config["required_action_epoch_floor"],
            "live_acquisition_implemented": config["live_acquisition_implemented"], "action_epoch": snapshot["action_epoch"]},
        "receipts": {}, "nodes": {}, "parameters": {}, "unbound_pins": [], "unbound_receipts": [], "unbound_nodes": []}}
    normalized_context = view["context"]
    assert isinstance(normalized_context, dict)
    pins_used: set[int] = set(); receipts_used: set[int] = set(); nodes_used: set[int] = set()
    for binding in verifier["receipt_bindings"]:
        pin_candidates = [copy.deepcopy(row) for row in config["pins"] if row["capability_pin_id"] == binding["capability_pin_id"]]
        receipt_candidates = [copy.deepcopy(row) for row in snapshot["store_read_receipts"] if row["observation_id"] == binding["observation_id"]]
        pins_used.update(i for i, row in enumerate(config["pins"]) if row["capability_pin_id"] == binding["capability_pin_id"])
        receipts_used.update(i for i, row in enumerate(snapshot["store_read_receipts"]) if row["observation_id"] == binding["observation_id"])
        normalized_context["receipts"][binding["role"]] = {"binding": copy.deepcopy(binding),
            "pin_candidates": pin_candidates, "receipt_candidates": receipt_candidates}
    normalized_context["unbound_pins"] = [copy.deepcopy(row) for i, row in enumerate(config["pins"]) if i not in pins_used]
    normalized_context["unbound_receipts"] = [copy.deepcopy(row) for i, row in enumerate(snapshot["store_read_receipts"]) if i not in receipts_used]
    for binding in verifier["node_bindings"]:
        candidates = [copy.deepcopy(row) for row in bundle["nodes"] if row["bundle_key"] == binding["bundle_key"]]
        nodes_used.update(i for i, row in enumerate(bundle["nodes"]) if row["bundle_key"] == binding["bundle_key"])
        clean_binding = {key: copy.deepcopy(value) for key, value in binding.items() if key != "bundle_key"}
        clean_candidates = [{key: copy.deepcopy(value) for key, value in row.items() if key != "bundle_key"} for row in candidates]
        normalized_context["nodes"][binding["role"]] = {"binding": clean_binding, "node_candidates": clean_candidates}
    normalized_context["unbound_nodes"] = [
        {key: copy.deepcopy(value) for key, value in row.items() if key != "bundle_key"}
        for i, row in enumerate(bundle["nodes"]) if i not in nodes_used]
    for binding in verifier["parameter_bindings"]:
        normalized_context["parameters"][binding["role"]] = decode_fact_value(binding["value"])
    return view


def _collect_digest_correspondence(old: object, new: object, path: str, pairs: list[tuple[str, str, str]]) -> None:
    if isinstance(old, dict) and isinstance(new, dict):
        old_schema, new_schema = old.get("schema"), new.get("schema")
        if old_schema == new_schema and old_schema in DIGEST_FIELDS:
            field = DIGEST_FIELDS[old_schema][1]
            if isinstance(old.get(field), str) and isinstance(new.get(field), str): pairs.append((old[field], new[field], path or "/"))
        for field in ("action_digest", "change_digest", "fact_digest", "freshness_cas_token_digest"):
            if isinstance(old.get(field), str) and isinstance(new.get(field), str): pairs.append((old[field], new[field], (path or "/") + "/" + field))
        for key in old.keys() & new.keys():
            token = str(key).replace("~", "~0").replace("/", "~1")
            _collect_digest_correspondence(old[key], new[key], path + "/" + token, pairs)
    elif isinstance(old, list) and isinstance(new, list):
        for index, (left, right) in enumerate(zip(old, new)): _collect_digest_correspondence(left, right, path + f"/{index}", pairs)


def _strip_digest_cascade(value: object, references: dict[str, str]) -> object:
    if isinstance(value, str): return references.get(value, value)
    if isinstance(value, list):
        rows = [_strip_digest_cascade(row, references) for row in value]
        return rows
    if isinstance(value, dict):
        self_field = DIGEST_FIELDS.get(value.get("schema"), (None, None))[1]
        omitted = {self_field, "fact_digest", "freshness_cas_token_digest"}
        return {key: _strip_digest_cascade(row, references) for key, row in value.items() if key not in omitted}
    return value


def normalized_semantic_pair(positive: dict, drift: dict) -> tuple[object, object]:
    old, new = semantic_authority_view(positive), semantic_authority_view(drift)
    pairs: list[tuple[str, str, str]] = []; _collect_digest_correspondence(old, new, "", pairs)
    paths: dict[str, str] = {}
    for old_digest, new_digest, path in pairs:
        stable = "semantic-ref:" + typed_digest("semantic-release.semantic-reference-path.v12", path)
        if old_digest not in paths or stable < paths[old_digest]: paths[old_digest] = stable
        if new_digest not in paths or stable < paths[new_digest]: paths[new_digest] = stable
    return _strip_digest_cascade(old, paths), _strip_digest_cascade(new, paths)


_MISSING = object()


def _mutation_hash(value: object) -> str:
    payload = {"present": value is not _MISSING}
    if value is not _MISSING: payload["value"] = value
    return typed_digest("semantic-release.semantic-mutation-value.v12", payload)


def _semantic_diff(old: object, new: object, path: str, rows: list[dict]) -> None:
    if isinstance(old, dict) and isinstance(new, dict):
        for key in sorted(old.keys() | new.keys(), key=lambda value: str(value).encode()):
            token = str(key).replace("~", "~0").replace("/", "~1")
            _semantic_diff(old.get(key, _MISSING), new.get(key, _MISSING), path + "/" + token, rows)
        return
    if isinstance(old, list) and isinstance(new, list):
        for index in range(max(len(old), len(new))):
            _semantic_diff(old[index] if index < len(old) else _MISSING, new[index] if index < len(new) else _MISSING,
                path + f"/{index}", rows)
        return
    if old is not _MISSING and new is not _MISSING and type(old) is type(new) and old == new: return
    rows.append({"path": path or "/", "old_semantic_hash": _mutation_hash(old), "new_semantic_hash": _mutation_hash(new)})


def semantic_mutation_descriptors(positive: dict, drift: dict) -> list[dict]:
    old, new = normalized_semantic_pair(positive, drift); rows: list[dict] = []
    _semantic_diff(old, new, "", rows)
    rows.sort(key=lambda row: row["path"].encode())
    return rows


def descriptor_role_ids(descriptors: list[dict]) -> list[str]:
    roles: set[str] = set()
    for row in descriptors:
        parts = row["path"].split("/")
        if len(parts) > 1 and parts[1] == "subject": roles.add("subject")
        elif len(parts) > 3 and parts[1] == "context" and parts[2] in {"receipts", "nodes", "parameters"}:
            role = parts[3].replace("~1", "/").replace("~0", "~")
            roles.add("authority_graph" if role == "surplus-role" else role)
        else: roles.add("authority_graph")
    return sorted(roles, key=str.encode)

def edge(edge_id: str, rule: str, description: str, positive: str, drift: str, expected_error: str) -> dict:
    return {"edge_id": edge_id, "rule": rule, "description": description, "ownership": {"kind": "single_owner", "owners": []},
        "role_owners": [], "role_ids": ["subject"], "positive_fixture": positive, "drift_fixture": drift,
        "expected_error": expected_error, "semantic_mutations": [], "edge_linkage_digest": ZERO}


def _owner_tuple(surface: str, owner_id: str, repository: dict) -> dict:
    return {"owner_surface": surface, "owner_id": owner_id, "owner_repository": copy.deepcopy(repository)}


def _manifest_mapping_for_role(manifest: dict, rule: str, role: str) -> dict:
    rule_row = next(row for row in manifest["rules"] if row["rule"] == rule)
    matches = [row for row in rule_row["role_mappings"]
        if row["role_prefix"] is None and row["role"] == role
        or row["role_prefix"] is not None and role.startswith(row["role_prefix"])]
    if len(matches) != 1: raise ValueError(f"{rule}:{role}: edge role has no unique manifest mapping")
    return matches[0]


def derive_role_owner(item: dict, role: str, manifest: dict | None) -> dict:
    if role == "subject":
        issuer, _claim, repository = artifact_authority(item["rule"], role, item["subject"])
        result = _owner_tuple(issuer["kind"], issuer["id"], repository)
        if manifest is not None:
            mapping = _manifest_mapping_for_role(manifest, item["rule"], role)
            declared = _owner_tuple(mapping["owner_surface"], mapping["owner_id"], mapping["owner_repository"])
            if result != declared or item["subject"]["schema"] not in mapping["expected_schemas"]:
                raise ValueError(f"{item['name']}: subject owner mapping drift")
        return result
    if role == "authority_graph":
        result = _owner_tuple("rocs", "rocs-cli", rocs_repo)
        if manifest is not None:
            mapping = _manifest_mapping_for_role(manifest, item["rule"], role)
            if result != _owner_tuple(mapping["owner_surface"], mapping["owner_id"], mapping["owner_repository"]):
                raise ValueError(f"{item['name']}: authority graph owner mapping drift")
        return result
    graph = item.get("context", {})
    verifier = graph.get("verifier_input", {}) if isinstance(graph, dict) else {}
    for binding in verifier.get("receipt_bindings", []):
        if binding["role"] == role:
            return _owner_tuple(binding["owner_surface"], binding["owner_id"], binding["owner_repository"])
    for binding in verifier.get("node_bindings", []):
        if binding["role"] == role:
            return _owner_tuple(binding["expected_issuer_kind"], binding["expected_issuer_id"], binding["expected_owner_repository"])
    if manifest is not None:
        mapping = _manifest_mapping_for_role(manifest, item["rule"], role)
        if mapping["owner_surface"] is not None and mapping["owner_id"] is not None and mapping["owner_repository"] is not None:
            return _owner_tuple(mapping["owner_surface"], mapping["owner_id"], mapping["owner_repository"])
    raise ValueError(f"{item['name']}:{role}: edge role owner is not mechanically derivable")


def bind_edge_ownership(row: dict, positive: dict, manifest: dict | None) -> None:
    role_owners = [{"role": role, "owner": derive_role_owner(positive, role, manifest)} for role in row["role_ids"]]
    role_owners.sort(key=lambda item: item["role"].encode())
    owners_by_jcs = {jcs(item["owner"]): item["owner"] for item in role_owners}
    owners = [copy.deepcopy(owners_by_jcs[key]) for key in sorted(owners_by_jcs, key=str.encode)]
    row["role_owners"] = role_owners
    row["ownership"] = {"kind": "single_owner" if len(owners) == 1 else "multi_owner", "owners": owners}
    linkage = {"edge_id": row["edge_id"], "rule": row["rule"], "ownership": row["ownership"],
        "role_owners": row["role_owners"], "role_ids": row["role_ids"], "positive_fixture": row["positive_fixture"],
        "drift_fixture": row["drift_fixture"], "expected_error": row["expected_error"]}
    row["edge_linkage_digest"] = typed_digest("semantic-release.authority-edge-linkage.v12", linkage)


# Finite inventory. Every row names one accepted witness and one direct one-edge drift.
authority_edge_registry = [
    edge("trust-rotation.current-root", "trust_rotation", "old root equals external semantic trust head", "valid_old_to_new_root_rotation", "rotation_not_bound_to_current_root", "trust_reference_stale"),
    edge("trust-rotation.revision", "trust_rotation", "new root and rotation revisions are prior plus one", "valid_old_to_new_root_rotation", "rotation_revision_not_increasing_rejected", "trust_reference_stale"),
    edge("trust-rotation.approval", "trust_rotation", "rotation resolves its exact owner approval action", "valid_old_to_new_root_rotation", "rotation_approval_action_drift_rejected", "trust_reference_stale"),
    edge("trust-rotation.owner-set", "trust_rotation", "rotation owner set equals owner authority chain", "valid_old_to_new_root_rotation", "rotation_owner_set_binding_drift_rejected", "trust_reference_stale"),
    edge("trust-rotation.predicate", "trust_rotation", "rotation predicate equals owner authority chain", "valid_old_to_new_root_rotation", "rotation_predicate_binding_drift_rejected", "trust_reference_stale"),
    edge("trust-rotation.namespace", "trust_rotation", "rotation namespace equals owner authority chain", "valid_old_to_new_root_rotation", "rotation_namespace_binding_drift_rejected", "trust_reference_stale"),
    edge("trust-rotation.unrevoked", "trust_rotation", "old root is absent from externally observed revocations", "valid_old_to_new_root_rotation", "revoked_rotation_root_rejected", "trust_revoked"),
    edge("trust-revocation.prior-head", "trust_revocation", "revocation prior head equals external revocation head", "valid_trust_revocation_transition", "revocation_prior_head_drift_rejected", "trust_reference_stale"),
    edge("trust-revocation.revision", "trust_revocation", "revocation revision is external prior plus one", "valid_trust_revocation_transition", "revocation_revision_not_increasing_rejected", "trust_reference_stale"),
    edge("trust-revocation.approval", "trust_revocation", "revocation resolves exact typed owner approval", "valid_trust_revocation_transition", "revocation_approval_action_drift_rejected", "trust_reference_stale"),
    edge("trust-revocation.authority-chain", "trust_revocation", "revocation action repeats complete owner authority chain", "valid_trust_revocation_transition", "trust_revocation_action_requires_full_authority_chain", "trust_reference_stale"),
    edge("publication.ak-store", "publication_commit", "publication decision store equals independent AK store anchor", "publication_result_journal_marker_bind_exactly", "canonical_ak_authority_requires_independent_store_head_fact", "self_certification"),
    edge("publication.ak-current-record", "publication_commit", "publication decision record equals independent AK current record", "publication_result_journal_marker_bind_exactly", "canonical_ak_authority_requires_independent_current_record_fact", "self_certification"),
    edge("publication.trust-namespace", "publication_commit", "publication trust root namespace joins semantic authority", "publication_result_journal_marker_bind_exactly", "publication_trust_root_namespace_binds_authority", "lifecycle_violation"),
    edge("publication.trust-policy", "publication_commit", "publication trust root policy joins semantic authority", "publication_result_journal_marker_bind_exactly", "publication_trust_root_policy_binds_authority", "lifecycle_violation"),
    edge("publication.trust-owner-set", "publication_commit", "publication trust root owner set joins semantic authority", "publication_result_journal_marker_bind_exactly", "publication_trust_root_set_binds_authority", "lifecycle_violation"),
    edge("publication.external-pin", "publication_commit", "publication trust root equals external trust anchor", "publication_result_journal_marker_bind_exactly", "publication_trust_root_requires_external_canonical_pin", "lifecycle_violation"),
    edge("publication.prior-journal-transaction", "publication_commit", "prior journal transaction equals prior status transaction", "publication_result_journal_marker_bind_exactly", "prior_journal_transaction_equals_prior_status_transaction", "lifecycle_violation"),
    edge("lifecycle.prior-head", "lifecycle", "removal prior lifecycle head equals deprecation head", "deprecation_interval_satisfied", "lifecycle_prior_head_drift_rejected", "lifecycle_violation"),
    edge("lifecycle.current-ledger-head", "lifecycle", "accepted removal endpoint equals external ledger head", "deprecation_interval_satisfied", "lifecycle_requires_accepted_current_ledger_heads", "lifecycle_violation"),
    edge("lifecycle.transaction-coordinate", "lifecycle", "lifecycle transaction coordinate equals endpoint coordinate", "deprecation_interval_satisfied", "lifecycle_transaction_coordinate_is_exact", "lifecycle_violation"),
    edge("lifecycle.transaction-namespace", "lifecycle", "lifecycle transaction namespace equals endpoint namespace", "deprecation_interval_satisfied", "lifecycle_transaction_namespace_is_exact", "lifecycle_violation"),
    edge("activation.pointer-digest", "activation_binding", "candidate prior digest equals external activation pointer", "activation_prior_plus_one_transition_accepts", "activation_current_head_equals_exact_prior", "self_certification"),
    edge("activation.pointer-pair", "activation_binding", "activation pointer digest and revision are atomically null or present", "activation_genesis_explicit_null_previous_agrees", "activation_null_pointer_revision_pair_is_atomic", "self_certification"),
    edge("activation.candidate-not-head", "activation_binding", "candidate cannot be supplied as prior canonical head", "activation_genesis_explicit_null_previous_agrees", "activation_candidate_is_not_prior_canonical_head", "self_certification"),
    edge("rollback.requester", "rollback", "rollback requester equals consumer owner", "semantic_rollback_retains_runtime", "rollback_requester_id_equals_consumer_owner", "issuer_scope_violation"),
    edge("rollback.target", "rollback", "request target equals activated intent and materialization", "semantic_rollback_retains_runtime", "rollback_request_target_equals_activated_intent_and_materialization", "rollback_unavailable"),
    edge("rollback.technical-subject", "rollback", "technical receipt subject equals target artifact", "semantic_rollback_retains_runtime", "rollback_technical_receipt_binds_exact_subject_digest", "rollback_unavailable"),
    edge("rollback.technical-coordinate", "rollback", "technical receipt coordinate equals rollback target", "semantic_rollback_retains_runtime", "rollback_technical_receipt_binds_exact_coordinate", "rollback_unavailable"),
    edge("rollback.technical-runtime", "rollback", "technical receipt runtime equals retained active runtime", "semantic_rollback_retains_runtime", "semantic_rollback_target_requires_runtime_compatibility", "rollback_unavailable"),
    edge("rollback.history-head", "rollback", "rollback prior history equals external consumer history head", "semantic_rollback_retains_runtime", "rollback_before_head_must_equal_canonical_head", "history_conflict"),
    edge("governance.task-store", "governance_contracts", "resolved task store equals independent AK task observation", "resolved_governance_reference_observation_accepts", "resolved_governance_reference_observed_head_is_exact", "self_certification"),
    edge("governance.task-record", "governance_contracts", "resolved task record equals independent AK task observation", "resolved_governance_reference_observation_accepts", "resolved_governance_reference_observed_task_digest_is_exact", "self_certification"),
    edge("governance.task-state", "governance_contracts", "resolved task state equals independent AK task observation", "resolved_governance_reference_observation_accepts", "resolved_governance_reference_observed_state_is_exact", "self_certification"),
    edge("governance.reference-owner", "governance_contracts", "reference repository equals fact owner repository", "non_authorizing_separate_coordination_and_consumer_contracts", "unresolved_dependency_binds_correct_owner_repository", "self_certification"),
    edge("governance.stop-condition", "governance_contracts", "stop condition identifier pairs exactly", "non_authorizing_separate_coordination_and_consumer_contracts", "stop_condition_id_pairs_exactly", "self_certification"),
    edge("governance.stop-fact", "governance_contracts", "stop fact identifier pairs exactly", "non_authorizing_separate_coordination_and_consumer_contracts", "stop_condition_fact_id_pairs_exactly", "self_certification"),
    edge("governance.stop-owner", "governance_contracts", "stop fact repository equals actual owner", "non_authorizing_separate_coordination_and_consumer_contracts", "stop_condition_repository_pairs_exactly", "self_certification"),
    edge("trust-rotation.ak-store", "trust_rotation", "rotation approval resolves decision under external AK store head", "valid_old_to_new_root_rotation", "rotation_requires_independent_ak_store_observation", "trust_reference_stale"),
    edge("trust-rotation.ak-current-record", "trust_rotation", "rotation approval resolves external AK current decision record", "valid_old_to_new_root_rotation", "rotation_requires_independent_ak_current_record", "trust_reference_stale"),
    edge("trust-revocation.ak-store", "trust_revocation", "revocation approval resolves decision under external AK store head", "valid_trust_revocation_transition", "revocation_requires_independent_ak_store_observation", "trust_reference_stale"),
    edge("trust-revocation.ak-current-record", "trust_revocation", "revocation approval resolves external AK current decision record", "valid_trust_revocation_transition", "revocation_requires_independent_ak_current_record", "trust_reference_stale"),
    edge("compatibility-override.ak-store", "compatibility", "override approval resolves decision under external AK store head", "executable_owner_override_accepts", "override_requires_independent_ak_store_observation", "compatibility_rejected"),
    edge("compatibility-override.ak-current-record", "compatibility", "override approval resolves external AK current decision record", "executable_owner_override_accepts", "override_requires_independent_ak_current_record", "compatibility_rejected"),
    edge("publication.trust-revocation", "publication_commit", "publication root is absent from external revocation ledger", "publication_result_journal_marker_bind_exactly", "publication_rejects_externally_revoked_trust_root", "lifecycle_violation"),
    edge("lifecycle.external-prior-head", "lifecycle", "candidate lifecycle predecessor equals external lifecycle head", "deprecation_interval_satisfied", "lifecycle_current_prior_head_is_external", "lifecycle_violation"),
    edge("activation.candidate-unrevoked", "activation_binding", "candidate activation is unrevoked before CAS", "activation_genesis_explicit_null_previous_agrees", "activation_candidate_must_be_unrevoked", "self_certification"),
    edge("activation.candidate-unsuperseded", "activation_binding", "candidate activation is unsuperseded before CAS", "activation_genesis_explicit_null_previous_agrees", "activation_candidate_must_be_unsuperseded", "self_certification"),
    edge("rollback.controller", "rollback", "rollback controller equals external recovery-controller observation", "semantic_rollback_retains_runtime", "rollback_controller_equals_external_recovery_observation", "rollback_unavailable"),
    edge("rollback.epoch", "rollback", "rollback epoch equals external recovery availability epoch", "semantic_rollback_retains_runtime", "rollback_epoch_equals_external_recovery_observation", "rollback_unavailable"),
    edge("recovery.controller", "publication_recovery", "publication recovery controller equals external controller observation", "recovery_after_linearization_completes", "publication_recovery_controller_is_exact", "recovery_needed"),
    edge("recovery.runtime", "publication_recovery", "publication recovery runtime equals external controller runtime", "recovery_after_linearization_completes", "publication_recovery_runtime_is_exact", "recovery_needed"),
    edge("recovery.epoch", "publication_recovery", "publication recovery epoch equals external availability epoch", "recovery_after_linearization_completes", "publication_recovery_epoch_is_exact", "recovery_needed"),
    edge("governance.independent-task-snapshot", "governance_contracts", "resolved task observation equals independent snapshot anchor", "resolved_governance_reference_observation_accepts", "resolved_governance_reference_compares_independent_snapshot", "self_certification"),
    edge("governance.evidence-owner", "governance_contracts", "evidence reference repository equals evidence fact owner", "non_authorizing_separate_coordination_and_consumer_contracts", "governance_evidence_reference_uses_fact_owner", "self_certification"),
    edge("governance.semantic-stop-owner", "governance_contracts", "semantic trust stop is owned by semantic owner", "non_authorizing_separate_coordination_and_consumer_contracts", "semantic_stop_fact_has_semantic_owner", "self_certification"),
    edge("governance.ak-stop-owner", "governance_contracts", "AK currentness stop is owned by AK", "non_authorizing_separate_coordination_and_consumer_contracts", "ak_stop_fact_has_ak_owner", "self_certification"),
    edge("governance.consumer-stop-owner", "governance_contracts", "activation/history stop is owned by consumer owner", "non_authorizing_separate_coordination_and_consumer_contracts", "consumer_stop_fact_has_consumer_owner", "self_certification"),
    edge("preflight.snapshot-self-digest", "publication_commit", "snapshot self-digest validates before every domain rule", "publication_result_journal_marker_bind_exactly", "authority_snapshot_self_digest_is_universal", "digest_mismatch"),
    edge("preflight.missing-node", "publication_commit", "every bound proof node is present", "publication_result_journal_marker_bind_exactly", "authority_bundle_missing_node_fails_closed", "self_certification"),
    edge("preflight.surplus-node", "publication_commit", "surplus authority nodes are rejected", "publication_result_journal_marker_bind_exactly", "authority_bundle_surplus_node_fails_closed", "self_certification"),
    edge("preflight.expected-schema", "publication_commit", "resolved node schema equals binding and rule expectation", "publication_result_journal_marker_bind_exactly", "authority_node_expected_schema_is_exact", "malformed_input"),
    edge("preflight.issuer-scope", "publication_commit", "resolved node issuer and claim scope are owner-correct", "publication_result_journal_marker_bind_exactly", "authority_node_issuer_scope_is_exact", "issuer_scope_violation"),
    edge("preflight.required-anchor", "publication_commit", "every rule-required external anchor is present", "publication_result_journal_marker_bind_exactly", "authority_required_anchor_is_mandatory", "self_certification"),
    edge("recovery.marker", "publication_recovery", "linearized recovery resolves exact durable marker", "recovery_after_linearization_completes", "recovery_marker_must_match_exact_journal_and_result", "recovery_needed"),
    edge("recovery.result-transaction", "publication_recovery", "recovery result transaction equals journal transaction", "recovery_after_linearization_completes", "recovery_result_transaction_binds_transaction", "recovery_needed"),
    edge("approval.vote-provenance", "approval_threshold", "every vote proof is read under the exact vote owner's capability pin", "threshold_two_of_three_accepts", "owner_vote_proof_requires_pinned_owner_capability", "issuer_scope_violation"),
    edge("acceptance.current-owner-head", "acceptance_binding", "consumer acceptance digest and revision equal the current consumer-owner store head", "acceptance_owner_scope_binding_exact", "consumer_acceptance_must_equal_current_owner_head", "self_certification"),
    edge("ak-decision.current-store", "ak_decision", "AK decision resolves against the exact canonical store head and current record", "canonical_accepted_ak_decision_accepts", "ak_store_head_stale_rejected", "self_certification"),
    edge("generation.current-activation", "generation_activation", "generation uses exactly the current consumer activation receipt and revision", "generation_from_current_activation_accepts", "generation_from_nonhead_activation_rejected", "activation_not_current"),
    edge("publication-cas.current-state", "publication_cas", "publication CAS expected revision equals the owner-read canonical ledger revision", "publication_fresh_cas_accepts", "publication_stale_cas_rejected", "publication_conflict"),
    edge("publication-cas.fork-head", "publication_cas", "publication CAS expected head equals the owner-read canonical ledger head", "publication_fresh_cas_accepts", "publication_fork_rejected", "publication_fork"),
    edge("publication-transition.prior-journal", "publication_transition", "publication transition joins the complete canonical prior journal", "withdrawal_transition_committed", "status_transition_prior_journal_drift_rejected", "lifecycle_violation"),
    edge("publication-transition.canonical-head", "publication_transition", "publication transition prior revision and head equal owner-read canonical publication state", "withdrawal_transition_committed", "publication_transition_requires_canonical_publication_head", "lifecycle_violation"),
    edge("version-binding.permanent", "version_binding", "namespace and version remain permanently bound to one capsule digest", "version_binding_existing_coordinate_is_stable", "namespace_version_digest_reuse_conflicts", "version_conflict"),
    edge("publication.canonical-head", "publication_commit", "publication expected prior revision and head equal owner-read canonical publication state", "publication_result_journal_marker_bind_exactly", "publication_commit_requires_canonical_publication_head", "lifecycle_violation"),
    edge("recovery.canonical-ledger-head", "publication_recovery", "recovery before-state and prior journal equal canonical owner ledger heads", "recovery_after_linearization_completes", "publication_recovery_requires_canonical_ledger_head", "recovery_needed"),
    edge("governance.rollback-owner-kind", "governance_contracts", "task rollback owner kind and ID equal the owning surface", "non_authorizing_separate_coordination_and_consumer_contracts", "task_contract_binds_exact_rollback_owner_kind", "self_certification"),
    edge("rollback.availability-owner", "rollback", "rollback availability proof is ROCS-owned technical evidence", "semantic_rollback_retains_runtime", "rollback_availability_proof_has_rocs_owner", "issuer_scope_violation"),
    edge("rollback.history-owner", "rollback", "rollback history transition is issued by the consumer owner", "semantic_rollback_retains_runtime", "rollback_history_transition_has_consumer_owner", "issuer_scope_violation"),
    edge("preflight.receipt-category", "publication_commit", "receipt role category equals the normative manifest mapping", "publication_result_journal_marker_bind_exactly", "authority_receipt_category_substitution_rejected", "issuer_scope_violation"),
    edge("preflight.receipt-repository", "publication_commit", "receipt carries the complete exact owner repository identity", "publication_result_journal_marker_bind_exactly", "authority_receipt_repository_identity_is_exact", "issuer_scope_violation"),
    edge("preflight.receipt-pin", "publication_commit", "receipt resolves only through its role's exact owner-specific capability pin", "publication_result_journal_marker_bind_exactly", "authority_receipt_owner_specific_pin_is_exact", "issuer_scope_violation"),
    edge("preflight.receipt-store-fact", "publication_commit", "receipt store head and revision cryptographically bind fact schema digest and value", "publication_result_journal_marker_bind_exactly", "authority_receipt_head_revision_fact_binding_is_exact", "issuer_scope_violation"),
    edge("preflight.receipt-freshness", "publication_commit", "receipt CAS freshness token meets the externally configured action-time floor", "publication_result_journal_marker_bind_exactly", "authority_receipt_freshness_cas_floor_is_enforced", "issuer_scope_violation"),
    edge("preflight.surplus-receipt", "publication_commit", "snapshot observation IDs equal receipt bindings with no surplus", "publication_result_journal_marker_bind_exactly", "authority_snapshot_surplus_receipt_rejected", "self_certification"),
    edge("preflight.duplicate-receipt", "publication_commit", "duplicate or conflicting snapshot observation IDs are rejected", "publication_result_journal_marker_bind_exactly", "authority_snapshot_duplicate_conflicting_receipt_rejected", "malformed_input"),
    edge("preflight.surplus-role", "publication_commit", "manifest closure rejects every unbound or surplus role", "publication_result_journal_marker_bind_exactly", "authority_verifier_surplus_role_rejected", "self_certification"),
    edge("preflight.collator-no-issuance", "publication_commit", "the transport-only collator cannot issue owner store-read receipts", "publication_result_journal_marker_bind_exactly", "authority_collator_cannot_issue_receipts", "issuer_scope_violation"),
    edge("preflight.acquisition-distribution", "publication_commit", "receipt acquisition contract distribution digest equals the external owner pin", "publication_result_journal_marker_bind_exactly", "authority_acquisition_distribution_digest_is_exact", "issuer_scope_violation"),
    edge("preflight.coherent-acquisition-rewrite", "publication_commit", "coherent config and receipt acquisition rewrites still equal the hard-pinned role manifest", "publication_result_journal_marker_bind_exactly", "authority_coherent_acquisition_rewrite_rejected", "issuer_scope_violation"),
    edge("preflight.coherent-owner-repository-rewrite", "publication_commit", "coherent config and receipt owner/repository rewrites still equal the hard-pinned role manifest", "publication_result_journal_marker_bind_exactly", "authority_coherent_owner_repository_rewrite_rejected", "issuer_scope_violation"),
    edge("tombstone-reuse.current-registry", "tombstone_reuse", "tombstone evaluation uses the semantic owner's current lifecycle/tombstone head", "non_tombstoned_identifier_accepts", "tombstone_reuse_stale_registry_rejected", "lifecycle_violation"),
    edge("tombstone-reuse.semantic-owner", "tombstone_reuse", "the current tombstone registry proof is issued by the exact semantic owner", "non_tombstoned_identifier_accepts", "tombstone_registry_semantic_owner_substitution_rejected", "issuer_scope_violation"),
    edge("projection.current-tombstone", "projection", "projection capsule tombstones equal the semantic owner's current lifecycle/tombstone head", "exact_payload_projection_accepts", "projection_stale_tombstone_registry_rejected", "projection_mismatch"),
    edge("projection.semantic-owner-capsule", "projection", "projection resolves its capsule from the exact semantic owner", "exact_payload_projection_accepts", "projection_capsule_semantic_owner_substitution_rejected", "issuer_scope_violation"),
    edge("projection.rocs-proof-owner", "projection", "projection and material-tree proofs are issued by the exact ROCS owner", "exact_payload_projection_accepts", "projection_rocs_proof_owner_substitution_rejected", "issuer_scope_violation"),
    edge("recovery.result-coordinate", "publication_recovery", "recovery result coordinate and namespace fully join the transaction", "recovery_after_linearization_completes", "publication_recovery_result_coordinate_join_is_exact", "recovery_needed"),
    edge("recovery.before-status", "publication_recovery", "recovery resolves the complete canonical before-status object", "recovery_after_linearization_completes", "publication_recovery_before_status_is_canonical", "recovery_needed"),
    edge("recovery.prior-journal-full", "publication_recovery", "recovery resolves and fully joins the canonical prior journal", "recovery_after_linearization_completes", "publication_recovery_prior_journal_full_join_is_exact", "recovery_needed"),
    edge("recovery.complete-transaction", "publication_recovery", "authority-bearing recovery requires a non-null complete transaction", "recovery_after_linearization_completes", "publication_recovery_null_transaction_rejected", "self_certification"),
    edge("recovery.complete-result", "publication_recovery", "authority-bearing recovery requires a non-null complete result", "recovery_after_linearization_completes", "publication_recovery_null_result_rejected", "self_certification"),
    edge("recovery.complete-marker", "publication_recovery", "authority-bearing recovery requires a non-null complete marker", "recovery_after_linearization_completes", "publication_recovery_null_marker_rejected", "recovery_needed"),
    edge("recovery.complete-before", "publication_recovery", "authority-bearing recovery requires a non-null complete before state", "recovery_after_linearization_completes", "publication_recovery_null_before_rejected", "self_certification"),
    edge("recovery.complete-after", "publication_recovery", "authority-bearing recovery requires a non-null complete after state", "recovery_after_linearization_completes", "publication_recovery_null_after_rejected", "self_certification"),
    edge("tombstone-reuse.namespace-currentness", "tombstone_reuse", "tombstone reuse joins the exact current namespace", "non_tombstoned_identifier_accepts", "tombstone_reuse_namespace_currentness_rejected", "lifecycle_violation"),
    edge("tombstone-reuse.lifecycle-head-currentness", "tombstone_reuse", "tombstone reuse joins the exact current lifecycle head", "non_tombstoned_identifier_accepts", "tombstone_reuse_lifecycle_head_currentness_rejected", "lifecycle_violation"),
    edge("tombstone-reuse.registry-revision-currentness", "tombstone_reuse", "tombstone reuse joins the exact current registry revision", "non_tombstoned_identifier_accepts", "tombstone_reuse_registry_revision_currentness_rejected", "lifecycle_violation"),
    edge("tombstone-reuse.prior-registry-object", "tombstone_reuse", "tombstone reuse resolves the exact prior registry object", "non_tombstoned_identifier_accepts", "tombstone_history_truncation_rejected", "lifecycle_violation"),
    edge("tombstone-reuse.append-only-prior", "tombstone_reuse", "tombstone reuse rejects deletion from the resolved prior registry", "non_tombstoned_identifier_accepts", "tombstone_history_dropped_cumulative_entry_rejected", "lifecycle_violation"),
    edge("projection.namespace-currentness", "projection", "projection joins the exact current tombstone namespace", "exact_payload_projection_accepts", "projection_namespace_currentness_rejected", "projection_mismatch"),
    edge("projection.lifecycle-head-currentness", "projection", "projection joins the exact current lifecycle head", "exact_payload_projection_accepts", "projection_lifecycle_head_currentness_rejected", "projection_mismatch"),
    edge("projection.registry-revision-currentness", "projection", "projection joins the exact current tombstone revision", "exact_payload_projection_accepts", "projection_registry_revision_currentness_rejected", "projection_mismatch"),
    edge("projection.prior-registry-object", "projection", "projection resolves the exact append-only prior registry", "exact_payload_projection_accepts", "projection_complete_tombstone_history_required", "projection_mismatch"),
    edge("projection.materialization-coordinate", "projection", "materialization coordinate equals the resolved capsule coordinate", "exact_payload_projection_accepts", "projection_materialization_coordinate_equals_capsule_coordinate", "projection_mismatch"),
    edge("projection.capsule-tombstone-revision", "projection", "capsule tombstone revision equals the current owner tuple", "exact_payload_projection_accepts", "projection_capsule_tombstone_revision_is_exact", "projection_mismatch"),
    edge("recovery.prelinear-no-durable-marker", "publication_recovery", "pre-linearization recovery proves no durable commit marker", "recovery_before_linearization_discards", "recovery_prelinearization_rejects_durable_marker", "recovery_needed"),
    edge("recovery.intent-required", "publication_recovery", "pre-linearization recovery requires its non-durable intent descriptor", "recovery_before_linearization_discards", "recovery_prelinearization_requires_intent_descriptor", "self_certification"),
    edge("recovery.intent-nondurable", "publication_recovery", "intent descriptor cannot claim completed fsync", "recovery_before_linearization_discards", "recovery_intent_descriptor_cannot_claim_fsync", "malformed_input"),
    edge("recovery.intent-owner", "publication_recovery", "intent descriptor is recovery-controller issued", "recovery_before_linearization_discards", "recovery_intent_descriptor_owner_is_exact", "issuer_scope_violation"),
    edge("recovery.before-state-owner", "publication_recovery", "before state receipt is semantic-owner issued", "recovery_after_linearization_completes", "recovery_before_state_is_semantic_owner_issued", "issuer_scope_violation"),
    edge("recovery.after-state-owner", "publication_recovery", "after operational state receipt is recovery-controller issued", "recovery_after_linearization_completes", "recovery_after_state_is_controller_issued", "issuer_scope_violation"),
    edge("recovery.state-namespace", "publication_recovery", "typed recovery state receipts bind the transaction namespace", "recovery_after_linearization_completes", "recovery_state_receipt_namespace_is_exact", "recovery_needed"),
    edge("recovery.current-journal", "publication_recovery", "current recovery journal equals the coherent owner snapshot", "recovery_after_linearization_completes", "publication_recovery_current_journal_receipt_is_exact", "recovery_needed"),
    edge("recovery.transition-expectation", "publication_recovery", "recovery result equals the owner-issued transition expectation", "recovery_after_linearization_completes", "publication_recovery_transition_expectation_is_exact", "recovery_needed"),
    edge("recovery.snapshot-head-coherence", "publication_recovery", "all semantic publication facts share one owner-store head", "recovery_after_linearization_completes", "publication_recovery_store_snapshot_head_drift_rejected", "issuer_scope_violation"),
    edge("recovery.snapshot-revision-coherence", "publication_recovery", "all semantic publication facts share one owner-store revision", "recovery_after_linearization_completes", "publication_recovery_store_snapshot_revision_drift_rejected", "issuer_scope_violation"),
    edge("recovery.snapshot-epoch-coherence", "publication_recovery", "all semantic publication facts share one action epoch", "recovery_after_linearization_completes", "publication_recovery_store_snapshot_action_epoch_drift_rejected", "issuer_scope_violation"),
    edge("recovery.snapshot-repository-coherence", "publication_recovery", "all semantic publication facts share one owner repository", "recovery_after_linearization_completes", "publication_recovery_store_snapshot_repository_drift_rejected", "issuer_scope_violation"),
]
authority_edge_registry.sort(key=lambda row: row["edge_id"].encode())
edge_ids_by_rule: dict[str, list[str]] = {}
for row in authority_edge_registry: edge_ids_by_rule.setdefault(row["rule"], []).append(row["edge_id"])
if set(edge_ids_by_rule) != AUTHORITY_BEARING_RULES:
    raise ValueError(f"authority rule registry coverage drift: {sorted(AUTHORITY_BEARING_RULES - set(edge_ids_by_rule))} / {sorted(set(edge_ids_by_rule) - AUTHORITY_BEARING_RULES)}")
legacy_cases = copy.deepcopy(cases)
legacy_by_name = {item["name"]: item for item in legacy_cases}
if len(legacy_by_name) != len(legacy_cases): raise ValueError("duplicate differential case")
for rule in AUTHORITY_BEARING_RULES:
    subjects = [item["subject"] for item in legacy_cases if item["rule"] == rule and item["schema_valid"] and item["expected_error"] is None]
    if not subjects: raise ValueError(f"{rule}: no structurally valid subject for owner mapping")
    tuples = []
    for subject in subjects:
        issuer, _claim, repository = artifact_authority(rule, "subject", subject)
        tuples.append(_owner_tuple(issuer["kind"], issuer["id"], repository))
    if any(row != tuples[0] for row in tuples): raise ValueError(f"{rule}: heterogeneous subject owner mapping")
    SUBJECT_PROFILE_BY_RULE[rule] = {**tuples[0], "expected_schemas": sorted({row["schema"] for row in subjects}, key=str.encode)}
for row in authority_edge_registry:
    if row["positive_fixture"] not in legacy_by_name or row["drift_fixture"] not in legacy_by_name: raise ValueError(f"missing edge fixture {row['edge_id']}")
# First pass computes normalized semantic mutations. Initial subject ownership is derived before the
# provisional manifest; final role ownership is re-derived from every concrete linked role mapping.
for row in authority_edge_registry:
    bind_edge_ownership(row, legacy_by_name[row["positive_fixture"]], None)
provisional_manifest = build_authority_manifest(authority_edge_registry)
provisional_cases = copy.deepcopy(legacy_cases)
for item in provisional_cases:
    item["context"] = wrap_authority_context(item, edge_ids_by_rule.get(item["rule"], []), provisional_manifest)
provisional_by_name = {item["name"]: item for item in provisional_cases}
for row in authority_edge_registry:
    descriptors = semantic_mutation_descriptors(provisional_by_name[row["positive_fixture"]], provisional_by_name[row["drift_fixture"]])
    if not descriptors: raise ValueError(f"authority edge has no normalized semantic mutation: {row['edge_id']}")
    row["semantic_mutations"] = descriptors
    row["role_ids"] = descriptor_role_ids(descriptors)
    bind_edge_ownership(row, provisional_by_name[row["positive_fixture"]], provisional_manifest)

authority_manifest = build_authority_manifest(authority_edge_registry)
cases = copy.deepcopy(legacy_cases)
for item in cases:
    item["context"] = wrap_authority_context(item, edge_ids_by_rule.get(item["rule"], []), authority_manifest)
by_case_name = {item["name"]: item for item in cases}
for row in authority_edge_registry:
    recomputed = semantic_mutation_descriptors(by_case_name[row["positive_fixture"]], by_case_name[row["drift_fixture"]])
    if recomputed != row["semantic_mutations"]: raise ValueError(f"semantic mutation descriptor did not converge: {row['edge_id']}")
source_case_explicitness_audit = build_source_case_explicitness_audit(legacy_cases, cases, authority_edge_registry)

# Golden graph examples make the terminal pin, owner receipt, manifest, and closed proof graph replayable.
accepted_graph = by_case_name["publication_result_journal_marker_bind_exactly"]["context"]
add("authority_rule_role_manifest", copy.deepcopy(authority_manifest))
add("authority_acquisition_config", copy.deepcopy(accepted_graph["acquisition_config"]))
add("authority_snapshot", copy.deepcopy(accepted_graph["authority_snapshot"]))
add("authority_proof_bundle", copy.deepcopy(accepted_graph["proof_bundle"]))
add("authority_verifier_input", copy.deepcopy(accepted_graph["verifier_input"]))
golden["chain_assertions"].extend([
    {"record": "authority_snapshot", "instance_path": "/authority_acquisition_config_digest", "equals_record": "authority_acquisition_config"},
    {"record": "authority_proof_bundle", "instance_path": "/authority_snapshot_digest", "equals_record": "authority_snapshot"},
    {"record": "authority_verifier_input", "instance_path": "/authority_rule_role_manifest_digest", "equals_record": "authority_rule_role_manifest"},
    {"record": "authority_verifier_input", "instance_path": "/authority_acquisition_config_digest", "equals_record": "authority_acquisition_config"},
    {"record": "authority_verifier_input", "instance_path": "/authority_snapshot_digest", "equals_record": "authority_snapshot"},
    {"record": "authority_verifier_input", "instance_path": "/authority_proof_bundle_digest", "equals_record": "authority_proof_bundle"},
])

differential = {"protocol": "semantic-release-v0", "rfc_revision": "semantic-release-revision-v12",
    "source_case_explicitness_audit": source_case_explicitness_audit,
    "authority_rule_role_manifest": authority_manifest, "authority_edge_registry": authority_edge_registry,
    "cases": cases, "raw_json_cases": raw_json_cases}

write_schema()
for path, value in ((ROOT / "golden-fixtures.json", golden), (ROOT / "differential-fixtures.json", differential)):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"wrote schema, {len(records)} golden records, {len(authority_manifest['rules'])} manifest rules, {len(authority_edge_registry)} authority edges, and {len(cases)} differential cases")
