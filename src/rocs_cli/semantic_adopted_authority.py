"""Pure authority and candidate-support checks for adopted policy v1.

All repository observations are explicit inputs.  This module deliberately has no
filesystem, Git, clock, signature, or network integration.
"""
from __future__ import annotations

import base64
import hashlib
import re
from datetime import date
from decimal import Decimal
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from rocs_cli.semantic_adopted_digests import domain_digest, object_digest
from rocs_cli.semantic_adopted_protocol import jcs_bytes, validate_definition
from rocs_cli.semantic_router_invariants import validate_invariants as validate_v0_invariants
from rocs_cli.semantic_router_protocol import (
    RouteProtocolError,
    parse_policy_bytes,
    parse_provenance_bytes,
)

OWNER_REPOSITORY = "softwareco/ontology"
ROLE_ORDER = (
    "semantic_owner", "policy_author", "development_author",
    "acceptance_author", "operational_author", "annotator", "annotator",
    "adjudicator", "custodian", "independent_reviewer",
    "evaluator_operator", "implementer",
)
_STAMP = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?(Z|[+-]\d{2}:\d{2})$"
)
_IDENTITY_FIELDS = (
    "repository_id", "git_commit", "git_tree", "principal_id", "authority_role",
)


class AdoptedAuthorityError(ValueError):
    """An authority coordinate or candidate support input is inconsistent."""


@dataclass(frozen=True)
class CandidateSupport:
    """Deterministic projection proven from the supplied source bytes."""

    policy: dict[str, Any]
    provenance: dict[str, Any]
    policy_concept_ids: tuple[str, ...]
    joint_route_ontology_id_sets: tuple[tuple[str, ...], ...]


def _fail(message: str) -> None:
    raise AdoptedAuthorityError(message)


def _schema(value: Any, definition: str) -> None:
    try:
        issues = validate_definition(value, definition)
    except (TypeError, ValueError) as exc:
        raise AdoptedAuthorityError(f"invalid {definition}") from exc
    if issues:
        _fail(f"invalid {definition}: {issues[0].instance_path or '/'}")


def _sha(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _sorted_strings(values: Sequence[str]) -> list[str]:
    return sorted(values, key=lambda value: value.encode("utf-8"))


def verify_authority_credential(
    authority: Mapping[str, Any], credential: Mapping[str, Any]
) -> None:
    """Verify a closed coordinate is exactly backed by its credential.

    Signature verification is intentionally out of scope; this checks schema,
    identity, credential/key digests, validity ordering, and non-revocation.
    """
    _schema(authority, "authorityCoordinate")
    _schema(credential, "authorityCredential")
    if any(authority[field] != credential[field] for field in _IDENTITY_FIELDS):
        _fail("authority and credential identity differ")
    if authority["authority_credential_digest"] != credential["credential_digest"]:
        _fail("authority credential digest differs")
    try:
        key = base64.b64decode(credential["public_key_base64"], validate=True)
    except (ValueError, TypeError) as exc:
        raise AdoptedAuthorityError("invalid credential public key") from exc
    if len(key) != 32 or base64.b64encode(key).decode("ascii") != credential["public_key_base64"]:
        _fail("credential public key is not canonical raw Ed25519")
    if credential["public_key_digest"] != _sha(key):
        _fail("credential public key digest differs")
    if credential["credential_digest"] != object_digest(
        "authority_credential", dict(credential), "credential_digest"
    ):
        _fail("credential digest differs")
    def instant(value: str) -> Decimal:
        match = _STAMP.fullmatch(value)
        if match is None:  # already excluded by schema; keeps this helper total
            _fail("credential validity timestamp differs")
        year, month, day, hour, minute, second = map(int, match.groups()[:6])
        fraction, zone = match.group(7) or "0", match.group(8)
        offset = 0
        if zone != "Z":
            sign = 1 if zone[0] == "+" else -1
            offset = sign * (int(zone[1:3]) * 3600 + int(zone[4:6]) * 60)
        whole = date(year, month, day).toordinal() * 86400 + hour * 3600 + minute * 60 + second
        return Decimal(whole - offset) + Decimal("0." + fraction)

    if instant(credential["valid_from"]) >= instant(credential["valid_until"]):
        _fail("credential validity interval is not increasing")
    if credential["revoked"] is not False:
        _fail("credential is revoked")


def verify_principal_separation(participants: Sequence[Mapping[str, Any]]) -> None:
    """Check the canonical twelve assignments and their mechanical separation."""
    if type(participants) not in (list, tuple) or len(participants) != 12:
        _fail("participants must contain exactly twelve assignments")
    for participant in participants:
        _schema(participant, "roleAssignment")
    roles = tuple(item["role"] for item in participants)
    if roles != ROLE_ORDER:
        _fail("participant roles are not in canonical order")
    principals = [item["authority"]["principal_id"] for item in participants]
    if len(set(principals)) != 12:
        _fail("participant principals are not pairwise distinct")
    for item in participants:
        authority = item["authority"]
        evidence = item["b0_exposure_evidence"]
        if authority["authority_role"] != item["role"]:
            _fail("authority role differs from assignment")
        if evidence["participant_principal_id"] != authority["principal_id"]:
            _fail("exposure evidence names another principal")
        if evidence["result"] != item["b0_exposure"]:
            _fail("exposure evidence result differs")
        if evidence["evidence_digest"] != item["b0_exposure_evidence_digest"]:
            _fail("exposure evidence digest join differs")
        if evidence["evidence_digest"] != object_digest(
            "b0_exposure_evidence", evidence, "evidence_digest"
        ):
            _fail("exposure evidence digest differs")
        if "policy_bytes" in item["access"] and (
            "sealed_acceptance_rows" in item["access"]
            or "sealed_operational_rows" in item["access"]
        ):
            _fail("participant has policy and sealed-row access")
    for index in (3, 4, 5, 6, 7, 8, 9, 10):
        if participants[index]["b0_exposure"] != "disproven":
            _fail("protected participant B0 exposure is not disproven")


def verify_role_separation_receipt(
    participants: Sequence[Mapping[str, Any]], receipt: Mapping[str, Any],
    *, access_history_digest: str,
) -> None:
    """Verify the receipt projections in addition to principal separation."""
    verify_principal_separation(participants)
    _schema(receipt, "roleSeparationReceipt")
    if receipt["participants_digest"] != _sha(jcs_bytes(list(participants))):
        _fail("participant array digest differs")
    if receipt["access_history_digest"] != access_history_digest:
        _fail("access history digest differs")
    if receipt["receipt_digest"] != object_digest(
        "role_separation_receipt", dict(receipt), "receipt_digest"
    ):
        _fail("role separation receipt digest differs")


def _put(expected: dict[str, bytes], path: str, raw: bytes) -> None:
    previous = expected.setdefault(path, raw)
    if previous != raw:
        _fail("one source path is claimed with different bytes")


def verify_candidate_support(
    candidate: Mapping[str, Any], *, policy_bytes: bytes, provenance_bytes: bytes,
    inventory: Mapping[str, Any], source_blobs: Mapping[str, bytes],
    resolved_owner_commit: str, resolved_owner_tree: str,
) -> CandidateSupport:
    """Verify candidate authority using only caller-supplied immutable observations.

    ``source_blobs`` is the exact path-to-bytes inventory at the supplied resolved
    commit/tree: policy, provenance, ontology inventory, and every Decision 102
    authority/provenance source must be present, with no extra path.
    """
    _schema(candidate, "candidate")
    _schema(inventory, "ontologyInventory")
    if type(policy_bytes) is not bytes or type(provenance_bytes) is not bytes:
        _fail("policy and provenance inputs must be bytes")
    if type(source_blobs) is not dict or any(
        type(path) is not str or type(raw) is not bytes for path, raw in source_blobs.items()
    ):
        _fail("source blobs must be an exact string-to-bytes mapping")
    if candidate["owner"]["owner_repository_id"] != OWNER_REPOSITORY:
        _fail("candidate owner differs")
    if candidate["owner_git_commit"] != resolved_owner_commit or candidate["owner_git_tree"] != resolved_owner_tree:
        _fail("resolved owner commit/tree differ")
    if dict(candidate["ontology_inventory"]) != dict(inventory):
        _fail("supplied inventory differs from nested inventory")
    for field in ("owner", "owner_git_commit", "owner_git_tree", "ontology_snapshot_digest"):
        candidate_field = field if field != "owner" else "owner"
        inventory_field = field
        if candidate[candidate_field] != inventory[inventory_field]:
            _fail("candidate and inventory coordinates differ")
    if inventory["inventory_digest"] != object_digest(
        "ontology_inventory", dict(inventory), "inventory_digest"
    ) or candidate["ontology_inventory_digest"] != inventory["inventory_digest"]:
        _fail("ontology inventory digest differs")
    inventory_ids = inventory["ontology_ids"]
    if inventory_ids != _sorted_strings(inventory_ids):
        _fail("ontology inventory is not UTF-8 sorted")
    selectable = candidate["selectable_ontology_ids"]
    if selectable != _sorted_strings(selectable) or not set(selectable) <= set(inventory_ids):
        _fail("selectable IDs lack exact inventory authority")
    try:
        policy = parse_policy_bytes(policy_bytes)
        provenance = parse_provenance_bytes(provenance_bytes)
    except RouteProtocolError as exc:
        raise AdoptedAuthorityError("invalid Decision 102 policy/provenance bytes") from exc
    failures = validate_v0_invariants(policy, "routingPolicy", provenance=provenance)
    failures += validate_v0_invariants(provenance, "provenanceManifest", policy=policy)
    if failures:
        _fail("Decision 102 policy/provenance invariants differ")
    if policy["authority"]["owner_repo"] != OWNER_REPOSITORY or provenance["policy_owner_repo"] != OWNER_REPOSITORY:
        _fail("Decision 102 policy owner differs")
    if any(record["source_owner_repo"] != OWNER_REPOSITORY for record in provenance["records"]):
        _fail("Decision 102 provenance source owner differs")
    if policy["authority"]["revision"] != resolved_owner_commit or provenance["policy_revision"] != resolved_owner_commit:
        _fail("Decision 102 owner revision differs")
    if any(record["source_revision"] != resolved_owner_commit for record in provenance["records"]):
        _fail("Decision 102 provenance source revision differs")
    if candidate["routing_policy_digest"] != policy["routing_policy_digest"] or candidate["provenance_manifest_digest"] != provenance["provenance_manifest_digest"]:
        _fail("candidate Decision 102 digest join differs")
    concepts = _sorted_strings([item["ont_id"] for item in policy["concepts"]])
    joints = [_sorted_strings(item["ont_ids"]) for item in policy["joint_routes"]]
    joints.sort(key=jcs_bytes)
    if len(concepts) != len(set(concepts)) or any(len(row) != len(set(row)) for row in joints):
        _fail("Decision 102 ontology projection is not a set")
    supported = set(selectable) & set(inventory_ids)
    if any(item not in supported for item in concepts) or any(item not in supported for row in joints for item in row):
        _fail("policy ID lacks candidate and inventory membership")
    binding = candidate["policy_semantic_binding"]
    receipt = binding["binding_receipt"]
    source_owners = [OWNER_REPOSITORY]
    expected_receipt = {
        "schema": "semantic-routing-policy-binding-receipt.v1",
        "extractor_algorithm": "rocs-adopted-policy-binding-v1",
        "routing_policy_digest": policy["routing_policy_digest"],
        "provenance_manifest_digest": provenance["provenance_manifest_digest"],
        "inventory_digest": inventory["inventory_digest"],
        "policy_owner_repository_id": OWNER_REPOSITORY,
        "provenance_policy_owner_repository_id": OWNER_REPOSITORY,
        "provenance_source_owner_repository_ids": source_owners,
        "policy_concept_ids_digest": domain_digest("policy_concept_ids", concepts),
        "joint_route_sets_digest": domain_digest("joint_route_sets", joints),
    }
    if {key: receipt.get(key) for key in expected_receipt} != expected_receipt:
        _fail("binding receipt projection differs")
    if receipt["receipt_digest"] != object_digest("policy_binding_receipt", receipt, "receipt_digest"):
        _fail("binding receipt digest differs")
    expected_binding = {
        "policy_owner_repository_id": OWNER_REPOSITORY,
        "provenance_owner_repository_id": OWNER_REPOSITORY,
        "inventory_digest": inventory["inventory_digest"],
        "policy_concept_ids": concepts,
        "joint_route_ontology_id_sets": joints,
        "provenance_source_owner_repository_ids": source_owners,
        "binding_receipt": receipt,
        "binding_receipt_digest": receipt["receipt_digest"],
    }
    if {key: binding.get(key) for key in expected_binding} != expected_binding:
        _fail("policy semantic binding projection differs")
    if binding["binding_digest"] != object_digest("policy_semantic_binding", binding, "binding_digest"):
        _fail("policy semantic binding digest differs")
    expected_sources: dict[str, bytes] = {}
    _put(expected_sources, candidate["policy_path"], policy_bytes)
    _put(expected_sources, candidate["provenance_path"], provenance_bytes)
    _put(expected_sources, candidate["ontology_inventory_path"], jcs_bytes(inventory))
    authority = policy["authority"]
    for path, raw_digest in [(authority["path"], authority["source_content_digest"]), *[
        (record["source_path"], record["source_content_digest"]) for record in provenance["records"]
    ]]:
        raw = source_blobs.get(path)
        if raw is None or _sha(raw) != raw_digest:
            _fail("source path/byte digest join differs")
        _put(expected_sources, path, raw)
    if source_blobs != expected_sources:
        _fail("source blob inventory is not exact")
    if candidate["candidate_digest"] != object_digest("candidate", dict(candidate), "candidate_digest"):
        _fail("candidate digest differs")
    return CandidateSupport(policy, provenance, tuple(concepts), tuple(tuple(row) for row in joints))
