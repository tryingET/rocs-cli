import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _cli_support import _mk_repo, _run
import rocs_cli.managed_surface as managed_surface
from rocs_cli.errors import RocsCliError
from rocs_cli.layers import dist_dir
from rocs_cli.managed_surface import (
    MANAGED_OUTPUT_LOCK,
    ROCS_OUTPUT_MARKER,
    ensure_managed_output_file,
)


class TestOutputRouting(unittest.TestCase):
    def _external_env(self) -> dict[str, str]:
        return {
            "ROCS_OUTPUT_ROOT": "governance/ontology-dist",
            "ROCS_AUTHORITY_AGGREGATE": "1",
        }

    def _fingerprint(self, root: Path) -> dict[str, bytes]:
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in sorted(root.rglob("*"))
            if path.is_file() and not path.is_symlink()
        }

    def test_validate_build_graph_and_cleanup_route_externally(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            ontology = repo / "ontology"
            legacy = ontology / "dist/legacy.txt"
            legacy.parent.mkdir()
            legacy.write_text("legacy internal output must survive override cleanup\n", "utf-8")
            source_before = self._fingerprint(ontology)
            with mock.patch.dict(os.environ, self._external_env(), clear=False):
                self.assertEqual(_run(["validate", "--repo", str(repo)]), 0)
                self.assertEqual(_run(["build", "--repo", str(repo)]), 0)
                self.assertEqual(_run(["graph", "--repo", str(repo), "--json"]), 0)
                output = repo / "governance/ontology-dist"
                expected = {
                    ROCS_OUTPUT_MARKER,
                    ".authority-receipt.lock",
                    "authority-receipt.json",
                    "authority-receipt.validate.json",
                    "authority-receipt.build.json",
                    "resolve.json",
                    "summary.json",
                    "id_index.json",
                    "graph.json",
                }
                self.assertEqual({p.name for p in output.iterdir()}, expected)
                command = json.loads((output / "authority-receipt.build.json").read_text("utf-8"))
                aggregate = json.loads((output / "authority-receipt.json").read_text("utf-8"))
                self.assertEqual(command["repo"], str(repo.resolve()))
                self.assertEqual(command["output_root"], "governance/ontology-dist")
                self.assertEqual(aggregate["output_root"], "governance/ontology-dist")
                self.assertEqual(sorted(aggregate["commands"]), ["build", "validate"])
                self.assertEqual(source_before, self._fingerprint(ontology))
                self.assertEqual(legacy.read_text("utf-8"), "legacy internal output must survive override cleanup\n")
                (output / "authority-receipt.json").write_bytes(b"\xff")
                self.assertEqual(_run(["validate", "--repo", str(repo)]), 0)
                self.assertEqual(_run(["build", "--repo", str(repo)]), 0)
                self.assertEqual(
                    sorted(json.loads((output / "authority-receipt.json").read_text("utf-8"))["commands"]),
                    ["build", "validate"],
                )

                stable_names = expected - {"graph.json"}
                first = {name: (output / name).read_bytes() for name in stable_names}
                self.assertEqual(_run(["build", "--repo", str(repo)]), 0)
                self.assertEqual(
                    first, {name: (output / name).read_bytes() for name in stable_names}
                )
                self.assertEqual(_run(["build", "--repo", str(repo), "--clean"]), 0)
                self.assertFalse((output / "authority-receipt.validate.json").exists())
                self.assertFalse((output / "graph.json").exists())
                self.assertEqual(_run(["cleanup", "--repo", str(repo)]), 0)
                self.assertEqual(
                    {path.name for path in output.iterdir()},
                    {ROCS_OUTPUT_MARKER, MANAGED_OUTPUT_LOCK},
                )
                self.assertEqual(source_before, self._fingerprint(ontology))

    def test_cleanup_uses_closed_allowlist_and_detects_race_insertions(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            with mock.patch.dict(os.environ, self._external_env(), clear=False):
                self.assertEqual(_run(["validate", "--repo", str(repo)]), 0)
                self.assertEqual(_run(["build", "--repo", str(repo)]), 0)
                output = repo / "governance/ontology-dist"
                known_before = self._fingerprint(output)

                unknown = output / "operator-owned.txt"
                unknown.write_text("KEEP\n", "utf-8")
                self.assertEqual(_run(["cleanup", "--repo", str(repo)]), 1)
                self.assertEqual(unknown.read_text("utf-8"), "KEEP\n")
                self.assertEqual(
                    known_before,
                    {key: value for key, value in self._fingerprint(output).items()
                     if key != "operator-owned.txt"},
                )
                self.assertEqual(_run(["cleanup", "--repo", str(repo), "--dry-run"]), 1)
                unknown.unlink()

                for malformed_name in (
                    ".summary.json.rocs-0-0123456789ab",
                    ".summary.json.rocs-١-0123456789ab",
                ):
                    malformed = output / malformed_name
                    malformed.write_text("KEEP\n", "utf-8")
                    self.assertEqual(_run(["cleanup", "--repo", str(repo)]), 1)
                    self.assertTrue(malformed.is_file())
                    malformed.unlink()
                orphan = output / ".summary.json.rocs-123-0123456789ab"
                orphan.write_text("owned transient\n", "utf-8")
                self.assertEqual(_run(["cleanup", "--repo", str(repo)]), 0)
                self.assertFalse(orphan.exists())
                self.assertEqual(
                    {path.name for path in output.iterdir()},
                    {ROCS_OUTPUT_MARKER, MANAGED_OUTPUT_LOCK},
                )

                self.assertEqual(_run(["validate", "--repo", str(repo)]), 0)
                before_race = self._fingerprint(output)
                real_listdir = managed_surface.os.listdir
                calls = 0

                def insert_during_preflight(descriptor: int) -> list[str]:
                    nonlocal calls
                    names = real_listdir(descriptor)
                    calls += 1
                    if calls == 1:
                        (output / "race-unknown.txt").write_text("KEEP\n", "utf-8")
                    return names

                with mock.patch.object(
                    managed_surface.os, "listdir", side_effect=insert_during_preflight
                ):
                    with self.assertRaisesRegex(RocsCliError, "unknown|changed"):
                        managed_surface.clear_managed_output_root(
                            repo, dist_dir(repo), remove_root=True
                        )
                self.assertTrue((output / "race-unknown.txt").is_file())
                self.assertEqual(
                    before_race,
                    {key: value for key, value in self._fingerprint(output).items()
                     if key != "race-unknown.txt"},
                )

    def test_cleanup_rejects_unknown_receipts_hardlinks_and_late_races(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            with mock.patch.dict(os.environ, self._external_env(), clear=False):
                self.assertEqual(_run(["build", "--repo", str(repo)]), 0)
                output = repo / "governance/ontology-dist"
                with self.assertRaisesRegex(RocsCliError, "unknown managed output"):
                    ensure_managed_output_file(
                        repo, output / "authority-receipt.operator.json", label="probe"
                    )
                with self.assertRaisesRegex(RocsCliError, "unknown managed output"):
                    ensure_managed_output_file(
                        repo, output / "nested/summary.json", label="probe"
                    )

                unknown_receipt = output / "authority-receipt.operator.json"
                unknown_receipt.write_text("KEEP\n", "utf-8")
                with mock.patch.dict(
                    os.environ, {"ROCS_AUTHORITY_AGGREGATE": ""}, clear=False
                ):
                    self.assertEqual(_run(["validate", "--repo", str(repo)]), 1)
                self.assertEqual(unknown_receipt.read_text("utf-8"), "KEEP\n")
                unknown_receipt.unlink()

                victim = repo / "ontology/src/cleanup-victim.txt"
                victim.write_text("SAFE\n", "utf-8")
                summary = output / "summary.json"
                summary.unlink()
                os.link(victim, summary)
                before = self._fingerprint(output)
                self.assertEqual(_run(["cleanup", "--repo", str(repo)]), 1)
                self.assertEqual(victim.read_text("utf-8"), "SAFE\n")
                self.assertEqual(before, self._fingerprint(output))
                summary.unlink()
                self.assertEqual(_run(["build", "--repo", str(repo)]), 0)

                real_unlink = managed_surface.os.unlink
                inserted = False

                def insert_after_delete(name: str, *args, **kwargs) -> None:
                    nonlocal inserted
                    real_unlink(name, *args, **kwargs)
                    if not inserted:
                        inserted = True
                        (output / "late-race.txt").write_text("KEEP\n", "utf-8")

                with mock.patch.object(
                    managed_surface.os, "unlink", side_effect=insert_after_delete
                ):
                    with self.assertRaisesRegex(RocsCliError, "unknown|changed"):
                        managed_surface.clear_managed_output_root(
                            repo, dist_dir(repo), remove_root=True
                        )
                self.assertTrue((output / "late-race.txt").is_file())
                self.assertEqual((output / "late-race.txt").read_text("utf-8"), "KEEP\n")

    def test_cleanup_preserves_same_name_substitutions_and_retained_identity(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            with mock.patch.dict(os.environ, self._external_env(), clear=False):
                self.assertEqual(_run(["build", "--repo", str(repo)]), 0)
                output = repo / "governance/ontology-dist"
                summary = output / "summary.json"
                original = repo / "summary.original"
                real_inventory = managed_surface._cleanup_inventory
                calls = 0

                def substitute_after_first(descriptor: int):
                    nonlocal calls
                    result = real_inventory(descriptor)
                    calls += 1
                    if calls == 1:
                        summary.rename(original)
                        summary.write_text("OPERATOR UNKNOWN\n", "utf-8")
                    return result

                with mock.patch.object(
                    managed_surface, "_cleanup_inventory", side_effect=substitute_after_first
                ):
                    with self.assertRaisesRegex(RocsCliError, "changed"):
                        managed_surface.clear_managed_output_root(
                            repo, dist_dir(repo), remove_root=True
                        )
                self.assertEqual(summary.read_text("utf-8"), "OPERATOR UNKNOWN\n")
                self.assertTrue(original.is_file())
                summary.unlink()
                original.rename(summary)

                real_rename = managed_surface._rename_noreplace
                inserted = False

                def insert_same_name(descriptor: int, source: str, target: str) -> None:
                    nonlocal inserted
                    real_rename(descriptor, source, target)
                    if not inserted:
                        inserted = True
                        (output / source).write_text("LATE UNKNOWN\n", "utf-8")

                with mock.patch.object(
                    managed_surface, "_rename_noreplace", side_effect=insert_same_name
                ):
                    with self.assertRaisesRegex(RocsCliError, "changed|private"):
                        managed_surface.clear_managed_output_root(
                            repo, dist_dir(repo), remove_root=True
                        )
                self.assertTrue(any(
                    path.read_text("utf-8") == "LATE UNKNOWN\n"
                    for path in output.iterdir() if path.is_file()
                ))

    def test_cleanup_binds_validated_marker_and_recovers_owned_quarantine(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            with mock.patch.dict(os.environ, self._external_env(), clear=False):
                self.assertEqual(_run(["build", "--repo", str(repo)]), 0)
                output = repo / "governance/ontology-dist"
                marker = output / ROCS_OUTPUT_MARKER
                valid_marker = repo / "valid-marker.json"
                before = self._fingerprint(output)
                real_read_marker = managed_surface._read_marker_at

                def replace_after_validation(root: Path, configured: Path, descriptor: int):
                    result = real_read_marker(root, configured, descriptor)
                    marker.rename(valid_marker)
                    marker.write_text("NOT A ROCS MARKER\n", "utf-8")
                    return result

                with mock.patch.object(
                    managed_surface, "_read_marker_at", side_effect=replace_after_validation
                ):
                    with self.assertRaisesRegex(RocsCliError, "marker changed"):
                        managed_surface.clear_managed_output_root(
                            repo, dist_dir(repo), remove_root=True
                        )
                self.assertEqual(
                    {key: value for key, value in before.items() if key != ROCS_OUTPUT_MARKER},
                    {key: value for key, value in self._fingerprint(output).items()
                     if key != ROCS_OUTPUT_MARKER},
                )
                marker.unlink()
                valid_marker.rename(marker)

                real_rename = managed_surface._rename_noreplace
                interrupted = False

                def interrupt_after_quarantine(descriptor: int, source: str, target: str) -> None:
                    nonlocal interrupted
                    real_rename(descriptor, source, target)
                    if not interrupted:
                        interrupted = True
                        raise KeyboardInterrupt("injected cleanup interruption")

                with mock.patch.object(
                    managed_surface, "_rename_noreplace", side_effect=interrupt_after_quarantine
                ):
                    with self.assertRaisesRegex(KeyboardInterrupt, "injected"):
                        managed_surface.clear_managed_output_root(
                            repo, dist_dir(repo), remove_root=True
                        )
                quarantines = list(output.glob(".rocs-cleanup-quarantine-*"))
                self.assertEqual(len(quarantines), 1)
                self.assertEqual(_run(["cleanup", "--repo", str(repo)]), 0)
                self.assertFalse(quarantines[0].exists())
                self.assertEqual(
                    {path.name for path in output.iterdir()},
                    {ROCS_OUTPUT_MARKER, MANAGED_OUTPUT_LOCK},
                )

    def test_external_pruner_preserves_same_name_substitution(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            with mock.patch.dict(os.environ, self._external_env(), clear=False):
                self.assertEqual(_run(["build", "--repo", str(repo)]), 0)
                output = repo / "governance/ontology-dist"
                summary = output / "summary.json"
                original = repo / "pruned-summary.original"
                real_rename = managed_surface._rename_noreplace
                substituted = False

                def substitute_before_move(descriptor: int, source: str, target: str) -> None:
                    nonlocal substituted
                    if not substituted:
                        substituted = True
                        summary.rename(original)
                        summary.write_text("PRUNER UNKNOWN\n", "utf-8")
                    real_rename(descriptor, source, target)

                with mock.patch.object(
                    managed_surface, "_rename_noreplace", side_effect=substitute_before_move
                ):
                    with self.assertRaisesRegex(RocsCliError, "changed"):
                        managed_surface.unlink_managed_output(repo, summary)
                self.assertTrue(original.is_file())
                self.assertTrue(any(
                    path.read_text("utf-8") == "PRUNER UNKNOWN\n"
                    for path in output.glob(".rocs-cleanup-quarantine-*")
                ))

    def test_default_output_is_byte_compatible_and_unmarked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            with mock.patch.dict(os.environ, {"ROCS_OUTPUT_ROOT": ""}, clear=False):
                self.assertEqual(_run(["validate", "--repo", str(repo)]), 0)
            output = repo / "ontology/dist"
            self.assertTrue((output / "authority-receipt.validate.json").is_file())
            self.assertFalse((output / ROCS_OUTPUT_MARKER).exists())
            receipt = json.loads((output / "authority-receipt.validate.json").read_text("utf-8"))
            self.assertNotIn("output_root", receipt)
            (output / "authority-receipt.json").write_bytes(b"\xff")
            with mock.patch.dict(
                os.environ,
                {"ROCS_OUTPUT_ROOT": "", "ROCS_AUTHORITY_AGGREGATE": ""},
                clear=False,
            ):
                self.assertEqual(_run(["validate", "--repo", str(repo)]), 0)
            self.assertEqual(
                json.loads((output / "authority-receipt.json").read_text("utf-8"))["last_command"],
                "validate",
            )

    def test_resolve_write_dist_routes_externally(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            with mock.patch.dict(os.environ, self._external_env(), clear=False):
                self.assertEqual(_run(["resolve", "--repo", str(repo), "--write-dist"]), 0)
            output = repo / "governance/ontology-dist"
            self.assertTrue((output / "resolve.json").is_file())
            self.assertTrue((output / ROCS_OUTPUT_MARKER).is_file())
            self.assertFalse((repo / "ontology/dist").exists())

    def test_root_layout_routes_externally_without_touching_source(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td), layout="root")
            source_before = self._fingerprint(repo / "src")
            with mock.patch.dict(os.environ, self._external_env(), clear=False):
                self.assertEqual(_run(["validate", "--repo", str(repo)]), 0)
                self.assertEqual(_run(["build", "--repo", str(repo)]), 0)
            self.assertEqual(source_before, self._fingerprint(repo / "src"))
            self.assertTrue((repo / "governance/ontology-dist/summary.json").is_file())
            self.assertFalse((repo / "dist").exists())

    def test_root_layout_rejects_output_inside_declared_local_layer(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td), layout="root")
            (repo / "src").rename(repo / "knowledge")
            (repo / "manifest.yaml").write_text(
                "rocs:\n  layers:\n    - name: knowledge\n      path: knowledge\n", "utf-8"
            )
            with mock.patch.dict(
                os.environ, {"ROCS_OUTPUT_ROOT": "knowledge/managed-dist"}, clear=False
            ):
                self.assertEqual(_run(["validate", "--repo", str(repo)]), 1)
            self.assertFalse((repo / "knowledge/managed-dist").exists())

    def test_descriptor_routing_rejects_parent_swap_before_write_and_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            with mock.patch.dict(os.environ, self._external_env(), clear=False):
                logical = dist_dir(repo)
                managed_surface.ensure_external_output_root(repo, logical)
                real_configured = managed_surface._configured_root
                governance = repo / "governance"
                backup = repo / "governance-safe"
                swapped = False

                def swap_parent(root: Path) -> Path | None:
                    nonlocal swapped
                    result = real_configured(root)
                    if not swapped:
                        governance.rename(backup)
                        governance.symlink_to(repo / "ontology", target_is_directory=True)
                        swapped = True
                    return result

                try:
                    with mock.patch.object(
                        managed_surface, "_configured_root", side_effect=swap_parent
                    ):
                        with self.assertRaises(RocsCliError):
                            managed_surface.write_managed_output_text(
                                repo, logical / "race.txt", "must not escape\n"
                            )
                    self.assertFalse((repo / "ontology/ontology-dist/race.txt").exists())
                    self.assertTrue((backup / "ontology-dist").is_dir())
                finally:
                    if governance.is_symlink():
                        governance.unlink()
                    if backup.exists():
                        backup.rename(governance)

                swapped = False
                try:
                    with mock.patch.object(
                        managed_surface, "_configured_root", side_effect=swap_parent
                    ):
                        with self.assertRaises(RocsCliError):
                            managed_surface.clear_managed_output_root(
                                repo, logical, remove_root=True
                            )
                    self.assertFalse((repo / "ontology/ontology-dist").exists())
                    self.assertTrue((backup / "ontology-dist" / ROCS_OUTPUT_MARKER).is_file())
                finally:
                    if governance.is_symlink():
                        governance.unlink()
                    if backup.exists():
                        backup.rename(governance)

    def test_final_component_symlink_and_fifo_never_redirect_writes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            victim = repo / "ontology/src/victim.txt"
            victim.write_text("SAFE\n", "utf-8")
            with mock.patch.dict(os.environ, self._external_env(), clear=False):
                output = dist_dir(repo)
                logical = ensure_managed_output_file(
                    repo, output / "summary.json", label="race probe"
                )
                logical.symlink_to(victim)
                managed_surface.write_managed_output_text(repo, logical, "REPLACED\n")
                self.assertEqual(victim.read_text("utf-8"), "SAFE\n")
                self.assertFalse(logical.is_symlink())
                self.assertEqual(logical.read_text("utf-8"), "REPLACED\n")
                logical.unlink()

                os.mkfifo(logical)
                managed_surface.write_managed_output_text(repo, logical, "REPLACED FIFO\n")
                self.assertTrue(logical.is_file())
                self.assertEqual(logical.read_text("utf-8"), "REPLACED FIFO\n")
                logical.unlink()

                os.link(victim, logical)
                managed_surface.write_managed_output_text(repo, logical, "REPLACED LINK\n")
                self.assertEqual(victim.read_text("utf-8"), "SAFE\n")
                self.assertEqual(logical.read_text("utf-8"), "REPLACED LINK\n")
                self.assertEqual(logical.stat().st_nlink, 1)
                logical.unlink()

                lock = output / ".authority-receipt.lock"
                lock.symlink_to(victim)
                self.assertEqual(_run(["validate", "--repo", str(repo)]), 1)
                self.assertEqual(victim.read_text("utf-8"), "SAFE\n")
                lock.unlink()
                os.link(victim, lock)
                self.assertEqual(_run(["validate", "--repo", str(repo)]), 1)
                self.assertEqual(victim.read_text("utf-8"), "SAFE\n")

    def test_rejects_unsafe_external_roots_without_partial_writes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            parent = Path(td)
            repo = _mk_repo(parent)
            outside = parent / "outside"
            cases = [
                "..",
                ".",
                ".git/rocs-output",
                "scripts/rocs-output",
                "ontology",
                "ontology/dist",
                str(outside),
            ]
            for value in cases:
                with self.subTest(value=value), mock.patch.dict(
                    os.environ, {"ROCS_OUTPUT_ROOT": value}, clear=False
                ):
                    self.assertEqual(_run(["validate", "--repo", str(repo)]), 1)
            self.assertFalse(outside.exists())
            self.assertFalse((repo / "ontology/dist").exists())

            absolute = repo / "governance/absolute-output"
            with mock.patch.dict(
                os.environ, {"ROCS_OUTPUT_ROOT": str(absolute)}, clear=False
            ):
                self.assertEqual(_run(["validate", "--repo", str(repo)]), 0)
                self.assertEqual(_run(["cleanup", "--repo", str(repo)]), 0)
            self.assertEqual(
                {path.name for path in absolute.iterdir()},
                {ROCS_OUTPUT_MARKER, MANAGED_OUTPUT_LOCK},
            )

            file_target = repo / "governance/output-file"
            file_target.parent.mkdir(exist_ok=True)
            file_target.write_text("keep\n", "utf-8")
            with mock.patch.dict(
                os.environ, {"ROCS_OUTPUT_ROOT": "governance/output-file"}, clear=False
            ):
                self.assertEqual(_run(["validate", "--repo", str(repo)]), 1)
            self.assertEqual(file_target.read_text("utf-8"), "keep\n")

            fifo_target = repo / "governance/output-fifo"
            os.mkfifo(fifo_target)
            with mock.patch.dict(
                os.environ, {"ROCS_OUTPUT_ROOT": "governance/output-fifo"}, clear=False
            ):
                self.assertEqual(_run(["validate", "--repo", str(repo)]), 1)
            fifo_target.unlink()

            nonempty = repo / "governance/nonempty"
            nonempty.mkdir(parents=True)
            (nonempty / "owned.txt").write_text("not ROCS\n", "utf-8")
            with mock.patch.dict(os.environ, {"ROCS_OUTPUT_ROOT": "governance/nonempty"}, clear=False):
                self.assertEqual(_run(["validate", "--repo", str(repo)]), 1)
            self.assertEqual((nonempty / "owned.txt").read_text("utf-8"), "not ROCS\n")

            marker_root = repo / "governance/marker-link"
            marker_root.mkdir()
            outside_marker = repo / "outside-marker"
            outside_marker.write_text("keep\n", "utf-8")
            (marker_root / ROCS_OUTPUT_MARKER).symlink_to(outside_marker)
            with mock.patch.dict(
                os.environ, {"ROCS_OUTPUT_ROOT": "governance/marker-link"}, clear=False
            ):
                self.assertEqual(_run(["validate", "--repo", str(repo)]), 1)
            self.assertEqual(outside_marker.read_text("utf-8"), "keep\n")
            (marker_root / ROCS_OUTPUT_MARKER).unlink()
            os.link(outside_marker, marker_root / ROCS_OUTPUT_MARKER)
            with mock.patch.dict(
                os.environ, {"ROCS_OUTPUT_ROOT": "governance/marker-link"}, clear=False
            ):
                self.assertEqual(_run(["validate", "--repo", str(repo)]), 1)
            self.assertEqual(outside_marker.read_text("utf-8"), "keep\n")

            target = repo / "governance/real"
            target.mkdir()
            link = repo / "governance/link"
            link.symlink_to(target, target_is_directory=True)
            with mock.patch.dict(os.environ, {"ROCS_OUTPUT_ROOT": "governance/link"}, clear=False):
                self.assertEqual(_run(["validate", "--repo", str(repo)]), 1)
            self.assertEqual(list(target.iterdir()), [])

    def test_cleanup_rejects_tampered_or_unmarked_external_root(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            output = repo / "governance/ontology-dist"
            output.mkdir(parents=True)
            sentinel = output / "sentinel"
            sentinel.write_text("keep\n", "utf-8")
            with mock.patch.dict(os.environ, self._external_env(), clear=False):
                self.assertEqual(_run(["cleanup", "--repo", str(repo)]), 1)
            self.assertEqual(sentinel.read_text("utf-8"), "keep\n")

            sentinel.unlink()
            with mock.patch.dict(os.environ, self._external_env(), clear=False):
                self.assertEqual(_run(["validate", "--repo", str(repo)]), 0)
            marker = output / ROCS_OUTPUT_MARKER
            payload = json.loads(marker.read_text("utf-8"))
            payload["path"] = "governance/other"
            marker.write_text(json.dumps(payload), "utf-8")
            with mock.patch.dict(os.environ, self._external_env(), clear=False):
                self.assertEqual(_run(["cleanup", "--repo", str(repo)]), 1)
            self.assertTrue(output.exists())
