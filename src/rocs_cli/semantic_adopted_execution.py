"""Fail-closed verifier for adopted S2 execution bundles."""
from __future__ import annotations

import base64
import hashlib
from datetime import datetime
from typing import Any, Mapping

from rocs_cli.semantic_adopted_authority import (
    AdoptedAuthorityError, verify_authority_credential, verify_principal_separation,
    verify_role_separation_receipt,
)
from rocs_cli.semantic_adopted_digests import object_digest
from rocs_cli.semantic_adopted_graph import (
    AdoptedGraphError, ExecutionGraphSupport, extract_execution_graph,
    verify_execution_graph,
)
from rocs_cli.semantic_adopted_protocol import jcs_bytes, validate_protocol
from rocs_cli.semantic_adopted_signatures import AdoptedSignatureError, verify_ed25519

ERROR_KINDS = (
    "invalid_bundle", "schema_invalid", "digest_mismatch", "nested_mismatch",
    "authority_invalid", "signature_invalid", "history_invalid", "contamination_invalid",
    "reservation_invalid", "ordering_invalid", "attempt_invalid", "closure_invalid",
)
_FIELDS = ("issuer", "subject_digest", "purpose", "valid_from", "valid_until", "revoked",
           "trust_root_digest", "public_key_digest")
_STAGES = (
    ("readiness_approval", "custody_readiness_subject", "custodian_credential", "custody_readiness"),
    ("contamination_custodian_approval", "execution_contamination_subject", "custodian_credential", "execution_contamination_custodian"),
    ("contamination_reviewer_approval", "execution_contamination_subject", "reviewer_credential", "execution_contamination_independent_review"),
    ("activation_approval", "activation_subject", "custodian_credential", "protected_access_activation"),
    ("start_approval", "start_subject", "evaluator_credential", "evaluator_execution_start"),
    ("launch_approval", "launch_subject", "gateway_credential", "evaluator_execution_launch"),
    ("handoff_approval", "handoff_subject", "gateway_credential", "protected_descriptor_handoff"),
    ("closure_approval", "closure_subject", "custodian_credential", "protected_access_closure"),
    ("verdict_custodian_approval", "verdict_subject", "custodian_credential", "custody"),
    ("verdict_reviewer_approval", "verdict_subject", "reviewer_credential", "independent_review"),
)


def _stamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _authority(credential: Mapping[str, Any]) -> dict[str, Any]:
    result = {field: credential[field] for field in
              ("repository_id", "git_commit", "git_tree", "principal_id", "authority_role")}
    result["authority_credential_digest"] = credential["credential_digest"]
    return result


def _verify_stage_approval(approval: Mapping[str, Any], subject: Mapping[str, Any],
                           credential: Mapping[str, Any], *, purpose: str,
                           trusted_now: str) -> None:
    """Verify the one exact approval representation and all of its bindings."""
    body = approval["attestation_body"]
    expected_authority = _authority(credential)
    subject_digest = subject["subject_digest"]
    if (any(approval[field] != body[field] for field in _FIELDS)
            or approval["issuer"] != expected_authority
            or body["issuer"] != expected_authority
            or approval["subject_digest"] != subject_digest
            or approval["purpose"] != purpose
            or approval["public_key_digest"] != credential["public_key_digest"]
            or approval["trust_root_digest"] != credential["trust_root_digest"]
            or approval["revoked"] is not False
            or body["body_digest"] != object_digest("approval_attestation_body", body, "body_digest")
            or approval["artifact_digest"] != object_digest("approval_artifact", approval, "artifact_digest")):
        raise AdoptedSignatureError("approval binding differs")
    verify_authority_credential(expected_authority, credential, trusted_now=trusted_now)
    now = _stamp(trusted_now)
    if not (_stamp(approval["valid_from"]) <= now < _stamp(approval["valid_until"])):
        raise AdoptedSignatureError("approval outside validity interval")
    verify_ed25519(purpose="approval", body_digest=body["body_digest"],
                   public_key_base64=credential["public_key_base64"],
                   signature_base64=approval["signature_base64"])


def _histories(objects: Mapping[str, Any]) -> bool:
    try:
        base, active, terminal = (objects[name] for name in
                                  ("base_access_history", "activated_access_history", "terminal_access_history"))
        if not (12 <= len(base["events"]) <= 254
                and len(active["events"]) == len(base["events"]) + 1 <= 255
                and len(terminal["events"]) == len(active["events"]) + 1 <= 256
                and active["events"][:-1] == base["events"]
                and terminal["events"][:-1] == active["events"]):
            return False
        participants = objects["preregistration"]["participants"]
        if len(base["events"]) < 12 or any(
            event["action"] != "assign" or event["principal_id"] != participant["authority"]["principal_id"]
            or event["role"] != participant["role"] or event["access"] != participant["access"]
            for event, participant in zip(base["events"][:12], participants)
        ): return False
        grant, revoke = active["events"][-1], terminal["events"][-1]
        activation, closure = objects["activation_subject"], objects["closure_subject"]
        return (grant["action"], revoke["action"]) == ("grant", "revoke") and (
            grant["occurred_at"] == activation["issued_at"] and revoke["occurred_at"] == closure["closed_at"] and
            grant["principal_id"] == revoke["principal_id"] == activation["executor_authority"]["principal_id"]
            and grant["access"] == revoke["access"] == activation["grant_access"]
            and grant["event_digest"] == activation["grant_event_digest"]
            and revoke["event_digest"] == closure["revoke_event_digest"])
    except (KeyError, TypeError):
        return False


def _execution(objects: Mapping[str, Any], trusted_now: str) -> tuple[bool, bool, bool]:
    try:
        envelope, reservation = objects["attempt_envelope"], objects["reservation"]
        reservation_ok = (envelope["process_invocations"] == reservation["single_invocation_limit"] == 1
            and envelope["process_retries"] == envelope["selective_row_reruns"] == envelope["same_candidate_repairs"] == 0
            and _stamp(reservation["reserved_at"]) <= _stamp(trusted_now) < _stamp(reservation["expires_at"]))
        order_ok = True
        if "start_proof" in objects:
            challenge, channel, start = objects["invocation_challenge"], objects["channel"], objects["start_subject"]
            order_ok &= (_stamp(challenge["issued_at"]) <= _stamp(trusted_now) < _stamp(challenge["expires_at"])
                         and _stamp(channel["established_at"]) <= _stamp(trusted_now) < _stamp(channel["expires_at"])
                         and _stamp(start["authorized_start_not_after"]) <= _stamp(challenge["expires_at"]))
        if "launch_subject" in objects:
            launch = objects["launch_subject"]
            order_ok &= _stamp(launch["launch_authorized_at"]) <= _stamp(launch["spawn_not_after"])
            order_ok &= launch["reservation_consumptions_before"] == 0 and launch["reservation_consumptions_after"] == 1
        if "handoff_subject" in objects:
            handoff = objects["handoff_subject"]
            order_ok &= (handoff["direct_os_descriptor_transfer"] is False
                         and _stamp(handoff["handed_off_at"]) <= _stamp(handoff["descriptor_access_expires_at"])
                         and _stamp(handoff["descriptor_access_expires_at"]) <= _stamp(objects["activation_subject"]["expires_at"]))
        closure = objects["closure_subject"]
        spawned = closure.get("process_spawned_at")
        if spawned is not None:
            spawn = _stamp(spawned)
            deadlines = [_stamp(reservation["expires_at"]), _stamp(objects["activation_subject"]["expires_at"])]
            if "channel" in objects: deadlines.append(_stamp(objects["channel"]["expires_at"]))
            if "invocation_challenge" in objects: deadlines.append(_stamp(objects["invocation_challenge"]["expires_at"]))
            if "start_subject" in objects: deadlines.append(_stamp(objects["start_subject"]["authorized_start_not_after"]))
            if "launch_subject" in objects:
                deadlines.append(_stamp(objects["launch_subject"]["spawn_not_after"]))
                order_ok &= _stamp(objects["launch_subject"]["launch_authorized_at"]) <= spawn
            if "handoff_subject" in objects: order_ok &= spawn <= _stamp(objects["handoff_subject"]["handed_off_at"])
            order_ok &= all(spawn < deadline for deadline in deadlines)
            fixed = [closure.get("process_terminated_at"), closure.get("descriptor_access_closed_at")]
            order_ok &= all(value is None or spawn <= _stamp(value) <= _stamp(closure["closed_at"]) for value in fixed)
        state = objects["attempt"]["attempt_state"]
        attempt_ok = state == objects["verdict"]["attempt_state"]
        if state == "completed":
            attempt_ok &= objects["verdict"]["outcome"] in {"pass", "fail"}
        return reservation_ok, order_ok, attempt_ok
    except (KeyError, TypeError, ValueError):
        return False, False, False


def verify_execution_bundle(bundle: Mapping[str, Any], *, support: ExecutionGraphSupport,
                            trusted_now: str) -> tuple[str, ...]:
    """Verify actual bundle preimages against fixed graph support and caller time."""
    if (type(bundle) is not dict or set(bundle) != {"attempt", "verdict", "execution_receipt_base64"}
            or any(type(bundle.get(k)) is not dict for k in ("attempt", "verdict"))):
        return ("invalid_bundle",)
    try:
        _stamp(trusted_now)
    except (TypeError, ValueError):
        return ("invalid_bundle",)
    if validate_protocol(bundle["attempt"]) or validate_protocol(bundle["verdict"]):
        return ("schema_invalid",)
    errors: list[str] = []
    try:
        verify_execution_graph(bundle, support)
        objects = extract_execution_graph(bundle, support)
    except AdoptedGraphError as exc:
        kind = {"schema_invalid": "schema_invalid", "digest_mismatch": "digest_mismatch",
                "nested_mismatch": "nested_mismatch"}.get(exc.kind, "authority_invalid")
        return (kind,)
    try:
        encoded = bundle["execution_receipt_base64"]
        raw = None if encoded is None else base64.b64decode(encoded, validate=True)
        actual = None if raw is None else "sha256:" + hashlib.sha256(raw).hexdigest()
        if actual != bundle["attempt"]["execution_receipt_digest"]:
            errors.append("digest_mismatch")
    except (TypeError, ValueError):
        return ("invalid_bundle",)
    try:
        participants = objects["preregistration"]["participants"]
        verify_principal_separation(participants)
        verify_role_separation_receipt(participants, objects["role_separation"],
                                       access_history_digest=objects["base_access_history"]["history_digest"])
        for participant, credential in zip(participants, support.participant_credentials):
            verify_authority_credential(participant["authority"], credential, trusted_now=trusted_now)
    except (AdoptedAuthorityError, KeyError, TypeError):
        errors.append("authority_invalid")
    try:
        for approval_role, subject_role, credential_role, purpose in _STAGES:
            if approval_role in objects:
                _verify_stage_approval(objects[approval_role], objects[subject_role], objects[credential_role],
                                       purpose=purpose, trusted_now=trusted_now)
    except (AdoptedAuthorityError, AdoptedSignatureError, KeyError, TypeError, ValueError):
        errors.append("signature_invalid")
    participants = objects["preregistration"]["participants"]
    contamination = objects["execution_contamination_subject"]
    if (sum(item["b0_exposure"] == "disproven" for item in participants) != 11
            or contamination["result"] != "no_reuse"):
        errors.append("contamination_invalid")
    if "terminal_access_history" in objects and not _histories(objects): errors.append("history_invalid")
    reservation_ok, ordering_ok, attempt_ok = _execution(objects, trusted_now)
    if not reservation_ok: errors.append("reservation_invalid")
    if not ordering_ok: errors.append("ordering_invalid")
    if not attempt_ok: errors.append("attempt_invalid")
    if objects["attempt"]["attempt_state"] == "completed":
        closure = objects["closure_subject"]
        if not (closure["process_termination_state"] == "terminated_and_reaped"
                and closure["descriptor_access_state"] == "revoked_and_closed"
                and closure["process_invocations"] == 1 and closure["closure_reason"] == "completed"
                and _stamp(closure["process_spawned_at"]) <= _stamp(closure["process_terminated_at"])
                <= _stamp(closure["descriptor_access_closed_at"]) <= _stamp(closure["closed_at"])
                <= _stamp(closure["activation_expires_at"])):
            errors.append("closure_invalid")
    return tuple(dict.fromkeys(errors))


def execution_verification_result(bundle: Mapping[str, Any], *, support: ExecutionGraphSupport,
                                  trusted_now: str) -> dict[str, Any]:
    kinds = verify_execution_bundle(bundle, support=support, trusted_now=trusted_now)
    return {"ok": not kinds, "error_kinds": list(kinds)}


def execution_verification_bytes(bundle: Mapping[str, Any], *, support: ExecutionGraphSupport,
                                 trusted_now: str) -> bytes:
    return jcs_bytes(execution_verification_result(bundle, support=support, trusted_now=trusted_now))
