#!/usr/bin/env python3
"""Generate fresh public-only synthetic Ed25519 vectors for Decision 103 S1."""
from __future__ import annotations

import base64
import hashlib
import json
import pathlib
import subprocess
import sys
from datetime import datetime, timezone

import cryptography
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from rocs_cli.semantic_adopted_digests import domain_digest
from rocs_cli.semantic_adopted_schema import load_protocol_schema
from rocs_cli.semantic_adopted_signatures import SIGNATURE_PREFIXES

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/semantic-adopted-policy-v1"
VECTORS = FIXTURES / "cryptographic-vectors.json"
PROVENANCE = FIXTURES / "fixture-provenance.json"
GENERATOR = ROOT / "tests/generate_semantic_adopted_fixtures.py"


def b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def raw_private(key: Ed25519PrivateKey) -> bytes:
    return key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )


def digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


SMALL_ORDER_PUBLIC_KEYS = (
    bytes(32),
    b"\x00" * 31 + b"\x80",
    b"\x01" + b"\x00" * 31,
    bytes.fromhex("26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc05"),
    bytes.fromhex("26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc85"),
    bytes.fromhex("c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac037a"),
    bytes.fromhex("c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac03fa"),
    bytes.fromhex("ecffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f"),
)


def main() -> None:
    body = {
        "schema": "synthetic-adopted-policy-signature-body.v1",
        "case_id": "conspicuously-synthetic-ed25519-vector",
        "authority": "synthetic.test.invalid",
    }
    body_digest = domain_digest("approval_attestation_body", body)
    private_key = Ed25519PrivateKey.generate()
    wrong_private_key = Ed25519PrivateKey.generate()
    public_raw = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw,
    )
    wrong_public_raw = wrong_private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw,
    )
    issuer = {"principal_id": "synthetic-signer", "authority_role": "synthetic_test"}
    trust_root = "sha256:" + "1" * 64
    common = {
        "body_digest": body_digest,
        "public_key_base64": b64(public_raw),
        "expected_public_key_digest": digest(public_raw),
        "issuer": issuer,
        "expected_issuer": issuer,
        "trust_root_digest": trust_root,
        "expected_trust_root_digest": trust_root,
        "valid_from": "2026-01-01T00:00:00Z",
        "valid_until": "2027-01-01T00:00:00Z",
        "trusted_now": "2026-08-02T06:00:00Z",
        "revoked": False,
    }
    vectors = []
    for purpose, prefix in SIGNATURE_PREFIXES.items():
        signature = private_key.sign(prefix + bytes.fromhex(body_digest.removeprefix("sha256:")))
        vectors.append({
            **common, "name": f"{purpose}_valid", "purpose": purpose,
            "expected_purpose": purpose, "signature_base64": b64(signature), "valid": True,
        })
    approval = vectors[0]
    approval_signature = base64.b64decode(approval["signature_base64"])
    wrong_signature = wrong_private_key.sign(
        SIGNATURE_PREFIXES["approval"] + bytes.fromhex(body_digest.removeprefix("sha256:"))
    )
    vectors.extend([
        {**approval, "name": "changed_domain_rejected", "body_digest": domain_digest("candidate", body), "valid": False},
        {**approval, "name": "changed_body_rejected", "body_digest": "sha256:" + "f" * 64, "valid": False},
        {**approval, "name": "wrong_key_rejected", "public_key_base64": b64(wrong_public_raw), "valid": False},
        {
            **approval, "name": "coordinated_key_and_signature_substitution_rejected",
            "public_key_base64": b64(wrong_public_raw), "signature_base64": b64(wrong_signature), "valid": False,
        },
        {**approval, "name": "wrong_signature_length_rejected", "signature_base64": b64(approval_signature[:-1]), "valid": False},
        {**approval, "name": "changed_signature_rejected", "signature_base64": b64(approval_signature[:-1] + bytes([approval_signature[-1] ^ 1])), "valid": False},
        {**approval, "name": "noncanonical_scalar_rejected", "signature_base64": b64(approval_signature[:32] + b"\xff" * 32), "valid": False},
        {**approval, "name": "purpose_pin_rejected", "expected_purpose": "receipt", "valid": False},
        {**approval, "name": "issuer_pin_rejected", "expected_issuer": {**issuer, "principal_id": "other"}, "valid": False},
        {**approval, "name": "trust_root_pin_rejected", "expected_trust_root_digest": "sha256:" + "2" * 64, "valid": False},
        {**approval, "name": "revoked_rejected", "revoked": True, "valid": False},
        {**approval, "name": "expired_rejected", "valid_until": "2026-01-02T00:00:00Z", "valid": False},
        {**approval, "name": "abbreviated_timestamp_rejected", "valid_from": "2026-01-01Z", "valid": False},
        {**approval, "name": "missing_seconds_timestamp_rejected", "valid_from": "2026-01-01T00:00Z", "valid": False},
        {**approval, "name": "offset_timestamp_rejected", "valid_from": "2026-01-01T00:00:00+00:00", "valid": False},
        {**approval, "name": "lowercase_zone_timestamp_rejected", "valid_from": "2026-01-01T00:00:00z", "valid": False},
        {**approval, "name": "invalid_calendar_timestamp_rejected", "valid_from": "2026-02-29T00:00:00Z", "valid": False},
        {**approval, "name": "invalid_leap_second_timestamp_rejected", "valid_from": "2026-01-01T00:00:60Z", "valid": False},
    ])
    identity_forgery = b"\x01" + b"\x00" * 63
    vectors.extend({
        **approval,
        "name": f"small_order_key_{index}_rejected",
        "public_key_base64": b64(raw),
        "expected_public_key_digest": digest(raw),
        "signature_base64": b64(identity_forgery),
        "valid": False,
    } for index, raw in enumerate(SMALL_ORDER_PUBLIC_KEYS))
    payload = {
        "schema": "semantic-adopted-policy-cryptographic-vectors.v1",
        "synthetic": True,
        "body": body,
        "body_digest": body_digest,
        "body_domain": "approval_attestation_body",
        "public_key_digest": digest(public_raw),
        "vectors": vectors,
    }
    VECTORS.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", "utf-8")
    vector_bytes = VECTORS.read_bytes()
    schema = load_protocol_schema()["$defs"]["contaminationManifest"]["properties"]
    b0_fields = ("b0_preregistration_commit", "b0_failure_commit", "b0_preregistration_lock_digest", "b0_prompt_set_digest", "b0_report_digest")
    b0_coordinates = [schema[field]["const"] for field in b0_fields]
    private_patterns = []
    for material in (raw_private(private_key), raw_private(wrong_private_key)):
        private_patterns.extend((material, material.hex().encode("ascii"), base64.b64encode(material)))
    if any(pattern in vector_bytes for pattern in private_patterns):
        raise RuntimeError("private fixture material escaped into public vectors")
    if any(coordinate.encode("ascii") in vector_bytes for coordinate in b0_coordinates):
        raise RuntimeError("Decision 98 B0 coordinate escaped into synthetic vectors")
    generator_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
    ).stdout.strip()
    provenance = {
        "schema": "semantic-adopted-policy-fixture-provenance.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "generator_path": "tests/generate_semantic_adopted_fixtures.py",
        "generator_commit": generator_commit,
        "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
        "python_version": sys.version.split()[0],
        "cryptography_version": cryptography.__version__,
        "entropy_source": "operating-system-randomness",
        "fixture_sha256": hashlib.sha256(vector_bytes).hexdigest(),
        "conspicuously_synthetic": True,
        "b0_scan_algorithm": "exact-five-coordinate-byte-deny-v1",
        "b0_coordinate_set_sha256": hashlib.sha256("\n".join(sorted(b0_coordinates)).encode()).hexdigest(),
        "b0_coordinate_hits": [],
        "private_material_scan": "raw-hex-base64-v1:pass",
        "private_key_serialized": False,
        "secret_material_serialized": False,
        "dependency_review": {
            "package": "cryptography",
            "version": cryptography.__version__,
            "license_expression": "Apache-2.0 OR BSD-3-Clause",
            "transitive_licenses": {"cffi": "MIT-0", "pycparser": "BSD-3-Clause"},
            "scope": "offline-caller-pinned-ed25519-verify-only",
            "network_calls": False,
            "signing_api_exposed_by_rocs": False,
            "independent_node_parity_required": True,
            "lock_sha256": hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest(),
        },
    }
    PROVENANCE.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", "utf-8")
    del private_key, wrong_private_key, private_patterns


if __name__ == "__main__":
    main()
