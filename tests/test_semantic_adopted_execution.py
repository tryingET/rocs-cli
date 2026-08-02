from __future__ import annotations

import copy
import json
import pathlib
import subprocess
import unittest

from rocs_cli.semantic_adopted_execution import (
    ERROR_KINDS,
    execution_verification_bytes,
    execution_verification_result,
    verify_execution_projection,
)
from rocs_cli.semantic_adopted_protocol import jcs_bytes

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tests/fixtures/semantic-adopted-policy-v1/execution-corpus.json"
NODE = ROOT / "tests/verify_semantic_adopted_execution.mjs"
BRANCHES = (
    "not_started_no_proof", "not_started_proof_only", "not_started_launch_ready",
    "interrupted_before_handoff", "interrupted_after_handoff",
    "interrupted_receipt_zero_pass", "interrupted_primary", "completed_repeat",
)


class AdoptedExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = json.loads(CORPUS.read_text("utf-8"))

    def test_closed_inventory_and_every_corpus_projection(self):
        self.assertEqual(tuple(self.corpus["error_kinds"]), ERROR_KINDS)
        observed = set()
        for case in self.corpus["cases"]:
            with self.subTest(case=case["name"]):
                before = copy.deepcopy(case["projection"])
                actual = verify_execution_projection(case["projection"])
                self.assertEqual(actual, tuple(case["expected_error_kinds"]))
                self.assertEqual(case["projection"], before)
                self.assertTrue(set(actual) <= set(ERROR_KINDS))
                observed.update(actual)
        self.assertEqual(observed, set(ERROR_KINDS))

    def test_all_eight_attempt_verdict_prefixes_are_covered(self):
        by_name = {case["name"]: case for case in self.corpus["cases"]}
        self.assertEqual(len(BRANCHES), 8)
        for name in BRANCHES:
            self.assertIn(name, by_name)
            self.assertEqual(verify_execution_projection(by_name[name]["projection"]), ())

    def test_boundaries_ordering_single_process_no_retry_and_closure_are_adversarial(self):
        by_name = {case["name"]: case for case in self.corpus["cases"]}
        groups = {
            "history_boundary": ("base_over_254", "activated_not_successor", "terminal_over_256"),
            "reservation_process": ("no_reservation", "two_processes"),
            "custody_order": ("launch_before_channel", "handoff_before_launch", "receipt_same_time_as_handoff", "closure_before_receipt"),
            "retry_rerun_forbidden": ("retry_forbidden", "rerun_forbidden"),
            "closure_required": ("not_closed", "closure_missing"),
        }
        for kind, names in groups.items():
            for name in names:
                with self.subTest(kind=kind, case=name):
                    self.assertIn(kind, verify_execution_projection(by_name[name]["projection"]))
        maximum = by_name["completed_repeat"]["projection"]["history"]
        minimum = by_name["minimum_history_valid"]["projection"]["history"]
        self.assertEqual(maximum, {"base": 254, "activated": 255, "terminal": 256})
        self.assertEqual(minimum, {"base": 12, "activated": 13, "terminal": 14})

    def test_result_bytes_are_canonical_and_node_is_byte_identical(self):
        results = []
        for case in self.corpus["cases"]:
            result = execution_verification_result(case["projection"])
            self.assertEqual(execution_verification_bytes(case["projection"]), jcs_bytes(result))
            results.append(result)
        completed = subprocess.run(
            ["node", str(NODE)], cwd=ROOT, check=True, capture_output=True,
        )
        self.assertEqual(completed.stderr, b"")
        self.assertEqual(completed.stdout, jcs_bytes(results) + b"\n")


if __name__ == "__main__":
    unittest.main()
