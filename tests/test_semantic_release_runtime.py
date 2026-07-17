from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from rocs_cli.semantic_release_protocol import (
    EXPECTED_PROTOCOL_TYPES,
    LIVE_ACQUISITION_IMPLEMENTED,
    MAX_INPUT_BYTES,
    PROTOCOL_ID,
    RUNTIME_CAPABILITIES,
    SemanticReleaseProtocolError,
    SemanticReleaseProtocolRuntime,
    computed_object_digest,
    domain_digest,
    jcs_bytes,
    load_protocol_schema,
    schema_definitions,
    strict_json_loads,
    validate_object,
    validate_protocol,
)
from rocs_cli.semantic_release_conformance import verify_golden_corpus
from rocs_cli.semantic_release_models import (
    CheckedAcquisitionObject, CheckedCoordinate, CheckedReleaseObject, CheckedRollbackObject,
)
from rocs_cli.semantic_release_schema import SCHEMA_BYTE_LENGTH, SCHEMA_SHA256, schema_bytes

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs" / "project" / "semantic-release-v0"


class SemanticReleaseRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.golden = json.loads((PACKET / "golden-fixtures.json").read_text(encoding="utf-8"))
        cls.normative_schema = (PACKET / "protocol.schema.json").read_bytes()

    def test_embedded_schema_is_exact_normative_snapshot(self) -> None:
        self.assertEqual(schema_bytes(), self.normative_schema)
        self.assertEqual(SCHEMA_BYTE_LENGTH, len(self.normative_schema))
        self.assertEqual(SCHEMA_SHA256, hashlib.sha256(self.normative_schema).hexdigest())
        self.assertEqual(len(schema_definitions()), EXPECTED_PROTOCOL_TYPES)
        self.assertEqual(len(load_protocol_schema()["oneOf"]), EXPECTED_PROTOCOL_TYPES)

    def test_schema_loader_returns_defensive_copy(self) -> None:
        first = load_protocol_schema()
        first["$id"] = "mutated"
        first["$defs"].clear()
        second = load_protocol_schema()
        self.assertEqual(second["$id"], PROTOCOL_ID)
        self.assertEqual(len(second["oneOf"]), EXPECTED_PROTOCOL_TYPES)
        self.assertGreater(len(second["$defs"]), EXPECTED_PROTOCOL_TYPES)
        with self.assertRaises(TypeError):
            schema_definitions()["future"] = "future"  # type: ignore[index]

    def test_all_golden_objects_validate_and_recompute(self) -> None:
        self.assertEqual(len(self.golden["records"]), 122)
        self.assertEqual(verify_golden_corpus(self.golden), ())
        for record in self.golden["records"]:
            with self.subTest(record=record["name"]):
                validated = validate_object(record["instance"])
                self.assertEqual(validated.computed_digest, record["digest"])
                self.assertEqual(validated.canonical_bytes.decode(), record["canonical_preimage"] if record["omitted_field"] is None else jcs_bytes(record["instance"]).decode())

    def test_raw_preimages_use_registered_closed_domains(self) -> None:
        for record in self.golden["raw_preimages"]:
            with self.subTest(record=record["name"]):
                self.assertEqual(
                    domain_digest(record["domain"], record["preimage_utf8"].encode()),
                    record["digest"],
                )
        with self.assertRaisesRegex(SemanticReleaseProtocolError, "unsupported"):
            domain_digest("semantic-release.caller-controlled.v0", b"x")

    def test_checked_snapshot_is_immutable_and_returns_fresh_values(self) -> None:
        instance = self.golden["records"][0]["instance"]
        validated = validate_object(instance)
        first = validated.to_value()
        first["schema"] = "mutated"
        self.assertEqual(validated.to_value(), instance)
        with self.assertRaises((AttributeError, TypeError)):
            validated.schema = "mutated"  # type: ignore[misc]
        malformed = CheckedReleaseObject("x", "x", b"[]", "sha256:" + "0" * 64)
        with self.assertRaisesRegex(ValueError, "not an object"):
            malformed.to_value()

    def test_runtime_is_validation_only_and_default_off(self) -> None:
        runtime = SemanticReleaseProtocolRuntime()
        record = self.golden["records"][0]["instance"]
        result = runtime.validate_bytes(jcs_bytes(record))
        self.assertEqual(result.schema, record["schema"])
        self.assertFalse(LIVE_ACQUISITION_IMPLEMENTED)
        self.assertFalse(runtime.live_acquisition_implemented)
        self.assertEqual(runtime.capabilities, RUNTIME_CAPABILITIES)
        for forbidden in (
            "acquire", "publish", "withdraw", "revoke", "materialize", "activate",
            "deliver", "rollback", "execute", "run", "spawn",
        ):
            self.assertFalse(hasattr(runtime, forbidden), forbidden)

    def test_typed_checked_models_cover_authority_families(self) -> None:
        by_schema = {record["instance"]["schema"]: record["instance"] for record in self.golden["records"]}
        self.assertIsInstance(validate_object(by_schema["semantic-release-coordinate.v0"]), CheckedCoordinate)
        self.assertIsInstance(
            validate_object(by_schema["semantic-authority-acquisition-config.v0"]),
            CheckedAcquisitionObject,
        )
        self.assertIsInstance(validate_object(by_schema["semantic-rollback-receipt.v0"]), CheckedRollbackObject)

    def test_strict_json_rejects_ambiguous_or_non_ijson_bytes(self) -> None:
        rejected = (
            b'{"x":1,"x":2}',
            b'{"x":1.0}',
            b'{"x":-0}',
            b'{"x":-1}',
            b'{"x":9007199254740992}',
            b'{"x":NaN}',
            b'"\\ud800"',
            '"é"'.encode(),
            b'"\\ufdd0"',
            b'\xff',
        )
        for raw in rejected:
            with self.subTest(raw=raw), self.assertRaises(SemanticReleaseProtocolError):
                strict_json_loads(raw)
        with self.assertRaisesRegex(SemanticReleaseProtocolError, "byte limit"):
            strict_json_loads(b" " * (MAX_INPUT_BYTES + 1))

    def test_strict_json_rejects_excessive_depth(self) -> None:
        with self.assertRaisesRegex(SemanticReleaseProtocolError, "nesting limit"):
            strict_json_loads(("[" * 65 + "0" + "]" * 65).encode())

    def test_jcs_uses_utf16_key_order_and_integer_profile(self) -> None:
        value = {"\ufffd": 2, "\U0001f600": 1, "a": [True, None, 0]}
        self.assertEqual(jcs_bytes(value), '{"a":[true,null,0],"😀":1,"�":2}'.encode())
        with self.assertRaises(SemanticReleaseProtocolError):
            jcs_bytes({"x": 1.5})

    def test_closed_schema_rejects_unknown_missing_and_wrong_typed_fields(self) -> None:
        coordinate = copy.deepcopy(next(
            record["instance"] for record in self.golden["records"]
            if record["instance"]["schema"] == "semantic-release-coordinate.v0"
        ))
        coordinate["unexpected"] = True
        self.assertIn("additionalProperties", {issue.keyword for issue in validate_protocol(coordinate)})
        coordinate.pop("unexpected")
        coordinate.pop("namespace")
        self.assertIn("required", {issue.keyword for issue in validate_protocol(coordinate)})
        coordinate["namespace"] = "ai-society.core"
        coordinate["semantic_version"] = True
        self.assertIn("type", {issue.keyword for issue in validate_protocol(coordinate)})

    def test_unknown_discriminator_and_non_object_fail_closed(self) -> None:
        issues = validate_protocol({"schema": "semantic-release-future.v9"})
        self.assertEqual(issues[0].instance_path, "/schema")
        self.assertEqual(validate_protocol([])[0].keyword, "type")

    def test_digest_mismatch_and_missing_digest_fail_closed(self) -> None:
        record = copy.deepcopy(self.golden["records"][0]["instance"])
        field = self.golden["records"][0]["omitted_field"]
        record[field] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(SemanticReleaseProtocolError, "digest mismatch"):
            validate_object(record)
        record.pop(field)
        with self.assertRaises(SemanticReleaseProtocolError):
            computed_object_digest(record)

    def test_nested_digest_mismatch_survives_recomputed_outer_digest(self) -> None:
        record = copy.deepcopy(next(
            item["instance"] for item in self.golden["records"]
            if item["name"] == "authority_acquisition_config"
        ))
        record["pins"][0]["capability_pin_digest"] = "sha256:" + "0" * 64
        record["authority_acquisition_config_digest"] = computed_object_digest(record)
        with self.assertRaisesRegex(SemanticReleaseProtocolError, "digest mismatch"):
            validate_object(record)

    def test_derived_action_change_and_freshness_digests_fail_closed(self) -> None:
        approval = copy.deepcopy(next(
            item["instance"] for item in self.golden["records"] if item["name"] == "owner_approval"
        ))
        approval["action_digest"] = "sha256:" + "0" * 64
        approval["owner_approval_digest"] = computed_object_digest(approval)
        with self.assertRaisesRegex(SemanticReleaseProtocolError, "derived action"):
            validate_object(approval)

        override = copy.deepcopy(next(
            item["instance"] for item in self.golden["records"] if item["name"] == "compatibility_override"
        ))
        override["change_digest"] = "sha256:" + "0" * 64
        override["compatibility_override_digest"] = computed_object_digest(override)
        with self.assertRaisesRegex(SemanticReleaseProtocolError, "derived compatibility"):
            validate_object(override)

        snapshot = copy.deepcopy(next(
            item["instance"] for item in self.golden["records"] if item["name"] == "authority_snapshot"
        ))
        receipt = snapshot["store_read_receipts"][0]
        receipt["freshness_cas_token_digest"] = "sha256:" + "0" * 64
        receipt["owner_store_read_receipt_digest"] = computed_object_digest(receipt)
        snapshot["authority_snapshot_digest"] = computed_object_digest(snapshot)
        with self.assertRaisesRegex(SemanticReleaseProtocolError, "derived freshness"):
            validate_object(snapshot)

    def test_chain_assertion_mutation_is_detected(self) -> None:
        corpus = copy.deepcopy(self.golden)
        corpus["chain_assertions"][0]["instance_path"] = "/owner_policy_digest"
        failures = verify_golden_corpus(corpus)
        self.assertTrue(any(failure.startswith("chain[0]:") for failure in failures), failures)

    def test_special_oneof_protocol_types_dispatch_exactly(self) -> None:
        special = {
            "semantic-publication-recovery-state-receipt.v0",
            "semantic-publication-status-transition.v0",
        }
        records = [record for record in self.golden["records"] if record["instance"]["schema"] in special]
        self.assertGreaterEqual(len(records), 2)
        for record in records:
            with self.subTest(record=record["name"]):
                self.assertEqual(validate_protocol(record["instance"]), ())
                self.assertIn(record["instance"]["schema"], schema_definitions())


if __name__ == "__main__":
    unittest.main()
