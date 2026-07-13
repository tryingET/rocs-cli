#!/usr/bin/env python3
"""Stdlib-only revision-10 owner-receipt authority-graph, schema, digest, link, and transition validator."""
from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
MAX_SAFE_INTEGER = 9_007_199_254_740_991
COORDINATE_DOMAIN = "semantic-release.coordinate.v0"
DOMAIN_ROWS = {
    "semantic-source-manifest.v0": ("source-manifest", "source_manifest_digest"),
    "semantic-material-manifest.v0": ("material-manifest", "material_manifest_digest"),
    "semantic-owner-set.v0": ("owner-set", "owner_set_digest"),
    "semantic-approval-predicate.v0": ("approval-predicate", "approval_predicate_digest"),
    "semantic-owner-policy.v0": ("owner-policy", "owner_policy_digest"),
    "semantic-trust-root.v0": ("trust-root", "trust_root_digest"),
    "semantic-trust-rotation.v0": ("trust-rotation", "trust_rotation_digest"),
    "semantic-trust-revocation.v0": ("trust-revocation", "trust_revocation_digest"),
    "semantic-compatibility-policy.v0": ("compatibility-policy", "compatibility_policy_digest"),
    "semantic-compatibility-report.v0": ("compatibility-report", "compatibility_report_digest"),
    "semantic-compatibility-override.v0": ("compatibility-override", "compatibility_override_digest"),
    "semantic-deprecation-record.v0": ("deprecation-record", "deprecation_record_digest"),
    "semantic-removal-record.v0": ("removal-record", "removal_record_digest"),
    "semantic-tombstone-registry.v0": ("tombstone-registry", "tombstone_registry_digest"),
    "semantic-publication-ledger-head.v0": ("publication-ledger-head", "publication_ledger_head_digest"),
    "semantic-accepted-lifecycle-ledger-record.v0": ("accepted-lifecycle-ledger-record", "accepted_lifecycle_ledger_record_digest"),
    "semantic-payload-projection.v0": ("payload-projection", "payload_projection_digest"),
    "semantic-capsule-archive-linkage.v0": ("capsule-archive-linkage", "capsule_archive_linkage_digest"),
    "semantic-release-capsule.v0": ("capsule", "capsule_digest"),
    "semantic-ak-decision-reference.v0": ("ak-decision-reference", "ak_decision_reference_digest"),
    "semantic-owner-approval.v0": ("owner-approval", "owner_approval_digest"),
    "semantic-build-receipt.v0": ("build-receipt", "build_receipt_digest"),
    "semantic-publication-transaction.v0": ("publication-transaction", "publication_transaction_digest"),
    "semantic-publication-journal.v0": ("publication-journal", "publication_journal_digest"),
    "semantic-publication-commit-marker.v0": ("publication-commit-marker", "publication_commit_marker_digest"),
    "semantic-owner-publication.v0": ("owner-publication", "owner_publication_digest"),
    "semantic-publication-status-transition.v0": ("publication-status-transition", "publication_status_transition_digest"),
    "semantic-consumer-intent.v0": ("consumer-intent", "consumer_intent_digest"),
    "semantic-owner-acceptance.v0": ("owner-acceptance", "owner_acceptance_digest"),
    "semantic-materialization-verification-receipt.v0": ("materialization-verification", "materialization_verification_receipt_digest"),
    "semantic-activation-receipt.v0": ("activation", "activation_receipt_digest"),
    "semantic-rocs-generation-receipt.v0": ("rocs-generation", "rocs_generation_receipt_digest"),
    "semantic-pi-delivery-receipt.v0": ("pi-delivery", "pi_delivery_receipt_digest"),
    "semantic-ak-evidence-linkage.v0": ("ak-evidence-linkage", "ak_evidence_linkage_digest"),
    "semantic-rollback-request.v0": ("rollback-request", "rollback_request_digest"),
    "semantic-rollback-technical-receipt.v0": ("rollback-technical-receipt", "rollback_technical_receipt_digest"),
    "semantic-rollback-availability-receipt.v0": ("rollback-availability-receipt", "rollback_available_artifact_digest"),
    "semantic-rollback-availability-proof.v0": ("rollback-availability-proof", "rollback_availability_proof_digest"),
    "semantic-rollback-history-transition.v0": ("rollback-history-transition", "rollback_history_transition_digest"),
    "semantic-rollback-receipt.v0": ("rollback-receipt", "rollback_receipt_digest"),
    "semantic-non-authorizing-task-contract.v0": ("non-authorizing-task-contract", "non_authorizing_task_contract_digest"),
    "semantic-audit-envelope.v0": ("audit-envelope", "audit_envelope_digest"),
    "semantic-protocol-error.v0": ("error", "error_digest"),
    "semantic-owner-acquisition-capability-pin.v0": ("owner-acquisition-capability-pin", "capability_pin_digest"),
    "semantic-authority-acquisition-config.v0": ("authority-acquisition-config", "authority_acquisition_config_digest"),
    "semantic-owner-store-read-receipt.v0": ("owner-store-read-receipt", "owner_store_read_receipt_digest"),
    "semantic-authority-snapshot.v0": ("authority-snapshot", "authority_snapshot_digest"),
    "semantic-authority-rule-role-manifest.v0": ("authority-rule-role-manifest", "authority_rule_role_manifest_digest"),
    "semantic-authority-proof-bundle.v0": ("authority-proof-bundle", "authority_proof_bundle_digest"),
    "semantic-authority-verifier-input.v0": ("authority-verifier-input", "authority_verifier_input_digest"),
}
DIGEST_FIELDS = {schema: (f"semantic-release.{domain}.v0", field) for schema, (domain, field) in DOMAIN_ROWS.items()}
SCHEMA_ROOT: dict[str, Any] | None = None

AUTHORITY_BEARING_RULES = {"acceptance_binding", "activation_binding", "ak_decision", "approval_threshold", "compatibility", "generation_activation", "governance_contracts", "lifecycle", "projection", "publication_cas", "publication_commit", "publication_recovery", "publication_transition", "rollback", "tombstone_reuse", "trust_revocation", "trust_rotation", "version_binding"}
ALL_RULES = {"acceptance_binding", "activation_binding", "ak_decision", "ak_optional_pi", "approval_threshold", "compatibility", "compatibility_policy", "digest", "generation_activation", "governance_contracts", "lifecycle", "pi_variant", "projection", "publication_cas", "publication_commit", "publication_journal_shape", "publication_recovery", "publication_transition", "rollback", "tombstone_reuse", "trust_revocation", "trust_rotation", "utc", "version_binding"}
EXPECTED_AUTHORITY_EDGE_COUNT = 105
EXPECTED_AUTHORITY_REGISTRY_DIGEST = "sha256:4231960e278b5ea7a2fc80164b4acdb93d88e466c0e28278a0107d6aa9b06a5a"
EXPECTED_AUTHORITY_MANIFEST_DIGEST = "sha256:f2b39cd5cbec2b1275d1518db14f131bb80ea1387442aead527a80fc81215820"
AUTHORITY_MANIFEST: dict[str, Any] | None = None
AUTHORITY_MANIFEST_BY_RULE: dict[str, dict] = {}



class ValidationError(Exception):
    pass


def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result: raise ValidationError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def parse_integer_token(token: str) -> int:
    if re.fullmatch(r"0|[1-9][0-9]*", token) is None: raise ValidationError(f"non-canonical integer token {token!r}")
    value = int(token)
    if value > MAX_SAFE_INTEGER: raise ValidationError("unsafe integer token")
    return value


def parse_json_text(text: str) -> Any:
    try:
        value = json.loads(text, object_pairs_hook=reject_duplicates, parse_int=parse_integer_token,
            parse_float=lambda token: (_ for _ in ()).throw(ValidationError(f"non-integer number token {token!r}")),
            parse_constant=lambda token: (_ for _ in ()).throw(ValidationError(f"non-I-JSON constant {token!r}")))
    except json.JSONDecodeError as exc:
        raise ValidationError(str(exc)) from exc
    validate_ijson(value)
    return value


def load_json(path: Path) -> Any:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"): raise ValidationError(f"{path}: BOM forbidden")
    try: return parse_json_text(raw.decode("utf-8", "strict"))
    except (UnicodeDecodeError, ValidationError) as exc: raise ValidationError(f"{path}: {exc}") from exc


def validate_ijson(value: Any, path: str = "$") -> None:
    if value is None or isinstance(value, bool): return
    if isinstance(value, int):
        if not 0 <= value <= MAX_SAFE_INTEGER: raise ValidationError(f"{path}: unsafe integer")
        return
    if isinstance(value, str):
        if unicodedata.normalize("NFC", value) != value: raise ValidationError(f"{path}: non-NFC string")
        if any(0xD800 <= ord(c) <= 0xDFFF or 0xFDD0 <= ord(c) <= 0xFDEF or (ord(c) & 0xFFFF) in (0xFFFE, 0xFFFF) for c in value):
            raise ValidationError(f"{path}: forbidden Unicode scalar")
        return
    if isinstance(value, list):
        for i, item in enumerate(value): validate_ijson(item, f"{path}/{i}")
        return
    if isinstance(value, dict):
        for key, item in value.items(): validate_ijson(key, f"{path}/key"); validate_ijson(item, f"{path}/{key}")
        return
    raise ValidationError(f"{path}: unsupported JSON type")


def jcs(value: Any) -> str:
    validate_ijson(value)
    if value is None: return "null"
    if value is True: return "true"
    if value is False: return "false"
    if isinstance(value, int): return str(value)
    if isinstance(value, str): return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, list): return "[" + ",".join(jcs(x) for x in value) + "]"
    if isinstance(value, dict): return "{" + ",".join(jcs(k) + ":" + jcs(value[k]) for k in sorted(value, key=lambda x: x.encode("utf-16-be"))) + "}"
    raise AssertionError


def domain_digest(domain: str, preimage: bytes) -> str:
    return "sha256:" + hashlib.sha256(domain.encode("ascii") + b"\0" + preimage).hexdigest()


def typed_digest(domain: str, value: Any) -> str: return domain_digest(domain, jcs(value).encode())
def action_digest(value: Any) -> str: return typed_digest("semantic-release.approval-action.v0", value)
def change_digest(value: Any) -> str: return typed_digest("semantic-release.compatibility-change.v0", value)


def object_digest(instance: dict[str, Any], domain: str, omitted: str | None) -> tuple[str, str]:
    candidate = copy.deepcopy(instance)
    if omitted is not None:
        if omitted not in candidate: raise ValidationError(f"missing self digest {omitted}")
        del candidate[omitted]
    canonical = jcs(candidate)
    return canonical, domain_digest(domain, canonical.encode())


def resolve_ref(root: dict, reference: str) -> dict:
    if not reference.startswith("#/"): raise ValidationError(f"external ref forbidden: {reference}")
    node: Any = root
    for token in reference[2:].split("/"): node = node[token.replace("~1", "/").replace("~0", "~")]
    if not isinstance(node, dict): raise ValidationError("schema ref is not object")
    return node


def json_equal(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(json_equal(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(json_equal(a, b) for a, b in zip(left, right))
    return left == right


def schema_validate(instance: Any, shape: dict, root: dict, path: str = "$") -> None:
    if "$ref" in shape: schema_validate(instance, resolve_ref(root, shape["$ref"]), root, path); return
    if "oneOf" in shape:
        matches = 0
        for option in shape["oneOf"]:
            try: schema_validate(instance, option, root, path); matches += 1
            except ValidationError: pass
        if matches != 1: raise ValidationError(f"{path}: oneOf matched {matches}")
        return
    if "const" in shape and not json_equal(instance, shape["const"]): raise ValidationError(f"{path}: const mismatch")
    if "enum" in shape and not any(json_equal(instance, option) for option in shape["enum"]): raise ValidationError(f"{path}: enum mismatch")
    expected = shape.get("type")
    if expected == "object":
        if not isinstance(instance, dict): raise ValidationError(f"{path}: expected object")
        props = shape.get("properties", {}); missing = [x for x in shape.get("required", []) if x not in instance]
        if missing: raise ValidationError(f"{path}: missing {missing}")
        if shape.get("additionalProperties") is False and (extra := sorted(set(instance) - set(props))): raise ValidationError(f"{path}: unknown {extra}")
        for key, value in instance.items():
            if key in props: schema_validate(value, props[key], root, f"{path}/{key}")
    elif expected == "array":
        if not isinstance(instance, list) or not shape.get("minItems", 0) <= len(instance) <= shape.get("maxItems", MAX_SAFE_INTEGER): raise ValidationError(f"{path}: array")
        for i, item in enumerate(instance): schema_validate(item, shape["items"], root, f"{path}/{i}")
    elif expected == "string":
        if not isinstance(instance, str) or not shape.get("minLength", 0) <= len(instance) <= shape.get("maxLength", MAX_SAFE_INTEGER): raise ValidationError(f"{path}: string")
        if "pattern" in shape and re.search(shape["pattern"], instance) is None: raise ValidationError(f"{path}: pattern")
    elif expected == "integer":
        if isinstance(instance, bool) or not isinstance(instance, int) or not shape.get("minimum", -MAX_SAFE_INTEGER) <= instance <= shape.get("maximum", MAX_SAFE_INTEGER): raise ValidationError(f"{path}: integer")
    elif expected == "boolean" and not isinstance(instance, bool): raise ValidationError(f"{path}: boolean")
    elif expected == "null" and instance is not None: raise ValidationError(f"{path}: null")


def pointer(instance: Any, path: str) -> Any:
    node = instance
    for token in path.lstrip("/").split("/") if path else []: node = node[int(token)] if isinstance(node, list) else node[token.replace("~1", "/").replace("~0", "~")]
    return node


def sorted_unique(values: list[str]) -> bool: return values == sorted(values, key=lambda x: x.encode()) and len(values) == len(set(values))


def check_order(instance: dict) -> None:
    kind = instance["schema"]
    if kind in {"semantic-source-manifest.v0", "semantic-material-manifest.v0"}:
        keys = [(x["path"].encode(), x["kind"]) for x in instance["entries"]]
        if keys != sorted(keys) or len(keys) != len({x["path"] for x in instance["entries"]}): raise ValidationError("manifest order")
    if kind == "semantic-owner-set.v0":
        if not sorted_unique([x["owner_id"] for x in instance["members"]]) or any(not sorted_unique(x["key_ids"]) for x in instance["members"]): raise ValidationError("owner order")
    if kind == "semantic-trust-root.v0" and not sorted_unique(instance["key_ids"]): raise ValidationError("trust root key order")
    if kind == "semantic-owner-approval.v0":
        keys = [(x["owner_id"].encode(), x["owner_key_id"].encode()) for x in instance["votes"]]
        if keys != sorted(keys) or len(keys) != len(set(keys)) or action_digest(instance["action"]) != instance["action_digest"] or any(x["approved_action_digest"] != instance["action_digest"] for x in instance["votes"]): raise ValidationError("approval order/binding")
    if kind == "semantic-compatibility-policy.v0" and not sorted_unique([x["category"] for x in instance["category_rules"]]): raise ValidationError("policy order")
    if kind == "semantic-compatibility-report.v0":
        keys = [(x["semantic_id"].encode(), x["category"].encode()) for x in instance["changes"]]
        if keys != sorted(keys) or len(keys) != len(set(keys)) or not sorted_unique([x["condition_id"] for x in instance["conditions"]]) or not sorted_unique(instance["override_digests"]): raise ValidationError("compatibility order")
    if kind == "semantic-tombstone-registry.v0" and not sorted_unique([x["semantic_id"] for x in instance["entries"]]): raise ValidationError("tombstone order")
    if kind == "semantic-payload-projection.v0":
        src = [x["capsule_path"] for x in instance["entries"]]; dst = [x["consumer_path"] for x in instance["entries"]]
        if not sorted_unique(src) or len(dst) != len(set(dst)): raise ValidationError("projection bijection")
    if kind == "semantic-release-capsule.v0" and not sorted_unique(instance["required_protocol_versions"]): raise ValidationError("protocol order")
    if kind == "semantic-rocs-generation-receipt.v0" and (not sorted_unique(instance["candidate_ids"]) or not sorted_unique(instance["pack_digests"])): raise ValidationError("generation order")
    if kind == "semantic-rollback-receipt.v0" and len(instance["stages"]) != len({x["stage"] for x in instance["stages"]}): raise ValidationError("stage uniqueness")
    if kind == "semantic-non-authorizing-task-contract.v0":
        groups = ([x["reference_id"] for x in instance["dependencies"]], [x["reference_id"] for x in instance["prerequisites"]],
            [x["reference_id"] for x in instance["required_evidence"]], [x["condition_id"] for x in instance["stop_conditions"]])
        if not sorted_unique(instance["allowed_paths"]) or any(not sorted_unique(x) for x in groups): raise ValidationError("task contract order")
    if kind == "semantic-authority-acquisition-config.v0" and not sorted_unique([x["capability_pin_id"] for x in instance["pins"]]):
        raise ValidationError("authority acquisition pin order")
    if kind == "semantic-authority-snapshot.v0" and not sorted_unique([x["observation_id"] for x in instance["store_read_receipts"]]):
        raise ValidationError("authority snapshot receipt order")
    if kind == "semantic-authority-rule-role-manifest.v0":
        if not sorted_unique([x["rule"] for x in instance["rules"]]): raise ValidationError("authority manifest rule order")
        for row in instance["rules"]:
            groups = ([x["role"] for x in row["role_mappings"]], row["required_roles"], row["edge_ids"],
                [x["edge_id"] for x in row["role_edge_links"]])
            if (any(not sorted_unique(x) for x in groups)
                or any(not sorted_unique(x["sources"]) or not sorted_unique(x["expected_schemas"]) for x in row["role_mappings"])
                or any(not sorted_unique(x["role_ids"]) for x in row["role_edge_links"])):
                raise ValidationError("authority manifest role order")
    if kind == "semantic-authority-proof-bundle.v0" and not sorted_unique([x["bundle_key"] for x in instance["nodes"]]):
        raise ValidationError("proof bundle order")
    if kind == "semantic-authority-verifier-input.v0":
        groups = ([x["role"] for x in instance["receipt_bindings"]], [x["role"] for x in instance["node_bindings"]],
            [x["role"] for x in instance["parameter_bindings"]], instance["required_observation_ids"], instance["required_role_ids"], instance["required_edge_ids"])
        if any(not sorted_unique(x) for x in groups): raise ValidationError("authority verifier input order")
    if kind == "semantic-protocol-error.v0" and not sorted_unique([x["key"] for x in instance["details"]]): raise ValidationError("error order")


def strict_utc(value: str) -> bool:
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value) is None or value[:4] == "0000": return False
    try:
        parsed = dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        return 1 <= parsed.year <= 9999 and parsed.strftime("%Y-%m-%dT%H:%M:%SZ") == value
    except ValueError: return False


SEMVER_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-((?:0|[1-9][0-9]*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9][0-9]*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*))*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$")
def semver(value: str) -> tuple[str, str, str, str | None, str | None]:
    if not isinstance(value, str) or not 5 <= len(value) <= 256 or (match := SEMVER_RE.fullmatch(value)) is None: raise ValidationError("bad semver")
    return match.groups()  # type: ignore[return-value]
def compare_integer_text(a: str, b: str) -> int: return (len(a) > len(b)) - (len(a) < len(b)) or (a > b) - (a < b)
def compare_semver(a: tuple[str, str, str, str | None, str | None], b: tuple[str, str, str, str | None, str | None]) -> int:
    for x, y in zip(a[:3], b[:3]):
        if (c := compare_integer_text(x, y)): return c
    ap, bp = a[3], b[3]
    if ap is None or bp is None: return (ap is None) - (bp is None)
    for x, y in zip(ap.split("."), bp.split(".")):
        if x == y: continue
        xn, yn = x.isdigit(), y.isdigit()
        if xn and yn: return compare_integer_text(x, y)
        if xn != yn: return -1 if xn else 1
        return (x > y) - (x < y)
    return (len(ap.split(".")) > len(bp.split("."))) - (len(ap.split(".")) < len(bp.split(".")))


def fixture_digest_valid(subject: dict) -> bool:
    domain, omitted = DIGEST_FIELDS[subject["schema"]]
    return object_digest(subject, domain, omitted)[1] == subject[omitted]


class ContextValidationError(Exception):
    def __init__(self, code: str):
        self.code = code


def expected_context(value: Any, expected_schema: str | tuple[str, ...], expected_digest: str | None = None, reference_error: str = "digest_mismatch") -> dict:
    if SCHEMA_ROOT is None: raise ValidationError("schema root unavailable")
    schemas = (expected_schema,) if isinstance(expected_schema, str) else expected_schema
    try:
        validate_ijson(value)
        schema_validate(value, SCHEMA_ROOT, SCHEMA_ROOT)
    except (ValidationError, KeyError, TypeError):
        raise ContextValidationError("malformed_input")
    if value.get("schema") not in schemas:
        raise ContextValidationError("malformed_input")
    if value["schema"] == "semantic-release-coordinate.v0":
        actual_digest = object_digest(value, COORDINATE_DOMAIN, None)[1]
    else:
        if not fixture_digest_valid(value): raise ContextValidationError("digest_mismatch")
        _, field = DIGEST_FIELDS[value["schema"]]; actual_digest = value[field]
    try:
        check_order(value); check_claim_scope(value)
    except ValidationError as exc:
        raise ContextValidationError("issuer_scope_violation" if str(exc) == "issuer_scope_violation" else "malformed_input")
    if expected_digest is not None and actual_digest != expected_digest:
        raise ContextValidationError(reference_error)
    return value


def expected_shape_context(value: Any, definition: str) -> Any:
    if SCHEMA_ROOT is None: raise ValidationError("schema root unavailable")
    try:
        validate_ijson(value); schema_validate(value, SCHEMA_ROOT["$defs"][definition], SCHEMA_ROOT)
    except (ValidationError, KeyError, TypeError):
        raise ContextValidationError("malformed_input")
    return value


REQUIRED_RECEIPT_ROLES = {
    "approval_threshold": set(),
    "trust_rotation": {"current_root_digest", "revoked", "canonical_store_head", "current_decision_record_digest"},
    "trust_revocation": {"prior_revision", "prior_head", "canonical_store_head", "current_decision_record_digest"},
    "compatibility": {"canonical_store_head", "current_decision_record_digest"},
    "lifecycle": {"canonical_deprecation_head", "canonical_deprecation_revision", "canonical_removal_head", "canonical_removal_revision", "canonical_store_head", "current_deprecation_decision_record_digest", "current_removal_decision_record_digest", "deprecation_prior_head", "current_lifecycle_head", "external_trust_root_pin", "canonical_trust_root_digest", "canonical_trust_revocation_revision", "canonical_trust_revocation_head", "revoked_trust_digests"},
    "publication_commit": {"canonical_store_head", "current_decision_record_digest", "external_trust_root_pin", "canonical_trust_root_digest", "canonical_trust_revocation_revision", "canonical_trust_revocation_head", "revoked_trust_digests", "canonical_publication_revision", "canonical_publication_head", "canonical_publication_journal_head"},
    "publication_transition": {"canonical_store_head", "current_decision_record_digest", "external_trust_root_pin", "canonical_trust_root_digest", "canonical_trust_revocation_revision", "canonical_trust_revocation_head", "revoked_trust_digests", "canonical_publication_revision", "canonical_publication_head", "canonical_publication_journal_head"},
    "publication_recovery": {"canonical_recovery_controller_id", "canonical_recovery_runtime_identity", "canonical_recovery_epoch", "canonical_publication_revision", "canonical_publication_head", "canonical_publication_status_digest", "canonical_recovery_journal_head"},
    "tombstone_reuse": {"canonical_lifecycle_tombstone_head"},
    "projection": {"canonical_lifecycle_tombstone_head"},
    "publication_cas": {"current_revision", "current_head", "existing_replay_key", "existing_coordinate", "existing_operation"},
    "version_binding": {"existing_coordinate"},
    "ak_decision": {"canonical_store_head", "current_decision_record_digest"},
    "acceptance_binding": {"canonical_store_head", "current_decision_record_digest", "current_acceptance_digest", "current_acceptance_revision", "canonical_trust_root_digest", "canonical_trust_revocation_revision", "canonical_trust_revocation_head", "revoked_trust_digests", "canonical_publication_revision", "canonical_publication_head"},
    "activation_binding": {"canonical_store_head", "current_decision_record_digest", "current_acceptance_digest", "current_acceptance_revision", "current_activation_digest", "current_activation_revision", "canonical_recovery_controller_id", "canonical_recovery_runtime_identity", "canonical_recovery_epoch", "canonical_trust_root_digest", "canonical_trust_revocation_revision", "canonical_trust_revocation_head", "revoked_trust_digests", "canonical_publication_revision", "canonical_publication_head"},
    "generation_activation": {"canonical_store_head", "current_decision_record_digest", "current_acceptance_digest", "current_acceptance_revision", "current_activation_digest", "current_activation_revision", "canonical_recovery_controller_id", "canonical_recovery_runtime_identity", "canonical_recovery_epoch", "canonical_trust_root_digest", "canonical_trust_revocation_revision", "canonical_trust_revocation_head", "revoked_trust_digests", "canonical_publication_revision", "canonical_publication_head"},
    "rollback": {"canonical_store_head", "current_decision_record_digest", "current_acceptance_digest", "current_acceptance_revision", "current_activation_digest", "current_activation_revision", "canonical_history_head", "canonical_recovery_controller_id", "canonical_recovery_runtime_identity", "canonical_recovery_epoch", "canonical_trust_root_digest", "canonical_trust_revocation_revision", "canonical_trust_revocation_head", "revoked_trust_digests", "canonical_publication_revision", "canonical_publication_head"},
    "governance_contracts": {"canonical_task_states"},
}
SEMANTIC_PROOF_SCHEMAS = {"semantic-source-manifest.v0", "semantic-owner-set.v0", "semantic-approval-predicate.v0", "semantic-owner-policy.v0", "semantic-trust-root.v0", "semantic-trust-rotation.v0", "semantic-trust-revocation.v0", "semantic-compatibility-policy.v0", "semantic-compatibility-report.v0", "semantic-compatibility-override.v0", "semantic-deprecation-record.v0", "semantic-removal-record.v0", "semantic-tombstone-registry.v0", "semantic-publication-ledger-head.v0", "semantic-accepted-lifecycle-ledger-record.v0", "semantic-release-capsule.v0", "semantic-owner-approval.v0", "semantic-publication-transaction.v0", "semantic-publication-journal.v0", "semantic-publication-commit-marker.v0", "semantic-owner-publication.v0", "semantic-publication-status-transition.v0", "semantic-release-coordinate.v0"}
ROCS_PROOF_SCHEMAS = {"semantic-material-manifest.v0", "semantic-payload-projection.v0", "semantic-capsule-archive-linkage.v0", "semantic-build-receipt.v0", "semantic-materialization-verification-receipt.v0", "semantic-rocs-generation-receipt.v0", "semantic-rollback-availability-proof.v0"}
CONSUMER_PROOF_SCHEMAS = {"semantic-consumer-intent.v0", "semantic-owner-acceptance.v0", "semantic-activation-receipt.v0", "semantic-rollback-request.v0", "semantic-rollback-history-transition.v0"}
AK_PROOF_SCHEMAS = {"semantic-ak-decision-reference.v0", "semantic-ak-evidence-linkage.v0"}
RECOVERY_PROOF_SCHEMAS = {"semantic-rollback-receipt.v0"}

PROTOCOL_ROLE_SCHEMAS = {
    "owner_set": "semantic-owner-set.v0", "predicate": "semantic-approval-predicate.v0", "old_root": "semantic-trust-root.v0", "new_root": "semantic-trust-root.v0",
    "approval": "semantic-owner-approval.v0", "decision": "semantic-ak-decision-reference.v0", "deprecation_decision": "semantic-ak-decision-reference.v0", "removal_decision": "semantic-ak-decision-reference.v0",
    "deprecation": "semantic-deprecation-record.v0", "prior_tombstones": "semantic-tombstone-registry.v0", "resulting_tombstones": "semantic-tombstone-registry.v0",
    "deprecation_ledger": "semantic-accepted-lifecycle-ledger-record.v0", "removal_ledger": "semantic-accepted-lifecycle-ledger-record.v0",
    "deprecation_publication": "semantic-owner-publication.v0", "removal_publication": "semantic-owner-publication.v0",
    "deprecation_transaction": "semantic-publication-transaction.v0", "removal_transaction": "semantic-publication-transaction.v0", "transaction": "semantic-publication-transaction.v0",
    "deprecation_journal": "semantic-publication-journal.v0", "removal_journal": "semantic-publication-journal.v0", "journal": "semantic-publication-journal.v0", "prior_journal": "semantic-publication-journal.v0", "deprecation_prior_journal": "semantic-publication-journal.v0", "removal_prior_journal": "semantic-publication-journal.v0",
    "deprecation_marker": "semantic-publication-commit-marker.v0", "removal_marker": "semantic-publication-commit-marker.v0", "marker": "semantic-publication-commit-marker.v0",
    "deprecation_approval": "semantic-owner-approval.v0", "removal_approval": "semantic-owner-approval.v0", "deprecation_prior_status": "semantic-owner-publication.v0",
    "deprecation_canonical_ledger": "semantic-publication-ledger-head.v0", "removal_canonical_ledger": "semantic-publication-ledger-head.v0", "owner_policy": "semantic-owner-policy.v0", "trust_root": "semantic-trust-root.v0",
    "projection": "semantic-payload-projection.v0", "capsule": "semantic-release-capsule.v0", "archive_linkage": "semantic-capsule-archive-linkage.v0", "payload_manifest": "semantic-material-manifest.v0", "consumer_manifest": "semantic-material-manifest.v0", "archive_manifest": "semantic-material-manifest.v0",
    "request": "semantic-rollback-request.v0", "activation": "semantic-activation-receipt.v0", "intent": "semantic-consumer-intent.v0", "acceptance": "semantic-owner-acceptance.v0", "materialization": "semantic-materialization-verification-receipt.v0", "availability": "semantic-rollback-availability-proof.v0", "activation_availability": "semantic-rollback-availability-proof.v0",
    "recovery_artifact": "semantic-rollback-availability-receipt.v0", "semantic_artifact": "semantic-rollback-availability-receipt.v0", "runtime_artifact": "semantic-rollback-availability-receipt.v0", "disable_artifact": "semantic-rollback-availability-receipt.v0",
    "history_after": "semantic-rollback-history-transition.v0", "ak_linkage": "semantic-ak-evidence-linkage.v0", "pi_receipt": "semantic-pi-delivery-receipt.v0",
    "semantic_materialization_technical": "semantic-rollback-technical-receipt.v0", "runtime_materialization_technical": "semantic-rollback-technical-receipt.v0", "runtime_revalidation_technical": "semantic-rollback-technical-receipt.v0", "disable_contract_technical": "semantic-rollback-technical-receipt.v0", "disable_rehearsal_technical": "semantic-rollback-technical-receipt.v0", "recovery_rehearsal_technical": "semantic-rollback-technical-receipt.v0", "recovery_health_technical": "semantic-rollback-technical-receipt.v0",
    "previous_activation": "semantic-activation-receipt.v0", "consumer_contract": "semantic-non-authorizing-task-contract.v0", "existing_coordinate": "semantic-release-coordinate.v0", "resulting_status": ("semantic-owner-publication.v0", "semantic-publication-status-transition.v0"), "prior_status": ("semantic-owner-publication.v0", "semantic-publication-status-transition.v0"), "override": "semantic-compatibility-override.v0",
}

def authority_artifact_digest(value: dict) -> str:
    if value["schema"] == "semantic-release-coordinate.v0": return object_digest(value, COORDINATE_DOMAIN, None)[1]
    return value[DIGEST_FIELDS[value["schema"]][1]]


def decode_authority_fact(value: dict) -> Any:
    if value["kind"] == "null": return None
    if value["kind"] == "empty_list": return []
    if value["kind"] == "empty_map": return {}
    return value.get("value")


def expected_role_schema(rule: str, role: str, artifact: dict) -> str | tuple[str, ...]:
    if role.startswith("overrides:"): return "semantic-compatibility-override.v0"
    if role.startswith("override_approvals:"): return "semantic-owner-approval.v0"
    base = role.split(":", 1)[0]
    if base == "policy": return "semantic-compatibility-policy.v0" if rule in {"compatibility", "lifecycle"} else "semantic-owner-policy.v0"
    return PROTOCOL_ROLE_SCHEMAS.get(base, artifact["schema"])


def expected_proof_authority(rule: str, role: str, artifact: dict, schema_name: str) -> tuple[dict, str, dict]:
    repos = {
        "semantic_owner": {"owner": "semantic-owner", "repository_id": "ontology-kernel", "canonical_locator": "local://core/ontology-kernel", "identity_revision": 1},
        "ak": {"owner": "agent-kernel-owner", "repository_id": "agent-kernel", "canonical_locator": "local://softwareco/owned/agent-kernel", "identity_revision": 9},
        "consumer_owner": {"owner": "consumer-owner", "repository_id": "pi-canary-consumer", "canonical_locator": "local://softwareco/pi-canary-consumer", "identity_revision": 3},
        "rocs": {"owner": "rocs-owner", "repository_id": "rocs-cli", "canonical_locator": "local://core/rocs-cli", "identity_revision": 4},
        "recovery_controller": {"owner": "rocs-owner", "repository_id": "rocs-cli", "canonical_locator": "local://core/rocs-cli", "identity_revision": 4},
        "pi": {"owner": "pi-owner", "repository_id": "pi-adapter", "canonical_locator": "local://softwareco/pi-adapter", "identity_revision": 1},
    }
    if schema_name == "semantic-rollback-technical-receipt.v0":
        kind = {"materialization": "rocs", "runtime_revalidation": "rocs", "disable_contract": "consumer_owner", "rehearsal": "recovery_controller", "health": "recovery_controller"}[artifact["receipt_kind"]]
        issuer = {"kind": kind, "id": {"rocs": "rocs-cli", "consumer_owner": "consumer-owner", "recovery_controller": "recovery"}[kind]}
    elif schema_name == "semantic-rollback-availability-receipt.v0":
        kind = {"semantic_target": "rocs", "runtime_target": "rocs", "disable_target": "consumer_owner", "recovery_runtime": "recovery_controller"}[artifact["artifact_kind"]]
        issuer = {"kind": kind, "id": {"rocs": "rocs-cli", "consumer_owner": "consumer-owner", "recovery_controller": "recovery"}[kind]}
    elif schema_name == "semantic-non-authorizing-task-contract.v0": issuer = {"kind": "consumer_owner" if artifact["task_kind"] == "first_consumer" else "ak", "id": artifact["task_owner_id"]}
    elif schema_name in SEMANTIC_PROOF_SCHEMAS: issuer = {"kind": "semantic_owner", "id": "semantic-owner"}
    elif schema_name in ROCS_PROOF_SCHEMAS: issuer = artifact.get("issuer", {"kind": "rocs", "id": "rocs-cli"})
    elif schema_name in CONSUMER_PROOF_SCHEMAS: issuer = artifact.get("issuer", artifact.get("acceptance_authority", {"kind": "consumer_owner", "id": "consumer-owner"}))
    elif schema_name in AK_PROOF_SCHEMAS: issuer = artifact.get("issuer", {"kind": "ak", "id": "agent-kernel-owner"})
    elif schema_name in RECOVERY_PROOF_SCHEMAS: issuer = artifact.get("issuer", {"kind": "recovery_controller", "id": "recovery"})
    elif schema_name == "semantic-pi-delivery-receipt.v0": issuer = artifact["issuer"]
    else: issuer = artifact.get("issuer", {"kind": "rocs", "id": "rocs-cli"})
    claim = {"semantic_owner": "semantic_owner_fact", "ak": "ak_canonical_fact", "consumer_owner": "consumer_owner_fact", "rocs": "rocs_technical_fact", "recovery_controller": "recovery_controller_fact", "pi": "pi_delivery_fact"}[issuer["kind"]]
    return issuer, claim, copy.deepcopy(repos[issuer["kind"]])


def authority_fact_digest(fact_schema: str, fact_value: dict) -> str:
    return typed_digest("semantic-release.authority-fact.v0", {"fact_schema": fact_schema, "fact_value": fact_value})


def authority_acquisition_capability_digest(fields: dict) -> str:
    keys = ("owner_surface", "owner_repository", "acquisition_contract", "acquisition_contract_digest", "acquisition_distribution_digest")
    return typed_digest("semantic-release.owner-acquisition-capability.v0", {key: fields[key] for key in keys})


def authority_freshness_token(fields: dict) -> str:
    keys = ("role", "category", "owner_surface", "owner_id", "owner_repository", "acquisition_contract", "acquisition_contract_digest",
        "acquisition_distribution_digest", "store_id", "store_head_digest", "store_revision", "fact_schema", "fact_digest",
        "action_epoch", "required_action_epoch_floor")
    return typed_digest("semantic-release.owner-store-freshness-cas.v0", {key: fields[key] for key in keys})


def manifest_mapping(rule_entry: dict, role: str) -> dict:
    matches = [row for row in rule_entry["role_mappings"] if row["role"] == role and row["role_prefix"] is None
        or row["role_prefix"] is not None and role.startswith(row["role_prefix"])]
    if len(matches) != 1: raise ContextValidationError("self_certification")
    return matches[0]


def expected_vote_receipts(subject: dict, node_artifacts: dict[str, dict]) -> dict[str, dict]:
    approvals: list[tuple[str, dict]] = []
    if subject.get("schema") == "semantic-owner-approval.v0": approvals.append(("subject", subject))
    approvals.extend((role, artifact) for role, artifact in node_artifacts.items() if artifact.get("schema") == "semantic-owner-approval.v0")
    result: dict[str, dict] = {}
    for approval_role, approval in approvals:
        for vote in approval["votes"]:
            role = f"vote-proof:{approval_role}:{vote['owner_id']}"
            if role in result: raise ContextValidationError("malformed_input")
            result[role] = {"owner_id": vote["owner_id"], "owner_key_id": vote["owner_key_id"],
                "approved_action_digest": vote["approved_action_digest"], "approval_proof_digest": vote["approval_proof_digest"]}
    return result


def authority_preflight(rule: str, subject: dict, context: dict) -> dict:
    if set(context) != {"acquisition_config", "verifier_input", "authority_snapshot", "proof_bundle"}: raise ContextValidationError("malformed_input")
    if AUTHORITY_MANIFEST is None or rule not in AUTHORITY_MANIFEST_BY_RULE: raise ContextValidationError("self_certification")
    config = expected_context(context["acquisition_config"], "semantic-authority-acquisition-config.v0")
    verifier = expected_context(context["verifier_input"], "semantic-authority-verifier-input.v0")
    snapshot = expected_context(context["authority_snapshot"], "semantic-authority-snapshot.v0")
    bundle = expected_context(context["proof_bundle"], "semantic-authority-proof-bundle.v0")
    rule_manifest = AUTHORITY_MANIFEST_BY_RULE[rule]; subject_digest = authority_artifact_digest(subject)
    expected_edges = set(rule_manifest["edge_ids"])
    if not (verifier["rule"] == bundle["rule"] == rule and verifier["subject_schema"] == bundle["subject_schema"] == subject["schema"]
        and verifier["subject_digest"] == bundle["subject_digest"] == subject_digest
        and verifier["authority_rule_role_manifest_digest"] == AUTHORITY_MANIFEST["authority_rule_role_manifest_digest"]
        and verifier["authority_acquisition_config_digest"] == snapshot["authority_acquisition_config_digest"] == config["authority_acquisition_config_digest"]
        and verifier["authority_snapshot_digest"] == bundle["authority_snapshot_digest"] == snapshot["authority_snapshot_digest"]
        and verifier["authority_proof_bundle_digest"] == bundle["authority_proof_bundle_digest"]
        and verifier["required_action_epoch_floor"] == config["required_action_epoch_floor"]
        and snapshot["collator"] == config["collator"] and snapshot["collation_scope"] == config["collation_scope"]):
        raise ContextValidationError("self_certification")
    if set(verifier["required_edge_ids"]) != expected_edges or len(verifier["required_edge_ids"]) != len(expected_edges): raise ContextValidationError("self_certification")

    pins = {row["capability_pin_id"]: row for row in config["pins"]}
    receipts = {row["observation_id"]: row for row in snapshot["store_read_receipts"]}
    if len(pins) != len(config["pins"]) or len(receipts) != len(snapshot["store_read_receipts"]): raise ContextValidationError("malformed_input")
    binding_observations = {row["observation_id"] for row in verifier["receipt_bindings"]}
    binding_pins = {row["capability_pin_id"] for row in verifier["receipt_bindings"]}
    if (set(receipts) != binding_observations or set(verifier["required_observation_ids"]) != binding_observations
        or set(pins) != binding_pins or len(verifier["receipt_bindings"]) != len(binding_observations)):
        raise ContextValidationError("self_certification")
    if snapshot["action_epoch"] < config["required_action_epoch_floor"]: raise ContextValidationError("issuer_scope_violation")
    resolved: dict[str, Any] = {}; receipt_roles: set[str] = set()
    category_profiles = {
        "semantic_trust": ("semantic_owner", "semantic-owner", {"owner": "semantic-owner", "repository_id": "ontology-kernel", "canonical_locator": "local://core/ontology-kernel", "identity_revision": 1}),
        "semantic_revocation": ("semantic_owner", "semantic-owner", {"owner": "semantic-owner", "repository_id": "ontology-kernel", "canonical_locator": "local://core/ontology-kernel", "identity_revision": 1}),
        "semantic_publication": ("semantic_owner", "semantic-owner", {"owner": "semantic-owner", "repository_id": "ontology-kernel", "canonical_locator": "local://core/ontology-kernel", "identity_revision": 1}),
        "semantic_lifecycle": ("semantic_owner", "semantic-owner", {"owner": "semantic-owner", "repository_id": "ontology-kernel", "canonical_locator": "local://core/ontology-kernel", "identity_revision": 1}),
        "ak_store": ("ak", "agent-kernel-owner", {"owner": "agent-kernel-owner", "repository_id": "agent-kernel", "canonical_locator": "local://softwareco/owned/agent-kernel", "identity_revision": 9}),
        "ak_decision": ("ak", "agent-kernel-owner", {"owner": "agent-kernel-owner", "repository_id": "agent-kernel", "canonical_locator": "local://softwareco/owned/agent-kernel", "identity_revision": 9}),
        "ak_task": ("ak", "agent-kernel-owner", {"owner": "agent-kernel-owner", "repository_id": "agent-kernel", "canonical_locator": "local://softwareco/owned/agent-kernel", "identity_revision": 9}),
        "consumer_acceptance": ("consumer_owner", "consumer-owner", {"owner": "consumer-owner", "repository_id": "pi-canary-consumer", "canonical_locator": "local://softwareco/pi-canary-consumer", "identity_revision": 3}),
        "consumer_activation": ("consumer_owner", "consumer-owner", {"owner": "consumer-owner", "repository_id": "pi-canary-consumer", "canonical_locator": "local://softwareco/pi-canary-consumer", "identity_revision": 3}),
        "consumer_history": ("consumer_owner", "consumer-owner", {"owner": "consumer-owner", "repository_id": "pi-canary-consumer", "canonical_locator": "local://softwareco/pi-canary-consumer", "identity_revision": 3}),
        "recovery_controller": ("recovery_controller", "recovery", {"owner": "rocs-owner", "repository_id": "rocs-cli", "canonical_locator": "local://core/rocs-cli", "identity_revision": 4}),
    }
    for binding in verifier["receipt_bindings"]:
        role = binding["role"]; mapping = manifest_mapping(rule_manifest, role); row = receipts[binding["observation_id"]]; pin = pins[binding["capability_pin_id"]]
        try:
            schema_validate(pin, SCHEMA_ROOT, SCHEMA_ROOT); schema_validate(row, SCHEMA_ROOT, SCHEMA_ROOT)
            if not fixture_digest_valid(pin) or not fixture_digest_valid(row): raise ContextValidationError("digest_mismatch")
            check_order(pin); check_order(row)
        except ContextValidationError: raise
        except (ValidationError, KeyError, TypeError): raise ContextValidationError("malformed_input")
        if not (row["role"] == pin["role"] == role and row["category"] == pin["category"] == binding["category"]
            and row["capability_pin_id"] == pin["capability_pin_id"] == binding["capability_pin_id"]
            and row["capability_pin_digest"] == pin["capability_pin_digest"]
            and row["acquisition_capability_digest"] == pin["acquisition_capability_digest"] == binding["acquisition_capability_digest"]):
            raise ContextValidationError("issuer_scope_violation")
        if mapping["sources"] != ["receipt"] or mapping["category"] != row["category"]: raise ContextValidationError("issuer_scope_violation")
        if mapping["capability_pin_id"] is not None:
            if binding["capability_pin_id"] != mapping["capability_pin_id"] or mapping["capability_pin_prefix"] is not None: raise ContextValidationError("issuer_scope_violation")
        elif mapping["capability_pin_prefix"] is None or not binding["capability_pin_id"].startswith(mapping["capability_pin_prefix"]):
            raise ContextValidationError("issuer_scope_violation")
        if row["category"] == "semantic_vote":
            expected_surface, expected_id, expected_repo = "semantic_owner", row["fact_value"].get("value", {}).get("owner_id"), {"owner": "semantic-owner", "repository_id": "ontology-kernel", "canonical_locator": "local://core/ontology-kernel", "identity_revision": 1}
            if (mapping["role_prefix"] != "vote-proof:" or expected_id is None or mapping["owner_surface"] != expected_surface
                or mapping["owner_id"] is not None or mapping["owner_repository"] != expected_repo): raise ContextValidationError("issuer_scope_violation")
        else:
            expected_surface, expected_id, expected_repo = category_profiles[row["category"]]
            if mapping["role_prefix"] is not None or mapping["owner_surface"] != expected_surface or mapping["owner_id"] != expected_id or mapping["owner_repository"] != expected_repo:
                raise ContextValidationError("issuer_scope_violation")
        if not (pin["owner_surface"] == row["issuer"]["kind"] == binding["owner_surface"] == expected_surface
            and pin["owner_id"] == row["issuer"]["id"] == binding["owner_id"] == expected_id
            and pin["owner_repository"] == row["owner_repository"] == binding["owner_repository"] == expected_repo
            and row["issuer"] != config["collator"]): raise ContextValidationError("issuer_scope_violation")
        repeated = ("acquisition_contract", "acquisition_contract_digest", "acquisition_distribution_digest", "store_id", "store_head_digest",
            "store_revision", "fact_schema", "fact_digest", "fact_value", "freshness_cas_token_digest", "required_action_epoch_floor")
        if any(pin[key] != row[key] for key in repeated): raise ContextValidationError("issuer_scope_violation")
        acquisition_keys = ("acquisition_contract", "acquisition_contract_digest", "acquisition_distribution_digest", "acquisition_capability_digest")
        if (any(binding[key] != row[key] or mapping[key] != row[key] for key in acquisition_keys)
            or row["acquisition_capability_digest"] != authority_acquisition_capability_digest({
                "owner_surface": expected_surface, "owner_repository": expected_repo,
                "acquisition_contract": row["acquisition_contract"], "acquisition_contract_digest": row["acquisition_contract_digest"],
                "acquisition_distribution_digest": row["acquisition_distribution_digest"]})):
            raise ContextValidationError("issuer_scope_violation")
        expected_fact_schema = "semantic-owner-vote-proof-fact.v0" if row["category"] == "semantic_vote" else f"semantic-authority-{row['category'].replace('_', '-')}-fact.v0"
        if row["fact_schema"] != expected_fact_schema or mapping["expected_schemas"] != [expected_fact_schema]: raise ContextValidationError("issuer_scope_violation")
        if row["fact_digest"] != authority_fact_digest(row["fact_schema"], row["fact_value"]): raise ContextValidationError("issuer_scope_violation")
        token_fields = {"role": role, "category": row["category"], "owner_surface": row["issuer"]["kind"], "owner_id": row["issuer"]["id"],
            "owner_repository": row["owner_repository"], "acquisition_contract": row["acquisition_contract"],
            "acquisition_contract_digest": row["acquisition_contract_digest"], "acquisition_distribution_digest": row["acquisition_distribution_digest"],
            "store_id": row["store_id"], "store_head_digest": row["store_head_digest"], "store_revision": row["store_revision"],
            "fact_schema": row["fact_schema"], "fact_digest": row["fact_digest"], "action_epoch": row["action_epoch"],
            "required_action_epoch_floor": row["required_action_epoch_floor"]}
        if (row["freshness_cas_token_digest"] != authority_freshness_token(token_fields) or row["action_epoch"] != snapshot["action_epoch"]
            or row["action_epoch"] < row["required_action_epoch_floor"] or row["required_action_epoch_floor"] != config["required_action_epoch_floor"]):
            raise ContextValidationError("issuer_scope_violation")
        if role == "canonical_store_head":
            value = decode_authority_fact(row["fact_value"])
            if (value["store_id"], value["store_head_digest"], value["store_revision"]) != (row["store_id"], row["store_head_digest"], row["store_revision"]): raise ContextValidationError("issuer_scope_violation")
        if role in receipt_roles: raise ContextValidationError("malformed_input")
        receipt_roles.add(role); resolved[role] = decode_authority_fact(row["fact_value"])

    nodes = {row["bundle_key"]: row for row in bundle["nodes"]}
    if len(nodes) != len(bundle["nodes"]): raise ContextValidationError("malformed_input")
    if {row["bundle_key"] for row in verifier["node_bindings"]} != set(nodes): raise ContextValidationError("self_certification")
    node_artifacts: dict[str, dict] = {}; node_roles: set[str] = set()
    grouped_lists: dict[str, list[tuple[str, dict]]] = {}; grouped_maps: dict[str, dict[str, dict]] = {}
    for binding in verifier["node_bindings"]:
        role = binding["role"]; node = nodes[binding["bundle_key"]]; artifact = node["artifact"]; mapping = manifest_mapping(rule_manifest, role)
        expected_context(artifact, artifact["schema"])
        if node["artifact_schema"] != artifact["schema"] or node["bundle_key"] != authority_artifact_digest(artifact): raise ContextValidationError("digest_mismatch")
        expected_schema = expected_role_schema(rule, role, artifact); allowed = (expected_schema,) if isinstance(expected_schema, str) else expected_schema
        if binding["expected_schema"] not in allowed or artifact["schema"] not in allowed or artifact["schema"] not in mapping["expected_schemas"] or "node" not in mapping["sources"]:
            raise ContextValidationError("malformed_input")
        issuer, claim, repository = expected_proof_authority(rule, role, artifact, artifact["schema"]); embedded = artifact.get("issuer", artifact.get("acceptance_authority"))
        if embedded is not None and node["issuer"] != embedded: raise ContextValidationError("issuer_scope_violation")
        if (node["issuer"] != issuer or node["owner_repository"] != repository or node["claim_scope"] != claim
            or binding["expected_issuer_kind"] != issuer["kind"] or binding["expected_issuer_id"] != issuer["id"]
            or binding["expected_owner_repository"] != repository or binding["expected_claim_scope"] != claim
            or mapping["owner_surface"] != issuer["kind"] or mapping["owner_id"] != issuer["id"] or mapping["owner_repository"] != repository):
            raise ContextValidationError("issuer_scope_violation")
        if role in node_roles: raise ContextValidationError("malformed_input")
        node_roles.add(role); node_artifacts[role] = artifact
        if role.startswith("overrides:"): grouped_lists.setdefault("overrides", []).append((role, artifact))
        elif role.startswith("override_approvals:"): grouped_maps.setdefault("override_approvals", {})[role.split(":", 1)[1]] = artifact
        else: resolved[role] = artifact

    parameter_roles: set[str] = set(); parameter_values: dict[str, Any] = {}
    for binding in verifier["parameter_bindings"]:
        role = binding["role"]; mapping = manifest_mapping(rule_manifest, role)
        if "parameter" not in mapping["sources"] or role in parameter_roles: raise ContextValidationError("self_certification")
        parameter_roles.add(role); parameter_values[role] = decode_authority_fact(binding["value"]); resolved[role] = parameter_values[role]
    all_roles = receipt_roles | node_roles | parameter_roles
    if (receipt_roles & node_roles or receipt_roles & parameter_roles or node_roles & parameter_roles
        or set(verifier["required_role_ids"]) != all_roles or len(verifier["required_role_ids"]) != len(all_roles)):
        raise ContextValidationError("self_certification")
    if not set(rule_manifest["required_roles"]) <= all_roles: raise ContextValidationError("self_certification")
    for mapping in rule_manifest["role_mappings"]:
        count = sum(1 for role in all_roles if role == mapping["role"] and mapping["role_prefix"] is None or mapping["role_prefix"] is not None and role.startswith(mapping["role_prefix"]))
        if not mapping["minimum_cardinality"] <= count <= mapping["maximum_cardinality"]: raise ContextValidationError("self_certification")
    expected_receipts = set(REQUIRED_RECEIPT_ROLES.get(rule, set()))
    vote_facts = expected_vote_receipts(subject, node_artifacts)
    expected_receipts |= set(vote_facts)
    if receipt_roles != expected_receipts: raise ContextValidationError("self_certification")
    for role, fact in vote_facts.items():
        if resolved.get(role) != fact: raise ContextValidationError("issuer_scope_violation")
    if "overrides" in parameter_values:
        rows = [artifact for _, artifact in sorted(grouped_lists.get("overrides", []))]
        if parameter_values["overrides"] != [authority_artifact_digest(row) for row in rows]: raise ContextValidationError("self_certification")
        resolved["overrides"] = rows
    if "override_approvals" in parameter_values:
        values = grouped_maps.get("override_approvals", {})
        if parameter_values["override_approvals"] != sorted(values, key=str.encode): raise ContextValidationError("self_certification")
        resolved["override_approvals"] = values
    resolved["_authority_task_states"] = resolved.get("canonical_task_states", [])
    resolved["_authority_snapshot_digest"] = snapshot["authority_snapshot_digest"]
    return resolved


def validate_rule_context(rule: str, subject: dict, context: dict) -> None:
    typed: list[tuple[str, str | tuple[str, ...]]] = []
    canonical_rules = {"trust_rotation", "trust_revocation", "publication_commit", "publication_transition", "rollback", "generation_activation", "ak_decision", "acceptance_binding", "activation_binding"}
    if rule in canonical_rules and ("canonical_store_head" not in context or "current_decision_record_digest" not in context):
        raise ContextValidationError("self_certification")
    if rule == "lifecycle" and ("canonical_store_head" not in context or "current_deprecation_decision_record_digest" not in context or "current_removal_decision_record_digest" not in context):
        raise ContextValidationError("self_certification")
    if rule == "activation_binding" and ("current_activation_digest" not in context or "current_activation_revision" not in context or ((context["current_activation_digest"] is None) != (context["current_activation_revision"] is None))):
        raise ContextValidationError("self_certification")
    if rule == "approval_threshold": typed = [("owner_set", "semantic-owner-set.v0"), ("predicate", "semantic-approval-predicate.v0"), ("policy", "semantic-owner-policy.v0")]
    elif rule == "trust_rotation": typed = [("old_root", "semantic-trust-root.v0"), ("new_root", "semantic-trust-root.v0"), ("approval", "semantic-owner-approval.v0"), ("policy", "semantic-owner-policy.v0"), ("owner_set", "semantic-owner-set.v0"), ("predicate", "semantic-approval-predicate.v0"), ("decision", "semantic-ak-decision-reference.v0")]
    elif rule == "trust_revocation": typed = [("approval", "semantic-owner-approval.v0"), ("policy", "semantic-owner-policy.v0"), ("owner_set", "semantic-owner-set.v0"), ("predicate", "semantic-approval-predicate.v0"), ("decision", "semantic-ak-decision-reference.v0")]
    elif rule == "compatibility_policy": typed = []
    elif rule == "compatibility":
        typed = [("policy", "semantic-compatibility-policy.v0")]
        for value in context["overrides"]: expected_context(value, "semantic-compatibility-override.v0")
        for value in context["override_approvals"].values(): expected_context(value, "semantic-owner-approval.v0")
        if context["overrides"]:
            if "canonical_store_head" not in context or "current_decision_record_digest" not in context: raise ContextValidationError("self_certification")
            typed += [("owner_policy", "semantic-owner-policy.v0"), ("owner_set", "semantic-owner-set.v0"), ("predicate", "semantic-approval-predicate.v0"), ("decision", "semantic-ak-decision-reference.v0")]
    elif rule == "lifecycle":
        typed = [("deprecation", "semantic-deprecation-record.v0"), ("policy", "semantic-compatibility-policy.v0"), ("prior_tombstones", "semantic-tombstone-registry.v0"), ("resulting_tombstones", "semantic-tombstone-registry.v0"), ("deprecation_ledger", "semantic-accepted-lifecycle-ledger-record.v0"), ("removal_ledger", "semantic-accepted-lifecycle-ledger-record.v0"), ("deprecation_publication", "semantic-owner-publication.v0"), ("removal_publication", "semantic-owner-publication.v0"), ("deprecation_transaction", "semantic-publication-transaction.v0"), ("removal_transaction", "semantic-publication-transaction.v0"), ("deprecation_journal", "semantic-publication-journal.v0"), ("removal_journal", "semantic-publication-journal.v0"), ("deprecation_marker", "semantic-publication-commit-marker.v0"), ("removal_marker", "semantic-publication-commit-marker.v0"), ("deprecation_approval", "semantic-owner-approval.v0"), ("removal_approval", "semantic-owner-approval.v0"), ("deprecation_prior_status", "semantic-owner-publication.v0"), ("removal_prior_status", ("semantic-owner-publication.v0", "semantic-publication-status-transition.v0")), ("deprecation_prior_journal", "semantic-publication-journal.v0"), ("removal_prior_journal", "semantic-publication-journal.v0"), ("deprecation_canonical_ledger", "semantic-publication-ledger-head.v0"), ("removal_canonical_ledger", "semantic-publication-ledger-head.v0"), ("owner_policy", "semantic-owner-policy.v0"), ("owner_set", "semantic-owner-set.v0"), ("predicate", "semantic-approval-predicate.v0"), ("trust_root", "semantic-trust-root.v0"), ("deprecation_decision", "semantic-ak-decision-reference.v0"), ("removal_decision", "semantic-ak-decision-reference.v0")]
        expected_shape_context(context["external_trust_root_pin"], "externalTrustRootPin")
    elif rule == "tombstone_reuse": typed = [("tombstones", "semantic-tombstone-registry.v0")]
    elif rule == "publication_commit":
        typed = [("transaction", "semantic-publication-transaction.v0"), ("journal", "semantic-publication-journal.v0"), ("marker", "semantic-publication-commit-marker.v0"), ("approval", "semantic-owner-approval.v0"), ("trust_root", "semantic-trust-root.v0"), ("prior_journal", "semantic-publication-journal.v0"), ("prior_status", "semantic-owner-publication.v0"), ("policy", "semantic-owner-policy.v0"), ("owner_set", "semantic-owner-set.v0"), ("predicate", "semantic-approval-predicate.v0"), ("decision", "semantic-ak-decision-reference.v0")]
        expected_shape_context(context["external_trust_root_pin"], "externalTrustRootPin")
    elif rule == "publication_transition":
        typed = [("transaction", "semantic-publication-transaction.v0"), ("journal", "semantic-publication-journal.v0"), ("marker", "semantic-publication-commit-marker.v0"), ("prior_status", ("semantic-owner-publication.v0", "semantic-publication-status-transition.v0")), ("approval", "semantic-owner-approval.v0"), ("trust_root", "semantic-trust-root.v0"), ("policy", "semantic-owner-policy.v0"), ("owner_set", "semantic-owner-set.v0"), ("predicate", "semantic-approval-predicate.v0"), ("prior_journal", "semantic-publication-journal.v0"), ("decision", "semantic-ak-decision-reference.v0")]
        expected_shape_context(context["external_trust_root_pin"], "externalTrustRootPin")
    elif rule == "publication_recovery":
        typed = [("transaction", "semantic-publication-transaction.v0"), ("resulting_status", ("semantic-owner-publication.v0", "semantic-publication-status-transition.v0")),
            ("marker", "semantic-publication-commit-marker.v0"), ("prior_status", ("semantic-owner-publication.v0", "semantic-publication-status-transition.v0")),
            ("prior_journal", "semantic-publication-journal.v0")]
        expected_shape_context(context["before"], "publicationRecoveryState"); expected_shape_context(context["after"], "publicationRecoveryState")
    elif rule == "projection": typed = [("projection", "semantic-payload-projection.v0"), ("capsule", "semantic-release-capsule.v0"), ("archive_linkage", "semantic-capsule-archive-linkage.v0"), ("payload_manifest", "semantic-material-manifest.v0"), ("consumer_manifest", "semantic-material-manifest.v0"), ("archive_manifest", "semantic-material-manifest.v0"), ("tombstones", "semantic-tombstone-registry.v0")]
    elif rule == "rollback":
        typed = [("request", "semantic-rollback-request.v0"), ("activation", "semantic-activation-receipt.v0"), ("decision", "semantic-ak-decision-reference.v0"), ("intent", "semantic-consumer-intent.v0"), ("acceptance", "semantic-owner-acceptance.v0"), ("materialization", "semantic-materialization-verification-receipt.v0"), ("availability", "semantic-rollback-availability-proof.v0"), ("recovery_artifact", "semantic-rollback-availability-receipt.v0")]
        for key in ("semantic_artifact", "runtime_artifact", "disable_artifact", "history_after", "ak_linkage", "pi_receipt"):
            if context[key] is not None:
                schema_name = {"semantic_artifact": "semantic-rollback-availability-receipt.v0", "runtime_artifact": "semantic-rollback-availability-receipt.v0", "disable_artifact": "semantic-rollback-availability-receipt.v0", "history_after": "semantic-rollback-history-transition.v0", "ak_linkage": "semantic-ak-evidence-linkage.v0", "pi_receipt": "semantic-pi-delivery-receipt.v0"}[key]
                expected_context(context[key], schema_name)
        expected_shape_context(context["canonical_history_head"], "historyHead")
    elif rule == "generation_activation": typed = [("activation", "semantic-activation-receipt.v0"), ("decision", "semantic-ak-decision-reference.v0"), ("intent", "semantic-consumer-intent.v0"), ("acceptance", "semantic-owner-acceptance.v0"), ("materialization", "semantic-materialization-verification-receipt.v0"), ("availability", "semantic-rollback-availability-proof.v0")]
    elif rule == "ak_decision": expected_shape_context(context["canonical_store_head"], "akStoreHead")
    elif rule == "acceptance_binding": typed = [("decision", "semantic-ak-decision-reference.v0"), ("intent", "semantic-consumer-intent.v0")]
    elif rule == "activation_binding": typed = [("decision", "semantic-ak-decision-reference.v0"), ("intent", "semantic-consumer-intent.v0"), ("acceptance", "semantic-owner-acceptance.v0"), ("materialization", "semantic-materialization-verification-receipt.v0"), ("availability", "semantic-rollback-availability-proof.v0")]
    elif rule == "governance_contracts": typed = [("consumer_contract", "semantic-non-authorizing-task-contract.v0")]
    elif rule == "version_binding": expected_context(context["existing_coordinate"], "semantic-release-coordinate.v0")
    elif rule == "publication_cas" and context["existing_coordinate"] is not None: expected_context(context["existing_coordinate"], "semantic-release-coordinate.v0")
    if rule in {"rollback", "generation_activation", "activation_binding"}:
        closure_typed = [("activation_availability", "semantic-rollback-availability-proof.v0"),
            ("semantic_artifact", "semantic-rollback-availability-receipt.v0"), ("runtime_artifact", "semantic-rollback-availability-receipt.v0"),
            ("disable_artifact", "semantic-rollback-availability-receipt.v0"), ("recovery_artifact", "semantic-rollback-availability-receipt.v0"),
            ("semantic_materialization_technical", "semantic-rollback-technical-receipt.v0"), ("runtime_materialization_technical", "semantic-rollback-technical-receipt.v0"),
            ("runtime_revalidation_technical", "semantic-rollback-technical-receipt.v0"), ("disable_contract_technical", "semantic-rollback-technical-receipt.v0"),
            ("disable_rehearsal_technical", "semantic-rollback-technical-receipt.v0"), ("recovery_rehearsal_technical", "semantic-rollback-technical-receipt.v0"),
            ("recovery_health_technical", "semantic-rollback-technical-receipt.v0")]
        typed += [row for row in closure_typed if context.get(row[0]) is not None]
    integer_context_keys = ("current_revision", "prior_revision", "canonical_deprecation_revision", "canonical_removal_revision", "current_acceptance_revision", "current_activation_revision", "current_activation_head_revision", "canonical_trust_revocation_revision", "canonical_publication_revision", "canonical_recovery_epoch")
    for key in integer_context_keys:
        if key in context and context[key] is not None and (isinstance(context[key], bool) or not isinstance(context[key], int) or not 0 <= context[key] <= MAX_SAFE_INTEGER): raise ContextValidationError("malformed_input")
    digest_context_keys = ("current_head", "existing_replay_key", "current_root_digest", "prior_head", "deprecation_prior_head", "current_lifecycle_head", "canonical_deprecation_head", "canonical_removal_head", "current_activation_digest", "current_decision_record_digest", "current_deprecation_decision_record_digest", "current_removal_decision_record_digest", "canonical_trust_root_digest", "canonical_trust_revocation_head", "canonical_publication_head", "current_acceptance_digest", "canonical_publication_journal_head", "canonical_recovery_journal_head", "canonical_publication_status_digest")
    for key in digest_context_keys:
        if key in context and context[key] is not None and (not isinstance(context[key], str) or re.fullmatch(r"sha256:[0-9a-f]{64}", context[key]) is None): raise ContextValidationError("malformed_input")
    if "revoked" in context and (not isinstance(context["revoked"], list) or any(not isinstance(x, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", x) is None for x in context["revoked"])): raise ContextValidationError("malformed_input")
    if "revoked_trust_digests" in context and (not isinstance(context["revoked_trust_digests"], list) or any(not isinstance(x, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", x) is None for x in context["revoked_trust_digests"])): raise ContextValidationError("malformed_input")
    if "prior_version" in context:
        try: semver(context["prior_version"])
        except ValidationError: raise ContextValidationError("malformed_input")
    if "override_approvals" in context:
        for key, value in context["override_approvals"].items():
            approval = expected_context(value, "semantic-owner-approval.v0")
            if key != approval["owner_approval_digest"]: raise ContextValidationError("digest_mismatch")
    for key, schema_name in typed:
        expected_context(context[key], schema_name)
    if rule == "publication_commit":
        expected_context(context["transaction"], "semantic-publication-transaction.v0", subject["transaction_digest"], "lifecycle_violation")
        expected_context(context["approval"], "semantic-owner-approval.v0", subject["owner_approval_digest"], "lifecycle_violation")
        expected_context(context["prior_journal"], "semantic-publication-journal.v0", context["prior_journal_digest"], "lifecycle_violation")
    elif rule == "publication_transition":
        expected_context(context["transaction"], "semantic-publication-transaction.v0", subject["transaction_digest"], "lifecycle_violation")
        expected_context(context["prior_status"], ("semantic-owner-publication.v0", "semantic-publication-status-transition.v0"), subject["prior_status_record_digest"], "lifecycle_violation")
        expected_context(context["approval"], "semantic-owner-approval.v0", subject["owner_approval_digest"], "lifecycle_violation")
        expected_context(context["prior_journal"], "semantic-publication-journal.v0", context["prior_journal_digest"], "lifecycle_violation")
    elif rule == "rollback":
        expected_context(context["request"], "semantic-rollback-request.v0", subject["rollback_request_digest"], "history_conflict")
        expected_context(context["availability"], "semantic-rollback-availability-proof.v0", subject["availability_proof_digest"], "rollback_unavailable")
    elif rule == "activation_binding":
        expected_context(context["acceptance"], "semantic-owner-acceptance.v0", subject["owner_acceptance_digest"], "self_certification")
        expected_context(context["materialization"], "semantic-materialization-verification-receipt.v0", subject["materialization_verification_receipt_digest"], "self_certification")
        expected_context(context["availability"], "semantic-rollback-availability-proof.v0", subject["rollback_availability_proof_digest"], "rollback_unavailable")
    elif rule == "projection":
        expected_context(context["projection"], "semantic-payload-projection.v0", subject["payload_projection_digest"], "projection_mismatch")
        expected_context(context["archive_linkage"], "semantic-capsule-archive-linkage.v0", subject["capsule_archive_linkage_digest"], "projection_mismatch")
    if "canonical_lifecycle_tombstone_head" in context: expected_shape_context(context["canonical_lifecycle_tombstone_head"], "lifecycleTombstoneHead")
    if "previous_activation" in context and context["previous_activation"] is not None: expected_context(context["previous_activation"], "semantic-activation-receipt.v0")
    if "expected_action" in context: expected_shape_context(context["expected_action"], "approvalAction")
    if "canonical_store_head" in context: expected_shape_context(context["canonical_store_head"], "akStoreHead")


def condition_true(value: dict) -> bool:
    if value["kind"] == "evidence_digest_equals":
        computed = value["expected_digest"] is not None and value["expected_digest"] == value["actual_digest"] and value["expected_integer"] is None and value["actual_integer"] is None
    else:
        computed = value["expected_digest"] is None and value["actual_digest"] is None and value["expected_integer"] is not None and value["actual_integer"] is not None and value["actual_integer"] >= value["expected_integer"]
    return value["satisfied"] == computed and computed


def technical_receipt_valid(receipt: dict, kind: str, issuer_kind: str, referenced: str | None = None) -> bool:
    return (receipt["receipt_kind"] == kind and receipt["issuer"]["kind"] == issuer_kind and receipt["outcome"] == "valid"
        and receipt["referenced_receipt_digest"] == referenced)


def rollback_availability_valid(intent: dict, acceptance: dict, materialization: dict, proof: dict, context: dict, target: dict | None = None) -> bool:
    target = target or intent["rollback_target"]
    if not (proof["consumer_intent_digest"] == intent["consumer_intent_digest"] == materialization["consumer_intent_digest"]
        and proof["owner_acceptance_digest"] == acceptance["owner_acceptance_digest"] == materialization["owner_acceptance_digest"]
        and proof["materialization_verification_receipt_digest"] == materialization["materialization_verification_receipt_digest"]
        and proof["recovery_controller_id"] == context["canonical_recovery_controller_id"]
        and proof["recovery_epoch"] == proof["availability_epoch"] == context["canonical_recovery_epoch"]
        and proof["availability_epoch"] >= acceptance["acceptance_epoch"] and proof["target_kind"] == target["kind"]
        and proof["recovery_runtime_available"]): return False
    recovery, rr, rh = context["recovery_artifact"], context["recovery_rehearsal_technical"], context["recovery_health_technical"]
    if not (recovery["issuer"]["kind"] == "recovery_controller"
        and recovery["issuer"]["id"] == proof["recovery_controller_id"] == context["canonical_recovery_controller_id"]
        and rr["issuer"]["id"] == rh["issuer"]["id"] == recovery["issuer"]["id"] and recovery["artifact_kind"] == "recovery_runtime"
        and recovery["rollback_available_artifact_digest"] == proof["recovery_artifact_digest"]
        and recovery["runtime_identity"] == proof["recovery_runtime_identity"] == context["canonical_recovery_runtime_identity"]
        and recovery["rehearsal_receipt_digest"] == rr["rollback_technical_receipt_digest"]
        and recovery["health_receipt_digest"] == rh["rollback_technical_receipt_digest"]
        and technical_receipt_valid(rr, "rehearsal", "recovery_controller")
        and technical_receipt_valid(rh, "health", "recovery_controller", rr["rollback_technical_receipt_digest"])
        and rr["subject_digest"] == rh["subject_digest"] == recovery["runtime_identity"]["distribution_digest"]
        and rr["coordinate"] is None and rh["coordinate"] is None
        and rr["runtime_identity"] == rh["runtime_identity"] == recovery["runtime_identity"] and recovery["availability_epoch"] == proof["availability_epoch"]): return False
    if target["kind"] in {"semantic", "combined"}:
        st = target if target["kind"] == "semantic" else target["semantic_stage"]
        artifact, receipt = context["semantic_artifact"], context["semantic_materialization_technical"]
        if not (artifact["issuer"]["kind"] == "rocs" and artifact["issuer"]["id"] == receipt["issuer"]["id"] == materialization["issuer"]["id"] and artifact["artifact_kind"] == "semantic_target"
            and artifact["rollback_available_artifact_digest"] == proof["semantic_target_artifact_digest"]
            and artifact["coordinate"] == st["target_coordinate"] == proof["semantic_coordinate"]
            and artifact["materialization_receipt_digest"] == st["target_materialization_receipt_digest"] == proof["semantic_materialization_receipt_digest"] == receipt["rollback_technical_receipt_digest"]
            and technical_receipt_valid(receipt, "materialization", "rocs")
            and receipt["subject_digest"] == st["target_coordinate"]["capsule_digest"]
            and receipt["coordinate"] == st["target_coordinate"] and receipt["runtime_identity"] == materialization["runtime_identity"]): return False
    if target["kind"] in {"runtime", "combined"}:
        rt = target if target["kind"] == "runtime" else target["runtime_stage"]
        artifact, mat, rv = context["runtime_artifact"], context["runtime_materialization_technical"], context["runtime_revalidation_technical"]
        if not (artifact["issuer"]["kind"] == "rocs" and artifact["issuer"]["id"] == mat["issuer"]["id"] == rv["issuer"]["id"] == materialization["issuer"]["id"] and artifact["artifact_kind"] == "runtime_target"
            and artifact["rollback_available_artifact_digest"] == proof["runtime_target_artifact_digest"]
            and artifact["runtime_identity"] == rt["target_runtime_identity"] == proof["runtime_identity"]
            and artifact["materialization_receipt_digest"] == rt["target_materialization_receipt_digest"] == proof["runtime_materialization_receipt_digest"] == mat["rollback_technical_receipt_digest"]
            and artifact["runtime_revalidation_receipt_digest"] == rt["runtime_revalidation_receipt_digest"] == proof["runtime_revalidation_receipt_digest"] == rv["rollback_technical_receipt_digest"]
            and technical_receipt_valid(mat, "materialization", "rocs") and technical_receipt_valid(rv, "runtime_revalidation", "rocs", mat["rollback_technical_receipt_digest"])
            and mat["subject_digest"] == rt["target_runtime_identity"]["distribution_digest"]
            and rv["subject_digest"] == materialization["coordinate"]["capsule_digest"]
            and mat["coordinate"] == rv["coordinate"] == materialization["coordinate"]
            and mat["runtime_identity"] == rv["runtime_identity"] == rt["target_runtime_identity"]): return False
    if target["kind"] == "no_prior_disable":
        artifact, contract, rehearsal = context["disable_artifact"], context["disable_contract_technical"], context["disable_rehearsal_technical"]
        if not (artifact["issuer"]["kind"] == "consumer_owner" and artifact["issuer"]["id"] == contract["issuer"]["id"] == acceptance["acceptance_authority"]["id"] and rehearsal["issuer"]["id"] == recovery["issuer"]["id"] and artifact["artifact_kind"] == "disable_target"
            and artifact["rollback_available_artifact_digest"] == proof["disable_target_artifact_digest"]
            and artifact["disable_contract_digest"] == target["disable_contract_digest"] == proof["disable_contract_digest"] == contract["rollback_technical_receipt_digest"]
            and artifact["rehearsal_receipt_digest"] == target["rehearsal_receipt_digest"] == proof["rehearsal_receipt_digest"] == rehearsal["rollback_technical_receipt_digest"]
            and technical_receipt_valid(contract, "disable_contract", "consumer_owner")
            and technical_receipt_valid(rehearsal, "rehearsal", "recovery_controller", contract["rollback_technical_receipt_digest"])): return False
    return True


def semantic_trust_current(intent: dict, materialization: dict, context: dict) -> bool:
    trust = intent["trust_reference"]
    return (materialization["trust_reference"] == trust
        and trust["trust_root_digest"] == context["canonical_trust_root_digest"]
        and trust["local_revocation_revision"] == context["canonical_trust_revocation_revision"]
        and trust["local_revocation_head_digest"] == context["canonical_trust_revocation_head"]
        and trust["publication_ledger_revision"] == context["canonical_publication_revision"]
        and trust["publication_digest"] == context["canonical_publication_head"]
        and trust["trust_root_digest"] not in context["revoked_trust_digests"])


def activation_chain_valid(activation: dict, context: dict, candidate: bool = False) -> bool:
    intent, acceptance, materialization, decision = context["intent"], context["acceptance"], context["materialization"], context["decision"]
    availability = context.get("activation_availability") or context["availability"]
    previous = context["previous_activation"]
    if candidate:
        pointer_digest, pointer_revision = context["current_activation_digest"], context["current_activation_revision"]
        genesis = (pointer_digest is None and pointer_revision is None and previous is None and activation["activation_revision"] == 1
            and activation["prior_activation_revision"] is None and activation["previous_activation_receipt_digest"] is None
            and activation["current_activation_head_digest"] is None)
        successor = (pointer_digest is not None and pointer_revision is not None and previous is not None
            and previous["activation_receipt_digest"] == pointer_digest and previous["activation_revision"] == pointer_revision
            and activation["previous_activation_receipt_digest"] == activation["current_activation_head_digest"] == pointer_digest
            and activation["prior_activation_revision"] == pointer_revision and activation["activation_revision"] == pointer_revision + 1
            and activation["activation_epoch"] > previous["activation_epoch"])
        continuity = genesis or successor
    else:
        continuity = ((previous is None and activation["activation_revision"] == 1 and activation["prior_activation_revision"] is None
                and activation["previous_activation_receipt_digest"] is None and activation["current_activation_head_digest"] is None)
            or (previous is not None and activation["previous_activation_receipt_digest"] == activation["current_activation_head_digest"] == previous["activation_receipt_digest"]
                and activation["prior_activation_revision"] == previous["activation_revision"] and activation["activation_revision"] == previous["activation_revision"] + 1
                and activation["activation_epoch"] > previous["activation_epoch"]))
    return (decision_current(decision, context) and continuity and semantic_trust_current(intent, materialization, context)
        and activation["status"] == "activated" and activation["revoked_by_digest"] is None and activation["superseded_by_activation_receipt_digest"] is None
        and activation["issuer"]["kind"] == "consumer_owner" and activation["issuer"]["id"] == activation["consumer_owner_issuer_id"] == intent["consumer_repository"]["owner"]
        and activation["consumer_intent_digest"] == intent["consumer_intent_digest"]
        and activation["owner_acceptance_digest"] == acceptance["owner_acceptance_digest"]
        and activation["materialization_verification_receipt_digest"] == materialization["materialization_verification_receipt_digest"]
        and activation["rollback_availability_proof_digest"] == availability["rollback_availability_proof_digest"]
        and rollback_availability_valid(intent, acceptance, materialization, availability, context)
        and acceptance["consumer_intent_digest"] == intent["consumer_intent_digest"] == materialization["consumer_intent_digest"]
        and materialization["owner_acceptance_digest"] == acceptance["owner_acceptance_digest"]
        and activation["consumer_repository"] == acceptance["consumer_repository"] == intent["consumer_repository"] == materialization["consumer_repository"]
        and activation["coordinate"] == intent["desired_coordinate"] == materialization["coordinate"]
        and activation["runtime_identity"] == intent["runtime_identity"] == materialization["runtime_identity"]
        and activation["activation_scope"] == acceptance["accepted_posture"] == intent["requested_posture"]
        and acceptance["acceptance_authority"]["kind"] == "consumer_owner" and acceptance["acceptance_authority"]["id"] == intent["consumer_repository"]["owner"]
        and acceptance["revoked_by_digest"] is None and acceptance["owner_acceptance_digest"] == context["current_acceptance_digest"]
        and acceptance["acceptance_revision"] == context["current_acceptance_revision"] and intent["intent_revision"] <= acceptance["valid_through_intent_revision"]
        and activation["acceptance_epoch"] == acceptance["acceptance_epoch"] <= availability["availability_epoch"] <= activation["activation_epoch"] <= acceptance["activation_epoch_not_after"]
        and intent["decision_reference_digest"] == acceptance["decision_reference_digest"] == activation["gate_decision_reference_digest"] == decision["ak_decision_reference_digest"]
        and acceptance["governing_scope_digest"] == decision["scope_digest"] and materialization["rollback_ready"] and materialization["journal_state"] == "committed"
        and materialization["rollback_target"] == intent["rollback_target"] and materialization["verifier_contract_digest"] == intent["verifier_contract_digest"]
        and materialization["compatibility_outcome"] == intent["accepted_compatibility"] and activation["activation_target_digest"] == decision["activation_target_digest"]
        and all(activation[k] == decision[k] for k in ("evidence_criteria_digest", "rollback_plan_digest", "stop_conditions_digest")))


def decision_current(subject: dict, context: dict) -> bool:
    canonical = context["canonical_store_head"]
    return (subject["lifecycle_state"] == "accepted" and subject["adr_reference"]["status"] == "accepted" and subject["revocation_digest"] is None
        and subject["superseded_by_decision_record_digest"] is None and subject["ak_store_head"] == canonical
        and context["current_decision_record_digest"] == subject["decision_record_digest"])


def publication_authority_valid(approval: dict, context: dict, coordinate: dict, expected_action: dict | None = None) -> bool:
    policy, owner_set, predicate, decision = context["policy"], context["owner_set"], context["predicate"], context["decision"]
    root, pin, action = context["trust_root"], context["external_trust_root_pin"], approval["action"]
    action_exact = expected_action is None or action == expected_action
    if action["kind"] == "release": action_exact = action_exact and action["candidate_capsule_digest"] == coordinate["capsule_digest"]
    trust_exact = (root["namespace"] == pin["namespace"] == policy["namespace"] == owner_set["namespace"] == predicate["namespace"] == approval["namespace"] == coordinate["namespace"]
        and root["owner_policy_digest"] == pin["owner_policy_digest"] == policy["owner_policy_digest"] == approval["owner_policy_digest"]
        and root["owner_set_digest"] == pin["owner_set_digest"] == owner_set["owner_set_digest"] == approval["owner_set_digest"]
        and root["trust_root_id"] == pin["trust_root_id"] and root["trust_root_revision"] == pin["trust_root_revision"]
        and root["trust_root_digest"] == pin["trust_root_digest"] == context["canonical_trust_root_digest"] and root["status"] == "active"
        and pin["revocation_revision"] == context["canonical_trust_revocation_revision"]
        and pin["revocation_head_digest"] == context["canonical_trust_revocation_head"]
        and root["trust_root_digest"] not in context["revoked_trust_digests"]
        and not any(vote["approval_proof_digest"] in context["revoked_trust_digests"] for vote in approval["votes"]))
    return (trust_exact and evaluate("approval_threshold", approval, {"policy": policy, "owner_set": owner_set, "predicate": predicate}, _resolved=True) is None
        and approval["decision_reference_digest"] == decision["ak_decision_reference_digest"] and decision_current(decision, context)
        and action_exact and action_digest(action) == approval["action_digest"])


def prior_publication_chain_valid(tx: dict, prior_status: dict, prior_journal: dict) -> bool:
    prior_digest = prior_status.get("owner_publication_digest", prior_status.get("publication_status_transition_digest"))
    return (prior_digest == tx["expected_prior_head_digest"] and prior_status["ledger_revision"] == tx["expected_prior_revision"]
        and prior_journal["transaction_digest"] == prior_status["transaction_digest"]
        and prior_journal["resulting_record_digest"] == prior_digest and prior_journal["resulting_ledger_head_digest"] == prior_digest
        and prior_journal["resulting_ledger_revision"] == prior_status["ledger_revision"] and prior_journal["state"] == "committed"
        and prior_journal["linearized"] and prior_journal["recovery_action"] == "none")

def lifecycle_publication_endpoint_valid(prefix: str, context: dict) -> bool:
    pub, tx, journal, marker, approval = (context[f"{prefix}_{x}"] for x in ("publication", "transaction", "journal", "marker", "approval"))
    prior, prior_journal, ledger = context[f"{prefix}_prior_status"], context[f"{prefix}_prior_journal"], context[f"{prefix}_canonical_ledger"]
    decision = context[f"{prefix}_decision"]
    authority_context = {"policy": context["owner_policy"], "owner_set": context["owner_set"], "predicate": context["predicate"], "decision": decision,
        "canonical_store_head": context["canonical_store_head"], "current_decision_record_digest": context[f"current_{prefix}_decision_record_digest"],
        "trust_root": context["trust_root"], "external_trust_root_pin": context["external_trust_root_pin"],
        "canonical_trust_root_digest": context["canonical_trust_root_digest"],
        "canonical_trust_revocation_revision": context["canonical_trust_revocation_revision"],
        "canonical_trust_revocation_head": context["canonical_trust_revocation_head"], "revoked_trust_digests": context["revoked_trust_digests"]}
    result = pub["owner_publication_digest"]
    return (publication_authority_valid(approval, authority_context, pub["coordinate"])
        and prior_publication_chain_valid(tx, prior, prior_journal) and tx["operation"] == "publish" and tx["status_reason_digest"] is None
        and tx["coordinate"] == pub["coordinate"] and tx["namespace"] == tx["coordinate"]["namespace"] == pub["ledger_namespace"] == pub["coordinate"]["namespace"]
        and pub["transaction_digest"] == tx["publication_transaction_digest"] == journal["transaction_digest"] == marker["transaction_digest"]
        and pub["owner_approval_digest"] == tx["owner_approval_digest"] == approval["owner_approval_digest"]
        and pub["trust_root_digest"] == context["trust_root"]["trust_root_digest"] and pub["ledger_revision"] == tx["expected_prior_revision"] + 1
        and journal["prior_journal_digest"] == prior_journal["publication_journal_digest"] and journal["state"] == "committed" and journal["linearized"] and journal["recovery_action"] == "none"
        and journal["resulting_record_digest"] == journal["resulting_ledger_head_digest"] == result and journal["resulting_ledger_revision"] == pub["ledger_revision"]
        and marker["journal_digest"] == journal["publication_journal_digest"] and marker["resulting_record_digest"] == marker["resulting_ledger_head_digest"] == result
        and marker["resulting_ledger_revision"] == pub["ledger_revision"] and marker["fsync_complete"]
        and ledger["namespace"] == pub["ledger_namespace"] and ledger["ledger_revision"] == pub["ledger_revision"]
        and ledger["ledger_head_digest"] == ledger["status_record_digest"] == result and ledger["transaction_digest"] == tx["publication_transaction_digest"]
        and ledger["journal_digest"] == journal["publication_journal_digest"] and ledger["commit_marker_digest"] == marker["publication_commit_marker_digest"]
        and ledger["prior_ledger_head_digest"] == tx["expected_prior_head_digest"])

def evaluate(rule: str, subject: dict, context: dict, *, _resolved: bool = False) -> str | None:
    if not _resolved:
        try: context = authority_preflight(rule, subject, context)
        except ContextValidationError as exc: return exc.code
    if rule != "digest":
        try: validate_rule_context(rule, subject, context)
        except ContextValidationError as exc: return exc.code
    if rule == "digest": return None if fixture_digest_valid(subject) else "digest_mismatch"
    if rule == "approval_threshold":
        owner_set, predicate, policy = context["owner_set"], context["predicate"], context["policy"]
        exact = subject["namespace"] == policy["namespace"] == owner_set["namespace"] == predicate["namespace"] and subject["owner_policy_digest"] == policy["owner_policy_digest"] and subject["owner_set_digest"] == policy["owner_set_digest"] == owner_set["owner_set_digest"] and subject["approval_predicate_digest"] == policy["approval_predicate_digest"] == predicate["approval_predicate_digest"]
        if not exact: return "approval_threshold_unsatisfied"
        members = {x["owner_id"]: x for x in owner_set["members"]}
        active = {key for key, value in members.items() if value["status"] == "active"}
        if action_digest(subject["action"]) != subject["action_digest"]: return "approval_threshold_unsatisfied"
        eligible: set[str] = set()
        for vote in subject["votes"]:
            member = members.get(vote["owner_id"])
            if member and member["status"] == "revoked": return "trust_revoked"
            if not member or vote["owner_key_id"] not in member["key_ids"] or vote["approved_action_digest"] != subject["action_digest"] or vote["owner_id"] in eligible: return "approval_threshold_unsatisfied"
            eligible.add(vote["owner_id"])
        if predicate["mode"] == "unanimous":
            if predicate["threshold"] != len(active): return "approval_threshold_unsatisfied"
            needed = len(active)
        else:
            needed = predicate["threshold"]
            if needed < 1 or needed > len(active): return "approval_threshold_unsatisfied"
        approved = eligible == active if predicate["mode"] == "unanimous" else len(eligible) >= needed
        return None if approved else "approval_threshold_unsatisfied"
    if rule == "trust_rotation":
        old, new, approval, policy = context["old_root"], context["new_root"], context["approval"], context["policy"]
        owner_set, predicate = context["owner_set"], context["predicate"]
        if old["trust_root_digest"] in context["revoked"]: return "trust_revoked"
        action = approval["action"]
        exact_authority = subject["namespace"] == old["namespace"] == new["namespace"] == policy["namespace"] == owner_set["namespace"] == predicate["namespace"] == approval["namespace"] and subject["owner_policy_digest"] == policy["owner_policy_digest"] == old["owner_policy_digest"] == new["owner_policy_digest"] == approval["owner_policy_digest"] and subject["owner_set_digest"] == policy["owner_set_digest"] == old["owner_set_digest"] == new["owner_set_digest"] == approval["owner_set_digest"] == owner_set["owner_set_digest"] and subject["approval_predicate_digest"] == policy["approval_predicate_digest"] == approval["approval_predicate_digest"] == predicate["approval_predicate_digest"]
        transition = subject["old_trust_root_digest"] == context["current_root_digest"] == old["trust_root_digest"] and subject["old_trust_root_id"] == old["trust_root_id"] and subject["old_trust_root_revision"] == old["trust_root_revision"] and subject["new_trust_root_digest"] == new["trust_root_digest"] and subject["new_trust_root_id"] == new["trust_root_id"] and subject["new_trust_root_revision"] == new["trust_root_revision"] == old["trust_root_revision"] + 1 and new["prior_trust_root_digest"] == old["trust_root_digest"] and subject["rotation_revision"] == new["trust_root_revision"]
        action_expected = {"kind": "trust_rotation", "namespace": subject["namespace"], "old_trust_root_digest": subject["old_trust_root_digest"], "new_trust_root_digest": subject["new_trust_root_digest"], "owner_policy_digest": subject["owner_policy_digest"], "owner_set_digest": subject["owner_set_digest"], "approval_predicate_digest": subject["approval_predicate_digest"], "new_trust_root_revision": subject["new_trust_root_revision"], "rotation_revision": subject["rotation_revision"]}
        approval_threshold_valid = evaluate("approval_threshold", approval, {"policy": policy, "owner_set": owner_set, "predicate": predicate}, _resolved=True) is None
        valid = (exact_authority and transition and approval_threshold_valid and subject["approval_digest"] == approval["owner_approval_digest"]
            and approval["decision_reference_digest"] == context["decision"]["ak_decision_reference_digest"]
            and decision_current(context["decision"], context) and action == action_expected and action_digest(action) == approval["action_digest"])
        return None if valid else "trust_reference_stale"
    if rule == "trust_revocation":
        approval = context["approval"]; action = approval["action"]
        expected_revision = context["prior_revision"] + 1
        policy, owner_set, predicate = context["policy"], context["owner_set"], context["predicate"]
        authority = subject["namespace"] == policy["namespace"] == owner_set["namespace"] == predicate["namespace"] == approval["namespace"] and approval["owner_policy_digest"] == policy["owner_policy_digest"] and approval["owner_set_digest"] == policy["owner_set_digest"] == owner_set["owner_set_digest"] and approval["approval_predicate_digest"] == policy["approval_predicate_digest"] == predicate["approval_predicate_digest"]
        approval_threshold_valid = evaluate("approval_threshold", approval, {"policy": policy, "owner_set": owner_set, "predicate": predicate}, _resolved=True) is None
        valid = (authority and approval_threshold_valid and subject["revocation_revision"] == expected_revision and subject["prior_revocation_digest"] == context["prior_head"]
            and subject["owner_approval_digest"] == approval["owner_approval_digest"] and approval["decision_reference_digest"] == context["decision"]["ak_decision_reference_digest"]
            and decision_current(context["decision"], context) and action["kind"] == "trust_revocation" and action_digest(action) == approval["action_digest"]
            and all(subject[k] == action[k] for k in ("namespace", "target_kind", "target_digest", "effective_ledger_revision", "reason_digest", "prior_revocation_digest", "revocation_revision"))
            and action["owner_policy_digest"] == policy["owner_policy_digest"] and action["owner_set_digest"] == owner_set["owner_set_digest"] and action["approval_predicate_digest"] == predicate["approval_predicate_digest"])
        return None if valid else "trust_reference_stale"
    if rule == "compatibility_policy":
        cats = [x["category"] for x in subject["category_rules"]]; expected = {"addition", "documentation", "compatible_refinement", "deprecation", "removal", "rename", "constraint_change", "relation_change", "identifier_reuse", "other"}
        return None if len(cats) == 10 and set(cats) == expected else "compatibility_rejected"
    if rule == "compatibility":
        policy = context["policy"]
        if subject["compatibility_policy_digest"] != policy["compatibility_policy_digest"]: return "compatibility_rejected"
        rules = {x["category"]: x for x in policy["category_rules"]}; conditions = {x["condition_id"]: x for x in subject["conditions"]}
        if len(conditions) != len(subject["conditions"]): return "compatibility_rejected"
        override_rows = context["overrides"]; overrides = {x["change_digest"]: x for x in override_rows}
        if len(overrides) != len(override_rows): return "compatibility_rejected"
        used_conditions: set[str] = set(); used_overrides: list[str] = []; effective: list[tuple[str, str]] = []
        for change in subject["changes"]:
            row = rules.get(change["category"])
            if not row or change["classification"] != row["classification"] or change["semver_effect"] != row["semver_effect"] or (row["condition_rule"] is None) != (change["condition_id"] is None): return "compatibility_rejected"
            classification, effect = change["classification"], change["semver_effect"]
            if change["condition_id"] is not None:
                condition = conditions.get(change["condition_id"]); used_conditions.add(change["condition_id"])
                if not condition or condition["kind"] != row["condition_rule"]["condition_kind"] or not condition_true(condition): return "compatibility_rejected"
            override = overrides.get(change_digest(change))
            if override:
                approval = context["override_approvals"].get(override["owner_approval_digest"])
                action = approval and approval["action"]
                expected_action = {k: copy.deepcopy(override[k]) for k in ("namespace", "compatibility_policy_digest", "change", "change_digest", "from_classification", "from_semver_effect", "to_classification", "semver_effect_floor", "condition")}; expected_action["kind"] = "compatibility_override"
                ranks = {"patch": 0, "minor": 1, "major": 2, "unknown": 2}
                non_lowering = ranks[override["semver_effect_floor"]] >= ranks[effect]
                approval_valid = bool(approval) and evaluate("approval_threshold", approval, {"policy": context["owner_policy"], "owner_set": context["owner_set"], "predicate": context["predicate"]}, _resolved=True) is None
                valid = approval_valid and approval["decision_reference_digest"] == context["decision"]["ak_decision_reference_digest"] and decision_current(context["decision"], context) and approval["namespace"] == override["namespace"] and context["owner_policy"]["compatibility_policy_digest"] == subject["compatibility_policy_digest"] and row["override_allowed"] and change["category"] != "identifier_reuse" and override["namespace"] == subject["namespace"] and override["compatibility_policy_digest"] == subject["compatibility_policy_digest"] and override["change"] == change and override["change_digest"] == change_digest(change) and override["from_classification"] == classification and override["from_semver_effect"] == effect and condition_true(override["condition"]) and non_lowering and action == expected_action and action_digest(action) == approval["action_digest"]
                if not valid: return "compatibility_rejected"
                classification, effect = override["to_classification"], override["semver_effect_floor"]; used_overrides.append(override["compatibility_override_digest"])
            effective.append((classification, effect))
        condition_refs = [x["condition_id"] for x in subject["changes"] if x["condition_id"] is not None]
        if len(condition_refs) != len(set(condition_refs)) or set(conditions) != used_conditions or len(condition_refs) != len(conditions) or sorted(used_overrides) != subject["override_digests"] or set(overrides) != {change_digest(x) for x in subject["changes"] if change_digest(x) in overrides}: return "compatibility_rejected"
        class_rank = {"compatible": 0, "conditionally_compatible": 1, "breaking": 2, "unknown": 3}; effect_rank = {"patch": 0, "minor": 1, "major": 2, "unknown": 3}
        classification = max((x[0] for x in effective), key=class_rank.get, default="compatible"); effect = max((x[1] for x in effective), key=effect_rank.get, default="patch")
        if subject["classification"] != classification or subject["required_semver_effect"] != effect: return "compatibility_rejected"
        if classification == "unknown" or effect == "unknown": return "compatibility_unknown"
        old = semver(context["prior_version"]); new = semver(subject["candidate_version"])
        if compare_semver(new, old) <= 0: return "semver_violation"
        major_cmp, minor_cmp = compare_integer_text(new[0], old[0]), compare_integer_text(new[1], old[1])
        valid = effect == "patch" and major_cmp == 0 and minor_cmp == 0 and compare_integer_text(new[2], old[2]) > 0 or effect == "minor" and (major_cmp > 0 or major_cmp == 0 and minor_cmp > 0) or effect == "major" and major_cmp > 0
        return None if valid else "semver_violation"
    if rule == "lifecycle":
        dep, policy, prior, resulting = context["deprecation"], context["policy"], context["prior_tombstones"], context["resulting_tombstones"]
        expected_entry = {"semantic_id": subject["semantic_id"], "reason": context["reason"], "origin_record_digest": subject["removal_record_digest"]}
        expected_entries = copy.deepcopy(prior["entries"]) + [expected_entry]
        expected_entries.sort(key=lambda x: x["semantic_id"].encode())
        exact_chain = (dep["prior_lifecycle_digest"] == context["deprecation_prior_head"]
            and subject["prior_lifecycle_digest"] == context["current_lifecycle_head"] == dep["deprecation_record_digest"])
        valid = subject["namespace"] == dep["namespace"] == dep["introduced_coordinate"]["namespace"] == subject["removed_coordinate"]["namespace"] == policy["namespace"] == prior["namespace"] == resulting["namespace"] and subject["semantic_id"] == dep["semantic_id"] and subject["deprecation_record_digest"] == dep["deprecation_record_digest"] and exact_chain and subject["deprecation_ledger_revision"] == dep["introduced_ledger_revision"] and subject["removed_ledger_revision"] > subject["deprecation_ledger_revision"] and subject["required_interval"] == policy["minimum_deprecation_releases"] and subject["removed_ledger_revision"] - subject["deprecation_ledger_revision"] >= subject["required_interval"] and subject["compatibility_policy_digest"] == policy["compatibility_policy_digest"] and subject["prior_tombstone_registry_digest"] == prior["tombstone_registry_digest"] and resulting["prior_registry_digest"] == prior["tombstone_registry_digest"] and resulting["registry_revision"] == prior["registry_revision"] + 1 and subject["semantic_id"] not in {x["semantic_id"] for x in prior["entries"]} and resulting["entries"] == expected_entries
        dep_ledger, rem_ledger = context["deprecation_ledger"], context["removal_ledger"]
        dep_pub, rem_pub = context["deprecation_publication"], context["removal_publication"]
        accepted_records = dep_ledger["namespace"] == rem_ledger["namespace"] == subject["namespace"] and dep_ledger["ledger_revision"] == dep["introduced_ledger_revision"] == context["canonical_deprecation_revision"] and dep_ledger["ledger_head_digest"] == context["canonical_deprecation_head"] == dep_pub["owner_publication_digest"] and dep_ledger["coordinate"] == dep["introduced_coordinate"] == dep_pub["coordinate"] and dep_ledger["publication_status_record_digest"] == dep_pub["owner_publication_digest"] and rem_ledger["ledger_revision"] == subject["removed_ledger_revision"] == context["canonical_removal_revision"] and rem_ledger["ledger_head_digest"] == context["canonical_removal_head"] == rem_pub["owner_publication_digest"] and rem_ledger["coordinate"] == subject["removed_coordinate"] == rem_pub["coordinate"] and rem_ledger["publication_status_record_digest"] == rem_pub["owner_publication_digest"] and dep_pub["status"] == rem_pub["status"] == "published" and dep_ledger["accepted_for_lifecycle"] and rem_ledger["accepted_for_lifecycle"]
        ledger_bindings = (dep_ledger["publication_transaction_digest"] == context["deprecation_transaction"]["publication_transaction_digest"]
            and dep_ledger["publication_journal_digest"] == context["deprecation_journal"]["publication_journal_digest"]
            and dep_ledger["publication_commit_marker_digest"] == context["deprecation_marker"]["publication_commit_marker_digest"]
            and dep_ledger["owner_approval_digest"] == context["deprecation_approval"]["owner_approval_digest"]
            and dep_ledger["trust_root_digest"] == context["trust_root"]["trust_root_digest"]
            and dep_ledger["canonical_ledger_digest"] == context["deprecation_canonical_ledger"]["publication_ledger_head_digest"]
            and rem_ledger["publication_transaction_digest"] == context["removal_transaction"]["publication_transaction_digest"]
            and rem_ledger["publication_journal_digest"] == context["removal_journal"]["publication_journal_digest"]
            and rem_ledger["publication_commit_marker_digest"] == context["removal_marker"]["publication_commit_marker_digest"]
            and rem_ledger["owner_approval_digest"] == context["removal_approval"]["owner_approval_digest"]
            and rem_ledger["trust_root_digest"] == context["trust_root"]["trust_root_digest"]
            and rem_ledger["canonical_ledger_digest"] == context["removal_canonical_ledger"]["publication_ledger_head_digest"])
        endpoints = lifecycle_publication_endpoint_valid("deprecation", context) and lifecycle_publication_endpoint_valid("removal", context)
        return None if valid and accepted_records and ledger_bindings and endpoints else "lifecycle_violation"
    if rule == "tombstone_reuse":
        current = context["canonical_lifecycle_tombstone_head"]; tombstones = context["tombstones"]
        current_exact = (current["namespace"] == tombstones["namespace"]
            and current["tombstone_registry_digest"] == tombstones["tombstone_registry_digest"]
            and current["tombstone_registry_revision"] == tombstones["registry_revision"])
        reused = any(x["semantic_id"] in {y["semantic_id"] for y in tombstones["entries"]} for x in subject["changes"])
        return None if current_exact and not reused else "lifecycle_violation"
    if rule == "publication_cas":
        if subject["operation"] == "publish" and subject["status_reason_digest"] is not None or subject["operation"] in {"withdraw", "revoke"} and subject["status_reason_digest"] is None: return "lifecycle_violation"
        if context["existing_replay_key"] == subject["replay_key_digest"] and context["existing_coordinate"] == subject["coordinate"] and context["existing_operation"] == subject["operation"]: return None
        if subject["expected_prior_revision"] != context["current_revision"]: return "publication_conflict"
        return None if subject["expected_prior_head_digest"] == context["current_head"] else "publication_fork"
    if rule == "version_binding":
        old, new = context["existing_coordinate"], subject["coordinate"]
        return "version_conflict" if (old["namespace"], old["semantic_version"]) == (new["namespace"], new["semantic_version"]) and old["capsule_digest"] != new["capsule_digest"] else None
    if rule == "publication_commit":
        tx, journal, marker = context["transaction"], context["journal"], context["marker"]; result_digest = subject["owner_publication_digest"]
        authority_valid = publication_authority_valid(context["approval"], context, subject["coordinate"], context["expected_action"])
        prior_valid = (prior_publication_chain_valid(tx, context["prior_status"], context["prior_journal"])
            and tx["expected_prior_revision"] == context["canonical_publication_revision"]
            and tx["expected_prior_head_digest"] == context["canonical_publication_head"]
            and context["prior_journal"]["publication_journal_digest"] == context["canonical_publication_journal_head"])
        valid = authority_valid and prior_valid and tx["operation"] == "publish" and tx["status_reason_digest"] is None and subject["transaction_digest"] == tx["publication_transaction_digest"] == journal["transaction_digest"] == marker["transaction_digest"] and subject["coordinate"] == tx["coordinate"] and subject["ledger_namespace"] == tx["namespace"] == tx["coordinate"]["namespace"] and subject["owner_approval_digest"] == tx["owner_approval_digest"] == context["approval"]["owner_approval_digest"] and subject["trust_root_digest"] == context["trust_root"]["trust_root_digest"] and subject["prior_publication_digest"] == tx["expected_prior_head_digest"] and subject["ledger_revision"] == tx["expected_prior_revision"] + 1 and journal["state"] == "committed" and journal["linearized"] and journal["recovery_action"] == "none" and journal["resulting_record_digest"] == journal["resulting_ledger_head_digest"] == result_digest and journal["resulting_ledger_revision"] == subject["ledger_revision"] and journal["prior_journal_digest"] == context["prior_journal_digest"] == context["prior_journal"]["publication_journal_digest"] and marker["journal_digest"] == journal["publication_journal_digest"] and marker["resulting_record_digest"] == marker["resulting_ledger_head_digest"] == result_digest and marker["resulting_ledger_revision"] == subject["ledger_revision"] and marker["fsync_complete"]
        return None if valid else "lifecycle_violation"
    if rule == "publication_transition":
        tx, journal, marker = context["transaction"], context["journal"], context["marker"]; result_digest = subject["publication_status_transition_digest"]
        op = "withdraw" if subject["to_status"] == "withdrawn" else "revoke"
        prior = context["prior_status"]
        prior_digest = prior.get("owner_publication_digest", prior.get("publication_status_transition_digest"))
        prior_status = prior.get("status", prior.get("to_status"))
        valid_from = subject["from_status"] == prior_status and prior_digest == subject["prior_status_record_digest"] and prior["coordinate"] == subject["coordinate"] and prior["ledger_revision"] == tx["expected_prior_revision"]
        approval, policy, owner_set, predicate = context["approval"], context["policy"], context["owner_set"], context["predicate"]
        expected_kind = "publication_withdrawal" if op == "withdraw" else "publication_revocation"
        expected_action = {"kind": expected_kind, "operation": op, "namespace": tx["namespace"], "owner_policy_digest": policy["owner_policy_digest"], "owner_set_digest": owner_set["owner_set_digest"], "approval_predicate_digest": predicate["approval_predicate_digest"], "coordinate": tx["coordinate"], "prior_status_record_digest": prior_digest, "prior_status": prior_status, "reason_digest": tx["status_reason_digest"], "expected_prior_revision": tx["expected_prior_revision"], "expected_prior_head_digest": tx["expected_prior_head_digest"]}
        authority_valid = publication_authority_valid(approval, context, subject["coordinate"], expected_action)
        valid = (valid_from and prior_publication_chain_valid(tx, prior, context["prior_journal"])
            and tx["expected_prior_revision"] == context["canonical_publication_revision"]
            and tx["expected_prior_head_digest"] == context["canonical_publication_head"]
            and context["prior_journal"]["publication_journal_digest"] == context["canonical_publication_journal_head"] and authority_valid and tx["operation"] == op and tx["owner_approval_digest"] == approval["owner_approval_digest"] == subject["owner_approval_digest"] and tx["publication_transaction_digest"] == subject["transaction_digest"] == journal["transaction_digest"] == marker["transaction_digest"] and tx["coordinate"] == subject["coordinate"] and tx["owner_approval_digest"] == subject["owner_approval_digest"] and tx["status_reason_digest"] == subject["reason_digest"] and tx["expected_prior_head_digest"] == subject["prior_status_record_digest"] and tx["expected_prior_revision"] + 1 == subject["ledger_revision"] and journal["state"] == "committed" and journal["linearized"] and journal["recovery_action"] == "none" and journal["prior_journal_digest"] == context["prior_journal_digest"] and journal["resulting_record_digest"] == journal["resulting_ledger_head_digest"] == result_digest and journal["resulting_ledger_revision"] == subject["ledger_revision"] and marker["journal_digest"] == journal["publication_journal_digest"] and marker["resulting_record_digest"] == marker["resulting_ledger_head_digest"] == result_digest and marker["resulting_ledger_revision"] == subject["ledger_revision"] and marker["fsync_complete"])
        return None if valid else "lifecycle_violation"
    if rule == "publication_journal_shape":
        state, linear, action = subject["state"], subject["linearized"], subject["recovery_action"]
        valid_tuple = ((state in {"prepared", "aborted"} and not linear and action == "discard_staging")
            or (state == "committing" and linear and action == "complete_commit")
            or (state == "committed" and linear and action == "none"))
        return None if valid_tuple else "recovery_needed"
    if rule == "publication_recovery":
        tx, result, marker = context["transaction"], context["resulting_status"], context["marker"]
        before, after, prior, prior_journal = context["before"], context["after"], context["prior_status"], context["prior_journal"]
        if (subject["recovery_controller_id"] != context["canonical_recovery_controller_id"]
            or subject["recovery_runtime_identity"] != context["canonical_recovery_runtime_identity"]
            or subject["recovery_epoch"] != context["canonical_recovery_epoch"]): return "recovery_needed"
        state, linear, action = subject["state"], subject["linearized"], subject["recovery_action"]
        valid_tuple = ((state in {"prepared", "aborted"} and not linear and action == "discard_staging")
            or (state == "committing" and linear and action == "complete_commit")
            or (state == "committed" and linear and action == "none"))
        if not valid_tuple: return "recovery_needed"
        prior_digest = prior.get("owner_publication_digest", prior.get("publication_status_transition_digest"))
        result_digest = result.get("owner_publication_digest", result.get("publication_status_transition_digest"))
        prior_status = prior.get("status", prior.get("to_status"))
        canonical_before = (prior_digest is not None and before["revision"] == context["canonical_publication_revision"] == prior["ledger_revision"]
            and before["head"] == context["canonical_publication_head"] == prior_digest
            and before["status_record_digest"] == context["canonical_publication_status_digest"] == prior_digest
            and before["marker"] is None and before["staging_present"]
            and subject["prior_journal_digest"] == context["canonical_recovery_journal_head"] == prior_journal["publication_journal_digest"]
            and prior_publication_chain_valid(tx, prior, prior_journal)
            and tx["expected_prior_revision"] == before["revision"] and tx["expected_prior_head_digest"] == before["head"])
        common_result = (result_digest is not None and subject["transaction_digest"] == tx["publication_transaction_digest"] == result["transaction_digest"]
            and subject["resulting_record_digest"] == subject["resulting_ledger_head_digest"] == result_digest
            and subject["resulting_ledger_revision"] == result["ledger_revision"] == tx["expected_prior_revision"] + 1
            and tx["coordinate"] == result["coordinate"] and tx["owner_approval_digest"] == result["owner_approval_digest"])
        if result["schema"] == "semantic-owner-publication.v0":
            result_join = (tx["operation"] == "publish" and tx["status_reason_digest"] is None and result["status"] == "published"
                and result["ledger_namespace"] == tx["namespace"] == tx["coordinate"]["namespace"]
                and result["prior_publication_digest"] == prior_digest)
        else:
            operation = "withdraw" if result["to_status"] == "withdrawn" else "revoke"
            result_join = (tx["operation"] == operation and tx["status_reason_digest"] == result["reason_digest"]
                and result["prior_status_record_digest"] == prior_digest and result["from_status"] == prior_status
                and prior["coordinate"] == result["coordinate"] and tx["namespace"] == tx["coordinate"]["namespace"])
        marker_join = (fixture_digest_valid(marker) and marker["fsync_complete"]
            and marker["journal_digest"] == subject["publication_journal_digest"]
            and marker["transaction_digest"] == subject["transaction_digest"]
            and marker["resulting_record_digest"] == subject["resulting_record_digest"]
            and marker["resulting_ledger_head_digest"] == subject["resulting_ledger_head_digest"]
            and marker["resulting_ledger_revision"] == subject["resulting_ledger_revision"])
        if not (canonical_before and common_result and result_join and marker_join): return "recovery_needed"
        if not linear:
            if (after["revision"] != before["revision"] or after["head"] != before["head"] or after["marker"] is not None
                or after["staging_present"] or after["status_record_digest"] != before["status_record_digest"]): return "recovery_needed"
        else:
            if (after["revision"] != subject["resulting_ledger_revision"] or after["head"] != subject["resulting_ledger_head_digest"]
                or after["status_record_digest"] != subject["resulting_record_digest"] or after["marker"] != marker
                or after["staging_present"]): return "recovery_needed"
        return None
    if rule == "projection":
        p, capsule, archive = context["projection"], context["capsule"], context["archive_linkage"]
        payload = {x["path"]: x for x in context["payload_manifest"]["entries"]}; consumer = {x["path"]: x for x in context["consumer_manifest"]["entries"]}; archived = {x["path"]: x for x in context["archive_manifest"]["entries"]}
        src = [x["capsule_path"] for x in p["entries"]]; dst = [x["consumer_path"] for x in p["entries"]]
        expected_src = {archive["payload_root"] + "/" + path for path in payload}; rows_ok = len(src) == len(set(src)) and len(dst) == len(set(dst)) and set(src) == expected_src and set(dst) == set(consumer)
        for row in p["entries"]:
            relative = row["capsule_path"][len(archive["payload_root"]) + 1:]; pe, ce, ae = payload.get(relative), consumer.get(row["consumer_path"]), archived.get(row["capsule_path"])
            if not pe or not ce or not ae or any(pe.get(k) != ce.get(k) or pe.get(k) != ae.get(k) for k in ("kind", "mode", "byte_length", "content_digest")) or row["mode"] != pe["mode"] or row["byte_length"] != pe.get("byte_length") or row["content_digest"] != pe.get("content_digest"): rows_ok = False
        meta = archive["capsule_metadata"]; meta_bytes = jcs(meta).encode(); meta_entry = archived.get(archive["capsule_metadata_path"])
        acyclic = set(meta) == {"schema", "namespace", "semantic_version", "payload_manifest_digest", "identity_mode"} and meta["namespace"] == capsule["namespace"] and meta["semantic_version"] == capsule["semantic_version"] and meta["payload_manifest_digest"] == capsule["payload_manifest_digest"] and meta_entry and meta_entry["content_digest"] == archive["capsule_metadata_content_digest"] == domain_digest("semantic-release.raw-blob.v0", meta_bytes) and meta_entry["byte_length"] == len(meta_bytes)
        expected_archive_paths = {archive["capsule_metadata_path"], archive["payload_root"]} | {archive["payload_root"] + "/" + path for path in payload}
        root_entry = archived.get(archive["payload_root"])
        archive_exact = set(archived) == expected_archive_paths and len(archived) == len(context["archive_manifest"]["entries"]) and root_entry == {"path": archive["payload_root"], "kind": "directory", "mode": 493}
        current_tombstones = context["canonical_lifecycle_tombstone_head"]; tombstones = context["tombstones"]
        tombstone_current = (current_tombstones["namespace"] == tombstones["namespace"] == capsule["namespace"]
            and current_tombstones["tombstone_registry_digest"] == tombstones["tombstone_registry_digest"] == capsule["tombstone_registry_digest"]
            and current_tombstones["tombstone_registry_revision"] == tombstones["registry_revision"])
        valid = rows_ok and acyclic and archive_exact and tombstone_current and archive["archive_manifest_digest"] == context["archive_manifest"]["material_manifest_digest"] and p["payload_manifest_digest"] == context["payload_manifest"]["material_manifest_digest"] and p["consumer_manifest_digest"] == context["consumer_manifest"]["material_manifest_digest"] and subject["payload_projection_digest"] == p["payload_projection_digest"] == capsule["payload_projection_digest"] and subject["capsule_archive_linkage_digest"] == archive["capsule_archive_linkage_digest"] == capsule["capsule_archive_linkage_digest"] and subject["source_payload_manifest_digest"] == p["payload_manifest_digest"] and subject["expected_consumer_manifest_digest"] == p["consumer_manifest_digest"] == subject["actual_consumer_manifest_digest"]
        return None if valid else "projection_mismatch"
    if rule == "rollback":
        request = context["request"]; target = request["target"]; before = subject["active_state_before"]; after = subject["active_state_after"]
        activation, decision = context["activation"], context["decision"]
        current_digest, current_revision = context["current_activation_digest"], context["current_activation_revision"]
        canonical_history = context["canonical_history_head"]
        activation_current = activation["activation_receipt_digest"] == current_digest and activation["activation_revision"] == current_revision and activation["status"] == "activated" and activation["revoked_by_digest"] is None and activation["superseded_by_activation_receipt_digest"] is None
        request_valid = (activation_current and request["issuer"]["kind"] == "consumer_owner"
            and request["issuer"]["id"] == activation["consumer_repository"]["owner"] == context["intent"]["consumer_repository"]["owner"]
            and request["target"] == context["intent"]["rollback_target"] == context["materialization"]["rollback_target"]
            and request["active_activation_receipt_digest"] == current_digest and request["from_state"]["enabled"] and request["from_state"]["coordinate"] == activation["coordinate"] and request["from_state"]["runtime_identity"] == activation["runtime_identity"] and request["owner_decision_reference_digest"] == decision["ak_decision_reference_digest"] and decision_current(decision, context)
            and request["recovery_controller_id"] == context["canonical_recovery_controller_id"]
            and request["recovery_epoch"] == context["canonical_recovery_epoch"]
            and request["recovery_runtime_identity"] == context["canonical_recovery_runtime_identity"]
            and request["recovery_runtime_identity"] != request["from_state"]["runtime_identity"])
        if not request_valid: return "rollback_unavailable"
        proof = context["availability"]
        if not proof or not fixture_digest_valid(proof) or subject["availability_proof_digest"] != proof["rollback_availability_proof_digest"] or proof["target_kind"] != target["kind"] or proof["recovery_runtime_identity"] != request["recovery_runtime_identity"] or not proof["recovery_runtime_available"] or not rollback_availability_valid(context["intent"], context["acceptance"], context["materialization"], proof, context, target): return "rollback_unavailable"
        nulls = {"semantic_materialization_receipt_digest": None, "semantic_coordinate": None, "runtime_materialization_receipt_digest": None, "runtime_identity": None, "runtime_revalidation_receipt_digest": None, "disable_contract_digest": None, "rehearsal_receipt_digest": None, "semantic_target_artifact_digest": None, "runtime_target_artifact_digest": None, "disable_target_artifact_digest": None, "recovery_artifact_digest": context["recovery_artifact"]["rollback_available_artifact_digest"]}
        expected_proof = dict(nulls)
        if target["kind"] in {"semantic", "combined"}:
            st = target if target["kind"] == "semantic" else target["semantic_stage"]
            expected_proof.update(semantic_materialization_receipt_digest=st["target_materialization_receipt_digest"], semantic_coordinate=st["target_coordinate"], semantic_target_artifact_digest=context["semantic_artifact"]["rollback_available_artifact_digest"])
        if target["kind"] in {"runtime", "combined"}:
            rt = target if target["kind"] == "runtime" else target["runtime_stage"]
            expected_proof.update(runtime_materialization_receipt_digest=rt["target_materialization_receipt_digest"], runtime_identity=rt["target_runtime_identity"], runtime_revalidation_receipt_digest=rt["runtime_revalidation_receipt_digest"], runtime_target_artifact_digest=context["runtime_artifact"]["rollback_available_artifact_digest"])
        if target["kind"] == "no_prior_disable": expected_proof.update(disable_contract_digest=target["disable_contract_digest"], rehearsal_receipt_digest=target["rehearsal_receipt_digest"], disable_target_artifact_digest=context["disable_artifact"]["rollback_available_artifact_digest"])
        if any(proof[k] != v for k, v in expected_proof.items()): return "rollback_unavailable"
        recovery = context["recovery_artifact"]
        artifacts_valid = recovery["artifact_kind"] == "recovery_runtime" and recovery["runtime_identity"] == request["recovery_runtime_identity"] and recovery["health_receipt_digest"] is not None and recovery["rehearsal_receipt_digest"] is not None and recovery["independently_available"]
        if target["kind"] in {"semantic", "combined"}:
            st, artifact = (target, context["semantic_artifact"]) if target["kind"] == "semantic" else (target["semantic_stage"], context["semantic_artifact"])
            artifacts_valid = artifacts_valid and artifact["artifact_kind"] == "semantic_target" and artifact["coordinate"] == st["target_coordinate"] and artifact["materialization_receipt_digest"] == st["target_materialization_receipt_digest"]
        if target["kind"] in {"runtime", "combined"}:
            rt, artifact = (target, context["runtime_artifact"]) if target["kind"] == "runtime" else (target["runtime_stage"], context["runtime_artifact"])
            artifacts_valid = artifacts_valid and artifact["artifact_kind"] == "runtime_target" and artifact["runtime_identity"] == rt["target_runtime_identity"] and artifact["materialization_receipt_digest"] == rt["target_materialization_receipt_digest"] and artifact["runtime_revalidation_receipt_digest"] == rt["runtime_revalidation_receipt_digest"]
        if target["kind"] == "no_prior_disable":
            artifact = context["disable_artifact"]; artifacts_valid = artifacts_valid and artifact["artifact_kind"] == "disable_target" and artifact["disable_contract_digest"] == target["disable_contract_digest"] and artifact["rehearsal_receipt_digest"] == target["rehearsal_receipt_digest"]
        if not artifacts_valid: return "rollback_unavailable"
        if not activation_chain_valid(activation, context): return "rollback_unavailable"
        if (subject["issuer"]["id"] != subject["recovery_controller_id"] or subject["recovery_controller_id"] != context["canonical_recovery_controller_id"]
            or subject["recovery_epoch"] != request["recovery_epoch"] or subject["recovery_epoch"] != context["canonical_recovery_epoch"]
            or subject["rollback_request_digest"] != request["rollback_request_digest"] or subject["request_target_kind"] != target["kind"] or before != request["from_state"] or not before["enabled"] or before["coordinate"] is None or subject["history_head_before"] != canonical_history): return "history_conflict"
        expected_names = {"semantic": ["semantic"], "runtime": ["runtime"], "no_prior_disable": ["disable"]}.get(target["kind"])
        if target["kind"] == "combined": expected_names = ["semantic", "runtime"] if target["stage_order"] == "semantic_then_runtime" else ["runtime", "semantic"]
        if [x["stage"] for x in subject["stages"]] != expected_names or subject["stage_order"] != (target.get("stage_order") if target["kind"] == "combined" else None): return "history_conflict"
        if any((x["result"] == "failed") != (x["error_digest"] is not None) for x in subject["stages"]): return "history_conflict"
        states = [x["result"] for x in subject["stages"]]
        failed_indexes = [i for i, x in enumerate(states) if x == "failed"]
        if len(failed_indexes) > 1 or failed_indexes and any(x != "not_started" for x in states[failed_indexes[0] + 1:]): return "history_conflict"
        if "not_started" in states and any(x != "not_started" for x in states[states.index("not_started") + 1:]): return "history_conflict"
        computed = copy.deepcopy(before)
        for stage in subject["stages"]:
            if stage["result"] != "completed": continue
            if stage["stage"] == "semantic": computed["coordinate"] = target["target_coordinate"] if target["kind"] == "semantic" else target["semantic_stage"]["target_coordinate"]
            elif stage["stage"] == "runtime": computed["runtime_identity"] = target["target_runtime_identity"] if target["kind"] == "runtime" else target["runtime_stage"]["target_runtime_identity"]
            else: computed["enabled"] = False; computed["coordinate"] = None
        failed = [x for x in subject["stages"] if x["result"] == "failed"]; completed = [x for x in subject["stages"] if x["result"] == "completed"]
        failure_stage = failed[0]["stage"] if failed else None; failure_error = failed[0]["error_digest"] if failed else None
        if subject["failure_stage"] != failure_stage or subject["error_digest"] != failure_error: return "history_conflict"
        if subject["result"] == "partial_failure" and (target["kind"] != "combined" or not failed or not completed): return "history_conflict"
        runtime_proof = target.get("runtime_revalidation_receipt_digest") if target["kind"] == "runtime" else target.get("runtime_stage", {}).get("runtime_revalidation_receipt_digest")
        if completed and any(x["stage"] == "runtime" for x in completed) and subject["runtime_revalidation_receipt_digest"] != runtime_proof: return "rollback_unavailable"
        if not any(x["stage"] == "runtime" for x in completed) and subject["runtime_revalidation_receipt_digest"] is not None: return "history_conflict"
        ak_digest, pi_digest = subject["ak_evidence_linkage_digest"], subject["pi_delivery_receipt_digest"]
        if (ak_digest is None) != (pi_digest is None): return "history_conflict"
        if ak_digest is not None:
            ak_link, pi_receipt = context["ak_linkage"], context["pi_receipt"]
            if not ak_link or not pi_receipt or ak_digest != ak_link["ak_evidence_linkage_digest"] or pi_digest != pi_receipt["pi_delivery_receipt_digest"] or ak_link["pi_delivery_receipt_digest"] != pi_digest or ak_link["activation_receipt_digest"] != request["active_activation_receipt_digest"]: return "history_conflict"
        if subject["result"] == "failed":
            return None if failed and not completed and after == before and subject["history_head_after"] == canonical_history and subject["supersedes_activation_receipt_digest"] is None else "history_conflict"
        if after != computed: return "history_conflict"
        history = context["history_after"]
        expected_kind = "disable" if target["kind"] == "no_prior_disable" else "rollback"
        history_valid = history and fixture_digest_valid(history) and subject["history_head_after"] == {"kind": expected_kind, "digest": history["rollback_history_transition_digest"]} and history["rollback_request_digest"] == request["rollback_request_digest"] and history["result"] == subject["result"] and history["active_state_before"] == before and history["active_state_after"] == after and history["stages"] == subject["stages"] and history["failure_stage"] == subject["failure_stage"] and history["error_digest"] == subject["error_digest"] and history["history_head_before"] == canonical_history and history["supersedes_activation_receipt_digest"] == subject["supersedes_activation_receipt_digest"]
        if not history_valid: return "history_conflict"
        if subject["result"] == "partial_failure": return None if target["kind"] == "combined" and failed and completed and subject["supersedes_activation_receipt_digest"] is None else "history_conflict"
        expected_result = "disabled" if target["kind"] == "no_prior_disable" else "rolled_back"
        valid = subject["result"] == expected_result and not failed and len(completed) == len(subject["stages"]) and subject["supersedes_activation_receipt_digest"] == current_digest
        if target["kind"] == "no_prior_disable": valid = valid and after["runtime_identity"] == before["runtime_identity"]
        return None if valid else "history_conflict"
    if rule == "generation_activation":
        activation = context["activation"]
        valid = activation_chain_valid(activation, context) and activation["activation_receipt_digest"] == context["current_activation_digest"] and activation["status"] == "activated" and activation["revoked_by_digest"] is None and activation["superseded_by_activation_receipt_digest"] is None and subject["activation_receipt_digest"] == subject["activation_head_digest"] == context["current_activation_digest"] and subject["activation_head_revision"] == context["current_activation_revision"] == activation["activation_revision"] and subject["coordinate"] == activation["coordinate"] and subject["runtime_identity"] == activation["runtime_identity"]
        return None if valid else "activation_not_current"
    if rule == "utc": return None if strict_utc(subject["recorded_at"]) else "malformed_input"
    if rule == "ak_decision": return None if decision_current(subject, context) else "self_certification"
    if rule == "acceptance_binding":
        decision, intent = context["decision"], context["intent"]
        valid = (subject["consumer_intent_digest"] == intent["consumer_intent_digest"] and subject["consumer_repository"] == intent["consumer_repository"] and subject["acceptance_authority"]["kind"] == "consumer_owner" and subject["acceptance_authority"]["id"] == subject["consumer_repository"]["owner"] and subject["decision_reference_digest"] == intent["decision_reference_digest"] == decision["ak_decision_reference_digest"] and subject["governing_scope_digest"] == decision["scope_digest"] and subject["accepted_posture"] == intent["requested_posture"] and intent["intent_revision"] <= subject["valid_through_intent_revision"] and subject["revoked_by_digest"] is None and subject["owner_acceptance_digest"] == context["current_acceptance_digest"]
            and subject["acceptance_revision"] == context["current_acceptance_revision"] and decision_current(decision, context))
        return None if valid else "self_certification"
    if rule == "activation_binding":
        return None if activation_chain_valid(subject, context, candidate=True) else "self_certification"
    if rule == "governance_contracts":
        consumer = context["consumer_contract"]
        expected_paths = ["config/semantic-release/canary.json", "docs/project/semantic-release-canary-evidence.md", "scripts/ci/semantic-release-canary.sh"]
        repos = {
            "ak": {"owner": "agent-kernel-owner", "repository_id": "agent-kernel", "canonical_locator": "local://softwareco/owned/agent-kernel", "identity_revision": 9},
            "rocs": {"owner": "rocs-owner", "repository_id": "rocs-cli", "canonical_locator": "local://core/rocs-cli", "identity_revision": 4},
            "owner": {"owner": "semantic-owner", "repository_id": "ontology-kernel", "canonical_locator": "local://core/ontology-kernel", "identity_revision": 1},
            "consumer": {"owner": "consumer-owner", "repository_id": "pi-canary-consumer", "canonical_locator": "local://softwareco/pi-canary-consumer", "identity_revision": 3}}
        def references(rows: list[dict], expected: dict[str, tuple[str, str]], contract_name: str, group: str) -> bool:
            if [x["reference_id"] for x in rows] != sorted(expected): return False
            state_map = {"accepted_current": "accepted", "completed_current": "completed", "evidence_accepted_current": "evidence_accepted"}
            for row in rows:
                repo_key, state = expected[row["reference_id"]]
                if row["repository"] != repos[repo_key] or row["required_state"] != state: return False
                if row["resolution"] == "unresolved_candidate":
                    if any(row[k] is not None for k in ("ak_store_head", "task_id", "task_record_digest", "artifact_digest", "observed_canonical_state")): return False
                elif row["resolution"] == "resolved":
                    observed = row["observed_canonical_state"]
                    anchors = [anchor for anchor in context["_authority_task_states"] if anchor == observed]
                    if (len(anchors) != 1 or observed["repository"] != row["repository"] or observed["ak_store_head"] != row["ak_store_head"]
                        or observed["task_id"] != row["task_id"] or observed["task_record_digest"] != row["task_record_digest"]
                        or observed["artifact_digest"] != row["artifact_digest"] or observed["state"] != state_map[state]): return False
                else: return False
            return True
        def stop_set(contract: dict, expected: dict[str, tuple[str, str, str]], contract_name: str) -> bool:
            if len(contract["stop_conditions"]) != len(expected): return False
            for row in contract["stop_conditions"]:
                if row["condition_kind"] not in expected: return False
                cid, fact_id, repo_key = expected[row["condition_kind"]]
                if (row["condition_id"] != cid or row["fact_reference"]["reference_id"] != fact_id
                    or row["trigger_state"] != "unsatisfied_or_noncurrent" or row["required_effect"] != "stop_before_mutation" or row["resume_state"] != "accepted_current"
                    or not references([row["fact_reference"]], {fact_id: (repo_key, "accepted_current")}, contract_name, "stop")): return False
            return True
        ak_prereqs = {x: ("ak", "accepted_current") for x in ["adr:0053", "decision:53", "plan:decision-53-implementation", "plan:decision-53-validation-rollout-rollback"]}
        ak_evidence = {"accepted-decision-reference": ("ak", "evidence_accepted_current"), "deterministic-rerun": ("rocs", "evidence_accepted_current"),
            "docs-strict": ("rocs", "evidence_accepted_current"), "node-validator": ("rocs", "evidence_accepted_current"),
            "owner-task-references": ("ak", "evidence_accepted_current"), "python-validator": ("rocs", "evidence_accepted_current"),
            "rollback-rehearsal": ("rocs", "evidence_accepted_current")}
        ak_stops = {
            "stale_or_revoked_decision": ("stale-or-revoked-decision", "fact:stale-or-revoked-decision", "ak"),
            "store_head_drift": ("store-head-drift", "fact:store-head-drift", "ak"), "scope_drift": ("scope-drift", "fact:scope-drift", "ak"),
            "missing_owner_task": ("missing-owner-task", "fact:missing-owner-task", "ak"),
            "owner_substitution": ("attempted-owner-substitution", "fact:attempted-owner-substitution", "ak"),
            "authorization_escalation": ("attempted-use-as-authorization", "fact:attempted-use-as-authorization", "ak")}
        consumer_dependencies = {"candidate-decision-53-ak-coordination": ("ak", "completed_current"),
            "candidate-decision-53-rocs-implementation": ("rocs", "completed_current"),
            "candidate-decision-53-semantic-owner-publication": ("owner", "completed_current")}
        consumer_prereqs = {"adr:0053": ("ak", "accepted_current"), "consent:pi-canary-consumer-owner": ("consumer", "accepted_current"),
            "decision:53": ("ak", "accepted_current"), "plan:decision-53-implementation": ("ak", "accepted_current"),
            "plan:decision-53-validation-rollout-rollback": ("ak", "accepted_current")}
        consumer_evidence = {
            "activation-receipt": ("consumer", "evidence_accepted_current"), "canary-evidence": ("consumer", "evidence_accepted_current"),
            "consumer-intent-and-acceptance": ("consumer", "evidence_accepted_current"), "exact-materialization-receipt": ("rocs", "evidence_accepted_current"),
            "rollback-availability-proof": ("rocs", "evidence_accepted_current"), "rollback-history": ("consumer", "evidence_accepted_current"),
            "rollback-rehearsal": ("rocs", "evidence_accepted_current"), "scoped-gate-decision": ("ak", "evidence_accepted_current")}
        consumer_stops = {
            "missing_owner_consent": ("missing-owner-consent", "fact:missing-owner-consent", "consumer"),
            "rollback_unavailable": ("target-or-recovery-unavailable", "fact:target-or-recovery-unavailable", "consumer"),
            "stale_semantic_trust_or_ledger": ("stale-semantic-trust-or-ledger", "fact:stale-semantic-trust-or-ledger", "owner"),
            "stale_ak_decision_or_store": ("stale-ak-decision-or-store", "fact:stale-ak-decision-or-store", "ak"),
            "stale_consumer_activation_or_history": ("stale-consumer-activation-or-history", "fact:stale-consumer-activation-or-history", "consumer"),
            "projection_or_issuer_drift": ("projection-or-issuer-drift", "fact:projection-or-issuer-drift", "rocs"),
            "validator_failure": ("failed-validator", "fact:failed-validator", "rocs"),
            "compatibility_failure": ("unknown-or-incompatible", "fact:unknown-or-incompatible", "owner"),
            "missing_rollback_rehearsal": ("missing-rollback-rehearsal", "fact:missing-rollback-rehearsal", "rocs"),
            "canary_scope_exceeded": ("scope-beyond-named-canary", "fact:scope-beyond-named-canary", "consumer"),
            "default_or_fleet_request": ("default-or-fleet-request", "fact:default-or-fleet-request", "consumer")}
        no_authority = all(not x[k] for x in (subject, consumer) for k in ("authorizes_execution", "authorizes_publication", "authorizes_adoption")) and subject["contract_status"] == consumer["contract_status"] == "candidate_not_created"
        exact = (subject["task_contract_id"] == "decision-53-ak-coordination" and subject["task_id"] == "candidate-decision-53-ak-coordination"
            and subject["task_owner_id"] == subject["rollback_owner"]["id"] == "agent-kernel-owner" and subject["rollback_owner"]["kind"] == "ak" and subject["task_kind"] == "ak_coordination"
            and subject["repository"] == repos["ak"] and subject["allowed_paths"] == [] and subject["dependencies"] == []
            and references(subject["prerequisites"], ak_prereqs, "ak", "prerequisites") and references(subject["required_evidence"], ak_evidence, "ak", "required_evidence") and stop_set(subject, ak_stops, "ak")
            and subject["authority_scope"] == "coordination_only" and consumer["task_contract_id"] == "decision-53-first-consumer-canary"
            and consumer["task_id"] == "candidate-decision-53-first-consumer-canary" and consumer["task_owner_id"] == consumer["rollback_owner"]["id"] == "consumer-owner" and consumer["rollback_owner"]["kind"] == "consumer_owner"
            and consumer["repository"] == repos["consumer"] and consumer["allowed_paths"] == expected_paths
            and references(consumer["dependencies"], consumer_dependencies, "consumer", "dependencies") and references(consumer["prerequisites"], consumer_prereqs, "consumer", "prerequisites")
            and references(consumer["required_evidence"], consumer_evidence, "consumer", "required_evidence") and stop_set(consumer, consumer_stops, "consumer")
            and consumer["authority_scope"] == "consumer_owner_candidate_only")
        return None if no_authority and subject["task_contract_id"] != consumer["task_contract_id"] and exact else "self_certification"
    if rule in {"pi_variant", "ak_optional_pi"}: return None
    raise ValidationError(f"unknown differential rule {rule}")


def decode_fact_value(value: dict) -> object:
    if value["kind"] == "null": return None
    if value["kind"] == "empty_list": return []
    if value["kind"] == "empty_map": return {}
    return copy.deepcopy(value["value"])


def semantic_authority_view(item: dict) -> dict:
    """Flatten role-keyed authority semantics while omitting wrapper linkage metadata."""
    graph = item["context"]
    config, snapshot, bundle, verifier = (graph[key] for key in ("acquisition_config", "authority_snapshot", "proof_bundle", "verifier_input"))
    view: dict[str, object] = {"rule": item["rule"], "subject": copy.deepcopy(item["subject"]), "context": {
        "acquisition": {"verifier_identity": copy.deepcopy(config["verifier_identity"]), "collator": copy.deepcopy(config["collator"]),
            "collation_scope": config["collation_scope"], "required_action_epoch_floor": config["required_action_epoch_floor"],
            "live_acquisition_implemented": config["live_acquisition_implemented"], "action_epoch": snapshot["action_epoch"]},
        "receipts": {}, "nodes": {}, "parameters": {}, "unbound_pins": [], "unbound_receipts": [], "unbound_nodes": []}}
    normalized_context = view["context"]
    assert isinstance(normalized_context, dict)
    pins_used: set[int] = set(); receipts_used: set[int] = set(); nodes_used: set[int] = set()
    for binding in verifier["receipt_bindings"]:
        pin_candidates = [copy.deepcopy(row) for row in config["pins"] if row["capability_pin_id"] == binding["capability_pin_id"]]
        receipt_candidates = [copy.deepcopy(row) for row in snapshot["store_read_receipts"] if row["observation_id"] == binding["observation_id"]]
        pins_used.update(i for i, row in enumerate(config["pins"]) if row["capability_pin_id"] == binding["capability_pin_id"])
        receipts_used.update(i for i, row in enumerate(snapshot["store_read_receipts"]) if row["observation_id"] == binding["observation_id"])
        normalized_context["receipts"][binding["role"]] = {"binding": copy.deepcopy(binding),
            "pin_candidates": pin_candidates, "receipt_candidates": receipt_candidates}
    normalized_context["unbound_pins"] = [copy.deepcopy(row) for i, row in enumerate(config["pins"]) if i not in pins_used]
    normalized_context["unbound_receipts"] = [copy.deepcopy(row) for i, row in enumerate(snapshot["store_read_receipts"]) if i not in receipts_used]
    for binding in verifier["node_bindings"]:
        candidates = [copy.deepcopy(row) for row in bundle["nodes"] if row["bundle_key"] == binding["bundle_key"]]
        nodes_used.update(i for i, row in enumerate(bundle["nodes"]) if row["bundle_key"] == binding["bundle_key"])
        clean_binding = {key: copy.deepcopy(value) for key, value in binding.items() if key != "bundle_key"}
        clean_candidates = [{key: copy.deepcopy(value) for key, value in row.items() if key != "bundle_key"} for row in candidates]
        normalized_context["nodes"][binding["role"]] = {"binding": clean_binding, "node_candidates": clean_candidates}
    normalized_context["unbound_nodes"] = [
        {key: copy.deepcopy(value) for key, value in row.items() if key != "bundle_key"}
        for i, row in enumerate(bundle["nodes"]) if i not in nodes_used]
    for binding in verifier["parameter_bindings"]:
        normalized_context["parameters"][binding["role"]] = decode_fact_value(binding["value"])
    return view


def _collect_digest_correspondence(old: object, new: object, path: str, pairs: list[tuple[str, str, str]]) -> None:
    if isinstance(old, dict) and isinstance(new, dict):
        old_schema, new_schema = old.get("schema"), new.get("schema")
        if old_schema == new_schema and old_schema in DIGEST_FIELDS:
            field = DIGEST_FIELDS[old_schema][1]
            if isinstance(old.get(field), str) and isinstance(new.get(field), str): pairs.append((old[field], new[field], path or "/"))
        for field in ("action_digest", "change_digest", "fact_digest", "freshness_cas_token_digest"):
            if isinstance(old.get(field), str) and isinstance(new.get(field), str): pairs.append((old[field], new[field], (path or "/") + "/" + field))
        for key in old.keys() & new.keys():
            token = str(key).replace("~", "~0").replace("/", "~1")
            _collect_digest_correspondence(old[key], new[key], path + "/" + token, pairs)
    elif isinstance(old, list) and isinstance(new, list):
        for index, (left, right) in enumerate(zip(old, new)): _collect_digest_correspondence(left, right, path + f"/{index}", pairs)


def _strip_digest_cascade(value: object, references: dict[str, str]) -> object:
    if isinstance(value, str): return references.get(value, value)
    if isinstance(value, list):
        rows = [_strip_digest_cascade(row, references) for row in value]
        return rows
    if isinstance(value, dict):
        self_field = DIGEST_FIELDS.get(value.get("schema"), (None, None))[1]
        omitted = {self_field, "fact_digest", "freshness_cas_token_digest"}
        return {key: _strip_digest_cascade(row, references) for key, row in value.items() if key not in omitted}
    return value


def normalized_semantic_pair(positive: dict, drift: dict) -> tuple[object, object]:
    old, new = semantic_authority_view(positive), semantic_authority_view(drift)
    pairs: list[tuple[str, str, str]] = []; _collect_digest_correspondence(old, new, "", pairs)
    paths: dict[str, str] = {}
    for old_digest, new_digest, path in pairs:
        stable = "semantic-ref:" + typed_digest("semantic-release.semantic-reference-path.v10", path)
        if old_digest not in paths or stable < paths[old_digest]: paths[old_digest] = stable
        if new_digest not in paths or stable < paths[new_digest]: paths[new_digest] = stable
    return _strip_digest_cascade(old, paths), _strip_digest_cascade(new, paths)


_MISSING = object()


def _mutation_hash(value: object) -> str:
    payload = {"present": value is not _MISSING}
    if value is not _MISSING: payload["value"] = value
    return typed_digest("semantic-release.semantic-mutation-value.v10", payload)


def _semantic_diff(old: object, new: object, path: str, rows: list[dict]) -> None:
    if isinstance(old, dict) and isinstance(new, dict):
        for key in sorted(old.keys() | new.keys(), key=lambda value: str(value).encode()):
            token = str(key).replace("~", "~0").replace("/", "~1")
            _semantic_diff(old.get(key, _MISSING), new.get(key, _MISSING), path + "/" + token, rows)
        return
    if isinstance(old, list) and isinstance(new, list):
        for index in range(max(len(old), len(new))):
            _semantic_diff(old[index] if index < len(old) else _MISSING, new[index] if index < len(new) else _MISSING,
                path + f"/{index}", rows)
        return
    if old is not _MISSING and new is not _MISSING and type(old) is type(new) and old == new: return
    rows.append({"path": path or "/", "old_semantic_hash": _mutation_hash(old), "new_semantic_hash": _mutation_hash(new)})


def semantic_mutation_descriptors(positive: dict, drift: dict) -> list[dict]:
    old, new = normalized_semantic_pair(positive, drift); rows: list[dict] = []
    _semantic_diff(old, new, "", rows)
    rows.sort(key=lambda row: row["path"].encode())
    return rows


def descriptor_role_ids(descriptors: list[dict]) -> list[str]:
    roles: set[str] = set()
    for row in descriptors:
        parts = row["path"].split("/")
        if len(parts) > 1 and parts[1] == "subject": roles.add("subject")
        elif len(parts) > 3 and parts[1] == "context" and parts[2] in {"receipts", "nodes", "parameters"}:
            role = parts[3].replace("~1", "/").replace("~0", "~")
            roles.add("authority_graph" if role == "surplus-role" else role)
        else: roles.add("authority_graph")
    return sorted(roles, key=str.encode)

def check_claim_scope(instance: dict) -> None:
    expected = {"semantic-owner-acceptance.v0": ("acceptance_authority", "consumer_owner"), "semantic-materialization-verification-receipt.v0": ("issuer", "rocs"), "semantic-activation-receipt.v0": ("issuer", "consumer_owner"), "semantic-rocs-generation-receipt.v0": ("issuer", "rocs"), "semantic-pi-delivery-receipt.v0": ("issuer", "pi"), "semantic-ak-evidence-linkage.v0": ("issuer", "ak"), "semantic-rollback-request.v0": ("issuer", "consumer_owner"), "semantic-rollback-availability-proof.v0": ("issuer", "rocs"), "semantic-rollback-history-transition.v0": ("issuer", "consumer_owner"), "semantic-rollback-receipt.v0": ("issuer", "recovery_controller")}
    if (row := expected.get(instance["schema"])) and instance[row[0]]["kind"] != row[1]: raise ValidationError("issuer_scope_violation")
    if instance["schema"] == "semantic-rollback-technical-receipt.v0":
        expected_kind = {"materialization": "rocs", "runtime_revalidation": "rocs", "disable_contract": "consumer_owner", "rehearsal": "recovery_controller", "health": "recovery_controller"}[instance["receipt_kind"]]
        if instance["issuer"]["kind"] != expected_kind: raise ValidationError("issuer_scope_violation")
    if instance["schema"] == "semantic-rollback-availability-receipt.v0":
        expected_kind = {"semantic_target": "rocs", "runtime_target": "rocs", "disable_target": "consumer_owner", "recovery_runtime": "recovery_controller"}[instance["artifact_kind"]]
        if instance["issuer"]["kind"] != expected_kind: raise ValidationError("issuer_scope_violation")


def main() -> int:
    global SCHEMA_ROOT, AUTHORITY_MANIFEST, AUTHORITY_MANIFEST_BY_RULE
    schema, golden, differential = (load_json(ROOT / name) for name in ("protocol.schema.json", "golden-fixtures.json", "differential-fixtures.json"))
    SCHEMA_ROOT = schema
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema": raise ValidationError("wrong schema draft")
    def closed(node: Any, path: str = "$") -> None:
        if isinstance(node, dict):
            if node.get("type") == "object" and node.get("additionalProperties") is not False: raise ValidationError(f"open object at {path}")
            if "$ref" in node: resolve_ref(schema, node["$ref"])
            for key, value in node.items(): closed(value, f"{path}/{key}")
        elif isinstance(node, list):
            for i, value in enumerate(node): closed(value, f"{path}/{i}")
    closed(schema)
    manifest = differential.get("authority_rule_role_manifest")
    if not isinstance(manifest, dict): raise ValidationError("authority manifest missing")
    expected_context(manifest, "semantic-authority-rule-role-manifest.v0"); check_order(manifest)
    if manifest["authority_rule_role_manifest_digest"] != EXPECTED_AUTHORITY_MANIFEST_DIGEST: raise ValidationError("authority manifest full-tuple digest drift")
    rules = manifest["rules"]
    if {row["rule"] for row in rules} != ALL_RULES or len(rules) != len(ALL_RULES): raise ValidationError("authority manifest rule coverage drift")
    if {row["rule"] for row in rules if row["authority_bearing"]} != AUTHORITY_BEARING_RULES: raise ValidationError("authority-bearing rule classification drift")
    AUTHORITY_MANIFEST = manifest; AUTHORITY_MANIFEST_BY_RULE = {row["rule"]: row for row in rules}
    registry = differential.get("authority_edge_registry")
    registry_keys = {"edge_id", "rule", "description", "owner_surface", "owner_id", "owner_repository", "role_ids",
        "positive_fixture", "drift_fixture", "expected_error", "semantic_mutations", "edge_linkage_digest"}
    mutation_keys = {"path", "old_semantic_hash", "new_semantic_hash"}
    if not isinstance(registry, list) or len(registry) != EXPECTED_AUTHORITY_EDGE_COUNT: raise ValidationError("authority edge registry cardinality drift")
    if [row["edge_id"] for row in registry] != sorted([row["edge_id"] for row in registry], key=str.encode) or len({row["edge_id"] for row in registry}) != len(registry): raise ValidationError("authority edge registry identity/order drift")
    if typed_digest("semantic-release.authority-edge-registry.v10", registry) != EXPECTED_AUTHORITY_REGISTRY_DIGEST: raise ValidationError("authority edge registry full-tuple drift")
    registry_ids = {row["edge_id"] for row in registry}; registry_by_id = {row["edge_id"]: row for row in registry}; manifest_edge_ids: list[str] = []
    for row in registry:
        if set(row) != registry_keys or row["rule"] not in AUTHORITY_BEARING_RULES: raise ValidationError(f"authority edge tuple drift {row.get('edge_id')}")
        expected_shape_context(row["owner_repository"], "repositoryIdentity")
        if not sorted_unique(row["role_ids"]): raise ValidationError(f"authority edge role linkage order {row['edge_id']}")
        mutations = row["semantic_mutations"]
        if (not isinstance(mutations, list) or not mutations or [item.get("path") for item in mutations] != sorted([item.get("path") for item in mutations], key=str.encode)
            or len({item.get("path") for item in mutations}) != len(mutations)
            or any(set(item) != mutation_keys or re.fullmatch(r"sha256:[0-9a-f]{64}", item["old_semantic_hash"]) is None
                or re.fullmatch(r"sha256:[0-9a-f]{64}", item["new_semantic_hash"]) is None for item in mutations)):
            raise ValidationError(f"authority semantic mutation descriptor shape {row['edge_id']}")
        linkage = {"edge_id": row["edge_id"], "rule": row["rule"], "owner_surface": row["owner_surface"], "owner_id": row["owner_id"],
            "owner_repository": row["owner_repository"], "role_ids": row["role_ids"], "positive_fixture": row["positive_fixture"],
            "drift_fixture": row["drift_fixture"], "expected_error": row["expected_error"]}
        if row["edge_linkage_digest"] != typed_digest("semantic-release.authority-edge-linkage.v10", linkage): raise ValidationError(f"authority edge linkage digest {row['edge_id']}")
    for rule_row in rules:
        if bool(rule_row["edge_ids"]) != rule_row["authority_bearing"]: raise ValidationError(f"authority manifest edge coverage {rule_row['rule']}")
        if [link["edge_id"] for link in rule_row["role_edge_links"]] != rule_row["edge_ids"]: raise ValidationError(f"authority role/edge order {rule_row['rule']}")
        manifest_edge_ids.extend(rule_row["edge_ids"])
        mappings = rule_row["role_mappings"]
        for mapping in mappings:
            acquisition_values = [mapping[key] for key in ("acquisition_contract", "acquisition_contract_digest", "acquisition_distribution_digest", "acquisition_capability_digest")]
            if mapping["sources"] == ["receipt"]:
                if any(value is None for value in acquisition_values): raise ValidationError(f"manifest acquisition tuple incomplete {rule_row['rule']}:{mapping['role']}")
            elif any(value is not None for value in acquisition_values): raise ValidationError(f"manifest nonreceipt acquisition claim {rule_row['rule']}:{mapping['role']}")
        for link in rule_row["role_edge_links"]:
            edge = registry_by_id.get(link["edge_id"])
            expected_link = {"edge_id": edge["edge_id"], "owner_surface": edge["owner_surface"], "owner_id": edge["owner_id"],
                "owner_repository": edge["owner_repository"], "role_ids": edge["role_ids"], "edge_linkage_digest": edge["edge_linkage_digest"]} if edge else None
            if edge is None or edge["rule"] != rule_row["rule"] or link != expected_link: raise ValidationError(f"manifest/registry full owner linkage {link['edge_id']}")
            for role in link["role_ids"]:
                if role not in {"subject", "authority_graph"}:
                    matches = [mapping for mapping in mappings if mapping["role_prefix"] is None and mapping["role"] == role
                        or mapping["role_prefix"] is not None and role.startswith(mapping["role_prefix"])]
                    if len(matches) != 1: raise ValidationError(f"manifest role/edge linkage {link['edge_id']}:{role}")
    if len(manifest_edge_ids) != len(set(manifest_edge_ids)) or set(manifest_edge_ids) != registry_ids: raise ValidationError("manifest/registry edge bijection drift")
    records: dict[str, dict] = {}
    for record in golden["records"]:
        name, instance = record["name"], record["instance"]
        if name in records: raise ValidationError(f"duplicate record {name}")
        schema_validate(instance, schema, schema); check_order(instance); check_claim_scope(instance)
        if instance["schema"] == "semantic-audit-envelope.v0" and not strict_utc(instance["recorded_at"]): raise ValidationError("invalid golden UTC")
        domain, omitted = (COORDINATE_DOMAIN, None) if instance["schema"] == "semantic-release-coordinate.v0" else DIGEST_FIELDS[instance["schema"]]
        if record["domain"] != domain or record["omitted_field"] != omitted: raise ValidationError(f"{name}: fixture digest metadata drift")
        canonical, digest_value = object_digest(instance, domain, omitted)
        if canonical != record["canonical_preimage"] or digest_value != record["digest"] or omitted and instance[omitted] != digest_value: raise ValidationError(f"{name}: canonical digest mismatch")
        records[name] = record
    for blob in golden["raw_preimages"]:
        if domain_digest(blob["domain"], blob["preimage_utf8"].encode()) != blob["digest"]: raise ValidationError("raw preimage mismatch")
    for assertion in golden["chain_assertions"]:
        if pointer(records[assertion["record"]]["instance"], assertion["instance_path"]) != records[assertion["equals_record"]]["digest"]: raise ValidationError(f"link mismatch {assertion}")
    accepted = rejected = 0
    case_results: dict[str, str | None] = {}
    for item in differential["cases"]:
        subject = item["subject"]; validate_ijson(subject)
        try: schema_validate(subject, schema, schema); structural = True
        except ValidationError: structural = False
        if structural != item["schema_valid"]: raise ValidationError(f"{item['name']}: schema_valid expected {item['schema_valid']}, got {structural}")
        if item["rule"] != "digest" and not fixture_digest_valid(subject): raise ValidationError(f"{item['name']}: counterexample digest masks rule")
        actual = item["expected_error"] if not structural else None
        if structural:
            try: check_claim_scope(subject)
            except ValidationError: actual = "issuer_scope_violation"
            if actual is None: actual = evaluate(item["rule"], subject, item["context"])
        if actual is None:
            try: check_order(subject)
            except ValidationError: actual = "malformed_input"
        if actual != item["expected_error"]: raise ValidationError(f"{item['name']}: expected {item['expected_error']}, got {actual}")
        if item["name"] in case_results: raise ValidationError(f"duplicate differential case {item['name']}")
        case_results[item["name"]] = actual
        if actual is None: accepted += 1
        else: rejected += 1
    case_by_name = {item["name"]: item for item in differential["cases"]}
    for row in registry:
        edge_id, positive, drift, expected_error = row["edge_id"], row["positive_fixture"], row["drift_fixture"], row["expected_error"]
        if case_results.get(positive, "missing") is not None or case_results.get(drift) != expected_error: raise ValidationError(f"authority edge fixture outcome drift {edge_id}")
        if positive not in case_by_name or drift not in case_by_name: raise ValidationError(f"authority edge fixture missing {edge_id}")
        recomputed = semantic_mutation_descriptors(case_by_name[positive], case_by_name[drift])
        if recomputed != row["semantic_mutations"]: raise ValidationError(f"authority semantic mutation descriptor mismatch {edge_id}")
        if descriptor_role_ids(recomputed) != row["role_ids"]: raise ValidationError(f"authority mutation role linkage mismatch {edge_id}")
    raw_accepted = raw_rejected = 0
    for item in differential["raw_json_cases"]:
        try: parse_json_text(item["raw_json"]); actual = None
        except ValidationError: actual = "malformed_input"
        if actual != item["expected_error"]: raise ValidationError(f"{item['name']}: expected {item['expected_error']}, got {actual}")
        if actual is None: raw_accepted += 1
        else: raw_rejected += 1
    print(f"schema: Draft 2020-12, {len(schema['oneOf'])} protocol types, all object shapes closed")
    print(f"golden: {len(records)} object preimages and {len(golden['raw_preimages'])} raw preimages independently recomputed")
    print(f"chain: {len(golden['chain_assertions'])} exact digest links verified")
    role_count = sum(len(row["role_mappings"]) for row in rules)
    print(f"authority manifest: {len(rules)} rules ({len(AUTHORITY_BEARING_RULES)} authority-bearing), {role_count} role mappings; registry bijection complete")
    print(f"authority graph: {len(registry)} full owner/repository/linkage edges; normalized semantic-mutation descriptors independently recomputed")
    print(f"differential: {len(differential['cases'])} cases ({accepted} accepted transitions, {rejected} expected rejections)")
    print(f"raw-json: {len(differential['raw_json_cases'])} lexical cases ({raw_accepted} accepted, {raw_rejected} expected rejections)")
    print("result: PASS (Python stdlib token-aware validator)")
    return 0


if __name__ == "__main__":
    try: raise SystemExit(main())
    except ValidationError as exc: print(f"result: FAIL: {exc}", file=sys.stderr); raise SystemExit(1)
