#!/usr/bin/env python3
"""Generate fresh public-only synthetic Ed25519 vectors for Decision 103 S1."""
from __future__ import annotations

import base64
import hashlib
import json
import pathlib
from datetime import datetime, timezone

import cryptography
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from rocs_cli.semantic_adopted_digests import domain_digest
from rocs_cli.semantic_adopted_signatures import SIGNATURE_PREFIXES

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/semantic-adopted-policy-v1"
VECTORS = FIXTURES / "cryptographic-vectors.json"
PROVENANCE = FIXTURES / "fixture-provenance.json"
GENERATOR = ROOT / "tests/generate_semantic_adopted_fixtures.py"


def b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def main() -> None:
    body = {
        "schema": "synthetic-adopted-policy-signature-body.v1",
        "case_id": "conspicuously-synthetic-ed25519-vector",
        "authority": "synthetic.test.invalid",
    }
    body_digest = domain_digest("approval_attestation_body", body)
    private_key = Ed25519PrivateKey.generate()
    public_raw = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    public_b64 = b64(public_raw)
    vectors = []
    for purpose, prefix in SIGNATURE_PREFIXES.items():
        signature = private_key.sign(prefix + bytes.fromhex(body_digest.removeprefix("sha256:")))
        vectors.append({
            "name": f"{purpose}_valid",
            "purpose": purpose,
            "body_digest": body_digest,
            "public_key_base64": public_b64,
            "signature_base64": b64(signature),
            "valid": True,
        })
    approval_signature = base64.b64decode(vectors[0]["signature_base64"])
    vectors.extend([
        {
            **vectors[0], "name": "changed_body_rejected",
            "body_digest": "sha256:" + "f" * 64, "valid": False,
        },
        {
            **vectors[0], "name": "changed_signature_rejected",
            "signature_base64": b64(approval_signature[:-1] + bytes([approval_signature[-1] ^ 1])),
            "valid": False,
        },
        {
            **vectors[0], "name": "noncanonical_scalar_rejected",
            "signature_base64": b64(approval_signature[:32] + b"\xff" * 32),
            "valid": False,
        },
        {
            **vectors[0], "name": "small_order_key_rejected",
            "public_key_base64": b64(b"\0" * 32), "valid": False,
        },
    ])
    payload = {
        "schema": "semantic-adopted-policy-cryptographic-vectors.v1",
        "synthetic": True,
        "body": body,
        "body_digest": body_digest,
        "public_key_digest": "sha256:" + hashlib.sha256(public_raw).hexdigest(),
        "vectors": vectors,
    }
    VECTORS.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", "utf-8")
    vector_bytes = VECTORS.read_bytes()
    provenance = {
        "schema": "semantic-adopted-policy-fixture-provenance.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "generator_path": "tests/generate_semantic_adopted_fixtures.py",
        "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
        "cryptography_version": cryptography.__version__,
        "entropy_source": "operating-system-randomness",
        "fixture_sha256": hashlib.sha256(vector_bytes).hexdigest(),
        "conspicuously_synthetic": True,
        "decision98_b0_material_present": False,
        "private_key_serialized": False,
        "secret_material_serialized": False,
    }
    PROVENANCE.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", "utf-8")
    del private_key


if __name__ == "__main__":
    main()
