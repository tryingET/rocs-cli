from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from rocs_cli.semantic_router_policy import capture_policy_bundle
from rocs_cli.semantic_router_protocol import (
    MAX_POLICY_BYTES,
    MAX_PROVENANCE_BYTES,
    SAFE_ERROR_MESSAGES,
    RouteProtocolError,
    jcs_bytes,
    object_digest,
)

from rocs_cli import semantic_router_policy as policy_io

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "docs" / "project" / "semantic-router-v0" / "golden-fixtures.json"
GIT_ENV = {
    "PATH": "/usr/bin:/bin", "HOME": "/nonexistent", "LANG": "C", "LC_ALL": "C",
    "GIT_AUTHOR_NAME": "Synthetic Test", "GIT_AUTHOR_EMAIL": "synthetic@example.invalid",
    "GIT_COMMITTER_NAME": "Synthetic Test", "GIT_COMMITTER_EMAIL": "synthetic@example.invalid",
}


def _digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


class SemanticRouterPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.policy_root = self.base / "captured"
        self.owner_root = self.base / "owner"
        self.policy_root.mkdir()
        self.owner_root.mkdir()
        self.git("init", "-q")
        valid = json.loads(GOLDEN.read_text("utf-8"))["valid"]
        self.policy = deepcopy(valid["policy"])
        self.provenance = deepcopy(valid["provenance"])
        self.request = deepcopy(valid["request"])
        self.materialize()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            ["/usr/bin/git", *args], cwd=self.owner_root, env=GIT_ENV,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check,
        )

    def materialize(self, authority_raw: bytes = b"synthetic authority\n", record_raw: bytes = b"synthetic record\n") -> None:
        (self.owner_root / "authority.txt").write_bytes(authority_raw)
        (self.owner_root / "record.txt").write_bytes(record_raw)
        self.git("add", "authority.txt", "record.txt")
        self.git("commit", "-q", "--allow-empty", "-m", "synthetic sources")
        revision = self.git("rev-parse", "HEAD").stdout.decode().strip()
        authority = self.policy["authority"]
        authority.update({
            "owner_repo": "synthetic-owner", "revision": revision, "path": "authority.txt",
            "source_content_digest": _digest(authority_raw),
        })
        self.provenance.update({
            "policy_owner_repo": "synthetic-owner", "policy_revision": revision,
            "policy_path": "authority.txt", "policy_source_content_digest": _digest(authority_raw),
        })
        for record in self.provenance["records"]:
            record.update({
                "source_owner_repo": "synthetic-owner", "source_revision": revision,
                "source_path": "record.txt", "source_content_digest": _digest(record_raw),
            })
        self.rewrite()

    def rewrite(self) -> None:
        self.provenance["provenance_manifest_digest"] = object_digest("provenance_manifest", self.provenance)
        self.policy["provenance_manifest_digest"] = self.provenance["provenance_manifest_digest"]
        self.policy["routing_policy_digest"] = object_digest("routing_policy", self.policy)
        self.request["expected_provenance_manifest_digest"] = self.provenance["provenance_manifest_digest"]
        self.request["expected_routing_policy_digest"] = self.policy["routing_policy_digest"]
        (self.policy_root / "policy.json").write_bytes(jcs_bytes(self.policy))
        (self.policy_root / "provenance.json").write_bytes(jcs_bytes(self.provenance))

    def capture(self, **overrides: object):
        arguments = {
            "routing_policy_root": self.policy_root,
            "policy_path": "policy.json", "provenance_path": "provenance.json",
            "owner_repo_id": "synthetic-owner", "owner_repo_root": self.owner_root,
            "request": self.request,
        }
        arguments.update(overrides)
        return capture_policy_bundle(**arguments)

    def assert_kind(self, kind: str, **overrides: object) -> RouteProtocolError:
        with self.assertRaises(RouteProtocolError) as caught:
            self.capture(**overrides)
        self.assertEqual(caught.exception.kind, kind)
        self.assertEqual(str(caught.exception), SAFE_ERROR_MESSAGES[kind])
        return caught.exception

    def test_valid_capture_is_descriptor_anchored_and_recheckable(self) -> None:
        with self.capture() as captured:
            self.assertEqual(captured.policy, self.policy)
            self.assertEqual(captured.provenance, self.provenance)
            self.assertEqual(captured.policy_content_digest, _digest((self.policy_root / "policy.json").read_bytes()))
            captured.recheck()
        self.assertTrue(captured._closed)

    def test_absolute_dot_dotdot_backslash_empty_and_escape_paths_fail(self) -> None:
        bad = (
            "/policy.json", ".", "./policy.json", "nested/../policy.json",
            "nested//policy.json", "nested\\policy.json", "policy.json/", "", "bad\0path", "\udcff",
        )
        for path in bad:
            with self.subTest(path=path):
                self.assert_kind("invalid_policy", policy_path=path)

    def test_symlink_root_intermediate_and_final_paths_fail(self) -> None:
        (self.base / "captured-link").symlink_to(self.policy_root, target_is_directory=True)
        self.assert_kind("invalid_policy", routing_policy_root=self.base / "captured-link")
        (self.policy_root / "policy-link.json").symlink_to("policy.json")
        self.assert_kind("invalid_policy", policy_path="policy-link.json")
        (self.policy_root / "directory-link").symlink_to(".", target_is_directory=True)
        self.assert_kind("invalid_policy", policy_path="directory-link/policy.json")

    def test_hardlink_nonregular_and_policy_provenance_aliases_fail(self) -> None:
        hard = self.policy_root / "hard.json"
        os.link(self.policy_root / "policy.json", hard)
        try:
            self.assert_kind("invalid_policy", policy_path="hard.json")
        finally:
            hard.unlink()
        (self.policy_root / "not-a-file").mkdir()
        self.assert_kind("invalid_policy", policy_path="not-a-file")
        self.assert_kind("invalid_policy", provenance_path="policy.json")

    def test_overlapping_same_parent_and_child_isolated_roots_fail(self) -> None:
        nested = self.policy_root / "nested"
        nested.mkdir()
        for other in (self.policy_root, nested, self.base):
            with self.subTest(other=other):
                self.assert_kind("invalid_policy", isolated_roots=(other,))

    def test_same_content_inode_replacement_at_intermediate_recheck_is_snapshot_changed(self) -> None:
        target = self.policy_root / "policy.json"
        original = target.read_bytes()
        old = target.stat()
        fired = False

        def race(stage: str) -> None:
            nonlocal fired
            if stage == "before_intermediate_recheck" and not fired:
                replacement = self.policy_root / "replacement"
                replacement.write_bytes(original)
                os.utime(replacement, ns=(old.st_atime_ns, old.st_mtime_ns))
                os.replace(replacement, target)
                fired = True

        with patch.object(policy_io, "_race_hook", side_effect=race):
            self.assert_kind("snapshot_changed")
        self.assertTrue(fired)

    def test_open_race_and_final_execution_race_are_snapshot_changed(self) -> None:
        target = self.policy_root / "policy.json"
        original = target.read_bytes()
        fired = False

        def race(stage: str) -> None:
            nonlocal fired
            if stage == "before_policy_open" and not fired:
                replacement = self.policy_root / "replacement"
                replacement.write_bytes(original)
                os.replace(replacement, target)
                fired = True

        with patch.object(policy_io, "_race_hook", side_effect=race):
            self.assert_kind("snapshot_changed")
        self.rewrite()
        with self.assertRaises(RouteProtocolError) as caught:
            with self.capture():
                (self.policy_root / "policy.json").write_bytes(b"{}")
        self.assertEqual(caught.exception.kind, "snapshot_changed")

    def test_recheck_closes_post_read_file_and_git_path_races(self) -> None:
        target = self.policy_root / "policy.json"
        original = target.read_bytes()
        fired = False
        def file_race(stage: str) -> None:
            nonlocal fired
            if stage == "during_file_final_recheck" and not fired:
                replacement = self.policy_root / "replacement"
                replacement.write_bytes(original)
                os.replace(replacement, target); fired = True
        with patch.object(policy_io, "_race_hook", side_effect=file_race):
            self.assert_kind("snapshot_changed")
        self.assertTrue(fired)
        self.rewrite(); fired = False
        def root_race(stage: str) -> None:
            nonlocal fired
            if stage == "before_bundle_post_recheck" and not fired:
                old = self.base / "captured-old"
                os.rename(self.policy_root, old)
                shutil.copytree(old, self.policy_root); fired = True
        with patch.object(policy_io, "_race_hook", side_effect=root_race):
            with self.assertRaises(RouteProtocolError) as caught:
                with self.capture(): pass
        self.assertEqual(caught.exception.kind, "snapshot_changed")
        self.assertTrue(fired)
        self.rewrite(); fired = False
        def git_race(stage: str) -> None:
            nonlocal fired
            if stage == "during_git_final_recheck" and not fired:
                old = self.owner_root / ".git-old"
                os.rename(self.owner_root / ".git", old)
                shutil.copytree(old, self.owner_root / ".git", symlinks=True); fired = True
        with patch.object(policy_io, "_race_hook", side_effect=git_race):
            self.assert_kind("snapshot_changed")
        self.assertTrue(fired)

    def test_absolute_preparse_maxima_precede_request_caps(self) -> None:
        (self.policy_root / "policy.json").write_bytes(b" " * (MAX_POLICY_BYTES + 1))
        self.assert_kind("resource_exhausted")
        self.rewrite()
        (self.policy_root / "provenance.json").write_bytes(b" ")
        os.truncate(self.policy_root / "provenance.json", MAX_PROVENANCE_BYTES + 1)
        self.assert_kind("resource_exhausted")

    def test_request_byte_depth_and_collection_caps_apply_after_hard_parse(self) -> None:
        for key, value in (
            ("policy_bytes", len((self.policy_root / "policy.json").read_bytes()) - 1),
            ("provenance_bytes", len((self.policy_root / "provenance.json").read_bytes()) - 1),
            ("parser_depth", 1), ("collection_items", 1),
        ):
            with self.subTest(key=key):
                request = deepcopy(self.request)
                request["route_limits"][key] = value
                self.assert_kind("resource_exhausted", request=request)
        request = deepcopy(self.request)
        request["discovery_limits"]["query_bytes"] = 1
        self.assert_kind("resource_exhausted", request=request)

    def test_existing_invariants_enforce_provenance_bijection(self) -> None:
        for mutation in ("missing", "duplicate"):
            with self.subTest(mutation=mutation):
                original = deepcopy(self.provenance["records"])
                if mutation == "missing":
                    self.provenance["records"] = original[:-1]
                else:
                    self.provenance["records"] = original + [deepcopy(original[-1])]
                self.rewrite()
                self.assert_kind("invalid_policy")
                self.provenance["records"] = original
                self.rewrite()

    def test_owner_coordinates_request_digests_and_source_digests_fail_closed(self) -> None:
        self.assert_kind("invalid_policy", owner_repo_id="another-owner")
        request = deepcopy(self.request)
        request["expected_routing_policy_digest"] = "sha256:" + "0" * 64
        self.assert_kind("invalid_policy", request=request)
        self.provenance["records"][0]["source_content_digest"] = "sha256:" + "0" * 64
        self.rewrite()
        self.assert_kind("invalid_policy")

    def test_git_subprocess_environment_flags_hooks_and_network_are_closed(self) -> None:
        real_run = subprocess.run
        calls: list[tuple[list[str], dict[str, object]]] = []

        def observed(*args: object, **kwargs: object):
            calls.append((list(args[0]), dict(kwargs)))
            return real_run(*args, **kwargs)

        with patch.object(policy_io.subprocess, "run", side_effect=observed):
            with self.capture():
                pass
        self.assertTrue(calls)
        for command, kwargs in calls:
            self.assertEqual(command[0], "/usr/bin/git")
            self.assertIn("--no-replace-objects", command)
            self.assertTrue(any(item.startswith("--git-dir=/proc/self/fd/") for item in command))
            self.assertIn("core.hooksPath=/dev/null", command)
            self.assertIn("protocol.allow=never", command)
            self.assertEqual(kwargs["cwd"], "/")
            self.assertEqual(kwargs["env"], policy_io._GIT_ENV)
            self.assertEqual(kwargs["stderr"], subprocess.DEVNULL)
            self.assertTrue(kwargs["pass_fds"])
        self.assertEqual(policy_io._GIT_ENV["GIT_CONFIG_NOSYSTEM"], "1")
        self.assertEqual(policy_io._GIT_ENV["GIT_CONFIG_GLOBAL"], "/dev/null")
        self.assertEqual(policy_io._GIT_ENV["GIT_ALLOW_PROTOCOL"], "")
        self.assertEqual(policy_io._GIT_ENV["GIT_NO_LAZY_FETCH"], "1")
        self.assertTrue(all(hasattr(kwargs["stdout"], "write") for _, kwargs in calls))
        self.assertTrue(all(callable(kwargs["preexec_fn"]) for _, kwargs in calls))

    def test_git_output_is_bounded_before_parent_allocation(self) -> None:
        def overflowing(*_args: object, **kwargs: object):
            kwargs["stdout"].write(b"x" * (1_048_576 + 1))
            return subprocess.CompletedProcess([], 0)
        with patch.object(policy_io.subprocess, "run", side_effect=overflowing):
            self.assert_kind("internal")

    def test_sources_are_read_from_committed_objects_not_worktree(self) -> None:
        (self.owner_root / "authority.txt").write_bytes(b"hostile worktree authority")
        (self.owner_root / "record.txt").unlink()
        with self.capture() as captured:
            raws = [item.raw for item in captured._git.verified]
            self.assertIn(b"synthetic authority\n", raws)
            self.assertIn(b"synthetic record\n", raws)

    def test_replace_refs_alternates_shallow_partial_and_promisor_repositories_fail(self) -> None:
        (self.owner_root / ".git/commondir").write_text("../external\n")
        self.assert_kind("invalid_policy")
        (self.owner_root / ".git/commondir").unlink()

        revision = self.git("rev-parse", "HEAD").stdout.decode().strip()
        hazards = (
            ("replace", lambda: self.git("update-ref", f"refs/replace/{revision}", revision),
             lambda: self.git("update-ref", "-d", f"refs/replace/{revision}")),
            ("alternates", lambda: (self.owner_root / ".git/objects/info/alternates").write_text("\n"),
             lambda: (self.owner_root / ".git/objects/info/alternates").unlink()),
            ("shallow", lambda: (self.owner_root / ".git/shallow").write_text(revision + "\n"),
             lambda: (self.owner_root / ".git/shallow").unlink()),
            ("partial", lambda: self.git("config", "extensions.partialClone", "origin"),
             lambda: self.git("config", "--unset", "extensions.partialClone")),
            ("promisor", lambda: self.git("config", "remote.origin.promisor", "true"),
             lambda: self.git("config", "--unset", "remote.origin.promisor")),
        )
        for name, install, remove in hazards:
            with self.subTest(name=name):
                install()
                try:
                    self.assert_kind("invalid_policy")
                finally:
                    remove()

    def test_missing_revisions_paths_and_objects_fail_without_worktree_fallback(self) -> None:
        original = deepcopy(self.provenance["records"])
        self.provenance["records"][0]["source_path"] = "missing.txt"
        self.rewrite()
        self.assert_kind("invalid_policy")
        self.provenance["records"] = deepcopy(original)
        self.provenance["records"][0]["source_revision"] = "0" * 40
        self.rewrite()
        self.assert_kind("invalid_policy")

    def test_batch_check_rejects_large_blob_before_batch_content_read(self) -> None:
        self.materialize(record_raw=b"x" * 20_000)
        request = deepcopy(self.request)
        request["route_limits"]["policy_bytes"] = len((self.policy_root / "policy.json").read_bytes()) + 100
        commands: list[list[str]] = []
        real_run = subprocess.run

        def observed(*args: object, **kwargs: object):
            commands.append(list(args[0]))
            return real_run(*args, **kwargs)

        with patch.object(policy_io.subprocess, "run", side_effect=observed):
            self.assert_kind("resource_exhausted", request=request)
        cat_commands = [command for command in commands if "cat-file" in command]
        self.assertTrue(any(any(item.startswith("--batch-check=") for item in command) for command in cat_commands))
        self.assertFalse(any("--batch" in command for command in cat_commands))

    def test_cumulative_provenance_source_bytes_share_policy_limit(self) -> None:
        self.materialize(record_raw=b"x" * 1_000)
        request = deepcopy(self.request)
        policy_size = len((self.policy_root / "policy.json").read_bytes())
        self.assertLess(policy_size, 6_000)
        request["route_limits"]["policy_bytes"] = max(policy_size, 1_000) + 10
        self.assertLess(1_000, request["route_limits"]["policy_bytes"])
        self.assert_kind("resource_exhausted", request=request)

    def test_source_object_change_after_capture_is_snapshot_changed(self) -> None:
        revision = self.policy["authority"]["revision"]
        oid = self.git("rev-parse", f"{revision}:record.txt").stdout.decode().strip()
        loose = self.owner_root / ".git" / "objects" / oid[:2] / oid[2:]
        self.assertTrue(loose.is_file())
        with self.assertRaises(RouteProtocolError) as caught:
            with self.capture():
                loose.unlink()
        self.assertEqual(caught.exception.kind, "snapshot_changed")

    def test_operational_git_failure_is_fixed_internal_error_not_abstention(self) -> None:
        with patch.object(policy_io, "_GIT", str(self.base / "missing-git")):
            error = self.assert_kind("internal")
        self.assertNotIn(str(self.base), str(error))
        self.assertNotIn(self.request["query"], str(error))


if __name__ == "__main__":
    unittest.main()
