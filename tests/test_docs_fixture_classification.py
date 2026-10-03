from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from scripts.decision98_b0_support import tree_digest


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tests/fixtures/decision98-b0/corpus"


class DocsFixtureClassificationTests(unittest.TestCase):
    def test_classifications_bind_only_the_ten_frozen_markdown_inputs(self) -> None:
        manifest = json.loads((ROOT / ".docs-list-fixtures.json").read_text("utf-8"))
        self.assertEqual(manifest["schema_version"], 1)
        expected_paths = sorted(p.relative_to(ROOT).as_posix() for p in CORPUS.rglob("*.md"))
        self.assertEqual(len(expected_paths), 10)
        entries = manifest["fixtures"]
        self.assertEqual(sorted(entry["path"] for entry in entries), expected_paths)
        for entry in entries:
            with self.subTest(path=entry["path"]):
                self.assertEqual(set(entry), {"path", "sha256", "reason"})
                self.assertEqual(
                    entry["sha256"], hashlib.sha256((ROOT / entry["path"]).read_bytes()).hexdigest()
                )
                self.assertIn("Immutable Decision 98 B0", entry["reason"])

    def test_corpus_and_preregistered_sources_still_match_recorded_evidence(self) -> None:
        lock = json.loads((ROOT / "tests/fixtures/decision98-b0/preregistration-lock.json").read_text("utf-8"))
        report = json.loads((ROOT / "docs/project/decision98-b0-semantic-relevance-report.json").read_text("utf-8"))
        digest = tree_digest(CORPUS)
        self.assertEqual(digest, "021278da7cb1fe4ecb86857ae2510c934fe53172c952a7b1c05885c4f6d88d40")
        self.assertEqual(digest, lock["source"]["corpus"]["tree_sha256"])
        self.assertEqual(digest, report["corpus_sha256"])
        for source in lock["source"].values():
            if "sha256" in source:
                with self.subTest(path=source["path"]):
                    self.assertEqual(
                        hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest(), source["sha256"]
                    )


if __name__ == "__main__":
    unittest.main()
