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
from rocs_cli.semantic_adopted_graph import (
    ExecutionGraphSupport, extract_execution_graph, verify_execution_graph,
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
        current[int(tokens[-1]) if isinstance(current, list) else tokens[-1]] = copy.deepcopy(operation["value"])
    return value


class ActualAdoptedExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = json.loads(CORPUS.read_text("utf-8"))
        raw = cls.corpus["support"]
        cls.support = ExecutionGraphSupport(raw["candidate"], tuple(raw["participant_credentials"]))
        cls.base = next(c["bundle"] for c in cls.corpus["cases"] if c["name"] == "branch_7_valid")

    def bundle(self, case):
        return case.get("bundle") or mutate(self.base, case["operations"])

    def verify(self, case):
        return verify_execution_bundle(self.bundle(case), support=self.support,
                                       trusted_now=case.get("trusted_now", self.corpus["trusted_now"]))

    def test_corpus_is_closed_secret_free_and_matches(self):
        self.assertEqual(self.corpus["schema"], "semantic-adopted-execution-actual-corpus.v3")
        self.assertEqual(len(self.support.participant_credentials), 12)
        def keys(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    yield key
                    yield from keys(child)
            elif isinstance(value, list):
                for child in value: yield from keys(child)
        self.assertFalse(any("private_key" in key.lower() for key in keys(self.corpus)))
        observed = set()
        for case in self.corpus["cases"]:
            with self.subTest(case=case["name"]):
                before = copy.deepcopy(self.bundle(case))
                actual = self.verify(case)
                self.assertEqual(actual, tuple(case["expected_error_kinds"]))
                self.assertEqual(before, self.bundle(case))
                self.assertTrue(set(actual) <= set(ERROR_KINDS))
                observed.update(actual)
        self.assertTrue({"schema_invalid", "digest_mismatch", "signature_invalid",
                         "authority_invalid", "reservation_invalid", "ordering_invalid"} <= observed)

    def test_all_branches_and_completed_outcomes_pass_the_real_graph(self):
        by_name = {case["name"]: case for case in self.corpus["cases"]}
        for index in range(8):
            bundle = by_name[f"branch_{index}_valid"]["bundle"]
            self.assertFalse(validate_protocol(bundle["attempt"]))
            self.assertFalse(validate_protocol(bundle["verdict"]))
            self.assertTrue(verify_execution_graph(bundle, self.support).consistency_verified)
            self.assertEqual(verify_execution_bundle(bundle, support=self.support,
                             trusted_now=self.corpus["trusted_now"]), ())
        for name in ("branch_7_valid", "completed_fail_valid"):
            self.assertEqual(self.verify(by_name[name]), ())
        self.assertEqual(by_name["completed_fail_valid"]["bundle"]["verdict"]["outcome"], "fail")

    def test_exact_histories_contamination_and_required_attacks(self):
        objects = extract_execution_graph(self.base, self.support)
        self.assertEqual(tuple(len(objects[x]["events"]) for x in
                         ("base_access_history", "activated_access_history", "terminal_access_history")), (12, 13, 14))
        participants = objects["preregistration"]["participants"]
        self.assertEqual(sum(p["b0_exposure"] == "disproven" for p in participants), 11)
        expected_purposes = (
            "custody_readiness", "execution_contamination_custodian",
            "execution_contamination_independent_review", "protected_access_activation",
            "evaluator_execution_start", "evaluator_execution_launch",
            "protected_descriptor_handoff", "protected_access_closure", "custody",
            "independent_review",
        )
        approval_roles = (
            "readiness_approval", "contamination_custodian_approval",
            "contamination_reviewer_approval", "activation_approval", "start_approval",
            "launch_approval", "handoff_approval", "closure_approval",
            "verdict_custodian_approval", "verdict_reviewer_approval",
        )
        self.assertEqual(tuple(objects[role]["purpose"] for role in approval_roles), expected_purposes)
        self.assertTrue(all(objects[role]["attestation_body"]["purpose"] == purpose
                            for role, purpose in zip(approval_roles, expected_purposes)))
        by_name = {case["name"]: case for case in self.corpus["cases"]}
        for name in ("direct_descriptor_transfer", "retained_process", "retained_descriptor_handle",
                     "excess_grant", "stale_signature_after_subject_mutation", "wrong_approval_key",
                     "wrong_approval_purpose", "expired_caller_time", "wrong_signer"):
            with self.subTest(case=name):
                self.assertTrue(self.verify(by_name[name]))
        stale = by_name["stale_signature_after_subject_mutation"]["bundle"]
        self.assertEqual(stale["verdict"]["evaluator_execution_start_proof"]["subject"]["process_start_id"],
                         "substituted-process")
        self.assertTrue(verify_execution_graph(stale, self.support).consistency_verified)

    def test_missing_graph_support_rejects(self):
        missing = ExecutionGraphSupport(self.support.candidate, self.support.participant_credentials[:-1])
        self.assertEqual(verify_execution_bundle(self.base, support=missing,
                         trusted_now=self.corpus["trusted_now"]), ("authority_invalid",))

    def test_node_independently_matches_python_bytes(self):
        results = [execution_verification_result(
            self.bundle(case), support=self.support,
            trusted_now=case.get("trusted_now", self.corpus["trusted_now"])) for case in self.corpus["cases"]]
        for case, result in zip(self.corpus["cases"], results):
            self.assertEqual(execution_verification_bytes(
                self.bundle(case), support=self.support,
                trusted_now=case.get("trusted_now", self.corpus["trusted_now"])), jcs_bytes(result))
        completed = subprocess.run(["node", str(NODE)], cwd=ROOT, check=True, capture_output=True)
        self.assertEqual(completed.stderr, b"")
        self.assertEqual(completed.stdout, jcs_bytes(results) + b"\n")


if __name__ == "__main__":
    unittest.main()
