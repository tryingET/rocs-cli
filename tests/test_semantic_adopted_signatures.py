from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import tempfile
import unittest

import cryptography

from rocs_cli.semantic_adopted_digests import domain_digest
from rocs_cli.semantic_adopted_schema import load_protocol_schema
from rocs_cli.semantic_adopted_signatures import (
    AdoptedSignatureError, decode_canonical_base64, digest_bytes,
    public_key_digest, signature_message, verify_pinned_ed25519,
)
from rocs_cli.wave1 import _vendor_from_assets

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
                key: vector[key] for key in (
                    "purpose", "expected_purpose", "body_digest", "public_key_base64",
                    "expected_public_key_digest", "signature_base64", "issuer", "expected_issuer", "trust_root_digest",
                    "expected_trust_root_digest", "valid_from", "valid_until", "trusted_now", "revoked",
                )
            }
            with self.subTest(vector=vector["name"]):
                if vector["valid"]:
                    verify_pinned_ed25519(**arguments)
                else:
                    with self.assertRaises(AdoptedSignatureError):
                        verify_pinned_ed25519(**arguments)

    def test_key_digest_and_signature_message_are_exact(self):
        self.assertEqual(
            sum(vector["name"].startswith("small_order_key_") for vector in self.payload["vectors"]),
            8,
        )
        self.assertIn(
            "coordinated_key_and_signature_substitution_rejected",
            {vector["name"] for vector in self.payload["vectors"]},
        )
        valid = self.payload["vectors"][0]
        self.assertEqual(
            self.payload["body_digest"],
            domain_digest(self.payload["body_domain"], self.payload["body"]),
        )
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
        committed_generator = subprocess.run(
            ["git", "show", f'{self.provenance["generator_commit"]}:tests/generate_semantic_adopted_fixtures.py'],
            cwd=ROOT, check=True, stdout=subprocess.PIPE,
        ).stdout
        self.assertEqual(hashlib.sha256(committed_generator).hexdigest(), self.provenance["generator_sha256"])
        props = load_protocol_schema()["$defs"]["contaminationManifest"]["properties"]
        fields = ("b0_preregistration_commit", "b0_failure_commit", "b0_preregistration_lock_digest", "b0_prompt_set_digest", "b0_report_digest")
        coordinates = [props[field]["const"] for field in fields]
        self.assertEqual(
            self.provenance["b0_coordinate_set_sha256"],
            hashlib.sha256("\n".join(sorted(coordinates)).encode()).hexdigest(),
        )
        self.assertEqual(self.provenance["b0_coordinate_hits"], [])
        self.assertFalse(self.provenance["private_key_serialized"])
        self.assertFalse(self.provenance["secret_material_serialized"])
        self.assertEqual(self.provenance["private_material_scan"], "raw-hex-base64-v1:pass")
        dependency = self.provenance["dependency_review"]
        self.assertEqual(dependency["version"], "46.0.5")
        self.assertEqual(dependency["scope"], "offline-caller-pinned-ed25519-verify-only")
        self.assertFalse(dependency["network_calls"])
        self.assertFalse(dependency["signing_api_exposed_by_rocs"])
        self.assertEqual(dependency["lock_sha256"], hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest())
        public_files = VECTORS.read_bytes() + PROVENANCE.read_bytes()
        self.assertNotIn(b"BEGIN PRIVATE KEY", public_files)
        self.assertNotIn(b"private_key_base64", public_files)

    def test_self_contained_runtime_carries_dependency_license_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            target = pathlib.Path(directory) / "rocs"
            _vendor_from_assets(
                ROOT / "src/rocs_cli",
                ROOT / "src/rocs_cli/_bootstrap_assets/pyproject.toml",
                ROOT / "README.md",
                ROOT / "src/rocs_cli/_bootstrap_assets/uv.lock",
                target,
                effective="0.2.1",
            )
            licenses = {path.relative_to(target / "runtime").parts[0] for path in (target / "runtime").glob("*.dist-info/licenses/*")}
            self.assertTrue(any(name.startswith("cryptography-46.0.5") for name in licenses))
            self.assertTrue(any(name.startswith("cffi-2.1.0") for name in licenses))
            self.assertTrue(any(name.startswith("pycparser-3.0") for name in licenses))


if __name__ == "__main__":
    unittest.main()
