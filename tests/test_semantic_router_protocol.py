from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from rocs_cli.semantic_protocol import ProtocolError, object_digest as discovery_digest
from rocs_cli.semantic_router_invariants import evaluate_policy, validate_bundle, validate_invariants
from rocs_cli.semantic_router_protocol import (
    MAX_POLICY_BYTES,
    MAX_REQUEST_BYTES,
    RouteProtocolError,
    alternative_tokens,
    caller_request_identity,
    error_envelope,
    jcs_bytes,
    load_protocol_schema,
    match_clause,
    match_group,
    object_digest,
    parse_bounded_json,
    parse_policy_bytes,
    parse_provenance_bytes,
    parse_request_bytes,
    route_capabilities,
    route_tokens,
    strict_json_loads,
    validate_definition,
    validate_protocol,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "docs" / "project" / "semantic-router-v0"


def _json(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text("utf-8"))


class SemanticRouterProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.golden = _json("golden-fixtures.json")
        cls.differential = _json("differential-fixtures.json")
        cls.valid = cls.golden["valid"]
        cls.corpus_kinds = {"synthetic.Alpha": "concept", "synthetic.Beta": "concept"}

    def test_embedded_schema_is_exact_and_registry_is_offline(self) -> None:
        self.assertEqual(load_protocol_schema(), _json("protocol.schema.json"))
        schema = load_protocol_schema()
        ref = schema["$defs"]["routeResult"]["properties"]["discovery_result"]["$ref"]
        self.assertEqual(ref, "https://ai-society.local/rocs/semantic-discovery-v0/protocol.schema.json#/$defs/result")
        schema["$defs"]["routeResult"]["properties"]["discovery_result"]["$ref"] = "https://remote.invalid/schema"
        from rocs_cli import semantic_router_protocol as protocol
        with patch.object(protocol, "SCHEMA_JSON", json.dumps(schema)), self.assertRaises(RouteProtocolError) as caught:
            protocol.load_protocol_schema()
        self.assertEqual(caught.exception.kind, "incompatible")

    def test_all_golden_route_objects_validate_and_bundle_closes(self) -> None:
        for name in ("request", "policy", "provenance", "effective_execution", "result", "error", "capabilities"):
            with self.subTest(name=name):
                self.assertEqual(validate_protocol(self.valid[name]), [])
        self.assertEqual(validate_definition(self.valid["result"]["discovery_result"], "routeResult")[0:0], [])
        self.assertEqual(validate_bundle(
            request=self.valid["request"], policy=self.valid["policy"],
            provenance=self.valid["provenance"], effective_execution=self.valid["effective_execution"],
            result=self.valid["result"], discovery_effective_execution=self.valid["discovery_effective_execution"],
            corpus_kinds=self.corpus_kinds,
        ), [])

    def test_five_route_digest_domains_and_jcs_preimages_are_exact(self) -> None:
        kinds = {
            "routing_policy": "policy", "provenance_manifest": "provenance",
            "caller_request": "request", "effective_execution": "effective_execution", "result": "result",
        }
        expected_names = {
            "routing_policy": "routing_policy_digest", "provenance_manifest": "provenance_manifest_digest",
            "caller_request": "caller_request_digest", "effective_execution": "effective_execution_digest",
            "result": "result_digest",
        }
        for kind, fixture_name in kinds.items():
            with self.subTest(kind=kind):
                value = self.valid[fixture_name]
                self.assertEqual(object_digest(kind, value), self.golden["digests"][expected_names[kind]])
                preimage = deepcopy(value)
                field = {
                    "routing_policy": "routing_policy_digest", "provenance_manifest": "provenance_manifest_digest",
                    "effective_execution": "effective_execution_digest", "result": "result_digest",
                }.get(kind)
                if field:
                    preimage.pop(field)
                committed = self.differential["canonical_preimages"][kind]
                self.assertEqual(jcs_bytes(preimage).hex(), committed["jcs_utf8_hex"])
                self.assertEqual(len(jcs_bytes(preimage)), committed["byte_length"])
        self.assertEqual(jcs_bytes({"\ue000": 1, "\U00010000": 2}), '{"𐀀":2,"":1}'.encode())
        with self.assertRaises(ProtocolError):
            object_digest("discovery_result", {})

    def test_strict_parser_matrix_and_digest_boundary(self) -> None:
        for case in self.differential["parser_cases"]:
            raw = bytes.fromhex(case["raw_utf8_hex"])
            with self.subTest(case=case["case"]), self.assertRaises(RouteProtocolError) as caught:
                parse_request_bytes(raw)
            self.assertEqual(caught.exception.kind, case["expected_kind"])
            self.assertEqual(caller_request_identity(raw), (None, None))
        for raw in (b'{"n":NaN}', b'{"n":Infinity}', b'{"n":01}', b'{"s":"\\ud800"}'):
            with self.subTest(raw=raw), self.assertRaises(RouteProtocolError) as caught:
                parse_request_bytes(raw)
            self.assertEqual(caught.exception.kind, "invalid_request")
        for integer in (-9_007_199_254_740_991, 9_007_199_254_740_991):
            self.assertEqual(strict_json_loads(f'{{"n":{integer}}}'.encode())["n"], integer)
        raw = jcs_bytes(self.valid["request"])
        value, digest = caller_request_identity(raw)
        self.assertEqual(value, self.valid["request"])
        self.assertEqual(digest, self.golden["digests"]["caller_request_digest"])
        malformed_schema = b'{"schema":"unknown"}'
        value, digest = caller_request_identity(malformed_schema)
        self.assertEqual(value, {"schema": "unknown"})
        self.assertIsNotNone(digest)

    def test_parser_absolute_byte_depth_item_and_query_byte_limits(self) -> None:
        raw = jcs_bytes(self.valid["request"])
        exact = raw + b" " * (MAX_REQUEST_BYTES - len(raw))
        self.assertEqual(parse_request_bytes(exact), self.valid["request"])
        with self.assertRaises(RouteProtocolError) as caught:
            parse_request_bytes(exact + b" ")
        self.assertEqual(caught.exception.kind, "invalid_request")
        deep = ("[" * 33 + "0" + "]" * 33).encode()
        with self.assertRaises(RouteProtocolError) as caught:
            parse_bounded_json(deep, byte_limit=1000, malformed_kind="invalid_request", oversize_kind="invalid_request")
        self.assertEqual(caught.exception.kind, "resource_exhausted")
        many = ("[" + ",".join("0" for _ in range(20_001)) + "]").encode()
        with self.assertRaises(RouteProtocolError) as caught:
            parse_bounded_json(many, byte_limit=len(many), malformed_kind="invalid_request", oversize_kind="invalid_request")
        self.assertEqual(caught.exception.kind, "resource_exhausted")
        too_large_policy = b" " * (MAX_POLICY_BYTES + 1)
        with self.assertRaises(RouteProtocolError) as caught:
            parse_policy_bytes(too_large_policy)
        self.assertEqual(caught.exception.kind, "resource_exhausted")
        request = deepcopy(self.valid["request"])
        request["query"] = "ä" * 8193
        request["discovery_limits"]["query_bytes"] = 16384
        self.assertIn("query UTF-8 byte limit", validate_invariants(request))

    def test_route_tokenizer_preserves_sequence_and_witnesses_are_canonical(self) -> None:
        for case in self.differential["tokenization"]:
            with self.subTest(raw=case["raw"]):
                self.assertEqual(route_tokens(case["raw"]), case["expected"])
        group = {"group_id": "g", "any_of": [
            {"kind": "token", "value": "alpha"}, {"kind": "phrase", "value": "alpha beta"},
        ]}
        self.assertEqual(match_group(route_tokens("alpha beta alpha"), group), {
            "group_id": "g", "kind": "token", "value": "alpha", "start_token": 0, "end_token": 1,
        })
        clause = {"clause_id": "c", "all_of": [
            {"group_id": "b", "any_of": [{"kind": "token", "value": "beta"}]},
            {"group_id": "a", "any_of": [{"kind": "token", "value": "alpha"}]},
        ]}
        self.assertEqual([item["group_id"] for item in match_clause(["alpha", "beta"], clause)], ["a", "b"])
        for alternative in (
            {"kind": "token", "value": "Alpha"}, {"kind": "token", "value": "alpha beta"},
            {"kind": "phrase", "value": "alpha"}, {"kind": "phrase", "value": "alpha  beta"},
        ):
            with self.subTest(alternative=alternative), self.assertRaises(ProtocolError):
                alternative_tokens(alternative)

    def _policy_for(self, case: str) -> tuple[dict, str]:
        policy = deepcopy(self.valid["policy"])
        query = "synthetic alpha bridge synthetic beta"
        token = lambda value: {"kind": "token", "value": value}
        clause = lambda cid, gid, value: {"clause_id": cid, "all_of": [{"group_id": gid, "any_of": [token(value)]}]}
        if case == "no_policy_domain_support":
            query = "alpha beta"
        elif case == "explicit_domain_exclusion":
            policy["domain"]["admit_any"] = [clause("d.other", "g.other", "jurisdiction")]
            policy["domain"]["exclude_any"] = [clause("d.exclude", "g.exclude", "synthetic")]
        elif case == "domain_support_exclusion_conflict":
            policy["domain"]["exclude_any"] = [clause("d.exclude", "g.exclude", "synthetic")]
        elif case == "single_supported_concept":
            query = "synthetic alpha"
        elif case == "no_concept_support":
            query = "synthetic"
        elif case == "concept_support_exclusion_conflict":
            policy["concepts"][0]["exclude_any"] = [clause("c.alpha-x", "g.alpha-x", "alpha")]
        elif case == "multiple_supported_without_joint_route":
            policy["joint_routes"] = []
        elif case == "joint_route_exclusion":
            policy["joint_routes"][0]["exclude_any"] = [clause("j.exclusion", "g.joint-x", "bridge")]
        return policy, query

    def test_complete_admission_and_routing_matrix(self) -> None:
        expected = {
            "no_policy_domain_support": ("abstained", "no_policy_domain_support", "not_evaluated", "admission_abstained"),
            "explicit_domain_exclusion": ("abstained", "explicit_domain_exclusion", "not_evaluated", "admission_abstained"),
            "domain_support_exclusion_conflict": ("abstained", "domain_support_exclusion_conflict", "not_evaluated", "admission_abstained"),
            "single_supported_concept": ("admitted", "domain_support", "single", "single_supported_concept"),
            "no_concept_support": ("admitted", "domain_support", "abstained", "no_concept_support"),
            "concept_support_exclusion_conflict": ("admitted", "domain_support", "abstained", "concept_support_exclusion_conflict"),
            "multiple_supported_without_joint_route": ("admitted", "domain_support", "ambiguous", "multiple_supported_without_joint_route"),
            "joint_route_exclusion": ("admitted", "domain_support", "abstained", "joint_route_exclusion"),
            "explicit_joint_route": ("admitted", "domain_support", "multi", "explicit_joint_route"),
        }
        self.assertEqual(set(expected), set(self.differential["state_cases"]))
        for case, states in expected.items():
            policy, query = self._policy_for(case)
            value = evaluate_policy(policy, query, self.valid["request"]["route_limits"])
            with self.subTest(case=case):
                self.assertEqual((value.admission["state"], value.admission["reason"], value.routing["state"], value.routing["reason"]), states)
                if value.admission["state"] == "abstained":
                    self.assertTrue(all(item["scope"] == "domain" for item in value.evidence))

    def test_ordering_provenance_and_evidence_mutations_fail_closed(self) -> None:
        policy = deepcopy(self.valid["policy"])
        policy["concepts"].reverse()
        policy["routing_policy_digest"] = object_digest("routing_policy", policy)
        self.assertIn("concept order or uniqueness", validate_invariants(policy))

        provenance = deepcopy(self.valid["provenance"])
        provenance["records"] = provenance["records"][:-1]
        provenance["provenance_manifest_digest"] = object_digest("provenance_manifest", provenance)
        self.assertIn("provenance alternative bijection", validate_invariants(provenance, policy=self.valid["policy"]))

        result = deepcopy(self.valid["result"])
        result["evidence"][0]["witnesses"][0]["start_token"] += 1
        result["result_digest"] = object_digest("result", result)
        failures = validate_invariants(
            result, request=self.valid["request"], policy=self.valid["policy"],
            provenance=self.valid["provenance"], effective_execution=self.valid["effective_execution"],
        )
        self.assertIn("evidence schedule or witness binding", failures)

        policy = deepcopy(self.valid["policy"])
        policy["authority"]["path"] = "fixtures/./policy.json"
        policy["routing_policy_digest"] = object_digest("routing_policy", policy)
        self.assertIn("canonical policy authority path", validate_invariants(policy))

    def test_nested_discovery_and_lineage_mutations_fail_closed(self) -> None:
        result = deepcopy(self.valid["result"])
        result["discovery_result"]["extra"] = True
        result["result_digest"] = object_digest("result", result)
        issues = validate_protocol(result)
        self.assertTrue(any(issue.keyword == "additionalProperties" for issue in issues))

        result = deepcopy(self.valid["result"])
        result["discovery_result"]["caller_request_digest"] = "sha256:" + "0" * 64
        result["discovery_result"]["result_digest"] = discovery_digest("result", result["discovery_result"])
        result["result_digest"] = object_digest("result", result)
        failures = validate_invariants(result, request=self.valid["request"], policy=self.valid["policy"], effective_execution=self.valid["effective_execution"])
        self.assertIn("nested discovery caller request binding", failures)

    def test_digest_bindings_and_standalone_state_matrices_fail_closed(self) -> None:
        request = deepcopy(self.valid["request"])
        request["expected_routing_policy_digest"] = "sha256:" + "0" * 64
        failures = validate_invariants(request, policy=self.valid["policy"], provenance=self.valid["provenance"])
        self.assertIn("expected routing policy digest binding", failures)

        policy = deepcopy(self.valid["policy"])
        policy["provenance_manifest_digest"] = "sha256:" + "0" * 64
        policy["routing_policy_digest"] = object_digest("routing_policy", policy)
        failures = validate_invariants(policy, provenance=self.valid["provenance"])
        self.assertIn("policy provenance manifest digest binding", failures)

        result = deepcopy(self.valid["result"])
        result["admission"] = {
            "state": "admitted", "reason": "no_policy_domain_support",
            "support_clause_ids": [], "exclusion_clause_ids": [],
        }
        result["routing"] = {
            "state": "single", "reason": "explicit_joint_route", "selected_ont_ids": [],
            "supported_ont_ids": [], "conflicted_ont_ids": [], "joint_route_id": None,
        }
        result["evidence"] = []
        result["result_digest"] = object_digest("result", result)
        failures = validate_invariants(result)
        self.assertIn("admission internal matrix", failures)
        self.assertIn("routing state reason matrix", failures)
        self.assertIn("single selection cardinality", failures)

        result = deepcopy(self.valid["result"])
        result["routing"] = {
            "state": "abstained", "reason": "no_concept_support", "selected_ont_ids": [],
            "supported_ont_ids": ["synthetic.Alpha"], "conflicted_ont_ids": [], "joint_route_id": None,
        }
        result["evidence"] = []
        result["result_digest"] = object_digest("result", result)
        self.assertIn("no concept support cardinality", validate_invariants(result))

        policy = deepcopy(self.valid["policy"])
        policy["domain"]["admit_any"].append({
            "clause_id": "a.first", "all_of": [{"group_id": "g.first", "any_of": [{"kind": "token", "value": "first"}]}],
        })
        policy["routing_policy_digest"] = object_digest("routing_policy", policy)
        self.assertIn("clause order or identity uniqueness", validate_invariants(policy))

        effective = deepcopy(self.valid["effective_execution"])
        effective["tool_identity"]["digest"] = "sha256:" + "0" * 64
        effective["effective_execution_digest"] = object_digest("effective_execution", effective)
        self.assertIn("tool identity digest", validate_invariants(effective))

        malformed_nested = {
            "effective_execution_digest": self.valid["discovery_effective_execution"]["effective_execution_digest"],
            "malformed": True,
        }
        failures = validate_bundle(
            request=self.valid["request"], policy=self.valid["policy"], provenance=self.valid["provenance"],
            effective_execution=self.valid["effective_execution"], result=self.valid["result"],
            discovery_effective_execution=malformed_nested,
        )
        self.assertTrue(any(item.startswith("nested discovery effective execution:schema:") for item in failures))

        nested = deepcopy(self.valid["discovery_effective_execution"])
        nested["caller_request_digest"] = "sha256:" + "0" * 64
        nested["effective_execution_digest"] = discovery_digest("effective_execution", nested)
        effective = deepcopy(self.valid["effective_execution"])
        effective["nested_discovery_effective_execution_digest"] = nested["effective_execution_digest"]
        effective["effective_execution_digest"] = object_digest("effective_execution", effective)
        failures = validate_invariants(effective, request=self.valid["request"], discovery_effective_execution=nested)
        self.assertIn("nested discovery effective execution caller_request_digest binding", failures)

    def test_request_supplied_policy_and_provenance_parser_limits_apply(self) -> None:
        policy_raw = jcs_bytes(self.valid["policy"])
        provenance_raw = jcs_bytes(self.valid["provenance"])
        with self.assertRaises(RouteProtocolError) as caught:
            parse_policy_bytes(policy_raw, byte_limit=len(policy_raw) - 1)
        self.assertEqual(caught.exception.kind, "resource_exhausted")
        with self.assertRaises(RouteProtocolError) as caught:
            parse_provenance_bytes(provenance_raw, collection_items=1)
        self.assertEqual(caught.exception.kind, "resource_exhausted")
        request = deepcopy(self.valid["request"])
        request["route_limits"]["policy_bytes"] = 1
        failures = validate_bundle(
            request=request, policy=self.valid["policy"], provenance=self.valid["provenance"],
            effective_execution=self.valid["effective_execution"], result=self.valid["result"],
        )
        self.assertIn("policy byte limit", failures)

    def test_date_time_paths_and_parser_signature_dimensions_are_closed(self) -> None:
        provenance = deepcopy(self.valid["provenance"])
        provenance["records"][0]["created_at"] = "definitely-not-rfc3339"
        issues = validate_protocol(provenance)
        self.assertTrue(any(issue.keyword == "format" for issue in issues))
        policy = deepcopy(self.valid["policy"])
        policy["authority"]["path"] += "\n"
        issues = validate_protocol(policy)
        self.assertTrue(any(issue.keyword == "pattern" for issue in issues))

        from tests.verify_semantic_router_compatibility import assert_base_signature_preserved
        base = {"actions": [{"type": "builtins.int", "help": "old"}], "children": {}, "subparser": None, "mutex": [], "settings": {"allow_abbrev": False}}
        changed_type = deepcopy(base); changed_type["actions"][0]["type"] = "builtins.str"
        with self.assertRaises(AssertionError):
            assert_base_signature_preserved(base, changed_type)
        changed_abbrev = deepcopy(base); changed_abbrev["settings"]["allow_abbrev"] = True
        with self.assertRaises(AssertionError):
            assert_base_signature_preserved(base, changed_abbrev)
        changed_help = deepcopy(base); changed_help["actions"][0]["help"] = "new"
        with self.assertRaises(AssertionError):
            assert_base_signature_preserved(base, changed_help)

    def test_safe_errors_and_capabilities_are_closed_and_exact(self) -> None:
        for kind in ("invalid_request", "invalid_policy", "resource_exhausted", "incompatible", "internal"):
            envelope = error_envelope(kind)
            self.assertEqual(validate_invariants(envelope), [])
            self.assertNotIn("/", envelope["error"]["message"])
        unknown = error_envelope("not-a-kind")
        self.assertEqual(unknown["error"]["kind"], "internal")
        self.assertEqual(validate_invariants(route_capabilities()), [])


if __name__ == "__main__":
    unittest.main()
