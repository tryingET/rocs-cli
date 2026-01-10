import tempfile
import unittest
import io
from pathlib import Path

from rich.console import Console

from rocs_cli import __main__ as cli
import rocs_cli.cli as cli_mod


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, "utf-8")


def _mk_repo(tmp: Path, *, manifest_extra: str = "") -> Path:
    repo = tmp / "repo"
    _write(
        repo / "ontology" / "manifest.yaml",
        "\n".join(
            [
                "rocs:",
                "  layer: core",
                '  id: "test.core"',
                '  version: "0.0.0"',
                '  created: "2026-01-10"',
                f"{manifest_extra}".rstrip(),
                "",
            ]
        ),
    )
    _write(repo / "ontology" / "src" / "system4d.yaml", "system4d: {}\n")
    _write(
        repo / "ontology" / "src" / "reference" / "relations" / "is_a.md",
        "\n".join(
            [
                "---",
                "ont:",
                '  id: "core.rel.is_a"',
                "  type: relation",
                '  labels: ["is_a"]',
                '  description: "taxonomy"',
                "  group: taxonomy",
                "  characteristics:",
                "    transitive: true",
                "    symmetric: false",
                "---",
                "",
                "examples:",
                '  - "core.Agent is_a core.Actor"',
                "",
                "# is_a",
                "",
                "## Definition",
                "taxonomy",
                "",
                "## Domain / Range",
                "- Domain: subtype concept",
                "- Range: supertype concept",
                "",
            ]
        ),
    )
    _write(
        repo / "ontology" / "src" / "reference" / "concepts" / "core.Actor.md",
        "\n".join(
            [
                "---",
                "ont:",
                '  id: "core.Actor"',
                "  type: concept",
                '  labels: ["Actor"]',
                '  description: "an actor"',
                "  relations: []",
                "  examples:",
                '    - "an example"',
                "  anti_examples:",
                '    - "an anti-example"',
                "---",
                "",
                "# Actor",
                "",
                "## Definition",
                "an actor",
                "",
            ]
        ),
    )
    _write(
        repo / "ontology" / "src" / "reference" / "concepts" / "core.Agent.md",
        "\n".join(
            [
                "---",
                "ont:",
                '  id: "core.Agent"',
                "  type: concept",
                '  labels: ["Agent"]',
                '  description: "an agent"',
                "  relations:",
                "    - type: is_a",
                '      target: "core.Actor"',
                "  examples:",
                '    - "an example"',
                "  anti_examples:",
                '    - "an anti-example"',
                "---",
                "",
                "# Agent",
                "",
                "## Definition",
                "an agent",
                "",
            ]
        ),
    )
    return repo


def _run(argv: list[str]) -> int:
    try:
        cli.main(argv)
    except SystemExit as e:
        return int(e.code or 0)
    return 0


def _run_capture(argv: list[str]) -> tuple[int, str]:
    buf = io.StringIO()
    prev_console = cli_mod.console
    cli_mod.console = Console(file=buf, force_terminal=False, color_system=None, width=200)
    try:
        code = _run(argv)
    finally:
        cli_mod.console = prev_console
    return code, buf.getvalue()


class TestRocsCli(unittest.TestCase):
    def test_version_subcommand(self) -> None:
        self.assertEqual(_run(["version"]), 0)

    def test_validate_ok(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            self.assertEqual(_run(["validate", "--repo", str(repo)]), 0)

    def test_strict_placeholders_allows_gitlab_locator_in_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td), manifest_extra='  note: "<gitlab:ai-society/core/ontology-kernel@v0.1.0>"')
            self.assertEqual(_run(["validate", "--repo", str(repo), "--strict-placeholders"]), 0)

    def test_strict_placeholders_rejects_other_placeholders_in_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td), manifest_extra='  note: "<placeholder>"')
            self.assertNotEqual(_run(["validate", "--repo", str(repo), "--strict-placeholders"]), 0)

    def test_relation_label_collision_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            _write(
                repo / "ontology" / "src" / "reference" / "relations" / "also_is_a.md",
                "\n".join(
                    [
                        "---",
                        "ont:",
                        '  id: "core.rel.is_a_2"',
                        "  type: relation",
                        '  labels: ["is_a"]',
                        '  description: "duplicate label"',
                        "  group: taxonomy",
                        "---",
                        "",
                        "# also_is_a",
                        "",
                    ]
                ),
            )
            self.assertNotEqual(_run(["validate", "--repo", str(repo)]), 0)

    def test_graph_writes_default_excalidraw(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            out = Path(td) / "g.excalidraw.json"
            self.assertEqual(_run(["graph", "--repo", str(repo), "--relation", "is_a", "--out", str(out)]), 0)
            self.assertTrue(out.exists())

    def test_normalize_check_then_apply(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            bad = repo / "ontology" / "src" / "reference" / "concepts" / "bad.md"
            _write(
                bad,
                "\n".join(
                    [
                        "---",
                        "ont:",
                        '  id: "core.Bad"',
                        "  type: concept",
                        '  labels: ["Bad"]',
                        '  description: "bad"',
                        "  relations:",
                        "---",
                        "",
                        "# Bad",
                        "",
                        "## Definition",
                        "bad",
                        "",
                    ]
                ),
            )
            self.assertEqual(_run(["normalize", "--repo", str(repo)]), 2)
            self.assertEqual(_run(["normalize", "--repo", str(repo), "--apply"]), 0)
            self.assertEqual(_run(["validate", "--repo", str(repo)]), 0)

    def test_pack_default_is_single_doc(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            code, out = _run_capture(["pack", "core.Agent", "--repo", str(repo)])
            self.assertEqual(code, 0)
            self.assertIn("core.Agent.md", out)
            self.assertNotIn("core.Actor.md", out)

    def test_pack_profile_depth_expands(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(
                Path(td),
                manifest_extra="\n".join(
                    [
                        "  profiles:",
                        "    default: repo-dev",
                        "    repo-dev:",
                        "      pack:",
                        "        max_depth: 1",
                        "        include_relation_defs: true",
                        "        rel_types: [is_a]",
                    ]
                ),
            )
            code, out = _run_capture(["pack", "core.Agent", "--repo", str(repo)])
            self.assertEqual(code, 0)
            self.assertIn("core.Agent.md", out)
            self.assertIn("core.Actor.md", out)
            self.assertIn("is_a.md", out)


if __name__ == "__main__":
    unittest.main()
