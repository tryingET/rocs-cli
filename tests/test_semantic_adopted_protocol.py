from __future__ import annotations

import hashlib
import json
import pathlib
import unittest
import zlib

from rocs_cli.semantic_adopted_protocol import (
    AdoptedProtocolError,
    MAX_ORDINARY_BYTES,
    jcs_bytes,
    protocol_byte_limit,
    schema_definitions,
    strict_json_loads,
    validate_definition,
)
from rocs_cli.semantic_adopted_schema import (
    COMPRESSED_SHA256,
    SCHEMA_SHA256,
    load_protocol_schema,
    schema_bytes,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tests/fixtures/semantic-adopted-policy-v1/schema-corpus.json"
SCHEMA = ROOT / "docs/project/semantic-router-adopted-policy-v1/protocol.schema.json"
ASSET = ROOT / "src/rocs_cli/_bootstrap_assets/semantic-router-adopted-policy-v1.schema.zlib"


def _walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _validate_inline(instance, schema):
    from rocs_cli.semantic_adopted_protocol import _validate  # independent corpus probe

    root = load_protocol_schema()
    return tuple(_validate(instance, schema, root, ""))


def _branch_signature(branch):
    """Stable branch-shape projection used to detect oneOf overlap regressions."""
    properties = branch.get("properties", {})
    projected = {}
    for name in (
        "attempt_state", "process_invocations", "passes", "outcome",
        "evaluator_execution_start_proof_digest",
        "evaluator_execution_start_verification_request_digest",
        "evaluator_execution_launch_receipt_digest",
        "protected_descriptor_handoff_receipt_digest", "execution_receipt_digest",
        "process_spawned_at", "process_terminated_at", "descriptor_access_state",
        "execution_attempt", "protected_access_closure",
    ):
        if name in properties:
            projected[name] = properties[name]
    return jcs_bytes(projected)


class AdoptedSchemaAssetTests(unittest.TestCase):
    def test_asset_is_exact_deterministic_packet_compression(self):
        raw = SCHEMA.read_bytes()
        compressed = ASSET.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), SCHEMA_SHA256)
        self.assertEqual(hashlib.sha256(compressed).hexdigest(), COMPRESSED_SHA256)
        self.assertEqual(compressed, zlib.compress(raw, 9))
        self.assertEqual(schema_bytes(), raw)

    def test_schema_inventory_references_and_reachability(self):
        root = load_protocol_schema()
        self.assertEqual(len(root["$defs"]), 69)
        self.assertEqual(len(root["oneOf"]), 54)
        references = [node["$ref"] for node in _walk(root) if "$ref" in node]
        self.assertEqual(len(references), 1115)
        self.assertEqual(len(schema_definitions()), 54)
        graph = {name: set() for name in root["$defs"]}
        for name, definition in root["$defs"].items():
            for node in _walk(definition):
                ref = node.get("$ref")
                if isinstance(ref, str) and ref.startswith("#/$defs/"):
                    graph[name].add(ref.removeprefix("#/$defs/").split("/", 1)[0])
        reached = set()

        def visit(name):
            if name in reached:
                return
            reached.add(name)
            for target in graph[name]:
                visit(target)

        for branch in root["oneOf"]:
            visit(branch["$ref"].removeprefix("#/$defs/").split("/", 1)[0])
        self.assertEqual(set(root["$defs"]) - reached, {"hexDigest"})

    def test_branch_inventory_is_unique_at_each_projection_level(self):
        root = load_protocol_schema()
        expected = json.loads(CORPUS.read_text())["branch_inventory"]
        for definition, count in expected.items():
            branches = root["$defs"][definition]["oneOf"]
            self.assertEqual(len(branches), count)
            encoded = [jcs_bytes(branch) for branch in branches]
            self.assertEqual(len(encoded), len(set(encoded)), definition)
            signatures = [_branch_signature(branch) for branch in branches]
            self.assertEqual(len(signatures), len(set(signatures)), definition)


class AdoptedStrictJsonTests(unittest.TestCase):
    def test_duplicate_float_noncanonical_and_surrogate_rejected(self):
        bad = [
            b'{"a":1,"a":2}', b"1.0", b"-0", b"01", b'"\\ud800"',
        ]
        for raw in bad:
            with self.subTest(raw=raw):
                with self.assertRaises(AdoptedProtocolError):
                    strict_json_loads(raw)

    def test_safe_negative_integer_and_nfd_are_preserved(self):
        self.assertEqual(strict_json_loads(b"-1"), -1)
        nfd = "e\u0301"
        value = {"value": nfd, "other": "é"}
        parsed = strict_json_loads(json.dumps(value, ensure_ascii=False).encode())
        self.assertEqual(parsed["value"], nfd)
        self.assertNotEqual(parsed["value"], parsed["other"])
        self.assertIn(nfd.encode(), jcs_bytes(parsed))

    def test_jcs_uses_utf16_property_order(self):
        value = {"\U00010000": 1, "\ue000": 2}
        self.assertEqual(jcs_bytes(value), '{"𐀀":1,"":2}'.encode())

    def test_structural_and_byte_limits_precede_json_parse(self):
        with self.assertRaisesRegex(AdoptedProtocolError, "byte limit"):
            strict_json_loads(b" " * (MAX_ORDINARY_BYTES + 1))
        with self.assertRaisesRegex(AdoptedProtocolError, "structural limits"):
            strict_json_loads(("[" * 33 + "]" * 33).encode())

    def test_only_root_history_and_currentness_discriminators_raise_byte_limit(self):
        history = b'{"schema":"semantic-routing-policy-publication-history.v1"}'
        proof = b'{"schema":"semantic-routing-policy-currentness-proof.v1"}'
        candidate = b'{"schema":"semantic-routing-policy-candidate.v1"}'
        self.assertEqual(protocol_byte_limit(history), 16_777_216)
        self.assertEqual(protocol_byte_limit(proof), 33_554_432)
        self.assertEqual(protocol_byte_limit(candidate), MAX_ORDINARY_BYTES)
        with self.assertRaisesRegex(AdoptedProtocolError, "duplicate schema"):
            protocol_byte_limit(b'{"schema":"a","schema":"b"}')


class AdoptedSchemaCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = json.loads(CORPUS.read_text())

    def test_python_matches_every_corpus_expectation(self):
        for case in self.corpus["cases"]:
            with self.subTest(case=case["name"]):
                if "definition" in case:
                    issues = validate_definition(case["instance"], case["definition"])
                else:
                    issues = _validate_inline(case["instance"], case["inline_schema"])
                self.assertEqual(not issues, case["valid"], issues[:2])

    def test_date_time_calendar_and_z_pattern(self):
        self.assertFalse(validate_definition("2024-02-29T23:59:59Z", "dateTime"))
        self.assertTrue(validate_definition("2023-02-29T23:59:59Z", "dateTime"))
        self.assertTrue(validate_definition("2026-08-02T06:00:00+00:00", "dateTime"))

    def test_actual_schema_arbitrary_pointer_reference(self):
        root = load_protocol_schema()
        ref = root["$defs"]["accessHistory"]["properties"]["events"]["items"]["properties"]["role"]["$ref"]
        self.assertEqual(ref, "#/$defs/roleAssignment/properties/role")
        schema = {"$ref": ref}
        self.assertFalse(_validate_inline("custodian", schema))
        self.assertTrue(_validate_inline("not-a-role", schema))


if __name__ == "__main__":
    unittest.main()
