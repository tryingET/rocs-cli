from __future__ import annotations
import base64, hashlib, os, re, resource, stat, subprocess, tempfile
from datetime import date
from decimal import Decimal
from dataclasses import dataclass
from typing import Any, Mapping, Sequence
from rocs_cli.semantic_adopted_digests import domain_digest, object_digest
from rocs_cli.semantic_adopted_protocol import jcs_bytes, strict_json_loads, validate_definition, validate_readiness_inventory
from rocs_cli.semantic_router_invariants import validate_invariants as validate_v0_invariants
from rocs_cli.semantic_router_protocol import RouteProtocolError, parse_policy_bytes, parse_provenance_bytes
from rocs_cli.semantic_adopted_signatures import AdoptedSignatureError, verify_pinned_ed25519
OWNER_REPOSITORY = "softwareco/ontology"
ROLE_ORDER = ("semantic_owner", "policy_author", "development_author", "acceptance_author", "operational_author", "annotator", "annotator", "adjudicator", "custodian", "independent_reviewer", "evaluator_operator", "implementer")
_STAMP = re.compile(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?(Z|[+-]\d{2}:\d{2})$")
_IDENTITY_FIELDS = ("repository_id", "git_commit", "git_tree", "principal_id", "authority_role")
class AdoptedAuthorityError(ValueError):
    kind: str
    def __init__(self, message: str, *, kind: str = "invalid_authority"):
        super().__init__(message); self.kind = kind
@dataclass(frozen=True)
class CandidateSupport:
    candidate_bytes: bytes; candidate_digest: str
    policy: dict[str, Any]; provenance: dict[str, Any]
    policy_concept_ids: tuple[str, ...]; joint_route_ontology_id_sets: tuple[tuple[str, ...], ...]
def _fail(message: str) -> None: raise AdoptedAuthorityError(message)
def _exhaust(message: str) -> None: raise AdoptedAuthorityError(message, kind="resource_exhausted")
def _schema(value: Any, definition: str) -> None:
    try:
        issues = validate_definition(value, definition)
    except (TypeError, ValueError) as exc:
        raise AdoptedAuthorityError(f"invalid {definition}") from exc
    if issues:
        _fail(f"invalid {definition}: {issues[0].instance_path or '/'}")
def _sha(raw: bytes) -> str: return "sha256:" + hashlib.sha256(raw).hexdigest()
def _sorted_strings(values: Sequence[str]) -> list[str]:
    return sorted(values, key=lambda value: value.encode("utf-8"))
def verify_authority_credential(
    authority: Mapping[str, Any], credential: Mapping[str, Any], *, trusted_now: str
) -> None:
    _schema(authority, "authorityCoordinate")
    _schema(credential, "authorityCredential")
    if any(authority[field] != credential[field] for field in _IDENTITY_FIELDS):
        _fail("authority and credential identity differ")
    if authority["authority_credential_digest"] != credential["credential_digest"]:
        _fail("authority credential digest differs")
    try:
        key = base64.b64decode(credential["public_key_base64"], validate=True)
    except (ValueError, TypeError) as exc:
        raise AdoptedAuthorityError("invalid credential public key") from exc
    if len(key) != 32 or base64.b64encode(key).decode("ascii") != credential["public_key_base64"]:
        _fail("credential public key is not canonical raw Ed25519")
    if credential["public_key_digest"] != _sha(key):
        _fail("credential public key digest differs")
    if credential["credential_digest"] != object_digest(
        "authority_credential", dict(credential), "credential_digest"
    ):
        _fail("credential digest differs")
    def instant(value: str) -> Decimal:
        match = _STAMP.fullmatch(value)
        if match is None:  # already excluded by schema; keeps this helper total
            _fail("credential validity timestamp differs")
        year, month, day, hour, minute, second = map(int, match.groups()[:6])
        fraction, zone = match.group(7) or "0", match.group(8)
        offset = 0
        if zone != "Z":
            sign = 1 if zone[0] == "+" else -1
            offset = sign * (int(zone[1:3]) * 3600 + int(zone[4:6]) * 60)
        whole = date(year, month, day).toordinal() * 86400 + hour * 3600 + minute * 60 + second
        return Decimal(whole - offset) + Decimal("0." + fraction)
    _schema(trusted_now, "dateTime")
    start = instant(credential["valid_from"])
    end = instant(credential["valid_until"])
    now = instant(trusted_now)
    if start >= end or now < start or now >= end:
        _fail("credential is outside its trusted validity interval")
    if credential["revoked"] is not False:
        _fail("credential is revoked")
def verify_principal_separation(participants: Sequence[Mapping[str, Any]]) -> None:
    if type(participants) not in (list, tuple) or len(participants) != 12:
        _fail("participants must contain exactly twelve assignments")
    for participant in participants:
        _schema(participant, "roleAssignment")
    roles = tuple(item["role"] for item in participants)
    if roles != ROLE_ORDER:
        _fail("participant roles are not in canonical order")
    principals = [item["authority"]["principal_id"] for item in participants]
    if len(set(principals)) != 12:
        _fail("participant principals are not pairwise distinct")
    assessors = [item["b0_exposure_evidence"]["assessor_authority"] for item in participants]
    if any(assessor != assessors[0] for assessor in assessors):
        _fail("B0 evidence does not use one independent assessor")
    assessor = assessors[0]
    if assessor["authority_role"] != "independent_reviewer" or assessor["principal_id"] in principals:
        _fail("B0 assessor is not a distinct independent reviewer")
    access_order = {
        name: index for index, name in enumerate((
            "ontology_sources", "development_rows", "sealed_acceptance_rows",
            "sealed_operational_rows", "blind_labels", "aggregate_verdict",
            "policy_bytes", "evaluator_bytes",
        ))
    }
    for item in participants:
        authority = item["authority"]
        evidence = item["b0_exposure_evidence"]
        if authority["authority_role"] != item["role"]:
            _fail("authority role differs from assignment")
        if evidence["participant_principal_id"] != authority["principal_id"]:
            _fail("exposure evidence names another principal")
        if evidence["result"] != item["b0_exposure"]:
            _fail("exposure evidence result differs")
        if evidence["evidence_digest"] != item["b0_exposure_evidence_digest"]:
            _fail("exposure evidence digest join differs")
        if evidence["evidence_digest"] != object_digest(
            "b0_exposure_evidence", evidence, "evidence_digest"
        ):
            _fail("exposure evidence digest differs")
        if item["access"] != sorted(item["access"], key=access_order.__getitem__):
            _fail("assignment access is not in canonical matrix order")
        if evidence["assessor_authority"]["principal_id"] == authority["principal_id"]:
            _fail("B0 evidence is self-assessed")
        sealed = {"sealed_acceptance_rows", "sealed_operational_rows"} & set(item["access"])
        if "policy_bytes" in item["access"] and sealed:
            _fail("participant has policy and sealed-row access")
        if item["role"] in ("policy_author", "development_author", "evaluator_operator") and sealed:
            _fail("canonical role matrix grants forbidden sealed-row access")
    for index in (3, 4, 5, 6, 7, 8, 9, 10):
        if participants[index]["b0_exposure"] != "disproven":
            _fail("protected participant B0 exposure is not disproven")
def verify_role_separation_receipt(
    participants: Sequence[Mapping[str, Any]], receipt: Mapping[str, Any],
    *, access_history_digest: str,
) -> None:
    verify_principal_separation(participants)
    _schema(receipt, "roleSeparationReceipt")
    if receipt["participants_digest"] != _sha(jcs_bytes(list(participants))):
        _fail("participant array digest differs")
    if receipt["access_history_digest"] != access_history_digest:
        _fail("access history digest differs")
    if receipt["receipt_digest"] != object_digest(
        "role_separation_receipt", dict(receipt), "receipt_digest"
    ):
        _fail("role separation receipt digest differs")
_GIT = "/usr/bin/git"
_GIT_ENV = {"PATH": "/usr/bin:/bin", "HOME": "/nonexistent", "LANG": "C", "LC_ALL": "C", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null", "GIT_TERMINAL_PROMPT": "0", "GIT_ALLOW_PROTOCOL": "", "GIT_NO_LAZY_FETCH": "1", "GIT_OPTIONAL_LOCKS": "0", "GIT_PAGER": "cat", "PAGER": "cat"}
_MAX_FILE, _MAX_PROVENANCE, _MAX_SOURCE_TOTAL = 1_048_576, 8_388_608, 1_048_576
_MAX_CONTENT_TOTAL, _MAX_METADATA = 11_534_336, 16_777_216
_MAX_OBJECTS, _MAX_RECORDS, _MAX_STDOUT, _MAX_STDOUT_TOTAL = 16_384, 16_384, 12_582_912, 16_777_216
_MAX_STDERR, _MAX_STDERR_TOTAL, _MAX_GIT_PROCESSES = 65_536, 524_288, 8
def _acquisition_bounds(policy: int, provenance: int, inventory: int, sources: Sequence[int] = (), contents: Sequence[int] = (), records: int = 0, objects: int = 0) -> None:
    if policy > _MAX_FILE or provenance > _MAX_PROVENANCE or inventory > _MAX_FILE or any(x > _MAX_FILE for x in sources): _exhaust("acquisition category byte limit exceeded")
    if sum(sources) > _MAX_SOURCE_TOTAL or sum(contents) > _MAX_CONTENT_TOTAL: _exhaust("acquisition aggregate byte limit exceeded")
    if records > _MAX_RECORDS or objects > _MAX_OBJECTS: _exhaust("acquisition count limit exceeded")
@dataclass
class _GitBudget: stdout: int = 0; stderr: int = 0; processes: int = 0
def _open_root(value: os.PathLike[str] | str) -> tuple[int, str, str, tuple[int, int]]:
    raw = os.fspath(value); fd = -1
    if type(raw) is not str or not os.path.isabs(raw) or os.path.normpath(raw) != raw: _fail("local Git root must be one canonical absolute path")
    try:
        fd = os.open(raw, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW); root_info = os.fstat(fd)
        identity = root_info.st_dev, root_info.st_ino; anchor = f"/proc/self/fd/{fd}"; git_dir = anchor + "/.git"; info = os.stat(git_dir, follow_symlinks=False)
        if not stat.S_ISDIR(info.st_mode) or not stat.S_ISDIR(os.stat(git_dir + "/objects", follow_symlinks=False).st_mode): _fail("local Git root is not a repository")
        return fd, raw, git_dir, identity
    except AdoptedAuthorityError:
        if fd >= 0: os.close(fd)
        raise
    except OSError as exc:
        if fd >= 0: os.close(fd)
        raise AdoptedAuthorityError("local Git root is unavailable") from exc
def _unsafe(git_dir: str) -> bool:
    forbidden = ("commondir", "shallow", "info/grafts", "objects/info/alternates", "objects/info/http-alternates", "refs/replace")
    try:
        if any(os.path.lexists(git_dir + "/" + item) for item in forbidden): return True
        packed = git_dir + "/packed-refs"
        if os.path.exists(packed):
            size = os.path.getsize(packed)
            if size > _MAX_FILE: _exhaust("packed refs exceeds byte bound")
            with open(packed, "rb") as stream:
                if b" refs/replace/" in stream.read(): return True
        entries = list(os.scandir(git_dir + "/objects"))
        if len(entries) > 100_000: _exhaust("Git object layout exceeds entry bound")
        if any(item.is_symlink() for item in entries): return True
        loose = 0
        for entry in entries:
            if len(entry.name) == 2:
                if not entry.is_dir(follow_symlinks=False): return True
                children = list(os.scandir(entry.path)); loose += len(children)
                if loose > 100_000: _exhaust("loose Git objects exceed entry bound")
                if any(not child.is_file(follow_symlinks=False) for child in children): return True
        pack = git_dir + "/objects/pack"
        if os.path.isdir(pack) and any(not child.is_file(follow_symlinks=False) or child.name.endswith(".promisor") for child in os.scandir(pack)): return True
        config = os.stat(git_dir + "/config", follow_symlinks=False)
        if not stat.S_ISREG(config.st_mode): return True
        if config.st_size > _MAX_FILE: _exhaust("Git config exceeds byte bound")
        return False
    except AdoptedAuthorityError: raise
    except OSError as exc: raise AdoptedAuthorityError("unsafe local Git state") from exc
def _run_git(git_dir: str, args: Sequence[str], *, budget: _GitBudget, data: bytes = b"", limit: int, repo_fd: int | None = None) -> bytes:
    if len(data) > _MAX_METADATA: _exhaust("Git inspection input exceeds aggregate bound")
    budget.processes += 1
    if budget.processes > _MAX_GIT_PROCESSES: _exhaust("Git subprocess count exceeds bound")
    out_limit = min(limit, _MAX_STDOUT, _MAX_STDOUT_TOTAL - budget.stdout); err_limit = min(_MAX_STDERR, _MAX_STDERR_TOTAL - budget.stderr)
    if out_limit < 0 or err_limit < 0: _exhaust("Git inspection output exceeds aggregate bound")
    command = [_GIT, "--no-replace-objects", f"--git-dir={git_dir}", "-c", "core.hooksPath=/dev/null", "-c", "credential.helper=", "-c", "protocol.allow=never", "-c", "maintenance.auto=false", *args]
    def bound() -> None:
        ceiling = max(out_limit, err_limit) + 1; resource.setrlimit(resource.RLIMIT_FSIZE, (ceiling, ceiling))
    try:
        with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
            done = subprocess.run(command, cwd="/", env=dict(_GIT_ENV), input=data, stdout=output, stderr=errors, timeout=30, check=False, preexec_fn=bound, pass_fds=((repo_fd,) if repo_fd is not None else ()))
            output.flush(); errors.flush(); out_size = os.fstat(output.fileno()).st_size; err_size = os.fstat(errors.fileno()).st_size; output.seek(0); raw = output.read(out_limit + 1)
    except subprocess.TimeoutExpired as exc: raise AdoptedAuthorityError("bounded Git inspection timed out", kind="resource_exhausted") from exc
    except OSError as exc: raise AdoptedAuthorityError("bounded local Git inspection failed") from exc
    budget.stdout += out_size; budget.stderr += err_size
    if out_size > out_limit or err_size > err_limit or budget.stdout > _MAX_STDOUT_TOTAL or budget.stderr > _MAX_STDERR_TOTAL: _exhaust("Git inspection output exceeds bound")
    if done.returncode:
        if done.returncode < 0 or out_size >= out_limit or err_size >= err_limit: _exhaust("bounded Git process exhausted output resource")
        _fail("bounded local Git inspection failed")
    return raw
def _safe_config(raw: bytes) -> None:
    try: keys = [x.split(b"\n", 1)[0].decode("ascii").lower() for x in raw.split(b"\0") if x]
    except UnicodeError as exc: raise AdoptedAuthorityError("unsafe local Git config") from exc
    if any(k.startswith(("include.", "includeif.")) or k in ("extensions.partialclone", "extensions.worktreeconfig", "extensions.objectformat", "core.alternaterefscommand") or (k.startswith("remote.") and k.endswith((".promisor", ".partialclonefilter"))) for k in keys): _fail("unsafe local Git config")
class _CatFile:
    def __init__(self, git_dir: str, fd: int, budget: _GitBudget):
        budget.processes += 1
        if budget.processes > _MAX_GIT_PROCESSES: _exhaust("Git subprocess count exceeds bound")
        self.budget, self.cache, self.stderr, self.content, self.object_ids = budget, {}, tempfile.TemporaryFile(), 0, set()
        command = [_GIT, "--no-replace-objects", f"--git-dir={git_dir}", "-c", "protocol.allow=never", "cat-file", "--batch"]
        try: self.process = subprocess.Popen(command, cwd="/", env=dict(_GIT_ENV), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr, pass_fds=(fd,))
        except OSError as exc: self.stderr.close(); raise AdoptedAuthorityError("bounded local Git inspection failed") from exc
    def get(self, expression: str) -> tuple[str, str, bytes]:
        if expression in self.cache: return self.cache[expression]
        try:
            assert self.process.stdin and self.process.stdout; self.process.stdin.write(expression.encode("ascii") + b"\n"); self.process.stdin.flush(); header = self.process.stdout.readline()
            fields = header.split()
            if len(fields) != 3 or len(fields[0]) != 40 or not fields[2].isdigit(): _fail("Git object coordinate differs")
            size = int(fields[2]); oid, kind = fields[0].decode(), fields[1].decode()
            if size > _MAX_CONTENT_TOTAL: _exhaust("Git object exceeds content bound")
            raw = self.process.stdout.read(size); newline = self.process.stdout.read(1)
        except AdoptedAuthorityError: raise
        except (OSError, UnicodeError, ValueError) as exc: raise AdoptedAuthorityError("Git batch framing differs") from exc
        acquired = len(header) + size + 1; self.budget.stdout += acquired
        if newline != b"\n" or len(raw) != size: _fail("Git batch framing differs")
        if acquired > _MAX_STDOUT or self.budget.stdout > _MAX_STDOUT_TOTAL: _exhaust("Git inspection stdout exceeds bound")
        if kind == "blob":
            self.content += size
            if self.content > _MAX_CONTENT_TOTAL: _exhaust("Git blob content aggregate exceeds bound")
        self.object_ids.add(oid)
        if len(self.object_ids) > _MAX_OBJECTS: _exhaust("Git unique object count exceeds bound")
        value = oid, kind, raw; self.cache[expression] = value; self.cache.setdefault(oid, value); return value
    def close(self) -> None:
        try:
            if self.process.stdin: self.process.stdin.close()
            code = self.process.wait(timeout=30); self.stderr.flush(); size = os.fstat(self.stderr.fileno()).st_size; self.budget.stderr += size
        except subprocess.TimeoutExpired as exc: self.process.kill(); raise AdoptedAuthorityError("Git batch timed out", kind="resource_exhausted") from exc
        finally:
            if self.process.stdout: self.process.stdout.close()
            self.stderr.close()
        if size > _MAX_STDERR or self.budget.stderr > _MAX_STDERR_TOTAL: _exhaust("Git inspection stderr exceeds bound")
        if code: _fail("Git batch inspection failed")
def _entries(raw: bytes) -> list[tuple[str, bytes, str]]:
    result = []; offset = 0; names = set()
    while offset < len(raw):
        space = raw.find(b" ", offset); nul = raw.find(b"\0", space + 1)
        if space < 0 or nul < 0 or nul + 21 > len(raw): _fail("Git tree framing differs")
        mode, name_raw, oid = raw[offset:space].decode("ascii"), raw[space + 1:nul], raw[nul + 1:nul + 21].hex(); offset = nul + 21
        try: name = name_raw.decode("utf-8")
        except UnicodeError as exc: raise AdoptedAuthorityError("Git tree path is not UTF-8") from exc
        if not name or "/" in name or name in names: _fail("Git tree contains duplicate/unsafe path")
        names.add(name); result.append((mode, name_raw, oid))
    return result
def _walk_tree(cat: _CatFile, expression: str, *, complete: bool) -> tuple[str, dict[str, tuple[str, str]], list[tuple[str, str]]]:
    root_oid, kind, raw = cat.get(expression)
    if kind != "tree": _fail("Git tree coordinate differs")
    paths: dict[str, tuple[str, str]] = {}; blobs = []; stack = [(b"", root_oid, raw)]; count = 0
    while stack:
        prefix, _oid, tree_raw = stack.pop()
        for mode, name, oid in _entries(tree_raw):
            count += 1
            if count > _MAX_OBJECTS: _exhaust("Git tree entry count exceeds bound")
            path_raw = prefix + name
            try: path = path_raw.decode("utf-8")
            except UnicodeError as exc: raise AdoptedAuthorityError("Git tree path is not UTF-8") from exc
            if path in paths: _fail("Git tree contains aliased path")
            paths[path] = mode, oid
            if mode == "40000":
                child_oid, child_kind, child = cat.get(oid)
                if child_kind != "tree": _fail("Git tree mode/object differs")
                stack.append((path_raw + b"/", child_oid, child))
            elif mode in ("100644", "100755"): blobs.append((path, oid))
            else: _fail("Git tree contains unsafe mode")
    return root_oid, paths, blobs
def _resolve(cat: _CatFile, revision: str, path: str) -> tuple[str, str, bytes]:
    _root, paths, _blobs = _walk_tree(cat, f"{revision}^{{tree}}", complete=False); coordinate = paths.get(path)
    if coordinate is None or coordinate[0] not in ("100644", "100755"): _fail("declared source path is not a regular blob")
    oid, kind, raw = cat.get(f"{revision}:{path}")
    if kind != "blob" or oid != coordinate[1]: _fail("declared source coordinate differs")
    return coordinate[0], oid, raw
def _git_proof(root_value: os.PathLike[str] | str, candidate: Mapping[str, Any], candidate_raw: bytes, inventory_raw: bytes, policy_raw: bytes, provenance_raw: bytes, claims: Sequence[tuple[str, str, str]], source_bytes: Mapping[tuple[str, str], bytes]) -> None:
    _acquisition_bounds(0, 0, 0, sources=[len(x) for x in source_bytes.values()] if isinstance(source_bytes, Mapping) else [_MAX_SOURCE_TOTAL + 1])
    fd, original_path, git_dir, identity = _open_root(root_value); budget = _GitBudget(); cat = None
    try:
        if _unsafe(git_dir): _fail("unsafe local Git state")
        config = _run_git(git_dir, ["config", "--local", "--no-includes", "--null", "--list"], budget=budget, limit=_MAX_FILE, repo_fd=fd); _safe_config(config)
        c, ct = candidate["owner_git_commit"], candidate["owner_git_tree"]; inv = candidate["ontology_inventory"]; i, it, ip = inv["owner_git_commit"], inv["owner_git_tree"], inv["inventory_source_path"]
        revisions = {i, *(rev for rev, _path, _digest in claims)}
        history = _run_git(git_dir, ["rev-list", c], budget=budget, limit=_MAX_METADATA, repo_fd=fd).splitlines()
        if len(history) > _MAX_OBJECTS: _exhaust("candidate ancestry count exceeds bound")
        if any(len(x) != 40 for x in history): _fail("candidate ancestry inventory differs")
        ancestors = {x.decode("ascii") for x in history[1:]}
        if history[:1] != [c.encode()] or not revisions <= ancestors: _fail("inventory/source revision is not a strict candidate ancestor")
        if c == i or ct == it: _fail("candidate and inventory commit/tree must both differ")
        cat = _CatFile(git_dir, fd, budget)
        if cat.get(c)[1] != "commit" or cat.get(i)[1] != "commit" or cat.get(f"{c}^{{tree}}")[0] != ct or cat.get(f"{i}^{{tree}}")[0] != it: _fail("commit/tree coordinate differs")
        _tree_oid, cpaths, cblobs = _walk_tree(cat, f"{c}^{{tree}}", complete=True)
        if any(cat.get(oid)[2] == candidate_raw for _path, oid in cblobs): _fail("candidate bytes are present inside candidate snapshot")
        expected_c = {candidate["policy_path"]: policy_raw, candidate["provenance_path"]: provenance_raw, ip: inventory_raw}
        for path, supplied in expected_c.items():
            mode_oid = cpaths.get(path)
            if mode_oid is None or mode_oid[0] != "100644" or cat.get(mode_oid[1])[2] != supplied: _fail("candidate artifact Git join differs")
        _imode, _ioid, i_raw = _resolve(cat, i, ip)
        if _imode != "100644" or i_raw != inventory_raw: _fail("inventory source I/C byte join differs")
        expected_keys = {(rev, path) for rev, path, _digest in claims}
        if type(source_bytes) is not dict or set(source_bytes) != expected_keys or any(type(x) is not bytes for x in source_bytes.values()): _fail("named source byte mapping differs")
        retained = {}
        for rev, path, digest in claims:
            _mode, _oid, origin = _resolve(cat, rev, path); supplied = source_bytes[(rev, path)]
            if origin != supplied or _sha(origin) != digest: _fail("declared source byte/digest join differs")
            prior = retained.setdefault(path, supplied)
            if prior != supplied: _fail("retained source aliases conflicting bytes")
        for path, supplied in retained.items():
            coordinate = cpaths.get(path)
            if coordinate is None or coordinate[0] not in ("100644", "100755") or cat.get(coordinate[1])[2] != supplied: _fail("retained source C byte/mode join differs")
        cat.close(); cat = None
        after = _run_git(git_dir, ["config", "--local", "--no-includes", "--null", "--list"], budget=budget, limit=_MAX_FILE, repo_fd=fd)
        try: path_info = os.stat(original_path, follow_symlinks=False); current = path_info.st_dev, path_info.st_ino
        except OSError as exc: raise AdoptedAuthorityError("repository root identity changed") from exc
        if after != config or _unsafe(git_dir) or (os.fstat(fd).st_dev, os.fstat(fd).st_ino) != identity or current != identity: _fail("repository descriptor identity changed")
    finally:
        if cat is not None:
            try: cat.close()
            except Exception: pass
        os.close(fd)
_CONTAMINATION_SURFACES = ("acceptance_dataset", "aliases", "development_dataset", "evaluator", "fixtures", "floors", "operational_dataset", "policy", "regression_inputs", "templates")
_NON_POLICY_SURFACES = tuple(x for x in _CONTAMINATION_SURFACES if x != "policy")
def verify_contamination_manifest(manifest: Mapping[str, Any], *, policy_source_digest: str, non_policy_source_digests: Mapping[str, str]) -> None:
    _schema(manifest, "contaminationManifest")
    if type(non_policy_source_digests) is not dict or set(non_policy_source_digests) != set(_NON_POLICY_SURFACES): _fail("contamination coordinates are not the exact nine non-policy surfaces")
    coverage = manifest["coverage"]; expected = {"policy": policy_source_digest, **non_policy_source_digests}
    if tuple(x["surface"] for x in coverage) != _CONTAMINATION_SURFACES or any(type(x) is not str for x in non_policy_source_digests.values()) or any(x["source_digest"] != expected[x["surface"]] for x in coverage): _fail("contamination source digest coordinate differs")
    if manifest["manifest_digest"] != object_digest("contamination_manifest", dict(manifest), "manifest_digest"): _fail("contamination manifest digest differs")
def _readiness(subject: Mapping[str, Any], receipt: Mapping[str, Any], request: Mapping[str, Any], inventory_raw: bytes) -> dict[str, Any]:
    _schema(subject, "custodyReadinessSubject"); _schema(receipt, "custodyReadinessReceipt"); _schema(request, "custodyReadinessVerificationRequest")
    if receipt["subject"] != subject: _fail("readiness subject preimage differs")
    inventory = subject["concept_inventory"]
    issues = validate_readiness_inventory(subject, request, inventory_raw)
    if issues: _fail(f"readiness inventory preimage differs: {issues[0].instance_path or '/'}")
    if inventory["inventory_digest"] != object_digest("ontology_inventory", inventory, "inventory_digest") or subject["subject_digest"] != object_digest("custody_readiness_subject", subject, "subject_digest") or receipt["readiness_digest"] != object_digest("custody_readiness", receipt, "readiness_digest") or request["request_digest"] != object_digest("custody_readiness_verification_request", request, "request_digest"): _fail("readiness/inventory digest differs")
    history = receipt["base_access_history"]; credential = receipt["custodian_credential"]; approval = receipt["custodian_approval"]
    if request["readiness_digest"] != receipt["readiness_digest"] or request["subject_digest"] != subject["subject_digest"] or request["expected_base_access_history"] != history or request["expected_base_access_history_digest"] != history["history_digest"] or receipt["base_access_history_digest"] != history["history_digest"] or subject["access_history_digest"] != history["history_digest"]: _fail("readiness base-history/request join differs")
    if request["expected_custodian_authority"] != subject["custodian_authority"] or request["expected_custodian_credential"] != credential or request["expected_custodian_approval_digest"] != approval["artifact_digest"] or request["expected_trust_root_digest"] != credential["trust_root_digest"] or request["expected_public_key_digest"] != credential["public_key_digest"]: _fail("readiness caller authority pin differs")
    body = approval["attestation_body"]
    if approval["issuer"] != subject["custodian_authority"] or approval["subject_digest"] != subject["subject_digest"] or approval["purpose"] != "custody_readiness" or approval["artifact_digest"] != object_digest("approval_artifact", approval, "artifact_digest") or body["body_digest"] != object_digest("approval_attestation_body", body, "body_digest"): _fail("readiness approval preimage differs")
    if history["history_digest"] != object_digest("access_history", history, "history_digest") or any(event["event_digest"] != object_digest("access_history_event", event, "event_digest") or event["previous_event_digest"] != (history["events"][n - 1]["event_digest"] if n else None) for n, event in enumerate(history["events"])): _fail("readiness base-history preimage differs")
    mirrored = ("issuer", "subject_digest", "purpose", "valid_from", "valid_until", "revoked", "trust_root_digest", "public_key_digest")
    if any(body[x] != approval[x] for x in mirrored): _fail("readiness approval body differs")
    try:
        verify_authority_credential(subject["custodian_authority"], credential, trusted_now=subject["issued_at"])
        verify_pinned_ed25519(purpose="approval", expected_purpose="approval", body_digest=body["body_digest"], public_key_base64=credential["public_key_base64"], expected_public_key_digest=request["expected_public_key_digest"], signature_base64=approval["signature_base64"], issuer=approval["issuer"], expected_issuer=request["expected_custodian_authority"], trust_root_digest=approval["trust_root_digest"], expected_trust_root_digest=request["expected_trust_root_digest"], valid_from=approval["valid_from"], valid_until=approval["valid_until"], trusted_now=subject["issued_at"], revoked=approval["revoked"])
    except (AdoptedAuthorityError, AdoptedSignatureError) as exc: raise AdoptedAuthorityError("readiness credential/signature differs") from exc
    return inventory
def verify_candidate_support(candidate_bytes: bytes, *, policy_bytes: bytes, provenance_bytes: bytes, inventory_source_bytes: bytes, source_bytes: Mapping[tuple[str, str], bytes], custody_readiness_subject: Mapping[str, Any], custody_readiness_receipt: Mapping[str, Any], custody_readiness_request: Mapping[str, Any], contamination_manifest: Mapping[str, Any], contamination_source_digests: Mapping[str, str], local_git_root: os.PathLike[str] | str) -> CandidateSupport:
    if type(candidate_bytes) is not bytes: _fail("candidate input must be canonical bytes")
    if len(candidate_bytes) > _MAX_FILE: _exhaust("candidate input exceeds byte bound")
    try: candidate = strict_json_loads(candidate_bytes, max_bytes=_MAX_FILE)
    except ValueError as exc: raise AdoptedAuthorityError("invalid candidate bytes") from exc
    if type(candidate) is not dict or jcs_bytes(candidate) != candidate_bytes: _fail("candidate bytes are not canonical JCS")
    candidate_raw = candidate_bytes; _schema(candidate, "candidate")
    if any(type(x) is not bytes for x in (policy_bytes, provenance_bytes, inventory_source_bytes)): _fail("policy, provenance, and inventory source inputs must be bytes")
    _acquisition_bounds(len(policy_bytes), len(provenance_bytes), len(inventory_source_bytes))
    inventory = _readiness(custody_readiness_subject, custody_readiness_receipt, custody_readiness_request, inventory_source_bytes)
    if candidate["owner"]["owner_repository_id"] != OWNER_REPOSITORY or inventory["owner"] != candidate["owner"] or candidate["ontology_inventory"] != inventory: _fail("candidate owner/readiness inventory differs")
    if candidate["ontology_inventory_path"] != inventory["inventory_source_path"] or candidate["ontology_snapshot_digest"] != inventory["ontology_snapshot_digest"] or candidate["ontology_inventory_digest"] != inventory["inventory_digest"] or candidate["selectable_ontology_ids"] != inventory["ontology_ids"]: _fail("candidate inventory projection differs")
    try: policy = parse_policy_bytes(policy_bytes); provenance = parse_provenance_bytes(provenance_bytes)
    except RouteProtocolError as exc: raise AdoptedAuthorityError("invalid Decision 102 policy/provenance bytes") from exc
    failures = validate_v0_invariants(policy, "routingPolicy", provenance=provenance) + validate_v0_invariants(provenance, "provenanceManifest", policy=policy)
    _acquisition_bounds(0, 0, 0, records=len(provenance["records"]))
    if failures: _fail("Decision 102 policy/provenance invariants differ")
    if policy["authority"]["owner_repo"] != OWNER_REPOSITORY or provenance["policy_owner_repo"] != OWNER_REPOSITORY or any(x["source_owner_repo"] != OWNER_REPOSITORY for x in provenance["records"]): _fail("Decision 102 source owner differs")
    if candidate["routing_policy_digest"] != policy["routing_policy_digest"] or candidate["provenance_manifest_digest"] != provenance["provenance_manifest_digest"]: _fail("candidate Decision 102 digest join differs")
    concepts = _sorted_strings([x["ont_id"] for x in policy["concepts"]]); joints = [_sorted_strings(x["ont_ids"]) for x in policy["joint_routes"]]; joints.sort(key=jcs_bytes)
    if len(concepts) != len(set(concepts)) or any(len(x) != len(set(x)) for x in joints) or any(x not in set(inventory["ontology_ids"]) for x in concepts) or any(x not in set(inventory["ontology_ids"]) for row in joints for x in row): _fail("Decision 102 ontology projection differs")
    receipt = candidate["policy_semantic_binding"]["binding_receipt"]; owners = [OWNER_REPOSITORY]
    expected_receipt = {"schema": "semantic-routing-policy-binding-receipt.v1", "extractor_algorithm": "rocs-adopted-policy-binding-v1", "routing_policy_digest": policy["routing_policy_digest"], "provenance_manifest_digest": provenance["provenance_manifest_digest"], "inventory_digest": inventory["inventory_digest"], "policy_owner_repository_id": OWNER_REPOSITORY, "provenance_policy_owner_repository_id": OWNER_REPOSITORY, "provenance_source_owner_repository_ids": owners, "policy_concept_ids_digest": domain_digest("policy_concept_ids", concepts), "joint_route_sets_digest": domain_digest("joint_route_sets", joints)}
    if {k: receipt.get(k) for k in expected_receipt} != expected_receipt or receipt["receipt_digest"] != object_digest("policy_binding_receipt", receipt, "receipt_digest"): _fail("binding receipt projection differs")
    binding = candidate["policy_semantic_binding"]; expected_binding = {"policy_owner_repository_id": OWNER_REPOSITORY, "provenance_owner_repository_id": OWNER_REPOSITORY, "inventory_digest": inventory["inventory_digest"], "policy_concept_ids": concepts, "joint_route_ontology_id_sets": joints, "provenance_source_owner_repository_ids": owners, "binding_receipt": receipt, "binding_receipt_digest": receipt["receipt_digest"]}
    if {k: binding.get(k) for k in expected_binding} != expected_binding or binding["binding_digest"] != object_digest("policy_semantic_binding", binding, "binding_digest"): _fail("policy semantic binding projection differs")
    verify_contamination_manifest(contamination_manifest, policy_source_digest=policy["routing_policy_digest"], non_policy_source_digests=contamination_source_digests)
    if candidate["contamination_manifest_digest"] != contamination_manifest["manifest_digest"]: _fail("candidate contamination manifest digest differs")
    claims = [(policy["authority"]["revision"], policy["authority"]["path"], policy["authority"]["source_content_digest"]), *( (x["source_revision"], x["source_path"], x["source_content_digest"]) for x in provenance["records"])]
    artifact_paths = {candidate["policy_path"], candidate["provenance_path"], candidate["ontology_inventory_path"]}
    if len(artifact_paths) != 3 or any(path in artifact_paths for _rev, path, _digest in claims): _fail("candidate artifact/source path alias")
    if type(source_bytes) is not dict or any(type(x) is not bytes for x in source_bytes.values()): _fail("named source byte mapping must be explicit bytes")
    source_snapshot = dict(source_bytes); _acquisition_bounds(0, 0, 0, sources=[len(x) for x in source_snapshot.values()])
    _git_proof(local_git_root, candidate, candidate_raw, inventory_source_bytes, policy_bytes, provenance_bytes, claims, source_snapshot)
    if candidate["candidate_digest"] != object_digest("candidate", dict(candidate), "candidate_digest"): _fail("candidate digest differs")
    raw = jcs_bytes(candidate)
    if raw != candidate_raw: _fail("candidate changed during verification")
    return CandidateSupport(raw, candidate["candidate_digest"], policy, provenance, tuple(concepts), tuple(tuple(x) for x in joints))
