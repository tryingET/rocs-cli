"""Canonical Decision 103 digest domains over RFC 8785 bytes."""
from __future__ import annotations

import hashlib
from copy import deepcopy
from types import MappingProxyType
from typing import Any, Mapping

from rocs_cli.semantic_adopted_protocol import jcs_bytes

DOMAINS: Mapping[str, str] = MappingProxyType({
    "candidate": "rocs-semantic-policy-candidate-v1",
    "verdict": "rocs-semantic-policy-verdict-v1",
    "publication_event": "rocs-semantic-policy-publication-event-v1",
    "publication_history": "rocs-semantic-policy-publication-history-v1",
    "owner_head": "rocs-semantic-policy-owner-head-v1",
    "read_receipt": "rocs-semantic-policy-owner-read-receipt-v1",
    "currentness_proof": "rocs-semantic-policy-currentness-v1",
    "custody_policy": "rocs-semantic-policy-custody-policy-v1",
    "contamination_manifest": "rocs-semantic-policy-contamination-v1",
    "preregistration": "rocs-semantic-policy-preregistration-v1",
    "execution_attempt": "rocs-semantic-policy-execution-attempt-v1",
    "approval_artifact": "rocs-semantic-policy-approval-artifact-v1",
    "issuer_trust": "rocs-semantic-policy-issuer-trust-v1",
    "caller_challenge": "rocs-semantic-policy-caller-challenge-v1",
    "owner_checkpoint": "rocs-semantic-policy-owner-checkpoint-v1",
    "policy_semantic_binding": "rocs-semantic-policy-binding-v1",
    "attempt_envelope": "rocs-semantic-policy-attempt-envelope-v1",
    "issuer_attestation": "rocs-semantic-policy-issuer-attestation-v1",
    "challenge_consumption": "rocs-semantic-policy-challenge-consumption-v1",
    "verification_request": "rocs-semantic-policy-verification-request-v1",
    "ontology_inventory": "rocs-semantic-policy-ontology-inventory-v1",
    "policy_binding_receipt": "rocs-semantic-policy-binding-receipt-v1",
    "receipt_attestation_body": "rocs-semantic-policy-receipt-body-v1",
    "challenge_consumption_body": "rocs-semantic-policy-consumption-body-v1",
    "b0_exposure_evidence": "rocs-semantic-policy-b0-exposure-v1",
    "access_history_event": "rocs-semantic-policy-access-event-v1",
    "access_history": "rocs-semantic-policy-access-history-v1",
    "role_separation_receipt": "rocs-semantic-policy-role-separation-v1",
    "process_reservation": "rocs-semantic-policy-process-reservation-v1",
    "rollback_plan": "rocs-semantic-policy-evaluation-rollback-v1",
    "policy_concept_ids": "rocs-semantic-policy-concept-ids-v1",
    "joint_route_sets": "rocs-semantic-policy-joint-sets-v1",
    "capability_coordinate": "rocs-semantic-policy-capability-coordinate-v1",
    "clock_coordinate": "rocs-semantic-policy-clock-coordinate-v1",
    "approval_attestation_body": "rocs-semantic-policy-approval-body-v1",
    "verdict_approval_subject": "rocs-semantic-policy-verdict-approval-subject-v1",
    "publication_approval_subject": "rocs-semantic-policy-publication-approval-subject-v1",
    "authority_credential": "rocs-semantic-policy-authority-credential-v1",
    "channel_coordinate": "rocs-semantic-policy-acquisition-channel-coordinate-v1",
    "consumption_store_coordinate": "rocs-semantic-policy-consumption-store-coordinate-v1",
    "consumption_signing_key_coordinate": "rocs-semantic-policy-consumption-signing-key-coordinate-v1",
    "execution_contamination": "rocs-semantic-policy-execution-contamination-v1",
    "custody_readiness": "rocs-semantic-policy-custody-readiness-v1",
    "custody_readiness_subject": "rocs-semantic-policy-custody-readiness-subject-v1",
    "execution_contamination_subject": "rocs-semantic-policy-execution-contamination-subject-v1",
    "custody_readiness_verification_request": "rocs-semantic-policy-custody-readiness-verification-request-v1",
    "execution_contamination_verification_request": "rocs-semantic-policy-execution-contamination-verification-request-v1",
    "preexecution_verification_bundle": "rocs-semantic-policy-preexecution-verification-bundle-v1",
    "protected_access_activation_subject": "rocs-semantic-policy-protected-access-activation-subject-v1",
    "protected_access_activation": "rocs-semantic-policy-protected-access-activation-v1",
    "evaluator_invocation_challenge": "rocs-semantic-policy-evaluator-invocation-challenge-v1",
    "evaluator_execution_start_subject": "rocs-semantic-policy-evaluator-execution-start-subject-v1",
    "evaluator_execution_start_proof": "rocs-semantic-policy-evaluator-execution-start-proof-v1",
    "evaluator_execution_start_verification_request": "rocs-semantic-policy-evaluator-execution-start-verification-request-v1",
    "evaluator_execution_launch_subject": "rocs-semantic-policy-evaluator-execution-launch-subject-v1",
    "evaluator_execution_launch_receipt": "rocs-semantic-policy-evaluator-execution-launch-receipt-v1",
    "evaluator_authenticated_channel_coordinate": "rocs-semantic-policy-evaluator-authenticated-channel-coordinate-v1",
    "protected_descriptor_handoff_subject": "rocs-semantic-policy-protected-descriptor-handoff-subject-v1",
    "protected_descriptor_handoff_receipt": "rocs-semantic-policy-protected-descriptor-handoff-receipt-v1",
    "protected_access_closure_subject": "rocs-semantic-policy-protected-access-closure-subject-v1",
    "protected_access_closure": "rocs-semantic-policy-protected-access-closure-v1",
})


class AdoptedDigestError(ValueError):
    """Unknown domain or malformed digest preimage."""


def raw_domain_digest(name: str, payload: bytes) -> str:
    if name not in DOMAINS or type(payload) is not bytes:
        raise AdoptedDigestError("unknown digest domain or non-byte payload")
    digest = hashlib.sha256(DOMAINS[name].encode("ascii") + b"\0" + payload).hexdigest()
    return f"sha256:{digest}"


def domain_digest(name: str, value: Any) -> str:
    return raw_domain_digest(name, jcs_bytes(value))


def object_digest(name: str, value: Mapping[str, Any], omitted_field: str) -> str:
    if type(value) is not dict or type(omitted_field) is not str or omitted_field not in value:
        raise AdoptedDigestError("object digest requires an exact omitted field")
    preimage = deepcopy(value)
    preimage.pop(omitted_field)
    return domain_digest(name, preimage)
