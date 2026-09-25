from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from rocs_cli.wave1 import cleanup


class CleanupScopeTests(unittest.TestCase):
    def _write(self, path: Path, text: str = "x\n") -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, "utf-8")

    def test_nested_layout_never_touches_project_root_dist(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._write(repo / "ontology/manifest.yaml", "rocs:\n  layers:\n    - name: repo\n      path: ontology/src\n")
            self._write(repo / "ontology/dist/summary.json")
            self._write(repo / "ontology/dist/authority-receipt.json")
            self._write(repo / "ontology/dist/.authority-receipt.lock", "")
            self._write(repo / "dist/app.js", "console.log(1)\n")
            self._write(repo / "dist/summary.json", "{}\n")
            result = cleanup(repo)
            self.assertEqual(sorted(result["removed"]), [
                "ontology/dist/.authority-receipt.lock",
                "ontology/dist/authority-receipt.json",
                "ontology/dist/summary.json",
            ])
            self.assertEqual(result["retained"], [])
            self.assertFalse((repo / "ontology/dist").exists())
            self.assertEqual((repo / "dist/app.js").read_text("utf-8"), "console.log(1)\n")
            self.assertTrue((repo / "dist/summary.json").is_file())

    def test_unknown_files_in_managed_dist_are_retained(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._write(repo / "ontology/manifest.yaml", "rocs:\n  layers:\n    - name: repo\n      path: ontology/src\n")
            self._write(repo / "ontology/dist/id_index.json")
            self._write(repo / "ontology/dist/notes.md")
            result = cleanup(repo)
            self.assertEqual(result["removed"], ["ontology/dist/id_index.json"])
            self.assertEqual(result["retained"], ["ontology/dist/notes.md"])
            self.assertTrue((repo / "ontology/dist/notes.md").is_file())

    def test_root_layout_cleans_root_dist_managed_outputs_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._write(repo / "manifest.yaml", "rocs:\n  layers:\n    - name: repo\n      path: src\n")
            self._write(repo / "dist/resolve.json")
            self._write(repo / "dist/keep.txt")
            result = cleanup(repo)
            self.assertEqual(result["removed"], ["dist/resolve.json"])
            self.assertEqual(result["retained"], ["dist/keep.txt"])

    def test_dry_run_removes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._write(repo / "ontology/manifest.yaml", "rocs:\n  layers:\n    - name: repo\n      path: ontology/src\n")
            self._write(repo / "ontology/dist/summary.json")
            result = cleanup(repo, dry_run=True)
            self.assertEqual(result["removed"], ["ontology/dist/summary.json"])
            self.assertTrue((repo / "ontology/dist/summary.json").is_file())


if __name__ == "__main__":
    unittest.main()
