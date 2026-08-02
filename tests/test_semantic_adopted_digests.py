from __future__ import annotations

import hashlib
import pathlib
import re
import unittest

from rocs_cli.semantic_adopted_digests import (
    DOMAINS, AdoptedDigestError, domain_digest, object_digest, raw_domain_digest,
)
from rocs_cli.semantic_adopted_protocol import jcs_bytes

ROOT = pathlib.Path(__file__).resolve().parents[1]
INVARIANTS = ROOT / "docs/project/semantic-router-adopted-policy-v1/invariants.md"


class AdoptedDigestTests(unittest.TestCase):
    def test_all_sixty_one_domains_equal_the_normative_packet(self):
        expected = dict(re.findall(
            r'^([a-z0-9_]+)_digest = SHA256\("([^"]+)\\0" \|\| J\)$',
            INVARIANTS.read_text(), re.MULTILINE,
        ))
        self.assertEqual(len(expected), 61)
        self.assertEqual(dict(DOMAINS), expected)
        self.assertEqual(len(set(DOMAINS.values())), 61)

    def test_raw_and_jcs_digest_preimages_are_exact(self):
        value = {"z": 1, "a": "e\u0301"}
        payload = jcs_bytes(value)
        expected = "sha256:" + hashlib.sha256(
            DOMAINS["candidate"].encode("ascii") + b"\0" + payload
        ).hexdigest()
        self.assertEqual(domain_digest("candidate", value), expected)
        self.assertEqual(raw_domain_digest("candidate", payload), expected)

    def test_object_digest_omits_exactly_one_named_field(self):
        value = {"schema": "synthetic", "candidate_digest": "sha256:" + "0" * 64, "x": 1}
        self.assertEqual(
            object_digest("candidate", value, "candidate_digest"),
            domain_digest("candidate", {"schema": "synthetic", "x": 1}),
        )
        self.assertIn("candidate_digest", value)

    def test_unknown_domain_and_missing_omitted_field_reject(self):
        with self.assertRaises(AdoptedDigestError):
            raw_domain_digest("unknown", b"")
        with self.assertRaises(AdoptedDigestError):
            object_digest("candidate", {"x": 1}, "candidate_digest")


if __name__ == "__main__":
    unittest.main()
