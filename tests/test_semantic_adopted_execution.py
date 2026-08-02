from __future__ import annotations
import base64, copy, dataclasses, hashlib, json, os, pathlib, subprocess, tempfile, unittest
from rocs_cli.semantic_adopted_authority import verify_candidate_support
from rocs_cli.semantic_adopted_execution import ERROR_KINDS, execution_verification_bytes, execution_verification_result, verify_execution_bundle
from rocs_cli.semantic_adopted_graph import ExecutionGraphSupport, extract_execution_graph, verify_execution_graph
from rocs_cli.semantic_adopted_protocol import jcs_bytes, validate_protocol
ROOT=pathlib.Path(__file__).resolve().parents[1];CORPUS=ROOT/"tests/fixtures/semantic-adopted-policy-v1/execution-corpus.json";NODE=ROOT/"tests/verify_semantic_adopted_execution.mjs"
def mutate(base,ops):
 v=copy.deepcopy(base)
 for op in ops:
  x=v;parts=op["path"].split("/")
  for token in parts[:-1]:x=x[int(token)] if isinstance(x,list) else x[token]
  x[int(parts[-1]) if isinstance(x,list) else parts[-1]]=copy.deepcopy(op["value"])
 return v
class ActualAdoptedExecutionTests(unittest.TestCase):
 @classmethod
 def git(cls,root,*args):
  env={**os.environ,"GIT_AUTHOR_NAME":"Synthetic","GIT_AUTHOR_EMAIL":"s@example.invalid","GIT_COMMITTER_NAME":"Synthetic","GIT_COMMITTER_EMAIL":"s@example.invalid","GIT_AUTHOR_DATE":"2030-01-01T00:00:00Z","GIT_COMMITTER_DATE":"2030-01-01T00:00:00Z"}
  return subprocess.run(["git",*args],cwd=root,env=env,check=True,stdout=subprocess.PIPE).stdout.strip().decode()
 @classmethod
 def real_candidate_support(cls,raw):
  fixture=raw["candidate_verification"];candidate=raw["candidate"];root=pathlib.Path(cls.temp.name);cls.git(root,"init","-q")
  inventory=fixture["inventory_source_bytes_utf8"].encode();ip=candidate["ontology_inventory_path"];source=fixture["source_text"].encode();sp="synthetic-authority/meaning.txt"
  (root/ip).parent.mkdir(parents=True);(root/ip).write_bytes(inventory);cls.git(root,"add",".");cls.git(root,"commit","-qm","inventory");I=cls.git(root,"rev-parse","HEAD")
  cls.git(root,"checkout","--orphan","source","-q");cls.git(root,"rm","-rf",".");(root/sp).parent.mkdir(parents=True,exist_ok=True);(root/sp).write_bytes(source);cls.git(root,"add",".");cls.git(root,"commit","-qm","source")
  policy=jcs_bytes(fixture["policy"]);provenance=jcs_bytes(fixture["provenance"]);(root/candidate["policy_path"]).parent.mkdir(parents=True,exist_ok=True);(root/candidate["policy_path"]).write_bytes(policy);(root/candidate["provenance_path"]).write_bytes(provenance);cls.git(root,"add",".");cls.git(root,"commit","-qm","policy");cls.git(root,"merge","--allow-unrelated-histories","--no-ff","-qm","candidate",I)

  if cls.git(root,"rev-parse","HEAD")!=candidate["owner_git_commit"] or candidate["owner_git_commit"]==candidate["ontology_inventory"]["owner_git_commit"]:raise AssertionError("deterministic I/C coordinates differ")
  source_bytes={(row["source_revision"],row["source_path"]):source for row in fixture["provenance"]["records"]}
  return verify_candidate_support(jcs_bytes(candidate),policy_bytes=policy,provenance_bytes=provenance,inventory_source_bytes=inventory,source_bytes=source_bytes,custody_readiness_subject=raw["custody_readiness_subject"],custody_readiness_receipt=raw["custody_readiness_receipt"],custody_readiness_request=raw["custody_readiness_request"],contamination_manifest=fixture["contamination_manifest"],contamination_source_digests=fixture["contamination_non_policy_source_digests"],local_git_root=root)
 @classmethod
 def setUpClass(cls):
  cls.corpus=json.loads(CORPUS.read_text());cls.temp=tempfile.TemporaryDirectory();raw=cls.corpus["support"];verified=cls.real_candidate_support(raw);cls.support=ExecutionGraphSupport(verified,tuple(raw["participant_credentials"]),raw["custody_readiness_subject"],raw["custody_readiness_receipt"],raw["custody_readiness_request"]);cls.base=next(c["bundle"] for c in cls.corpus["cases"] if c["name"]=="branch_7_valid")
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def bundle(self,c):return c.get("bundle") or mutate(self.base,c["operations"])
 def verify(self,c,support=None):return verify_execution_bundle(self.bundle(c),support=support or self.support,trusted_now=c.get("trusted_now",self.corpus["trusted_now"]))
 def test_r14_public_corpus_and_closed_results(self):
  self.assertEqual(self.corpus["schema"],"semantic-adopted-execution-corpus.r14");self.assertEqual(self.corpus["support"]["custody_readiness_subject"]["concept_inventory"],self.corpus["support"]["candidate"]["ontology_inventory"])
  raw=CORPUS.read_bytes();patterns=(b"BEGIN PRIVATE KEY",b'"private_key"',b"private_key_base64",hashlib.sha256(b"authority-test-only-private-seed").digest(),hashlib.sha256(b"corpus-only-signing-seed").digest())
  for pattern in patterns:self.assertNotIn(pattern,raw)
  observed=set()
  for c in self.corpus["cases"]:
   with self.subTest(c=c["name"]):
    before=copy.deepcopy(self.bundle(c));actual=self.verify(c);self.assertEqual(actual,tuple(c["expected_error_kinds"]));self.assertEqual(before,self.bundle(c));self.assertTrue(set(actual)<=set(ERROR_KINDS));observed.update(actual)
  self.assertTrue({"schema_invalid","digest_mismatch","signature_invalid","authority_invalid","ordering_invalid"}<=observed)
 def test_eight_real_graph_branches_fail_outcome_and_idempotence(self):
  by={c["name"]:c for c in self.corpus["cases"]};ids=set()
  for n in range(8):
   b=by[f"branch_{n}_valid"]["bundle"];self.assertFalse(validate_protocol(b["attempt"]));self.assertFalse(validate_protocol(b["verdict"]));self.assertTrue(verify_execution_graph(b,self.support).consistency_verified);self.assertEqual(self.verify(by[f"branch_{n}_valid"]),());self.assertEqual(self.verify(by[f"branch_{n}_valid"]),());ids.add((b["attempt"]["attempt_id"],b["verdict"]["attempt_envelope"]["process_reservation"]["reservation_id"]))
  self.assertEqual(len(ids),8);self.assertEqual(by["completed_fail_valid"]["bundle"]["verdict"]["outcome"],"fail");self.assertEqual(self.verify(by["completed_fail_valid"]),())
 def test_exact_preimages_histories_contamination_and_lifecycle(self):
  o=extract_execution_graph(self.base,self.support);self.assertEqual(tuple(len(o[x]["events"]) for x in ("base_access_history","activated_access_history","terminal_access_history")),(12,13,14));self.assertEqual(sum(x["b0_exposure"]=="disproven" for x in o["preregistration"]["participants"]),11);self.assertEqual(o["execution_contamination_subject"]["source_digest"],o["attempt_envelope"]["envelope_digest"])
  g=o["activated_access_history"]["events"][-1];r=o["terminal_access_history"]["events"][-1];self.assertEqual(g["occurred_at"],o["activation_subject"]["issued_at"]);self.assertEqual(r["occurred_at"],o["closure_subject"]["closed_at"])
  times=[o["launch_subject"]["launch_authorized_at"],o["closure_subject"]["process_spawned_at"],o["handoff_subject"]["handed_off_at"],o["closure_subject"]["process_terminated_at"],o["closure_subject"]["descriptor_access_closed_at"],o["closure_subject"]["closed_at"]];self.assertEqual(times,sorted(times));self.assertLessEqual(o["handoff_subject"]["descriptor_access_expires_at"],o["activation_subject"]["expires_at"])
 def test_support_and_protocol_attacks(self):
  by={c["name"]:c for c in self.corpus["cases"]}
  for name in ("stale_signature_after_subject_mutation","wrong_approval_key","wrong_approval_purpose","expired_caller_time","wrong_signer","direct_descriptor_transfer","retry_forbidden","rerun_forbidden","retained_process","retained_descriptor_handle","excess_grant","b0_ten_not_plus_one","fake_history"):
   with self.subTest(name=name):self.assertTrue(self.verify(by[name]))
  for field, key in (("custody_readiness_subject", "subject_digest"), ("custody_readiness_receipt", "readiness_digest"), ("custody_readiness_request", "request_digest")):
   with self.subTest(support_preimage=field):
    changed=copy.deepcopy(getattr(self.support,field));changed[key]="sha256:"+"9"*64;bad=dataclasses.replace(self.support,**{field:changed});self.assertEqual(verify_execution_bundle(self.base,support=bad,trusted_now=self.corpus["trusted_now"]),("nested_mismatch",))
  substituted=dataclasses.replace(self.support.candidate_support,candidate_digest="sha256:"+"9"*64);bad_candidate=dataclasses.replace(self.support,candidate_support=substituted);self.assertEqual(verify_execution_bundle(self.base,support=bad_candidate,trusted_now=self.corpus["trusted_now"]),("digest_mismatch",))
 def test_node_byte_identical(self):
  results=[execution_verification_result(self.bundle(c),support=self.support,trusted_now=c.get("trusted_now",self.corpus["trusted_now"])) for c in self.corpus["cases"]];done=subprocess.run(["node",str(NODE)],cwd=ROOT,check=True,capture_output=True);self.assertEqual(done.stderr,b"");self.assertEqual(done.stdout,jcs_bytes(results)+b"\n")
if __name__=="__main__":unittest.main()
