import hashlib, re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Iterable, Mapping
from rocs_cli.semantic_adopted_digests import domain_digest, object_digest
from rocs_cli.semantic_adopted_authority import CandidateSupport
from rocs_cli.semantic_adopted_protocol import jcs_bytes, strict_json_loads, validate_definition
ISSUE_KINDS = frozenset({"invalid_input", "unknown_role", "missing_preimage", "schema_invalid", "self_edge", "back_edge", "phase_forward_edge", "digest_mismatch", "nested_mismatch", "opaque_caller_request", "topology_invalid"})
class AdoptedGraphError(ValueError):
    def __init__(self, kind: str, role: str | None = None):
        self.kind = kind if kind in ISSUE_KINDS else "topology_invalid"
        self.role = role if type(role) is str and role in ROLE_SPECS else None
        super().__init__(self.kind if self.role is None else f"{self.kind}:{self.role}")
@dataclass(frozen=True)
class GraphEdge: source: str; digest_field: str; target: str; object_field: str | None = None; nullable: bool = False
@dataclass(frozen=True)
class RoleSpec: phase: int; definition: str | None; schema: str | None; digest_domain: str | None; self_digest_field: str | None
@dataclass(frozen=True)
class ExecutionGraphSupport:
    candidate_support: CandidateSupport; participant_credentials: tuple[Mapping[str, Any], ...]; custody_readiness_subject: Mapping[str, Any]; custody_readiness_receipt: Mapping[str, Any]; custody_readiness_request: Mapping[str, Any]
@dataclass(frozen=True)
class GraphConsistency: consistency_verified: bool; authority_verified: bool; roles_verified: tuple[str, ...]
_SPECS: dict[str, RoleSpec] = {}; _EDGES: list[GraphEdge] = []
def _role(role: str, phase: int, definition: str, schema: str, domain: str, field: str) -> None: _SPECS[role] = RoleSpec(phase, definition, schema, domain, field)
def _projection(role: str, phase: int, domain: str | None) -> None: _SPECS[role] = RoleSpec(phase, None, None, domain, None)
def _edge(source: str, digest: str, target: str, obj: str | None = None, nullable: bool = False) -> None: _EDGES.append(GraphEdge(source, digest, target, obj, nullable))
_role("inventory", 0, "ontologyInventory", "semantic-routing-policy-ontology-inventory.v1", "ontology_inventory", "inventory_digest")
_role("custody_policy", 0, "custodyPolicy", "semantic-routing-policy-custody-policy.v1", "custody_policy", "policy_digest")
for name in ("base_access_history", "activated_access_history", "terminal_access_history"):
    _role(name, {"base_access_history": 0, "activated_access_history": 13, "terminal_access_history": 24}[name], "accessHistory", "semantic-routing-policy-access-history.v1", "access_history", "history_digest")
_role("role_separation", 0, "roleSeparationReceipt", "semantic-routing-policy-role-separation-receipt.v1", "role_separation_receipt", "receipt_digest")
_projection("policy_concept_ids", 3, "policy_concept_ids")
_projection("joint_route_sets", 3, "joint_route_sets")
_role("semantic_binding", 4, "policySemanticBinding", None, "policy_semantic_binding", "binding_digest")
_role("custodian_credential", 0, "authorityCredential", "semantic-routing-policy-authority-credential.v1", "authority_credential", "credential_digest")
_role("reviewer_credential", 0, "authorityCredential", "semantic-routing-policy-authority-credential.v1", "authority_credential", "credential_digest")
_role("evaluator_credential", 15, "authorityCredential", "semantic-routing-policy-authority-credential.v1", "authority_credential", "credential_digest")
_role("gateway_credential", 15, "authorityCredential", "semantic-routing-policy-authority-credential.v1", "authority_credential", "credential_digest")
_role("semantic_owner_credential", 28, "authorityCredential", "semantic-routing-policy-authority-credential.v1", "authority_credential", "credential_digest")
for _name in ("policy_author", "development_author", "acceptance_author", "operational_author",
              "annotator_a", "annotator_b", "adjudicator", "implementer"):
    _role(f"{_name}_credential", 0, "authorityCredential", "semantic-routing-policy-authority-credential.v1", "authority_credential", "credential_digest")
for _index in range(12):
    _role(f"exposure_{_index:02d}", 0, "exposureEvidence", "semantic-routing-policy-b0-exposure-evidence.v1", "b0_exposure_evidence", "evidence_digest")
_PRIMARY = (
    ("custody_readiness_subject", 1, "custodyReadinessSubject", "custodyReadinessSubject", "custody_readiness_subject", "subject_digest"),
    ("custody_readiness", 2, "custodyReadinessReceipt", "custodyReadiness", "custody_readiness", "readiness_digest"),
    ("custody_readiness_request", 3, "custodyReadinessVerificationRequest", "custodyReadinessVerificationRequest", "custody_readiness_verification_request", "request_digest"),
    ("binding_receipt", 4, "policyBindingReceipt", "policyBindingReceipt", "policy_binding_receipt", "receipt_digest"),
    ("candidate_contamination", 4, "contaminationManifest", "contaminationManifest", "contamination_manifest", "manifest_digest"),
    ("candidate", 5, "candidate", "candidate", "candidate", "candidate_digest"),
    ("reservation", 6, "processReservation", "processReservation", "process_reservation", "reservation_digest"),
    ("rollback_plan", 6, "rollbackPlan", "rollbackPlan", "rollback_plan", "plan_digest"),
    ("attempt_envelope", 7, "attemptEnvelope", "attemptEnvelope", "attempt_envelope", "envelope_digest"),
    ("execution_contamination_subject", 8, "executionContaminationSubject", "executionContaminationSubject", "execution_contamination_subject", "subject_digest"),
    ("execution_contamination", 9, "executionContaminationAttestation", "executionContaminationAttestation", "execution_contamination", "attestation_digest"),
    ("execution_contamination_request", 10, "executionContaminationVerificationRequest", "executionContaminationVerificationRequest", "execution_contamination_verification_request", "request_digest"),
    ("preexecution_bundle", 11, "preexecutionVerificationBundle", "preexecutionVerificationBundle", "preexecution_verification_bundle", "bundle_digest"),
    ("preregistration", 12, "preregistration", "preregistration", "preregistration", "preregistration_digest"),
    ("activation_subject", 13, "protectedAccessActivationSubject", "protectedAccessActivationSubject", "protected_access_activation_subject", "subject_digest"),
    ("activation", 14, "protectedAccessActivation", "protectedAccessActivation", "protected_access_activation", "activation_digest"),
    ("channel", 15, "evaluatorAuthenticatedChannelCoordinate", "evaluatorAuthenticatedChannelCoordinate", "evaluator_authenticated_channel_coordinate", "channel_coordinate_digest"),
    ("invocation_challenge", 16, "evaluatorInvocationChallenge", "evaluatorInvocationChallenge", "evaluator_invocation_challenge", "challenge_digest"),
    ("start_subject", 17, "evaluatorExecutionStartSubject", "evaluatorExecutionStartSubject", "evaluator_execution_start_subject", "subject_digest"),
    ("start_request", 18, "evaluatorExecutionStartVerificationRequest", "evaluatorExecutionStartVerificationRequest", "evaluator_execution_start_verification_request", "request_digest"),
    ("start_proof", 19, "evaluatorExecutionStartProof", "evaluatorExecutionStartProof", "evaluator_execution_start_proof", "start_proof_digest"),
    ("launch_subject", 20, "evaluatorExecutionLaunchSubject", "evaluatorExecutionLaunchSubject", "evaluator_execution_launch_subject", "subject_digest"),
    ("launch", 21, "evaluatorExecutionLaunchReceipt", "evaluatorExecutionLaunchReceipt", "evaluator_execution_launch_receipt", "launch_receipt_digest"),
    ("handoff_subject", 22, "protectedDescriptorHandoffSubject", "protectedDescriptorHandoffSubject", "protected_descriptor_handoff_subject", "subject_digest"),
    ("handoff", 23, "protectedDescriptorHandoffReceipt", "protectedDescriptorHandoffReceipt", "protected_descriptor_handoff_receipt", "handoff_receipt_digest"),
    ("closure_subject", 25, "protectedAccessClosureSubject", "protectedAccessClosureSubject", "protected_access_closure_subject", "subject_digest"),
    ("closure", 26, "protectedAccessClosure", "protectedAccessClosure", "protected_access_closure", "closure_digest"),
    ("attempt", 27, "executionAttempt", "executionAttempt", "execution_attempt", "attempt_digest"),
    ("verdict_subject", 28, "verdictApprovalSubject", "verdictApprovalSubject", "verdict_approval_subject", "subject_digest"),
    ("verdict", 30, "verdict", "verdict", "verdict", "verdict_digest"),
    ("publication_subject", 31, "publicationApprovalSubject", "publicationApprovalSubject", "publication_approval_subject", "subject_digest"),
    ("publication_event", 33, "publicationEvent", "publicationEvent", "publication_event", "event_digest"),
    ("publication_history", 34, "publicationHistory", "publicationHistory", "publication_history", "history_digest"),
    ("owner_head", 35, "ownerHead", "ownerHead", "owner_head", "head_digest"),
    ("owner_checkpoint", 36, "ownerCheckpoint", "ownerCheckpoint", "owner_checkpoint", "checkpoint_digest"),
)
for role, phase, definition, suffix, domain, field in _PRIMARY:
    _role(role, phase, definition, f"semantic-routing-policy-{re.sub(r'(?<!^)(?=[A-Z])', '-', suffix).lower()}.v1", domain, field)
for role, schema in {
    "custody_readiness": "semantic-routing-policy-custody-readiness.v1",
    "binding_receipt": "semantic-routing-policy-binding-receipt.v1",
    "candidate_contamination": "semantic-routing-policy-contamination-manifest.v1",
    "rollback_plan": "semantic-routing-policy-evaluation-rollback-plan.v1",
    "execution_contamination": "semantic-routing-policy-execution-contamination-attestation.v1",
    "channel": "semantic-routing-policy-evaluator-authenticated-channel-coordinate.v1",
    "launch": "semantic-routing-policy-evaluator-execution-launch-receipt.v1",
    "handoff_subject": "semantic-routing-policy-protected-descriptor-handoff-subject.v1",
    "handoff": "semantic-routing-policy-protected-descriptor-handoff-receipt.v1",
    "attempt": "semantic-routing-policy-execution-attempt.v1",
    "publication_subject": "semantic-routing-policy-publication-approval-subject.v1",
    "publication_event": "semantic-routing-policy-publication-event.v1",
    "publication_history": "semantic-routing-policy-publication-history.v1",
    "owner_head": "semantic-routing-policy-owner-head.v1",
    "owner_checkpoint": "semantic-routing-policy-owner-checkpoint.v1",
}.items():
    spec = _SPECS[role]
    _SPECS[role] = RoleSpec(spec.phase, spec.definition, schema, spec.digest_domain, spec.self_digest_field)
_SPECS["raw_execution_receipt"] = RoleSpec(24, None, None, None, None)
_APPROVALS = {
    "readiness": (1, "custodian_credential"),
    "contamination_custodian": (8, "custodian_credential"),
    "contamination_reviewer": (8, "reviewer_credential"),
    "activation": (13, "custodian_credential"),
    "start": (18, "evaluator_credential"),
    "launch": (20, "gateway_credential"),
    "handoff": (22, "gateway_credential"),
    "closure": (25, "custodian_credential"),
    "verdict_custodian": (29, "custodian_credential"),
    "verdict_reviewer": (29, "reviewer_credential"),
    "publication": (32, "semantic_owner_credential"),
}
for name, (phase, _credential) in _APPROVALS.items():
    _role(f"{name}_approval_body", phase, "approvalAttestationBody", "semantic-routing-policy-approval-attestation-body.v1", "approval_attestation_body", "body_digest")
    _role(f"{name}_approval", phase, "approvalArtifact", "semantic-routing-policy-approval-artifact.v1", "approval_artifact", "artifact_digest")
    _edge(f"{name}_approval", "attestation_body.body_digest", f"{name}_approval_body", "attestation_body")
    _edge(f"{name}_approval", "issuer.authority_credential_digest", _credential)
_APPROVAL_SUBJECTS = {"readiness": "custody_readiness_subject", "contamination_custodian": "execution_contamination_subject", "contamination_reviewer": "execution_contamination_subject", "activation": "activation_subject", "start": "start_subject", "launch": "launch_subject", "handoff": "handoff_subject", "closure": "closure_subject", "verdict_custodian": "verdict_subject", "verdict_reviewer": "verdict_subject", "publication": "publication_subject"}
for _name, _subject in _APPROVAL_SUBJECTS.items():
    _edge(f"{_name}_approval", "subject_digest", _subject)
_PARTICIPANT_CREDENTIALS = ("semantic_owner_credential", "policy_author_credential",
    "development_author_credential", "acceptance_author_credential", "operational_author_credential",
    "annotator_a_credential", "annotator_b_credential", "adjudicator_credential",
    "custodian_credential", "reviewer_credential", "evaluator_credential", "implementer_credential")
for _index, _credential in enumerate(_PARTICIPANT_CREDENTIALS):
    _edge("preregistration", f"participants.{_index}.authority.authority_credential_digest", _credential)
    _edge("preregistration", f"participants.{_index}.b0_exposure_evidence_digest", f"exposure_{_index:02d}", f"participants.{_index}.b0_exposure_evidence")
for args in (
    ("role_separation", "access_history_digest", "base_access_history"),
    ("binding_receipt", "policy_concept_ids_digest", "policy_concept_ids"),
    ("binding_receipt", "joint_route_sets_digest", "joint_route_sets"),
    ("semantic_binding", "inventory_digest", "inventory"),
    ("semantic_binding", "binding_receipt_digest", "binding_receipt", "binding_receipt"),
    ("semantic_binding", "binding_receipt.policy_concept_ids_digest", "policy_concept_ids", "policy_concept_ids"),
    ("semantic_binding", "binding_receipt.joint_route_sets_digest", "joint_route_sets", "joint_route_ontology_id_sets"),
    ("custody_readiness_subject", "custody_policy_digest", "custody_policy"),
    ("custody_readiness_subject", "role_separation_digest", "role_separation"),
    ("custody_readiness_subject", "access_history_digest", "base_access_history"),
    ("custody_readiness_subject", "concept_inventory_digest", "inventory", "concept_inventory"),
    ("custody_readiness", "subject.subject_digest", "custody_readiness_subject", "subject"),
    ("custody_readiness", "base_access_history_digest", "base_access_history", "base_access_history"),
    ("custody_readiness", "custodian_credential.credential_digest", "custodian_credential", "custodian_credential"),
    ("custody_readiness", "custodian_approval.artifact_digest", "readiness_approval", "custodian_approval"),
    ("custody_readiness_request", "readiness_digest", "custody_readiness"),
    ("custody_readiness_request", "subject_digest", "custody_readiness_subject"),
    ("custody_readiness_request", "expected_base_access_history_digest", "base_access_history", "expected_base_access_history"),
    ("custody_readiness_request", "expected_concept_inventory_digest", "inventory", "expected_concept_inventory"),
    ("custody_readiness_request", "expected_custodian_credential.credential_digest", "custodian_credential", "expected_custodian_credential"),
    ("custody_readiness_request", "expected_custodian_approval_digest", "readiness_approval"),
    ("binding_receipt", "inventory_digest", "inventory"),
    ("candidate", "ontology_inventory_digest", "inventory", "ontology_inventory"),
    ("candidate", "policy_semantic_binding.binding_digest", "semantic_binding", "policy_semantic_binding"),
    ("candidate", "contamination_manifest_digest", "candidate_contamination"),
    ("attempt_envelope", "candidate_digest", "candidate"),
    ("attempt_envelope", "reservation_digest", "reservation", "process_reservation"),
    ("attempt_envelope", "rollback_plan_digest", "rollback_plan", "rollback_plan"),
    ("execution_contamination_subject", "candidate_digest", "candidate"),
    ("execution_contamination_subject", "candidate_contamination_manifest_digest", "candidate_contamination"),
    ("execution_contamination_subject", "attempt_envelope_digest", "attempt_envelope"),
    ("execution_contamination_subject", "source_digest", "attempt_envelope"),
    ("execution_contamination", "subject.subject_digest", "execution_contamination_subject", "subject"),
    ("execution_contamination", "custodian_credential.credential_digest", "custodian_credential", "custodian_credential"),
    ("execution_contamination", "independent_review_credential.credential_digest", "reviewer_credential", "independent_review_credential"),
    ("execution_contamination", "custodian_approval.artifact_digest", "contamination_custodian_approval", "custodian_approval"),
    ("execution_contamination", "independent_review_approval.artifact_digest", "contamination_reviewer_approval", "independent_review_approval"),
    ("execution_contamination_request", "attestation_digest", "execution_contamination"),
    ("execution_contamination_request", "subject_digest", "execution_contamination_subject"),
    ("execution_contamination_request", "expected_custodian_credential.credential_digest", "custodian_credential", "expected_custodian_credential"),
    ("execution_contamination_request", "expected_independent_review_credential.credential_digest", "reviewer_credential", "expected_independent_review_credential"),
    ("execution_contamination_request", "expected_custodian_approval_digest", "contamination_custodian_approval"),
    ("execution_contamination_request", "expected_independent_review_approval_digest", "contamination_reviewer_approval"),
    ("preexecution_bundle", "custody_readiness_verification_request_digest", "custody_readiness_request", "custody_readiness_verification_request"),
    ("preexecution_bundle", "execution_contamination_verification_request_digest", "execution_contamination_request", "execution_contamination_verification_request"),
    ("preregistration", "custody_policy_digest", "custody_policy"),
    ("preregistration", "concept_inventory_digest", "inventory"),
    ("preregistration", "contamination_manifest_digest", "candidate_contamination"),
    ("preregistration", "role_separation_digest", "role_separation", "role_separation_receipt"),
    ("preregistration", "access_history_digest", "base_access_history", "access_history"),
    ("preregistration", "candidate_digest", "candidate"),
    ("preregistration", "attempt_envelope_digest", "attempt_envelope", "attempt_envelope"),
    ("preregistration", "custody_readiness_digest", "custody_readiness", "custody_readiness_receipt"),
    ("preregistration", "execution_contamination_digest", "execution_contamination", "execution_contamination_attestation"),
    ("preregistration", "custody_readiness_verification_request_digest", "custody_readiness_request"),
    ("preregistration", "execution_contamination_verification_request_digest", "execution_contamination_request"),
    ("preregistration", "preexecution_verification_bundle_digest", "preexecution_bundle", "preexecution_verification_bundle"),
    ("activation_subject", "preregistration_digest", "preregistration"),
    ("activation_subject", "base_access_history_digest", "base_access_history"),
    ("activation_subject", "activated_access_history_digest", "activated_access_history"),
    ("activation_subject", "reservation_digest", "reservation"),
    ("activation", "subject.subject_digest", "activation_subject", "subject"),
    ("activation", "base_access_history_digest", "base_access_history", "base_access_history"),
    ("activation", "activated_access_history_digest", "activated_access_history", "activated_access_history"),
    ("activation", "custodian_credential.credential_digest", "custodian_credential", "custodian_credential"),
    ("activation", "custodian_approval.artifact_digest", "activation_approval", "custodian_approval"),
): _edge(*args)
for args in (
    ("invocation_challenge", "preregistration_digest", "preregistration"), ("invocation_challenge", "attempt_envelope_digest", "attempt_envelope"),
    ("invocation_challenge", "reservation_digest", "reservation"), ("invocation_challenge", "protected_access_activation_digest", "activation"),
    ("invocation_challenge", "authenticated_channel_coordinate_digest", "channel", "authenticated_channel_coordinate"),
    ("start_subject", "preregistration_digest", "preregistration"), ("start_subject", "attempt_envelope_digest", "attempt_envelope"),
    ("start_subject", "reservation_digest", "reservation"),
    ("start_subject", "invocation_challenge_digest", "invocation_challenge"), ("start_subject", "authenticated_channel_coordinate_digest", "channel", "authenticated_channel_coordinate"),
    ("start_subject", "protected_access_activation_digest", "activation"),
    ("start_request", "invocation_challenge_digest", "invocation_challenge", "invocation_challenge"),
    ("start_request", "expected_authenticated_channel_coordinate_digest", "channel", "expected_authenticated_channel_coordinate"),
    ("start_request", "expected_start_subject_digest", "start_subject"),
    ("start_request", "expected_evaluator_credential.credential_digest", "evaluator_credential", "expected_evaluator_credential"),
    ("start_request", "expected_launch_gateway_credential.credential_digest", "gateway_credential", "expected_launch_gateway_credential"),
    ("start_proof", "challenge_digest", "invocation_challenge", "challenge"), ("start_proof", "subject_digest", "start_subject", "subject"),
    ("start_proof", "evaluator_credential.credential_digest", "evaluator_credential", "evaluator_credential"),
    ("start_proof", "evaluator_approval.artifact_digest", "start_approval", "evaluator_approval"),
    ("launch_subject", "evaluator_execution_start_proof_digest", "start_proof"), ("launch_subject", "evaluator_start_verification_request_digest", "start_request"),
    ("launch_subject", "authenticated_channel_coordinate_digest", "channel", "authenticated_channel_coordinate"), ("launch_subject", "reservation_digest", "reservation"),
    ("launch", "subject_digest", "launch_subject", "subject"), ("launch", "launch_gateway_credential.credential_digest", "gateway_credential", "launch_gateway_credential"),
    ("launch", "launch_gateway_approval.artifact_digest", "launch_approval", "launch_gateway_approval"),
    ("handoff_subject", "evaluator_execution_start_proof_digest", "start_proof"), ("handoff_subject", "evaluator_execution_launch_receipt_digest", "launch"),
    ("handoff_subject", "evaluator_start_verification_request_digest", "start_request"), ("handoff_subject", "authenticated_channel_coordinate_digest", "channel", "authenticated_channel_coordinate"),
    ("handoff_subject", "reservation_digest", "reservation"),
    ("handoff", "subject_digest", "handoff_subject", "subject"), ("handoff", "launch_gateway_credential.credential_digest", "gateway_credential", "launch_gateway_credential"),
    ("handoff", "launch_gateway_approval.artifact_digest", "handoff_approval", "launch_gateway_approval"),
    ("closure_subject", "preregistration_digest", "preregistration"), ("closure_subject", "protected_access_activation_digest", "activation"),
    ("closure_subject", "activated_access_history_digest", "activated_access_history"), ("closure_subject", "terminal_access_history_digest", "terminal_access_history"),
    ("closure_subject", "reservation_digest", "reservation"),
    ("closure", "subject_digest", "closure_subject", "subject"), ("closure", "activated_access_history_digest", "activated_access_history", "activated_access_history"),
    ("closure", "terminal_access_history_digest", "terminal_access_history", "terminal_access_history"),
    ("closure", "custodian_credential.credential_digest", "custodian_credential", "custodian_credential"),
    ("closure", "custodian_approval.artifact_digest", "closure_approval", "custodian_approval"),
): _edge(*args)
_NULLABLE = (
    ("evaluator_execution_start_proof_digest", "start_proof", "evaluator_execution_start_proof"),
    ("evaluator_execution_start_verification_request_digest", "start_request", "evaluator_execution_start_verification_request"),
    ("evaluator_execution_launch_receipt_digest", "launch", "evaluator_execution_launch_receipt"),
    ("protected_descriptor_handoff_receipt_digest", "handoff", "protected_descriptor_handoff_receipt"),
    ("execution_receipt_digest", "raw_execution_receipt", None),
)
for source in ("attempt", "verdict"):
    for field, target, obj in _NULLABLE:
        _edge(source, field, target, obj, True)
for source in ("closure_subject", "verdict_subject"):
    for field, target, _obj in _NULLABLE:
        if source != "closure_subject" or field != "evaluator_execution_start_verification_request_digest":
            _edge(source, field, target, None, True)
for args in (
    ("attempt", "candidate_digest", "candidate"), ("attempt", "preregistration_digest", "preregistration"),
    ("attempt", "attempt_envelope_digest", "attempt_envelope"), ("attempt", "protected_access_activation_digest", "activation", "protected_access_activation"),
    ("attempt", "protected_access_closure_digest", "closure", "protected_access_closure"),
    ("verdict_subject", "candidate_digest", "candidate"), ("verdict_subject", "preregistration_digest", "preregistration"),
    ("verdict_subject", "contamination_manifest_digest", "candidate_contamination"), ("verdict_subject", "custody_policy_digest", "custody_policy"),
    ("verdict_subject", "attempt_envelope_digest", "attempt_envelope"), ("verdict_subject", "execution_contamination_digest", "execution_contamination"),
    ("verdict_subject", "protected_access_activation_digest", "activation"), ("verdict_subject", "execution_attempt_digest", "attempt"),
    ("verdict_subject", "protected_access_closure_digest", "closure"),
    ("verdict", "candidate_digest", "candidate"), ("verdict", "preregistration_digest", "preregistration", "preregistration"),
    ("verdict", "contamination_manifest_digest", "candidate_contamination", "contamination_manifest"),
    ("verdict", "custody_policy_digest", "custody_policy", "custody_policy"), ("verdict", "attempt_envelope_digest", "attempt_envelope", "attempt_envelope"),
    ("verdict", "execution_contamination_digest", "execution_contamination", "execution_contamination_attestation"),
    ("verdict", "protected_access_activation_digest", "activation", "protected_access_activation"),
    ("verdict", "execution_attempt_digest", "attempt", "execution_attempt"), ("verdict", "protected_access_closure_digest", "closure", "protected_access_closure"),
    ("verdict", "verdict_approval_subject_digest", "verdict_subject", "verdict_approval_subject"),
    ("verdict", "custodian_approval.artifact_digest", "verdict_custodian_approval", "custodian_approval"),
    ("verdict", "independent_review_approval.artifact_digest", "verdict_reviewer_approval", "independent_review_approval"),
    ("publication_subject", "candidate_digest", "candidate"), ("publication_subject", "verdict_digest", "verdict"),
    ("publication_event", "candidate_digest", "candidate"), ("publication_event", "verdict_digest", "verdict"),
    ("publication_event", "publication_approval_subject_digest", "publication_subject", "publication_approval_subject"),
    ("publication_event", "owner_approval.artifact_digest", "publication_approval", "owner_approval"),
    ("owner_head", "terminal_event_digest", "publication_event"), ("owner_head", "publication_history_digest", "publication_history"),
    ("owner_checkpoint", "head_digest", "owner_head"), ("owner_checkpoint", "history_digest", "publication_history"),
): _edge(*args)
_edge("publication_history", "events.-1.event_digest", "publication_event", "events.-1")
@dataclass(frozen=True)
class PrimitiveJoin: left_role: str; left_path: str; right_role: str; right_path: str
_PRIMITIVE_JOINS = tuple(PrimitiveJoin(*item) for item in (
    ("invocation_challenge","process_start_id","start_subject","process_start_id"), ("start_subject","process_start_id","launch_subject","process_start_id"),
    ("launch_subject","process_start_id","handoff_subject","process_start_id"), ("launch_subject","process_start_id","closure_subject","process_start_id"),
    ("reservation","executor_authority","activation_subject","executor_authority"), ("reservation","executor_authority","start_subject","evaluator_authority"),
    ("reservation","executor_authority","channel","evaluator_authority"), ("reservation","executor_authority","start_request","expected_evaluator_authority"),
    ("reservation","executor_authority","launch_subject","evaluator_authority"), ("reservation","executor_authority","handoff_subject","evaluator_authority"),
    ("reservation","executor_authority","closure_subject","executor_authority"), ("channel","launch_gateway_authority","start_request","expected_launch_gateway_authority"),
    ("channel","launch_gateway_authority","launch_subject","launch_gateway_authority"), ("channel","launch_gateway_authority","handoff_subject","launch_gateway_authority"),
    ("preregistration","custodian_authority","activation_subject","custodian_authority"), ("preregistration","custodian_authority","closure_subject","custodian_authority"),
    ("attempt_envelope","acceptance_dataset_seal_digest","activation_subject","acceptance_dataset_seal_digest"), ("attempt_envelope","operational_dataset_seal_digest","activation_subject","operational_dataset_seal_digest"),
    ("attempt_envelope","acceptance_dataset_seal_digest","launch_subject","acceptance_dataset_seal_digest"), ("attempt_envelope","operational_dataset_seal_digest","launch_subject","operational_dataset_seal_digest"),
    ("attempt_envelope","acceptance_dataset_seal_digest","handoff_subject","acceptance_dataset_seal_digest"), ("attempt_envelope","operational_dataset_seal_digest","handoff_subject","operational_dataset_seal_digest"),
    ("activation_subject","expires_at","closure_subject","activation_expires_at"),
))
_PRIMITIVE_JOINS += tuple(PrimitiveJoin(f"{name}_approval", field, f"{name}_approval_body", field) for name in _APPROVALS for field in ("subject_digest", "purpose"))
_PRIMITIVE_JOINS += tuple(PrimitiveJoin(*item) for item in (
    ("readiness_approval","issuer","custody_readiness_subject","custodian_authority"), ("activation_approval","issuer","activation_subject","custodian_authority"),
    ("start_approval","issuer","start_subject","evaluator_authority"), ("launch_approval","issuer","launch_subject","launch_gateway_authority"),
    ("handoff_approval","issuer","handoff_subject","launch_gateway_authority"), ("closure_approval","issuer","closure_subject","custodian_authority"),
    ("verdict_custodian_approval","issuer","verdict_subject","custodian_authority"), ("verdict_reviewer_approval","issuer","verdict_subject","independent_review_authority"),
    ("contamination_custodian_approval","issuer","execution_contamination_subject","custodian_authority"), ("contamination_reviewer_approval","issuer","execution_contamination_subject","independent_review_authority"),
    ("publication_approval","issuer","publication_subject","semantic_owner_authority"),
    ("preregistration","custodian_authority","preregistration","participants.8.authority"), ("preregistration","independent_review_authority","preregistration","participants.9.authority"),
    ("custody_readiness_request","expected_custodian_authority","custody_readiness_subject","custodian_authority"), ("custody_readiness_request","expected_custodian_authority","preregistration","custodian_authority"), ("custody_readiness_request","expected_custodian_credential","custody_readiness","custodian_credential"), ("custody_readiness_request","expected_custodian_approval_digest","custody_readiness","custodian_approval.artifact_digest"), ("custody_readiness_request","expected_trust_root_digest","custody_readiness","custodian_credential.trust_root_digest"), ("custody_readiness_request","expected_public_key_digest","custody_readiness","custodian_credential.public_key_digest"), ("execution_contamination_request","expected_custodian_authority","execution_contamination_subject","custodian_authority"), ("execution_contamination_request","expected_custodian_authority","preregistration","custodian_authority"), ("execution_contamination_request","expected_independent_review_authority","execution_contamination_subject","independent_review_authority"), ("execution_contamination_request","expected_independent_review_authority","preregistration","independent_review_authority"), ("execution_contamination_request","expected_custodian_credential","execution_contamination","custodian_credential"), ("execution_contamination_request","expected_independent_review_credential","execution_contamination","independent_review_credential"), ("execution_contamination_request","expected_custodian_approval_digest","execution_contamination","custodian_approval.artifact_digest"), ("execution_contamination_request","expected_independent_review_approval_digest","execution_contamination","independent_review_approval.artifact_digest"), ("execution_contamination_request","expected_custodian_trust_root_digest","execution_contamination","custodian_credential.trust_root_digest"), ("execution_contamination_request","expected_custodian_public_key_digest","execution_contamination","custodian_credential.public_key_digest"), ("execution_contamination_request","expected_independent_review_trust_root_digest","execution_contamination","independent_review_credential.trust_root_digest"), ("execution_contamination_request","expected_independent_review_public_key_digest","execution_contamination","independent_review_credential.public_key_digest"),
))
_CONSTANTS = {**{f"{name}_approval": {"purpose": purpose, "revoked": False} for name, purpose in {
    "readiness":"custody_readiness", "contamination_custodian":"execution_contamination_custodian", "contamination_reviewer":"execution_contamination_independent_review", "activation":"protected_access_activation", "start":"evaluator_execution_start", "launch":"evaluator_execution_launch", "handoff":"protected_descriptor_handoff", "closure":"protected_access_closure", "verdict_custodian":"custody", "verdict_reviewer":"independent_review", "publication":"semantic_publication"}.items()},
    "launch_subject":{"reservation_consumptions_before":0,"reservation_consumptions_after":1,"protected_descriptors_opened":False}, "handoff_subject":{"descriptor_handoffs_before":0,"descriptor_handoffs_after":1,"direct_os_descriptor_transfer":False}}
_order = {role: spec.phase * 100 for role, spec in _SPECS.items()}
for _ in range(len(_SPECS)):
    changed = False
    for edge in _EDGES:
        required = _order[edge.target] + 1
        if _order[edge.source] < required:
            _order[edge.source] = required
            changed = True
    if not changed:
        break
else:
    raise RuntimeError("adopted graph topology is cyclic")
for _name, _spec in tuple(_SPECS.items()):
    _SPECS[_name] = RoleSpec(_order[_name], _spec.definition, _spec.schema, _spec.digest_domain, _spec.self_digest_field)
ROLE_SPECS: Mapping[str, RoleSpec] = MappingProxyType(_SPECS)
def normative_edges() -> tuple[GraphEdge, ...]: return tuple(_EDGES)
def _get(value: Any, path: str) -> Any:
    current = value
    for token in path.split("."):
        if type(current) is list:
            index = len(current) - 1 if token == "-1" else int(token)
            if not -len(current) <= index < len(current):
                return _MISSING
            current = current[index]
        elif type(current) is dict and token in current:
            current = current[token]
        else:
            return _MISSING
    return current
_MISSING = object()
def _digest(role: str, value: Any) -> str:
    spec = ROLE_SPECS[role]
    if spec.definition is None:
        if spec.digest_domain is None:
            if type(value) is bytes: return "sha256:" + hashlib.sha256(value).hexdigest()
            raise AdoptedGraphError("schema_invalid", role)
        if type(value) is not list:
            raise AdoptedGraphError("schema_invalid", role)
        return domain_digest(spec.digest_domain, value)
    if type(value) is not dict or (spec.schema is not None and value.get("schema") != spec.schema) or validate_definition(value, spec.definition):
        raise AdoptedGraphError("schema_invalid", role)
    try:
        result = object_digest(spec.digest_domain, value, spec.self_digest_field)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise AdoptedGraphError("schema_invalid", role) from None
    if value.get(spec.self_digest_field) != result:
        raise AdoptedGraphError("digest_mismatch", role)
    _embedded_self_digests(value, role)
    return result
_SELF = {spec.schema: (spec.digest_domain, spec.self_digest_field) for spec in _SPECS.values() if spec.schema and spec.digest_domain}
def _embedded_self_digests(value: Any, role: str) -> None:
    if type(value) is list:
        for child in value:
            _embedded_self_digests(child, role)
        return
    if type(value) is not dict:
        return
    schema = value.get("schema")
    config = _SELF.get(schema)
    if config and config[1] in value:
        try:
            if object_digest(config[0], value, config[1]) != value[config[1]]:
                raise AdoptedGraphError("digest_mismatch", role)
        except (TypeError, ValueError):
            raise AdoptedGraphError("schema_invalid", role) from None
    if schema == "semantic-routing-policy-access-history.v1":
        prior = None
        for event in value.get("events", []):
            try:
                actual = object_digest("access_history_event", event, "event_digest")
            except (TypeError, ValueError):
                raise AdoptedGraphError("schema_invalid", role) from None
            if event.get("event_digest") != actual or event.get("previous_event_digest") != prior:
                raise AdoptedGraphError("digest_mismatch", role)
            prior = actual
    if schema == "semantic-routing-policy-preregistration.v1":
        participants, receipt = value.get("participants"), value.get("role_separation_receipt")
        if type(participants) is not list or type(receipt) is not dict or receipt.get("participants_digest") != "sha256:" + hashlib.sha256(jcs_bytes(participants)).hexdigest(): raise AdoptedGraphError("digest_mismatch", role)
    if schema == "semantic-routing-policy-publication-history.v1":
        prior = None
        for event in value.get("events", []):
            if event.get("previous_event_digest") != prior:
                raise AdoptedGraphError("digest_mismatch", role)
            prior = event.get("event_digest")
    for child in value.values():
        _embedded_self_digests(child, role)
def _edge_failure(edge: GraphEdge) -> str | None:
    if edge.source == edge.target: return "self_edge"
    source, target = ROLE_SPECS.get(edge.source), ROLE_SPECS.get(edge.target)
    if source is None or target is None: return "unknown_role"
    if target.phase > source.phase: return "phase_forward_edge"
    if target.phase == source.phase: return "back_edge"
    return None
_BUNDLE_PATHS = {'attempt': 'attempt', 'verdict': 'verdict', 'preregistration': 'verdict.preregistration', 'custody_policy': 'verdict.custody_policy', 'candidate_contamination': 'verdict.contamination_manifest', 'attempt_envelope': 'verdict.attempt_envelope', 'reservation': 'verdict.attempt_envelope.process_reservation', 'rollback_plan': 'verdict.attempt_envelope.rollback_plan', 'base_access_history': 'verdict.preregistration.access_history', 'role_separation': 'verdict.preregistration.role_separation_receipt', 'custody_readiness': 'verdict.preregistration.custody_readiness_receipt', 'custody_readiness_subject': 'verdict.preregistration.custody_readiness_receipt.subject', 'readiness_approval': 'verdict.preregistration.custody_readiness_receipt.custodian_approval', 'execution_contamination': 'verdict.execution_contamination_attestation', 'execution_contamination_subject': 'verdict.execution_contamination_attestation.subject', 'contamination_custodian_approval': 'verdict.execution_contamination_attestation.custodian_approval', 'contamination_reviewer_approval': 'verdict.execution_contamination_attestation.independent_review_approval', 'preexecution_bundle': 'verdict.preregistration.preexecution_verification_bundle', 'custody_readiness_request': 'verdict.preregistration.preexecution_verification_bundle.custody_readiness_verification_request', 'execution_contamination_request': 'verdict.preregistration.preexecution_verification_bundle.execution_contamination_verification_request', 'activation': 'verdict.protected_access_activation', 'activation_subject': 'verdict.protected_access_activation.subject', 'activated_access_history': 'verdict.protected_access_activation.activated_access_history', 'activation_approval': 'verdict.protected_access_activation.custodian_approval', 'start_proof': 'verdict.evaluator_execution_start_proof', 'start_request': 'verdict.evaluator_execution_start_verification_request', 'invocation_challenge': 'verdict.evaluator_execution_start_proof.challenge', 'start_subject': 'verdict.evaluator_execution_start_proof.subject', 'channel': 'verdict.evaluator_execution_start_proof.challenge.authenticated_channel_coordinate', 'start_approval': 'verdict.evaluator_execution_start_proof.evaluator_approval', 'launch': 'verdict.evaluator_execution_launch_receipt', 'launch_subject': 'verdict.evaluator_execution_launch_receipt.subject', 'launch_approval': 'verdict.evaluator_execution_launch_receipt.launch_gateway_approval', 'handoff': 'verdict.protected_descriptor_handoff_receipt', 'handoff_subject': 'verdict.protected_descriptor_handoff_receipt.subject', 'handoff_approval': 'verdict.protected_descriptor_handoff_receipt.launch_gateway_approval', 'closure': 'verdict.protected_access_closure', 'closure_subject': 'verdict.protected_access_closure.subject', 'closure_approval': 'verdict.protected_access_closure.custodian_approval', 'terminal_access_history': 'verdict.protected_access_closure.terminal_access_history', 'verdict_subject': 'verdict.verdict_approval_subject', 'verdict_custodian_approval': 'verdict.custodian_approval', 'verdict_reviewer_approval': 'verdict.independent_review_approval'}
_CANDIDATE_PATHS = {"candidate":"", "inventory":"ontology_inventory", "semantic_binding":"policy_semantic_binding", "binding_receipt":"policy_semantic_binding.binding_receipt", "policy_concept_ids":"policy_semantic_binding.policy_concept_ids", "joint_route_sets":"policy_semantic_binding.joint_route_ontology_id_sets"}
_CREDENTIAL_COPIES = {
 "custodian_credential": ("verdict.preregistration.custody_readiness_receipt.custodian_credential", "verdict.execution_contamination_attestation.custodian_credential", "verdict.protected_access_activation.custodian_credential", "verdict.protected_access_closure.custodian_credential"),
 "reviewer_credential": ("verdict.execution_contamination_attestation.independent_review_credential",),
 "evaluator_credential": ("verdict.evaluator_execution_start_proof.evaluator_credential", "verdict.evaluator_execution_start_verification_request.expected_evaluator_credential"),
 "gateway_credential": ("verdict.evaluator_execution_start_verification_request.expected_launch_gateway_credential", "verdict.evaluator_execution_launch_receipt.launch_gateway_credential", "verdict.protected_descriptor_handoff_receipt.launch_gateway_credential")}
def _active_execution_roles(objects: Mapping[str, Any]) -> set[str]:
    active, pending, by_source = set(), ["verdict"], {}
    for edge in _EDGES: by_source.setdefault(edge.source, []).append(edge)
    while pending:
        role = pending.pop()
        if role in active: continue
        if role not in objects: raise AdoptedGraphError("missing_preimage", role)
        active.add(role)
        for edge in by_source.get(role, ()):
            if not (edge.nullable and _get(objects[role], edge.digest_field) is None): pending.append(edge.target)
    return active
def extract_execution_graph(bundle: Mapping[str, Any], support: ExecutionGraphSupport) -> dict[str, Any]:
    if type(bundle) is not dict or type(support) is not ExecutionGraphSupport or type(support.candidate_support) is not CandidateSupport or type(support.participant_credentials) is not tuple or len(support.participant_credentials) != 12: raise AdoptedGraphError("missing_preimage")
    verified = support.candidate_support
    try: candidate = strict_json_loads(verified.candidate_bytes)
    except (TypeError, ValueError): raise AdoptedGraphError("schema_invalid", "candidate") from None
    if type(candidate) is not dict or jcs_bytes(candidate) != verified.candidate_bytes: raise AdoptedGraphError("schema_invalid", "candidate")
    if candidate.get("candidate_digest") != verified.candidate_digest: raise AdoptedGraphError("digest_mismatch", "candidate")
    p3 = (("custody_readiness_subject", support.custody_readiness_subject), ("custody_readiness", support.custody_readiness_receipt), ("custody_readiness_request", support.custody_readiness_request))
    if any(type(value) is not dict for _role_name, value in p3): raise AdoptedGraphError("missing_preimage")
    result: dict[str, Any] = {}
    for role, path in _BUNDLE_PATHS.items():
        value = _get(bundle, path)
        if value is not _MISSING and value is not None: result[role] = value
    if any(result.get(role) != value for role, value in p3): raise AdoptedGraphError("nested_mismatch", "custody_readiness")
    result.update(p3)
    for role, path in _CANDIDATE_PATHS.items():
        value = candidate if not path else _get(candidate, path)
        if value is _MISSING or value is None: raise AdoptedGraphError("missing_preimage", role)
        result[role] = value
    participants = _get(result.get("preregistration"), "participants")
    if type(participants) is not list or len(participants) != 12: raise AdoptedGraphError("missing_preimage", "preregistration")
    for index, (role, credential) in enumerate(zip(_PARTICIPANT_CREDENTIALS, support.participant_credentials)):
        if type(credential) is not dict: raise AdoptedGraphError("missing_preimage", role)
        evidence = _get(participants[index], "b0_exposure_evidence")
        if evidence is _MISSING: raise AdoptedGraphError("missing_preimage", f"exposure_{index:02d}")
        result[role], result[f"exposure_{index:02d}"] = credential, evidence
    for role, paths in _CREDENTIAL_COPIES.items():
        present = [value for path in paths if (value := _get(bundle, path)) is not _MISSING and value is not None]
        if role == "gateway_credential" and present: result[role] = present[0]
        if any(value != result[role] for value in present): raise AdoptedGraphError("nested_mismatch", role)
    for name in _APPROVALS:
        role = f"{name}_approval"
        if role not in result: continue
        body = _get(result[role], "attestation_body")
        if body is _MISSING: raise AdoptedGraphError("missing_preimage", role)
        result[f"{name}_approval_body"] = body
    encoded = bundle.get("execution_receipt_base64")
    if encoded is not None:
        try:
            import base64
            result["raw_execution_receipt"] = base64.b64decode(encoded, validate=True)
        except (TypeError, ValueError): raise AdoptedGraphError("invalid_input") from None
    active = _active_execution_roles(result)
    return {role: result[role] for role in active}
def verify_execution_graph(bundle: Mapping[str, Any], support: ExecutionGraphSupport) -> GraphConsistency:
    return verify_graph(extract_execution_graph(bundle, support))
def verify_graph(objects: Mapping[str, Any], *, edges: Iterable[GraphEdge] | None = None) -> GraphConsistency:
    if not isinstance(objects, Mapping) or not objects or any(type(role) is not str for role in objects): raise AdoptedGraphError("invalid_input")
    supplied = dict(objects)
    if set(supplied) - set(ROLE_SPECS):
        raise AdoptedGraphError("unknown_role")
    expected = {edge for edge in _EDGES if edge.source in supplied}
    selected = expected if edges is None else set(edges)
    if any(type(edge) is not GraphEdge for edge in selected):
        raise AdoptedGraphError("invalid_input")
    for edge in selected:
        failure = _edge_failure(edge)
        if failure:
            raise AdoptedGraphError(failure, edge.source)
    if selected != expected:
        raise AdoptedGraphError("topology_invalid")
    computed = {role: _digest(role, value) for role, value in supplied.items()}
    for edge in expected:
        digest = _get(supplied[edge.source], edge.digest_field)
        nested = _get(supplied[edge.source], edge.object_field) if edge.object_field else _MISSING
        if edge.nullable and digest is None:
            if edge.object_field and nested is not None:
                raise AdoptedGraphError("nested_mismatch", edge.source)
            continue
        if digest is _MISSING:
            raise AdoptedGraphError("schema_invalid", edge.source)
        if edge.target not in supplied:
            kind = "opaque_caller_request" if edge.target.endswith("_request") else "missing_preimage"
            raise AdoptedGraphError(kind, edge.source)
        if digest != computed[edge.target]:
            raise AdoptedGraphError("digest_mismatch", edge.source)
        if edge.object_field and nested != supplied[edge.target]:
            raise AdoptedGraphError("nested_mismatch", edge.source)
    for role, fields in _CONSTANTS.items():
        if role in supplied and any(_get(supplied[role], path) != expected for path, expected in fields.items()):
            raise AdoptedGraphError("nested_mismatch", role)
    for join in _PRIMITIVE_JOINS:
        if join.left_role in supplied and join.right_role in supplied and _get(supplied[join.left_role], join.left_path) != _get(supplied[join.right_role], join.right_path):
            raise AdoptedGraphError("nested_mismatch", join.left_role)
    ordered = tuple(sorted(supplied, key=lambda role: (ROLE_SPECS[role].phase, role)))
    return GraphConsistency(True, False, ordered)
