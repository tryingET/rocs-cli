"""Caller-pinned Ed25519 verification primitives for Decision 103."""
from __future__ import annotations

import base64
import binascii
import hashlib
import re
from datetime import datetime
from types import MappingProxyType
from typing import Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

SIGNATURE_PREFIXES: Mapping[str, bytes] = MappingProxyType({
    "approval": b"rocs-semantic-policy-approval-signature-v1\0",
    "receipt": b"rocs-semantic-policy-receipt-signature-v1\0",
    "consumption": b"rocs-semantic-policy-consumption-signature-v1\0",
})
_DIGEST = re.compile(r"^sha256:([0-9a-f]{64})$")


class AdoptedSignatureError(ValueError):
    """Malformed key, signature, body digest, or unsupported signature purpose."""


def decode_canonical_base64(value: str, *, expected_bytes: int) -> bytes:
    if type(value) is not str or type(expected_bytes) is not int or expected_bytes < 0:
        raise AdoptedSignatureError("base64 input contract is invalid")
    try:
        raw = base64.b64decode(value.encode("ascii"), validate=True)
    except (UnicodeEncodeError, binascii.Error, ValueError) as exc:
        raise AdoptedSignatureError("base64 value is malformed") from exc
    if len(raw) != expected_bytes or base64.b64encode(raw).decode("ascii") != value:
        raise AdoptedSignatureError("base64 value is non-canonical or has the wrong length")
    return raw


def digest_bytes(value: str) -> bytes:
    match = _DIGEST.fullmatch(value) if type(value) is str else None
    if match is None:
        raise AdoptedSignatureError("body digest is malformed")
    return bytes.fromhex(match.group(1))


def public_key_digest(public_key_base64: str) -> str:
    raw = decode_canonical_base64(public_key_base64, expected_bytes=32)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def signature_message(purpose: str, body_digest: str) -> bytes:
    if purpose not in SIGNATURE_PREFIXES:
        raise AdoptedSignatureError("signature purpose is unsupported")
    return SIGNATURE_PREFIXES[purpose] + digest_bytes(body_digest)


def verify_ed25519(
    *, purpose: str, body_digest: str, public_key_base64: str, signature_base64: str,
) -> None:
    public_key = decode_canonical_base64(public_key_base64, expected_bytes=32)
    signature = decode_canonical_base64(signature_base64, expected_bytes=64)
    message = signature_message(purpose, body_digest)
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, message)
    except (InvalidSignature, ValueError) as exc:
        raise AdoptedSignatureError("Ed25519 signature verification failed") from exc


def _timestamp(value: str) -> datetime:
    if type(value) is not str or not value.endswith("Z"):
        raise AdoptedSignatureError("signature validity time is malformed")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise AdoptedSignatureError("signature validity time is malformed") from exc


def verify_pinned_ed25519(
    *, purpose: str, expected_purpose: str, body_digest: str,
    public_key_base64: str, signature_base64: str,
    issuer: Mapping[str, object], expected_issuer: Mapping[str, object],
    trust_root_digest: str, expected_trust_root_digest: str,
    valid_from: str, valid_until: str, trusted_now: str, revoked: bool,
) -> None:
    if (
        purpose != expected_purpose
        or dict(issuer) != dict(expected_issuer)
        or trust_root_digest != expected_trust_root_digest
        or type(revoked) is not bool
        or revoked
    ):
        raise AdoptedSignatureError("signature authority pins do not match")
    digest_bytes(trust_root_digest)
    if not _timestamp(valid_from) <= _timestamp(trusted_now) <= _timestamp(valid_until):
        raise AdoptedSignatureError("signature credential is outside its validity interval")
    verify_ed25519(
        purpose=purpose, body_digest=body_digest,
        public_key_base64=public_key_base64, signature_base64=signature_base64,
    )
