from _cli_support import *  # noqa: F403
from _cli_support import _mk_repo, _parse_json, _run, _run_capture, _write

class TestProposalCliArtifactMembrane(unittest.TestCase):
    def test_capsule_validate_compile_and_adversarial_sinks_leave_sources_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            ontology = base / "ontology"; ontology.mkdir()
            _write(ontology / "local.md", "local\n")
            _write(ontology / "upstream.md", "ref\n")
            artifact = base / "artifacts"; artifact.mkdir()
            capsule = artifact / "capsule.json"
            proposal_path = base / "proposal.json"
            source_before_context = {p.name: p.read_bytes() for p in ontology.iterdir() if p.is_file()}
            self.assertEqual(_run(["context", "create", "--root", str(ontology),
                "--input", "path:local.md", "--input", "ref:upstream.md",
                "--artifact-root", str(artifact), "--out", "capsule.json"]), 0)
            self.assertEqual({p.name: p.read_bytes() for p in ontology.iterdir() if p.is_file()}, source_before_context)
            self.assertNotEqual(_run(["context", "create", "--root", str(ontology),
                "--input", "path:local.md", "--artifact-root", str(ontology), "--out", "local.md"]), 0)
            cap = json.loads(capsule.read_text("utf-8"))
            proposal = {
                "schema_version": 1, "capsule_digest": cap["capsule_digest"], "registry_version": 1,
                "capabilities": ["ontology.propose.write", "ontology.read"],
                "read_paths": ["local.md", "upstream.md"], "write_paths": ["local.md"],
                "authority_requirement": {"kind": "human", "approval_required": True},
                "verifier": {"kind": "rocs-cli", "id": "ontology.validate.v1"},
                "rollback": {"kind": "restore", "paths": ["local.md"]},
                "operations": [{"op": "replace_text", "path": "local.md", "content": "proposed\n"}],
            }
            proposal_path.write_text(json.dumps(proposal), "utf-8")
            code, output = _run_capture(["proposal", "validate", "--capsule", str(capsule),
                                         "--proposal", str(proposal_path)])
            self.assertEqual(code, 0)
            digest = json.loads(output)["proposal_digest"]
            approval = artifact / "approval.json"
            approval.write_text(json.dumps({"schema_version": 1, "proposal_digest": digest,
                "approved": True, "approver": "operator:test"}), "utf-8")
            compile_base = ["proposal", "compile", "--capsule", str(capsule),
                "--proposal", str(proposal_path), "--approval", str(approval),
                "--ontology-root", str(ontology), "--artifact-root", str(artifact)]
            before = {p.relative_to(ontology): p.read_bytes() for p in ontology.rglob("*") if p.is_file()}
            self.assertEqual(_run(compile_base + ["--out", "plans/plan.json"]), 0)
            self.assertTrue((artifact / "plans/plan.json").is_file())

            (artifact / "linked").symlink_to(ontology, target_is_directory=True)
            (artifact / "hard-plan.json").hardlink_to(ontology / "local.md")
            hostile = [
                (compile_base, "/tmp/absolute-plan.json"),
                (compile_base, "../escape.json"),
                (compile_base, "local.md"),  # capsule path-layer collision
                (compile_base, "upstream.md"),  # capsule ref-layer collision
                (compile_base, "approval.json"),  # existing CLI input collision
                (compile_base, "linked/plan.json"),
                (compile_base, "hard-plan.json"),
                (compile_base[:-2] + ["--artifact-root", str(ontology)], "plan.json"),
            ]
            for command, out in hostile:
                with self.subTest(out=out):
                    self.assertNotEqual(_run(command + ["--out", out]), 0)
            after = {p.relative_to(ontology): p.read_bytes() for p in ontology.rglob("*") if p.is_file()}
            self.assertEqual(after, before)

    def test_module_cli_dogfoods_valid_and_hardlink_hostile_sinks(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); ontology = base / "ontology"; artifacts = base / "artifacts"
            ontology.mkdir(); artifacts.mkdir(); _write(ontology / "local.md", "local\n")
            run = lambda args: subprocess.run(
                [sys.executable, "-m", "rocs_cli", *args], cwd=Path(__file__).resolve().parents[1],
                text=True, capture_output=True,
            )
            source_before = (ontology / "local.md").read_bytes()
            (artifacts / "hard-capsule.json").hardlink_to(ontology / "local.md")
            hostile_context = run(["context", "create", "--root", str(ontology), "--input", "path:local.md",
                                   "--artifact-root", str(artifacts), "--out", "hard-capsule.json"])
            self.assertNotEqual(hostile_context.returncode, 0)
            self.assertEqual((ontology / "local.md").read_bytes(), source_before)
            result = run(["context", "create", "--root", str(ontology), "--input", "path:local.md",
                          "--artifact-root", str(artifacts), "--out", "capsule.json"])
            self.assertEqual(result.returncode, 0, result.stderr)
            cap = json.loads((artifacts / "capsule.json").read_text("utf-8"))
            proposal = {
                "schema_version": 1, "capsule_digest": cap["capsule_digest"], "registry_version": 1,
                "capabilities": ["ontology.propose.write", "ontology.read"],
                "read_paths": ["local.md"], "write_paths": ["local.md"],
                "authority_requirement": {"kind": "human", "approval_required": True},
                "verifier": {"kind": "rocs-cli", "id": "ontology.validate.v1"},
                "rollback": {"kind": "restore", "paths": ["local.md"]},
                "operations": [{"op": "replace_text", "path": "local.md", "content": "proposal\n"}],
            }
            proposal_path = base / "proposal.json"; proposal_path.write_text(json.dumps(proposal), "utf-8")
            validated = run(["proposal", "validate", "--capsule", str(artifacts / "capsule.json"),
                             "--proposal", str(proposal_path)])
            self.assertEqual(validated.returncode, 0, validated.stderr)
            digest = json.loads(validated.stdout)["proposal_digest"]
            approval = base / "approval.json"
            approval.write_text(json.dumps({"schema_version": 1, "proposal_digest": digest,
                                            "approved": True, "approver": "operator:dogfood"}), "utf-8")
            common = ["proposal", "compile", "--capsule", str(artifacts / "capsule.json"),
                      "--proposal", str(proposal_path), "--approval", str(approval),
                      "--ontology-root", str(ontology), "--artifact-root", str(artifacts)]
            before = (ontology / "local.md").read_bytes()
            duplicate_approval = base / "duplicate-approval.json"
            duplicate_approval.write_text(
                '{"schema_version":1,"proposal_digest":"' + digest +
                '","approved":false,"approved":true,"approver":"operator:dogfood"}', "utf-8")
            duplicate_command = list(common)
            duplicate_command[duplicate_command.index(str(approval))] = str(duplicate_approval)
            duplicate = run(duplicate_command + ["--out", "duplicate-plan.json"])
            self.assertNotEqual(duplicate.returncode, 0)
            self.assertFalse((artifacts / "duplicate-plan.json").exists())
            self.assertEqual((ontology / "local.md").read_bytes(), before)
            (artifacts / "hard.json").hardlink_to(ontology / "local.md")
            rejected = run(common + ["--out", "hard.json"])
            self.assertNotEqual(rejected.returncode, 0)
            self.assertEqual((ontology / "local.md").read_bytes(), before)
            accepted = run(common + ["--out", "plan.json"])
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            self.assertEqual((ontology / "local.md").read_bytes(), before)
