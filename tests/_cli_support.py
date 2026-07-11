import tempfile
import unittest
import io
import json
import os
import subprocess
import sys
from pathlib import Path

from rich.console import Console

from rocs_cli import __main__ as cli
import rocs_cli.cli as cli_mod
from rocs_cli.vendored import compute_expected_hashes


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, "utf-8")


def _mk_repo(tmp: Path, *, manifest_extra: str = "", layout: str = "nested") -> Path:
    repo = tmp / "repo"
    ontology_root = repo if layout == "root" else repo / "ontology"
    _write(
        ontology_root / "manifest.yaml",
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
    _write(ontology_root / "src" / "system4d.yaml", "system4d: {}\n")
    _write(
        ontology_root / "src" / "reference" / "relations" / "is_a.md",
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
        ontology_root / "src" / "reference" / "concepts" / "core.Actor.md",
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
        ontology_root / "src" / "reference" / "concepts" / "core.Agent.md",
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
    buf = io.StringIO()
    prev_console = cli_mod.console
    cli_mod.console = Console(file=buf, force_terminal=False, color_system=None, width=200)
    try:
        cli.main(argv)
    except SystemExit as e:
        return int(e.code or 0)
    finally:
        cli_mod.console = prev_console
    return 0


def _run_capture(argv: list[str]) -> tuple[int, str]:
    buf = io.StringIO()
    prev_console = cli_mod.console
    cli_mod.console = Console(file=buf, force_terminal=False, color_system=None, width=200)
    try:
        try:
            cli.main(argv)
        except SystemExit as e:
            code = int(e.code or 0)
        else:
            code = 0
    finally:
        cli_mod.console = prev_console
    return code, buf.getvalue()


def _parse_json(out: str) -> dict:
    return json.loads(out.strip())
