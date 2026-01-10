from __future__ import annotations

import re
import unittest
from pathlib import Path

from rocs_cli.cli_signature import cli_signature


_CODE_TICK_RE = re.compile(r"`([^`]+)`")
_FLAG_RE = re.compile(r"(?<!-)--[a-z0-9][a-z0-9-]*")


class TestDocsMatchCli(unittest.TestCase):
    def test_readme_commands_match_actual_cli(self) -> None:
        sig = cli_signature()
        cmds: dict[str, dict] = sig["commands"]
        global_opts = set(sig["global_options"])

        readme = Path(__file__).resolve().parents[1] / "README.md"
        text = readme.read_text("utf-8")

        # Negative check: this is a common uvx/argparse mistake.
        self.assertNotIn("`rocs -- --version`", text)

        for code in _CODE_TICK_RE.findall(text):
            code = code.strip()
            if not code.startswith("rocs "):
                continue

            rest = code[len("rocs ") :].strip()
            if not rest:
                continue

            first = rest.split()[0]
            if first.startswith("-"):
                # global opts (e.g. rocs --version)
                for flg in _FLAG_RE.findall(rest):
                    self.assertIn(flg, global_opts, msg=f"README mentions unknown global flag {flg!r} in `{code}`")
                continue

            cmd = first
            self.assertIn(cmd, cmds, msg=f"README mentions unknown command {cmd!r} in `{code}`")

            allowed = set(cmds[cmd]["option_strings"]) | global_opts
            for flg in _FLAG_RE.findall(rest):
                self.assertIn(flg, allowed, msg=f"README mentions unknown flag {flg!r} for {cmd!r} in `{code}`")
