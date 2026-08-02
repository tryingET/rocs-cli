from __future__ import annotations

import base64
import copy
import hashlib
import json
from pathlib import Path
import unittest

from rocs_cli.semantic_adopted_authority import (
    AdoptedAuthorityError,
    ROLE_ORDER,
    verify_authority_credential,
    verify_candidate_support,
    verify_principal_separation,
)
from rocs_cli.semantic_adopted_digests import object_digest
from rocs_cli.semantic_adopted_protocol import jcs_bytes

CORPUS = Path(__file__).parent / "fixtures/semantic-adopted-policy-v1/candidate-support-corpus.json"


def _sha(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


class CandidateSupportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(CORPUS.read_text("utf-8"))

    def fresh(self):
        value = copy.deepcopy(self.fixture)
        policy_raw = jcs_bytes(value["policy"])
        provenance_raw = jcs_bytes(value["provenance"])
        blobs = {
            value["candidate"]["policy_path"]: policy_raw,
            value["candidate"]["provenance_path"]: provenance_raw,
            value["candidate"]["ontology_inventory_path"]: jcs_bytes(value["inventory"]),
            "synthetic-authority/meaning.txt": value["source_text"].encode("utf-8"),
        }
        return value, policy_raw, provenance_raw, blobs

    def verify(self, value, policy_raw, provenance_raw, blobs):
        return verify_candidate_support(
            value["candidate"], policy_bytes=policy_raw,
            provenance_bytes=provenance_raw, inventory=value["inventory"],
            source_blobs=blobs,
            resolved_owner_commit=value["resolved_owner_commit"],
            resolved_owner_tree=value["resolved_owner_tree"],
        )

    def test_conspicuously_synthetic_exact_candidate_passes(self):
        value, policy_raw, provenance_raw, blobs = self.fresh()
        result = self.verify(value, policy_raw, provenance_raw, blobs)
        self.assertEqual(result.policy_concept_ids, ("co.software.ConspicuouslySynthetic",))
        self.assertEqual(result.joint_route_ontology_id_sets, ())
        self.assertIn("CONSPICUOUSLY SYNTHETIC", value["warning"])

    def test_receipt_only_cannot_substitute_for_complete_binding(self):
        value, policy_raw, provenance_raw, blobs = self.fresh()
        binding = value["candidate"]["policy_semantic_binding"]
        binding["policy_concept_ids"] = ["co.software.ReceiptOnlySubstitution"]
        binding["binding_digest"] = object_digest(
            "policy_semantic_binding", binding, "binding_digest"
        )
        value["candidate"]["candidate_digest"] = object_digest(
            "candidate", value["candidate"], "candidate_digest"
        )
        with self.assertRaisesRegex(AdoptedAuthorityError, "binding projection"):
            self.verify(value, policy_raw, provenance_raw, blobs)

    def test_prefix_only_and_copied_core_membership_are_rejected(self):
        for ont_id in (
            "co.software.PrefixOnlyNotInOwnerInventory",
            "co.software.CopiedCoreMeaningNotInExactInventory",
        ):
            with self.subTest(ont_id=ont_id):
                value, policy_raw, provenance_raw, blobs = self.fresh()
                value["candidate"]["selectable_ontology_ids"].append(ont_id)
                value["candidate"]["selectable_ontology_ids"].sort(key=str.encode)
                value["candidate"]["candidate_digest"] = object_digest(
                    "candidate", value["candidate"], "candidate_digest"
                )
                with self.assertRaisesRegex(AdoptedAuthorityError, "inventory authority"):
                    self.verify(value, policy_raw, provenance_raw, blobs)

    def test_missing_source_and_source_byte_drift_reject(self):
        for mode in ("missing", "drift"):
            with self.subTest(mode=mode):
                value, policy_raw, provenance_raw, blobs = self.fresh()
                if mode == "missing":
                    blobs.pop("synthetic-authority/meaning.txt")
                else:
                    blobs["synthetic-authority/meaning.txt"] += b"DRIFT"
                with self.assertRaisesRegex(AdoptedAuthorityError, "source path/byte"):
                    self.verify(value, policy_raw, provenance_raw, blobs)

    def test_exact_source_inventory_rejects_extra_and_policy_byte_substitution(self):
        value, policy_raw, provenance_raw, blobs = self.fresh()
        blobs["synthetic-unclaimed.txt"] = b"synthetic extra"
        with self.assertRaisesRegex(AdoptedAuthorityError, "not exact"):
            self.verify(value, policy_raw, provenance_raw, blobs)
        value, policy_raw, provenance_raw, blobs = self.fresh()
        with self.assertRaises(AdoptedAuthorityError):
            self.verify(value, policy_raw + b" ", provenance_raw, blobs)

    def test_commit_tree_and_inventory_drift_reject(self):
        value, policy_raw, provenance_raw, blobs = self.fresh()
        value["resolved_owner_tree"] = "9" * 40
        with self.assertRaisesRegex(AdoptedAuthorityError, "commit/tree"):
            self.verify(value, policy_raw, provenance_raw, blobs)
        value, policy_raw, provenance_raw, blobs = self.fresh()
        value["inventory"]["ontology_snapshot_digest"] = "sha256:" + "9" * 64
        with self.assertRaisesRegex(AdoptedAuthorityError, "supplied inventory"):
            self.verify(value, policy_raw, provenance_raw, blobs)

    def test_manifest_owner_alone_does_not_cover_record_owners(self):
        value, policy_raw, provenance_raw, blobs = self.fresh()
        provenance = value["provenance"]
        provenance["records"][0]["source_owner_repo"] = "synthetic/copied-core"
        # It remains schema-valid; recompute Decision 102 digests to isolate owner rejection.
        from rocs_cli.semantic_router_protocol import object_digest as d102_digest
        provenance["provenance_manifest_digest"] = d102_digest("provenance_manifest", provenance)
        value["policy"]["provenance_manifest_digest"] = provenance["provenance_manifest_digest"]
        value["policy"]["routing_policy_digest"] = d102_digest("routing_policy", value["policy"])
        policy_raw, provenance_raw = jcs_bytes(value["policy"]), jcs_bytes(provenance)
        blobs[value["candidate"]["policy_path"]] = policy_raw
        blobs[value["candidate"]["provenance_path"]] = provenance_raw
        with self.assertRaises(AdoptedAuthorityError):
            self.verify(value, policy_raw, provenance_raw, blobs)


class AuthorityCredentialAndSeparationTests(unittest.TestCase):
    def credential(self, role="custodian", principal="synthetic-principal"):
        key = bytes(range(32))
        credential = {
            "schema": "semantic-routing-policy-authority-credential.v1",
            "repository_id": "synthetic.repository",
            "git_commit": "6" * 40,
            "git_tree": "7" * 40,
            "principal_id": principal,
            "authority_role": role,
            "trust_root_digest": "sha256:" + "8" * 64,
            "public_key_encoding": "ed25519-raw-32",
            "public_key_base64": base64.b64encode(key).decode("ascii"),
            "public_key_digest": _sha(key),
            "valid_from": "2026-01-01T00:00:00Z",
            "valid_until": "2027-01-01T00:00:00Z",
            "revoked": False,
            "credential_digest": "sha256:" + "0" * 64,
        }
        credential["credential_digest"] = object_digest(
            "authority_credential", credential, "credential_digest"
        )
        authority = {
            key: credential[key]
            for key in ("repository_id", "git_commit", "git_tree", "principal_id", "authority_role")
        }
        authority["authority_credential_digest"] = credential["credential_digest"]
        return authority, credential

    def participants(self):
        participants = []
        assessor, _ = self.credential("independent_reviewer", "synthetic-assessor")
        for index, role in enumerate(ROLE_ORDER):
            authority, _ = self.credential(role, f"synthetic-principal-{index}")
            result = "disproven" if index in (3, 4, 5, 6, 7, 8, 9, 10) else "possible"
            evidence = {
                "schema": "semantic-routing-policy-b0-exposure-evidence.v1",
                "participant_principal_id": authority["principal_id"],
                "assessor_authority": assessor,
                "sources_checked_digest": "sha256:" + format(index, "064x"),
                "evaluated_at": "2026-02-01T00:00:00Z",
                "result": result,
                "evidence_digest": "sha256:" + "0" * 64,
            }
            evidence["evidence_digest"] = object_digest(
                "b0_exposure_evidence", evidence, "evidence_digest"
            )
            participants.append({
                "authority": authority, "role": role, "b0_exposure": result,
                "b0_exposure_evidence": evidence,
                "b0_exposure_evidence_digest": evidence["evidence_digest"],
                "access": ["policy_bytes"] if role == "policy_author" else ["ontology_sources"],
                "assigned_at": "2026-03-01T00:00:00Z",
            })
        return participants

    def test_authority_coordinate_and_credential_are_exactly_joined(self):
        authority, credential = self.credential()
        verify_authority_credential(authority, credential)
        for field, changed in (
            ("git_tree", "9" * 40),
            ("principal_id", "synthetic-other"),
            ("authority_role", "policy_author"),
        ):
            with self.subTest(field=field):
                bad = dict(authority); bad[field] = changed
                with self.assertRaises(AdoptedAuthorityError):
                    verify_authority_credential(bad, credential)

    def test_key_digest_and_credential_digest_drift_reject(self):
        authority, credential = self.credential()
        credential["public_key_digest"] = "sha256:" + "9" * 64
        with self.assertRaises(AdoptedAuthorityError):
            verify_authority_credential(authority, credential)

    def test_all_twelve_principals_and_roles_are_mechanical(self):
        participants = self.participants()
        verify_principal_separation(participants)
        duplicate = copy.deepcopy(participants)
        duplicate[11]["authority"]["principal_id"] = duplicate[0]["authority"]["principal_id"]
        with self.assertRaisesRegex(AdoptedAuthorityError, "pairwise"):
            verify_principal_separation(duplicate)
        wrong_role = copy.deepcopy(participants)
        wrong_role[0]["authority"]["authority_role"] = "policy_author"
        with self.assertRaisesRegex(AdoptedAuthorityError, "authority role"):
            verify_principal_separation(wrong_role)

    def test_policy_and_sealed_row_access_conflicts(self):
        participants = self.participants()
        participants[1]["access"].append("sealed_acceptance_rows")
        with self.assertRaisesRegex(AdoptedAuthorityError, "policy and sealed-row"):
            verify_principal_separation(participants)


if __name__ == "__main__":
    unittest.main()
