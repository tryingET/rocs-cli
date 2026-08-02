from __future__ import annotations

import unittest
import json
import pathlib
import rocs_cli.semantic_adopted_graph as graph
from copy import deepcopy
from unittest.mock import patch

from rocs_cli.semantic_adopted_authority import CandidateSupport
from rocs_cli.semantic_adopted_digests import domain_digest, object_digest
from rocs_cli.semantic_adopted_graph import (
    ISSUE_KINDS, AdoptedGraphError, ExecutionGraphSupport, GraphEdge, ROLE_SPECS, extract_execution_graph,
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
        def replace_placeholder(value):
            if type(value) is dict:
                if value.get("authority_credential_digest") == "sha256:" + "a" * 64:
                    value["authority_credential_digest"] = selected["custodian_credential"]["credential_digest"]
                for child in value.values(): replace_placeholder(child)
            elif type(value) is list:
                for child in value: replace_placeholder(child)
        for value in objects.values(): replace_placeholder(value)
        for role, fields in graph._CONSTANTS.items():
            if role in objects:
                for path, constant in fields.items(): _put(objects[role], path, constant)
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

    def actual_graph(self, branch):
        fixture = pathlib.Path(__file__).parent / "fixtures/semantic-adopted-policy-v1"
        corpus = json.loads((fixture / "execution-corpus.json").read_text("utf-8"))
        bundle = deepcopy(next(case["bundle"] for case in corpus["cases"] if case["name"] == f"branch_{branch}_valid"))
        candidate = deepcopy(corpus["support"]["candidate"])
        copies = graph._CREDENTIAL_COPIES
        selected = {
            "custodian_credential": graph._get(bundle, copies["custodian_credential"][-1]),
            "reviewer_credential": graph._get(bundle, copies["reviewer_credential"][0]),
            "evaluator_credential": graph._get(bundle, copies["evaluator_credential"][0]),
            "gateway_credential": graph._get(bundle, copies["gateway_credential"][1]),
        }
        fallback = selected["custodian_credential"]
        selected = {role: fallback if value is graph._MISSING else value for role, value in selected.items()
        }
        for role, paths in copies.items():
            for path in paths:
                if graph._get(bundle, path) is not graph._MISSING:
                    _put(bundle, path, deepcopy(selected[role]))
        credentials = [deepcopy(selected["custodian_credential"]) for _ in range(12)]
        credentials[8], credentials[9], credentials[10] = (deepcopy(selected[name]) for name in
            ("custodian_credential", "reviewer_credential", "evaluator_credential"))
        candidate_support = CandidateSupport(graph.jcs_bytes(candidate), candidate["candidate_digest"], {}, {}, (), ())
        support = ExecutionGraphSupport(candidate_support, tuple(credentials))
        objects = extract_execution_graph(bundle, support)
        preregistration = objects["preregistration"]
        for index, role in enumerate(graph._PARTICIPANT_CREDENTIALS):
            _put(preregistration, f"participants.{index}.authority.authority_credential_digest",
                 objects[role]["credential_digest"])
        separation = objects["role_separation"]
        separation["participants_digest"] = "sha256:" + __import__("hashlib").sha256(
            graph.jcs_bytes(preregistration["participants"])).hexdigest()
        separation["receipt_digest"] = object_digest("role_separation_receipt", separation, "receipt_digest")
        for join in graph._PRIMITIVE_JOINS:
            if join.left_role in objects and join.right_role in objects:
                joined = graph._get(objects[join.left_role], join.left_path)
                if joined is graph._MISSING:
                    joined = graph._get(objects[join.right_role], join.right_path)
                _put(objects[join.left_role], join.left_path, deepcopy(joined))
                _put(objects[join.right_role], join.right_path, deepcopy(joined))
        separation["participants_digest"] = "sha256:" + __import__("hashlib").sha256(
            graph.jcs_bytes(preregistration["participants"])).hexdigest()
        separation["receipt_digest"] = object_digest("role_separation_receipt", separation, "receipt_digest")
        by_source = {}
        for edge in normative_edges():
            by_source.setdefault(edge.source, []).append(edge)
        for role in sorted(objects, key=lambda item: ROLE_SPECS[item].phase):
            value = objects[role]
            for edge in by_source.get(role, ()):
                if edge.nullable and graph._get(value, edge.digest_field) is None:
                    continue
                target = objects[edge.target]
                _put(value, edge.digest_field, (
                    target[ROLE_SPECS[edge.target].self_digest_field] if ROLE_SPECS[edge.target].self_digest_field
                    else graph._digest(edge.target, target)))
                if edge.object_field:
                    _put(value, edge.object_field, target)
            spec = ROLE_SPECS[role]
            if spec.self_digest_field:
                value[spec.self_digest_field] = object_digest(spec.digest_domain, value, spec.self_digest_field)
        def normalize_authority(value):
            if type(value) is dict:
                digest = value.get("authority_credential_digest")
                for name in ("custodian_credential", "evaluator_credential"):
                    if digest == selected[name]["credential_digest"]:
                        value["authority_role"] = selected[name]["authority_role"]
                for child in value.values(): normalize_authority(child)
            elif type(value) is list:
                for child in value: normalize_authority(child)
        for value in objects.values(): normalize_authority(value)
        authority_pins = (("custody_readiness_request", "expected_custodian_authority", "custody_readiness_subject", "custodian_authority"),
            ("execution_contamination_request", "expected_custodian_authority", "execution_contamination_subject", "custodian_authority"),
            ("execution_contamination_request", "expected_independent_review_authority", "execution_contamination_subject", "independent_review_authority"))
        for request, expected, subject, authority in authority_pins:
            _put(objects[request], expected, deepcopy(objects[subject][authority]))
        preregistration["custodian_authority"] = deepcopy(objects["custody_readiness_subject"]["custodian_authority"])
        preregistration["independent_review_authority"] = deepcopy(objects["execution_contamination_subject"]["independent_review_authority"])
        preregistration["participants"][8]["authority"] = deepcopy(preregistration["custodian_authority"])
        preregistration["participants"][9]["authority"] = deepcopy(preregistration["independent_review_authority"])
        for _ in range(4):
            for join in graph._PRIMITIVE_JOINS:
                if join.left_role in objects and join.right_role in objects:
                    left = graph._get(objects[join.left_role], join.left_path)
                    right = graph._get(objects[join.right_role], join.right_path)
                    score = lambda item: (2 if selected["evaluator_credential"]["credential_digest"] in repr(item) else 1 if selected["custodian_credential"]["credential_digest"] in repr(item) else 0)
                    joined = right if score(right) > score(left) else left
                    _put(objects[join.left_role], join.left_path, deepcopy(joined))
                    _put(objects[join.right_role], join.right_path, deepcopy(joined))
        for _final in range(12):
            authorities = (("custodian", "contamination_custodian_approval"), ("independent_review", "contamination_reviewer_approval"))
            for name, approval in authorities:
                authority = deepcopy(objects[approval]["issuer"])
                objects["execution_contamination_subject"][f"{name}_authority"] = authority
                objects["execution_contamination_request"][f"expected_{name}_authority"] = deepcopy(authority)
                preregistration[f"{name}_authority"] = deepcopy(authority)
                preregistration["participants"][8 if name == "custodian" else 9]["authority"] = deepcopy(authority)
            for join in graph._PRIMITIVE_JOINS:
                if join.left_role in objects and join.right_role in objects and not (
                        join.left_role == join.right_role == "preregistration"):
                    destination, path, source, source_path = (join.left_role, join.left_path, join.right_role, join.right_path) if join.left_role.endswith("_request") else (join.right_role, join.right_path, join.left_role, join.left_path)
                    _put(objects[destination], path, deepcopy(graph._get(objects[source], source_path)))
            separation["participants_digest"] = "sha256:" + __import__("hashlib").sha256(
                graph.jcs_bytes(preregistration["participants"])).hexdigest()
            separation["receipt_digest"] = object_digest("role_separation_receipt", separation, "receipt_digest")
            for role in sorted(objects, key=lambda item: ROLE_SPECS[item].phase):
                value = objects[role]
                for edge in by_source.get(role, ()):
                    if edge.nullable and graph._get(value, edge.digest_field) is None:
                        continue
                    target = objects[edge.target]
                    field = ROLE_SPECS[edge.target].self_digest_field
                    _put(value, edge.digest_field, target[field] if field else graph._digest(edge.target, target))
                    if edge.object_field:
                        _put(value, edge.object_field, target)
                spec = ROLE_SPECS[role]
                if spec.self_digest_field:
                    value[spec.self_digest_field] = object_digest(spec.digest_domain, value, spec.self_digest_field)
        separation["participants_digest"] = "sha256:" + __import__("hashlib").sha256(
            graph.jcs_bytes(preregistration["participants"])).hexdigest()
        separation["receipt_digest"] = object_digest("role_separation_receipt", separation, "receipt_digest")
        for role in sorted(objects, key=lambda item: ROLE_SPECS[item].phase):
            value = objects[role]
            for edge in by_source.get(role, ()):
                if edge.nullable and graph._get(value, edge.digest_field) is None: continue
                target, field = objects[edge.target], ROLE_SPECS[edge.target].self_digest_field
                _put(value, edge.digest_field, target[field] if field else graph._digest(edge.target, target))
                if edge.object_field: _put(value, edge.object_field, target)
            spec = ROLE_SPECS[role]
            if spec.self_digest_field: value[spec.self_digest_field] = object_digest(spec.digest_domain, value, spec.self_digest_field)
        return bundle, support, objects

    def test_actual_execution_corpus_branches_pass_real_active_graph(self):
        for branch, expected in ((0, 68), (7, 85)):
            with self.subTest(branch=branch):
                bundle, support, objects = self.actual_graph(branch)
                self.assertEqual(len(objects), expected)
                post_verdict = {"publication_subject", "publication_approval_body", "publication_approval",
                    "publication_event", "publication_history", "owner_head", "owner_checkpoint"}
                self.assertTrue(post_verdict.isdisjoint(objects))
                if branch == 0:
                    self.assertNotIn("start_proof", objects)
                    self.assertNotIn("raw_execution_receipt", objects)
                self.assertTrue(verify_graph(objects).consistency_verified)
                self.assertTrue(verify_execution_graph(bundle, support).consistency_verified)

    def test_execution_support_is_fixed_exact_and_overlap_checked(self):
        bundle, support, _ = self.actual_graph(7)
        self.assert_kind("missing_preimage", lambda: extract_execution_graph(bundle, support.participant_credentials))
        parsed = json.loads(support.candidate.candidate_bytes)
        self.assert_kind("missing_preimage", lambda: extract_execution_graph(
            bundle, ExecutionGraphSupport(parsed, support.participant_credentials)))
        mismatched = CandidateSupport(support.candidate.candidate_bytes, ZERO, {}, {}, (), ())
        self.assert_kind("digest_mismatch", lambda: extract_execution_graph(
            bundle, ExecutionGraphSupport(mismatched, support.participant_credentials)))
        noncanonical = CandidateSupport(support.candidate.candidate_bytes + b"\n", support.candidate.candidate_digest, {}, {}, (), ())
        self.assert_kind("schema_invalid", lambda: extract_execution_graph(
            bundle, ExecutionGraphSupport(noncanonical, support.participant_credentials)))
        self.assert_kind("missing_preimage", lambda: extract_execution_graph(
            bundle, ExecutionGraphSupport(support.candidate, support.participant_credentials[:-1])))
        changed = list(support.participant_credentials)
        changed[8] = changed[10]
        self.assert_kind("nested_mismatch", lambda: extract_execution_graph(
            bundle, ExecutionGraphSupport(support.candidate, tuple(changed))))

    def test_request_pins_and_contamination_source_reject_substitution(self):
        objects = synthetic_closure("preregistration")
        objects["custody_readiness_request"]["expected_public_key_digest"] = "digest:substituted"
        self.assert_kind("nested_mismatch", lambda: self.mocked_verify(objects))
        objects = synthetic_closure("execution_contamination_request")
        objects["execution_contamination_request"]["expected_independent_review_authority"] = {"substituted": True}
        self.assert_kind("nested_mismatch", lambda: self.mocked_verify(objects))
        objects = synthetic_closure("execution_contamination")
        objects["execution_contamination_subject"]["source_digest"] = "digest:substituted"
        self.assert_kind("digest_mismatch", lambda: self.mocked_verify(objects))

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
