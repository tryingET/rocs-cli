"""Independent insertion-attempt state machine."""

from __future__ import annotations

from typing import Any

from python.common import (
    DIGEST_RE,
    DOMAINS,
    MAX_INT,
    REVISION,
    SCHEMA_NAMES,
    SPAN_RE,
    ConformanceError,
    ProtocolFailure,
    StrictJSONError,
    canonical_base64,
    object_digest,
    raw_digest,
    require,
    same,
    snapshot_text,
    strict_json_loads,
)
from python.schedule import Schedule

def make_request(generation: int, attempt: int, index: int, input_raw: bytes, contribution: bytes) -> dict[str, Any]:
    value = {
        "schema": SCHEMA_NAMES[0],
        "protocol_revision": REVISION,
        "repository_id": "pi-extensions",
        "component_id": "pi-ontology-workflows",
        "package_name": "@tryinget/pi-ontology-workflows",
        "execution_generation": generation,
        "attempt_id": attempt,
        "handler_registration_index": index,
        "input_prompt_byte_length": len(input_raw),
        "input_prompt_digest": raw_digest(DOMAINS[5], input_raw),
        "contribution_byte_length": len(contribution),
        "contribution_digest": raw_digest(DOMAINS[6], contribution),
    }
    value["request_digest"] = object_digest(DOMAINS[0], value, "request_digest")
    return value


def make_witness(request: dict[str, Any], assigned: bytes, readback: bytes, start: int, end: int) -> dict[str, Any]:
    value = {
        "schema": SCHEMA_NAMES[1],
        "host_package": "@earendil-works/pi-coding-agent",
        "protocol_revision": REVISION,
        "request_digest": request["request_digest"],
        "execution_generation": request["execution_generation"],
        "attempt_id": request["attempt_id"],
        "handler_registration_index": request["handler_registration_index"],
        "assigned_prompt_chain_byte_length": len(assigned),
        "assigned_prompt_chain_digest": raw_digest(DOMAINS[7], assigned),
        "readback_prompt_chain_byte_length": len(readback),
        "readback_prompt_chain_digest": raw_digest(DOMAINS[7], readback),
        "contribution_start_byte_offset": start,
        "contribution_end_byte_offset": end,
        "observation_phase": "post_assignment_readback_pre_dispatch",
        "provider_request_dispatched_at_observation": False,
        "model_invocation_started_at_observation": False,
    }
    value["witness_digest"] = object_digest(DOMAINS[1], value, "witness_digest")
    return value


def make_acknowledgement(request: dict[str, Any], witness: dict[str, Any]) -> dict[str, Any]:
    value = {
        "schema": SCHEMA_NAMES[2],
        "issuer": {"kind": "pi_extension_component", "id": "pi-ontology-workflows"},
        "request_digest": request["request_digest"],
        "witness_digest": witness["witness_digest"],
        "execution_generation": request["execution_generation"],
        "attempt_id": request["attempt_id"],
        "handler_registration_index": request["handler_registration_index"],
        "acknowledgement_outcome": "observed_inserted",
        "claim_scope": "prompt_chain_insertion_only",
    }
    value["acknowledgement_digest"] = object_digest(DOMAINS[2], value, "acknowledgement_digest")
    return value


def make_record(request: dict[str, Any], witness: dict[str, Any], acknowledgement: dict[str, Any]) -> dict[str, Any]:
    value = {
        "schema": SCHEMA_NAMES[3],
        "host_package": "@earendil-works/pi-coding-agent",
        "protocol_revision": REVISION,
        "request_digest": request["request_digest"],
        "witness_digest": witness["witness_digest"],
        "acknowledgement_digest": acknowledgement["acknowledgement_digest"],
        "execution_generation": request["execution_generation"],
        "attempt_id": request["attempt_id"],
        "handler_registration_index": request["handler_registration_index"],
        "insertion_outcome": "observed_inserted",
        "claim_scope": "prompt_chain_insertion_only",
        "provider_request_dispatched_at_record": False,
        "model_invocation_started_at_record": False,
        "record_phase": "acknowledged_pre_dispatch",
    }
    value["insertion_record_digest"] = object_digest(DOMAINS[3], value, "insertion_record_digest")
    return value


def make_error(generation: int, attempt: int | None, stage: str, code: str) -> dict[str, Any]:
    value = {
        "schema": SCHEMA_NAMES[4],
        "protocol_revision": REVISION,
        "execution_generation": generation,
        "attempt_id_or_null": attempt,
        "stage": stage,
        "error_code": code,
        "details": [],
    }
    value["error_digest"] = object_digest(DOMAINS[4], value, "error_digest")
    return value


def run_attempt(spec: dict[str, Any], fixture: bool) -> tuple[dict[str, Any], dict[str, Any]]:
    schedule = Schedule(spec["events"], fixture)
    generation = spec["initial_generation"]
    next_attempt = spec["initial_next_attempt_id"]
    index = spec["handler_registration_index"]
    deadline = spec["deadline_monotonic_ns"]
    require(all(type(value) is int and 0 <= value <= MAX_INT for value in (generation, next_attempt, index, deadline)), "invalid attempt integer")
    input_raw = canonical_base64(spec["input_bytes_base64"], "input_bytes_base64")
    default_contribution = canonical_base64(spec["contribution_bytes_base64"], "contribution_bytes_base64")
    current_generation, now, aborted = generation, 0, False
    registration_component, reservation_override = "pi-ontology-workflows", None
    attempt: int | None = None
    request = witness = acknowledgement = record = None
    state, guard_active, frame_active = "reserved", False, False
    provider_before_record = model_before_record = 0
    controls: list[dict[str, Any]] = []
    cloned = reused = poisoned = deferred = threw = registration_b = False
    assigned_done = readback_done = witness_done = False

    def generic(event: dict[str, str]) -> bool:
        nonlocal current_generation, now, aborted
        kind, value = event["kind"], event["value"]
        if kind == "advance_monotonic_ns":
            now = int(value)
        elif kind == "reload_generation":
            require(int(value) > current_generation, "reload_generation must advance generation")
            current_generation = int(value)
        elif kind == "abort_signal":
            aborted = True
        else:
            return False
        return True

    def predicate(stage: str, before: tuple[tuple[bool, str], ...] = ()) -> None:
        if current_generation != generation:
            raise ProtocolFailure(stage, "stale_generation")
        for established, code in before:
            if established:
                raise ProtocolFailure("dispatch_guard" if code == "reentry_attempt" else "witness", code)
        if aborted:
            raise ProtocolFailure(stage, "aborted")
        if now >= deadline:
            raise ProtocolFailure(stage, "deadline_exceeded")

    def add_control(kind: str, entrypoint: str) -> None:
        require(attempt is not None, "control result before reservation")
        controls.append({"kind": kind, "entrypoint": entrypoint, "execution_generation": generation, "attempt_id": attempt})

    def entrypoint(event: dict[str, str]) -> bool:
        nonlocal poisoned
        kind, value = event["kind"], event["value"]
        mapping = {
            "prompt_attempt": "prompt",
            "continuation_attempt": "continuation",
            "completion_attempt": "completion",
            "provider_dispatch_attempt": "provider_dispatch",
            "model_invocation_attempt": "model_invocation",
            "contributor_callback_attempt": "contributor_callback",
        }
        if kind not in mapping:
            return False
        if value == "blocked":
            require(guard_active, "blocked classification without guard")
            add_control("dispatch_blocked", mapping[kind])
        elif value == "reentry":
            require(guard_active and frame_active, "reentry classification without matching frame")
            poisoned = True
        else:
            add_control("stale_invocation", mapping[kind])
            poisoned = guard_active
        return True

    failure: ProtocolFailure | None = None
    try:
        for event in schedule.take("before_reservation"):
            if generic(event):
                continue
            if event["kind"] == "reserve_attempt_override":
                reservation_override = int(event["value"])
            elif event["kind"] == "replace_registration_component_id":
                registration_component = event["value"]
            elif event["kind"] == "create_registration_b":
                registration_b = True
        if registration_component != "pi-ontology-workflows":
            raise ProtocolFailure("registration", "identity_mismatch")
        if current_generation != generation:
            raise ProtocolFailure("registration", "stale_generation")
        if aborted:
            raise ProtocolFailure("registration", "aborted")
        if now >= deadline:
            raise ProtocolFailure("registration", "deadline_exceeded")
        candidate = next_attempt if reservation_override is None else reservation_override
        if next_attempt == MAX_INT or candidate != next_attempt:
            raise ProtocolFailure("registration", "attempt_reuse")
        attempt, next_attempt = candidate, next_attempt + 1
        guard_active = True
        state = "reserved"
        for event in schedule.take("after_reservation"):
            if generic(event):
                continue
            require(event["kind"] == "reserve" and event["value"] == str(attempt), "reservation assertion failed")

        predicate("prepare")
        state, frame_active = "preparing", True
        contribution = default_contribution
        for event in schedule.take("during_prepare"):
            if generic(event):
                continue
            if event["kind"] == "prepare_return_base64":
                contribution = canonical_base64(event["value"], "prepare_return_base64")
        predicate("prepare")
        if not snapshot_text(input_raw, 0, 16_777_216) or not snapshot_text(contribution, 1, 16_777_216):
            raise ProtocolFailure("prepare", "malformed_input")
        frame_active, state = False, "prepared"
        request = make_request(generation, attempt, index, input_raw, contribution)
        for event in schedule.take("after_prepare"):
            require(generic(event), "unsupported after_prepare event")
        for event in schedule.take("before_apply"):
            require(generic(event), "unsupported before_apply event")
        predicate("apply")
        state = "applying"
        start, end = len(input_raw), len(input_raw) + len(contribution)
        for event in schedule.take("after_apply"):
            if generic(event):
                continue
            match = SPAN_RE.fullmatch(event["value"])
            require(event["kind"] == "apply_span" and match is not None, "invalid apply event")
            start, end = (int(part) for part in match.groups())
        assigned = input_raw[:start] + contribution + input_raw[start:] if start <= len(input_raw) else input_raw + contribution
        if not snapshot_text(assigned, 1, 33_554_432):
            raise ProtocolFailure("apply", "malformed_input")
        inserted = start < end <= len(assigned) and end - start == len(contribution) and assigned[start:end] == contribution
        if not inserted:
            raise ProtocolFailure("apply", "contribution_not_inserted")
        predicate("assignment")
        assigned_done, state = True, "assigned"
        for event in schedule.take("after_assignment"):
            if generic(event):
                continue
            if event["kind"] == "assign_base64":
                require(canonical_base64(event["value"], "assign_base64") == assigned, "assignment assertion failed")
            elif event["kind"] == "assign":
                require(event["value"] == "done" and assigned_done, "assignment order assertion failed")

        readback = assigned
        for event in schedule.take("after_readback"):
            if generic(event):
                continue
            if event["kind"] == "readback_base64":
                readback = canonical_base64(event["value"], "readback_base64")
            elif event["kind"] == "readback":
                require(event["value"] == "verified" and assigned_done, "readback order assertion failed")
        if not snapshot_text(readback, 1, 33_554_432):
            raise ProtocolFailure("readback", "malformed_input")
        predicate("readback")
        if readback != assigned:
            raise ProtocolFailure("readback", "readback_mismatch")
        readback_done, state = True, "readback_verified"
        for event in schedule.take("before_witness"):
            if generic(event):
                continue
            if event["kind"] == "clone_witness_json":
                cloned = True
        predicate("witness")
        witness = make_witness(request, assigned, readback, start, end)
        witness_done, state = True, "witnessed"
        for event in schedule.take("after_witness"):
            if generic(event):
                continue
            kind, value = event["kind"], event["value"]
            if kind == "issue_witness":
                require(value == witness["witness_digest"], "witness digest assertion failed")
            elif kind == "clone_witness_json":
                cloned = True
            elif kind == "witness_issued":
                facts = {"after_assign": assigned_done, "after_readback": readback_done, "generation0": generation == 0}
                require(facts[value] and witness_done, "witness order assertion failed")
        predicate("acknowledgement")
        if cloned:
            raise ProtocolFailure("witness", "witness_forged")

        state, frame_active = "acknowledging", True
        for event in schedule.take("during_applied"):
            if generic(event) or entrypoint(event):
                continue
            kind = event["kind"]
            if kind == "consume_witness_twice":
                reused = True
            elif kind == "invoke_nested_prompt":
                poisoned = True
            elif kind == "detached_callback_call":
                add_control("dispatch_blocked", "contributor_callback")
            elif kind == "consume_from_registration_b":
                require(registration_b, "registration B was not created")
                add_control("stale_invocation", "contributor_callback")
                poisoned = True
            elif kind == "defer_applied":
                deferred = True
            elif kind == "applied_throw":
                threw = True
        predicate("acknowledgement", ((reused, "witness_reused"), (poisoned, "reentry_attempt")))
        if threw:
            raise ProtocolFailure("acknowledgement", "internal_failure")
        if deferred:
            raise ConformanceError("deferred callback remained pending without terminal observer")
        acknowledgement = make_acknowledgement(request, witness)
        malformed_ack = False
        for event in schedule.take("after_applied"):
            if generic(event):
                continue
            kind, value = event["kind"], event["value"]
            if kind == "replace_ack_issuer":
                acknowledgement["issuer"] = {"kind": "pi_extension_component", "id": value}
            elif kind == "inject_ack_bytes_base64":
                try:
                    decoded = canonical_base64(value, kind)
                    candidate_ack = strict_json_loads(decoded, kind)
                    if not isinstance(candidate_ack, dict):
                        raise StrictJSONError("acknowledgement is not an object")
                    acknowledgement = candidate_ack
                except (ConformanceError, StrictJSONError):
                    malformed_ack = True
            elif kind == "applied_return_digest":
                require(acknowledgement.get("acknowledgement_digest") == value, "acknowledgement digest assertion failed")
        if malformed_ack:
            raise ProtocolFailure("acknowledgement", "malformed_input")
        predicate("acknowledgement")
        ack_keys = {
            "schema", "issuer", "request_digest", "witness_digest", "execution_generation", "attempt_id",
            "handler_registration_index", "acknowledgement_outcome", "claim_scope", "acknowledgement_digest",
        }
        issuer = acknowledgement.get("issuer")
        shape_ok = (
            set(acknowledgement) == ack_keys
            and isinstance(issuer, dict)
            and set(issuer) == {"kind", "id"}
            and all(isinstance(acknowledgement[key], str) for key in (
                "schema", "request_digest", "witness_digest", "acknowledgement_outcome", "claim_scope", "acknowledgement_digest"
            ))
            and all(type(acknowledgement[key]) is int for key in ("execution_generation", "attempt_id", "handler_registration_index"))
            and all(isinstance(issuer[key], str) for key in issuer)
            and DIGEST_RE.fullmatch(acknowledgement["acknowledgement_digest"]) is not None
        )
        if not shape_ok:
            raise ProtocolFailure("acknowledgement", "malformed_input")
        if not same(acknowledgement, make_acknowledgement(request, witness)):
            raise ProtocolFailure("acknowledgement", "acknowledgement_mismatch")
        frame_active, state = False, "acknowledging"

        for event in schedule.take("before_record_commit"):
            if generic(event) or entrypoint(event):
                continue
        predicate("record", ((False, "witness_reused"), (poisoned, "reentry_attempt")))
        record = make_record(request, witness, acknowledgement)
        state = "record_committed"
        for event in schedule.take("after_record_commit"):
            if generic(event):
                continue
            if event["kind"] == "commit_record":
                require(event["value"] == record["insertion_record_digest"], "record digest assertion failed")
            elif event["kind"] == "record_commit":
                require(event["value"] == "done" and record is not None, "record commit assertion failed")
        guard_active, state = False, "dispatch_eligible"
        for event in schedule.take("after_guard_release"):
            if generic(event):
                continue
            require(event["kind"] == "provider_dispatch_eligibility" and event["value"] == "released", "guard release assertion failed")
        schedule.finish()
    except ProtocolFailure as exc:
        failure = exc
        frame_active, guard_active, state = False, False, "failed"
        for event in schedule.take("after_failure"):
            if generic(event):
                continue
            kind, value = event["kind"], event["value"]
            if kind == "settle_applied":
                require(value == "late" and deferred, "late settlement assertion failed")
            elif kind == "start_next_attempt":
                require(value == "allowed" and attempt is not None and next_attempt < MAX_INT, "next attempt was not released")
            elif kind == "record_commit":
                require(value == "forbidden" and record is None, "record committed after failure")
            elif kind in {"consume_stale_witness", "stale_api_call"}:
                require(witness_done and value == "rejected", "stale witness/API assertion failed")
                add_control("stale_invocation", "contributor_callback")
        schedule.finish()

    metadata = {
        "terminal_state": state,
        "provider_operations_before_record": provider_before_record,
        "model_operations_before_record": model_before_record,
        "control_results": controls,
    }
    if failure is not None:
        actual = {
            "accepted": False,
            "error_or_null": make_error(generation, attempt, failure.stage, failure.code),
            "request_or_null": None,
            "witness_or_null": None,
            "acknowledgement_or_null": None,
            "record_or_null": None,
        }
    else:
        require(all(value is not None for value in (request, witness, acknowledgement, record)), "incomplete accepted execution")
        actual = {
            "accepted": True,
            "error_or_null": None,
            "request_or_null": request,
            "witness_or_null": witness,
            "acknowledgement_or_null": acknowledgement,
            "record_or_null": record,
        }
    return actual, metadata
