from __future__ import annotations
import io, json, subprocess, sys, tempfile, unittest
from pathlib import Path
from rocs_cli.constitution import ConstitutionError, challenge_candidate, digest, differential, evaluate, generate_mutants, pareto_frontier, strict_json_load, validate_candidate


def evidence(name="ev-1"):
    r={"evidence_id":name,"status":"unverified_claim","provenance_locator":f"test://{name}","payload":{"claim":name},"evidence_digest":""}; r["evidence_digest"]=digest(r,"evidence_digest"); return r

def candidate(name="rule-1", value=True):
    ev=evidence(name+"-ev")
    fixtures={
      "positive_fixtures":[{"fixture_id":name+"-positive","subject":{"safe":True},"must_match":True}],
      "negative_fixtures":[{"fixture_id":name+"-negative","subject":{"safe":False},"must_not_match":True}],
      "adversarial_counterexamples":[{"fixture_id":name+"-counter","subject":{"safe":"True"},"counterexample_must_not_match":True}],
      "false_positive_challenges":[{"fixture_id":name+"-fp","subject":{"safe":0},"acceptable_must_not_match":True}],}
    p={"schema_version":1,"candidate_id":name,"owner":"owner:rocs","adoption_scope":["repo:a"],"rationale":"Reject unsafe records","predicate":{"op":"eq","args":[{"op":"get","path":"safe"},{"op":"literal","value":value}]},**fixtures,"severity":"error","suppression_policy":"none","evidence_digests":[ev["evidence_digest"]],"evidence_manifest":[ev],"candidate_digest":""}
    p["candidate_digest"]=digest(p,"candidate_digest"); return p

def subjects(items):
    p={"schema_version":1,"subjects":sorted(items,key=lambda x:json.dumps(x,sort_keys=True,separators=(",",":"))),"subjects_digest":""}; p["subjects_digest"]=digest(p,"subjects_digest"); return p

def contract():
    c={"schema_version":1,"contract_id":"contract-1","capabilities":["read"],"operations":["observe"],"contract_digest":""}; c["contract_digest"]=digest(c,"contract_digest"); return c

def acceptance(c):
    a={"schema_version":1,"acceptance_id":"acceptance-1","generation_id":"generation-1","nonce":"nonce-1","actor_type":"operator","actor_id":"operator:alice","assertion":"accepted-for-mutation-testing","contract_digest":c["contract_digest"],"acceptance_digest":""}; a["acceptance_digest"]=digest(a,"acceptance_digest"); return a

def corpus():
    p={"schema_version":1,"generation_id":"generation-1","acceptance_nonce":"nonce-1","consumed_acceptance_digests":[],"tests":[{"test_id":"read-test","required_capabilities":["read"],"required_operations":[],"ambiguous_capabilities":[],"ambiguous_operations":["observe"]}],"corpus_digest":""}; p["corpus_digest"]=digest(p,"corpus_digest"); return p

class ConstitutionTests(unittest.TestCase):
    def test_candidate_challenge_and_positional_differential(self):
        p=candidate(); result=validate_candidate(p)
        self.assertTrue(result["schema_conformant"]); self.assertTrue(result["fixtures_consistent"]); self.assertFalse(result["certifies_validity"]); self.assertNotIn("valid",result)
        d=differential(p,p,subjects([{"safe":True},{"safe":False}]))
        self.assertEqual(p["candidate_digest"],d["candidate_a_digest"]); self.assertEqual([],d["differences"]); self.assertFalse(challenge_candidate(p)["certifies_validity"])

    def test_plain_json_exact_types_budgets_and_global_identities_fail_closed(self):
        self.assertFalse(evaluate({"op":"eq","args":[{"op":"literal","value":True},{"op":"literal","value":1}]},{}))
        with self.assertRaises(ConstitutionError): evaluate({"op":"literal","value":object()}, {})
        with self.assertRaises(ConstitutionError): strict_json_load(io.StringIO('{"x":1,"x":2}'))
        with self.assertRaises(ConstitutionError): strict_json_load(io.StringIO('"' + 'x' * 300000 + '"'))
        with self.assertRaises(ConstitutionError): strict_json_load(io.StringIO('[' * 1000 + '0' + ']' * 1000))
        with self.assertRaises(ConstitutionError): evaluate({"op":"literal","value":"x"*20000},{})
        p=candidate(); p["negative_fixtures"][0]["fixture_id"]=p["positive_fixtures"][0]["fixture_id"]; p["candidate_digest"]=digest(p,"candidate_digest")
        with self.assertRaises(ConstitutionError): validate_candidate(p)

    def test_mutants_require_separate_exact_operator_acceptance_and_closed_corpus(self):
        c=contract(); a=acceptance(c); result=generate_mutants(c,a,corpus())
        self.assertEqual(["killed","spec-ambiguous"],[m["classification"] for m in result["mutants"]]); self.assertFalse(result["installed"])
        self.assertTrue(all(m["mutated_contract_digest"]==m["mutated_contract"]["contract_digest"] for m in result["mutants"]))
        cp=corpus(); cp["tests"][0]["ambiguous_operations"]=[]; cp["corpus_digest"]=digest(cp,"corpus_digest"); self.assertEqual("survived",generate_mutants(c,a,cp)["mutants"][1]["classification"])
        replay=corpus(); replay["consumed_acceptance_digests"]=[a["acceptance_digest"]]; replay["corpus_digest"]=digest(replay,"corpus_digest")
        with self.assertRaises(ConstitutionError): generate_mutants(c,a,replay)
        baseline_bad=corpus(); baseline_bad["tests"][0]["required_capabilities"]=["absent-from-baseline"]; baseline_bad["corpus_digest"]=digest(baseline_bad,"corpus_digest")
        with self.assertRaises(ConstitutionError): generate_mutants(c,a,baseline_bad)
        for field,value in (("actor_type","model"),("actor_id","model:fake-operator"),("actor_id","acceptance-1"),("contract_digest","sha256:"+"0"*64)):
            bad=acceptance(c); bad[field]=value; bad["acceptance_digest"]=digest(bad,"acceptance_digest")
            with self.assertRaises(ConstitutionError): generate_mutants(c,bad,corpus())

    def test_pareto_does_not_reward_claim_count_and_binds_market(self):
        ev1,ev2=evidence("ev-a"),evidence("ev-b"); manifest=sorted([ev1,ev2],key=lambda x:x["evidence_digest"])
        def bid(name, claims):
            b={"schema_version":1,"bid_id":name,"proposer":"model:data-only","plan":{"summary":name,"steps":["step"],"affected_repositories":["repo:a"],"verification_commands":["test"],"rollback_steps":["revert"]},"mutation_radius":1,"owner_crossings":0,"rollback_cost":1,"verification_cost":1,"maintenance_burden":1,"convergence_evidence_digests":sorted(claims),"bid_digest":""}; b["bid_digest"]=digest(b,"bid_digest"); return b
        bids=sorted([bid("a",[ev1["evidence_digest"]]),bid("b",[ev1["evidence_digest"],ev2["evidence_digest"]])],key=lambda x:x["bid_digest"])
        m={"schema_version":1,"market_id":"m","metric_definition":{"name":"repair-cost","version":"1","metrics":["mutation_radius","owner_crossings","rollback_cost","verification_cost","maintenance_burden"]},"evidence_manifest":manifest,"bids":bids,"market_digest":""}; m["market_digest"]=digest(m,"market_digest")
        out=pareto_frontier(m); self.assertEqual(2,len(out["pareto_frontier"])); self.assertEqual([b["bid_digest"] for b in bids],out["bid_digests"]); self.assertIsNone(out["winner"])

    def test_real_cli_duplicate_abbreviation_nonconformance_and_no_mutation(self):
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); (base / ".ignored").mkdir(); (base / ".ignored/sentinel").write_bytes(b"protected")
            p=candidate(); c=contract(); ev=evidence("market-ev")
            plan={"summary":"repair","steps":["step"],"affected_repositories":["repo:a"],"verification_commands":["test"],"rollback_steps":["revert"]}
            bid={"schema_version":1,"bid_id":"bid-1","proposer":"operator:alice","plan":plan,"mutation_radius":1,"owner_crossings":0,"rollback_cost":1,"verification_cost":1,"maintenance_burden":1,"convergence_evidence_digests":[ev["evidence_digest"]],"bid_digest":""}; bid["bid_digest"]=digest(bid,"bid_digest")
            market={"schema_version":1,"market_id":"market-1","metric_definition":{"name":"repair-cost","version":"1","metrics":["mutation_radius","owner_crossings","rollback_cost","verification_cost","maintenance_burden"]},"evidence_manifest":[ev],"bids":[bid],"market_digest":""}; market["market_digest"]=digest(market,"market_digest")
            bad=candidate(); bad["positive_fixtures"][0]["subject"]={"safe":False}; bad["candidate_digest"]=digest(bad,"candidate_digest")
            values={"candidate.json":p,"other.json":p,"subjects.json":subjects([{"safe":False},{"safe":True}]),"contract.json":c,"acceptance.json":acceptance(c),"corpus.json":corpus(),"market.json":market,"inconsistent.json":bad}
            for name,value in values.items(): (base/name).write_text(json.dumps(value),"utf-8")
            (base/"duplicate.json").write_text('{"schema_version":1,"schema_version":1}',"utf-8")
            def snapshot():
                return {x.relative_to(base).as_posix():("link",x.readlink().as_posix()) if x.is_symlink() else ("file",x.read_bytes()) if x.is_file() else ("dir",None) for x in sorted(base.rglob("*"))}
            before=snapshot(); env={**__import__('os').environ,"PYTHONPATH":str(repo/"src"),"PYTHONDONTWRITEBYTECODE":"1"}
            def run(args): return subprocess.run([sys.executable,"-m","rocs_cli",*args],cwd=base,env=env,text=True,capture_output=True)
            path=base/"candidate.json"
            commands=[
              ["constitution","validate","--candidate",str(path)],
              ["constitution","challenge","--candidate",str(path)],
              ["constitution","differential","--candidate-a",str(path),"--candidate-b",str(base/"other.json"),"--subjects",str(base/"subjects.json")],
              ["constitution","mutate","--contract",str(base/"contract.json"),"--acceptance",str(base/"acceptance.json"),"--corpus",str(base/"corpus.json")],
              ["repair-market","--market",str(base/"market.json")],]
            for command in commands:
                result=run(command); self.assertEqual(0,result.returncode,result.stderr)
            self.assertNotEqual(0,run(["constitution","validate","--cand",str(path)]).returncode)
            duplicate=run(["constitution","validate","--candidate",str(base/"duplicate.json")]); self.assertNotEqual(0,duplicate.returncode); self.assertIn("error",json.loads(duplicate.stdout))
            repeated=run(["constitution","validate","--candidate",str(path),"--candidate",str(path)]); self.assertNotEqual(0,repeated.returncode); self.assertIn("error",json.loads(repeated.stdout))
            inconsistent=run(["constitution","validate","--candidate",str(base/"inconsistent.json")]); self.assertNotEqual(0,inconsistent.returncode)
            self.assertEqual(before,snapshot())

if __name__ == "__main__": unittest.main()
