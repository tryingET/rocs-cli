#!/usr/bin/env python3
"""Deterministically regenerate the normative JSON fixtures; not an authority source."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from validate_fixtures import COORDINATE_DOMAIN, DIGEST_FIELDS, domain_digest, object_digest

ROOT = Path(__file__).resolve().parent
ZERO = "sha256:" + "0" * 64
records: list[dict] = []
by_name: dict[str, dict] = {}


def raw(label: str, domain: str = "semantic-release.raw-blob.v0") -> str:
    return domain_digest(domain, label.encode("utf-8"))


def add(name: str, instance: dict, domain: str | None = None, omitted: str | None = None) -> dict:
    if instance["schema"] == "semantic-release-coordinate.v0":
        domain = COORDINATE_DOMAIN
        omitted = None
    else:
        mapped_domain, mapped_omitted = DIGEST_FIELDS[instance["schema"]]
        domain = domain or mapped_domain
        omitted = omitted or mapped_omitted
        instance[omitted] = ZERO
    canonical, digest = object_digest(instance, domain, omitted)
    if omitted:
        instance[omitted] = digest
    record = {
        "name": name,
        "domain": domain,
        "omitted_field": omitted,
        "canonical_preimage": canonical,
        "digest": digest,
        "instance": instance,
    }
    records.append(record)
    by_name[name] = record
    return instance


def d(name: str) -> str:
    return by_name[name]["digest"]


def rehash(instance: dict) -> None:
    domain, omitted = DIGEST_FIELDS[instance["schema"]]
    instance[omitted] = ZERO
    _, instance[omitted] = object_digest(instance, domain, omitted)


owner_repo = {
    "owner": "semantic-owner",
    "repository_id": "ontology-kernel",
    "canonical_locator": "local://core/ontology-kernel",
    "identity_revision": 1,
}
consumer_repo = {
    "owner": "consumer-owner",
    "repository_id": "pi-canary-consumer",
    "canonical_locator": "local://softwareco/pi-canary-consumer",
    "identity_revision": 3,
}
rocs_tool = {
    "tool": "rocs-cli",
    "version": "1.4.0",
    "distribution_digest": raw("rocs-cli-1.4.0-distribution"),
    "protocol_version": "semantic-release-v0",
}
recovery_tool = {
    "tool": "semantic-recovery-controller",
    "version": "1.0.0",
    "distribution_digest": raw("recovery-controller-1.0.0-distribution"),
    "protocol_version": "semantic-release-v0",
}
old_runtime = {
    "tool": "rocs-cli",
    "version": "1.3.2",
    "distribution_digest": raw("rocs-cli-1.3.2-distribution"),
    "protocol_version": "semantic-release-v0",
}
predecessor_coordinate = {
    "schema": "semantic-release-coordinate.v0",
    "namespace": "ai-society.core",
    "semantic_version": "1.0.0",
    "capsule_digest": raw("predecessor-capsule"),
}

source = add("source_manifest", {
    "schema": "semantic-source-manifest.v0",
    "repository": owner_repo,
    "source_revision": "0123456789abcdef0123456789abcdef01234567",
    "source_root": "ontology",
    "clean_committed": True,
    "entries": [
        {"path": "concepts", "kind": "directory", "mode": 493},
        {"path": "concepts/agent.yaml", "kind": "file", "mode": 420, "byte_length": 28, "content_digest": raw("id: core.Agent\nlabel: Agent\n")},
        {"path": "manifest.yaml", "kind": "file", "mode": 420, "byte_length": 16, "content_digest": raw("namespace: core\n")},
    ],
    "source_manifest_digest": ZERO,
})

payload = add("payload_manifest", {
    "schema": "semantic-material-manifest.v0",
    "tree_role": "compiled_payload",
    "entries": [
        {"path": "index.json", "kind": "file", "mode": 420, "byte_length": 17, "content_digest": raw('{"core.Agent":0}\n')},
        {"path": "records", "kind": "directory", "mode": 493},
        {"path": "records/core.Agent.json", "kind": "file", "mode": 420, "byte_length": 36, "content_digest": raw('{"id":"core.Agent","label":"Agent"}\n')},
    ],
    "material_manifest_digest": ZERO,
})

compatibility = add("compatibility_report", {
    "schema": "semantic-compatibility-report.v0",
    "namespace": "ai-society.core",
    "prior_coordinate": predecessor_coordinate,
    "candidate_version": "1.1.0",
    "policy_revision": 7,
    "policy_digest": raw("compatibility-policy-revision-7"),
    "changes": [
        {"category": "addition", "semantic_id": "core.Agent", "effect": "minor", "condition_id": None}
    ],
    "conditions": [],
    "classification": "compatible",
    "required_semver_effect": "minor",
    "deprecations": [],
    "removals": [],
    "tombstones": [],
    "override_approval_digest": None,
    "compatibility_report_digest": ZERO,
})

capsule = add("capsule", {
    "schema": "semantic-release-capsule.v0",
    "namespace": "ai-society.core",
    "semantic_version": "1.1.0",
    "source_manifest_digest": d("source_manifest"),
    "semantic_payload_digest": raw("semantic-payload-v1.1.0", "semantic-release.semantic-payload.v0"),
    "material_manifest_digest": d("payload_manifest"),
    "compatibility_report_digest": d("compatibility_report"),
    "owner_policy_revision": 12,
    "owner_policy_digest": raw("owner-policy-revision-12"),
    "compilation_contract_digest": raw("compilation-contract-v0"),
    "required_protocol_versions": ["semantic-discovery-v0", "semantic-release-v0"],
    "predecessor_coordinate": predecessor_coordinate,
    "tombstone_registry_digest": raw("tombstone-registry-revision-4"),
    "capsule_digest": ZERO,
})

coordinate = add("coordinate", {
    "schema": "semantic-release-coordinate.v0",
    "namespace": capsule["namespace"],
    "semantic_version": capsule["semantic_version"],
    "capsule_digest": d("capsule"),
})

build = add("build_receipt", {
    "schema": "semantic-build-receipt.v0",
    "source_manifest_digest": d("source_manifest"),
    "compilation_contract_digest": capsule["compilation_contract_digest"],
    "tool_identity": rocs_tool,
    "payload_manifest_digest": d("payload_manifest"),
    "semantic_payload_digest": capsule["semantic_payload_digest"],
    "compatibility_report_digest": d("compatibility_report"),
    "candidate_capsule_digest": d("capsule"),
    "reproducible": True,
    "build_receipt_digest": ZERO,
})

owner_approval = add("owner_approval", {
    "schema": "semantic-owner-approval.v0",
    "namespace": "ai-society.core",
    "owner_policy_revision": 12,
    "owner_policy_digest": capsule["owner_policy_digest"],
    "owner_set_digest": raw("semantic-owner-set-revision-8"),
    "approval_predicate": "threshold",
    "source_manifest_digest": d("source_manifest"),
    "candidate_capsule_digest": d("capsule"),
    "compatibility_report_digest": d("compatibility_report"),
    "votes": [
        {"owner_id": "owner-a", "owner_key_id": "owner-a-key-3", "approved_candidate_digest": d("capsule"), "approval_proof_digest": raw("owner-a-approval-proof")},
        {"owner_id": "owner-b", "owner_key_id": "owner-b-key-2", "approved_candidate_digest": d("capsule"), "approval_proof_digest": raw("owner-b-approval-proof")},
    ],
    "decision": {"authority": "semantic-owner", "decision_id": "release-1-1-0", "outcome": "accepted", "record_digest": raw("semantic-owner-release-decision")},
    "owner_approval_digest": ZERO,
})

publication = add("owner_publication", {
    "schema": "semantic-owner-publication.v0",
    "coordinate": coordinate,
    "owner_approval_digest": d("owner_approval"),
    "ledger_namespace": "ai-society.core",
    "expected_prior_revision": 1,
    "ledger_revision": 2,
    "prior_publication_digest": raw("publication-ledger-revision-1"),
    "trust_root_id": "semantic-owner-local-root",
    "trust_root_revision": 5,
    "trust_root_digest": raw("semantic-owner-trust-root-revision-5"),
    "status": "published",
    "supersedes_publication_digest": None,
    "owner_publication_digest": ZERO,
})
trust = {
    "trust_root_id": publication["trust_root_id"],
    "trust_root_revision": publication["trust_root_revision"],
    "trust_root_digest": publication["trust_root_digest"],
    "publication_ledger_revision": publication["ledger_revision"],
    "publication_digest": d("owner_publication"),
}
rollback_target = {
    "semantic_mode": "predecessor",
    "semantic_coordinate": predecessor_coordinate,
    "runtime_mode": "retain",
    "runtime_identity": None,
}

intent = add("consumer_intent", {
    "schema": "semantic-consumer-intent.v0",
    "consumer_repository": consumer_repo,
    "intent_revision": 4,
    "desired_coordinate": coordinate,
    "runtime_identity": rocs_tool,
    "requested_posture": "named_canary",
    "accepted_compatibility": "compatible",
    "rollback_target": rollback_target,
    "owner_decision": {"authority": "consumer-owner", "decision_id": "request-named-canary", "outcome": "accepted", "record_digest": raw("consumer-intent-decision")},
    "trust_reference": trust,
    "verifier_contract_digest": raw("materialization-verifier-contract-v0"),
    "limits_digest": raw("materialization-limits-v0"),
    "consumer_intent_digest": ZERO,
})

acceptance = add("owner_acceptance", {
    "schema": "semantic-owner-acceptance.v0",
    "consumer_intent_digest": d("consumer_intent"),
    "consumer_repository": consumer_repo,
    "acceptance_authority": {"kind": "consumer_owner", "id": "consumer-owner"},
    "acceptance_revision": 4,
    "governing_scope": "repository:pi-canary-consumer/canary:operator-a",
    "accepted_posture": "named_canary",
    "decision": {"authority": "consumer-owner", "decision_id": "accept-materialization", "outcome": "accepted", "record_digest": raw("consumer-acceptance-decision")},
    "valid_through_intent_revision": 4,
    "activation_epoch_not_after": 100,
    "revoked_by_digest": None,
    "owner_acceptance_digest": ZERO,
})

consumer_manifest = add("consumer_material_manifest", {
    "schema": "semantic-material-manifest.v0",
    "tree_role": "consumer_materialization",
    "entries": [
        {"path": "index.json", "kind": "file", "mode": 420, "byte_length": 17, "content_digest": raw('{"core.Agent":0}\n')},
        {"path": "records", "kind": "directory", "mode": 493},
        {"path": "records/core.Agent.json", "kind": "file", "mode": 420, "byte_length": 36, "content_digest": raw('{"id":"core.Agent","label":"Agent"}\n')},
    ],
    "material_manifest_digest": ZERO,
})

materialization = add("materialization_verification_receipt", {
    "schema": "semantic-materialization-verification-receipt.v0",
    "issuer": {"kind": "rocs", "id": "rocs-cli"},
    "consumer_intent_digest": d("consumer_intent"),
    "owner_acceptance_digest": d("owner_acceptance"),
    "coordinate": coordinate,
    "owner_approval_digest": d("owner_approval"),
    "trust_reference": trust,
    "runtime_identity": rocs_tool,
    "expected_manifest_digest": d("consumer_material_manifest"),
    "actual_manifest_digest": d("consumer_material_manifest"),
    "consumer_repository": consumer_repo,
    "compatibility_report_digest": d("compatibility_report"),
    "compatibility_outcome": "compatible",
    "prior_receipt_digest": raw("predecessor-materialization-receipt"),
    "rollback_target": rollback_target,
    "rollback_materialized": True,
    "verifier_contract_digest": intent["verifier_contract_digest"],
    "transaction_id": "materialize-intent-4",
    "journal_state": "committed",
    "commit_marker_digest": raw("materialization-commit-marker-4"),
    "materialization_verification_receipt_digest": ZERO,
})

activation = add("activation_receipt", {
    "schema": "semantic-activation-receipt.v0",
    "issuer": {"kind": "consumer_owner", "id": "consumer-owner"},
    "owner_acceptance_digest": d("owner_acceptance"),
    "materialization_verification_receipt_digest": d("materialization_verification_receipt"),
    "consumer_repository": consumer_repo,
    "coordinate": coordinate,
    "runtime_identity": rocs_tool,
    "activation_scope": "named_canary",
    "activation_revision": 1,
    "activation_epoch": 90,
    "gate_decision": {"authority": "consumer-owner", "decision_id": "activate-operator-a-canary", "outcome": "accepted", "record_digest": raw("named-canary-activation-decision")},
    "previous_activation_receipt_digest": None,
    "status": "activated",
    "supersedes_activation_receipt_digest": None,
    "activation_receipt_digest": ZERO,
})

rocs_generation = add("rocs_generation_receipt", {
    "schema": "semantic-rocs-generation-receipt.v0",
    "issuer": {"kind": "rocs", "id": "rocs-cli"},
    "claim_scope": "generated_output_only",
    "activation_receipt_digest": d("activation_receipt"),
    "coordinate": coordinate,
    "runtime_identity": rocs_tool,
    "request_digest": raw("discovery-request"),
    "result_digest": raw("discovery-result"),
    "effective_execution_digest": raw("effective-execution"),
    "candidate_ids": ["core.Agent"],
    "pack_digests": [raw("bounded-pack-core-agent")],
    "outcome": "matched",
    "rocs_generation_receipt_digest": ZERO,
})

pi_delivery = add("pi_delivery_receipt", {
    "schema": "semantic-pi-delivery-receipt.v0",
    "issuer": {"kind": "pi", "id": "pi-semantic-adapter"},
    "claim_scope": "delivered_to_prompt_run_only",
    "rocs_generation_receipt_digest": d("rocs_generation_receipt"),
    "prompt_run_digest": raw("prompt-run-42"),
    "delivered_effective_execution_digest": rocs_generation["effective_execution_digest"],
    "delivery_outcome": "delivered",
    "pi_delivery_receipt_digest": ZERO,
})

ak_link = add("ak_evidence_linkage", {
    "schema": "semantic-ak-evidence-linkage.v0",
    "issuer": {"kind": "ak", "id": "agent-kernel"},
    "claim_scope": "lineage_linkage_only",
    "task_reference_digest": raw("ak-task-9001"),
    "decision_reference_digest": activation["gate_decision"]["record_digest"],
    "evidence_record_digest": raw("ak-evidence-9001"),
    "activation_receipt_digest": d("activation_receipt"),
    "rocs_generation_receipt_digest": d("rocs_generation_receipt"),
    "pi_delivery_receipt_digest": d("pi_delivery_receipt"),
    "empirical_outcome_reference_digest": None,
    "ak_evidence_linkage_digest": ZERO,
})

rollback_request = add("rollback_request", {
    "schema": "semantic-rollback-request.v0",
    "issuer": {"kind": "consumer_owner", "id": "consumer-owner"},
    "axis": "semantic",
    "active_activation_receipt_digest": d("activation_receipt"),
    "from_coordinate": coordinate,
    "from_runtime_identity": rocs_tool,
    "target": rollback_target,
    "target_materialization_receipt_digest": materialization["prior_receipt_digest"],
    "recovery_runtime_identity": recovery_tool,
    "owner_decision": {"authority": "consumer-owner", "decision_id": "rollback-canary", "outcome": "accepted", "record_digest": raw("rollback-decision")},
    "precondition_digest": raw("rollback-preconditions-verified"),
    "rollback_request_digest": ZERO,
})

rollback_receipt = add("rollback_receipt", {
    "schema": "semantic-rollback-receipt.v0",
    "issuer": {"kind": "recovery_controller", "id": "semantic-recovery-controller"},
    "rollback_request_digest": d("rollback_request"),
    "result": "rolled_back",
    "active_coordinate_after": predecessor_coordinate,
    "active_runtime_after": rocs_tool,
    "availability_proof_digest": raw("predecessor-availability-proof"),
    "history_head_before": d("activation_receipt"),
    "history_head_after": raw("consumer-history-head-after-rollback"),
    "error_digest": None,
    "supersedes_activation_receipt_digest": d("activation_receipt"),
    "rollback_receipt_digest": ZERO,
})

audit = add("audit_envelope", {
    "schema": "semantic-audit-envelope.v0",
    "artifact_schema": "semantic-rollback-receipt.v0",
    "artifact_digest": d("rollback_receipt"),
    "event": "rolled_back",
    "recorded_at": "2026-07-12T22:00:00Z",
    "issuer": {"kind": "ak", "id": "agent-kernel"},
    "audit_sequence": 9,
    "previous_audit_envelope_digest": raw("audit-envelope-8"),
    "audit_envelope_digest": ZERO,
})

error = add("error_envelope", {
    "schema": "semantic-protocol-error.v0",
    "code": "rollback_unavailable",
    "stage": "rollback",
    "retryable": False,
    "related_artifact_digest": d("rollback_request"),
    "details": [{"key": "target", "value": "predecessor materialization absent"}],
    "error_digest": ZERO,
})

links = [
    ("capsule", "/source_manifest_digest", "source_manifest"),
    ("capsule", "/material_manifest_digest", "payload_manifest"),
    ("capsule", "/compatibility_report_digest", "compatibility_report"),
    ("coordinate", "/capsule_digest", "capsule"),
    ("build_receipt", "/candidate_capsule_digest", "capsule"),
    ("owner_approval", "/candidate_capsule_digest", "capsule"),
    ("owner_publication", "/owner_approval_digest", "owner_approval"),
    ("consumer_intent", "/trust_reference/publication_digest", "owner_publication"),
    ("owner_acceptance", "/consumer_intent_digest", "consumer_intent"),
    ("materialization_verification_receipt", "/owner_acceptance_digest", "owner_acceptance"),
    ("materialization_verification_receipt", "/expected_manifest_digest", "consumer_material_manifest"),
    ("activation_receipt", "/materialization_verification_receipt_digest", "materialization_verification_receipt"),
    ("rocs_generation_receipt", "/activation_receipt_digest", "activation_receipt"),
    ("pi_delivery_receipt", "/rocs_generation_receipt_digest", "rocs_generation_receipt"),
    ("ak_evidence_linkage", "/pi_delivery_receipt_digest", "pi_delivery_receipt"),
    ("rollback_request", "/active_activation_receipt_digest", "activation_receipt"),
    ("rollback_receipt", "/rollback_request_digest", "rollback_request"),
    ("audit_envelope", "/artifact_digest", "rollback_receipt"),
]

golden = {
    "protocol": "semantic-release-v0",
    "rfc_revision": "semantic-release-revision-v1",
    "canonicalization": "RFC8785 JCS after duplicate-free UTF-8 integer-only I-JSON validation",
    "digest_construction": "sha256(UTF8(domain) || 0x00 || preimage)",
    "raw_preimages": [
        {"name": "raw_blob_example", "domain": "semantic-release.raw-blob.v0", "preimage_utf8": "id: core.Agent\nlabel: Agent\n", "digest": raw("id: core.Agent\nlabel: Agent\n")},
        {"name": "semantic_payload_example", "domain": "semantic-release.semantic-payload.v0", "preimage_utf8": "semantic-payload-v1.1.0", "digest": raw("semantic-payload-v1.1.0", "semantic-release.semantic-payload.v0")},
    ],
    "records": records,
    "chain_assertions": [
        {"record": a, "instance_path": p, "equals_record": b} for a, p, b in links
    ],
}

self_certification = copy.deepcopy(acceptance)
self_certification["acceptance_authority"] = {"kind": "rocs", "id": "rocs-cli"}
version_conflict = copy.deepcopy(publication)
version_conflict["coordinate"] = {**coordinate, "capsule_digest": raw("conflicting-capsule")}
incomplete_tree = copy.deepcopy(materialization)
incomplete_tree["actual_manifest_digest"] = raw("actual-incomplete-tree")
compatibility_unknown = copy.deepcopy(materialization)
compatibility_unknown["compatibility_outcome"] = "unknown"
mutable_timestamp = copy.deepcopy(materialization)
mutable_timestamp["recorded_at"] = "2026-07-12T22:00:00Z"
stale_trust = copy.deepcopy(intent)
revoked_trust = copy.deepcopy(intent)
rollback_unavailable = copy.deepcopy(rollback_request)
rollback_unavailable["target_materialization_receipt_digest"] = None
bad_order = copy.deepcopy(source)
bad_order["entries"] = list(reversed(bad_order["entries"]))
bad_issuer = copy.deepcopy(pi_delivery)
bad_issuer["issuer"] = {"kind": "rocs", "id": "rocs-cli"}
for counterexample in (
    self_certification,
    version_conflict,
    incomplete_tree,
    compatibility_unknown,
    mutable_timestamp,
    stale_trust,
    revoked_trust,
    rollback_unavailable,
    bad_order,
    bad_issuer,
):
    rehash(counterexample)

differential = {
    "protocol": "semantic-release-v0",
    "rfc_revision": "semantic-release-revision-v1",
    "cases": [
        {"name": "consumer_cannot_self_certify_acceptance", "rule": "self_certification", "schema_valid": True, "expected_error": "self_certification", "subject": self_certification, "context": {}},
        {"name": "namespace_version_digest_reuse_conflicts", "rule": "version_conflict", "schema_valid": True, "expected_error": "version_conflict", "subject": version_conflict, "context": {"existing_coordinate": coordinate}},
        {"name": "complete_tree_digest_mismatch", "rule": "incomplete_tree", "schema_valid": True, "expected_error": "incomplete_tree", "subject": incomplete_tree, "context": {"expected_paths": ["index.json", "records", "records/core.Agent.json"], "actual_paths": ["index.json", "records"]}},
        {"name": "compatibility_unknown_fails_closed", "rule": "compatibility_unknown", "schema_valid": True, "expected_error": "compatibility_unknown", "subject": compatibility_unknown, "context": {}},
        {"name": "timestamp_forbidden_in_receipt", "rule": "mutable_timestamp", "schema_valid": False, "expected_error": "malformed_input", "subject": mutable_timestamp, "context": {}},
        {"name": "trust_root_revision_stale", "rule": "stale_trust", "schema_valid": True, "expected_error": "trust_reference_stale", "subject": stale_trust, "context": {"minimum_trust_root_revision": 6, "minimum_publication_ledger_revision": 2}},
        {"name": "publication_ledger_revision_stale", "rule": "stale_trust", "schema_valid": True, "expected_error": "trust_reference_stale", "subject": stale_trust, "context": {"minimum_trust_root_revision": 5, "minimum_publication_ledger_revision": 3}},
        {"name": "trust_root_explicitly_revoked", "rule": "revoked_trust", "schema_valid": True, "expected_error": "trust_revoked", "subject": revoked_trust, "context": {"revoked_trust_root_digests": [trust["trust_root_digest"]]}},
        {"name": "semantic_rollback_target_not_materialized", "rule": "rollback_unavailability", "schema_valid": True, "expected_error": "rollback_unavailable", "subject": rollback_unavailable, "context": {}},
        {"name": "manifest_entries_not_utf8_sorted", "rule": "manifest_order", "schema_valid": True, "expected_error": "malformed_input", "subject": bad_order, "context": {}},
        {"name": "pi_delivery_wrong_issuer_scope", "rule": "issuer_scope", "schema_valid": True, "expected_error": "issuer_scope_violation", "subject": bad_issuer, "context": {}},
    ],
}

for path, value in ((ROOT / "golden-fixtures.json", golden), (ROOT / "differential-fixtures.json", differential)):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"wrote {len(records)} golden records and {len(differential['cases'])} differential cases")
