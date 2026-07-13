#!/usr/bin/env python3
"""Stdlib-only revision-4 token-aware schema, digest, link, and transition validator."""
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
    "semantic-rollback-available-artifact.v0": ("rollback-available-artifact", "rollback_available_artifact_digest"),
    "semantic-rollback-availability-proof.v0": ("rollback-availability-proof", "rollback_availability_proof_digest"),
    "semantic-rollback-history-transition.v0": ("rollback-history-transition", "rollback_history_transition_digest"),
    "semantic-rollback-receipt.v0": ("rollback-receipt", "rollback_receipt_digest"),
    "semantic-non-authorizing-task-contract.v0": ("non-authorizing-task-contract", "non_authorizing_task_contract_digest"),
    "semantic-audit-envelope.v0": ("audit-envelope", "audit_envelope_digest"),
    "semantic-protocol-error.v0": ("error", "error_digest"),
}
DIGEST_FIELDS = {schema: (f"semantic-release.{domain}.v0", field) for schema, (domain, field) in DOMAIN_ROWS.items()}
SCHEMA_ROOT: dict[str, Any] | None = None


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
    if kind == "semantic-non-authorizing-task-contract.v0" and (not sorted_unique(instance["allowed_paths"]) or not sorted_unique(instance["dependency_task_ids"]) or not sorted_unique(instance["prerequisite_ids"]) or not sorted_unique(instance["prerequisite_artifact_digests"]) or not sorted_unique(instance["required_evidence"]) or not sorted_unique(instance["stop_conditions"])): raise ValidationError("task contract order")
    if kind == "semantic-protocol-error.v0" and not sorted_unique([x["key"] for x in instance["details"]]): raise ValidationError("error order")


def strict_utc(value: str) -> bool:
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value) is None or value[:4] == "0000": return False
    try:
        parsed = dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        return 1 <= parsed.year <= 9999 and parsed.strftime("%Y-%m-%dT%H:%M:%SZ") == value
    except ValueError: return False


def semver(value: str) -> tuple[int, int, int]:
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", value)
    if not match: raise ValidationError("bad semver")
    return tuple(map(int, match.groups()))  # type: ignore[return-value]


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


def validate_rule_context(rule: str, subject: dict, context: dict) -> None:
    typed: list[tuple[str, str | tuple[str, ...]]] = []
    if rule == "approval_threshold": typed = [("owner_set", "semantic-owner-set.v0"), ("predicate", "semantic-approval-predicate.v0"), ("policy", "semantic-owner-policy.v0")]
    elif rule == "trust_rotation": typed = [("old_root", "semantic-trust-root.v0"), ("new_root", "semantic-trust-root.v0"), ("approval", "semantic-owner-approval.v0"), ("policy", "semantic-owner-policy.v0"), ("owner_set", "semantic-owner-set.v0"), ("predicate", "semantic-approval-predicate.v0")]
    elif rule == "trust_revocation": typed = [("approval", "semantic-owner-approval.v0"), ("policy", "semantic-owner-policy.v0"), ("owner_set", "semantic-owner-set.v0"), ("predicate", "semantic-approval-predicate.v0")]
    elif rule == "compatibility_policy": typed = []
    elif rule == "compatibility":
        typed = [("policy", "semantic-compatibility-policy.v0")]
        for value in context.get("overrides", []): expected_context(value, "semantic-compatibility-override.v0")
        for value in context.get("override_approvals", {}).values(): expected_context(value, "semantic-owner-approval.v0")
        if context.get("overrides"):
            typed += [("owner_policy", "semantic-owner-policy.v0"), ("owner_set", "semantic-owner-set.v0"), ("predicate", "semantic-approval-predicate.v0")]
    elif rule == "lifecycle": typed = [("deprecation", "semantic-deprecation-record.v0"), ("policy", "semantic-compatibility-policy.v0"), ("prior_tombstones", "semantic-tombstone-registry.v0"), ("resulting_tombstones", "semantic-tombstone-registry.v0"), ("deprecation_ledger", "semantic-accepted-lifecycle-ledger-record.v0"), ("removal_ledger", "semantic-accepted-lifecycle-ledger-record.v0"), ("deprecation_publication", "semantic-owner-publication.v0"), ("removal_publication", "semantic-owner-publication.v0")]
    elif rule == "tombstone_reuse": typed = [("tombstones", "semantic-tombstone-registry.v0")]
    elif rule == "publication_commit": typed = [("transaction", "semantic-publication-transaction.v0"), ("journal", "semantic-publication-journal.v0"), ("marker", "semantic-publication-commit-marker.v0"), ("approval", "semantic-owner-approval.v0"), ("trust_root", "semantic-trust-root.v0"), ("prior_journal", "semantic-publication-journal.v0")]
    elif rule == "publication_transition": typed = [("transaction", "semantic-publication-transaction.v0"), ("journal", "semantic-publication-journal.v0"), ("marker", "semantic-publication-commit-marker.v0"), ("prior_status", ("semantic-owner-publication.v0", "semantic-publication-status-transition.v0")), ("approval", "semantic-owner-approval.v0"), ("policy", "semantic-owner-policy.v0"), ("owner_set", "semantic-owner-set.v0"), ("predicate", "semantic-approval-predicate.v0"), ("prior_journal", "semantic-publication-journal.v0")]
    elif rule == "publication_recovery":
        if context:
            typed = [("transaction", "semantic-publication-transaction.v0"), ("resulting_status", ("semantic-owner-publication.v0", "semantic-publication-status-transition.v0")), ("marker", "semantic-publication-commit-marker.v0")]
            expected_shape_context(context["before"], "publicationRecoveryState"); expected_shape_context(context["after"], "publicationRecoveryState")
    elif rule == "projection": typed = [("projection", "semantic-payload-projection.v0"), ("capsule", "semantic-release-capsule.v0"), ("archive_linkage", "semantic-capsule-archive-linkage.v0"), ("payload_manifest", "semantic-material-manifest.v0"), ("consumer_manifest", "semantic-material-manifest.v0"), ("archive_manifest", "semantic-material-manifest.v0")]
    elif rule == "rollback":
        typed = [("request", "semantic-rollback-request.v0"), ("activation", "semantic-activation-receipt.v0"), ("decision", "semantic-ak-decision-reference.v0"), ("intent", "semantic-consumer-intent.v0"), ("acceptance", "semantic-owner-acceptance.v0"), ("materialization", "semantic-materialization-verification-receipt.v0"), ("availability", "semantic-rollback-availability-proof.v0"), ("recovery_artifact", "semantic-rollback-available-artifact.v0")]
        for key in ("semantic_artifact", "runtime_artifact", "disable_artifact", "history_after", "ak_linkage", "pi_receipt"):
            if context.get(key) is not None:
                schema_name = {"semantic_artifact": "semantic-rollback-available-artifact.v0", "runtime_artifact": "semantic-rollback-available-artifact.v0", "disable_artifact": "semantic-rollback-available-artifact.v0", "history_after": "semantic-rollback-history-transition.v0", "ak_linkage": "semantic-ak-evidence-linkage.v0", "pi_receipt": "semantic-pi-delivery-receipt.v0"}[key]
                expected_context(context[key], schema_name)
        expected_shape_context(context["canonical_history_head"], "historyHead")
    elif rule == "generation_activation": typed = [("activation", "semantic-activation-receipt.v0"), ("decision", "semantic-ak-decision-reference.v0"), ("intent", "semantic-consumer-intent.v0"), ("acceptance", "semantic-owner-acceptance.v0"), ("materialization", "semantic-materialization-verification-receipt.v0")]
    elif rule == "ak_decision": expected_shape_context(context["canonical_store_head"], "akStoreHead")
    elif rule == "acceptance_binding": typed = [("decision", "semantic-ak-decision-reference.v0"), ("intent", "semantic-consumer-intent.v0")]
    elif rule == "activation_binding": typed = [("decision", "semantic-ak-decision-reference.v0"), ("intent", "semantic-consumer-intent.v0"), ("acceptance", "semantic-owner-acceptance.v0"), ("materialization", "semantic-materialization-verification-receipt.v0")]
    elif rule == "governance_contracts": typed = [("consumer_contract", "semantic-non-authorizing-task-contract.v0")]
    elif rule == "version_binding": expected_context(context["existing_coordinate"], "semantic-release-coordinate.v0")
    elif rule == "publication_cas" and context.get("existing_coordinate") is not None: expected_context(context["existing_coordinate"], "semantic-release-coordinate.v0")
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
    elif rule == "projection":
        expected_context(context["projection"], "semantic-payload-projection.v0", subject["payload_projection_digest"], "projection_mismatch")
        expected_context(context["archive_linkage"], "semantic-capsule-archive-linkage.v0", subject["capsule_archive_linkage_digest"], "projection_mismatch")
    if "canonical_store_head" in context: expected_shape_context(context["canonical_store_head"], "akStoreHead")


def condition_true(value: dict) -> bool:
    if value["kind"] == "evidence_digest_equals":
        computed = value["expected_digest"] is not None and value["expected_digest"] == value["actual_digest"] and value["expected_integer"] is None and value["actual_integer"] is None
    else:
        computed = value["expected_digest"] is None and value["actual_digest"] is None and value["expected_integer"] is not None and value["actual_integer"] is not None and value["actual_integer"] >= value["expected_integer"]
    return value["satisfied"] == computed and computed


def activation_chain_valid(activation: dict, context: dict) -> bool:
    intent, acceptance, materialization, decision = context["intent"], context["acceptance"], context["materialization"], context["decision"]
    return (decision_current(decision, context)
        and activation["issuer"]["kind"] == "consumer_owner"
        and activation["owner_acceptance_digest"] == acceptance["owner_acceptance_digest"]
        and activation["materialization_verification_receipt_digest"] == materialization["materialization_verification_receipt_digest"]
        and acceptance["consumer_intent_digest"] == intent["consumer_intent_digest"] == materialization["consumer_intent_digest"]
        and materialization["owner_acceptance_digest"] == acceptance["owner_acceptance_digest"]
        and activation["consumer_repository"] == acceptance["consumer_repository"] == intent["consumer_repository"] == materialization["consumer_repository"]
        and activation["coordinate"] == intent["desired_coordinate"] == materialization["coordinate"]
        and activation["runtime_identity"] == intent["runtime_identity"] == materialization["runtime_identity"]
        and activation["activation_scope"] == acceptance["accepted_posture"] == intent["requested_posture"]
        and acceptance["acceptance_authority"]["kind"] == "consumer_owner"
        and acceptance["acceptance_authority"]["id"] == intent["consumer_repository"]["owner"]
        and acceptance["revoked_by_digest"] is None
        and intent["intent_revision"] <= acceptance["valid_through_intent_revision"]
        and activation["activation_epoch"] <= acceptance["activation_epoch_not_after"]
        and intent["decision_reference_digest"] == acceptance["decision_reference_digest"] == activation["gate_decision_reference_digest"] == decision["ak_decision_reference_digest"]
        and acceptance["governing_scope_digest"] == decision["scope_digest"]
        and materialization["rollback_ready"] and materialization["journal_state"] == "committed"
        and materialization["rollback_target"] == intent["rollback_target"]
        and materialization["verifier_contract_digest"] == intent["verifier_contract_digest"]
        and materialization["compatibility_outcome"] == intent["accepted_compatibility"]
        and activation["activation_target_digest"] == decision["activation_target_digest"]
        and all(activation[k] == decision[k] for k in ("evidence_criteria_digest", "rollback_plan_digest", "stop_conditions_digest")))


def decision_current(subject: dict, context: dict) -> bool:
    head = subject["ak_store_head"]; canonical = context.get("canonical_store_head", head)
    return subject["lifecycle_state"] == "accepted" and subject["adr_reference"]["status"] == "accepted" and subject["revocation_digest"] is None and subject["superseded_by_decision_record_digest"] is None and head == canonical and head["store_head_digest"] == canonical["store_head_digest"] and head["revocation_head_digest"] == canonical["revocation_head_digest"] and context.get("current_decision_record_digest", subject["decision_record_digest"]) == subject["decision_record_digest"]


def evaluate(rule: str, subject: dict, context: dict) -> str | None:
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
        if old["trust_root_digest"] in context.get("revoked", []): return "trust_revoked"
        action = approval["action"]
        exact_authority = subject["namespace"] == old["namespace"] == new["namespace"] == policy["namespace"] == owner_set["namespace"] == predicate["namespace"] == approval["namespace"] and subject["owner_policy_digest"] == policy["owner_policy_digest"] == old["owner_policy_digest"] == new["owner_policy_digest"] == approval["owner_policy_digest"] and subject["owner_set_digest"] == policy["owner_set_digest"] == old["owner_set_digest"] == new["owner_set_digest"] == approval["owner_set_digest"] == owner_set["owner_set_digest"] and subject["approval_predicate_digest"] == policy["approval_predicate_digest"] == approval["approval_predicate_digest"] == predicate["approval_predicate_digest"]
        transition = subject["old_trust_root_digest"] == context["current_root_digest"] == old["trust_root_digest"] and subject["old_trust_root_id"] == old["trust_root_id"] and subject["old_trust_root_revision"] == old["trust_root_revision"] and subject["new_trust_root_digest"] == new["trust_root_digest"] and subject["new_trust_root_id"] == new["trust_root_id"] and subject["new_trust_root_revision"] == new["trust_root_revision"] == old["trust_root_revision"] + 1 and new["prior_trust_root_digest"] == old["trust_root_digest"] and subject["rotation_revision"] == new["trust_root_revision"]
        action_expected = {"kind": "trust_rotation", "namespace": subject["namespace"], "old_trust_root_digest": subject["old_trust_root_digest"], "new_trust_root_digest": subject["new_trust_root_digest"], "owner_policy_digest": subject["owner_policy_digest"], "owner_set_digest": subject["owner_set_digest"], "approval_predicate_digest": subject["approval_predicate_digest"], "new_trust_root_revision": subject["new_trust_root_revision"], "rotation_revision": subject["rotation_revision"]}
        approval_threshold_valid = evaluate("approval_threshold", approval, {"policy": policy, "owner_set": owner_set, "predicate": predicate}) is None
        valid = exact_authority and transition and approval_threshold_valid and subject["approval_digest"] == approval["owner_approval_digest"] and action == action_expected and action_digest(action) == approval["action_digest"]
        return None if valid else "trust_reference_stale"
    if rule == "trust_revocation":
        approval = context["approval"]; action = approval["action"]
        expected_revision = context["prior_revision"] + 1
        policy, owner_set, predicate = context["policy"], context["owner_set"], context["predicate"]
        authority = subject["namespace"] == policy["namespace"] == owner_set["namespace"] == predicate["namespace"] == approval["namespace"] and approval["owner_policy_digest"] == policy["owner_policy_digest"] and approval["owner_set_digest"] == policy["owner_set_digest"] == owner_set["owner_set_digest"] and approval["approval_predicate_digest"] == policy["approval_predicate_digest"] == predicate["approval_predicate_digest"]
        approval_threshold_valid = evaluate("approval_threshold", approval, {"policy": policy, "owner_set": owner_set, "predicate": predicate}) is None
        valid = authority and approval_threshold_valid and subject["revocation_revision"] == expected_revision and subject["prior_revocation_digest"] == context["prior_head"] and subject["owner_approval_digest"] == approval["owner_approval_digest"] and action["kind"] == "trust_revocation" and action_digest(action) == approval["action_digest"] and all(subject[k] == action[k] for k in ("namespace", "target_kind", "target_digest", "effective_ledger_revision", "reason_digest", "prior_revocation_digest", "revocation_revision")) and action["owner_policy_digest"] == policy["owner_policy_digest"] and action["owner_set_digest"] == owner_set["owner_set_digest"] and action["approval_predicate_digest"] == predicate["approval_predicate_digest"]
        return None if valid else "trust_reference_stale"
    if rule == "compatibility_policy":
        cats = [x["category"] for x in subject["category_rules"]]; expected = {"addition", "documentation", "compatible_refinement", "deprecation", "removal", "rename", "constraint_change", "relation_change", "identifier_reuse", "other"}
        return None if len(cats) == 10 and set(cats) == expected else "compatibility_rejected"
    if rule == "compatibility":
        policy = context["policy"]
        if subject["compatibility_policy_digest"] != policy["compatibility_policy_digest"]: return "compatibility_rejected"
        rules = {x["category"]: x for x in policy["category_rules"]}; conditions = {x["condition_id"]: x for x in subject["conditions"]}
        if len(conditions) != len(subject["conditions"]): return "compatibility_rejected"
        override_rows = context.get("overrides", []); overrides = {x["change_digest"]: x for x in override_rows}
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
                approval = context.get("override_approvals", {}).get(override["owner_approval_digest"])
                action = approval and approval["action"]
                expected_action = {k: copy.deepcopy(override[k]) for k in ("namespace", "compatibility_policy_digest", "change", "change_digest", "from_classification", "from_semver_effect", "to_classification", "semver_effect_floor", "condition")}; expected_action["kind"] = "compatibility_override"
                ranks = {"patch": 0, "minor": 1, "major": 2, "unknown": 2}
                non_lowering = ranks[override["semver_effect_floor"]] >= ranks[effect]
                approval_valid = bool(approval) and evaluate("approval_threshold", approval, {"policy": context["owner_policy"], "owner_set": context["owner_set"], "predicate": context["predicate"]}) is None
                valid = approval_valid and approval["namespace"] == override["namespace"] and context["owner_policy"]["compatibility_policy_digest"] == subject["compatibility_policy_digest"] and row["override_allowed"] and change["category"] != "identifier_reuse" and override["namespace"] == subject["namespace"] and override["compatibility_policy_digest"] == subject["compatibility_policy_digest"] and override["change"] == change and override["change_digest"] == change_digest(change) and override["from_classification"] == classification and override["from_semver_effect"] == effect and condition_true(override["condition"]) and non_lowering and action == expected_action and action_digest(action) == approval["action_digest"]
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
        if new <= old: return "semver_violation"
        valid = effect == "patch" and new[:2] == old[:2] or effect == "minor" and (new[0] > old[0] or new[0] == old[0] and new[1] > old[1]) or effect == "major" and new[0] > old[0]
        return None if valid else "semver_violation"
    if rule == "lifecycle":
        dep, policy, prior, resulting = context["deprecation"], context["policy"], context["prior_tombstones"], context["resulting_tombstones"]
        expected_entry = {"semantic_id": subject["semantic_id"], "reason": context.get("reason", "removed"), "origin_record_digest": subject["removal_record_digest"]}
        expected_entries = copy.deepcopy(prior["entries"]) + [expected_entry]
        expected_entries.sort(key=lambda x: x["semantic_id"].encode())
        exact_chain = dep["prior_lifecycle_digest"] == context.get("deprecation_prior_head") and subject["prior_lifecycle_digest"] == context.get("current_lifecycle_head", dep["deprecation_record_digest"]) == dep["deprecation_record_digest"]
        valid = subject["namespace"] == dep["namespace"] == dep["introduced_coordinate"]["namespace"] == subject["removed_coordinate"]["namespace"] == policy["namespace"] == prior["namespace"] == resulting["namespace"] and subject["semantic_id"] == dep["semantic_id"] and subject["deprecation_record_digest"] == dep["deprecation_record_digest"] and exact_chain and subject["deprecation_ledger_revision"] == dep["introduced_ledger_revision"] and subject["removed_ledger_revision"] > subject["deprecation_ledger_revision"] and subject["required_interval"] == policy["minimum_deprecation_releases"] and subject["removed_ledger_revision"] - subject["deprecation_ledger_revision"] >= subject["required_interval"] and subject["compatibility_policy_digest"] == policy["compatibility_policy_digest"] and subject["prior_tombstone_registry_digest"] == prior["tombstone_registry_digest"] and resulting["prior_registry_digest"] == prior["tombstone_registry_digest"] and resulting["registry_revision"] == prior["registry_revision"] + 1 and subject["semantic_id"] not in {x["semantic_id"] for x in prior["entries"]} and resulting["entries"] == expected_entries
        dep_ledger, rem_ledger = context["deprecation_ledger"], context["removal_ledger"]
        dep_pub, rem_pub = context["deprecation_publication"], context["removal_publication"]
        accepted_records = dep_ledger["namespace"] == rem_ledger["namespace"] == subject["namespace"] and dep_ledger["ledger_revision"] == dep["introduced_ledger_revision"] == context["canonical_deprecation_revision"] and dep_ledger["ledger_head_digest"] == context["canonical_deprecation_head"] == dep_pub["owner_publication_digest"] and dep_ledger["coordinate"] == dep["introduced_coordinate"] == dep_pub["coordinate"] and dep_ledger["publication_status_record_digest"] == dep_pub["owner_publication_digest"] and rem_ledger["ledger_revision"] == subject["removed_ledger_revision"] == context["canonical_removal_revision"] and rem_ledger["ledger_head_digest"] == context["canonical_removal_head"] == rem_pub["owner_publication_digest"] and rem_ledger["coordinate"] == subject["removed_coordinate"] == rem_pub["coordinate"] and rem_ledger["publication_status_record_digest"] == rem_pub["owner_publication_digest"] and dep_pub["status"] == rem_pub["status"] == "published" and dep_ledger["accepted_for_lifecycle"] and rem_ledger["accepted_for_lifecycle"]
        return None if valid and accepted_records else "lifecycle_violation"
    if rule == "tombstone_reuse": return "lifecycle_violation" if any(x["semantic_id"] in {y["semantic_id"] for y in context["tombstones"]["entries"]} for x in subject["changes"]) else None
    if rule == "publication_cas":
        if subject["operation"] == "publish" and subject["status_reason_digest"] is not None or subject["operation"] in {"withdraw", "revoke"} and subject["status_reason_digest"] is None: return "lifecycle_violation"
        if context.get("existing_replay_key") == subject["replay_key_digest"] and context.get("existing_coordinate") == subject["coordinate"] and context.get("existing_operation", subject["operation"]) == subject["operation"]: return None
        if subject["expected_prior_revision"] != context["current_revision"]: return "publication_conflict"
        return None if subject["expected_prior_head_digest"] == context["current_head"] else "publication_fork"
    if rule == "version_binding":
        old, new = context["existing_coordinate"], subject["coordinate"]
        return "version_conflict" if (old["namespace"], old["semantic_version"]) == (new["namespace"], new["semantic_version"]) and old["capsule_digest"] != new["capsule_digest"] else None
    if rule == "publication_commit":
        tx, journal, marker = context["transaction"], context["journal"], context["marker"]; result_digest = subject["owner_publication_digest"]
        valid = tx["operation"] == "publish" and tx["status_reason_digest"] is None and subject["transaction_digest"] == tx["publication_transaction_digest"] == journal["transaction_digest"] == marker["transaction_digest"] and subject["coordinate"] == tx["coordinate"] and subject["ledger_namespace"] == tx["namespace"] == tx["coordinate"]["namespace"] and subject["owner_approval_digest"] == tx["owner_approval_digest"] == context["approval"]["owner_approval_digest"] and subject["trust_root_digest"] == context["trust_root"]["trust_root_digest"] and subject["prior_publication_digest"] == tx["expected_prior_head_digest"] and subject["ledger_revision"] == tx["expected_prior_revision"] + 1 and journal["state"] == "committed" and journal["linearized"] and journal["recovery_action"] == "none" and journal["resulting_record_digest"] == journal["resulting_ledger_head_digest"] == result_digest and journal["resulting_ledger_revision"] == subject["ledger_revision"] and journal["prior_journal_digest"] == context["prior_journal_digest"] == context["prior_journal"]["publication_journal_digest"] and marker["journal_digest"] == journal["publication_journal_digest"] and marker["resulting_record_digest"] == marker["resulting_ledger_head_digest"] == result_digest and marker["resulting_ledger_revision"] == subject["ledger_revision"] and marker["fsync_complete"]
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
        authority_valid = evaluate("approval_threshold", approval, {"policy": policy, "owner_set": owner_set, "predicate": predicate}) is None and approval["action"] == expected_action and action_digest(approval["action"]) == approval["action_digest"]
        valid = valid_from and authority_valid and tx["operation"] == op and tx["owner_approval_digest"] == approval["owner_approval_digest"] == subject["owner_approval_digest"] and tx["publication_transaction_digest"] == subject["transaction_digest"] == journal["transaction_digest"] == marker["transaction_digest"] and tx["coordinate"] == subject["coordinate"] and tx["owner_approval_digest"] == subject["owner_approval_digest"] and tx["status_reason_digest"] == subject["reason_digest"] and tx["expected_prior_head_digest"] == subject["prior_status_record_digest"] and tx["expected_prior_revision"] + 1 == subject["ledger_revision"] and journal["state"] == "committed" and journal["linearized"] and journal["recovery_action"] == "none" and journal["prior_journal_digest"] == context["prior_journal_digest"] and journal["resulting_record_digest"] == journal["resulting_ledger_head_digest"] == result_digest and journal["resulting_ledger_revision"] == subject["ledger_revision"] and marker["journal_digest"] == journal["publication_journal_digest"] and marker["resulting_record_digest"] == marker["resulting_ledger_head_digest"] == result_digest and marker["resulting_ledger_revision"] == subject["ledger_revision"] and marker["fsync_complete"]
        return None if valid else "lifecycle_violation"
    if rule == "publication_recovery":
        state, linear, action = subject["state"], subject["linearized"], subject["recovery_action"]
        if context:
            tx, result = context["transaction"], context["resulting_status"]
            result_digest = result.get("owner_publication_digest", result.get("publication_status_transition_digest"))
            if subject["transaction_digest"] != tx["publication_transaction_digest"] or subject["resulting_record_digest"] != subject["resulting_ledger_head_digest"] or subject["resulting_record_digest"] != result_digest or subject["resulting_ledger_revision"] != result["ledger_revision"]: return "recovery_needed"
        valid_tuple = state in {"prepared", "aborted"} and not linear and action == "discard_staging" or state == "committing" and linear and action == "complete_commit" or state == "committed" and linear and action == "none"
        if not valid_tuple: return "recovery_needed"
        if context:
            before, after = context["before"], context["after"]
            marker = context.get("marker")
            if not linear:
                if after["revision"] != before["revision"] or after["head"] != before["head"] or after["marker"] is not None or after["staging_present"] or after["status_record_digest"] != before["status_record_digest"]: return "recovery_needed"
            else:
                exact_marker = marker and fixture_digest_valid(marker) and after["marker"] == marker and marker["journal_digest"] == subject["publication_journal_digest"] and marker["transaction_digest"] == subject["transaction_digest"] and marker["resulting_record_digest"] == subject["resulting_record_digest"] and marker["resulting_ledger_head_digest"] == subject["resulting_ledger_head_digest"] and marker["resulting_ledger_revision"] == subject["resulting_ledger_revision"]
                if after["revision"] != subject["resulting_ledger_revision"] or after["head"] != subject["resulting_ledger_head_digest"] or after["status_record_digest"] != subject["resulting_record_digest"] or not exact_marker or after["staging_present"]: return "recovery_needed"
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
        valid = rows_ok and acyclic and archive_exact and archive["archive_manifest_digest"] == context["archive_manifest"]["material_manifest_digest"] and p["payload_manifest_digest"] == context["payload_manifest"]["material_manifest_digest"] and p["consumer_manifest_digest"] == context["consumer_manifest"]["material_manifest_digest"] and subject["payload_projection_digest"] == p["payload_projection_digest"] == capsule["payload_projection_digest"] and subject["capsule_archive_linkage_digest"] == archive["capsule_archive_linkage_digest"] == capsule["capsule_archive_linkage_digest"] and subject["source_payload_manifest_digest"] == p["payload_manifest_digest"] and subject["expected_consumer_manifest_digest"] == p["consumer_manifest_digest"] == subject["actual_consumer_manifest_digest"]
        return None if valid else "projection_mismatch"
    if rule == "rollback":
        request = context["request"]; target = request["target"]; before = subject["active_state_before"]; after = subject["active_state_after"]
        activation, decision = context["activation"], context["decision"]
        current_digest, current_revision = context["current_activation_digest"], context["current_activation_revision"]
        canonical_history = context["canonical_history_head"]
        activation_current = activation["activation_receipt_digest"] == current_digest and activation["activation_revision"] == current_revision and activation["status"] == "activated" and activation["revoked_by_digest"] is None and activation["superseded_by_activation_receipt_digest"] is None
        request_valid = activation_current and request["issuer"]["kind"] == "consumer_owner" and request["active_activation_receipt_digest"] == current_digest and request["from_state"]["enabled"] and request["from_state"]["coordinate"] == activation["coordinate"] and request["from_state"]["runtime_identity"] == activation["runtime_identity"] and request["owner_decision_reference_digest"] == decision["ak_decision_reference_digest"] and decision_current(decision, context) and request["recovery_runtime_identity"] != request["from_state"]["runtime_identity"]
        if not request_valid: return "rollback_unavailable"
        proof = context.get("availability")
        if not proof or not fixture_digest_valid(proof) or subject["availability_proof_digest"] != proof["rollback_availability_proof_digest"] or proof["rollback_request_digest"] != request["rollback_request_digest"] or proof["target_kind"] != target["kind"] or proof["canonical_activation_digest"] != current_digest or proof["recovery_runtime_identity"] != request["recovery_runtime_identity"] or not proof["recovery_runtime_available"]: return "rollback_unavailable"
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
        if subject["rollback_request_digest"] != request["rollback_request_digest"] or subject["request_target_kind"] != target["kind"] or before != request["from_state"] or not before["enabled"] or before["coordinate"] is None or subject["history_head_before"] != canonical_history: return "history_conflict"
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
            ak_link, pi_receipt = context.get("ak_linkage"), context.get("pi_receipt")
            if not ak_link or not pi_receipt or ak_digest != ak_link["ak_evidence_linkage_digest"] or pi_digest != pi_receipt["pi_delivery_receipt_digest"] or ak_link["pi_delivery_receipt_digest"] != pi_digest or ak_link["activation_receipt_digest"] != request["active_activation_receipt_digest"]: return "history_conflict"
        if subject["result"] == "failed":
            return None if failed and not completed and after == before and subject["history_head_after"] == canonical_history and subject["supersedes_activation_receipt_digest"] is None else "history_conflict"
        if after != computed: return "history_conflict"
        history = context.get("history_after")
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
        valid = subject["consumer_intent_digest"] == intent["consumer_intent_digest"] and subject["consumer_repository"] == intent["consumer_repository"] and subject["acceptance_authority"]["kind"] == "consumer_owner" and subject["acceptance_authority"]["id"] == subject["consumer_repository"]["owner"] and subject["decision_reference_digest"] == intent["decision_reference_digest"] == decision["ak_decision_reference_digest"] and subject["governing_scope_digest"] == decision["scope_digest"] and subject["accepted_posture"] == intent["requested_posture"] and intent["intent_revision"] <= subject["valid_through_intent_revision"] and subject["revoked_by_digest"] is None and decision_current(decision, context)
        return None if valid else "self_certification"
    if rule == "activation_binding":
        return None if activation_chain_valid(subject, context) else "self_certification"
    if rule == "governance_contracts":
        consumer = context["consumer_contract"]
        expected_paths = ["config/semantic-release/canary.json", "docs/project/semantic-release-canary-evidence.md", "scripts/ci/semantic-release-canary.sh"]
        rd = lambda label: domain_digest("semantic-release.raw-blob.v0", label.encode())
        ak_evidence = ["accepted-decision-reference", "deterministic-rerun", "docs-strict", "node-validator", "owner-task-references", "python-validator", "rollback-rehearsal"]
        ak_stops = ["attempted-owner-substitution", "attempted-use-as-authorization", "missing-owner-task", "scope-drift", "stale-or-revoked-decision", "store-head-drift"]
        consumer_evidence = ["activation-receipt", "canary-evidence", "consumer-intent-and-acceptance", "exact-materialization-receipt", "rollback-availability-proof", "rollback-history-and-rehearsal", "scoped-gate-decision"]
        consumer_stops = ["failed-validator", "missing-owner-consent", "missing-rollback-rehearsal", "projection-or-issuer-drift", "scope-beyond-named-canary", "stale-head-or-trust", "target-or-recovery-unavailable", "unknown-or-incompatible"]
        ak_prereq_ids = ["adr:0053", "decision:53", "plan:decision-53-implementation", "plan:decision-53-validation-rollout-rollback"]
        consumer_prereq_ids = ["adr:0053", "consent:pi-canary-consumer-owner", "decision:53", "plan:decision-53-implementation", "plan:decision-53-validation-rollout-rollback"]
        ak_prereq_digests = sorted(rd(x) for x in ("accepted-adr-0053", "accepted-decision-53", "decision-53-implementation-plan", "decision-53-validation-plan"))
        consumer_prereq_digests = sorted(rd(x) for x in ("accepted-adr-0053", "accepted-decision-53", "consumer-owner-consent", "decision-53-implementation-plan", "decision-53-validation-plan"))
        no_authority = all(not x[k] for x in (subject, consumer) for k in ("authorizes_execution", "authorizes_publication", "authorizes_adoption")) and subject["contract_status"] == consumer["contract_status"] == "candidate_not_created"
        separate = subject["task_contract_id"] != consumer["task_contract_id"] and subject["rollback_owner"]["kind"] == "ak" and consumer["rollback_owner"]["kind"] == "consumer_owner"
        exact = subject["task_contract_id"] == "decision-53-ak-coordination" and subject["task_id"] == "candidate-decision-53-ak-coordination" and subject["task_owner_id"] == subject["rollback_owner"]["id"] == "agent-kernel-owner" and subject["task_kind"] == "ak_coordination" and subject["repository"] == "softwareco/owned/agent-kernel" and subject["allowed_paths"] == [] and subject["dependency_task_ids"] == [] and subject["prerequisite_ids"] == ak_prereq_ids and subject["prerequisite_artifact_digests"] == ak_prereq_digests and subject["required_evidence"] == ak_evidence and subject["stop_conditions"] == ak_stops and subject["authority_scope"] == "coordination_only" and consumer["task_contract_id"] == "decision-53-first-consumer-canary" and consumer["task_id"] == "candidate-decision-53-first-consumer-canary" and consumer["task_owner_id"] == consumer["rollback_owner"]["id"] == "consumer-owner" and consumer["task_kind"] == "first_consumer" and consumer["repository"] == "softwareco/pi-canary-consumer" and consumer["allowed_paths"] == expected_paths and consumer["dependency_task_ids"] == ["candidate-decision-53-ak-coordination", "candidate-decision-53-rocs-implementation", "candidate-decision-53-semantic-owner-publication"] and consumer["prerequisite_ids"] == consumer_prereq_ids and consumer["prerequisite_artifact_digests"] == consumer_prereq_digests and consumer["required_evidence"] == consumer_evidence and consumer["stop_conditions"] == consumer_stops and consumer["authority_scope"] == "consumer_owner_candidate_only"
        return None if no_authority and separate and exact else "self_certification"
    if rule in {"pi_variant", "ak_optional_pi"}: return None
    raise ValidationError(f"unknown differential rule {rule}")


def check_claim_scope(instance: dict) -> None:
    expected = {"semantic-owner-acceptance.v0": ("acceptance_authority", "consumer_owner"), "semantic-materialization-verification-receipt.v0": ("issuer", "rocs"), "semantic-activation-receipt.v0": ("issuer", "consumer_owner"), "semantic-rocs-generation-receipt.v0": ("issuer", "rocs"), "semantic-pi-delivery-receipt.v0": ("issuer", "pi"), "semantic-ak-evidence-linkage.v0": ("issuer", "ak"), "semantic-rollback-request.v0": ("issuer", "consumer_owner"), "semantic-rollback-receipt.v0": ("issuer", "recovery_controller")}
    if (row := expected.get(instance["schema"])) and instance[row[0]]["kind"] != row[1]: raise ValidationError("issuer_scope_violation")


def main() -> int:
    global SCHEMA_ROOT
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
        if actual is None: accepted += 1
        else: rejected += 1
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
    print(f"differential: {len(differential['cases'])} cases ({accepted} accepted transitions, {rejected} expected rejections)")
    print(f"raw-json: {len(differential['raw_json_cases'])} lexical cases ({raw_accepted} accepted, {raw_rejected} expected rejections)")
    print("result: PASS (Python stdlib token-aware validator)")
    return 0


if __name__ == "__main__":
    try: raise SystemExit(main())
    except ValidationError as exc: print(f"result: FAIL: {exc}", file=sys.stderr); raise SystemExit(1)
