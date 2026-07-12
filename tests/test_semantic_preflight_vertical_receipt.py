from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "artifacts" / "semantic-preflight" / "decision52-i7-receipt.json"
PROOF = ROOT / "tests" / "verify_semantic_preflight_vertical.mjs"
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")


class SemanticPreflightVerticalReceiptTests(unittest.TestCase):
    def test_development_only_isolated_vertical_receipt_is_closed(self) -> None:
        payload = json.loads(RECEIPT.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema"], "decision52-semantic-preflight-vertical-proof.v0")
        self.assertIs(payload["development_only"], True)
        self.assertIs(payload["adopted_runtime"], False)
        self.assertEqual(payload["automatic_modes"], ["tui"])
        self.assertEqual(
            payload["sanitized_environment"],
            {
                "inherited_pythonpath": False,
                "inherited_runner_override": False,
                "shell_invoked": False,
                "network_required": False,
                "sibling_runner_discovery": False,
            },
        )
        self.assertEqual(set(payload["implementation"]), {"rocs_cli", "pi_host", "pi_ontology_workflows"})
        for commit in payload["implementation"].values():
            self.assertRegex(commit, COMMIT)
        self.assertEqual(
            payload["implementation"],
            {
                "rocs_cli": "ddbfa70b29c5805c859d32abc3265278cc6ce0d2",
                "pi_host": "5be4473cc156eb03d0069cc6770f1b95ea9eac97",
                "pi_ontology_workflows": "5719669cf4476f5f33cc9ac082b2de3af6940dd2",
            },
        )
        self.assertEqual(payload["runtime"]["rocs_commit"], payload["implementation"]["rocs_cli"])
        self.assertRegex(payload["runtime"]["manifest_digest"], DIGEST)
        self.assertGreater(payload["runtime"]["file_count"], 0)
        self.assertEqual(payload["preflight"]["outcome"], "matched")
        self.assertEqual(payload["preflight"]["candidate_count"], 1)
        self.assertIs(payload["preflight"]["ontology_prose_in_system_role"], False)
        self.assertRegex(payload["preflight"]["prompt_block_digest"], DIGEST)
        self.assertRegex(payload["preflight"]["candidates_digest"], DIGEST)
        self.assertEqual(payload["pack"]["ont_id"], "core.Agent")
        self.assertIs(payload["pack"]["bound"], True)
        self.assertRegex(payload["pack"]["text_digest"], DIGEST)
        self.assertIs(payload["consumer_tree_unchanged"], True)
        self.assertIs(payload["managed_dist_absent"], True)
        self.assertTrue(PROOF.is_file())

    def test_proof_script_keeps_production_adoption_closed(self) -> None:
        source = PROOF.read_text(encoding="utf-8")
        self.assertIn('mode: "tui"', source)
        self.assertIn('adopted_runtime: false', source)
        self.assertIn('assert.equal(process.env.PYTHONPATH, undefined', source)
        self.assertNotIn("PI_ONTOLOGY_ROCS_BIN =", source)
        self.assertNotIn("ROCS_BIN =", source)


if __name__ == "__main__":
    unittest.main()
