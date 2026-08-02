from __future__ import annotations

import unittest

from rocs_cli.semantic_adopted_digests import object_digest
from rocs_cli.semantic_adopted_graph import (
    ISSUE_KINDS, AdoptedGraphError, GraphEdge, ROLE_SPECS, normative_edges,
    verify_graph,
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
        "policy_concept_ids_digest": ZERO,
        "joint_route_sets_digest": ZERO,
        "receipt_digest": ZERO,
    }
    value["receipt_digest"] = object_digest("policy_binding_receipt", value, "receipt_digest")
    return value


class AdoptedGraphTests(unittest.TestCase):
    def assert_kind(self, kind, function):
        with self.assertRaises(AdoptedGraphError) as caught:
            function()
        self.assertEqual(caught.exception.kind, kind)
        self.assertIn(kind, ISSUE_KINDS)

    def test_static_topology_is_acyclic_and_phase_ordered(self):
        self.assertGreater(len(ROLE_SPECS), 25)
        self.assertGreater(len(normative_edges()), 60)
        for edge in normative_edges():
            self.assertNotEqual(edge.source, edge.target)
            self.assertLess(ROLE_SPECS[edge.target].phase, ROLE_SPECS[edge.source].phase)

    def test_isolated_preimage_proves_consistency_not_authority(self):
        result = verify_graph({"inventory": inventory()})
        self.assertTrue(result.consistency_verified)
        self.assertFalse(result.authority_verified)
        self.assertEqual(result.roles_verified, ("inventory",))

    def test_required_digest_join_uses_supplied_preimage(self):
        inv = inventory()
        receipt = binding_receipt(inv["inventory_digest"])
        result = verify_graph({"inventory": inv, "binding_receipt": receipt})
        self.assertTrue(result.consistency_verified)
        receipt["inventory_digest"] = ZERO
        receipt["receipt_digest"] = object_digest("policy_binding_receipt", receipt, "receipt_digest")
        self.assert_kind("digest_mismatch", lambda: verify_graph({"inventory": inv, "binding_receipt": receipt}))

    def test_exact_self_digest_is_required(self):
        value = inventory()
        value["ontology_ids"] = ["co.software.changed"]
        self.assert_kind("digest_mismatch", lambda: verify_graph({"inventory": value}))

    def test_schema_invalidity_is_closed(self):
        value = inventory()
        value["unexpected"] = "not leaked"
        self.assert_kind("schema_invalid", lambda: verify_graph({"inventory": value}))

    def test_unknown_extra_role_rejects(self):
        self.assert_kind("unknown_role", lambda: verify_graph({"inventory": inventory(), "invented": {}}))

    def test_missing_preimage_rejects_before_digest_use(self):
        candidate = {"schema": ROLE_SPECS["candidate"].schema}
        self.assert_kind("missing_preimage", lambda: verify_graph({"candidate": candidate}))

    def test_opaque_caller_request_digest_rejects(self):
        preregistration = {"schema": ROLE_SPECS["preregistration"].schema}
        objects = {role: {"schema": ROLE_SPECS[role].schema} for role in (
            "candidate", "attempt_envelope", "custody_readiness", "execution_contamination",
            "execution_contamination_request", "preexecution_bundle", "preregistration",
        )}
        objects["preregistration"] = preregistration
        # The custody request preimage is intentionally absent. Other missing
        # ancestors do not hide this direct opaque-request failure.
        self.assert_kind("opaque_caller_request", lambda: verify_graph(objects))

    def test_caller_cannot_replace_static_edges(self):
        self.assert_kind(
            "self_edge",
            lambda: verify_graph({"inventory": inventory()}, edges=[GraphEdge("inventory", "inventory_digest", "inventory")]),
        )
        self.assert_kind(
            "phase_forward_edge",
            lambda: verify_graph(
                {"inventory": inventory(), "channel": acquisition_channel()},
                edges=[GraphEdge("inventory", "inventory_digest", "channel")],
            ),
        )
        self.assert_kind(
            "back_edge",
            lambda: verify_graph(
                {"reservation": {}, "rollback_plan": {}},
                edges=[GraphEdge("reservation", "reservation_digest", "rollback_plan")],
            ),
        )

    def test_safe_error_contains_no_object_value(self):
        value = inventory()
        value["unexpected"] = "sensitive-synthetic-value"
        with self.assertRaises(AdoptedGraphError) as caught:
            verify_graph({"inventory": value})
        self.assertNotIn("sensitive", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
