from __future__ import annotations
import base64, copy, hashlib, json, os, subprocess, tempfile, unittest
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import patch
import rocs_cli.semantic_adopted_authority as authority_module
from rocs_cli.semantic_adopted_authority import AdoptedAuthorityError, ROLE_ORDER, verify_authority_credential, verify_candidate_support, verify_contamination_manifest, verify_principal_separation
from rocs_cli.semantic_adopted_digests import object_digest
from rocs_cli.semantic_adopted_protocol import jcs_bytes
from rocs_cli.semantic_router_protocol import object_digest as d102_digest
from rocs_cli.semantic_adopted_signatures import signature_message
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
CORPUS = Path(__file__).parent / "fixtures/semantic-adopted-policy-v1/candidate-support-corpus.json"
def _sha(raw: bytes) -> str: return "sha256:" + hashlib.sha256(raw).hexdigest()
class CandidateSupportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(CORPUS.read_text()); cls.private_raw = hashlib.sha256(b"authority-test-only-private-seed").digest(); cls.signing_key = Ed25519PrivateKey.from_private_bytes(cls.private_raw)
    def git(self, root, *args, data=None):
        env={**os.environ,"GIT_AUTHOR_NAME":"Synthetic","GIT_AUTHOR_EMAIL":"s@example.invalid","GIT_COMMITTER_NAME":"Synthetic","GIT_COMMITTER_EMAIL":"s@example.invalid"}
        return subprocess.run(["git",*args],cwd=root,input=data,env=env,check=True,stdout=subprocess.PIPE).stdout.strip().decode()
    def sync_readiness(self, v, inventory):
        s=v["custody_readiness_subject"]; r=v["custody_readiness_receipt"]; q=v["custody_readiness_request"]; cred=r["custodian_credential"]
        public=self.signing_key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw);cred["public_key_base64"]=base64.b64encode(public).decode();cred["public_key_digest"]=_sha(public);cred["credential_digest"]=object_digest("authority_credential",cred,"credential_digest");authority=s["custodian_authority"];authority["authority_credential_digest"]=cred["credential_digest"]
        s["concept_inventory"]=copy.deepcopy(inventory);s["concept_inventory_digest"]=inventory["inventory_digest"];s["subject_digest"]=object_digest("custody_readiness_subject",s,"subject_digest")
        r["subject"]=copy.deepcopy(s); a=r["custodian_approval"];a.update(issuer=copy.deepcopy(authority),subject_digest=s["subject_digest"],public_key_digest=cred["public_key_digest"]);body=a["attestation_body"]
        for field in ("issuer","subject_digest","purpose","valid_from","valid_until","revoked","trust_root_digest","public_key_digest"): body[field]=copy.deepcopy(a[field])
        body["body_digest"]=object_digest("approval_attestation_body",body,"body_digest");a["signature_base64"]=base64.b64encode(self.signing_key.sign(signature_message("approval",body["body_digest"]))).decode();a["artifact_digest"]=object_digest("approval_artifact",a,"artifact_digest");r["readiness_digest"]=object_digest("custody_readiness",r,"readiness_digest")
        q.update(readiness_digest=r["readiness_digest"],subject_digest=s["subject_digest"],expected_custodian_authority=copy.deepcopy(authority),expected_custodian_credential=copy.deepcopy(cred),expected_custodian_approval_digest=a["artifact_digest"],expected_public_key_digest=cred["public_key_digest"],expected_concept_inventory=copy.deepcopy(inventory),expected_concept_inventory_digest=inventory["inventory_digest"]);q["request_digest"]=object_digest("custody_readiness_verification_request",q,"request_digest")
    def sync_candidate(self,v):
        p,g,c=v["policy"],v["provenance"],v["candidate"]
        g["provenance_manifest_digest"]=d102_digest("provenance_manifest",g);p["provenance_manifest_digest"]=g["provenance_manifest_digest"];p["routing_policy_digest"]=d102_digest("routing_policy",p)
        c["routing_policy_digest"]=p["routing_policy_digest"];c["provenance_manifest_digest"]=g["provenance_manifest_digest"]
        receipt=c["policy_semantic_binding"]["binding_receipt"];receipt["routing_policy_digest"]=p["routing_policy_digest"];receipt["provenance_manifest_digest"]=g["provenance_manifest_digest"];receipt["inventory_digest"]=c["ontology_inventory_digest"];receipt["receipt_digest"]=object_digest("policy_binding_receipt",receipt,"receipt_digest")
        binding=c["policy_semantic_binding"];binding["inventory_digest"]=c["ontology_inventory_digest"];binding["binding_receipt_digest"]=receipt["receipt_digest"];binding["binding_digest"]=object_digest("policy_semantic_binding",binding,"binding_digest")
        row=next(x for x in v["contamination_manifest"]["coverage"] if x["surface"]=="policy");row["source_digest"]=p["routing_policy_digest"];m=v["contamination_manifest"];m["manifest_digest"]=object_digest("contamination_manifest",m,"manifest_digest");c["contamination_manifest_digest"]=m["manifest_digest"];c["candidate_digest"]=object_digest("candidate",c,"candidate_digest")
    def fresh(self, extra_sources=0):
        v=copy.deepcopy(self.fixture); td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);root=Path(td.name);self.git(root,"init","-q")
        invraw=v["inventory_source_bytes_utf8"].encode(); ip=v["candidate"]["ontology_inventory_path"]; source=v["source_text"].encode();sp="synthetic-authority/meaning.txt"
        (root/ip).parent.mkdir(parents=True);(root/ip).write_bytes(invraw);self.git(root,"add",".");self.git(root,"commit","-qm","inventory");I=self.git(root,"rev-parse","HEAD");IT=self.git(root,"rev-parse","HEAD^{tree}");base=self.git(root,"rev-parse","HEAD^") if False else None
        # S is intentionally unrelated to I: an orphan source root, later merged into C.
        self.git(root,"checkout","--orphan","source","-q");self.git(root,"rm","-rf",".");(root/sp).parent.mkdir(parents=True,exist_ok=True);(root/sp).write_bytes(source);self.git(root,"add",".");self.git(root,"commit","-qm","source");S=self.git(root,"rev-parse","HEAD")
        extras=[]
        for n in range(extra_sources):
            path=f"synthetic-authority/extra-{n}.txt";data=f"extra-{n}\n".encode();(root/path).write_bytes(data);self.git(root,"add",path);self.git(root,"commit","-qm",f"source {n}");extras.append((self.git(root,"rev-parse","HEAD"),path,data))
        v["_extra_sources"]=extras;v["policy"]["authority"]["revision"]=S;v["provenance"]["policy_revision"]=S
        for x in v["provenance"]["records"]: x["source_revision"]=S
        self.sync_candidate(v); policy=jcs_bytes(v["policy"]); provenance=jcs_bytes(v["provenance"])
        c=v["candidate"];(root/c["policy_path"]).parent.mkdir(parents=True,exist_ok=True);(root/c["policy_path"]).write_bytes(policy);(root/c["provenance_path"]).write_bytes(provenance);self.git(root,"add",".");self.git(root,"commit","-qm","policy")
        self.git(root,"merge","--allow-unrelated-histories","--no-ff","-qm","candidate",I);C=self.git(root,"rev-parse","HEAD");CT=self.git(root,"rev-parse","HEAD^{tree}")
        inventory=copy.deepcopy(c["ontology_inventory"]);inventory.update(owner_git_commit=I,owner_git_tree=IT,inventory_source_digest=_sha(invraw));inventory["inventory_digest"]=object_digest("ontology_inventory",inventory,"inventory_digest")
        c.update(owner_git_commit=C,owner_git_tree=CT,ontology_inventory=inventory,ontology_inventory_digest=inventory["inventory_digest"],ontology_snapshot_digest=inventory["ontology_snapshot_digest"],selectable_ontology_ids=inventory["ontology_ids"]);self.sync_readiness(v,inventory);self.sync_candidate(v)
        return v,root,policy,provenance,invraw,I,S,C
    def verify(self,args):
        v,root,policy,provenance,invraw,*_=args
        key=(v["policy"]["authority"]["revision"],v["policy"]["authority"]["path"]);sources={key:v["source_text"].encode()}
        return verify_candidate_support(jcs_bytes(v["candidate"]),policy_bytes=policy,provenance_bytes=provenance,inventory_source_bytes=invraw,source_bytes=sources,custody_readiness_subject=v["custody_readiness_subject"],custody_readiness_receipt=v["custody_readiness_receipt"],custody_readiness_request=v["custody_readiness_request"],contamination_manifest=v["contamination_manifest"],contamination_source_digests=v["contamination_non_policy_source_digests"],local_git_root=root)
    def test_real_git_positive_unrelated_i_s_and_external_immutable_candidate(self):
        args=self.fresh();result=self.verify(args);v,root,*_=args
        self.assertFalse((root/"synthetic-candidate/candidate.json").exists());self.assertEqual(result.candidate_bytes,jcs_bytes(v["candidate"]));self.assertEqual(result.candidate_digest,v["candidate"]["candidate_digest"])
        v["candidate"]["candidate_id"]="later-mutation";self.assertNotIn(b"later-mutation",result.candidate_bytes)
    def test_candidate_requires_canonical_bytes_and_exact_named_sources(self):
        args=self.fresh();v=args[0];self.assertEqual(self.fixture["candidate_bytes_utf8"].encode(),jcs_bytes(self.fixture["candidate"]))
        with self.assertRaises(AdoptedAuthorityError): verify_candidate_support(v["candidate"],policy_bytes=args[2],provenance_bytes=args[3],inventory_source_bytes=args[4],source_bytes={},custody_readiness_subject=v["custody_readiness_subject"],custody_readiness_receipt=v["custody_readiness_receipt"],custody_readiness_request=v["custody_readiness_request"],contamination_manifest=v["contamination_manifest"],contamination_source_digests=v["contamination_non_policy_source_digests"],local_git_root=args[1])
        candidate=jcs_bytes(v["candidate"])
        with self.assertRaisesRegex(AdoptedAuthorityError,"canonical JCS"): verify_candidate_support(b" "+candidate,policy_bytes=args[2],provenance_bytes=args[3],inventory_source_bytes=args[4],source_bytes={},custody_readiness_subject=v["custody_readiness_subject"],custody_readiness_receipt=v["custody_readiness_receipt"],custody_readiness_request=v["custody_readiness_request"],contamination_manifest=v["contamination_manifest"],contamination_source_digests=v["contamination_non_policy_source_digests"],local_git_root=args[1])
        key=(args[6],"synthetic-authority/meaning.txt")
        for sources in ({},{key:b"wrong"},{key:v["source_text"].encode(),("0"*40,"extra"):b"x"}):
            with self.assertRaises(AdoptedAuthorityError): verify_candidate_support(candidate,policy_bytes=args[2],provenance_bytes=args[3],inventory_source_bytes=args[4],source_bytes=sources,custody_readiness_subject=v["custody_readiness_subject"],custody_readiness_receipt=v["custody_readiness_receipt"],custody_readiness_request=v["custody_readiness_request"],contamination_manifest=v["contamination_manifest"],contamination_source_digests=v["contamination_non_policy_source_digests"],local_git_root=args[1])
    def test_real_same_and_nonancestor_source_attacks(self):
        for attack in ("same","nonancestor"):
            args=self.fresh();v,root,policy,provenance,raw,I,S,C=args
            revision=C
            if attack=="nonancestor":
                (root/"other").write_text("x");self.git(root,"add","other");self.git(root,"commit","-qm","later");revision=self.git(root,"rev-parse","HEAD")
            with self.subTest(attack=attack),self.assertRaisesRegex(AdoptedAuthorityError,"strict candidate ancestor"):
                authority_module._git_proof(root,v["candidate"],jcs_bytes(v["candidate"]),raw,policy,provenance,[(revision,"synthetic-authority/meaning.txt",_sha(v["source_text"].encode()))],{(revision,"synthetic-authority/meaning.txt"):v["source_text"].encode()})
    def recommit(self,args,path,raw):
        v,root,*_=args;(root/path).write_bytes(raw);self.git(root,"add",path);self.git(root,"commit","-qm","attack");v["candidate"]["owner_git_commit"]=self.git(root,"rev-parse","HEAD");v["candidate"]["owner_git_tree"]=self.git(root,"rev-parse","HEAD^{tree}");self.sync_candidate(v)
    def test_real_i_same_nonancestor_tree_and_source_path_attacks(self):
        for attack in ("same_i", "nonancestor_i", "same_tree", "source_path"):
            args=self.fresh();v,root,policy,provenance,raw,I,S,C=args;c=copy.deepcopy(v["candidate"]);inv=c["ontology_inventory"]
            if attack=="same_i": inv.update(owner_git_commit=C,owner_git_tree=c["owner_git_tree"])
            elif attack=="nonancestor_i":
                (root/"later").write_text("x");self.git(root,"add","later");self.git(root,"commit","-qm","later");inv.update(owner_git_commit=self.git(root,"rev-parse","HEAD"),owner_git_tree=self.git(root,"rev-parse","HEAD^{tree}"))
            elif attack=="same_tree": inv["owner_git_tree"]=c["owner_git_tree"]
            claims=[(S,"missing/source",_sha(v["source_text"].encode()))] if attack=="source_path" else [(S,"synthetic-authority/meaning.txt",_sha(v["source_text"].encode()))]
            with self.subTest(attack=attack),self.assertRaises(AdoptedAuthorityError): authority_module._git_proof(root,c,jcs_bytes(c),raw,policy,provenance,claims,{(rev,path):v["source_text"].encode() for rev,path,_digest in claims})
    def test_real_multi_s_batched_complete_tree_and_hidden_candidate_bytes(self):
        args=self.fresh(extra_sources=5);v,root,policy,provenance,raw,I,S,C=args;base=(S,"synthetic-authority/meaning.txt",_sha(v["source_text"].encode()));claims=[base]+[(rev,path,_sha(data)) for rev,path,data in v["_extra_sources"]];sources={(S,base[1]):v["source_text"].encode(),**{(rev,path):data for rev,path,data in v["_extra_sources"]}}
        real_run,real_popen=subprocess.run,subprocess.Popen
        with patch.object(authority_module.subprocess,"run",wraps=real_run) as runs,patch.object(authority_module.subprocess,"Popen",wraps=real_popen) as popens:
            authority_module._git_proof(root,v["candidate"],jcs_bytes(v["candidate"]),raw,policy,provenance,claims,sources)
        self.assertLessEqual(runs.call_count+popens.call_count,8)
        hidden=v["_extra_sources"][-1][2]
        with self.assertRaisesRegex(AdoptedAuthorityError,"present inside"): authority_module._git_proof(root,v["candidate"],hidden,raw,policy,provenance,claims,sources)
    def test_repository_descriptor_replacement_rejects(self):
        args=self.fresh();v,root,*_=args;original_close=authority_module._CatFile.close;done=False
        def replace(cat):
            nonlocal done
            original_close(cat)
            if not done:
                moved=Path(str(root)+"-moved");root.rename(moved);root.mkdir();done=True;self.addCleanup(lambda: moved.exists() and __import__("shutil").rmtree(moved))
        with patch.object(authority_module._CatFile,"close",replace),self.assertRaisesRegex(AdoptedAuthorityError,"descriptor identity"): self.verify(args)
    def test_real_retained_source_and_inventory_drift_attacks(self):
        for kind,path in (("source","synthetic-authority/meaning.txt"),("inventory",self.fixture["candidate"]["ontology_inventory_path"])):
            args=self.fresh();self.recommit(args,path,b"drift")
            with self.subTest(kind=kind),self.assertRaises(AdoptedAuthorityError): self.verify(args)
    def test_real_nonregular_source_mode_attack(self):
        args=self.fresh();v,root,*_=args;path=root/"synthetic-authority/meaning.txt";path.unlink();path.symlink_to("nonregular-target");self.git(root,"add","synthetic-authority/meaning.txt");self.git(root,"commit","-qm","mode attack");v["candidate"]["owner_git_commit"]=self.git(root,"rev-parse","HEAD");v["candidate"]["owner_git_tree"]=self.git(root,"rev-parse","HEAD^{tree}");self.sync_candidate(v)
        with self.assertRaisesRegex(AdoptedAuthorityError,"unsafe mode"): self.verify(args)
    def test_path_extractor_and_p3_preimage_attacks(self):
        attacks=(lambda v:v["candidate"].__setitem__("ontology_inventory_path","wrong/path"),lambda v:v["candidate"]["ontology_inventory"].__setitem__("inventory_extractor_algorithm","wrong"),lambda v:v["custody_readiness_request"].__setitem__("expected_concept_inventory_digest","sha256:"+"9"*64))
        for n,attack in enumerate(attacks):
            args=self.fresh();attack(args[0]);self.sync_candidate(args[0])
            with self.subTest(n=n),self.assertRaises(AdoptedAuthorityError): self.verify(args)
    def test_canonical_inventory_source_boundaries(self):
        for raw in (b' {"ontology_ids":["co.software.ConspicuouslySynthetic"],"schema":"softwareco-ontology-inventory-source.v1"}',b'{"ontology_ids":[],"schema":"softwareco-ontology-inventory-source.v1"}',b'{"ontology_ids":["core.Impostor"],"schema":"softwareco-ontology-inventory-source.v1"}'):
            args=self.fresh();args=list(args);args[4]=raw
            with self.assertRaisesRegex(AdoptedAuthorityError,"inventory preimage"): self.verify(args)
    def test_real_source_resource_attack_and_input_ceilings(self):
        args=self.fresh();v,root,*_=args;raw=b"x"*(authority_module._MAX_FILE+1);self.recommit(args,"synthetic-authority/meaning.txt",raw)
        with self.assertRaises(AdoptedAuthorityError) as caught: authority_module._git_proof(root,v["candidate"],jcs_bytes(v["candidate"]),args[4],args[2],args[3],[(args[6],"synthetic-authority/meaning.txt",_sha(raw))],{(args[6],"synthetic-authority/meaning.txt"):raw})
        self.assertEqual(caught.exception.kind,"resource_exhausted")
        for limit in (authority_module._MAX_FILE,authority_module._MAX_PROVENANCE,authority_module._MAX_METADATA): self.assertEqual(len(b"x"*limit),limit);self.assertEqual(len(b"x"*(limit+1)),limit+1)
    def test_every_declared_acquisition_max_and_max_plus_one(self):
        A=authority_module
        cases=[((A._MAX_FILE,A._MAX_PROVENANCE,A._MAX_FILE),{}),((0,0,0),{"sources":[A._MAX_FILE]}),((0,0,0),{"sources":[A._MAX_SOURCE_TOTAL]}),((0,0,0),{"contents":[A._MAX_CONTENT_TOTAL]}),((0,0,0),{"records":A._MAX_RECORDS}),((0,0,0),{"objects":A._MAX_OBJECTS})]
        for args,kw in cases: A._acquisition_bounds(*args,**kw)
        failures=[((A._MAX_FILE+1,0,0),{}),((0,A._MAX_PROVENANCE+1,0),{}),((0,0,A._MAX_FILE+1),{}),((0,0,0),{"sources":[A._MAX_FILE+1]}),((0,0,0),{"sources":[A._MAX_SOURCE_TOTAL,1]}),((0,0,0),{"contents":[A._MAX_CONTENT_TOTAL,1]}),((0,0,0),{"records":A._MAX_RECORDS+1}),((0,0,0),{"objects":A._MAX_OBJECTS+1})]
        for args,kw in failures:
            with self.assertRaises(AdoptedAuthorityError) as caught: A._acquisition_bounds(*args,**kw)
            self.assertEqual(caught.exception.kind,"resource_exhausted")
    def test_real_metadata_process_and_isolated_output_boundaries(self):
        args=self.fresh();gitdir=str(args[1]/".git")
        for extra in (0,1):
            data=b"x"*(authority_module._MAX_METADATA+extra)
            if not extra: authority_module._run_git(gitdir,["hash-object","--stdin"],budget=authority_module._GitBudget(),data=data,limit=128)
            else:
                with self.assertRaisesRegex(AdoptedAuthorityError,"input") as caught: authority_module._run_git(gitdir,["hash-object","--stdin"],budget=authority_module._GitBudget(),data=data,limit=128)
                self.assertEqual(caught.exception.kind,"resource_exhausted")
        b=authority_module._GitBudget()
        for _ in range(authority_module._MAX_GIT_PROCESSES): authority_module._run_git(gitdir,["rev-parse","HEAD"],budget=b,limit=128)
        with self.assertRaisesRegex(AdoptedAuthorityError,"subprocess") as caught: authority_module._run_git(gitdir,["rev-parse","HEAD"],budget=b,limit=128)
        self.assertEqual(caught.exception.kind,"resource_exhausted")
        def invoke(out=b"",err=b"",budget=None):
            def run(_cmd,**kw): kw["stdout"].write(out);kw["stderr"].write(err);return type("R",(),{"returncode":0})()
            with patch.object(authority_module.subprocess,"run",side_effect=run): return authority_module._run_git("/tmp/x",["x"],budget=budget or authority_module._GitBudget(),limit=authority_module._MAX_STDOUT)
        self.assertEqual(len(invoke(out=b"x"*authority_module._MAX_STDOUT)),authority_module._MAX_STDOUT)
        with self.assertRaises(AdoptedAuthorityError) as caught: invoke(out=b"x"*(authority_module._MAX_STDOUT+1))
        self.assertEqual(caught.exception.kind,"resource_exhausted")
        self.assertEqual(invoke(err=b"x"*authority_module._MAX_STDERR),b"")
        with self.assertRaises(AdoptedAuthorityError) as caught: invoke(err=b"x"*(authority_module._MAX_STDERR+1))
        self.assertEqual(caught.exception.kind,"resource_exhausted")
        for field,maximum in (("stdout",authority_module._MAX_STDOUT_TOTAL),("stderr",authority_module._MAX_STDERR_TOTAL)):
            for extra in (0,1):
                budget=authority_module._GitBudget();setattr(budget,field,maximum-1);kw={"out" if field=="stdout" else "err":b"x"*(1+extra)}
                if not extra: invoke(budget=budget,**kw)
                else:
                    with self.assertRaises(AdoptedAuthorityError) as caught: invoke(budget=budget,**kw)
                    self.assertEqual(caught.exception.kind,"resource_exhausted")
    def test_ten_contamination_coordinates_recomputed(self):
        args=self.fresh();v=args[0];verify_contamination_manifest(v["contamination_manifest"],policy_source_digest=v["policy"]["routing_policy_digest"],non_policy_source_digests=v["contamination_non_policy_source_digests"])
        v["contamination_non_policy_source_digests"]["aliases"]="sha256:"+"9"*64
        with self.assertRaises(AdoptedAuthorityError): self.verify(args)
    def test_fixture_private_material_scan(self):
        raws=[CORPUS.read_bytes(),(CORPUS.parent/"execution-corpus.json").read_bytes()];seeds=[self.private_raw,hashlib.sha256(b"corpus-only-signing-seed").digest(),bytes(range(32)),bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")];patterns=[b"BEGIN PRIVATE KEY",b"private_key_base64",b'"private_key"',b'"seed"']
        for seed in seeds: patterns += [seed,seed.hex().encode(),base64.b64encode(seed)]
        for raw in raws:
            for pattern in patterns: self.assertNotIn(pattern,raw)

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
