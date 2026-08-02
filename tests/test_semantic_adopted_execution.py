from __future__ import annotations

import copy
import json
import pathlib
import subprocess
import unittest

from rocs_cli.semantic_adopted_execution import (
    ERROR_KINDS, execution_verification_bytes, execution_verification_result,
    verify_execution_bundle,
)
from rocs_cli.semantic_adopted_protocol import jcs_bytes, validate_protocol

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tests/fixtures/semantic-adopted-policy-v1/execution-corpus.json"
NODE = ROOT / "tests/verify_semantic_adopted_execution.mjs"


def mutate(base, operations):
    value = copy.deepcopy(base)
    for operation in operations:
        current = value
        tokens = operation["path"].split("/")
        for token in tokens[:-1]:
            current = current[int(token)] if isinstance(current, list) else current[token]
        if operation["op"] != "set":
            raise AssertionError("closed mutation operation")
        current[tokens[-1]] = copy.deepcopy(operation["value"])
    return value


class ActualAdoptedExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = json.loads(CORPUS.read_text("utf-8"))
        cls.base = next(case["bundle"] for case in cls.corpus["cases"] if case["name"] == "branch_7_valid")

    def bundle(self, case):
        return case.get("bundle") or mutate(self.base, case["operations"])

    def test_corpus_contains_actual_schema_objects_and_closed_results(self):
        self.assertEqual(self.corpus["schema"], "semantic-adopted-execution-actual-corpus.v2")
        observed = set()
        for case in self.corpus["cases"]:
            with self.subTest(case=case["name"]):
                bundle = self.bundle(case)
                self.assertIn("semantic-routing-policy-execution-attempt.v1", jcs_bytes(bundle).decode())
                before = copy.deepcopy(bundle)
                actual = verify_execution_bundle(bundle)
                self.assertEqual(actual, tuple(case["expected_error_kinds"]))
                self.assertEqual(bundle, before)
                self.assertTrue(set(actual) <= set(ERROR_KINDS))
                observed.update(actual)
        self.assertTrue({"schema_invalid", "digest_mismatch", "signature_invalid", "history_invalid", "ordering_invalid"} <= observed)

    def test_all_eight_schema_branches_and_completed_fail_are_lawful(self):
        by_name = {case["name"]: case for case in self.corpus["cases"]}
        for index in range(8):
            bundle = by_name[f"branch_{index}_valid"]["bundle"]
            self.assertFalse(validate_protocol(bundle["attempt"]))
            self.assertFalse(validate_protocol(bundle["verdict"]))
            self.assertEqual(verify_execution_bundle(bundle), ())
        failed = by_name["completed_fail_valid"]["bundle"]
        self.assertEqual(failed["attempt"]["attempt_state"], "completed")
        self.assertEqual(failed["verdict"]["outcome"], "fail")
        self.assertEqual(verify_execution_bundle(failed), ())

    def test_exact_histories_and_adversarial_negatives(self):
        verdict = self.base["verdict"]
        lengths = (
            len(verdict["preregistration"]["access_history"]["events"]),
            len(verdict["protected_access_activation"]["activated_access_history"]["events"]),
            len(verdict["protected_access_closure"]["terminal_access_history"]["events"]),
        )
        self.assertEqual(lengths, (12, 13, 14))
        maximum = next(case["bundle"] for case in self.corpus["cases"] if case["name"] == "history_boundary_254_255_256_valid")["verdict"]
        self.assertEqual((len(maximum["preregistration"]["access_history"]["events"]), len(maximum["protected_access_activation"]["activated_access_history"]["events"]), len(maximum["protected_access_closure"]["terminal_access_history"]["events"])), (254, 255, 256))
        by_name = {case["name"]: case for case in self.corpus["cases"]}
        expected = {
            "wrong_signer": "signature_invalid", "direct_descriptor_transfer": "schema_invalid",
            "retry_forbidden": "schema_invalid", "rerun_forbidden": "schema_invalid",
            "retained_process": "schema_invalid", "fake_history": "history_invalid",
            "expired_handoff": "ordering_invalid", "b0_ten_not_plus_one": "contamination_invalid",
        }
        for name, kind in expected.items():
            self.assertIn(kind, verify_execution_bundle(self.bundle(by_name[name])))

    def test_node_independently_recomputes_byte_identical_results(self):
        results = [execution_verification_result(self.bundle(case)) for case in self.corpus["cases"]]
        for case, result in zip(self.corpus["cases"], results):
            self.assertEqual(execution_verification_bytes(self.bundle(case)), jcs_bytes(result))
        completed = subprocess.run(["node", str(NODE)], cwd=ROOT, check=True, capture_output=True)
        self.assertEqual(completed.stderr, b"")
        self.assertEqual(completed.stdout, jcs_bytes(results) + b"\n")


if __name__ == "__main__":
    unittest.main()
