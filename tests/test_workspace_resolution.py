import io
import json
import os
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path

from rich.console import Console

from rocs_cli import __main__ as cli
import rocs_cli.cli as cli_mod
from rocs_cli.gitlab import gitlab_cache_dest
from rocs_cli.workspace import _project_path_from_remote_url, git_rev_sha


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, "utf-8")


class _Env:
    def __init__(self, **updates: str) -> None:
        self._updates = updates
        self._prev: dict[str, str | None] = {}

    def __enter__(self) -> None:
        for k, v in self._updates.items():
            self._prev[k] = os.environ.get(k)
            os.environ[k] = v

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        for k, prev in self._prev.items():
            if prev is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = prev


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


def _parse_json(out: str) -> dict:
    return json.loads(out.strip())


def _git(repo: Path, args: list[str]) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _init_workspace_repo(repo: Path, *, project_path: str, tag: str, make_mismatch: bool, origin_project_path: str | None = None) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, ["init"])
    _git(repo, ["config", "user.email", "test@example.invalid"])
    _git(repo, ["config", "user.name", "test"])

    origin_pp = origin_project_path or project_path
    _git(repo, ["remote", "add", "origin", f"http://example.invalid/{origin_pp}.git"])

    _write(repo / "ontology" / "src" / "system4d.yaml", "system4d: {}\n")
    _git(repo, ["add", "."])
    _git(repo, ["commit", "-m", "init"])
    _git(repo, ["tag", tag])

    if make_mismatch:
        _write(repo / "README.md", "mismatch\n")
        _git(repo, ["add", "README.md"])
        _git(repo, ["commit", "-m", "mismatch"])


def _mk_rocs_repo(tmp: Path, *, locator: str) -> Path:
    repo = tmp / "repo"
    _write(
        repo / "ontology" / "manifest.yaml",
        "\n".join(
            [
                "rocs:",
                "  layers:",
                "    - name: dep",
                f"      ref: {locator!r}",
                "    - name: core",
                "      path: ontology/src",
                "",
            ]
        ),
    )
    _write(repo / "ontology" / "src" / "system4d.yaml", "system4d: {}\n")
    return repo


def _tar_gz_bytes(members: list[tuple[tarfile.TarInfo, bytes | None]]) -> bytes:
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode="w:gz") as tf:
        for ti, data in members:
            if data is None:
                tf.addfile(ti)
            else:
                tf.addfile(ti, io.BytesIO(data))
    return out.getvalue()


def _good_repo_tar() -> bytes:
    top = "repo-abc123"
    ti_dir = tarfile.TarInfo(f"{top}/")
    ti_dir.type = tarfile.DIRTYPE
    ti_dir.mode = 0o755

    content = b"ok\n"
    ti_file = tarfile.TarInfo(f"{top}/ontology/src/system4d.yaml")
    ti_file.size = len(content)
    ti_file.mode = 0o644
    return _tar_gz_bytes([(ti_dir, None), (ti_file, content)])


class TestWorkspaceResolution(unittest.TestCase):
    def test_workspace_git_rev_sha_rejects_dash_ref(self) -> None:
        project_path = "ai-society/core/dep"
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo = td_path / "dep"
            _init_workspace_repo(repo, project_path=project_path, tag="v1", make_mismatch=False)

            good = git_rev_sha(repo, "v1")
            self.assertIsNotNone(good)

            # Must not treat `--help` as a flag; should resolve as "not a rev".
            self.assertIsNone(git_rev_sha(repo, "--help"))

    def test_remote_url_parser_handles_urls_with_port(self) -> None:
        cases = {
            "ssh://git@192.168.161.10:2224/ai-society/core/ontology-kernel.git": "ai-society/core/ontology-kernel",
            "https://token@192.168.161.10:8929/ai-society/softwareco/ontology.git": "ai-society/softwareco/ontology",
            "git@192.168.161.10:ai-society/core/rocs-cli.git": "ai-society/core/rocs-cli",
        }
        for remote_url, want in cases.items():
            with self.subTest(remote_url=remote_url):
                self.assertEqual(_project_path_from_remote_url(remote_url), want)

    def test_workspace_wins_over_cache_and_gitlab(self) -> None:
        project_path = "ai-society/core/dep"
        locator = f"<gitlab:{project_path}@v1>"
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            ws = td_path / "ws"
            cache = td_path / "cache"
            _init_workspace_repo(ws / "core" / "dep", project_path=project_path, tag="v1", make_mismatch=False)
            repo = _mk_rocs_repo(td_path, locator=locator)

            with _Env(ROCS_CACHE_DIR=str(cache)):
                code, out = _run_capture(
                    [
                        "resolve",
                        "--repo",
                        str(repo),
                        "--resolve-refs",
                        "--workspace-root",
                        str(ws),
                        "--workspace-ref-mode",
                        "strict",
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = _parse_json(out)
            dep = [x for x in payload["layers"] if x["name"] == "dep"][0]
            self.assertEqual(dep["source"], "workspace")

    def test_repo_locator_uses_workspace_layout_without_origin_match(self) -> None:
        project_path = "core/dep"
        locator = f"<repo:{project_path}@v1>"
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            ws = td_path / "ws"
            cache = td_path / "cache"
            _init_workspace_repo(
                ws / "core" / "dep",
                project_path=project_path,
                origin_project_path="github/example/dep",
                tag="v1",
                make_mismatch=False,
            )
            repo = _mk_rocs_repo(td_path, locator=locator)

            with _Env(ROCS_CACHE_DIR=str(cache)):
                code, out = _run_capture(
                    [
                        "resolve",
                        "--repo",
                        str(repo),
                        "--resolve-refs",
                        "--workspace-root",
                        str(ws),
                        "--workspace-ref-mode",
                        "strict",
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = _parse_json(out)
            dep = [x for x in payload["layers"] if x["name"] == "dep"][0]
            self.assertEqual(dep["source"], "workspace")

    def test_cache_used_when_workspace_strict_mismatch(self) -> None:
        project_path = "ai-society/core/dep"
        locator = f"<gitlab:{project_path}@v1>"
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            ws = td_path / "ws"
            cache = td_path / "cache"
            _init_workspace_repo(ws / "core" / "dep", project_path=project_path, tag="v1", make_mismatch=True)
            repo = _mk_rocs_repo(td_path, locator=locator)

            with _Env(ROCS_CACHE_DIR=str(cache)):
                dest = gitlab_cache_dest(project_path, "v1")
                _write(dest / "ontology" / "src" / "system4d.yaml", "system4d: {}\n")
                _write(
                    dest / ".rocs_cache_ok.json",
                    json.dumps({"project_path": project_path, "ref": "v1", "schema": 1}, sort_keys=True) + "\n",
                )

                code, out = _run_capture(
                    [
                        "resolve",
                        "--repo",
                        str(repo),
                        "--resolve-refs",
                        "--workspace-root",
                        str(ws),
                        "--workspace-ref-mode",
                        "strict",
                        "--show-resolve-details",
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = _parse_json(out)
            dep = [x for x in payload["layers"] if x["name"] == "dep"][0]
            self.assertEqual(dep["source"], "cache")
            self.assertEqual(dep.get("details", {}).get("workspace", {}).get("present"), True)
            self.assertEqual(dep.get("details", {}).get("workspace", {}).get("used"), False)
            self.assertEqual(dep.get("details", {}).get("workspace", {}).get("reason"), "ref_mismatch")

    def test_strict_mismatch_fails_cleanly_without_cache_or_gitlab(self) -> None:
        project_path = "ai-society/core/dep"
        locator = f"<gitlab:{project_path}@v1>"
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            ws = td_path / "ws"
            cache = td_path / "cache"
            _init_workspace_repo(ws / "core" / "dep", project_path=project_path, tag="v1", make_mismatch=True)
            repo = _mk_rocs_repo(td_path, locator=locator)

            with _Env(ROCS_CACHE_DIR=str(cache)):
                code, out = _run_capture(
                    [
                        "resolve",
                        "--repo",
                        str(repo),
                        "--resolve-refs",
                        "--workspace-root",
                        str(ws),
                        "--workspace-ref-mode",
                        "strict",
                        "--json",
                    ]
                )
            self.assertEqual(code, 1)
            payload = _parse_json(out)
            self.assertEqual(payload.get("ok"), False)
            self.assertIn("workspace ref mismatch", payload.get("error", {}).get("message", ""))

    def test_gitlab_used_when_no_workspace_and_cache_empty(self) -> None:
        locator = "<gitlab:ai-society/core/dep@v1>"
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            ws = td_path / "ws"
            cache = td_path / "cache"
            repo = _mk_rocs_repo(td_path, locator=locator)

            body = _good_repo_tar()
            import rocs_cli.gitlab as gitlab_mod

            def _urlopen(_req, timeout):  # noqa: ANN001
                class _Resp:
                    def __init__(self, b: bytes) -> None:
                        self._buf = io.BytesIO(b)
                        self.headers = {}

                    def __enter__(self):  # noqa: ANN001
                        return self

                    def __exit__(self, exc_type, exc, tb):  # noqa: ANN001
                        return None

                    def read(self, n: int) -> bytes:
                        return self._buf.read(n)

                return _Resp(body)

            prev = gitlab_mod.urlopen
            gitlab_mod.urlopen = _urlopen
            try:
                with _Env(ROCS_CACHE_DIR=str(cache), ROCS_GITLAB_BASE_URL="http://example.invalid"):
                    code, out = _run_capture(
                        [
                            "resolve",
                            "--repo",
                            str(repo),
                            "--resolve-refs",
                            "--workspace-root",
                            str(ws),
                            "--json",
                        ]
                    )
                self.assertEqual(code, 0)
                payload = _parse_json(out)
                dep = [x for x in payload["layers"] if x["name"] == "dep"][0]
                self.assertEqual(dep["source"], "gitlab")
            finally:
                gitlab_mod.urlopen = prev

    def test_workspace_origin_mismatch_is_ignored(self) -> None:
        project_path = "ai-society/core/dep"
        locator = f"<gitlab:{project_path}@v1>"
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            ws = td_path / "ws"
            cache = td_path / "cache"
            _init_workspace_repo(
                ws / "core" / "dep",
                project_path=project_path,
                origin_project_path="ai-society/core/other",
                tag="v1",
                make_mismatch=False,
            )
            repo = _mk_rocs_repo(td_path, locator=locator)

            with _Env(ROCS_CACHE_DIR=str(cache)):
                dest = gitlab_cache_dest(project_path, "v1")
                _write(dest / "ontology" / "src" / "system4d.yaml", "system4d: {}\n")
                _write(
                    dest / ".rocs_cache_ok.json",
                    json.dumps({"project_path": project_path, "ref": "v1", "schema": 1}, sort_keys=True) + "\n",
                )

                code, out = _run_capture(
                    [
                        "resolve",
                        "--repo",
                        str(repo),
                        "--resolve-refs",
                        "--workspace-root",
                        str(ws),
                        "--workspace-ref-mode",
                        "loose",
                        "--show-resolve-details",
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = _parse_json(out)
            dep = [x for x in payload["layers"] if x["name"] == "dep"][0]
            self.assertEqual(dep["source"], "cache")
            self.assertEqual(dep.get("details", {}).get("workspace", {}).get("present"), True)
            self.assertEqual(dep.get("details", {}).get("workspace", {}).get("used"), False)
            self.assertEqual(dep.get("details", {}).get("workspace", {}).get("reason"), "origin_mismatch")

    def test_repo_locator_missing_workspace_never_mentions_gitlab_config(self) -> None:
        locator = "<repo:core/dep@v1>"
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            ws = td_path / "ws"
            cache = td_path / "cache"
            repo = _mk_rocs_repo(td_path, locator=locator)

            with _Env(ROCS_CACHE_DIR=str(cache)):
                code, out = _run_capture(
                    [
                        "resolve",
                        "--repo",
                        str(repo),
                        "--resolve-refs",
                        "--workspace-root",
                        str(ws),
                        "--json",
                    ]
                )
            self.assertEqual(code, 1)
            payload = _parse_json(out)
            self.assertEqual(payload.get("ok"), False)
            self.assertIn("local ref not available", payload.get("error", {}).get("message", ""))
            self.assertNotIn("GitLab base url", payload.get("error", {}).get("message", ""))

    def test_build_authority_receipt_captures_workspace_repo_resolution(self) -> None:
        project_path = "core/dep"
        locator = f"<repo:{project_path}@v1>"
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            ws = td_path / "ws"
            cache = td_path / "cache"
            _init_workspace_repo(ws / "core" / "dep", project_path=project_path, tag="v1", make_mismatch=False)
            repo = _mk_rocs_repo(td_path, locator=locator)

            with _Env(ROCS_CACHE_DIR=str(cache), ROCS_CI_PROFILE="branch-ci"):
                code, _out = _run_capture(
                    [
                        "build",
                        "--repo",
                        str(repo),
                        "--resolve-refs",
                        "--workspace-root",
                        str(ws),
                    ]
                )
            self.assertEqual(code, 0)
            aggregate = json.loads((repo / "ontology" / "dist" / "authority-receipt.json").read_text("utf-8"))
            receipt = json.loads((repo / "ontology" / "dist" / "authority-receipt.build.json").read_text("utf-8"))
            self.assertEqual(aggregate.get("last_command"), "build")
            self.assertIn("build", aggregate.get("commands", {}))
            self.assertEqual(receipt.get("command"), "build")
            self.assertEqual(receipt.get("ok"), True)
            self.assertEqual(receipt.get("ci_profile"), "branch-ci")
            self.assertEqual(receipt.get("authority_mode"), "strict_ref_resolution")
            self.assertEqual(receipt.get("authoritative"), True)
            self.assertEqual(receipt.get("resolve_refs_requested"), True)
            self.assertEqual(sorted(receipt.get("locator_kinds_present") or []), ["path", "repo"])
            dep = [x for x in receipt.get("layer_sources") or [] if x.get("name") == "dep"][0]
            self.assertEqual(dep.get("source"), "workspace")
            self.assertEqual(dep.get("locator_kind"), "repo")
            self.assertEqual(receipt.get("legacy_gitlab_fallback_used"), False)

    def test_loose_workspace_ref_resolution_is_marked_best_effort(self) -> None:
        project_path = "core/dep"
        locator = f"<repo:{project_path}@v1>"
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            ws = td_path / "ws"
            cache = td_path / "cache"
            _init_workspace_repo(ws / "core" / "dep", project_path=project_path, tag="v1", make_mismatch=True)
            repo = _mk_rocs_repo(td_path, locator=locator)

            with _Env(ROCS_CACHE_DIR=str(cache)):
                code, _out = _run_capture(
                    [
                        "build",
                        "--repo",
                        str(repo),
                        "--resolve-refs",
                        "--workspace-root",
                        str(ws),
                        "--workspace-ref-mode",
                        "loose",
                    ]
                )
            self.assertEqual(code, 0)
            receipt = json.loads((repo / "ontology" / "dist" / "authority-receipt.build.json").read_text("utf-8"))
            self.assertEqual(receipt.get("authority_mode"), "best_effort_workspace_loose")
            self.assertEqual(receipt.get("authoritative"), False)
            self.assertEqual(receipt.get("loose_workspace_ref_layers_used"), 1)

    def test_ci_wrapper_preserves_validate_and_build_receipts_in_aggregate(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo = _mk_rocs_repo(td_path, locator="<repo:core/dep@v1>")
            ws = td_path / "ws"
            _init_workspace_repo(ws / "core" / "dep", project_path="core/dep", tag="v1", make_mismatch=False)

            with _Env(ROCS_CI_PROFILE="branch-ci", ROCS_REPO=str(repo), ROCS_WORKSPACE_ROOT=str(ws), ROCS_CMD="uv run python -m rocs_cli"):
                proc = subprocess.run(
                    ["bash", "scripts/ci/full.sh"],
                    check=False,
                    capture_output=True,
                    text=True,
                )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            aggregate = json.loads((repo / "ontology" / "dist" / "authority-receipt.json").read_text("utf-8"))
            self.assertEqual(aggregate.get("last_command"), "build")
            self.assertEqual(sorted(aggregate.get("commands", {}).keys()), ["build", "validate"])
            self.assertEqual(aggregate.get("command_files", {}).get("validate"), "authority-receipt.validate.json")
            self.assertEqual(aggregate.get("command_files", {}).get("build"), "authority-receipt.build.json")

    def test_ci_wrapper_defaults_workspace_root_from_home_ai_society(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            home = td_path / "home"
            ws = home / "ai-society"
            repo = _mk_rocs_repo(td_path, locator="<repo:core/dep@v1>")
            _init_workspace_repo(ws / "core" / "dep", project_path="core/dep", tag="v1", make_mismatch=False)

            with _Env(HOME=str(home), ROCS_CI_PROFILE="branch-ci", ROCS_REPO=str(repo), ROCS_CMD="uv run python -m rocs_cli"):
                proc = subprocess.run(
                    ["bash", "scripts/ci/full.sh"],
                    check=False,
                    capture_output=True,
                    text=True,
                )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            aggregate = json.loads((repo / "ontology" / "dist" / "authority-receipt.json").read_text("utf-8"))
            self.assertEqual(sorted(aggregate.get("commands", {}).keys()), ["build", "validate"])

    def test_ci_wrapper_branch_ci_defaults_workspace_matching_to_strict(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo = _mk_rocs_repo(td_path, locator="<repo:core/dep@v1>")
            ws = td_path / "ws"
            cache = td_path / "cache"
            _init_workspace_repo(ws / "core" / "dep", project_path="core/dep", tag="v1", make_mismatch=True)

            with _Env(
                ROCS_CACHE_DIR=str(cache),
                ROCS_CI_PROFILE="branch-ci",
                ROCS_REPO=str(repo),
                ROCS_WORKSPACE_ROOT=str(ws),
                ROCS_CMD="uv run python -m rocs_cli",
            ):
                proc = subprocess.run(
                    ["bash", "scripts/ci/full.sh"],
                    check=False,
                    capture_output=True,
                    text=True,
                )
            self.assertNotEqual(proc.returncode, 0)
            combined = (proc.stdout + proc.stderr).replace("\n", " ")
            self.assertIn("ref mismatch in strict mode", combined)

    def test_ci_wrapper_local_dev_opt_in_defaults_workspace_matching_to_strict(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            repo = _mk_rocs_repo(td_path, locator="<repo:core/dep@v1>")
            ws = td_path / "ws"
            cache = td_path / "cache"
            _init_workspace_repo(ws / "core" / "dep", project_path="core/dep", tag="v1", make_mismatch=True)

            with _Env(
                ROCS_CACHE_DIR=str(cache),
                ROCS_CI_PROFILE="local-dev",
                ROCS_LOCAL_RESOLVE_REFS="1",
                ROCS_REPO=str(repo),
                ROCS_WORKSPACE_ROOT=str(ws),
                ROCS_CMD="uv run python -m rocs_cli",
            ):
                proc = subprocess.run(
                    ["bash", "scripts/ci/full.sh"],
                    check=False,
                    capture_output=True,
                    text=True,
                )
            self.assertNotEqual(proc.returncode, 0)
            combined = (proc.stdout + proc.stderr).replace("\n", " ")
            self.assertIn("ref mismatch in strict mode", combined)

    def test_build_authority_receipt_marks_legacy_gitlab_fallback(self) -> None:
        locator = "<gitlab:ai-society/core/dep@v1>"
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            ws = td_path / "ws"
            cache = td_path / "cache"
            repo = _mk_rocs_repo(td_path, locator=locator)

            body = _good_repo_tar()
            import rocs_cli.gitlab as gitlab_mod

            def _urlopen(_req, timeout):  # noqa: ANN001
                class _Resp:
                    def __init__(self, b: bytes) -> None:
                        self._buf = io.BytesIO(b)
                        self.headers = {}

                    def __enter__(self):  # noqa: ANN001
                        return self

                    def __exit__(self, exc_type, exc, tb):  # noqa: ANN001
                        return None

                    def read(self, n: int) -> bytes:
                        return self._buf.read(n)

                return _Resp(body)

            prev = gitlab_mod.urlopen
            gitlab_mod.urlopen = _urlopen
            try:
                with _Env(ROCS_CACHE_DIR=str(cache), ROCS_GITLAB_BASE_URL="http://example.invalid"):
                    code, _out = _run_capture(
                        [
                            "build",
                            "--repo",
                            str(repo),
                            "--resolve-refs",
                            "--workspace-root",
                            str(ws),
                        ]
                    )
                self.assertEqual(code, 0)
                receipt = json.loads((repo / "ontology" / "dist" / "authority-receipt.build.json").read_text("utf-8"))
                dep = [x for x in receipt.get("layer_sources") or [] if x.get("name") == "dep"][0]
                self.assertEqual(dep.get("source"), "gitlab")
                self.assertEqual(dep.get("locator_kind"), "gitlab")
                self.assertEqual(receipt.get("legacy_gitlab_fallback_used"), True)
            finally:
                gitlab_mod.urlopen = prev
