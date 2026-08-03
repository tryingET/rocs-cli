"""Strict JSON, canonicalization, digest, and schema primitives."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
import struct
import unicodedata
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
