"""Strict offline schema substrate for Decision 103 adopted-policy v1."""
from __future__ import annotations

import json
import re
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import Any, Mapping

from rocs_cli.semantic_adopted_schema import (
    AdoptedSchemaError, load_protocol_schema, resolve_pointer,
)

MAX_ORDINARY_BYTES = 1_048_576
MAX_HISTORY_BYTES = 16_777_216
MAX_CURRENTNESS_BYTES = 33_554_432
MAX_DEPTH = 32
MAX_COLLECTION_ITEMS = 50_000
MAX_STRING_BYTES = 65_536
MAX_SAFE_INTEGER = 9_007_199_254_740_991
_DATE_TIME = re.compile(
    r"^(?P<year>[0-9]{4})-(?P<month>0[1-9]|1[0-2])-(?P<day>0[1-9]|[12][0-9]|3[01])"
    r"T(?P<hour>[01][0-9]|2[0-3]):(?P<minute>[0-5][0-9]):(?P<second>[0-5][0-9]|60)"
    r"(?:\.[0-9]+)?(?P<zone>Z|[+-][0-2][0-9]:[0-5][0-9])$"
)


class AdoptedProtocolError(ValueError):
    """Malformed, over-budget, or schema-invalid adopted-policy input."""


@dataclass(frozen=True)
class ValidationIssue:
    instance_path: str
    keyword: str
    message: str


def _pointer(token: str) -> str:
    return token.replace("~", "~0").replace("/", "~1")


def _reject_ijson(value: Any, path: str = "") -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is str:
        if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
            raise AdoptedProtocolError(f"non-scalar string at {path or '/'}")
        if len(value.encode("utf-8")) > MAX_STRING_BYTES:
            raise AdoptedProtocolError(f"string exceeds byte limit at {path or '/'}")
        return
    if type(value) is int:
        if not -MAX_SAFE_INTEGER <= value <= MAX_SAFE_INTEGER:
            raise AdoptedProtocolError(f"integer outside I-JSON range at {path or '/'}")
        return
    if type(value) is float:
        raise AdoptedProtocolError(f"floating-point value at {path or '/'}")
    if type(value) is list:
        for index, child in enumerate(value):
            _reject_ijson(child, f"{path}/{index}")
        return
    if type(value) is dict:
        for key, child in value.items():
            if type(key) is not str:
                raise AdoptedProtocolError(f"non-string key at {path or '/'}")
            _reject_ijson(key, path)
            _reject_ijson(child, f"{path}/{_pointer(key)}")
        return
    raise AdoptedProtocolError(f"unsupported JSON value at {path or '/'}")


def _decoded_string_bytes(raw: bytes, start: int, end: int) -> int:
    size = 0
    index = start
    while index < end:
        if raw[index] != 0x5C:
            size += 1
            index += 1
            continue
        if index + 1 >= end:
            return MAX_STRING_BYTES + 1
        if raw[index + 1] != 0x75 or index + 6 > end:
            size += 1
            index += 2
            continue
        try:
            code = int(raw[index + 2:index + 6].decode("ascii"), 16)
        except (UnicodeDecodeError, ValueError):
            return MAX_STRING_BYTES + 1
        if 0xD800 <= code <= 0xDBFF and index + 12 <= end and raw[index + 6:index + 8] == b"\\u":
            try:
                low = int(raw[index + 8:index + 12].decode("ascii"), 16)
            except (UnicodeDecodeError, ValueError):
                return MAX_STRING_BYTES + 1
            if 0xDC00 <= low <= 0xDFFF:
                size += 4
                index += 12
                continue
        size += len(chr(code).encode("utf-8", "surrogatepass"))
        index += 6
    return size


def _scan_structure(raw: bytes) -> None:
    items = 0
    stack: list[dict[str, Any]] = []
    in_string = escaped = False
    string_start = 0

    def mark_item() -> None:
        nonlocal items
        if stack and not stack[-1]["nonempty"]:
            stack[-1]["nonempty"] = True
            items += 1

    for index, byte in enumerate(raw):
        if in_string:
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                if _decoded_string_bytes(raw, string_start, index) > MAX_STRING_BYTES:
                    raise AdoptedProtocolError("protocol string exceeds byte limit")
                in_string = False
            continue
        if byte in b" \t\r\n":
            continue
        if byte == 0x22:
            mark_item()
            in_string = True
            string_start = index + 1
        elif byte in (0x5B, 0x7B):
            mark_item()
            stack.append({"opener": byte, "nonempty": False})
            if len(stack) > MAX_DEPTH:
                raise AdoptedProtocolError("protocol input exceeds structural limits")
        elif byte in (0x5D, 0x7D):
            if stack:
                stack.pop()
        elif byte == 0x2C and stack:
            items += 1
        else:
            mark_item()
        if items > MAX_COLLECTION_ITEMS:
            raise AdoptedProtocolError("protocol input exceeds structural limits")


def _skip_ws(raw: bytes, index: int) -> int:
    while index < len(raw) and raw[index] in b" \t\r\n":
        index += 1
    return index


def _string_end(raw: bytes, index: int) -> int:
    if index >= len(raw) or raw[index] != 0x22:
        raise AdoptedProtocolError("protocol discriminator is not a string")
    index += 1
    escaped = False
    while index < len(raw):
        byte = raw[index]
        index += 1
        if escaped:
            escaped = False
        elif byte == 0x5C:
            escaped = True
        elif byte == 0x22:
            return index
    raise AdoptedProtocolError("protocol discriminator string is unterminated")


def _string_token(raw: bytes, index: int) -> tuple[str, int]:
    end = _string_end(raw, index)
    token = raw[index:end]
    if len(token) > 1024:
        raise AdoptedProtocolError("protocol discriminator token is too large")
    try:
        value = json.loads(token.decode("utf-8", "strict"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise AdoptedProtocolError("protocol discriminator string is invalid") from exc
    if type(value) is not str:
        raise AdoptedProtocolError("protocol discriminator is not a string")
    return value, end


def _skip_value(raw: bytes, index: int) -> int:
    index = _skip_ws(raw, index)
    if index >= len(raw):
        raise AdoptedProtocolError("protocol root value is missing")
    if raw[index] == 0x22:
        return _string_end(raw, index)
    if raw[index] not in (0x5B, 0x7B):
        while index < len(raw) and raw[index] not in b",}]":
            index += 1
        return index
    stack = [raw[index]]
    index += 1
    in_string = escaped = False
    while index < len(raw) and stack:
        byte = raw[index]
        index += 1
        if in_string:
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                in_string = False
        elif byte == 0x22:
            in_string = True
        elif byte in (0x5B, 0x7B):
            stack.append(byte)
            if len(stack) > MAX_DEPTH:
                raise AdoptedProtocolError("protocol discriminator exceeds depth limit")
        elif byte in (0x5D, 0x7D):
            stack.pop()
    if stack:
        raise AdoptedProtocolError("protocol root value is unterminated")
    return index


def protocol_byte_limit(raw: bytes) -> int:
    """Select the only lawful pre-parse byte exception from a root discriminator."""
    index = _skip_ws(raw, 0)
    if index >= len(raw) or raw[index] != 0x7B:
        raise AdoptedProtocolError("protocol input is not a root object")
    index += 1
    discriminator = None
    while True:
        index = _skip_ws(raw, index)
        if index >= len(raw):
            raise AdoptedProtocolError("protocol root object is unterminated")
        if raw[index] == 0x7D:
            break
        key, index = _string_token(raw, index)
        index = _skip_ws(raw, index)
        if index >= len(raw) or raw[index] != 0x3A:
            raise AdoptedProtocolError("protocol root property lacks a colon")
        index = _skip_ws(raw, index + 1)
        if key == "schema":
            if discriminator is not None:
                raise AdoptedProtocolError("protocol input has duplicate schema keys")
            discriminator, index = _string_token(raw, index)
        else:
            index = _skip_value(raw, index)
        index = _skip_ws(raw, index)
        if index < len(raw) and raw[index] == 0x2C:
            index += 1
            continue
        if index < len(raw) and raw[index] == 0x7D:
            break
        raise AdoptedProtocolError("protocol root property separator is invalid")
    if discriminator == "semantic-routing-policy-publication-history.v1":
        return MAX_HISTORY_BYTES
    if discriminator == "semantic-routing-policy-currentness-proof.v1":
        return MAX_CURRENTNESS_BYTES
    return MAX_ORDINARY_BYTES


def strict_json_loads(raw: bytes, *, max_bytes: int = MAX_ORDINARY_BYTES) -> Any:
    """Parse duplicate-free integer-only I-JSON under an explicit byte ceiling."""
    if type(raw) is not bytes:
        raise AdoptedProtocolError("protocol input must be bytes")
    if len(raw) > max_bytes:
        raise AdoptedProtocolError("protocol input exceeds byte limit")
    _scan_structure(raw)
    try:
        text = raw.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise AdoptedProtocolError("protocol input is not UTF-8") from exc

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise AdoptedProtocolError("protocol input has duplicate keys")
            result[key] = value
        return result

    def integer(token: str) -> int:
        if re.fullmatch(r"0|-?[1-9][0-9]*", token) is None:
            raise AdoptedProtocolError("protocol input has a non-canonical integer")
        return int(token)

    def reject(token: str) -> Any:
        raise AdoptedProtocolError(f"protocol input has a forbidden number: {token}")

    try:
        value = json.loads(
            text, object_pairs_hook=pairs, parse_int=integer,
            parse_float=reject, parse_constant=reject,
        )
    except (json.JSONDecodeError, RecursionError) as exc:
        raise AdoptedProtocolError("protocol input is not valid JSON") from exc
    _reject_ijson(value)
    return value


def _quoted(value: str) -> str:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def jcs_bytes(value: Any) -> bytes:
    """RFC 8785 bytes for the protocol's integer-only I-JSON profile."""
    _reject_ijson(value)

    def encode(item: Any) -> str:
        if item is None:
            return "null"
        if item is True:
            return "true"
        if item is False:
            return "false"
        if type(item) is int:
            return str(item)
        if type(item) is str:
            return _quoted(item)
        if type(item) is list:
            return "[" + ",".join(encode(child) for child in item) + "]"
        keys = sorted(item, key=lambda key: key.encode("utf-16-be"))
        return "{" + ",".join(f"{_quoted(key)}:{encode(item[key])}" for key in keys) + "}"

    return encode(value).encode("utf-8")

def _same(left: Any, right: Any) -> bool:
    return type(left) is type(right) and left == right

def _type_matches(instance: Any, expected: Any) -> bool:
    if type(expected) is list:
        return any(_type_matches(instance, choice) for choice in expected)
    return {
        "object": type(instance) is dict,
        "array": type(instance) is list,
        "string": type(instance) is str,
        "integer": type(instance) is int,
        "boolean": type(instance) is bool,
        "null": instance is None,
    }.get(expected, True)

def _date_time_valid(value: str) -> bool:
    match = _DATE_TIME.fullmatch(value)
    if match is None:
        return False
    zone = match.group("zone")
    if zone != "Z" and int(zone[1:3]) > 23:
        return False
    leap = match.group("second") == "60"
    if leap and not (
        zone == "Z" and match.group("hour") == "23" and match.group("minute") == "59"
        and (match.group("month"), match.group("day")) in {("06", "30"), ("12", "31")}
    ):
        return False
    candidate = value.replace(":60", ":59", 1) if leap else value
    try:
        parsed = candidate[:-1] + "+00:00" if candidate.endswith("Z") else candidate
        datetime.fromisoformat(parsed)
    except ValueError:
        return False
    return True


def _pattern_matches(pattern: str, value: str) -> bool:
    match = re.search(pattern, value)
    return match is not None and (not pattern.endswith("$") or match.end() == len(value))

def _validate(instance: Any, schema: Any, root: dict[str, Any], path: str) -> list[ValidationIssue]:
    if schema is True:
        return []
    if schema is False or type(schema) is not dict:
        return [ValidationIssue(path, "schema", "instance is forbidden")]
    issues: list[ValidationIssue] = []
    reference = schema.get("$ref")
    if reference is not None:
        try:
            target = resolve_pointer(root, reference)
        except AdoptedSchemaError:
            return [ValidationIssue(path, "$ref", "schema reference is unresolved")]
        issues.extend(_validate(instance, target, root, path))
        if reference == "#/$defs/path" and type(instance) is str and len(instance.encode("utf-8")) > 1024:
            issues.append(ValidationIssue(path, "maxBytes", "path exceeds UTF-8 byte limit"))
    for branch in schema.get("allOf", []):
        issues.extend(_validate(instance, branch, root, path))
    if "oneOf" in schema:
        matches = sum(not _validate(instance, branch, root, path) for branch in schema["oneOf"])
        if matches != 1:
            issues.append(ValidationIssue(path, "oneOf", "instance must match exactly one branch"))
    condition = schema.get("if")
    if condition is not None and not _validate(instance, condition, root, path) and "then" in schema:
        issues.extend(_validate(instance, schema["then"], root, path))
    if "const" in schema and not _same(instance, schema["const"]):
        issues.append(ValidationIssue(path, "const", "instance differs from required constant"))
    if "enum" in schema and not any(_same(instance, choice) for choice in schema["enum"]):
        issues.append(ValidationIssue(path, "enum", "instance is outside the closed enumeration"))
    expected = schema.get("type")
    if expected is not None and not _type_matches(instance, expected):
        issues.append(ValidationIssue(path, "type", "instance has the wrong type"))
        return issues
    if type(instance) is dict:
        properties = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in instance:
                issues.append(ValidationIssue(path, "required", f"missing property: {key}"))
        if schema.get("additionalProperties") is False:
            for key in instance:
                if key not in properties:
                    issues.append(ValidationIssue(path, "additionalProperties", f"forbidden property: {key}"))
        for key, child_schema in properties.items():
            if key in instance:
                issues.extend(_validate(instance[key], child_schema, root, f"{path}/{_pointer(key)}"))
    elif type(instance) is list:
        if len(instance) < schema.get("minItems", 0):
            issues.append(ValidationIssue(path, "minItems", "array has too few items"))
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            issues.append(ValidationIssue(path, "maxItems", "array has too many items"))
        if schema.get("uniqueItems"):
            encoded = [jcs_bytes(child) for child in instance]
            if len(encoded) != len(set(encoded)):
                issues.append(ValidationIssue(path, "uniqueItems", "array items are not unique"))
        prefix = schema.get("prefixItems", [])
        for index, child_schema in enumerate(prefix[:len(instance)]):
            issues.extend(_validate(instance[index], child_schema, root, f"{path}/{index}"))
        item_schema = schema.get("items")
        if item_schema is False and len(instance) > len(prefix):
            issues.append(ValidationIssue(path, "items", "array has forbidden trailing items"))
        elif item_schema not in (None, False):
            start = len(prefix) if prefix else 0
            for index in range(start, len(instance)):
                issues.extend(_validate(instance[index], item_schema, root, f"{path}/{index}"))
    elif type(instance) is str:
        if len(instance) < schema.get("minLength", 0):
            issues.append(ValidationIssue(path, "minLength", "string is too short"))
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            issues.append(ValidationIssue(path, "maxLength", "string is too long"))
        if "pattern" in schema and not _pattern_matches(schema["pattern"], instance):
            issues.append(ValidationIssue(path, "pattern", "string does not match pattern"))
        if schema.get("format") == "date-time" and not _date_time_valid(instance):
            issues.append(ValidationIssue(path, "format", "string is not an RFC 3339 date-time"))
    elif type(instance) is int:
        if instance < schema.get("minimum", instance):
            issues.append(ValidationIssue(path, "minimum", "integer is below minimum"))
        if instance > schema.get("maximum", instance):
            issues.append(ValidationIssue(path, "maximum", "integer is above maximum"))
    return issues


@lru_cache(maxsize=1)
def schema_definitions() -> Mapping[str, str]:
    root = load_protocol_schema()
    result: dict[str, str] = {}
    for branch in root["oneOf"]:
        reference = branch.get("$ref") if type(branch) is dict else None
        if type(reference) is not str or not reference.startswith("#/$defs/"):
            raise AdoptedProtocolError("root protocol branch is not a definition reference")
        name = reference.removeprefix("#/$defs/").split("/", 1)[0]
        definition = root["$defs"][name]
        constant = definition.get("properties", {}).get("schema", {}).get("const")
        if type(constant) is not str or constant in result:
            raise AdoptedProtocolError("ambiguous schema discriminator")
        result[constant] = name
    if len(result) != 54:
        raise AdoptedProtocolError("schema discriminator inventory mismatch")
    return result


def validate_definition(instance: Any, definition: str) -> tuple[ValidationIssue, ...]:
    _reject_ijson(instance)
    root = load_protocol_schema()
    selected = root["$defs"].get(definition)
    if type(selected) is not dict:
        raise AdoptedProtocolError("unknown protocol definition")
    issues = list(_validate(instance, selected, root, ""))
    if definition == "path" and type(instance) is str and len(instance.encode("utf-8")) > 1024:
        issues.append(ValidationIssue("", "maxBytes", "path exceeds UTF-8 byte limit"))
    return tuple(issues)


def validate_protocol(instance: Any) -> tuple[ValidationIssue, ...]:
    if type(instance) is not dict:
        return (ValidationIssue("", "type", "protocol instance must be an object"),)
    discriminator = instance.get("schema")
    definitions = schema_definitions()
    if type(discriminator) is not str or discriminator not in definitions:
        return (ValidationIssue("/schema", "const", "unsupported protocol schema"),)
    return validate_definition(instance, definitions[discriminator])


def validate_protocol_bytes(raw: bytes) -> tuple[dict[str, Any], tuple[ValidationIssue, ...]]:
    if type(raw) is not bytes or len(raw) > MAX_CURRENTNESS_BYTES:
        raise AdoptedProtocolError("protocol input exceeds absolute byte limit")
    _scan_structure(raw)
    limit = protocol_byte_limit(raw)
    value = strict_json_loads(raw, max_bytes=limit)
    if type(value) is not dict:
        raise AdoptedProtocolError("protocol instance must be an object")
    snapshot = strict_json_loads(jcs_bytes(deepcopy(value)), max_bytes=limit)
    return snapshot, validate_protocol(snapshot)
