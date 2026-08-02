"""Fail-closed verifier for supplied Decision 103 S2 protocol preimages."""
from __future__ import annotations

import base64
import hashlib
from datetime import datetime
from typing import Any, Mapping

from rocs_cli.semantic_adopted_authority import (
    AdoptedAuthorityError, verify_authority_credential, verify_principal_separation,
)
from rocs_cli.semantic_adopted_digests import object_digest
from rocs_cli.semantic_adopted_graph import AdoptedGraphError, ROLE_SPECS, verify_graph
from rocs_cli.semantic_adopted_protocol import jcs_bytes, validate_protocol
from rocs_cli.semantic_adopted_signatures import AdoptedSignatureError, verify_ed25519

ERROR_KINDS = (
    "invalid_bundle", "schema_invalid", "digest_mismatch", "nested_mismatch",
    "authority_invalid", "signature_invalid", "history_invalid", "contamination_invalid",
    "reservation_invalid", "ordering_invalid", "attempt_invalid", "closure_invalid",
)
_SELF = {s.schema: (s.digest_domain, s.self_digest_field) for s in ROLE_SPECS.values() if s.schema}
_SELF["semantic-routing-policy-b0-exposure-evidence.v1"] = ("b0_exposure_evidence", "evidence_digest")


def _walk(value: Any):
    if type(value) is dict:
        yield value
        for child in value.values():
            yield from _walk(child)
    elif type(value) is list:
        for child in value:
            yield from _walk(child)


def _stamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _self_digests(value: Any) -> bool:
    try:
        for item in _walk(value):
            config = _SELF.get(item.get("schema"))
            if config and config[1] in item and item[config[1]] != object_digest(config[0], item, config[1]):
                return False
            if item.get("schema") == "semantic-routing-policy-access-history.v1":
                prior = None
                for index, event in enumerate(item["events"], 1):
                    if event["sequence"] != index or event["previous_event_digest"] != prior:
                        return False
                    if event["event_digest"] != object_digest("access_history_event", event, "event_digest"):
                        return False
                    prior = event["event_digest"]
        return True
    except (KeyError, TypeError, ValueError):
        return False


def _nested_digest_joins(value: Any) -> bool:
    for item in _walk(value):
        for field, digest in item.items():
            if not field.endswith("_digest") or field in {"body_digest", "artifact_digest"}:
                continue
            nested = item.get(field[:-7])
            if type(nested) is dict:
                config = _SELF.get(nested.get("schema"))
                if config and nested.get(config[1]) != digest:
                    return False
    return True


def _signatures_valid(root: Any) -> bool:
    try:
        count = 0
        names = (("custodian_credential", "custodian_approval"), ("independent_review_credential", "independent_review_approval"), ("evaluator_credential", "evaluator_approval"), ("launch_gateway_credential", "launch_gateway_approval"))
        for item in _walk(root):
            for credential_field, approval_field in names:
                if credential_field not in item or approval_field not in item:
                    continue
                count += 1; credential, approval = item[credential_field], item[approval_field]
                verify_authority_credential(approval["issuer"], credential, trusted_now="2030-01-01T00:00:00Z")
                body = approval["attestation_body"]
                for field in ("issuer", "subject_digest", "purpose", "valid_from", "valid_until", "revoked", "trust_root_digest", "public_key_digest"):
                    if body[field] != approval[field]: return False
                if approval["public_key_digest"] != credential["public_key_digest"] or approval["trust_root_digest"] != credential["trust_root_digest"]: return False
                verify_ed25519(purpose="approval", body_digest=body["body_digest"], public_key_base64=credential["public_key_base64"], signature_base64=approval["signature_base64"])
        return count >= 2
    except (AdoptedAuthorityError, AdoptedSignatureError, KeyError, TypeError):
        return False


def _histories(verdict: dict[str, Any]) -> bool:
    try:
        prereg = verdict["preregistration"]
        activation = verdict["protected_access_activation"]
        closure = verdict["protected_access_closure"]
        base, active, terminal = prereg["access_history"], activation["activated_access_history"], closure["terminal_access_history"]
        if activation["base_access_history"] != base or closure["activated_access_history"] != active:
            return False
        if not (12 <= len(base["events"]) <= 254 and len(active["events"]) == len(base["events"]) + 1 <= 255 and len(terminal["events"]) == len(active["events"]) + 1 <= 256):
            return False
        if active["events"][:-1] != base["events"] or terminal["events"][:-1] != active["events"]:
            return False
        grant, revoke = active["events"][-1], terminal["events"][-1]
        subject = activation["subject"]
        return (
            grant["action"] == "grant" and revoke["action"] == "revoke"
            and grant["principal_id"] == revoke["principal_id"] == subject["executor_authority"]["principal_id"]
            and grant["access"] == revoke["access"] == subject["grant_access"]
            and grant["event_digest"] == subject["grant_event_digest"]
            and revoke["event_digest"] == closure["subject"]["revoke_event_digest"]
        )
    except (KeyError, TypeError):
        return False


def _execution_chain(verdict: dict[str, Any], attempt: dict[str, Any]) -> tuple[bool, bool, bool]:
    try:
        prereg, envelope = verdict["preregistration"], verdict["attempt_envelope"]
        reservation = envelope["process_reservation"]
        reservation_ok = (
            prereg["attempt_envelope"] == envelope and envelope["process_invocations"] == 1
            and envelope["process_retries"] == envelope["selective_row_reruns"] == envelope["same_candidate_repairs"] == 0
            and reservation["single_invocation_limit"] == 1 and envelope["reservation_digest"] == reservation["reservation_digest"]
            and _stamp(reservation["reserved_at"]) < _stamp(reservation["expires_at"])
        )
        for field in ("protected_access_activation", "evaluator_execution_start_proof", "evaluator_execution_start_verification_request", "evaluator_execution_launch_receipt", "protected_descriptor_handoff_receipt", "protected_access_closure"):
            if attempt[field] != verdict[field]:
                return reservation_ok, False, False
        present = attempt["evaluator_execution_start_proof"] is not None
        order_ok = True
        if present:
            proof, request = attempt["evaluator_execution_start_proof"], attempt["evaluator_execution_start_verification_request"]
            challenge = proof["challenge"]
            if request["invocation_challenge"] != challenge:
                order_ok = False
            channel = challenge["authenticated_channel_coordinate"]
            start = proof["subject"]
            if not (_stamp(challenge["issued_at"]) < _stamp(challenge["expires_at"]) and _stamp(channel["established_at"]) < _stamp(channel["expires_at"]) and _stamp(start["authorized_start_not_after"]) <= _stamp(challenge["expires_at"])):
                order_ok = False
            if request["expected_authenticated_channel_coordinate"] != channel or start["authenticated_channel_coordinate"] != channel or request["expected_start_subject_digest"] != start["subject_digest"]:
                order_ok = False
            if any(x["reservation_digest"] != reservation["reservation_digest"] for x in (challenge, start)):
                order_ok = False
        launch = attempt["evaluator_execution_launch_receipt"]
        if launch is not None:
            ls = launch["subject"]
            if not (_stamp(ls["launch_authorized_at"]) <= _stamp(ls["spawn_not_after"])) or ls["reservation_digest"] != reservation["reservation_digest"]:
                order_ok = False
        handoff = attempt["protected_descriptor_handoff_receipt"]
        if handoff is not None:
            hs = handoff["subject"]
            if hs["direct_os_descriptor_transfer"] is not False or hs["reservation_digest"] != reservation["reservation_digest"] or _stamp(hs["handed_off_at"]) > _stamp(hs["descriptor_access_expires_at"]):
                order_ok = False
        return reservation_ok, order_ok, True
    except (KeyError, TypeError, ValueError):
        return False, False, False


def verify_execution_bundle(bundle: Mapping[str, Any]) -> tuple[str, ...]:
    """Verify caller-supplied schema-defined attempt/verdict preimages."""
    if type(bundle) is not dict or set(bundle) != {"attempt", "verdict", "execution_receipt_base64"} or any(type(bundle[k]) is not dict for k in ("attempt", "verdict")):
        return ("invalid_bundle",)
    attempt, verdict = bundle["attempt"], bundle["verdict"]
    errors: list[str] = []
    encoded_receipt = bundle["execution_receipt_base64"]
    expected_receipt = attempt.get("execution_receipt_digest")
    try:
        raw_receipt = None if encoded_receipt is None else base64.b64decode(encoded_receipt, validate=True)
    except (ValueError, TypeError):
        return ("invalid_bundle",)
    actual_receipt = None if raw_receipt is None else "sha256:" + hashlib.sha256(raw_receipt).hexdigest()
    receipt_values = {item["execution_receipt_digest"] for item in _walk(bundle) if type(item) is dict and "execution_receipt_digest" in item}
    if actual_receipt != expected_receipt or receipt_values != {expected_receipt}:
        errors.append("digest_mismatch")
    if validate_protocol(attempt) or validate_protocol(verdict):
        return ("schema_invalid",)
    if not _self_digests(bundle): errors.append("digest_mismatch")
    if not _nested_digest_joins(bundle) or verdict["execution_attempt"] != attempt: errors.append("nested_mismatch")
    try:
        verify_principal_separation(verdict["preregistration"]["participants"])
        # Exercise the shared graph verifier over supplied closed leaf preimages.
        verify_graph({"base_access_history": verdict["preregistration"]["access_history"]})
    except (AdoptedAuthorityError, AdoptedGraphError, KeyError, TypeError): errors.append("authority_invalid")
    participants = verdict["preregistration"]["participants"]
    subject = verdict["execution_contamination_attestation"]["subject"]
    if sum(p["b0_exposure"] == "disproven" for p in participants) != 11 or subject["result"] != "no_reuse":
        errors.append("contamination_invalid")
    if not _signatures_valid(verdict): errors.append("signature_invalid")
    if not _histories(verdict): errors.append("history_invalid")
    reservation_ok, order_ok, nested_ok = _execution_chain(verdict, attempt)
    if not reservation_ok: errors.append("reservation_invalid")
    if not order_ok: errors.append("ordering_invalid")
    if not nested_ok: errors.append("nested_mismatch")
    if attempt["process_retries"] or attempt["selective_row_reruns"] or attempt["same_candidate_repairs"]:
        errors.append("attempt_invalid")
    state = attempt["attempt_state"]
    if state != verdict["attempt_state"] or (state == "completed" and verdict["outcome"] not in {"pass", "fail"}):
        errors.append("attempt_invalid")
    closure = attempt["protected_access_closure"]["subject"]
    if state == "completed" and not (
        closure["process_termination_state"] == "terminated_and_reaped"
        and closure["descriptor_access_state"] == "revoked_and_closed"
        and closure["process_invocations"] == 1 and closure["closure_reason"] == "completed"
        and _stamp(closure["process_spawned_at"]) <= _stamp(closure["process_terminated_at"])
        <= _stamp(closure["descriptor_access_closed_at"]) <= _stamp(closure["closed_at"])
        <= _stamp(closure["activation_expires_at"])
    ): errors.append("closure_invalid")
    return tuple(dict.fromkeys(errors))


def execution_verification_result(bundle: Mapping[str, Any]) -> dict[str, Any]:
    kinds = verify_execution_bundle(bundle)
    return {"ok": not kinds, "error_kinds": list(kinds)}


def execution_verification_bytes(bundle: Mapping[str, Any]) -> bytes:
    return jcs_bytes(execution_verification_result(bundle))
