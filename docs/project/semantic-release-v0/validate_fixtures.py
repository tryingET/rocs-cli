#!/usr/bin/env python3
"""Stdlib-only independent validator for the Decision 53 documentation fixtures."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
MAX_SAFE_INTEGER = 9_007_199_254_740_991
DIGEST_FIELDS = {
    "semantic-source-manifest.v0": ("semantic-release.source-manifest.v0", "source_manifest_digest"),
    "semantic-material-manifest.v0": ("semantic-release.material-manifest.v0", "material_manifest_digest"),
    "semantic-compatibility-report.v0": ("semantic-release.compatibility-report.v0", "compatibility_report_digest"),
    "semantic-release-capsule.v0": ("semantic-release.capsule.v0", "capsule_digest"),
    "semantic-owner-approval.v0": ("semantic-release.owner-approval.v0", "owner_approval_digest"),
    "semantic-owner-publication.v0": ("semantic-release.owner-publication.v0", "owner_publication_digest"),
    "semantic-build-receipt.v0": ("semantic-release.build-receipt.v0", "build_receipt_digest"),
    "semantic-consumer-intent.v0": ("semantic-release.consumer-intent.v0", "consumer_intent_digest"),
    "semantic-owner-acceptance.v0": ("semantic-release.owner-acceptance.v0", "owner_acceptance_digest"),
    "semantic-materialization-verification-receipt.v0": ("semantic-release.materialization-verification.v0", "materialization_verification_receipt_digest"),
    "semantic-activation-receipt.v0": ("semantic-release.activation.v0", "activation_receipt_digest"),
    "semantic-rocs-generation-receipt.v0": ("semantic-release.rocs-generation.v0", "rocs_generation_receipt_digest"),
    "semantic-pi-delivery-receipt.v0": ("semantic-release.pi-delivery.v0", "pi_delivery_receipt_digest"),
    "semantic-ak-evidence-linkage.v0": ("semantic-release.ak-evidence-linkage.v0", "ak_evidence_linkage_digest"),
    "semantic-rollback-request.v0": ("semantic-release.rollback-request.v0", "rollback_request_digest"),
    "semantic-rollback-receipt.v0": ("semantic-release.rollback-receipt.v0", "rollback_receipt_digest"),
    "semantic-audit-envelope.v0": ("semantic-release.audit-envelope.v0", "audit_envelope_digest"),
    "semantic-protocol-error.v0": ("semantic-release.error.v0", "error_digest"),
}
COORDINATE_DOMAIN = "semantic-release.coordinate.v0"


class ValidationError(Exception):
    pass


def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ValidationError(f"duplicate JSON key: {key!r}")
        out[key] = value
    return out


def load_json(path: Path) -> Any:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValidationError(f"{path}: UTF-8 BOM forbidden")
    try:
        text = raw.decode("utf-8", errors="strict")
        return json.loads(text, object_pairs_hook=reject_duplicates, parse_float=lambda _: (_ for _ in ()).throw(ValidationError("non-integer JSON number")), parse_int=int)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"{path}: {exc}") from exc


def utf16_key(value: str) -> bytes:
    return value.encode("utf-16-be", errors="strict")


def validate_ijson(value: Any, path: str = "$") -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        if not 0 <= value <= MAX_SAFE_INTEGER:
            raise ValidationError(f"{path}: integer outside safe nonnegative range")
        return
    if isinstance(value, str):
        if unicodedata.normalize("NFC", value) != value:
            raise ValidationError(f"{path}: string is not NFC")
        if any(
            0xD800 <= ord(ch) <= 0xDFFF
            or 0xFDD0 <= ord(ch) <= 0xFDEF
            or (ord(ch) & 0xFFFF) in (0xFFFE, 0xFFFF)
            for ch in value
        ):
            raise ValidationError(f"{path}: forbidden Unicode scalar")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            validate_ijson(item, f"{path}/{index}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValidationError(f"{path}: non-string key")
            validate_ijson(key, f"{path}/<key>")
            validate_ijson(item, f"{path}/{key}")
        return
    raise ValidationError(f"{path}: unsupported JSON type {type(value).__name__}")


def jcs(value: Any) -> str:
    validate_ijson(value)
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, list):
        return "[" + ",".join(jcs(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{" + ",".join(jcs(key) + ":" + jcs(value[key]) for key in sorted(value, key=utf16_key)) + "}"
    raise AssertionError("validate_ijson should have rejected this value")


def domain_digest(domain: str, preimage: bytes) -> str:
    return "sha256:" + hashlib.sha256(domain.encode("ascii") + b"\x00" + preimage).hexdigest()


def object_digest(instance: dict[str, Any], domain: str, omitted: str | None) -> tuple[str, str]:
    candidate = copy.deepcopy(instance)
    if omitted is not None:
        if omitted not in candidate:
            raise ValidationError(f"missing omitted digest field {omitted}")
        del candidate[omitted]
    canonical = jcs(candidate)
    return canonical, domain_digest(domain, canonical.encode("utf-8"))


def resolve_ref(root: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValidationError(f"external schema reference forbidden: {ref}")
    node: Any = root
    for token in ref[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or token not in node:
            raise ValidationError(f"unresolved schema reference: {ref}")
        node = node[token]
    if not isinstance(node, dict):
        raise ValidationError(f"schema reference is not an object: {ref}")
    return node


def schema_validate(instance: Any, schema: dict[str, Any], root: dict[str, Any], path: str = "$") -> None:
    if "$ref" in schema:
        schema_validate(instance, resolve_ref(root, schema["$ref"]), root, path)
        return
    if "oneOf" in schema:
        successes = 0
        for variant in schema["oneOf"]:
            try:
                schema_validate(instance, variant, root, path)
                successes += 1
            except ValidationError:
                pass
        if successes != 1:
            raise ValidationError(f"{path}: oneOf matched {successes} variants")
        return
    if "const" in schema and instance != schema["const"]:
        raise ValidationError(f"{path}: const mismatch")
    if "enum" in schema and instance not in schema["enum"]:
        raise ValidationError(f"{path}: enum mismatch")
    expected = schema.get("type")
    if expected == "object":
        if not isinstance(instance, dict):
            raise ValidationError(f"{path}: expected object")
        properties = schema.get("properties", {})
        missing = [name for name in schema.get("required", []) if name not in instance]
        if missing:
            raise ValidationError(f"{path}: missing required {missing}")
        if schema.get("additionalProperties") is False:
            extra = sorted(set(instance) - set(properties))
            if extra:
                raise ValidationError(f"{path}: unknown properties {extra}")
        for name, value in instance.items():
            if name in properties:
                schema_validate(value, properties[name], root, f"{path}/{name}")
    elif expected == "array":
        if not isinstance(instance, list):
            raise ValidationError(f"{path}: expected array")
        if len(instance) < schema.get("minItems", 0) or len(instance) > schema.get("maxItems", MAX_SAFE_INTEGER):
            raise ValidationError(f"{path}: array size out of range")
        if "items" in schema:
            for index, item in enumerate(instance):
                schema_validate(item, schema["items"], root, f"{path}/{index}")
    elif expected == "string":
        if not isinstance(instance, str):
            raise ValidationError(f"{path}: expected string")
        if len(instance) < schema.get("minLength", 0) or len(instance) > schema.get("maxLength", MAX_SAFE_INTEGER):
            raise ValidationError(f"{path}: string length out of range")
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            raise ValidationError(f"{path}: pattern mismatch")
    elif expected == "integer":
        if isinstance(instance, bool) or not isinstance(instance, int):
            raise ValidationError(f"{path}: expected integer")
        if instance < schema.get("minimum", -MAX_SAFE_INTEGER) or instance > schema.get("maximum", MAX_SAFE_INTEGER):
            raise ValidationError(f"{path}: integer out of range")
    elif expected == "boolean":
        if not isinstance(instance, bool):
            raise ValidationError(f"{path}: expected boolean")
    elif expected == "null":
        if instance is not None:
            raise ValidationError(f"{path}: expected null")
    elif expected is not None:
        raise ValidationError(f"{path}: unsupported schema type {expected}")


def check_schema_contract(schema: dict[str, Any]) -> None:
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise ValidationError("schema is not Draft 2020-12")
    seen_protocols: set[str] = set()

    def walk(node: Any, path: str) -> None:
        if isinstance(node, dict):
            if "$ref" in node:
                resolve_ref(schema, node["$ref"])
            if node.get("type") == "object":
                if node.get("additionalProperties") is not False:
                    raise ValidationError(f"{path}: object schema is not closed")
                props = node.get("properties", {})
                for required in node.get("required", []):
                    if required not in props:
                        raise ValidationError(f"{path}: required property {required} is undefined")
                protocol = props.get("schema", {}).get("const") if isinstance(props.get("schema"), dict) else None
                if protocol:
                    if protocol in seen_protocols:
                        raise ValidationError(f"duplicate protocol discriminator {protocol}")
                    seen_protocols.add(protocol)
            for key, value in node.items():
                walk(value, f"{path}/{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{path}/{index}")

    walk(schema, "$")
    expected = set(DIGEST_FIELDS) | {"semantic-release-coordinate.v0"}
    if not expected <= seen_protocols:
        raise ValidationError(f"schema missing protocol objects: {sorted(expected - seen_protocols)}")


def pointer(instance: Any, value: str) -> Any:
    node = instance
    if value == "":
        return node
    for token in value.lstrip("/").split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        node = node[int(token)] if isinstance(node, list) else node[token]
    return node


def check_order_and_uniqueness(instance: dict[str, Any]) -> None:
    schema = instance.get("schema")
    if schema in {"semantic-source-manifest.v0", "semantic-material-manifest.v0"}:
        entries = instance["entries"]
        keys = [(item["path"].encode("utf-8"), item["kind"]) for item in entries]
        paths = {item["path"] for item in entries}
        if keys != sorted(keys) or len(paths) != len(entries):
            raise ValidationError(f"{schema}: entries not sorted/unique")
        for path in paths:
            if "/" in path and path.rsplit("/", 1)[0] not in paths:
                raise ValidationError(f"{schema}: unlisted parent directory for {path}")
    if schema == "semantic-release-capsule.v0":
        values = instance["required_protocol_versions"]
        if values != sorted(values, key=lambda x: x.encode()) or len(values) != len(set(values)):
            raise ValidationError("required_protocol_versions not sorted/unique")
    if schema == "semantic-owner-approval.v0":
        votes = instance["votes"]
        keys = [(x["owner_id"].encode(), x["owner_key_id"].encode()) for x in votes]
        if keys != sorted(keys) or len(keys) != len(set(keys)):
            raise ValidationError("approval votes not sorted/unique")
        if any(x["approved_candidate_digest"] != instance["candidate_capsule_digest"] for x in votes):
            raise ValidationError("approval vote candidate mismatch")
    if schema == "semantic-compatibility-report.v0":
        changes = [(x["semantic_id"].encode(), x["category"].encode()) for x in instance["changes"]]
        if changes != sorted(changes) or len(set(changes)) != len(changes):
            raise ValidationError("compatibility changes not sorted/unique")
        conditions = [x["condition_id"] for x in instance["conditions"]]
        if conditions != sorted(conditions, key=lambda x: x.encode()) or len(conditions) != len(set(conditions)):
            raise ValidationError("compatibility conditions not sorted/unique")
        for field in ("deprecations", "removals", "tombstones"):
            values = instance[field]
            if values != sorted(values, key=lambda x: x.encode()) or len(values) != len(set(values)):
                raise ValidationError(f"{field} not sorted/unique")
    if schema == "semantic-rocs-generation-receipt.v0":
        for field in ("candidate_ids", "pack_digests"):
            values = instance[field]
            if values != sorted(values, key=lambda x: x.encode()) or len(values) != len(set(values)):
                raise ValidationError(f"{field} not sorted/unique")
    if schema == "semantic-protocol-error.v0":
        keys = [x["key"] for x in instance["details"]]
        if keys != sorted(keys, key=lambda x: x.encode()) or len(keys) != len(set(keys)):
            raise ValidationError("error details not sorted/unique")


def check_cross_fields(instance: dict[str, Any]) -> None:
    schema = instance.get("schema")
    if schema == "semantic-owner-publication.v0":
        if instance["ledger_namespace"] != instance["coordinate"]["namespace"] or instance["ledger_revision"] != instance["expected_prior_revision"] + 1:
            raise ValidationError("publication CAS relationship mismatch")
    if schema == "semantic-consumer-intent.v0":
        target = instance["rollback_target"]
        if (target["semantic_mode"] == "predecessor") != (target["semantic_coordinate"] is not None):
            raise ValidationError("consumer rollback target mismatch")
    if schema == "semantic-owner-acceptance.v0":
        if instance["acceptance_authority"]["id"] != instance["consumer_repository"]["owner"]:
            raise ValidationError("consumer acceptance owner mismatch")
    if schema == "semantic-materialization-verification-receipt.v0":
        if instance["expected_manifest_digest"] != instance["actual_manifest_digest"]:
            raise ValidationError("golden materialization tree mismatch")
        if instance["compatibility_outcome"] in {"breaking", "unknown"} or not instance["rollback_materialized"]:
            raise ValidationError("golden materialization is not activatable")
    if schema == "semantic-rollback-receipt.v0":
        if instance["result"] == "failed":
            if instance["error_digest"] is None:
                raise ValidationError("failed rollback lacks error")
        elif instance["error_digest"] is not None or instance["history_head_before"] == instance["history_head_after"]:
            raise ValidationError("successful rollback result/history mismatch")


def check_claim_scope(instance: dict[str, Any]) -> None:
    expected = {
        "semantic-owner-acceptance.v0": ("acceptance_authority", "consumer_owner"),
        "semantic-materialization-verification-receipt.v0": ("issuer", "rocs"),
        "semantic-activation-receipt.v0": ("issuer", "consumer_owner"),
        "semantic-rocs-generation-receipt.v0": ("issuer", "rocs"),
        "semantic-pi-delivery-receipt.v0": ("issuer", "pi"),
        "semantic-ak-evidence-linkage.v0": ("issuer", "ak"),
        "semantic-rollback-receipt.v0": ("issuer", "recovery_controller"),
    }
    rule = expected.get(instance.get("schema"))
    if rule and instance[rule[0]]["kind"] != rule[1]:
        code = "self_certification" if instance.get("schema") == "semantic-owner-acceptance.v0" else "issuer_scope_violation"
        raise ValidationError(code)


def differential_error(rule: str, subject: dict[str, Any], context: dict[str, Any]) -> str | None:
    if rule == "self_certification":
        return "self_certification" if subject["acceptance_authority"]["kind"] != "consumer_owner" else None
    if rule == "version_conflict":
        old = context["existing_coordinate"]
        new = subject["coordinate"]
        return "version_conflict" if (old["namespace"], old["semantic_version"]) == (new["namespace"], new["semantic_version"]) and old["capsule_digest"] != new["capsule_digest"] else None
    if rule == "incomplete_tree":
        expected = context.get("expected_paths", [])
        actual = context.get("actual_paths", [])
        mismatch = subject["expected_manifest_digest"] != subject["actual_manifest_digest"]
        return "incomplete_tree" if mismatch and expected != actual else None
    if rule == "compatibility_unknown":
        return "compatibility_unknown" if subject["compatibility_outcome"] == "unknown" else None
    if rule == "mutable_timestamp":
        forbidden = {key for key in subject if key.endswith("_at") or key in {"timestamp", "recorded_at"}}
        return "malformed_input" if subject.get("schema") != "semantic-audit-envelope.v0" and forbidden else None
    if rule == "stale_trust":
        trust = subject["trust_reference"]
        return "trust_reference_stale" if trust["trust_root_revision"] < context["minimum_trust_root_revision"] or trust["publication_ledger_revision"] < context["minimum_publication_ledger_revision"] else None
    if rule == "revoked_trust":
        return "trust_revoked" if subject["trust_reference"]["trust_root_digest"] in context["revoked_trust_root_digests"] else None
    if rule == "rollback_unavailability":
        target = subject["target"]
        unavailable = target["semantic_mode"] == "predecessor" and subject["target_materialization_receipt_digest"] is None
        return "rollback_unavailable" if unavailable else None
    if rule == "manifest_order":
        try:
            check_order_and_uniqueness(subject)
        except ValidationError:
            return "malformed_input"
        return None
    if rule == "issuer_scope":
        try:
            check_claim_scope(subject)
        except ValidationError:
            return "issuer_scope_violation"
        return None
    raise ValidationError(f"unknown differential rule {rule}")


def main() -> int:
    schema = load_json(ROOT / "protocol.schema.json")
    golden = load_json(ROOT / "golden-fixtures.json")
    differential = load_json(ROOT / "differential-fixtures.json")
    validate_ijson(schema)
    validate_ijson(golden)
    validate_ijson(differential)
    check_schema_contract(schema)

    records: dict[str, dict[str, Any]] = {}
    for record in golden["records"]:
        name = record["name"]
        if name in records:
            raise ValidationError(f"duplicate golden record {name}")
        instance = record["instance"]
        schema_validate(instance, schema, schema)
        check_order_and_uniqueness(instance)
        check_cross_fields(instance)
        check_claim_scope(instance)
        canonical, digest = object_digest(instance, record["domain"], record["omitted_field"])
        if canonical != record["canonical_preimage"]:
            raise ValidationError(f"{name}: canonical preimage mismatch")
        if digest != record["digest"]:
            raise ValidationError(f"{name}: digest mismatch")
        if record["omitted_field"] is not None and instance[record["omitted_field"]] != digest:
            raise ValidationError(f"{name}: embedded digest mismatch")
        records[name] = record

    for blob in golden["raw_preimages"]:
        raw = blob["preimage_utf8"].encode("utf-8")
        if domain_digest(blob["domain"], raw) != blob["digest"]:
            raise ValidationError(f"{blob['name']}: raw digest mismatch")

    for assertion in golden["chain_assertions"]:
        actual = pointer(records[assertion["record"]]["instance"], assertion["instance_path"])
        expected = records[assertion["equals_record"]]["digest"]
        if actual != expected:
            raise ValidationError(f"chain assertion failed: {assertion}")
    acceptance = records["owner_acceptance"]["instance"]
    intent = records["consumer_intent"]["instance"]
    activation = records["activation_receipt"]["instance"]
    if acceptance["valid_through_intent_revision"] < intent["intent_revision"]:
        raise ValidationError("golden acceptance expired by intent revision")
    if activation["activation_epoch"] > acceptance["activation_epoch_not_after"]:
        raise ValidationError("golden activation expired by owner epoch")

    for case in differential["cases"]:
        subject = case["subject"]
        validate_ijson(subject)
        subject_domain, subject_omitted = DIGEST_FIELDS[subject["schema"]]
        _, subject_digest = object_digest(subject, subject_domain, subject_omitted)
        if subject[subject_omitted] != subject_digest:
            raise ValidationError(f"{case['name']}: counterexample digest mismatch masks its intended failure")
        structurally_valid = True
        try:
            schema_validate(subject, schema, schema)
        except ValidationError:
            structurally_valid = False
        if structurally_valid != case["schema_valid"]:
            raise ValidationError(f"{case['name']}: schema_valid mismatch")
        actual = differential_error(case["rule"], subject, case.get("context", {}))
        if actual != case["expected_error"]:
            raise ValidationError(f"{case['name']}: expected {case['expected_error']}, got {actual}")

    print(f"schema: Draft 2020-12 marker, closed objects, and {len(DIGEST_FIELDS) + 1} protocol types verified")
    print(f"golden: {len(records)} canonical object preimages and {len(golden['raw_preimages'])} raw preimages recomputed")
    print(f"chain: {len(golden['chain_assertions'])} digest links verified")
    print(f"differential: {len(differential['cases'])} counterexamples rejected with expected errors")
    print("result: PASS (stdlib-only independent validator)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        print(f"result: FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
