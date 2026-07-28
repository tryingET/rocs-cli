#!/usr/bin/env python3
"""Independent stdlib conformance runner for Decision 85 insertion evidence."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
import struct
import sys
import unicodedata
from pathlib import Path
from typing import Any

MAX_INT = 9_007_199_254_740_991
REVISION = "semantic-pi-insertion-evidence-v1-r1"
VECTOR_SHA256 = "e23437e075f49c36e7487deeec2ab8126cd8fb14c0dbf07bf48d17e466525ed4"
FROZEN_AGGREGATE = "272c892af593ff10ddb056b1914f20372308fe8a47ca28b3ca04ca8e27882991"
ACCEPTED_AGGREGATE = "e1a715cd868bdd9807eecb798b29ac02342697cc2afd9ac8eb7d9b6296b97a7e"
SCHEMA_NAMES = (
    "semantic-pi-insertion-request.v1",
    "pi.prompt-chain-application-witness.v1",
    "semantic-pi-insertion-acknowledgement.v1",
    "pi.prompt-chain-insertion-record.v1",
    "semantic-pi-insertion-error.v1",
    "semantic-pi-insertion-vector-set.v1",
)
DOMAINS = (
    "semantic-pi-insertion.request.v1",
    "pi.prompt-chain-application-witness.v1",
    "semantic-pi-insertion.acknowledgement.v1",
    "pi.prompt-chain-insertion-record.v1",
    "semantic-pi-insertion.error.v1",
    "semantic-pi-insertion.input-prompt-bytes.v1",
    "semantic-pi-insertion.contribution-bytes.v1",
    "pi.prompt-chain-bytes.v1",
)
OBJECT_DOMAINS = {
    SCHEMA_NAMES[0]: (DOMAINS[0], "request_digest"),
    SCHEMA_NAMES[1]: (DOMAINS[1], "witness_digest"),
    SCHEMA_NAMES[2]: (DOMAINS[2], "acknowledgement_digest"),
    SCHEMA_NAMES[3]: (DOMAINS[3], "insertion_record_digest"),
    SCHEMA_NAMES[4]: (DOMAINS[4], "error_digest"),
}
HOOKS = (
    "before_reservation",
    "after_reservation",
    "during_prepare",
    "after_prepare",
    "before_apply",
    "after_apply",
    "after_assignment",
    "after_readback",
    "before_witness",
    "after_witness",
    "during_applied",
    "after_applied",
    "before_record_commit",
    "after_record_commit",
    "after_guard_release",
    "after_failure",
)
DIGEST_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")
ID_RE = re.compile(r"[a-z][a-z0-9-]*\Z")
DECIMAL_RE = re.compile(r"(?:0|[1-9][0-9]*)\Z")
SPAN_RE = re.compile(r"(0|[1-9][0-9]*):(0|[1-9][0-9]*)\Z")


class ConformanceError(Exception):
    pass


class StrictJSONError(ConformanceError):
    pass


class ProtocolFailure(Exception):
    def __init__(self, stage: str, code: str) -> None:
        self.stage = stage
        self.code = code


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ConformanceError(message)


def valid_scalar_text(value: str) -> bool:
    if unicodedata.normalize("NFC", value) != value:
        return False
    return all(not (0xD800 <= ord(ch) <= 0xDFFF or 0xFDD0 <= ord(ch) <= 0xFDEF or ord(ch) & 0xFFFF in (0xFFFE, 0xFFFF)) for ch in value)


def strict_json_loads(raw: bytes, label: str) -> Any:
    if raw.startswith(b"\xef\xbb\xbf"):
        raise StrictJSONError(f"{label}: BOM is forbidden")

    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in rows:
            if key in result:
                raise StrictJSONError(f"{label}: duplicate key {key!r}")
            result[key] = value
        return result

    def integer(token: str) -> int:
        value = int(token)
        if not 0 <= value <= MAX_INT:
            raise StrictJSONError(f"{label}: integer outside I-JSON range")
        return value

    def forbidden_number(_: str) -> None:
        raise StrictJSONError(f"{label}: non-integer number is forbidden")

    try:
        text = raw.decode("utf-8", "strict")
        value = json.loads(
            text,
            object_pairs_hook=pairs,
            parse_int=integer,
            parse_float=forbidden_number,
            parse_constant=forbidden_number,
        )
    except StrictJSONError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StrictJSONError(f"{label}: invalid strict JSON: {exc}") from exc

    def visit(item: Any) -> None:
        if isinstance(item, str):
            if not valid_scalar_text(item):
                raise StrictJSONError(f"{label}: string is not an NFC Unicode scalar string")
        elif isinstance(item, list):
            for child in item:
                visit(child)
        elif isinstance(item, dict):
            for key, child in item.items():
                visit(key)
                visit(child)

    visit(value)
    return value


def jcs_bytes(value: Any) -> bytes:
    def render(item: Any) -> str:
        if item is None:
            return "null"
        if item is True:
            return "true"
        if item is False:
            return "false"
        if type(item) is int and 0 <= item <= MAX_INT:
            return str(item)
        if isinstance(item, str) and valid_scalar_text(item):
            return json.dumps(item, ensure_ascii=False, separators=(",", ":"))
        if isinstance(item, list):
            return "[" + ",".join(render(child) for child in item) + "]"
        if isinstance(item, dict) and all(isinstance(key, str) and valid_scalar_text(key) for key in item):
            keys = sorted(item, key=lambda key: key.encode("utf-16-be"))
            return "{" + ",".join(f"{render(key)}:{render(item[key])}" for key in keys) + "}"
        raise ConformanceError("value is outside the restricted JCS profile")

    return render(value).encode("utf-8")


def object_digest(domain: str, value: dict[str, Any], self_field: str) -> str:
    preimage = {key: child for key, child in value.items() if key != self_field}
    return "sha256:" + hashlib.sha256(domain.encode() + b"\0" + jcs_bytes(preimage)).hexdigest()


def raw_digest(domain: str, raw: bytes) -> str:
    preimage = domain.encode() + b"\0" + struct.pack(">Q", len(raw)) + raw
    return "sha256:" + hashlib.sha256(preimage).hexdigest()


def canonical_base64(value: Any, label: str) -> bytes:
    require(isinstance(value, str), f"{label}: base64 value must be a string")
    try:
        raw = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ConformanceError(f"{label}: invalid base64") from exc
    require(base64.b64encode(raw).decode("ascii") == value, f"{label}: base64 is not canonical padded standard base64")
    return raw


def snapshot_text(raw: bytes, minimum: int, maximum: int) -> bool:
    if not minimum <= len(raw) <= maximum:
        return False
    try:
        value = raw.decode("utf-8", "strict")
    except UnicodeDecodeError:
        return False
    return valid_scalar_text(value) and value.encode("utf-8") == raw


def same(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, list):
        return len(left) == len(right) and all(same(a, b) for a, b in zip(left, right, strict=True))
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(same(left[key], right[key]) for key in left)
    return left == right


def resolve_ref(root: dict[str, Any], ref: str) -> Any:
    require(ref.startswith("#/"), f"non-local schema reference: {ref}")
    value: Any = root
    for token in ref[2:].split("/"):
        key = token.replace("~1", "/").replace("~0", "~")
        require(isinstance(value, dict) and key in value, f"unresolved local schema reference: {ref}")
        value = value[key]
    return value


def schema_matches(instance: Any, schema: dict[str, Any], root: dict[str, Any]) -> bool:
    if "$ref" in schema:
        return schema_matches(instance, resolve_ref(root, schema["$ref"]), root)
    if "oneOf" in schema and sum(schema_matches(instance, choice, root) for choice in schema["oneOf"]) != 1:
        return False
    if "const" in schema and not same(instance, schema["const"]):
        return False
    if "enum" in schema and not any(same(instance, choice) for choice in schema["enum"]):
        return False
    kind = schema.get("type")
    checks = {
        "null": instance is None,
        "boolean": type(instance) is bool,
        "integer": type(instance) is int,
        "string": isinstance(instance, str),
        "array": isinstance(instance, list),
        "object": isinstance(instance, dict),
    }
    if kind is not None and not checks.get(kind, False):
        return False
    if type(instance) is int and (instance < schema.get("minimum", instance) or instance > schema.get("maximum", instance)):
        return False
    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0) or len(instance) > schema.get("maxLength", len(instance)):
            return False
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            return False
    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0) or len(instance) > schema.get("maxItems", len(instance)):
            return False
        if "items" in schema and not all(schema_matches(child, schema["items"], root) for child in instance):
            return False
    if isinstance(instance, dict) and ("properties" in schema or "required" in schema):
        properties = schema.get("properties", {})
        if any(key not in instance for key in schema.get("required", [])):
            return False
        if schema.get("additionalProperties") is False and any(key not in properties for key in instance):
            return False
        if any(key in instance and not schema_matches(instance[key], child, root) for key, child in properties.items()):
            return False
    return True


def inspect_schema(schema: dict[str, Any]) -> None:
    require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", "schema draft mismatch")
    require(tuple(schema.get("$defs", {})) == SCHEMA_NAMES, "bundle must have exactly the six named top-level schemas")
    require(tuple(schema.get("x-digest-domains", ())) == DOMAINS, "bundle must declare exactly the eight closed domains")
    refs = tuple(choice.get("$ref") for choice in schema.get("oneOf", ()))
    require(refs == tuple(f"#/$defs/{name}" for name in SCHEMA_NAMES), "root schema union mismatch")

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            if "$ref" in value:
                resolve_ref(schema, value["$ref"])
            if value.get("type") == "object":
                require(value.get("additionalProperties") is False, "every object schema must be closed")
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(schema)


COMMON_COMPAT: dict[str, set[str]] = {
    "reserve": {"after_reservation"},
    "prepare_return_base64": {"during_prepare"},
    "apply_span": {"after_apply"},
    "assign_base64": {"after_assignment"},
    "readback_base64": {"after_readback"},
    "issue_witness": {"after_witness"},
    "applied_return_digest": {"after_applied"},
    "commit_record": {"after_record_commit"},
    "abort_signal": {hook for hook in HOOKS if hook.startswith(("before_", "during_"))},
    "replace_ack_issuer": {"after_applied"},
    "inject_ack_bytes_base64": {"after_applied"},
    "invoke_nested_prompt": {"during_applied"},
    "reserve_attempt_override": {"before_reservation"},
    "replace_registration_component_id": {"before_reservation"},
    "advance_monotonic_ns": set(HOOKS),
    "reload_generation": set(HOOKS),
    "clone_witness_json": {"before_witness", "after_witness"},
    "consume_witness_twice": {"during_applied"},
}
FIXTURE_COMPAT: dict[str, set[str]] = {
    "prompt_attempt": {"during_applied", "before_record_commit"},
    "continuation_attempt": {"during_applied", "before_record_commit"},
    "completion_attempt": {"during_applied", "before_record_commit"},
    "provider_dispatch_attempt": {"during_applied", "before_record_commit"},
    "model_invocation_attempt": {"during_applied", "before_record_commit"},
    "contributor_callback_attempt": {"during_applied", "before_record_commit"},
    "stale_api_call": {"after_failure"},
    "detached_callback_call": {"during_applied"},
    "provider_dispatch_eligibility": {"after_guard_release"},
    "applied_throw": {"during_applied"},
    "record_commit": {"after_record_commit", "after_failure"},
    "create_registration_b": {"before_reservation"},
    "consume_from_registration_b": {"during_applied"},
    "consume_stale_witness": {"after_failure"},
    "defer_applied": {"during_applied"},
    "settle_applied": {"after_failure"},
    "start_next_attempt": {"after_failure"},
    "assign": {"after_assignment"},
    "readback": {"after_readback"},
    "witness_issued": {"after_witness"},
}
EXACT_VALUES = {
    "abort_signal": {"set"},
    "replace_ack_issuer": {"other-component"},
    "replace_registration_component_id": {"pi-adapter"},
    "invoke_nested_prompt": {"attempt"},
    "clone_witness_json": {"true"},
    "consume_witness_twice": {"true"},
    "stale_api_call": {"rejected"},
    "detached_callback_call": {"rejected"},
    "provider_dispatch_eligibility": {"released"},
    "applied_throw": {"error"},
    "create_registration_b": {"other-component"},
    "consume_from_registration_b": {"rejected"},
    "consume_stale_witness": {"rejected"},
    "defer_applied": {"pending"},
    "settle_applied": {"late"},
    "start_next_attempt": {"allowed"},
    "assign": {"done"},
    "readback": {"verified"},
    "witness_issued": {"after_assign", "after_readback", "generation0"},
}


class Schedule:
    def __init__(self, events: Any, fixture: bool) -> None:
        require(isinstance(events, list) and 1 <= len(events) <= 64, "events must contain 1..64 rows")
        compat = dict(COMMON_COMPAT)
        if fixture:
            compat.update(FIXTURE_COMPAT)
        self.events = events
        self.used: set[int] = set()
        seen: set[tuple[str, str]] = set()
        positions: list[int] = []
        for event in events:
            require(isinstance(event, dict) and set(event) == {"at_hook", "kind", "value"}, "invalid event row")
            hook, kind, value = event["at_hook"], event["kind"], event["value"]
            require(isinstance(hook, str) and isinstance(kind, str) and isinstance(value, str), "event fields must be strings")
            require(kind in compat and hook in compat[kind], f"hook-incompatible or unknown event: {hook}/{kind}")
            require((hook, kind) not in seen, f"duplicate event pair: {hook}/{kind}")
            seen.add((hook, kind))
            positions.append(HOOKS.index(hook))
            self._validate_value(kind, value)
            if fixture:
                self._validate_fixture_combination(hook, kind, value)
        require(positions == sorted(positions), "events are not in hook order")

    @staticmethod
    def _validate_value(kind: str, value: str) -> None:
        if kind in {"reserve", "reserve_attempt_override", "advance_monotonic_ns", "reload_generation"}:
            require(DECIMAL_RE.fullmatch(value) is not None and int(value) <= MAX_INT, f"invalid decimal event value: {kind}")
        elif kind in {"prepare_return_base64", "assign_base64", "readback_base64", "inject_ack_bytes_base64"}:
            canonical_base64(value, kind)
        elif kind == "apply_span":
            match = SPAN_RE.fullmatch(value)
            require(match is not None and all(int(part) <= MAX_INT for part in match.groups()), "invalid apply span")
        elif kind in {"issue_witness", "applied_return_digest", "commit_record"}:
            require(DIGEST_RE.fullmatch(value) is not None, f"invalid digest assertion: {kind}")
        elif kind in EXACT_VALUES:
            require(value in EXACT_VALUES[kind], f"invalid event value: {kind}={value}")
        elif kind == "record_commit":
            require(value in {"done", "forbidden"}, "invalid record_commit value")
        elif kind.endswith("_attempt"):
            allowed = {"blocked", "reentry", "stale"} if kind == "contributor_callback_attempt" else {"blocked", "reentry"}
            require(value in allowed, f"invalid entrypoint event value: {kind}={value}")
        else:
            require(bool(value), f"empty event value: {kind}")

    @staticmethod
    def _validate_fixture_combination(hook: str, kind: str, value: str) -> None:
        entrypoints = {
            "prompt_attempt", "continuation_attempt", "completion_attempt",
            "provider_dispatch_attempt", "model_invocation_attempt", "contributor_callback_attempt",
        }
        if kind in entrypoints:
            expected_hook = "before_record_commit" if value == "blocked" else "during_applied"
            require(hook == expected_hook, f"hook-incompatible fixture event: {hook}/{kind}={value}")
        elif kind == "record_commit":
            expected_hook = "after_record_commit" if value == "done" else "after_failure"
            require(hook == expected_hook, f"hook-incompatible fixture event: {hook}/{kind}={value}")

    def take(self, hook: str) -> list[dict[str, str]]:
        rows = []
        for index, event in enumerate(self.events):
            if event["at_hook"] == hook:
                require(index not in self.used, f"event consumed twice at {hook}")
                self.used.add(index)
                rows.append(event)
        return rows

    def finish(self) -> None:
        require(len(self.used) == len(self.events), "unreachable or unused event")


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


def frozen_aggregate(repo: Path) -> str:
    names = sorted(
        (
            "docs/project/semantic-pi-insertion-evidence-v1-problem-brief.md",
            "docs/project/semantic-pi-insertion-evidence-v1-evidence-note.md",
            "docs/project/semantic-pi-insertion-evidence-v1-rfc.md",
            "docs/project/semantic-pi-insertion-evidence-v1-review-set-plan.md",
            "docs/project/semantic-pi-insertion-evidence-v1-vectors.json",
        ),
        key=lambda name: name.encode(),
    )
    rows = bytearray()
    for name in names:
        raw = (repo / name).read_bytes()
        rows.extend(f"{name}\t{len(raw)}\t{hashlib.sha256(raw).hexdigest()}\n".encode())
    return hashlib.sha256(rows).hexdigest()


def validate_shells(vectors: dict[str, Any]) -> None:
    require(set(vectors) == {"schema", "protocol_revision", "cases", "host_fixtures", "accepted_object_aggregate_sha256"}, "vector root keys mismatch")
    require(vectors["schema"] == SCHEMA_NAMES[5] and vectors["protocol_revision"] == REVISION, "vector identity mismatch")
    require(isinstance(vectors["cases"], list) and len(vectors["cases"]) == 16, "case count mismatch")
    require(isinstance(vectors["host_fixtures"], list) and len(vectors["host_fixtures"]) == 13, "host fixture count mismatch")
    case_keys = {
        "id", "input_bytes_base64", "contribution_bytes_base64", "initial_generation", "initial_next_attempt_id",
        "handler_registration_index", "deadline_monotonic_ns", "events", "expected",
    }
    fixture_keys = {
        "id", "baseline_case_id", "events", "expected_terminal_state", "expected_provider_operations_before_record",
        "expected_model_operations_before_record", "expected_control_results",
    }
    for case in vectors["cases"]:
        require(isinstance(case, dict) and set(case) == case_keys and ID_RE.fullmatch(case["id"]) is not None, "invalid case shell")
    for fixture in vectors["host_fixtures"]:
        require(isinstance(fixture, dict) and set(fixture) == fixture_keys and ID_RE.fullmatch(fixture["id"]) is not None, "invalid fixture shell")
    for values, label in ((vectors["cases"], "case"), (vectors["host_fixtures"], "fixture")):
        ids = [item["id"] for item in values]
        require(len(ids) == len(set(ids)) and ids == sorted(ids, key=lambda value: value.encode()), f"{label} IDs are not unique ASCII-sorted IDs")


def main() -> int:
    packet = Path(__file__).resolve().parent
    repo = packet.parents[2]
    vector_path = packet.parent / "semantic-pi-insertion-evidence-v1-vectors.json"
    schema = strict_json_loads((packet / "protocol.schema.json").read_bytes(), "protocol.schema.json")
    vectors_raw = vector_path.read_bytes()
    vectors = strict_json_loads(vectors_raw, vector_path.name)
    require(isinstance(schema, dict) and isinstance(vectors, dict), "schema and vectors must be JSON objects")
    inspect_schema(schema)
    validate_shells(vectors)

    case_runs: list[tuple[str, dict[str, Any]]] = []
    case_inputs: dict[str, dict[str, Any]] = {}
    core = (
        "input_bytes_base64", "contribution_bytes_base64", "initial_generation", "initial_next_attempt_id",
        "handler_registration_index", "deadline_monotonic_ns", "events",
    )
    for case in vectors["cases"]:
        execution_input = {key: case[key] for key in core}
        actual, _ = run_attempt(execution_input, False)
        case_runs.append((case["id"], actual))
        case_inputs[case["id"]] = execution_input

    fixture_runs: list[tuple[str, dict[str, Any]]] = []
    for fixture in vectors["host_fixtures"]:
        baseline = case_inputs.get(fixture["baseline_case_id"])
        require(baseline is not None, "host fixture baseline does not exist")
        execution_input = dict(baseline)
        execution_input["events"] = fixture["events"]
        _, metadata = run_attempt(execution_input, True)
        fixture_runs.append((fixture["id"], metadata))

    vector_schema = schema["$defs"][SCHEMA_NAMES[5]]
    require(schema_matches(vectors, vector_schema, schema), "frozen vector set does not satisfy protocol schema")
    cases_by_id = {case["id"]: case for case in vectors["cases"]}
    fixtures_by_id = {fixture["id"]: fixture for fixture in vectors["host_fixtures"]}
    for case_id, actual in case_runs:
        expected = cases_by_id[case_id]["expected"]
        require(same(actual, expected), f"case result mismatch: {case_id}")
        for value in actual.values():
            if isinstance(value, dict) and value.get("schema") in OBJECT_DOMAINS:
                name = value["schema"]
                require(schema_matches(value, schema["$defs"][name], schema), f"actual object schema mismatch: {case_id}/{name}")
                domain, self_field = OBJECT_DOMAINS[name]
                require(value[self_field] == object_digest(domain, value, self_field), f"actual object digest mismatch: {case_id}/{name}")
    for fixture_id, actual in fixture_runs:
        expected_source = fixtures_by_id[fixture_id]
        expected = {
            "terminal_state": expected_source["expected_terminal_state"],
            "provider_operations_before_record": expected_source["expected_provider_operations_before_record"],
            "model_operations_before_record": expected_source["expected_model_operations_before_record"],
            "control_results": expected_source["expected_control_results"],
        }
        require(same(actual, expected), f"host fixture result mismatch: {fixture_id}")

    accepted = sorted(((case_id, value) for case_id, value in case_runs if value["accepted"]), key=lambda row: row[0].encode())
    aggregate_bytes = b"".join(
        jcs_bytes(value[field])
        for _, value in accepted
        for field in ("request_or_null", "witness_or_null", "acknowledgement_or_null", "record_or_null")
    )
    accepted_hash = hashlib.sha256(aggregate_bytes).hexdigest()
    vector_hash = hashlib.sha256(vectors_raw).hexdigest()
    frozen_hash = frozen_aggregate(repo)
    require(len(accepted) == 3, "accepted case count mismatch")
    require(accepted_hash == vectors["accepted_object_aggregate_sha256"] == ACCEPTED_AGGREGATE, "accepted-object aggregate mismatch")
    require(vector_hash == VECTOR_SHA256, "frozen vector SHA-256 mismatch")
    require(frozen_hash == FROZEN_AGGREGATE, "frozen five-file aggregate mismatch")
    tools = strict_json_loads((repo / "scripts/tool_versions.json").read_bytes(), "tool_versions.json")
    require(isinstance(tools, dict) and tools.get("node") == "26.1.0", "Node validator pin must be exactly 26.1.0")
    report = {
        "accepted_cases": len(accepted),
        "accepted_object_aggregate_sha256": accepted_hash,
        "cases": len(case_runs),
        "digest_domains": len(DOMAINS),
        "frozen_aggregate_sha256": frozen_hash,
        "host_fixtures": len(fixture_runs),
        "implementation": "python-stdlib-independent",
        "node_pin": tools["node"],
        "schema_count": len(SCHEMA_NAMES),
        "unused_events": 0,
        "vector_sha256": vector_hash,
    }
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ConformanceError, StrictJSONError, OSError) as exc:
        print(f"semantic-pi-insertion conformance failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
