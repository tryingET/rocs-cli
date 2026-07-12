from __future__ import annotations

import json
import os
import unittest
from copy import deepcopy
from unittest.mock import patch
from pathlib import Path

from rocs_cli.semantic_protocol import (
    DOMAINS,
    ProtocolError,
    caller_request_identity,
    document_digest,
    domain_digest,
    jcs_bytes,
    lexical_tokens,
    load_protocol_schema,
    normalize_lexical,
    object_digest,
    preimage_digest,
    project_evidence,
    query_limit_outcome,
    strict_json_loads,
    validate_definition,
    validate_invariants,
    validate_protocol,
    verify_fixture_digests,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "docs" / "project" / "semantic-discovery-v0"


def _json(name: str) -> dict:
    return json.loads((FIXTURE_ROOT / name).read_text("utf-8"))


def _pointer(root: object, pointer: str) -> object:
    value = root
    for raw in pointer.removeprefix("/").split("/") if pointer else []:
        key = raw.replace("~1", "/").replace("~0", "~")
        value = value[int(key)] if isinstance(value, list) else value[key]  # type: ignore[index]
    return value


class SemanticProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.golden = _json("golden-fixtures.json")
        cls.differential = _json("differential-fixtures.json")

    def test_packaged_schema_is_exact_offline_copy_of_normative_schema(self) -> None:
        source = _json("protocol.schema.json")
        self.assertEqual(load_protocol_schema(), source)
        self.assertTrue(source["$id"].startswith("https://ai-society.local/"))

    def test_every_golden_object_validates_and_every_digest_reproduces(self) -> None:
        definitions = {"tool_identity": "toolIdentity"}
        for name, instance in self.golden["valid"].items():
            with self.subTest(name=name):
                issues = validate_definition(instance, definitions[name]) if name in definitions else validate_protocol(instance)
                self.assertEqual(issues, [])
                self.assertEqual(validate_invariants(instance, definitions.get(name)), [])
        self.assertEqual(verify_fixture_digests(self.golden), [])

    def test_every_committed_jcs_preimage_is_byte_identical(self) -> None:
        valid = self.golden["valid"]
        sources = {
            "caller_request": valid["request"],
            "corpus_snapshot": {k: v for k, v in valid["corpus_snapshot"].items() if k != "corpus_snapshot_digest"},
            "tool_identity": {k: v for k, v in valid["tool_identity"].items() if k != "digest"},
            "effective_execution": {k: v for k, v in valid["effective_execution"].items() if k != "effective_execution_digest"},
            "result": {k: v for k, v in valid["result"].items() if k != "result_digest"},
            "pack": {k: v for k, v in valid["pack"].items() if k != "pack_digest"},
        }
        for name, fixture in self.differential["canonical_preimages"].items():
            with self.subTest(name=name):
                actual = jcs_bytes(sources[name])
                self.assertEqual(actual.hex(), fixture["jcs_utf8_hex"])
                self.assertEqual(len(actual), fixture["byte_length"])

    def test_schema_invalid_fixtures_reject_at_portable_tuple(self) -> None:
        for fixture in self.differential["schema_invalid"]:
            instance = _pointer(self.golden, fixture["fixture_ref"].split("#", 1)[1])
            issues = validate_protocol(instance)
            tuples = {(issue.instance_path, issue.keyword) for issue in issues}
            with self.subTest(case=fixture["case"]):
                self.assertIn((fixture["expected_instance_path"], fixture["expected_keyword"]), tuples)
                expected_params = fixture.get("expected_params")
                if expected_params:
                    match = next(issue for issue in issues if (issue.instance_path, issue.keyword) == (fixture["expected_instance_path"], fixture["expected_keyword"]))
                    self.assertEqual(match.params, expected_params)

    def test_golden_schema_invalid_baseline_is_rejected(self) -> None:
        for fixture in self.golden["invalid"]:
            with self.subTest(case=fixture["case"]):
                self.assertNotEqual(validate_protocol(fixture["instance"]), [])

    def test_every_invariant_invalid_fixture_drives_its_declared_execution(self) -> None:
        def resolve(ref: str) -> object:
            self.assertTrue(ref.startswith("golden-fixtures.json#"))
            return deepcopy(_pointer(self.golden, ref.split("#", 1)[1]))

        def apply(target: object, operation: dict) -> None:
            path, _, leaf = operation["path"].rpartition("/")
            parent = _pointer(target, path)
            if operation["op"] == "reverse":
                _pointer(target, operation["path"]).reverse()
            elif operation["op"] == "append":
                _pointer(target, operation["path"]).append(operation["value"])
            elif isinstance(parent, list):
                parent[int(leaf)] = operation["value"]
            else:
                parent[leaf] = operation["value"]

        executed: set[str] = set()
        for fixture in self.differential["invariant_invalid"]:
            execution = fixture["execution"]
            executed.add(fixture["case"])
            with self.subTest(case=fixture["case"]):
                if execution["kind"] == "digest_preimage_reject":
                    with self.assertRaisesRegex(ProtocolError, fixture["expected_invariant"]):
                        preimage_digest(execution["digest_kind"], resolve(execution["base_ref"]))
                    continue
                if execution["kind"] == "validate_instance":
                    instance = deepcopy(fixture["instance"])
                    self.assertEqual(validate_protocol(instance), [])
                    self.assertEqual(object_digest("pack", instance), instance["pack_digest"])
                    self.assertIn(fixture["expected_invariant"], validate_invariants(instance))
                    continue
                instance = resolve(execution["base_ref"])
                request = resolve(execution["request_ref"]) if "request_ref" in execution else None
                eligible = resolve(execution["eligible_candidates_ref"]) if "eligible_candidates_ref" in execution else None
                targets = {"instance": instance, "request": request, "eligible_candidates": eligible}
                for operation in execution["operations"]:
                    apply(targets[operation["target"]], operation)
                failures = validate_invariants(instance, request=request, eligible_candidates=eligible)
                self.assertIn(fixture["expected_invariant"], failures)
        self.assertEqual(executed, {x["case"] for x in self.differential["invariant_invalid"]})

    def test_digest_omission_is_exact_and_non_circular(self) -> None:
        kind_by_case = {
            "result_digest_absent": "result",
            "pack_digest_absent": "pack",
            "tool_digest_absent": "tool_identity",
        }
        for fixture in self.differential["digest_omission"]:
            instance = _pointer(self.golden, fixture["fixture_ref"].split("#", 1)[1])
            expected = _pointer(self.golden, fixture["expected_digest_ref"].split("#", 1)[1])
            kind = kind_by_case[fixture["case"]]
            with self.subTest(case=fixture["case"]):
                self.assertEqual(object_digest(kind, instance), expected)
                self.assertNotEqual(object_digest(kind, instance, omit_digest=False), expected)

    def test_strict_json_error_hashing_boundary(self) -> None:
        for case in self.differential["error_hashing"]:
            raw = json.dumps(case["raw_json"], separators=(",", ":")).encode() if "raw_json" in case else bytes.fromhex(case["raw_utf8_hex"])
            value, digest = caller_request_identity(raw)
            with self.subTest(case=case["case"]):
                self.assertEqual(digest, case["expected_caller_request_digest"])
                if digest is None:
                    self.assertIsNone(value)
                else:
                    self.assertEqual(value, case["raw_json"])
        with self.assertRaises(ProtocolError):
            strict_json_loads(b'{"x":1,"x":2}')

    def test_integer_only_ijson_and_utf16_key_order(self) -> None:
        for raw in (b'{"n":1.0}', b'{"n":9007199254740992}', b'{"n":NaN}'):
            with self.subTest(raw=raw), self.assertRaises(ProtocolError):
                strict_json_loads(raw)
        value = {"\ue000": 1, "\U00010000": 2}
        # RFC 8785 orders object keys by UTF-16 code units, unlike code-point order.
        self.assertEqual(jcs_bytes(value), '{"𐀀":2,"":1}'.encode())

    def test_byte_boundaries_and_raw_document_domain(self) -> None:
        for fixture in self.differential["byte_boundaries"]:
            unit = bytes.fromhex(fixture["unit_utf8_hex"])
            raw = unit * fixture["repeat"]
            query = unit.decode("utf-8") * fixture["repeat"]
            with self.subTest(bytes=fixture["expected_utf8_bytes"]):
                self.assertEqual(len(raw), fixture["expected_utf8_bytes"])
                self.assertEqual(query_limit_outcome(query, 16384), fixture["expected"])
        document = self.golden["valid"]["pack"]["documents"][0]
        self.assertEqual(document_digest(document["text"].encode()), document["document_digest"])

    def test_normalization_order_projection_and_metamorphic_corpus(self) -> None:
        for fixture in self.differential["normalization"]:
            with self.subTest(case=fixture["raw"]):
                self.assertEqual(normalize_lexical(fixture["raw"]), fixture["expected_normalized"])
                self.assertEqual(lexical_tokens(fixture["raw"]), fixture["expected_tokens"])

        ordering = {case["case"]: case for case in self.differential["ordering_cases"]}
        candidates = sorted(ordering["candidate_total_order"]["input"], key=lambda x: (-x["score"], x["ont_id"].encode(), 0 if x["kind"] == "concept" else 1))
        self.assertEqual([f"{x['ont_id']}:{x['kind']}" for x in candidates], ordering["candidate_total_order"]["expected_order"])
        refs = sorted(ordering["resolved_ref_tie_break"]["input"], key=lambda x: (x["layer_order"], x["layer"].encode(), x["locator"].encode()))
        self.assertEqual([f"{x['layer']}:{x['locator']}" for x in refs], ordering["resolved_ref_tie_break"]["expected_order"])
        pack_case = ordering["pack_document_order"]
        root, *rest = pack_case["expected_order"]
        scrambled = pack_case["input"]
        actual = [root] + sorted((x for x in scrambled if x != root), key=lambda x: (0 if x.endswith(":concept") else 1, x.rsplit(":", 1)[0].encode()))
        self.assertEqual(actual, pack_case["expected_order"])

        metamorphic = {case["case"]: case for case in self.differential["metamorphic"]}
        enumeration = metamorphic["enumeration_permutation"]
        entries = {x["logical_path"]: x for x in self.golden["valid"]["corpus_snapshot"]["entries"]}
        snapshot = deepcopy(self.golden["valid"]["corpus_snapshot"])
        snapshot["entries"] = [entries[path] for path in enumeration["input_logical_paths"]]
        snapshot["entries"].sort(key=lambda x: (x["layer_order"], x["logical_path"].encode(), x["kind"]))
        self.assertEqual([x["logical_path"] for x in snapshot["entries"]], enumeration["expected_canonical_order"])
        self.assertEqual(object_digest("corpus_snapshot", snapshot), enumeration["expected_digest"])
        self.assertEqual(project_evidence(metamorphic["evidence_projection"]["input"]), metamorphic["evidence_projection"]["expected"])
        top_k = metamorphic["top_k_monotonicity"]
        ranked = [{"ont_id": ont_id, "score": len(top_k["full_order"]) - index} for index, ont_id in enumerate(reversed(list(reversed(top_k["full_order"]))))]
        ordered_ids = [x["ont_id"] for x in sorted(ranked, key=lambda x: -x["score"])]
        self.assertEqual([ordered_ids[:k] for k in top_k["k_values"]], top_k["expected_prefixes"])
        locale = metamorphic["locale_environment_invariance"]
        normalized: list[str] = []
        digests: list[str] = []
        for environment in locale["environments"]:
            with patch.dict(os.environ, environment, clear=True):
                normalized.append(normalize_lexical(locale["query"]))
                digests.append(object_digest("result", self.golden["valid"]["result"]))
        self.assertEqual(normalized, [locale["expected_normalized"]] * len(normalized))
        self.assertEqual(len(set(digests)), 1)
        drift = metamorphic["one_byte_identity_drift"]
        document_digests = [document_digest(bytes.fromhex(drift[key])) for key in ("raw_a_hex", "raw_b_hex")]
        snapshot_digests = []
        for digest in document_digests:
            changed = deepcopy(self.golden["valid"]["corpus_snapshot"])
            changed["entries"][1]["document_digest"] = digest
            snapshot_digests.append(object_digest("corpus_snapshot", changed))
        self.assertEqual(document_digests[0] == document_digests[1], drift["expected_document_digest_equal"])
        self.assertEqual(snapshot_digests[0] == snapshot_digests[1], drift["expected_corpus_snapshot_digest_equal"])
        equivalent = metamorphic["equivalent_canonical_requests"]
        reordered = dict(reversed(list(equivalent["request_b"].items())))
        self.assertEqual(jcs_bytes(equivalent["request_a"]), jcs_bytes(reordered))
        self.assertEqual(object_digest("caller_request", equivalent["request_a"]), object_digest("caller_request", reordered))
        self.assertEqual(set(metamorphic), {x["case"] for x in self.differential["metamorphic"]})

    def test_adversarial_cross_field_checks_fail_closed(self) -> None:
        valid = self.golden["valid"]
        result = deepcopy(valid["result"])
        result["candidates"][0]["matched_query_tokens"].append("extra")
        result["result_digest"] = object_digest("result", result)
        self.assertIn("matched query tokens exactly positive evidence", validate_invariants(result))

        result = deepcopy(valid["result"])
        result["effective_limits"]["candidates"] = 1
        second = deepcopy(result["candidates"][0])
        second.update(rank=2, ont_id="core.Other", score=100)
        result["candidates"].append(second)
        result["result_digest"] = object_digest("result", result)
        self.assertIn("candidate limit", validate_invariants(result))

        result = deepcopy(valid["result"])
        result["retrieval"] = "unique_candidate"
        result["candidates"] = []
        result["result_digest"] = object_digest("result", result)
        self.assertIn("nonempty retrieval cardinality", validate_invariants(result))

        request = deepcopy(valid["request"])
        request["query"] = "ä" * 8193
        self.assertIn("query UTF-8 byte limit", validate_invariants(request))

        result = deepcopy(valid["result"])
        result["result_digest"] = "sha256:" + "0" * 64
        self.assertIn("result digest", validate_invariants(result))

        result = deepcopy(valid["result"])
        result["candidates"][0]["score"] = 99
        result["result_digest"] = object_digest("result", result)
        self.assertIn("candidate eligibility threshold", validate_invariants(result))

        result = deepcopy(valid["result"])
        result["retrieval"] = "ambiguous_equivalence"
        result["result_digest"] = object_digest("result", result)
        self.assertIn("ambiguous equivalence cardinality", validate_invariants(result, eligible_count=1))

        result = deepcopy(valid["result"])
        result["candidates"][0]["evidence"].append({"field": "anti_example", "rule": "anti_token", "query_term": "Ä"})
        result["result_digest"] = object_digest("result", result)
        self.assertIn("canonical evidence query term", validate_invariants(result))

        pack_value = deepcopy(valid["pack"])
        pack_value["documents"][0]["logical_path"] = "reference/concepts/core.A\u0308gent.md"
        pack_value["pack_digest"] = object_digest("pack", pack_value)
        self.assertIn("pack logical path NFC", validate_invariants(pack_value))

    def test_unknown_digest_domain_and_nonlocal_schema_never_resolve(self) -> None:
        with self.assertRaises(ProtocolError):
            domain_digest("https://remote.invalid/schema", b"payload")
        self.assertEqual(set(DOMAINS), {"caller_request", "corpus_snapshot", "document", "tool_identity", "effective_execution", "result", "pack"})


if __name__ == "__main__":
    unittest.main()
