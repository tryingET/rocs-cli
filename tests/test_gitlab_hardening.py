import io
import os
import tarfile
import tempfile
import unittest
from urllib.error import HTTPError

from pathlib import Path

from rocs_cli.errors import RocsCliError
from rocs_cli.gitlab import fetch_repo_archive, gitlab_cache_dest


class _FakeResponse:
    def __init__(self, body: bytes, *, headers: dict[str, str] | None = None) -> None:
        self._buf = io.BytesIO(body)
        self.headers = headers or {}

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        return None

    def read(self, n: int) -> bytes:
        return self._buf.read(n)


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
    ti_file = tarfile.TarInfo(f"{top}/README.md")
    ti_file.size = len(content)
    ti_file.mode = 0o644
    return _tar_gz_bytes([(ti_dir, None), (ti_file, content)])


class TestGitlabArchiveHardening(unittest.TestCase):
    def test_gitlab_cache_dest_does_not_collapse_distinct_project_or_ref_names(self) -> None:
        project_a = gitlab_cache_dest("group/a__b", "main")
        project_b = gitlab_cache_dest("group/a/b", "main")
        ref_a = gitlab_cache_dest("group/proj", "release__2026")
        ref_b = gitlab_cache_dest("group/proj", "release/2026")

        self.assertNotEqual(project_a, project_b)
        self.assertNotEqual(ref_a, ref_b)

    def test_fetch_reuses_legacy_complete_cache_location(self) -> None:
        project_path = "x/y"
        ref = "main"
        with tempfile.TemporaryDirectory() as td, _Env(ROCS_CACHE_DIR=td):
            legacy = Path(td) / "gitlab" / project_path.replace("/", "__") / ref.replace("/", "__")
            legacy.mkdir(parents=True, exist_ok=True)
            (legacy / "README.md").write_text("ok\n", "utf-8")
            (legacy / ".rocs_cache_ok.json").write_text(
                '{"project_path": "x/y", "ref": "main", "schema": 1}\n',
                "utf-8",
            )

            import rocs_cli.gitlab as gitlab_mod

            def _urlopen(_req, timeout):  # noqa: ANN001
                raise AssertionError("should not fetch when legacy cache is complete")

            prev = gitlab_mod.urlopen
            gitlab_mod.urlopen = _urlopen
            try:
                resolved = fetch_repo_archive(project_path, ref, base_url="http://example.invalid", headers={})
                self.assertEqual(resolved, legacy)
            finally:
                gitlab_mod.urlopen = prev

    def test_extract_rejects_path_traversal(self) -> None:
        top = "repo-abc123"
        ti_dir = tarfile.TarInfo(f"{top}/")
        ti_dir.type = tarfile.DIRTYPE
        ti_dir.mode = 0o755

        content = b"pwnd\n"
        ti_bad = tarfile.TarInfo(f"{top}/../evil.txt")
        ti_bad.size = len(content)
        ti_bad.mode = 0o644

        body = _tar_gz_bytes([(ti_dir, None), (ti_bad, content)])

        with tempfile.TemporaryDirectory() as td, _Env(ROCS_CACHE_DIR=td):
            import rocs_cli.gitlab as gitlab_mod

            def _urlopen(_req, timeout):  # noqa: ANN001
                return _FakeResponse(body)

            prev = gitlab_mod.urlopen
            gitlab_mod.urlopen = _urlopen
            try:
                with self.assertRaises(RocsCliError) as ctx:
                    fetch_repo_archive("x/y", "main", base_url="http://example.invalid", headers={})
                self.assertIn("unsafe GitLab archive member path", str(ctx.exception))
            finally:
                gitlab_mod.urlopen = prev

    def test_extract_rejects_symlink(self) -> None:
        top = "repo-abc123"
        ti_dir = tarfile.TarInfo(f"{top}/")
        ti_dir.type = tarfile.DIRTYPE
        ti_dir.mode = 0o755

        ti_link = tarfile.TarInfo(f"{top}/link")
        ti_link.type = tarfile.SYMTYPE
        ti_link.linkname = "/etc/passwd"

        body = _tar_gz_bytes([(ti_dir, None), (ti_link, None)])

        with tempfile.TemporaryDirectory() as td, _Env(ROCS_CACHE_DIR=td):
            import rocs_cli.gitlab as gitlab_mod

            def _urlopen(_req, timeout):  # noqa: ANN001
                return _FakeResponse(body)

            prev = gitlab_mod.urlopen
            gitlab_mod.urlopen = _urlopen
            try:
                with self.assertRaises(RocsCliError) as ctx:
                    fetch_repo_archive("x/y", "main", base_url="http://example.invalid", headers={})
                self.assertIn("unsafe GitLab archive member (link)", str(ctx.exception))
            finally:
                gitlab_mod.urlopen = prev

    def test_extract_rejects_hardlink(self) -> None:
        top = "repo-abc123"
        ti_dir = tarfile.TarInfo(f"{top}/")
        ti_dir.type = tarfile.DIRTYPE
        ti_dir.mode = 0o755

        ti_link = tarfile.TarInfo(f"{top}/hardlink")
        ti_link.type = tarfile.LNKTYPE
        ti_link.linkname = f"{top}/README.md"

        body = _tar_gz_bytes([(ti_dir, None), (ti_link, None)])

        with tempfile.TemporaryDirectory() as td, _Env(ROCS_CACHE_DIR=td):
            import rocs_cli.gitlab as gitlab_mod

            def _urlopen(_req, timeout):  # noqa: ANN001
                return _FakeResponse(body)

            prev = gitlab_mod.urlopen
            gitlab_mod.urlopen = _urlopen
            try:
                with self.assertRaises(RocsCliError) as ctx:
                    fetch_repo_archive("x/y", "main", base_url="http://example.invalid", headers={})
                self.assertIn("unsafe GitLab archive member (link)", str(ctx.exception))
            finally:
                gitlab_mod.urlopen = prev

    def test_download_enforces_max_archive_bytes(self) -> None:
        body = _good_repo_tar()

        with tempfile.TemporaryDirectory() as td, _Env(ROCS_CACHE_DIR=td, ROCS_GITLAB_MAX_ARCHIVE_BYTES="1"):
            import rocs_cli.gitlab as gitlab_mod

            def _urlopen(_req, timeout):  # noqa: ANN001
                return _FakeResponse(body, headers={"Content-Length": str(len(body))})

            prev = gitlab_mod.urlopen
            gitlab_mod.urlopen = _urlopen
            try:
                with self.assertRaises(RocsCliError) as ctx:
                    fetch_repo_archive("x/y", "main", base_url="http://example.invalid", headers={})
                self.assertIn("download size limit", str(ctx.exception))
            finally:
                gitlab_mod.urlopen = prev

    def test_cache_marker_written_and_reused(self) -> None:
        body = _good_repo_tar()
        calls = {"n": 0}

        with tempfile.TemporaryDirectory() as td, _Env(ROCS_CACHE_DIR=td):
            import rocs_cli.gitlab as gitlab_mod

            def _urlopen(_req, timeout):  # noqa: ANN001
                calls["n"] += 1
                return _FakeResponse(body)

            prev = gitlab_mod.urlopen
            gitlab_mod.urlopen = _urlopen
            try:
                p1 = fetch_repo_archive("x/y", "main", base_url="http://example.invalid", headers={})
                self.assertTrue((p1 / ".rocs_cache_ok.json").exists())
                self.assertTrue((p1 / "README.md").exists())
                self.assertEqual(calls["n"], 1)

                p2 = fetch_repo_archive("x/y", "main", base_url="http://example.invalid", headers={})
                self.assertEqual(p1, p2)
                self.assertEqual(calls["n"], 1, msg="cache hit should not re-download")
            finally:
                gitlab_mod.urlopen = prev

    def test_retries_timeout_then_succeeds(self) -> None:
        body = _good_repo_tar()
        calls = {"n": 0}

        with tempfile.TemporaryDirectory() as td, _Env(ROCS_CACHE_DIR=td, ROCS_GITLAB_RETRIES="3", ROCS_GITLAB_BACKOFF_S="0.0001"):
            import rocs_cli.gitlab as gitlab_mod

            def _urlopen(_req, timeout):  # noqa: ANN001
                calls["n"] += 1
                if calls["n"] < 3:
                    raise TimeoutError("nope")
                return _FakeResponse(body)

            prev_urlopen = gitlab_mod.urlopen
            prev_sleep = gitlab_mod.time.sleep
            gitlab_mod.urlopen = _urlopen
            gitlab_mod.time.sleep = lambda _s: None
            try:
                fetch_repo_archive("x/y", "main", base_url="http://example.invalid", headers={})
                self.assertEqual(calls["n"], 3)
            finally:
                gitlab_mod.urlopen = prev_urlopen
                gitlab_mod.time.sleep = prev_sleep

    def test_http_404_is_actionable(self) -> None:
        with tempfile.TemporaryDirectory() as td, _Env(ROCS_CACHE_DIR=td):
            import rocs_cli.gitlab as gitlab_mod

            def _urlopen(_req, timeout):  # noqa: ANN001
                raise HTTPError(url="http://example.invalid", code=404, msg="not found", hdrs=None, fp=None)

            prev = gitlab_mod.urlopen
            gitlab_mod.urlopen = _urlopen
            try:
                with self.assertRaises(RocsCliError) as ctx:
                    fetch_repo_archive("x/y", "nope", base_url="http://example.invalid", headers={})
                self.assertIn("HTTP 404", str(ctx.exception))
            finally:
                gitlab_mod.urlopen = prev
