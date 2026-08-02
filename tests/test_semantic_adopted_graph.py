from __future__ import annotations

import unittest
import json
import pathlib
import rocs_cli.semantic_adopted_graph as graph
from copy import deepcopy

from rocs_cli.semantic_adopted_authority import CandidateSupport
from rocs_cli.semantic_adopted_digests import domain_digest, object_digest
from rocs_cli.semantic_adopted_graph import (
    ISSUE_KINDS, AdoptedGraphError, ExecutionGraphSupport, GraphEdge, ROLE_SPECS, extract_execution_graph,
    normative_edges, verify_execution_graph, verify_graph,
)


ZERO = "sha256:" + "0" * 64


def inventory():
    fixture = pathlib.Path(__file__).parent / "fixtures/semantic-adopted-policy-v1/candidate-support-corpus.json"
    return deepcopy(json.loads(fixture.read_text("utf-8"))["candidate"]["ontology_inventory"])


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



class AdoptedGraphTests(unittest.TestCase):
    def assert_kind(self, kind, function):
        with self.assertRaises(AdoptedGraphError) as caught:
            function()
        self.assertEqual(caught.exception.kind, kind)
        self.assertIn(kind, ISSUE_KINDS)

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

    def test_stage_ancestry_approvals_and_purposes_are_normative(self):
        self.assertTrue({"preregistration", "attempt_envelope", "reservation", "activation", "invocation_challenge", "channel"} <= {e.target for e in normative_edges() if e.source == "start_subject"})
        for name, subject in graph._APPROVAL_SUBJECTS.items():
            self.assertIn(GraphEdge(f"{name}_approval", "subject_digest", subject), normative_edges())
        self.assertEqual(graph._CONSTANTS["readiness_approval"]["purpose"], "custody_readiness")


    def test_process_authority_channel_seal_and_timing_joins_are_normative(self):
        joins = {(j.left_role, j.left_path, j.right_role, j.right_path) for j in graph._PRIMITIVE_JOINS}
        required = {
            ("launch_subject", "process_start_id", "closure_subject", "process_start_id"),
            ("reservation", "executor_authority", "channel", "evaluator_authority"),
            ("channel", "launch_gateway_authority", "start_request", "expected_launch_gateway_authority"),
            ("attempt_envelope", "acceptance_dataset_seal_digest", "handoff_subject", "acceptance_dataset_seal_digest"),
            ("activation_subject", "expires_at", "closure_subject", "activation_expires_at"),
        }
        self.assertTrue(required <= joins)


    def actual_graph(self, branch):
        fixture = pathlib.Path(__file__).parent / "fixtures/semantic-adopted-policy-v1"
        corpus = json.loads((fixture / "execution-corpus.json").read_text("utf-8"))
        bundle = deepcopy(next(case["bundle"] for case in corpus["cases"] if case["name"] == f"branch_{branch}_valid"))
        authority = json.loads((fixture / "candidate-support-corpus.json").read_text("utf-8"))
        candidate = deepcopy(authority["candidate"])
        bundle["verdict"]["contamination_manifest"] = deepcopy(authority["contamination_manifest"])
        prereg = bundle["verdict"]["preregistration"]
        receipt, request = deepcopy(authority["custody_readiness_receipt"]), deepcopy(authority["custody_readiness_request"])
        prereg["custody_readiness_receipt"] = receipt
        prereg["preexecution_verification_bundle"]["custody_readiness_verification_request"] = request
        copies = graph._CREDENTIAL_COPIES
        selected = {
            "custodian_credential": receipt["custodian_credential"],
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
        support = ExecutionGraphSupport(candidate_support, tuple(credentials), receipt["subject"], receipt, request)
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
        for _final in range(20):
            readiness_request, readiness_subject = objects["custody_readiness_request"], objects["custody_readiness_subject"]
            readiness_request["expected_custodian_authority"] = deepcopy(readiness_subject["custodian_authority"])
            readiness_request["expected_concept_inventory"] = deepcopy(objects["inventory"])
            readiness_request["expected_concept_inventory_digest"] = objects["inventory"]["inventory_digest"]
            for approval in ("readiness_approval", "contamination_custodian_approval", "activation_approval", "closure_approval", "verdict_custodian_approval"):
                objects[approval]["issuer"] = deepcopy(readiness_subject["custodian_authority"])
                objects[approval]["attestation_body"]["issuer"] = deepcopy(readiness_subject["custodian_authority"])
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
        support = ExecutionGraphSupport(candidate_support, tuple(credentials), objects["custody_readiness_subject"], objects["custody_readiness"], objects["custody_readiness_request"])
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
        parsed = json.loads(support.candidate_support.candidate_bytes)
        self.assert_kind("missing_preimage", lambda: extract_execution_graph(
            bundle, ExecutionGraphSupport(parsed, support.participant_credentials, support.custody_readiness_subject, support.custody_readiness_receipt, support.custody_readiness_request)))
        mismatched = CandidateSupport(support.candidate_support.candidate_bytes, ZERO, {}, {}, (), ())
        self.assert_kind("digest_mismatch", lambda: extract_execution_graph(
            bundle, ExecutionGraphSupport(mismatched, support.participant_credentials, support.custody_readiness_subject, support.custody_readiness_receipt, support.custody_readiness_request)))
        noncanonical = CandidateSupport(support.candidate_support.candidate_bytes + b"\n", support.candidate_support.candidate_digest, {}, {}, (), ())
        self.assert_kind("schema_invalid", lambda: extract_execution_graph(
            bundle, ExecutionGraphSupport(noncanonical, support.participant_credentials, support.custody_readiness_subject, support.custody_readiness_receipt, support.custody_readiness_request)))
        self.assert_kind("missing_preimage", lambda: extract_execution_graph(
            bundle, ExecutionGraphSupport(support.candidate_support, support.participant_credentials[:-1], support.custody_readiness_subject, support.custody_readiness_receipt, support.custody_readiness_request)))
        substituted_request = deepcopy(support.custody_readiness_request)
        substituted_request["expected_concept_inventory_digest"] = ZERO
        self.assert_kind("nested_mismatch", lambda: extract_execution_graph(bundle,
            ExecutionGraphSupport(support.candidate_support, support.participant_credentials, support.custody_readiness_subject, support.custody_readiness_receipt, substituted_request)))
        changed = list(support.participant_credentials)
        changed[8] = changed[10]
        self.assert_kind("nested_mismatch", lambda: extract_execution_graph(
            bundle, ExecutionGraphSupport(support.candidate_support, tuple(changed), support.custody_readiness_subject, support.custody_readiness_receipt, support.custody_readiness_request)))

    def test_r14_inventory_request_and_contamination_substitutions_reject(self):
        _bundle, _support, objects = self.actual_graph(7)
        request = objects["custody_readiness_request"]
        changed = deepcopy(objects["inventory"])
        changed["ontology_ids"] = [*changed["ontology_ids"], "co.software.substituted"]
        changed["inventory_digest"] = object_digest("ontology_inventory", changed, "inventory_digest")
        request["expected_concept_inventory"] = changed
        request["expected_concept_inventory_digest"] = changed["inventory_digest"]
        request["request_digest"] = object_digest("custody_readiness_verification_request", request, "request_digest")
        self.assert_kind("digest_mismatch", lambda: verify_graph(objects))
        _bundle, _support, objects = self.actual_graph(7)
        objects["execution_contamination_subject"]["source_digest"] = ZERO
        objects["execution_contamination_subject"]["subject_digest"] = object_digest("execution_contamination_subject", objects["execution_contamination_subject"], "subject_digest")
        self.assert_kind("digest_mismatch", lambda: verify_graph(objects))



    def test_raw_execution_receipt_is_an_explicit_byte_preimage(self):
        result = verify_graph({"raw_execution_receipt": b"synthetic raw receipt"})
        self.assertTrue(result.consistency_verified)
        self.assertFalse(result.authority_verified)
        self.assert_kind("schema_invalid", lambda: verify_graph({"raw_execution_receipt": {}}))

    def test_opaque_request_and_unknown_role_reject(self):
        _bundle, _support, objects = self.actual_graph(7)
        del objects["custody_readiness_request"]
        self.assert_kind("opaque_caller_request", lambda: verify_graph(objects))
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
