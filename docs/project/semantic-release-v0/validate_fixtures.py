#!/usr/bin/env python3
"""Stdlib-only revision-2 schema, digest, link, and adversarial validator."""

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
    "semantic-rollback-receipt.v0": ("rollback-receipt", "rollback_receipt_digest"),
    "semantic-audit-envelope.v0": ("audit-envelope", "audit_envelope_digest"),
    "semantic-protocol-error.v0": ("error", "error_digest"),
}
DIGEST_FIELDS = {schema: (f"semantic-release.{domain}.v0", field) for schema, (domain, field) in DOMAIN_ROWS.items()}


class ValidationError(Exception):
    pass


def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValidationError(f"{path}: BOM forbidden")
    try:
        return json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=reject_duplicates,
                          parse_float=lambda _: (_ for _ in ()).throw(ValidationError("non-integer number")), parse_int=int)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"{path}: {exc}") from exc


def validate_ijson(value: Any, path: str = "$") -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        if not 0 <= value <= MAX_SAFE_INTEGER:
            raise ValidationError(f"{path}: unsafe integer")
        return
    if isinstance(value, str):
        if unicodedata.normalize("NFC", value) != value:
            raise ValidationError(f"{path}: non-NFC string")
        if any(0xD800 <= ord(c) <= 0xDFFF or 0xFDD0 <= ord(c) <= 0xFDEF or (ord(c) & 0xFFFF) in (0xFFFE, 0xFFFF) for c in value):
            raise ValidationError(f"{path}: forbidden Unicode scalar")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            validate_ijson(item, f"{path}/{index}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            validate_ijson(key, f"{path}/key")
            validate_ijson(item, f"{path}/{key}")
        return
    raise ValidationError(f"{path}: unsupported JSON type")


def utf16_key(value: str) -> bytes:
    return value.encode("utf-16-be")


def jcs(value: Any) -> str:
    validate_ijson(value)
    if value is None: return "null"
    if value is True: return "true"
    if value is False: return "false"
    if isinstance(value, int): return str(value)
    if isinstance(value, str): return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, list): return "[" + ",".join(jcs(x) for x in value) + "]"
    if isinstance(value, dict): return "{" + ",".join(jcs(k) + ":" + jcs(value[k]) for k in sorted(value, key=utf16_key)) + "}"
    raise AssertionError


def domain_digest(domain: str, preimage: bytes) -> str:
    return "sha256:" + hashlib.sha256(domain.encode("ascii") + b"\0" + preimage).hexdigest()


def object_digest(instance: dict[str, Any], domain: str, omitted: str | None) -> tuple[str, str]:
    candidate = copy.deepcopy(instance)
    if omitted is not None:
        if omitted not in candidate:
            raise ValidationError(f"missing self digest {omitted}")
        del candidate[omitted]
    canonical = jcs(candidate)
    return canonical, domain_digest(domain, canonical.encode())


def resolve_ref(root: dict, reference: str) -> dict:
    if not reference.startswith("#/"):
        raise ValidationError(f"external ref forbidden: {reference}")
    node: Any = root
    for token in reference[2:].split("/"):
        node = node[token.replace("~1", "/").replace("~0", "~")]
    if not isinstance(node, dict):
        raise ValidationError("schema ref is not object")
    return node


def schema_validate(instance: Any, schema: dict, root: dict, path: str = "$") -> None:
    if "$ref" in schema:
        schema_validate(instance, resolve_ref(root, schema["$ref"]), root, path); return
    if "oneOf" in schema:
        matches = 0
        for option in schema["oneOf"]:
            try: schema_validate(instance, option, root, path); matches += 1
            except ValidationError: pass
        if matches != 1: raise ValidationError(f"{path}: oneOf matched {matches}")
        return
    if "const" in schema and instance != schema["const"]: raise ValidationError(f"{path}: const mismatch")
    if "enum" in schema and instance not in schema["enum"]: raise ValidationError(f"{path}: enum mismatch")
    expected = schema.get("type")
    if expected == "object":
        if not isinstance(instance, dict): raise ValidationError(f"{path}: expected object")
        props = schema.get("properties", {})
        missing = [x for x in schema.get("required", []) if x not in instance]
        if missing: raise ValidationError(f"{path}: missing {missing}")
        if schema.get("additionalProperties") is False:
            extra = sorted(set(instance) - set(props))
            if extra: raise ValidationError(f"{path}: unknown {extra}")
        for key, value in instance.items():
            if key in props: schema_validate(value, props[key], root, f"{path}/{key}")
    elif expected == "array":
        if not isinstance(instance, list): raise ValidationError(f"{path}: expected array")
        if not schema.get("minItems", 0) <= len(instance) <= schema.get("maxItems", MAX_SAFE_INTEGER): raise ValidationError(f"{path}: array length")
        for index, item in enumerate(instance): schema_validate(item, schema["items"], root, f"{path}/{index}")
    elif expected == "string":
        if not isinstance(instance, str): raise ValidationError(f"{path}: expected string")
        if not schema.get("minLength", 0) <= len(instance) <= schema.get("maxLength", MAX_SAFE_INTEGER): raise ValidationError(f"{path}: string length")
        if "pattern" in schema and re.search(schema["pattern"], instance) is None: raise ValidationError(f"{path}: pattern")
    elif expected == "integer":
        if isinstance(instance, bool) or not isinstance(instance, int): raise ValidationError(f"{path}: expected integer")
        if not schema.get("minimum", -MAX_SAFE_INTEGER) <= instance <= schema.get("maximum", MAX_SAFE_INTEGER): raise ValidationError(f"{path}: integer range")
    elif expected == "boolean":
        if not isinstance(instance, bool): raise ValidationError(f"{path}: expected boolean")
    elif expected == "null":
        if instance is not None: raise ValidationError(f"{path}: expected null")
    elif expected is not None:
        raise ValidationError(f"{path}: unsupported schema type")


def pointer(instance: Any, path: str) -> Any:
    node = instance
    for token in path.lstrip("/").split("/") if path else []:
        node = node[int(token)] if isinstance(node, list) else node[token.replace("~1", "/").replace("~0", "~")]
    return node


def sorted_unique(values: list[str]) -> bool:
    return values == sorted(values, key=lambda x: x.encode()) and len(values) == len(set(values))


def check_order(instance: dict) -> None:
    schema = instance["schema"]
    if schema in {"semantic-source-manifest.v0", "semantic-material-manifest.v0"}:
        entries = instance["entries"]
        keys = [(x["path"].encode(), x["kind"]) for x in entries]
        if keys != sorted(keys) or len({x["path"] for x in entries}) != len(entries): raise ValidationError("manifest order/uniqueness")
    if schema == "semantic-owner-set.v0":
        ids = [x["owner_id"] for x in instance["members"]]
        if not sorted_unique(ids) or any(not sorted_unique(x["key_ids"]) for x in instance["members"]): raise ValidationError("owner set order")
    if schema == "semantic-owner-approval.v0":
        keys = [(x["owner_id"].encode(), x["owner_key_id"].encode()) for x in instance["votes"]]
        if keys != sorted(keys) or len(keys) != len(set(keys)): raise ValidationError("vote order")
        if any(x["approved_candidate_digest"] != instance["candidate_capsule_digest"] for x in instance["votes"]): raise ValidationError("vote candidate mismatch")
    if schema == "semantic-compatibility-policy.v0":
        if not sorted_unique([x["category"] for x in instance["category_rules"]]): raise ValidationError("category rules not exhaustive/sorted")
    if schema == "semantic-compatibility-report.v0":
        keys = [(x["semantic_id"].encode(), x["category"].encode()) for x in instance["changes"]]
        if keys != sorted(keys) or len(keys) != len(set(keys)) or not sorted_unique([x["condition_id"] for x in instance["conditions"]]): raise ValidationError("compatibility order")
    if schema == "semantic-tombstone-registry.v0" and not sorted_unique([x["semantic_id"] for x in instance["entries"]]): raise ValidationError("tombstone order")
    if schema == "semantic-payload-projection.v0" and not sorted_unique([x["capsule_path"] for x in instance["entries"]]): raise ValidationError("projection order")
    if schema == "semantic-release-capsule.v0" and not sorted_unique(instance["required_protocol_versions"]): raise ValidationError("protocol order")
    if schema == "semantic-rocs-generation-receipt.v0":
        if not sorted_unique(instance["candidate_ids"]) or not sorted_unique(instance["pack_digests"]): raise ValidationError("generation set order")
    if schema == "semantic-protocol-error.v0" and not sorted_unique([x["key"] for x in instance["details"]]): raise ValidationError("error detail order")


def strict_utc(value: str) -> bool:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value): return False
    try:
        parsed = dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        return parsed.strftime("%Y-%m-%dT%H:%M:%SZ") == value and parsed.year >= 1
    except ValueError:
        return False


def semver(value: str) -> tuple[int, int, int]:
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", value)
    if not match: raise ValidationError("bad semver")
    return tuple(map(int, match.groups()))  # type: ignore[return-value]


def fixture_digest_valid(subject: dict) -> bool:
    domain, omitted = DIGEST_FIELDS[subject["schema"]]
    return object_digest(subject, domain, omitted)[1] == subject[omitted]


def evaluate(rule: str, subject: dict, context: dict) -> str | None:
    if rule == "digest": return None if fixture_digest_valid(subject) else "digest_mismatch"
    if rule == "approval_threshold":
        members = {x["owner_id"]: x for x in context["owner_set"]["members"]}
        eligible: set[str] = set()
        for vote in subject["votes"]:
            member = members.get(vote["owner_id"])
            if not member or vote["owner_key_id"] not in member["key_ids"]: return "approval_threshold_unsatisfied"
            if member["status"] == "revoked": return "trust_revoked"
            eligible.add(vote["owner_id"])
        predicate = context["predicate"]
        needed = len([x for x in members.values() if x["status"] == "active"]) if predicate["mode"] == "unanimous" else predicate["threshold"]
        return None if len(eligible) >= needed else "approval_threshold_unsatisfied"
    if rule == "trust_rotation":
        if subject["old_trust_root_digest"] in context["revoked"]: return "trust_revoked"
        return None if subject["old_trust_root_digest"] == context["current_root_digest"] else "trust_reference_stale"
    if rule == "compatibility_policy":
        categories = [x["category"] for x in subject["category_rules"]]
        expected = {"addition", "documentation", "compatible_refinement", "deprecation", "removal", "rename", "constraint_change", "relation_change", "identifier_reuse", "other"}
        return None if len(categories) == 10 and set(categories) == expected else "compatibility_rejected"
    if rule == "compatibility":
        policy = context["policy"]
        if subject["compatibility_policy_digest"] != policy["compatibility_policy_digest"]: return "compatibility_rejected"
        rules = {x["category"]: x for x in policy["category_rules"]}
        changes = subject["changes"]
        if any(x["category"] not in rules or x["classification"] != rules[x["category"]]["classification"] or x["semver_effect"] != rules[x["category"]]["semver_effect"] or (rules[x["category"]]["condition_rule"] is None) != (x["condition_id"] is None) for x in changes): return "compatibility_rejected"
        severity = {"patch": 0, "minor": 1, "major": 2, "unknown": 3}
        class_severity = {"compatible": 0, "conditionally_compatible": 1, "breaking": 2, "unknown": 3}
        if changes and (subject["required_semver_effect"] != max((x["semver_effect"] for x in changes), key=lambda x: severity[x]) or subject["classification"] != max((x["classification"] for x in changes), key=lambda x: class_severity[x])): return "compatibility_rejected"
        if subject["classification"] == "unknown": return "compatibility_unknown"
        required_conditions = {x["condition_id"] for x in changes if x["condition_id"] is not None}
        conditions = {x["condition_id"]: x for x in subject["conditions"]}
        if any(conditions.get(x["condition_id"], {}).get("kind") != rules[x["category"]]["condition_rule"]["condition_kind"] for x in changes if x["condition_id"] is not None): return "compatibility_rejected"
        def condition_true(value: dict) -> bool:
            if value["kind"] == "evidence_digest_equals":
                computed = value["expected_digest"] is not None and value["expected_digest"] == value["actual_digest"] and value["expected_integer"] is None and value["actual_integer"] is None
            else:
                computed = value["expected_digest"] is None and value["actual_digest"] is None and value["expected_integer"] is not None and value["actual_integer"] is not None and value["actual_integer"] >= value["expected_integer"]
            return value["satisfied"] == computed and computed
        if any(x not in conditions or not condition_true(conditions[x]) for x in required_conditions):
            return "compatibility_rejected"
        old, new = semver(context["prior_version"]), semver(subject["candidate_version"])
        if new <= old: return "semver_violation"
        effect = subject["required_semver_effect"]
        valid = (effect == "patch" and new[:2] == old[:2]) or (effect == "minor" and (new[0] > old[0] or (new[0] == old[0] and new[1] > old[1]))) or (effect == "major" and new[0] > old[0])
        return None if valid else "semver_violation"
    if rule == "lifecycle":
        dep = context["deprecation"]
        valid = subject["deprecation_record_digest"] == dep["deprecation_record_digest"] and subject["removed_ledger_revision"] - dep["introduced_ledger_revision"] >= context["minimum"]
        return None if valid else "lifecycle_violation"
    if rule == "tombstone_reuse":
        tombstoned = {x["semantic_id"] for x in context["tombstones"]["entries"]}
        return "lifecycle_violation" if any(x["category"] == "identifier_reuse" and x["semantic_id"] in tombstoned for x in subject["changes"]) else None
    if rule == "publication_cas":
        if subject["operation"] == "publish" and subject["status_reason_digest"] is not None: return "lifecycle_violation"
        if subject["operation"] in {"withdraw", "revoke"} and subject["status_reason_digest"] is None: return "lifecycle_violation"
        if context.get("existing_replay_key") == subject["replay_key_digest"] and context.get("existing_coordinate") == subject["coordinate"]: return None
        if subject["expected_prior_revision"] != context["current_revision"]: return "publication_conflict"
        if subject["expected_prior_head_digest"] != context["current_head"]: return "publication_fork"
        return None
    if rule == "version_binding":
        old, new = context["existing_coordinate"], subject["coordinate"]
        return "version_conflict" if (old["namespace"], old["semantic_version"]) == (new["namespace"], new["semantic_version"]) and old["capsule_digest"] != new["capsule_digest"] else None
    if rule == "publication_transition":
        tx, journal, marker = context["transaction"], context["journal"], context["marker"]
        expected_op = "withdraw" if subject["to_status"] == "withdrawn" else "revoke"
        valid = subject["transaction_digest"] == tx["publication_transaction_digest"] and subject["journal_digest"] == journal["publication_journal_digest"] and subject["commit_marker_digest"] == marker["publication_commit_marker_digest"] and tx["operation"] == expected_op and tx["coordinate"] == subject["coordinate"] and tx["status_reason_digest"] == subject["reason_digest"] and journal["transaction_digest"] == tx["publication_transaction_digest"] and journal["state"] == "committed" and journal["linearized"] and marker["transaction_digest"] == tx["publication_transaction_digest"] and marker["journal_digest"] == journal["publication_journal_digest"] and marker["ledger_revision"] == subject["ledger_revision"] and marker["fsync_complete"]
        return None if valid else "lifecycle_violation"
    if rule == "publication_recovery":
        state, linear, action = subject["state"], subject["linearized"], subject["recovery_action"]
        if state in {"prepared", "aborted"} and not linear and action == "discard_staging": return None
        if state == "committing" and linear and action == "complete_commit": return None
        if state == "committed" and linear and action == "none": return None
        return "recovery_needed"
    if rule == "projection":
        projection, capsule, archive = context["projection"], context["capsule"], context["archive_linkage"]
        payload_entries = {x["path"]: x for x in context["payload_manifest"]["entries"]}
        consumer_entries = {x["path"]: x for x in context["consumer_manifest"]["entries"]}
        archive_entries = {x["path"]: x for x in context["archive_manifest"]["entries"]}
        rows_ok = len(projection["entries"]) == len(payload_entries) == len(consumer_entries)
        for row in projection["entries"]:
            relative = row["capsule_path"].removeprefix(archive["payload_root"] + "/")
            p, c, a = payload_entries.get(relative), consumer_entries.get(row["consumer_path"]), archive_entries.get(row["capsule_path"])
            if not p or not c or not a or any(p.get(k) != c.get(k) or p.get(k) != a.get(k) for k in ("kind", "mode", "byte_length", "content_digest")) or row["mode"] != p["mode"] or row["byte_length"] != p.get("byte_length") or row["content_digest"] != p.get("content_digest"):
                rows_ok = False
        valid = rows_ok and archive["archive_manifest_digest"] == context["archive_manifest"]["material_manifest_digest"] and projection["payload_manifest_digest"] == context["payload_manifest"]["material_manifest_digest"] and projection["consumer_manifest_digest"] == context["consumer_manifest"]["material_manifest_digest"] and subject["payload_projection_digest"] == projection["payload_projection_digest"] == capsule["payload_projection_digest"] and subject["capsule_archive_linkage_digest"] == archive["capsule_archive_linkage_digest"] == capsule["capsule_archive_linkage_digest"] and subject["source_payload_manifest_digest"] == projection["payload_manifest_digest"] and subject["expected_consumer_manifest_digest"] == projection["consumer_manifest_digest"] == subject["actual_consumer_manifest_digest"]
        return None if valid else "projection_mismatch"
    if rule == "rollback":
        request = context["request"]
        target, before, after = request["target"], subject["active_state_before"], subject["active_state_after"]
        if subject["result"] == "failed":
            return None if after == before and subject["history_head_after"] == subject["history_head_before"] and subject["error_digest"] else "history_conflict"
        if target["kind"] == "semantic" and (after["runtime_identity"] != before["runtime_identity"] or after["coordinate"] != target["target_coordinate"]): return "history_conflict"
        if target["kind"] == "runtime" and (after["coordinate"] != before["coordinate"] or after["runtime_identity"] != target["target_runtime_identity"] or not target.get("runtime_revalidation_receipt_digest")): return "rollback_unavailable"
        if target["kind"] == "no_prior_disable" and (after["enabled"] or after["coordinate"] is not None): return "history_conflict"
        failed_stages = [x for x in subject["stages"] if x["result"] == "failed"]
        if subject["result"] == "partial_failure" and (not failed_stages or subject["active_state_after"] == before): return "history_conflict"
        if subject["result"] not in {"failed", "partial_failure"} and (subject["error_digest"] is not None or subject["history_head_after"] == subject["history_head_before"]): return "history_conflict"
        return None
    if rule == "generation_activation":
        activation = context["activation"]
        valid = activation["status"] == "activated" and activation["revoked_by_digest"] is None and activation["superseded_by_activation_receipt_digest"] is None and subject["activation_receipt_digest"] == context["current_activation_digest"]
        return None if valid else "activation_not_current"
    if rule == "utc": return None if strict_utc(subject["recorded_at"]) else "malformed_input"
    if rule == "ak_decision": return None if subject["lifecycle_state"] == "accepted" and subject["adr_reference"]["status"] == "accepted" and subject["revocation_digest"] is None else "self_certification"
    if rule == "acceptance_binding":
        decision = context["decision"]
        valid = subject["acceptance_authority"]["kind"] == "consumer_owner" and subject["acceptance_authority"]["id"] == subject["consumer_repository"]["owner"] and subject["decision_reference_digest"] == decision["ak_decision_reference_digest"] and subject["governing_scope_digest"] == decision["scope_digest"] and decision["lifecycle_state"] == "accepted" and decision["revocation_digest"] is None
        return None if valid else "self_certification"
    if rule == "activation_binding":
        decision = context["decision"]
        valid = subject["gate_decision_reference_digest"] == decision["ak_decision_reference_digest"] and all(subject[k] == decision[k] for k in ("activation_target_digest", "evidence_criteria_digest", "rollback_plan_digest", "stop_conditions_digest"))
        return None if valid else "self_certification"
    if rule == "pi_variant": return None
    if rule == "ak_optional_pi": return None
    raise ValidationError(f"unknown differential rule {rule}")


def check_claim_scope(instance: dict) -> None:
    expected = {"semantic-owner-acceptance.v0": ("acceptance_authority", "consumer_owner"), "semantic-materialization-verification-receipt.v0": ("issuer", "rocs"),
        "semantic-activation-receipt.v0": ("issuer", "consumer_owner"), "semantic-rocs-generation-receipt.v0": ("issuer", "rocs"), "semantic-pi-delivery-receipt.v0": ("issuer", "pi"),
        "semantic-ak-evidence-linkage.v0": ("issuer", "ak"), "semantic-rollback-receipt.v0": ("issuer", "recovery_controller")}
    rule = expected.get(instance["schema"])
    if rule and instance[rule[0]]["kind"] != rule[1]: raise ValidationError("issuer_scope_violation")


def main() -> int:
    schema, golden, differential = (load_json(ROOT / name) for name in ("protocol.schema.json", "golden-fixtures.json", "differential-fixtures.json"))
    for value in (schema, golden, differential): validate_ijson(value)
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema": raise ValidationError("wrong schema draft")
    # Every object shape, including nested alternatives, is closed.
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
        schema_validate(instance, schema, schema)
        check_order(instance); check_claim_scope(instance)
        if instance["schema"] == "semantic-audit-envelope.v0" and not strict_utc(instance["recorded_at"]): raise ValidationError("invalid golden UTC")
        canonical, digest = object_digest(instance, record["domain"], record["omitted_field"])
        if canonical != record["canonical_preimage"] or digest != record["digest"]: raise ValidationError(f"{name}: canonical digest mismatch")
        if record["omitted_field"] and instance[record["omitted_field"]] != digest: raise ValidationError(f"{name}: embedded digest mismatch")
        records[name] = record
    for blob in golden["raw_preimages"]:
        if domain_digest(blob["domain"], blob["preimage_utf8"].encode()) != blob["digest"]: raise ValidationError("raw preimage mismatch")
    for assertion in golden["chain_assertions"]:
        if pointer(records[assertion["record"]]["instance"], assertion["instance_path"]) != records[assertion["equals_record"]]["digest"]: raise ValidationError(f"link mismatch {assertion}")

    accepted = rejected = 0
    for item in differential["cases"]:
        subject = item["subject"]
        validate_ijson(subject)
        structural = True
        try: schema_validate(subject, schema, schema)
        except ValidationError: structural = False
        if structural != item["schema_valid"]: raise ValidationError(f"{item['name']}: schema_valid expected {item['schema_valid']}, got {structural}")
        if item["rule"] != "digest" and not fixture_digest_valid(subject): raise ValidationError(f"{item['name']}: counterexample digest masks rule")
        if not structural:
            actual = "malformed_input" if item["expected_error"] == "malformed_input" else item["expected_error"]
        else:
            actual = evaluate(item["rule"], subject, item["context"])
        if actual != item["expected_error"]: raise ValidationError(f"{item['name']}: expected {item['expected_error']}, got {actual}")
        if actual is None: accepted += 1
        else: rejected += 1

    print(f"schema: Draft 2020-12, {len(DIGEST_FIELDS) + 1} protocol types, all object shapes closed")
    print(f"golden: {len(records)} object preimages and {len(golden['raw_preimages'])} raw preimages independently recomputed")
    print(f"chain: {len(golden['chain_assertions'])} exact digest links verified")
    print(f"differential: {len(differential['cases'])} cases ({accepted} accepted transitions, {rejected} expected rejections)")
    print("result: PASS (Python stdlib validator)")
    return 0


if __name__ == "__main__":
    try: raise SystemExit(main())
    except ValidationError as exc:
        print(f"result: FAIL: {exc}", file=sys.stderr); raise SystemExit(1)
