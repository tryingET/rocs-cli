from __future__ import annotations

import base64
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from rocs_cli.semantic_adopted_authority import (
    AdoptedAuthorityError, ROLE_ORDER, verify_authority_credential,
    verify_candidate_support, verify_contamination_manifest,
    verify_principal_separation,
)
from rocs_cli.semantic_adopted_digests import object_digest
from rocs_cli.semantic_adopted_protocol import jcs_bytes
from rocs_cli.semantic_router_protocol import object_digest as d102_digest

CORPUS = Path(__file__).parent / "fixtures/semantic-adopted-policy-v1/candidate-support-corpus.json"

def _sha(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()



class CandidateSupportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(CORPUS.read_text("utf-8"))

    def fresh(self):
        value = copy.deepcopy(self.fixture)
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / ".git/objects/pack").mkdir(parents=True)
        (root / ".git/config").write_text("[user]\n\tname = Synthetic\n", "utf-8")
        policy = jcs_bytes(value["policy"])
        provenance = jcs_bytes(value["provenance"])
        inventory = value["inventory_bytes_utf8"].encode("utf-8")
        blobs = {
            value["candidate"]["policy_path"]: policy,
            value["candidate"]["provenance_path"]: provenance,
            value["candidate"]["ontology_inventory_path"]: inventory,
            "synthetic-authority/meaning.txt": value["source_text"].encode(),
        }
        return value, policy, provenance, inventory, root, blobs

    def runner(self, value, blobs):
        commit, tree = value["candidate"]["owner_git_commit"], value["candidate"]["owner_git_tree"]
        oids = {path: hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
                for path, raw in blobs.items()}
        by_oid = {oids[path]: raw for path, raw in blobs.items()}
        calls = []
        def run(command, **kwargs):
            calls.append(command)
            args = command[command.index("-c", command.index("-c") + 1) + 2:]  # ignored; inspect tail
            data, output = kwargs.get("input", b""), kwargs["stdout"]
            if "config" in command:
                raw = b"user.name\nSynthetic\0"
            elif "for-each-ref" in command:
                raw = b""
            elif "--batch-check=%(objectname) %(objecttype) %(objectsize)" in command:
                rows = []
                for expression in data.decode().splitlines():
                    if expression == commit:
                        rows.append(f"{commit} commit 123")
                    elif expression == f"{commit}^{{tree}}":
                        rows.append(f"{tree} tree 123")
                    else:
                        path = expression.split(":", 1)[1]
                        raw_blob = blobs[path]
                        rows.append(f"{oids[path]} blob {len(raw_blob)}")
                raw = ("\n".join(rows) + "\n").encode()
            elif "ls-tree" in command:
                raw = b"".join(
                    f"100644 blob {oids[path]}\t{path}".encode() + b"\0"
                    for path in sorted(blobs)
                )
            elif "--batch" in command:
                chunks = []
                for oid in data.decode().splitlines():
                    blob = by_oid[oid]
                    chunks.append(f"{oid} blob {len(blob)}\n".encode() + blob + b"\n")
                raw = b"".join(chunks)
            else:
                raise AssertionError(command)
            output.write(raw)
            return type("Result", (), {"returncode": 0})()
        return run, calls

    def verify(self, value, policy, provenance, inventory, root, blobs):
        runner, calls = self.runner(value, blobs)
        with patch("rocs_cli.semantic_adopted_authority.subprocess.run", side_effect=runner):
            result = verify_candidate_support(
                value["candidate"], policy_bytes=policy, provenance_bytes=provenance,
                inventory_bytes=inventory, contamination_manifest=value["contamination_manifest"],
                contamination_source_digests=value["contamination_non_policy_source_digests"],
                local_git_root=root,
            )
        self.assertLessEqual(len(calls), 8)
        return result

    def sync(self, value):
        policy, provenance = value["policy"], value["provenance"]
        provenance["provenance_manifest_digest"] = d102_digest("provenance_manifest", provenance)
        policy["provenance_manifest_digest"] = provenance["provenance_manifest_digest"]
        policy["routing_policy_digest"] = d102_digest("routing_policy", policy)
        candidate = value["candidate"]
        candidate["routing_policy_digest"] = policy["routing_policy_digest"]
        candidate["provenance_manifest_digest"] = provenance["provenance_manifest_digest"]
        receipt = candidate["policy_semantic_binding"]["binding_receipt"]
        receipt["routing_policy_digest"] = policy["routing_policy_digest"]
        receipt["provenance_manifest_digest"] = provenance["provenance_manifest_digest"]
        receipt["receipt_digest"] = object_digest("policy_binding_receipt", receipt, "receipt_digest")
        binding = candidate["policy_semantic_binding"]
        binding["binding_receipt_digest"] = receipt["receipt_digest"]
        binding["binding_digest"] = object_digest("policy_semantic_binding", binding, "binding_digest")
        policy_row = next(row for row in value["contamination_manifest"]["coverage"] if row["surface"] == "policy")
        policy_row["source_digest"] = policy["routing_policy_digest"]
        manifest = value["contamination_manifest"]
        manifest["manifest_digest"] = object_digest("contamination_manifest", manifest, "manifest_digest")
        candidate["contamination_manifest_digest"] = manifest["manifest_digest"]
        candidate["candidate_digest"] = object_digest("candidate", candidate, "candidate_digest")

    def test_exact_batched_candidate_and_eight_process_ceiling(self):
        args = self.fresh()
        result = self.verify(*args)
        self.assertEqual(result.policy_concept_ids, ("co.software.ConspicuouslySynthetic",))

    def test_parent_and_caller_source_revisions_reject_before_git(self):
        for target in ("authority", "record"):
            with self.subTest(target=target):
                value, policy, provenance, inventory, root, blobs = self.fresh()
                if target == "authority":
                    value["policy"]["authority"]["revision"] = "9" * 40
                    value["provenance"]["policy_revision"] = "9" * 40
                else:
                    value["provenance"]["records"][0]["source_revision"] = "9" * 40
                self.sync(value)
                policy, provenance = jcs_bytes(value["policy"]), jcs_bytes(value["provenance"])
                blobs[value["candidate"]["policy_path"]] = policy
                blobs[value["candidate"]["provenance_path"]] = provenance
                with self.assertRaisesRegex(AdoptedAuthorityError, "candidate commit"):
                    self.verify(value, policy, provenance, inventory, root, blobs)

    def test_full_inventory_blob_bytes_not_ontology_projection(self):
        value, policy, provenance, inventory, root, blobs = self.fresh()
        inventory = b" \n" + inventory + b"\n"
        blobs[value["candidate"]["ontology_inventory_path"]] = inventory
        self.verify(value, policy, provenance, inventory, root, blobs)
        blobs[value["candidate"]["ontology_inventory_path"]] = jcs_bytes({"ontology_ids": value["inventory"]["ontology_ids"]})
        with self.assertRaises(AdoptedAuthorityError):
            self.verify(value, policy, provenance, inventory, root, blobs)

    def test_each_source_and_aggregate_bounds_reject(self):
        value, policy, provenance, inventory, root, blobs = self.fresh()
        blobs["synthetic-authority/meaning.txt"] = b"x" * (1_048_576 + 1)
        with self.assertRaisesRegex(AdoptedAuthorityError, "byte limit"):
            self.verify(value, policy, provenance, inventory, root, blobs)

    def test_unsafe_state_rejects_without_git_subprocess(self):
        for relative in ("shallow", "objects/info/alternates", "info/grafts"):
            with self.subTest(relative=relative):
                value, policy, provenance, inventory, root, blobs = self.fresh()
                path = root / ".git" / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("unsafe\n")
                with patch("rocs_cli.semantic_adopted_authority.subprocess.run") as run:
                    with self.assertRaisesRegex(AdoptedAuthorityError, "unsafe"):
                        verify_candidate_support(
                            value["candidate"], policy_bytes=policy, provenance_bytes=provenance,
                            inventory_bytes=inventory, contamination_manifest=value["contamination_manifest"],
                            contamination_source_digests=value["contamination_non_policy_source_digests"],
                            local_git_root=root,
                        )
                    run.assert_not_called()

    def test_all_ten_contamination_source_coordinates_join(self):
        value, policy, provenance, inventory, root, blobs = self.fresh()
        verify_contamination_manifest(
            value["contamination_manifest"], policy_source_digest=value["policy"]["routing_policy_digest"],
            non_policy_source_digests=value["contamination_non_policy_source_digests"],
        )
        bad = dict(value["contamination_non_policy_source_digests"])
        bad["aliases"] = "sha256:" + "9" * 64
        with self.assertRaisesRegex(AdoptedAuthorityError, "coordinate differs"):
            verify_contamination_manifest(
                value["contamination_manifest"], policy_source_digest=value["policy"]["routing_policy_digest"],
                non_policy_source_digests=bad,
            )

class AuthorityCredentialAndSeparationTests(unittest.TestCase):
    def credential(self, role="custodian", principal="synthetic-principal"):
        key = bytes(range(32))
        credential = {
            "schema": "semantic-routing-policy-authority-credential.v1",
            "repository_id": "synthetic.repository", "git_commit": "6" * 40,
            "git_tree": "7" * 40, "principal_id": principal, "authority_role": role,
            "trust_root_digest": "sha256:" + "8" * 64,
            "public_key_encoding": "ed25519-raw-32",
            "public_key_base64": base64.b64encode(key).decode(), "public_key_digest": _sha(key),
            "valid_from": "2026-01-01T00:00:00Z", "valid_until": "2027-01-01T00:00:00Z",
            "revoked": False, "credential_digest": "sha256:" + "0" * 64,
        }
        credential["credential_digest"] = object_digest("authority_credential", credential, "credential_digest")
        authority = {key: credential[key] for key in (
            "repository_id", "git_commit", "git_tree", "principal_id", "authority_role"
        )}
        authority["authority_credential_digest"] = credential["credential_digest"]
        return authority, credential

    def participants(self):
        assessor, _ = self.credential("independent_reviewer", "synthetic-external-assessor")
        result = []
        for index, role in enumerate(ROLE_ORDER):
            authority, _ = self.credential(role, f"synthetic-principal-{index}")
            exposure = "disproven" if index in range(3, 11) else "possible"
            evidence = {
                "schema": "semantic-routing-policy-b0-exposure-evidence.v1",
                "participant_principal_id": authority["principal_id"], "assessor_authority": assessor,
                "sources_checked_digest": "sha256:" + format(index, "064x"),
                "evaluated_at": "2026-02-01T00:00:00Z", "result": exposure,
                "evidence_digest": "sha256:" + "0" * 64,
            }
            evidence["evidence_digest"] = object_digest("b0_exposure_evidence", evidence, "evidence_digest")
            result.append({
                "authority": authority, "role": role, "b0_exposure": exposure,
                "b0_exposure_evidence": evidence, "b0_exposure_evidence_digest": evidence["evidence_digest"],
                "access": ["policy_bytes"] if role == "policy_author" else ["ontology_sources"],
                "assigned_at": "2026-03-01T00:00:00Z",
            })
        return result

    def test_trusted_now_enforces_credential_window(self):
        authority, credential = self.credential()
        verify_authority_credential(authority, credential, trusted_now="2026-06-01T00:00:00Z")
        for now in ("2025-12-31T23:59:59Z", "2027-01-01T00:00:01Z"):
            with self.subTest(now=now), self.assertRaises(AdoptedAuthorityError):
                verify_authority_credential(authority, credential, trusted_now=now)

    def test_single_external_independent_assessor_and_no_self_assessment(self):
        participants = self.participants()
        verify_principal_separation(participants)
        bad = copy.deepcopy(participants)
        bad[0]["b0_exposure_evidence"]["assessor_authority"] = bad[0]["authority"]
        with self.assertRaises(AdoptedAuthorityError):
            verify_principal_separation(bad)
        bad = copy.deepcopy(participants)
        other, _ = self.credential("independent_reviewer", "another-assessor")
        bad[1]["b0_exposure_evidence"]["assessor_authority"] = other
        with self.assertRaisesRegex(AdoptedAuthorityError, "one independent assessor"):
            verify_principal_separation(bad)

    def test_twelve_distinct_roles_b0_and_access_matrix(self):
        participants = self.participants()
        participants[11]["authority"]["principal_id"] = participants[0]["authority"]["principal_id"]
        with self.assertRaisesRegex(AdoptedAuthorityError, "pairwise"):
            verify_principal_separation(participants)
        participants = self.participants()
        participants[3]["b0_exposure"] = "possible"
        with self.assertRaises(AdoptedAuthorityError):
            verify_principal_separation(participants)
        participants = self.participants()
        participants[1]["access"] = ["policy_bytes", "ontology_sources"]
        with self.assertRaisesRegex(AdoptedAuthorityError, "canonical matrix order"):
            verify_principal_separation(participants)


if __name__ == "__main__":
    unittest.main()
