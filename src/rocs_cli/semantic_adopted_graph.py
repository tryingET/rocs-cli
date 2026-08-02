"""Closed, offline dependency-graph checks for Decision 103 adopted policy v1.

This module proves only that explicitly supplied protocol preimages are schema,
digest, and dependency consistent.  It does not acquire facts or establish that
an issuer, owner, custodian, or caller is authoritative.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from rocs_cli.semantic_adopted_digests import object_digest
from rocs_cli.semantic_adopted_protocol import validate_protocol


ISSUE_KINDS = frozenset({
    "invalid_input", "unknown_role", "missing_preimage", "schema_invalid",
    "self_edge", "back_edge", "phase_forward_edge", "digest_mismatch",
    "opaque_caller_request", "topology_invalid",
})


class AdoptedGraphError(ValueError):
    """A closed, non-secret graph failure."""

    def __init__(self, kind: str, role: str | None = None):
        if kind not in ISSUE_KINDS:
            kind = "topology_invalid"
        self.kind = kind
        self.role = role if type(role) is str and role in ROLE_SPECS else None
        super().__init__(kind if self.role is None else f"{kind}:{self.role}")


@dataclass(frozen=True)
class GraphEdge:
    """A normative dependency: ``source`` carries ``target``'s digest."""

    source: str
    digest_field: str
    target: str


@dataclass(frozen=True)
class RoleSpec:
    phase: int
    schema: str
    digest_domain: str
    self_digest_field: str
    dependencies: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class GraphConsistency:
    consistency_verified: bool
    authority_verified: bool
    roles_verified: tuple[str, ...]


# Phase numbers preserve the accepted Section 3.1 order.  Multiple access
# histories are distinct preimages despite sharing a protocol schema/domain.
_SPECS: dict[str, RoleSpec] = {
    "inventory": RoleSpec(0, "semantic-routing-policy-ontology-inventory.v1", "ontology_inventory", "inventory_digest"),
    "custody_policy": RoleSpec(0, "semantic-routing-policy-custody-policy.v1", "custody_policy", "policy_digest"),
    "base_access_history": RoleSpec(0, "semantic-routing-policy-access-history.v1", "access_history", "history_digest"),
    "custody_readiness_subject": RoleSpec(1, "semantic-routing-policy-custody-readiness-subject.v1", "custody_readiness_subject", "subject_digest", (("custody_policy_digest", "custody_policy"), ("access_history_digest", "base_access_history"), ("concept_inventory_digest", "inventory"))),
    "custody_readiness": RoleSpec(2, "semantic-routing-policy-custody-readiness.v1", "custody_readiness", "readiness_digest", (("base_access_history_digest", "base_access_history"), ("subject_digest", "custody_readiness_subject"))),
    "custody_readiness_request": RoleSpec(3, "semantic-routing-policy-custody-readiness-verification-request.v1", "custody_readiness_verification_request", "request_digest", (("readiness_digest", "custody_readiness"), ("subject_digest", "custody_readiness_subject"), ("expected_base_access_history_digest", "base_access_history"))),
    "binding_receipt": RoleSpec(4, "semantic-routing-policy-binding-receipt.v1", "policy_binding_receipt", "receipt_digest", (("inventory_digest", "inventory"),)),
    "candidate_contamination": RoleSpec(4, "semantic-routing-policy-contamination-manifest.v1", "contamination_manifest", "manifest_digest"),
    "candidate": RoleSpec(5, "semantic-routing-policy-candidate.v1", "candidate", "candidate_digest", (("ontology_inventory_digest", "inventory"), ("contamination_manifest_digest", "candidate_contamination"))),
    "reservation": RoleSpec(6, "semantic-routing-policy-process-reservation.v1", "process_reservation", "reservation_digest"),
    "rollback_plan": RoleSpec(6, "semantic-routing-policy-evaluation-rollback-plan.v1", "rollback_plan", "plan_digest"),
    "attempt_envelope": RoleSpec(7, "semantic-routing-policy-attempt-envelope.v1", "attempt_envelope", "envelope_digest", (("candidate_digest", "candidate"), ("reservation_digest", "reservation"), ("rollback_plan_digest", "rollback_plan"))),
    "execution_contamination_subject": RoleSpec(8, "semantic-routing-policy-execution-contamination-subject.v1", "execution_contamination_subject", "subject_digest", (("candidate_digest", "candidate"), ("candidate_contamination_manifest_digest", "candidate_contamination"), ("attempt_envelope_digest", "attempt_envelope"))),
    "execution_contamination": RoleSpec(9, "semantic-routing-policy-execution-contamination-attestation.v1", "execution_contamination", "attestation_digest", (("subject_digest", "execution_contamination_subject"),)),
    "execution_contamination_request": RoleSpec(10, "semantic-routing-policy-execution-contamination-verification-request.v1", "execution_contamination_verification_request", "request_digest", (("attestation_digest", "execution_contamination"), ("subject_digest", "execution_contamination_subject"))),
    "preexecution_bundle": RoleSpec(11, "semantic-routing-policy-preexecution-verification-bundle.v1", "preexecution_verification_bundle", "bundle_digest", (("custody_readiness_verification_request_digest", "custody_readiness_request"), ("execution_contamination_verification_request_digest", "execution_contamination_request"))),
    "preregistration": RoleSpec(12, "semantic-routing-policy-preregistration.v1", "preregistration", "preregistration_digest", (("candidate_digest", "candidate"), ("attempt_envelope_digest", "attempt_envelope"), ("custody_readiness_digest", "custody_readiness"), ("execution_contamination_digest", "execution_contamination"), ("custody_readiness_verification_request_digest", "custody_readiness_request"), ("execution_contamination_verification_request_digest", "execution_contamination_request"), ("preexecution_verification_bundle_digest", "preexecution_bundle"))),
    "activation_subject": RoleSpec(13, "semantic-routing-policy-protected-access-activation-subject.v1", "protected_access_activation_subject", "subject_digest", (("preregistration_digest", "preregistration"), ("base_access_history_digest", "base_access_history"), ("reservation_digest", "reservation"))),
    "activated_access_history": RoleSpec(13, "semantic-routing-policy-access-history.v1", "access_history", "history_digest"),
    "activation": RoleSpec(14, "semantic-routing-policy-protected-access-activation.v1", "protected_access_activation", "activation_digest", (("subject_digest", "activation_subject"), ("base_access_history_digest", "base_access_history"), ("activated_access_history_digest", "activated_access_history"))),
    "channel": RoleSpec(15, "semantic-routing-policy-evaluator-authenticated-channel-coordinate.v1", "evaluator_authenticated_channel_coordinate", "channel_coordinate_digest"),
    "invocation_challenge": RoleSpec(16, "semantic-routing-policy-evaluator-invocation-challenge.v1", "evaluator_invocation_challenge", "challenge_digest", (("preregistration_digest", "preregistration"), ("attempt_envelope_digest", "attempt_envelope"), ("reservation_digest", "reservation"), ("protected_access_activation_digest", "activation"), ("authenticated_channel_coordinate_digest", "channel"))),
    "start_subject": RoleSpec(17, "semantic-routing-policy-evaluator-execution-start-subject.v1", "evaluator_execution_start_subject", "subject_digest", (("invocation_challenge_digest", "invocation_challenge"), ("authenticated_channel_coordinate_digest", "channel"), ("protected_access_activation_digest", "activation"))),
    "start_request": RoleSpec(18, "semantic-routing-policy-evaluator-execution-start-verification-request.v1", "evaluator_execution_start_verification_request", "request_digest", (("invocation_challenge_digest", "invocation_challenge"), ("expected_authenticated_channel_coordinate_digest", "channel"), ("expected_start_subject_digest", "start_subject"))),
    "start_proof": RoleSpec(19, "semantic-routing-policy-evaluator-execution-start-proof.v1", "evaluator_execution_start_proof", "start_proof_digest", (("challenge_digest", "invocation_challenge"), ("subject_digest", "start_subject"))),
    "launch_subject": RoleSpec(20, "semantic-routing-policy-evaluator-execution-launch-subject.v1", "evaluator_execution_launch_subject", "subject_digest", (("evaluator_execution_start_proof_digest", "start_proof"), ("evaluator_start_verification_request_digest", "start_request"), ("authenticated_channel_coordinate_digest", "channel"), ("reservation_digest", "reservation"))),
    "launch": RoleSpec(21, "semantic-routing-policy-evaluator-execution-launch-receipt.v1", "evaluator_execution_launch_receipt", "launch_receipt_digest", (("subject_digest", "launch_subject"),)),
    "handoff_subject": RoleSpec(22, "semantic-routing-policy-protected-descriptor-handoff-subject.v1", "protected_descriptor_handoff_subject", "subject_digest", (("evaluator_execution_start_proof_digest", "start_proof"), ("evaluator_execution_launch_receipt_digest", "launch"), ("evaluator_start_verification_request_digest", "start_request"), ("authenticated_channel_coordinate_digest", "channel"), ("reservation_digest", "reservation"))),
    "handoff": RoleSpec(23, "semantic-routing-policy-protected-descriptor-handoff-receipt.v1", "protected_descriptor_handoff_receipt", "handoff_receipt_digest", (("subject_digest", "handoff_subject"),)),
    "terminal_access_history": RoleSpec(24, "semantic-routing-policy-access-history.v1", "access_history", "history_digest"),
    "closure_subject": RoleSpec(25, "semantic-routing-policy-protected-access-closure-subject.v1", "protected_access_closure_subject", "subject_digest", (("preregistration_digest", "preregistration"), ("protected_access_activation_digest", "activation"), ("activated_access_history_digest", "activated_access_history"), ("terminal_access_history_digest", "terminal_access_history"), ("evaluator_execution_start_proof_digest", "start_proof"), ("evaluator_execution_launch_receipt_digest", "launch"), ("protected_descriptor_handoff_receipt_digest", "handoff"), ("reservation_digest", "reservation"))),
    "closure": RoleSpec(26, "semantic-routing-policy-protected-access-closure.v1", "protected_access_closure", "closure_digest", (("subject_digest", "closure_subject"), ("activated_access_history_digest", "activated_access_history"), ("terminal_access_history_digest", "terminal_access_history"))),
    "attempt": RoleSpec(27, "semantic-routing-policy-execution-attempt.v1", "execution_attempt", "attempt_digest", (("candidate_digest", "candidate"), ("attempt_envelope_digest", "attempt_envelope"), ("protected_access_activation_digest", "activation"), ("evaluator_execution_start_proof_digest", "start_proof"), ("evaluator_execution_start_verification_request_digest", "start_request"), ("evaluator_execution_launch_receipt_digest", "launch"), ("protected_descriptor_handoff_receipt_digest", "handoff"), ("protected_access_closure_digest", "closure"))),
    "verdict_subject": RoleSpec(28, "semantic-routing-policy-verdict-approval-subject.v1", "verdict_approval_subject", "subject_digest", (("candidate_digest", "candidate"), ("preregistration_digest", "preregistration"), ("execution_contamination_digest", "execution_contamination"), ("protected_access_activation_digest", "activation"), ("execution_attempt_digest", "attempt"), ("protected_access_closure_digest", "closure"))),
    "verdict": RoleSpec(29, "semantic-routing-policy-verdict.v1", "verdict", "verdict_digest", (("candidate_digest", "candidate"), ("preregistration_digest", "preregistration"), ("execution_contamination_digest", "execution_contamination"), ("protected_access_activation_digest", "activation"), ("execution_attempt_digest", "attempt"), ("protected_access_closure_digest", "closure"), ("verdict_approval_subject_digest", "verdict_subject"))),
    "publication_event": RoleSpec(30, "semantic-routing-policy-publication-event.v1", "publication_event", "event_digest", (("candidate_digest", "candidate"), ("verdict_digest", "verdict"))),
    "publication_history": RoleSpec(31, "semantic-routing-policy-publication-history.v1", "publication_history", "history_digest"),
    "owner_head": RoleSpec(32, "semantic-routing-policy-owner-head.v1", "owner_head", "head_digest", (("terminal_event_digest", "publication_event"), ("publication_history_digest", "publication_history"))),
    "owner_checkpoint": RoleSpec(33, "semantic-routing-policy-owner-checkpoint.v1", "owner_checkpoint", "checkpoint_digest", (("head_digest", "owner_head"), ("history_digest", "publication_history"))),
    "currentness_proof": RoleSpec(34, "semantic-routing-policy-currentness-proof.v1", "currentness_proof", "proof_digest"),
}
ROLE_SPECS: Mapping[str, RoleSpec] = MappingProxyType(_SPECS)


def normative_edges() -> tuple[GraphEdge, ...]:
    """Return the immutable normative digest-edge inventory."""
    return tuple(GraphEdge(source, field, target) for source, spec in ROLE_SPECS.items() for field, target in spec.dependencies)


def _edge_failure(edge: GraphEdge) -> str | None:
    if edge.source == edge.target:
        return "self_edge"
    source = ROLE_SPECS.get(edge.source)
    target = ROLE_SPECS.get(edge.target)
    if source is None or target is None:
        return "unknown_role"
    if target.phase > source.phase:
        return "phase_forward_edge"
    if target.phase == source.phase:
        return "back_edge"
    return None


def verify_graph(objects: Mapping[str, Mapping[str, Any]], *, edges: Iterable[GraphEdge] | None = None) -> GraphConsistency:
    """Verify a closed supplied subgraph; never infer authority from consistency."""
    if not isinstance(objects, Mapping) or not objects:
        raise AdoptedGraphError("invalid_input")
    supplied = dict(objects)
    if any(type(role) is not str or type(value) is not dict for role, value in supplied.items()):
        raise AdoptedGraphError("invalid_input")
    unknown = set(supplied) - set(ROLE_SPECS)
    if unknown:
        raise AdoptedGraphError("unknown_role")

    expected = {edge for edge in normative_edges() if edge.source in supplied}
    selected = expected if edges is None else set(edges)
    if any(type(edge) is not GraphEdge for edge in selected):
        raise AdoptedGraphError("invalid_input")
    for edge in selected:
        failure = _edge_failure(edge)
        if failure:
            raise AdoptedGraphError(failure, edge.source)
    if selected != expected:
        raise AdoptedGraphError("topology_invalid")

    missing = [edge for edge in expected if edge.target not in supplied]
    opaque = next((edge for edge in missing if edge.target in {
        "custody_readiness_request", "execution_contamination_request"
    }), None)
    if opaque is not None:
        raise AdoptedGraphError("opaque_caller_request", opaque.source)
    if missing:
        raise AdoptedGraphError("missing_preimage", missing[0].source)

    computed: dict[str, str] = {}
    for role, value in supplied.items():
        spec = ROLE_SPECS[role]
        if value.get("schema") != spec.schema or validate_protocol(value):
            raise AdoptedGraphError("schema_invalid", role)
        try:
            computed[role] = object_digest(spec.digest_domain, value, spec.self_digest_field)
        except (TypeError, ValueError):
            raise AdoptedGraphError("schema_invalid", role) from None
        if value.get(spec.self_digest_field) != computed[role]:
            raise AdoptedGraphError("digest_mismatch", role)

    for edge in expected:
        if supplied[edge.source].get(edge.digest_field) != computed[edge.target]:
            raise AdoptedGraphError("digest_mismatch", edge.source)

    ordered = tuple(sorted(supplied, key=lambda role: (ROLE_SPECS[role].phase, role)))
    return GraphConsistency(True, False, ordered)
