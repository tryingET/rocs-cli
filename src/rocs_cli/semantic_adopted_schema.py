"""Integrity-checked packaged schema for Decision 103 adopted-policy v1."""
from __future__ import annotations

import hashlib
import json
import zlib
from copy import deepcopy
from functools import lru_cache
from importlib.resources import files
from typing import Any

SCHEMA_ID = "urn:rocs:semantic-router-adopted-policy-v1"
SCHEMA_DRAFT = "https://json-schema.org/draft/2020-12/schema"
SCHEMA_BYTE_LENGTH = 323_224
SCHEMA_SHA256 = "5940be962e14f881f554a68bd9ba669f8a40d891228ac310dfd9a1a67f8a934f"
COMPRESSED_BYTE_LENGTH = 18_346
COMPRESSED_SHA256 = "47cf3f474c1a655595b0e90d192568ec8e99ab950ed4ad2d7bdfef86414c4d42"
EXPECTED_DEFINITIONS = 69
EXPECTED_REFERENCES = 1_115
EXPECTED_ROOT_BRANCHES = 54
ASSET_NAME = "_bootstrap_assets/semantic-router-adopted-policy-v1.schema.zlib"


class AdoptedSchemaError(ValueError):
    """Packaged schema is missing, corrupt, ambiguous, or incompatible."""


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


@lru_cache(maxsize=1)
def schema_bytes() -> bytes:
    compressed = files("rocs_cli").joinpath(ASSET_NAME).read_bytes()
    if len(compressed) != COMPRESSED_BYTE_LENGTH or _sha256(compressed) != COMPRESSED_SHA256:
        raise AdoptedSchemaError("packaged adopted-policy schema asset mismatch")
    decoder = zlib.decompressobj()
    raw = decoder.decompress(compressed, SCHEMA_BYTE_LENGTH + 1)
    raw += decoder.flush()
    if (
        len(raw) != SCHEMA_BYTE_LENGTH
        or _sha256(raw) != SCHEMA_SHA256
        or not decoder.eof
        or decoder.unused_data
        or decoder.unconsumed_tail
    ):
        raise AdoptedSchemaError("packaged adopted-policy schema bytes mismatch")
    return raw


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        if key in result:
            raise AdoptedSchemaError("packaged schema contains a duplicate key")
        result[key] = value
    return result


def resolve_pointer(root: Any, reference: str) -> Any:
    if not reference.startswith("#/"):
        raise AdoptedSchemaError("packaged schema contains a non-local reference")
    current = root
    for raw in reference[2:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if type(current) is not dict or token not in current:
            raise AdoptedSchemaError("packaged schema contains an unresolved reference")
        current = current[token]
    return current


def _references(value: Any) -> list[str]:
    found: list[str] = []
    if type(value) is dict:
        reference = value.get("$ref")
        if reference is not None:
            if type(reference) is not str:
                raise AdoptedSchemaError("packaged schema reference is not a string")
            found.append(reference)
        for child in value.values():
            found.extend(_references(child))
    elif type(value) is list:
        for child in value:
            found.extend(_references(child))
    return found


def _definition_graph(root: dict[str, Any]) -> dict[str, set[str]]:
    definitions = root["$defs"]
    graph: dict[str, set[str]] = {name: set() for name in definitions}
    for name, definition in definitions.items():
        for reference in _references(definition):
            if reference.startswith("#/$defs/"):
                target = reference.removeprefix("#/$defs/").split("/", 1)[0]
                if target not in definitions:
                    raise AdoptedSchemaError("definition graph has an unknown target")
                graph[name].add(target)
    return graph


def _assert_acyclic(graph: dict[str, set[str]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(name: str) -> None:
        if name in visiting:
            raise AdoptedSchemaError("definition reference graph is cyclic")
        if name in visited:
            return
        visiting.add(name)
        for target in graph[name]:
            visit(target)
        visiting.remove(name)
        visited.add(name)

    for name in graph:
        visit(name)


@lru_cache(maxsize=1)
def _schema_root() -> dict[str, Any]:
    try:
        root = json.loads(schema_bytes(), object_pairs_hook=_pairs)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise AdoptedSchemaError("packaged schema is not duplicate-free UTF-8 JSON") from exc
    if (
        type(root) is not dict
        or root.get("$schema") != SCHEMA_DRAFT
        or root.get("$id") != SCHEMA_ID
        or type(root.get("$defs")) is not dict
        or len(root["$defs"]) != EXPECTED_DEFINITIONS
        or type(root.get("oneOf")) is not list
        or len(root["oneOf"]) != EXPECTED_ROOT_BRANCHES
    ):
        raise AdoptedSchemaError("packaged schema identity or inventory mismatch")
    references = _references(root)
    if len(references) != EXPECTED_REFERENCES:
        raise AdoptedSchemaError("packaged schema reference inventory mismatch")
    for reference in references:
        resolve_pointer(root, reference)
    graph = _definition_graph(root)
    _assert_acyclic(graph)
    reached: set[str] = set()

    def reach(name: str) -> None:
        if name in reached:
            return
        reached.add(name)
        for target in graph[name]:
            reach(target)

    for branch in root["oneOf"]:
        reference = branch.get("$ref") if type(branch) is dict else None
        if type(reference) is str and reference.startswith("#/$defs/"):
            reach(reference.removeprefix("#/$defs/").split("/", 1)[0])
    if len(reached) != 68 or set(root["$defs"]) - reached != {"hexDigest"}:
        raise AdoptedSchemaError("packaged schema reachability inventory mismatch")
    return root


def load_protocol_schema() -> dict[str, Any]:
    """Return a defensive copy of the accepted, integrity-checked schema."""
    return deepcopy(_schema_root())
