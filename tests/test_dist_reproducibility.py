from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from _cli_support import _mk_repo, _parse_json, _run_capture
from rocs_cli import authority, cli_ontology_lifecycle, cli_support
from rocs_cli.cli_support import _write_resolve_artifact
from rocs_cli.layers import LayerSpec, dist_dir
from test_workspace_resolution import _git, _init_workspace_repo


TRACKED = ("resolve.json", "summary.json", "id_index.json")


class DistReproducibilityTests(unittest.TestCase):
    def test_root_layout_clones_emit_identical_tracked_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = _mk_repo(root / "first", layout="root")
            second = _mk_repo(root / "second", layout="root")
            self.assertEqual(self.build(first), self.build(second))
            self.assertEqual(json.loads((first / "dist/resolve.json").read_text())["layers"][0]["origin"], "src")

    def test_output_root_location_does_not_enter_tracked_projection(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            original = self.build(repo)
            with patch.dict(os.environ, {"ROCS_OUTPUT_ROOT": "governance/ontology-output"}):
                self.assertEqual(original, self.build(repo))
                receipt = json.loads((dist_dir(repo) / "authority-receipt.build.json").read_text())
                self.assertEqual(receipt["output_root"], "governance/ontology-output")

    def test_actual_strict_workspace_to_snapshot_binding_preserves_projection(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            workspace = root / "workspace"
            dependency = workspace / "core/dependency"
            concept = dependency / "ontology/src/reference/concepts/dep.Example.md"
            concept.parent.mkdir(parents=True)
            concept.write_text("---\nont:\n  id: dep.Example\n  type: concept\n  labels: [Example]\n  description: Synthetic dependency concept for artifact regression.\n  relations: []\n---\n")
            _init_workspace_repo(dependency, project_path="core/dependency", tag="v1.2.3", make_mismatch=False)
            repo = _mk_repo(root / "consumer", manifest_extra=(
                "  depends_on:\n    - layer: dependency\n      ref: '<repo:core/dependency@v1.2.3>'"
            ))
            args = ["build", "--repo", str(repo), "--resolve-refs", "--workspace-root", str(workspace),
                    "--workspace-ref-mode", "strict", "--json"]
            with patch.dict(os.environ, {"ROCS_CACHE_DIR": str(root / "cache")}):
                code, output = _run_capture(args)
                self.assertEqual(code, 0, output)
                before = {name: (dist_dir(repo) / name).read_bytes() for name in TRACKED}
                self.assertIn("dep.Example", json.loads(before["summary.json"])["concept_ids"])
                self.assertTrue(any(item["id"] == "dep.Example" for item in json.loads(before["id_index.json"])["items"]))
                receipt = json.loads((dist_dir(repo) / "authority-receipt.build.json").read_text())
                old_layer = next(layer for layer in receipt["layer_sources"] if layer["kind"] == "ref")
                self.assertEqual(old_layer["source"], "workspace")
                (dependency / ".gitignore").write_text("ontology/src/local-only.yaml\n")
                _git(dependency, ["add", ".gitignore"])
                _git(dependency, ["commit", "-m", "ignore local-only YAML"])
                (dependency / "ontology/src/local-only.yaml").write_text("local: '<placeholder>'\n")
                code, output = _run_capture(args)
                self.assertEqual(code, 0, output)
                after = {name: (dist_dir(repo) / name).read_bytes() for name in TRACKED}
                self.assertEqual(before, after)
                receipt = json.loads((dist_dir(repo) / "authority-receipt.build.json").read_text())
                new_layer = next(layer for layer in receipt["layer_sources"] if layer["kind"] == "ref")
                self.assertEqual(new_layer["source"], "workspace_ref_snapshot")
                self.assertNotEqual(old_layer["src_root"], new_layer["src_root"])
                self.assertEqual(old_layer["binding"], new_layer["binding"])

    def build(self, repo: Path) -> dict[str, bytes]:
        code, output = _run_capture(["build", "--repo", str(repo), "--json"])
        self.assertEqual(code, 0, output)
        return {name: (dist_dir(repo) / name).read_bytes() for name in TRACKED}

    def test_same_inputs_in_different_clone_paths_emit_identical_tracked_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = _mk_repo(root / "first-clone")
            second = _mk_repo(root / "another-checkout")
            self.assertEqual(self.build(first), self.build(second))
            for repo in (first, second):
                receipt = json.loads((repo / "ontology/dist/authority-receipt.build.json").read_text())
                self.assertEqual(receipt["repo"], str(repo.resolve()))
                self.assertEqual(receipt["layer_sources"][0]["src_root"], str((repo / "ontology/src").resolve()))

    def test_tool_version_is_receipt_provenance_not_tracked_projection_input(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            first = self.build(repo)
            with patch.object(authority, "__version__", "99.88.77"), \
                 patch.object(cli_support, "__version__", "99.88.77", create=True), \
                 patch.object(cli_ontology_lifecycle, "__version__", "99.88.77", create=True):
                second = self.build(repo)
            self.assertEqual(first, second)
            receipt = json.loads((repo / "ontology/dist/authority-receipt.build.json").read_text())
            self.assertEqual(receipt["version"], "99.88.77")

    def test_new_artifact_schemas_omit_runtime_fields_but_keep_index_contract(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            artifacts = {name: json.loads(raw) for name, raw in self.build(repo).items()}
            resolve = artifacts["resolve.json"]
            self.assertEqual(resolve["schema_version"], 3)
            self.assertEqual(set(resolve), {"schema_version", "profile", "layers"})
            self.assertEqual(set(resolve["layers"][0]), {"name", "kind", "origin", "source_contract"})
            summary = artifacts["summary.json"]
            self.assertEqual(summary["schema_version"], 2)
            self.assertNotIn("repo", summary)
            self.assertNotIn("version", summary)
            self.assertIn("core.Agent", summary["concept_ids"])
            index = artifacts["id_index.json"]
            self.assertEqual(index["schema_version"], 1)
            self.assertTrue(all(not Path(item["path_in_layer"]).is_absolute() for item in index["items"]))

    def test_workspace_checkout_and_exact_tree_snapshot_are_not_projection_fields(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo = _mk_repo(root / "consumer")
            origin = "<repo:core/dependency@v1.2.3>"
            first = LayerSpec(name="dependency", src_root=root / "workspace/ontology/src",
                              origin=origin, kind="ref", source="workspace")
            second = LayerSpec(name="dependency", src_root=root / "cache/tree-key/ontology/src",
                               origin=origin, kind="ref", source="workspace_ref_snapshot")
            out = _write_resolve_artifact(repo, layers=[first], profile=None)
            before = out.read_bytes()
            _write_resolve_artifact(repo, layers=[second], profile=None)
            self.assertEqual(before, out.read_bytes())
            for layer in (first, second):
                receipt = authority.authority_receipt_payload(
                    repo, command="build", ok=True, profile=None, resolve_refs_requested=True,
                    workspace_ref_mode="strict", layers=[layer],
                )
                self.assertEqual(receipt["layer_sources"][0]["source"], layer.source)
                self.assertEqual(receipt["layer_sources"][0]["src_root"], str(layer.src_root))

    def test_resolve_write_dist_keeps_ordinary_cli_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            code, output = _run_capture(["resolve", "--repo", str(repo), "--write-dist", "--json"])
            self.assertEqual(code, 0, output)
            runtime = _parse_json(output)
            self.assertEqual(runtime["repo"], str(repo.resolve()))
            self.assertEqual(runtime["layers"][0]["source"], "path")
            self.assertEqual(runtime["layers"][0]["src_root"], str((repo / "ontology/src").resolve()))
            persisted = json.loads((repo / "ontology/dist/resolve.json").read_text())
            self.assertEqual(persisted["schema_version"], 3)
            self.assertNotIn("repo", persisted)
            self.assertNotIn("src_root", persisted["layers"][0])


if __name__ == "__main__":
    unittest.main()
