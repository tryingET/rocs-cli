from __future__ import annotations

import hashlib
import json
import pathlib
import unittest

import cryptography

from rocs_cli.semantic_adopted_signatures import (
    AdoptedSignatureError, decode_canonical_base64, digest_bytes,
    public_key_digest, signature_message, verify_ed25519,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/semantic-adopted-policy-v1"
VECTORS = FIXTURES / "cryptographic-vectors.json"
PROVENANCE = FIXTURES / "fixture-provenance.json"
GENERATOR = ROOT / "tests/generate_semantic_adopted_fixtures.py"


class AdoptedSignatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(VECTORS.read_text())
        cls.provenance = json.loads(PROVENANCE.read_text())

    def test_public_vectors_match_expected_validity(self):
        for vector in self.payload["vectors"]:
            arguments = {
                "purpose": vector["purpose"],
                "body_digest": vector["body_digest"],
                "public_key_base64": vector["public_key_base64"],
                "signature_base64": vector["signature_base64"],
            }
            with self.subTest(vector=vector["name"]):
                if vector["valid"]:
                    verify_ed25519(**arguments)
                else:
                    with self.assertRaises(AdoptedSignatureError):
                        verify_ed25519(**arguments)

    def test_key_digest_and_signature_message_are_exact(self):
        valid = self.payload["vectors"][0]
        self.assertEqual(public_key_digest(valid["public_key_base64"]), self.payload["public_key_digest"])
        self.assertEqual(
            signature_message("approval", valid["body_digest"]),
            b"rocs-semantic-policy-approval-signature-v1\0" + digest_bytes(valid["body_digest"]),
        )

    def test_malformed_noncanonical_and_wrong_length_base64_reject(self):
        for value, length in (("!!!!", 32), ("AA==", 32), ("A" * 44, 32), ("é", 32)):
            with self.subTest(value=value):
                with self.assertRaises(AdoptedSignatureError):
                    decode_canonical_base64(value, expected_bytes=length)
        with self.assertRaises(AdoptedSignatureError):
            signature_message("unknown", "sha256:" + "0" * 64)
        with self.assertRaises(AdoptedSignatureError):
            digest_bytes("sha256:" + "A" * 64)

    def test_fixture_provenance_hashes_and_contains_no_private_material(self):
        self.assertEqual(self.provenance["cryptography_version"], cryptography.__version__)
        self.assertEqual(self.provenance["fixture_sha256"], hashlib.sha256(VECTORS.read_bytes()).hexdigest())
        self.assertEqual(self.provenance["generator_sha256"], hashlib.sha256(GENERATOR.read_bytes()).hexdigest())
        self.assertFalse(self.provenance["decision98_b0_material_present"])
        self.assertFalse(self.provenance["private_key_serialized"])
        self.assertFalse(self.provenance["secret_material_serialized"])
        public_files = VECTORS.read_bytes() + PROVENANCE.read_bytes()
        self.assertNotIn(b"BEGIN PRIVATE KEY", public_files)
        self.assertNotIn(b"private_key_base64", public_files)


if __name__ == "__main__":
    unittest.main()
