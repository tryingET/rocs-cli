"""Caller-pinned Ed25519 verification primitives for Decision 103."""
from __future__ import annotations

import base64
import binascii
import hashlib
import re
from decimal import Decimal
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
_DATE_TIME = re.compile(
    r"^(?P<year>[0-9]{4})-(?P<month>0[1-9]|1[0-2])-(?P<day>0[1-9]|[12][0-9]|3[01])"
    r"T(?P<hour>[01][0-9]|2[0-3]):(?P<minute>[0-5][0-9]):(?P<second>[0-5][0-9]|60)"
    r"(?:\.(?P<fraction>[0-9]+))?Z$"
)
# The eight canonical encodings of the Ed25519 small-order subgroup.
_SMALL_ORDER_PUBLIC_KEYS = frozenset({
    bytes(32),
    b"\x00" * 31 + b"\x80",
    b"\x01" + b"\x00" * 31,
    bytes.fromhex("26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc05"),
    bytes.fromhex("26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc85"),
    bytes.fromhex("c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac037a"),
    bytes.fromhex("c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac03fa"),
    bytes.fromhex("ecffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f"),
})


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
    if public_key in _SMALL_ORDER_PUBLIC_KEYS:
        raise AdoptedSignatureError("Ed25519 public key has small order")
    signature = decode_canonical_base64(signature_base64, expected_bytes=64)
    message = signature_message(purpose, body_digest)
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, message)
    except (InvalidSignature, ValueError) as exc:
        raise AdoptedSignatureError("Ed25519 signature verification failed") from exc


def _timestamp(value: str) -> tuple[int, int, int, int, int, int, Decimal]:
    match = _DATE_TIME.fullmatch(value) if type(value) is str and len(value) <= 65_536 else None
    if match is None:
        raise AdoptedSignatureError("signature validity time is malformed")
    year, month, day, hour, minute, second = (
        int(match.group(name)) for name in ("year", "month", "day", "hour", "minute", "second")
    )
    leap_year = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    month_days = (31, 29 if leap_year else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    if day > month_days[month - 1] or (second == 60 and not (hour == 23 and minute == 59 and (month, day) in {(6, 30), (12, 31)})):
        raise AdoptedSignatureError("signature validity time is malformed")
    fraction = match.group("fraction")
    return year, month, day, hour, minute, second, Decimal(f"0.{fraction}" if fraction else "0")


def verify_pinned_ed25519(
    *, purpose: str, expected_purpose: str, body_digest: str,
    public_key_base64: str, expected_public_key_digest: str, signature_base64: str,
    issuer: Mapping[str, object], expected_issuer: Mapping[str, object],
    trust_root_digest: str, expected_trust_root_digest: str,
    valid_from: str, valid_until: str, trusted_now: str, revoked: bool,
) -> None:
    if (
        purpose != expected_purpose
        or public_key_digest(public_key_base64) != expected_public_key_digest
        or dict(issuer) != dict(expected_issuer)
        or trust_root_digest != expected_trust_root_digest
        or type(revoked) is not bool
        or revoked
    ):
        raise AdoptedSignatureError("signature authority pins do not match")
    digest_bytes(expected_public_key_digest)
    digest_bytes(trust_root_digest)
    if not _timestamp(valid_from) <= _timestamp(trusted_now) <= _timestamp(valid_until):
        raise AdoptedSignatureError("signature credential is outside its validity interval")
    verify_ed25519(
        purpose=purpose, body_digest=body_digest,
        public_key_base64=public_key_base64, signature_base64=signature_base64,
    )
