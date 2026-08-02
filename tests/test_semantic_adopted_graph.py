from __future__ import annotations

import unittest
import json
import pathlib
import rocs_cli.semantic_adopted_graph as graph
from copy import deepcopy
from unittest.mock import patch

from rocs_cli.semantic_adopted_digests import domain_digest, object_digest
from rocs_cli.semantic_adopted_graph import (
    ISSUE_KINDS, AdoptedGraphError, GraphEdge, ROLE_SPECS, extract_execution_graph,
    normative_edges, verify_execution_graph, verify_graph,
)


ZERO = "sha256:" + "0" * 64


def inventory():
    value = {
        "schema": "semantic-routing-policy-ontology-inventory.v1",
        "owner": {"owner_company": "softwareco", "owner_repository_id": "softwareco/ontology", "namespace": "softwareco.semantic-routing-policy.v1"},
        "owner_git_commit": "1" * 40,
        "owner_git_tree": "2" * 40,
        "ontology_snapshot_digest": ZERO,
        "ontology_ids": ["co.software.synthetic"],
        "inventory_digest": ZERO,
    }
    value["inventory_digest"] = object_digest("ontology_inventory", value, "inventory_digest")
    return value


def acquisition_channel():
    # A schema-valid isolated coordinate is useful for self-digest negatives; it
    # deliberately carries no authority assertion or live acquisition claim.
    value = {
        "schema": "semantic-routing-policy-evaluator-authenticated-channel-coordinate.v1",
        "channel_id": "synthetic-channel",
        "binding_algorithm": "mutual-tls-1.3-exporter-sha256",
        "exporter_context": "rocs-semantic-policy-evaluator-launch-v1",
        "exporter_digest": ZERO,
        "evaluator_authority": {
            "principal_id": "synthetic-evaluator", "repository_id": "synthetic/repo",
            "git_commit": "3" * 40, "git_tree": "4" * 40,
            "authority_credential_digest": ZERO, "authority_role": "evaluator_operator",
        },
        "launch_gateway_authority": {
            "principal_id": "synthetic-gateway", "repository_id": "synthetic/repo",
            "git_commit": "5" * 40, "git_tree": "6" * 40,
            "authority_credential_digest": ZERO, "authority_role": "custodian",
        },
        "established_at": "2030-01-01T00:00:00Z",
        "expires_at": "2030-01-01T00:01:00Z",
        "channel_coordinate_digest": ZERO,
    }
    value["channel_coordinate_digest"] = object_digest(
        "evaluator_authenticated_channel_coordinate", value, "channel_coordinate_digest"
    )
    return value


def binding_receipt(inventory_digest):
    value = {
        "schema": "semantic-routing-policy-binding-receipt.v1",
        "extractor_algorithm": "rocs-adopted-policy-binding-v1",
        "routing_policy_digest": ZERO,
        "provenance_manifest_digest": ZERO,
        "inventory_digest": inventory_digest,
        "policy_owner_repository_id": "softwareco/ontology",
        "provenance_policy_owner_repository_id": "softwareco/ontology",
        "provenance_source_owner_repository_ids": ["softwareco/ontology"],
        "policy_concept_ids_digest": domain_digest("policy_concept_ids", ["co.software.synthetic"]),
        "joint_route_sets_digest": domain_digest("joint_route_sets", []),
        "receipt_digest": ZERO,
    }
    value["receipt_digest"] = object_digest("policy_binding_receipt", value, "receipt_digest")
    return value


def _put(root, path, value):
    tokens = path.split(".")
    current = root
    for index, token in enumerate(tokens[:-1]):
        following = tokens[index + 1]
        if token.isdigit() or token == "-1":
            if token == "-1" and not current:
                current.append([] if following.isdigit() or following == "-1" else {})
            position = len(current) - 1 if token == "-1" else int(token)
            while len(current) <= position:
                current.append([] if following.isdigit() or following == "-1" else {})
            current = current[position]
        else:
            current = current.setdefault(token, [] if following.isdigit() or following == "-1" else {})
    final = tokens[-1]
    if final.isdigit() or final == "-1":
        if final == "-1" and not current:
            current.append(None)
        position = len(current) - 1 if final == "-1" else int(final)
        while len(current) <= position:
            current.append(None)
        current[position] = value
    else:
        current[final] = value


def synthetic_closure(root, *, present_nullable=()):
    """Construct the static predecessor closure for graph-mechanics tests."""
    present_nullable = set(present_nullable)
    objects = {}
    by_source = {}
    for edge in normative_edges():
        by_source.setdefault(edge.source, []).append(edge)

    def add(role):
        if role in objects:
            return objects[role]
        value = {"self": "digest:" + role}
        field = ROLE_SPECS[role].self_digest_field
        if field:
            value[field] = value["self"]
        value.update(graph._CONSTANTS.get(role, {}))
        objects[role] = value
        for edge in by_source.get(role, ()):
            if edge.nullable and edge.target not in present_nullable:
                _put(value, edge.digest_field, None)
                if edge.object_field:
                    _put(value, edge.object_field, None)
                continue
            target = add(edge.target)
            _put(value, edge.digest_field, target["self"])
            if edge.object_field:
                _put(value, edge.object_field, target)
        return value

    add(root)
    authority_groups = (
        ({"authority_credential_digest": "digest:custodian_credential", "principal": "custodian"}, (("preregistration","custodian_authority"),("preregistration","participants.8.authority"),("activation_subject","custodian_authority"),("closure_subject","custodian_authority"),("readiness_approval","issuer"),("activation_approval","issuer"),("closure_approval","issuer"),("verdict_custodian_approval","issuer"),("execution_contamination_subject","custodian_authority"),("contamination_custodian_approval","issuer"))),
        ({"authority_credential_digest": "digest:reviewer_credential", "principal": "reviewer"}, (("preregistration","independent_review_authority"),("preregistration","participants.9.authority"),("verdict_subject","independent_review_authority"),("verdict_reviewer_approval","issuer"),("execution_contamination_subject","independent_review_authority"),("contamination_reviewer_approval","issuer"))),
        ({"authority_credential_digest": "digest:evaluator_credential", "principal": "evaluator"}, (("reservation","executor_authority"),("activation_subject","executor_authority"),("start_subject","evaluator_authority"),("channel","evaluator_authority"),("start_request","expected_evaluator_authority"),("launch_subject","evaluator_authority"),("handoff_subject","evaluator_authority"),("closure_subject","executor_authority"),("start_approval","issuer"))),
        ({"authority_credential_digest": "digest:gateway_credential", "principal": "gateway"}, (("channel","launch_gateway_authority"),("start_request","expected_launch_gateway_authority"),("launch_subject","launch_gateway_authority"),("handoff_subject","launch_gateway_authority"),("launch_approval","issuer"),("handoff_approval","issuer"))),
    )
    for authority, coordinates in authority_groups:
        for role, path in coordinates:
            if role in objects:
                _put(objects[role], path, authority)
    for index, join in enumerate(graph._PRIMITIVE_JOINS):
        if join.left_role not in objects or join.right_role not in objects:
            continue
        value = graph._get(objects[join.left_role], join.left_path)
        if value is graph._MISSING:
            value = graph._get(objects[join.right_role], join.right_path)
        if value is graph._MISSING:
            value = {"primitive": index}
        _put(objects[join.left_role], join.left_path, value)
        _put(objects[join.right_role], join.right_path, value)
    if "preregistration" in objects:
        for index, credential in enumerate(graph._PARTICIPANT_CREDENTIALS):
            if credential in objects:
                _put(objects["preregistration"], f"participants.{index}.authority.authority_credential_digest", objects[credential]["self"])
    for _ in range(3):
        for join in graph._PRIMITIVE_JOINS:
            if join.left_role in objects and join.right_role in objects:
                value = graph._get(objects[join.left_role], join.left_path)
                if value is not graph._MISSING:
                    _put(objects[join.right_role], join.right_path, value)
    return objects


class AdoptedGraphTests(unittest.TestCase):
    def assert_kind(self, kind, function):
        with self.assertRaises(AdoptedGraphError) as caught:
            function()
        self.assertEqual(caught.exception.kind, kind)
        self.assertIn(kind, ISSUE_KINDS)

    def mocked_verify(self, objects):
        with patch("rocs_cli.semantic_adopted_graph._digest", side_effect=lambda role, value: value["self"]):
            return verify_graph(objects)

    def test_static_topology_covers_actual_s2_preimages_and_is_ordered(self):
        required = {
            "role_separation", "base_access_history", "activated_access_history",
            "terminal_access_history", "candidate_contamination", "execution_contamination",
            "custodian_credential", "reviewer_credential", "evaluator_credential",
            "gateway_credential", "readiness_approval", "activation_approval",
            "start_approval", "launch_approval", "handoff_approval", "closure_approval",
            "verdict_custodian_approval", "verdict_reviewer_approval",
            "publication_approval", "raw_execution_receipt", "publication_subject",
        }
        self.assertTrue(required <= set(ROLE_SPECS))
        self.assertGreaterEqual(len(ROLE_SPECS), 69)
        self.assertGreaterEqual(len(normative_edges()), 160)
        for edge in normative_edges():
            self.assertNotEqual(edge.source, edge.target)
            self.assertLess(ROLE_SPECS[edge.target].phase, ROLE_SPECS[edge.source].phase)

    def test_isolated_preimage_proves_consistency_not_authority(self):
        result = verify_graph({"inventory": inventory()})
        self.assertTrue(result.consistency_verified)
        self.assertFalse(result.authority_verified)

    def test_required_digest_join_uses_supplied_preimage(self):
        inv = inventory()
        receipt = binding_receipt(inv["inventory_digest"])
        supplied = {"inventory": inv, "binding_receipt": receipt,
                    "policy_concept_ids": ["co.software.synthetic"], "joint_route_sets": []}
        self.assertTrue(verify_graph(supplied).consistency_verified)
        receipt["inventory_digest"] = ZERO
        receipt["receipt_digest"] = object_digest("policy_binding_receipt", receipt, "receipt_digest")
        self.assert_kind("digest_mismatch", lambda: verify_graph({**supplied, "binding_receipt": receipt}))

    def test_exact_self_digest_and_schema_are_required(self):
        value = inventory()
        value["ontology_ids"] = ["co.software.changed"]
        self.assert_kind("digest_mismatch", lambda: verify_graph({"inventory": value}))
        value = inventory()
        value["unexpected"] = "not leaked"
        self.assert_kind("schema_invalid", lambda: verify_graph({"inventory": value}))

    def test_start_subject_has_all_predecessors_and_stage_approvals_bind_subjects(self):
        start_targets = {edge.target for edge in normative_edges() if edge.source == "start_subject"}
        self.assertTrue({"preregistration", "attempt_envelope", "reservation", "activation", "invocation_challenge", "channel"} <= start_targets)
        for name, subject in {
            "readiness": "custody_readiness_subject", "activation": "activation_subject",
            "start": "start_subject", "launch": "launch_subject", "handoff": "handoff_subject",
            "closure": "closure_subject", "verdict_custodian": "verdict_subject",
            "verdict_reviewer": "verdict_subject", "publication": "publication_subject",
        }.items():
            self.assertIn(GraphEdge(f"{name}_approval", "subject_digest", subject), normative_edges())
        objects = synthetic_closure("start_proof")
        objects["start_approval"]["subject_digest"] = "digest:other-subject"
        self.assert_kind("digest_mismatch", lambda: self.mocked_verify(objects))

    def test_process_id_authority_channel_and_seal_primitive_joins(self):
        present = {"start_proof", "start_request", "launch", "handoff", "raw_execution_receipt"}
        objects = synthetic_closure("verdict", present_nullable=present)
        for role in ("invocation_challenge", "start_subject", "launch_subject", "handoff_subject", "closure_subject"):
            objects[role]["process_start_id"] = "process-one"
        self.assertTrue(self.mocked_verify(objects).consistency_verified)
        objects["closure_subject"]["process_start_id"] = "process-two"
        self.assert_kind("nested_mismatch", lambda: self.mocked_verify(objects))
        objects = synthetic_closure("verdict", present_nullable=present)
        objects["channel"]["evaluator_authority"] = {"coordinate": "changed"}
        self.assert_kind("nested_mismatch", lambda: self.mocked_verify(objects))

    def test_actual_bundle_extraction_invokes_full_92_role_graph(self):
        present = {"start_proof", "start_request", "launch", "handoff", "raw_execution_receipt"}
        supplied = synthetic_closure("owner_checkpoint", present_nullable=present)
        self.assertEqual(set(supplied), set(ROLE_SPECS))
        corpus = json.loads((pathlib.Path(__file__).parent / "fixtures/semantic-adopted-policy-v1/execution-corpus.json").read_text("utf-8"))
        bundle = next(case["bundle"] for case in corpus["cases"] if case["name"] == "branch_7_valid")
        extracted = extract_execution_graph(bundle, supplied)
        self.assertEqual(len(extracted), 92)
        self.assertIs(extracted["attempt"], bundle["attempt"])
        with patch("rocs_cli.semantic_adopted_graph.verify_graph") as invoked:
            invoked.return_value = object()
            verify_execution_graph(bundle, supplied)
            invoked.assert_called_once()
            mapped = invoked.call_args.args[0]
            self.assertEqual(set(mapped), set(ROLE_SPECS))
            self.assertEqual(len(mapped), 92)
            self.assertIs(mapped["verdict"], bundle["verdict"])
        incomplete = dict(supplied)
        incomplete.pop("candidate")
        self.assert_kind("missing_preimage", lambda: extract_execution_graph(bundle, incomplete))

    def test_nullable_dependencies_are_exactly_conditional(self):
        absent = synthetic_closure("attempt")
        result = self.mocked_verify(absent)
        self.assertFalse(result.authority_verified)
        self.assertNotIn("raw_execution_receipt", absent)

        present = synthetic_closure("attempt", present_nullable={
            "start_proof", "start_request", "launch", "handoff", "raw_execution_receipt",
        })
        self.assertTrue(self.mocked_verify(present).consistency_verified)
        del present["raw_execution_receipt"]
        self.assert_kind("missing_preimage", lambda: self.mocked_verify(present))

        inconsistent = synthetic_closure("attempt")
        inconsistent["attempt"]["execution_receipt_digest"] = "digest:raw_execution_receipt"
        self.assert_kind("missing_preimage", lambda: self.mocked_verify(inconsistent))
        inconsistent = synthetic_closure("attempt")
        inconsistent["attempt"]["evaluator_execution_start_proof"] = {"detached": True}
        self.assert_kind("nested_mismatch", lambda: self.mocked_verify(inconsistent))

    def test_nested_object_equality_not_only_digest(self):
        objects = synthetic_closure("verdict", present_nullable={
            "start_proof", "start_request", "launch", "handoff", "raw_execution_receipt",
        })
        self.assertTrue(self.mocked_verify(objects).consistency_verified)
        objects["verdict"]["attempt_envelope"] = deepcopy(objects["attempt_envelope"])
        objects["verdict"]["attempt_envelope"]["changed"] = True
        self.assert_kind("nested_mismatch", lambda: self.mocked_verify(objects))

    def test_preregistration_verdict_and_publication_embedded_joins_are_closed(self):
        for root, field in (
            ("preregistration", "preexecution_verification_bundle"),
            ("verdict", "verdict_approval_subject"),
            ("publication_event", "publication_approval_subject"),
            ("publication_history", "events"),
        ):
            objects = synthetic_closure(root)
            self.assertTrue(self.mocked_verify(objects).consistency_verified)
            if field == "events":
                changed = deepcopy(objects[root][field][-1])
                changed["changed"] = True
                objects[root][field][-1] = changed
            else:
                changed = deepcopy(objects[root][field])
                changed["changed"] = True
                objects[root][field] = changed
            self.assert_kind("nested_mismatch", lambda objects=objects: self.mocked_verify(objects))

    def test_raw_execution_receipt_is_an_explicit_byte_preimage(self):
        result = verify_graph({"raw_execution_receipt": b"synthetic raw receipt"})
        self.assertTrue(result.consistency_verified)
        self.assertFalse(result.authority_verified)
        self.assert_kind("schema_invalid", lambda: verify_graph({"raw_execution_receipt": {}}))

    def test_opaque_request_and_unknown_role_reject(self):
        objects = synthetic_closure("preregistration")
        del objects["custody_readiness_request"]
        self.assert_kind("opaque_caller_request", lambda: self.mocked_verify(objects))
        self.assert_kind("unknown_role", lambda: verify_graph({"inventory": inventory(), "invented": {}}))

    def test_caller_cannot_replace_static_edges(self):
        self.assert_kind("self_edge", lambda: verify_graph(
            {"inventory": inventory()}, edges=[GraphEdge("inventory", "inventory_digest", "inventory")]))
        self.assert_kind("phase_forward_edge", lambda: verify_graph(
            {"inventory": inventory(), "channel": acquisition_channel()},
            edges=[GraphEdge("inventory", "inventory_digest", "channel")]))
        self.assert_kind("back_edge", lambda: verify_graph(
            {"inventory": {}, "custody_policy": {}},
            edges=[GraphEdge("inventory", "inventory_digest", "custody_policy")]))

    def test_safe_error_contains_no_object_value(self):
        value = inventory()
        value["unexpected"] = "sensitive-synthetic-value"
        with self.assertRaises(AdoptedGraphError) as caught:
            verify_graph({"inventory": value})
        self.assertNotIn("sensitive", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
