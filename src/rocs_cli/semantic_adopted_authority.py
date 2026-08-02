from __future__ import annotations
import base64, hashlib, os, re, resource, stat, subprocess, tempfile
from datetime import date
from decimal import Decimal
from dataclasses import dataclass
from typing import Any, Mapping, Sequence
from rocs_cli.semantic_adopted_digests import domain_digest, object_digest
from rocs_cli.semantic_adopted_protocol import jcs_bytes, strict_json_loads, validate_definition
from rocs_cli.semantic_router_invariants import validate_invariants as validate_v0_invariants
from rocs_cli.semantic_router_protocol import RouteProtocolError, parse_policy_bytes, parse_provenance_bytes
OWNER_REPOSITORY = "softwareco/ontology"
ROLE_ORDER = ("semantic_owner", "policy_author", "development_author", "acceptance_author",
              "operational_author", "annotator", "annotator", "adjudicator", "custodian",
              "independent_reviewer", "evaluator_operator", "implementer")
_STAMP = re.compile(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?(Z|[+-]\d{2}:\d{2})$")
_IDENTITY_FIELDS = ("repository_id", "git_commit", "git_tree", "principal_id", "authority_role")
class AdoptedAuthorityError(ValueError):
    pass
@dataclass(frozen=True)
class CandidateSupport:
    policy: dict[str, Any]
    provenance: dict[str, Any]
    policy_concept_ids: tuple[str, ...]
    joint_route_ontology_id_sets: tuple[tuple[str, ...], ...]
def _fail(message: str) -> None:
    raise AdoptedAuthorityError(message)
def _schema(value: Any, definition: str) -> None:
    try:
        issues = validate_definition(value, definition)
    except (TypeError, ValueError) as exc:
        raise AdoptedAuthorityError(f"invalid {definition}") from exc
    if issues:
        _fail(f"invalid {definition}: {issues[0].instance_path or '/'}")
def _sha(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()
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
_GIT_ENV = {
    "PATH": "/usr/bin:/bin", "HOME": "/nonexistent", "LANG": "C", "LC_ALL": "C",
    "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_SYSTEM": "/dev/null", "GIT_TERMINAL_PROMPT": "0",
    "GIT_ALLOW_PROTOCOL": "", "GIT_NO_LAZY_FETCH": "1", "GIT_OPTIONAL_LOCKS": "0",
    "GIT_PAGER": "cat", "PAGER": "cat",
}
_MAX_FILE, _MAX_PROVENANCE, _MAX_SOURCE_TOTAL = 1_048_576, 8_388_608, 8_388_608
_MAX_CONTENT_TOTAL, _MAX_METADATA = 18_874_368, 16_777_216
def _git_root(value: os.PathLike[str] | str) -> tuple[str, str]:
    raw = os.fspath(value)
    if type(raw) is not str or not os.path.isabs(raw) or os.path.normpath(raw) != raw:
        _fail("local Git root must be an explicit canonical absolute path")
    try:
        current = "/"
        for part in raw.split("/")[1:]:
            current = os.path.join(current, part)
            if stat.S_ISLNK(os.lstat(current).st_mode):
                _fail("local Git root traverses a symlink")
        git_dir = os.path.join(raw, ".git")
        if not stat.S_ISDIR(os.lstat(git_dir).st_mode):
            _fail("local Git root is not a non-linked repository")
        objects = os.path.join(git_dir, "objects")
        if not stat.S_ISDIR(os.lstat(objects).st_mode):
            _fail("local Git object directory differs")
    except OSError as exc:
        raise AdoptedAuthorityError("local Git root is unavailable") from exc
    return raw, git_dir
def _repo_fingerprint(root: str, git_dir: str) -> tuple[tuple[int, int, int, int], ...]:
    try:
        return tuple((s.st_dev, s.st_ino, s.st_mode, s.st_mtime_ns) for s in map(os.lstat, (root, git_dir, os.path.join(git_dir, "objects"), os.path.join(git_dir, "config"))))
    except OSError as exc:
        raise AdoptedAuthorityError("local Git snapshot changed") from exc
def _unsafe_state(git_dir: str) -> tuple[tuple[str, int, int, int], ...]:
    forbidden = (
        "commondir", "shallow", "info/grafts", "objects/info/alternates",
        "objects/info/http-alternates",
    )
    result = []
    try:
        for relative in forbidden:
            path = os.path.join(git_dir, relative)
            try:
                info = os.lstat(path)
            except FileNotFoundError:
                continue
            result.append((relative, info.st_mode, info.st_size, info.st_mtime_ns))
        objects = os.path.join(git_dir, "objects")
        entries = list(os.scandir(objects))
        if len(entries) > 100_000 or any(item.is_symlink() for item in entries):
            result.append(("object-layout", 0, 0, 0))
        pack = os.path.join(objects, "pack")
        packs = list(os.scandir(pack)) if os.path.isdir(pack) else []
        if len(packs) > 100_000 or any(item.is_symlink() or item.name.endswith(".promisor") for item in packs):
            result.append(("promisor-or-linked-pack", 0, 0, 0))
        loose_total = 0
        for entry in entries:
            if len(entry.name) == 2 and entry.is_dir(follow_symlinks=False):
                loose = list(os.scandir(entry.path)); loose_total += len(loose)
                if loose_total > 100_000 or any(item.is_symlink() for item in loose):
                    result.append(("linked-or-excess-loose-object", 0, 0, 0))
        config = os.path.join(git_dir, "config")
        info = os.lstat(config)
        if not stat.S_ISREG(info.st_mode) or info.st_size > _MAX_FILE:
            result.append(("config", info.st_mode, info.st_size, info.st_mtime_ns))
    except OSError as exc:
        raise AdoptedAuthorityError("unsafe local Git state") from exc
    return tuple(result)
def _run_git(git_dir: str, args: Sequence[str], *, data: bytes = b"", limit: int) -> bytes:
    if len(data) > _MAX_METADATA:
        _fail("Git inspection input exceeds aggregate bound")
    command = [
        _GIT, "--no-replace-objects", f"--git-dir={git_dir}",
        "-c", "core.hooksPath=/dev/null", "-c", "credential.helper=",
        "-c", "protocol.allow=never", "-c", "maintenance.auto=false", *args,
    ]
    def bound() -> None:
        resource.setrlimit(resource.RLIMIT_FSIZE, (limit + 1, limit + 1))
    try:
        with tempfile.TemporaryFile() as output:
            completed = subprocess.run(
                command, cwd="/", env=dict(_GIT_ENV), input=data, stdout=output,
                stderr=subprocess.DEVNULL, timeout=30, check=False, preexec_fn=bound,
            )
            output.seek(0)
            raw = output.read(limit + 1)
    except (OSError, subprocess.SubprocessError) as exc:
        raise AdoptedAuthorityError("bounded local Git inspection failed") from exc
    if completed.returncode or len(raw) > limit:
        _fail("bounded local Git inspection failed")
    return raw
def _safe_config(raw: bytes) -> None:
    try:
        keys = [item.split(b"\n", 1)[0].decode("ascii").lower() for item in raw.split(b"\0") if item]
    except UnicodeError as exc:
        raise AdoptedAuthorityError("unsafe local Git config") from exc
    if any(
        key.startswith("include.") or key.startswith("includeif.")
        or key in ("extensions.partialclone", "extensions.worktreeconfig", "core.alternaterefscommand")
        or key == "extensions.objectformat"
        or (key.startswith("remote.") and (key.endswith(".promisor") or key.endswith(".partialclonefilter")))
        for key in keys
    ):
        _fail("unsafe local Git config")
def _batch_check(raw: bytes, count: int) -> list[tuple[str, str, int]]:
    lines = raw.splitlines()
    if len(lines) != count:
        _fail("Git object inventory differs")
    result = []
    for line in lines:
        fields = line.split()
        if len(fields) != 3 or len(fields[0]) != 40 or not fields[2].isdigit():
            _fail("Git object inventory differs")
        try:
            result.append((fields[0].decode("ascii"), fields[1].decode("ascii"), int(fields[2])))
        except (UnicodeError, ValueError) as exc:
            raise AdoptedAuthorityError("Git object inventory differs") from exc
    return result
def _tree_modes(raw: bytes) -> dict[str, tuple[str, str]]:
    result = {}
    for row in raw.split(b"\0"):
        if not row:
            continue
        metadata, separator, path = row.partition(b"\t")
        fields = metadata.split()
        if not separator or len(fields) != 3:
            _fail("Git tree inventory differs")
        try:
            name = path.decode("utf-8", "strict")
            value = (fields[0].decode("ascii"), fields[2].decode("ascii"))
        except UnicodeError as exc:
            raise AdoptedAuthorityError("Git tree inventory differs") from exc
        if name in result:
            _fail("Git tree inventory contains duplicate paths")
        result[name] = value
    return result
def _batch_content(raw: bytes, checked: Sequence[tuple[str, str, int]]) -> list[bytes]:
    offset = 0
    result = []
    for oid, kind, size in checked:
        end = raw.find(b"\n", offset)
        fields = raw[offset:end].split() if end >= 0 else []
        if fields != [oid.encode(), kind.encode(), str(size).encode()]:
            _fail("Git batch content framing differs")
        start, finish = end + 1, end + 1 + size
        if finish >= len(raw) or raw[finish:finish + 1] != b"\n":
            _fail("Git batch content framing differs")
        result.append(raw[start:finish])
        offset = finish + 1
    if offset != len(raw):
        _fail("Git batch content has trailing output")
    return result
def _git_blobs(
    local_git_root: os.PathLike[str] | str, commit: str, tree: str,
    expected: Mapping[str, tuple[str, bytes | None, str]],
) -> dict[str, bytes]:
    root, git_dir = _git_root(local_git_root)
    fingerprint = _repo_fingerprint(root, git_dir)
    if _unsafe_state(git_dir):
        _fail("unsafe local Git state")
    config_before = _run_git(git_dir, ["config", "--local", "--no-includes", "--null", "--list"], limit=_MAX_FILE)
    _safe_config(config_before)
    replace_before = _run_git(git_dir, ["for-each-ref", "--format=%(refname)", "refs/replace"], limit=65_536)
    if replace_before.strip():
        _fail("unsafe local Git replace state")
    expressions = [commit, f"{commit}^{{tree}}", *(f"{commit}:{path}" for path in expected)]
    request = b"".join(item.encode("ascii") + b"\n" for item in expressions)
    check_args = ["cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)"]
    checked_raw = _run_git(git_dir, check_args, data=request, limit=_MAX_METADATA)
    checked = _batch_check(checked_raw, len(expressions))
    if checked[0][0:2] != (commit, "commit") or checked[1][0:2] != (tree, "tree"):
        _fail("candidate commit/tree resolution differs")
    blobs = checked[2:]
    tree_raw = _run_git(git_dir, ["ls-tree", "-rz", "--full-tree", commit], limit=_MAX_METADATA)
    modes = _tree_modes(tree_raw)
    source_total = content_total = 0
    for (path, (digest, supplied, category)), (oid, kind, size) in zip(expected.items(), blobs):
        mode = modes.get(path); allowed_modes = ("100644", "100755") if category == "source" else ("100644",)
        if kind != "blob" or mode is None or mode[0] not in allowed_modes or mode[1] != oid:
            _fail("candidate path is not one exact permitted blob")
        limit = _MAX_PROVENANCE if category == "provenance" else _MAX_FILE
        if size > limit:
            _fail("candidate Git blob exceeds category byte limit")
        content_total += size
        if category == "source":
            source_total += size
        if supplied is not None and len(supplied) != size:
            _fail("supplied bytes differ from Git blob size")
        if len(digest) != 71:
            _fail("source digest coordinate differs")
    if source_total > _MAX_SOURCE_TOTAL or content_total > _MAX_CONTENT_TOTAL:
        _fail("candidate Git blobs exceed aggregate byte limit")
    oid_request = b"".join(oid.encode("ascii") + b"\n" for oid, _kind, _size in blobs)
    content_limit = content_total + len(blobs) * 128 + 1024
    content_raw = _run_git(git_dir, ["cat-file", "--batch"], data=oid_request, limit=content_limit)
    contents = _batch_content(content_raw, blobs)
    result = {}
    for (path, (digest, supplied, _category)), raw in zip(expected.items(), contents):
        if _sha(raw) != digest or (supplied is not None and raw != supplied):
            _fail("candidate Git blob byte/digest join differs")
        result[path] = raw
    config_after = _run_git(git_dir, ["config", "--local", "--no-includes", "--null", "--list"], limit=_MAX_FILE)
    replace_after = _run_git(git_dir, ["for-each-ref", "--format=%(refname)", "refs/replace"], limit=65_536)
    checked_after = _run_git(git_dir, check_args, data=request, limit=_MAX_METADATA)
    if (
        config_after != config_before or replace_after != replace_before
        or checked_after != checked_raw or _unsafe_state(git_dir)
        or _repo_fingerprint(root, git_dir) != fingerprint
    ):
        _fail("local Git snapshot changed")
    return result
_CONTAMINATION_SURFACES = (
    "acceptance_dataset", "aliases", "development_dataset", "evaluator",
    "fixtures", "floors", "operational_dataset", "policy",
    "regression_inputs", "templates",
)
_NON_POLICY_SURFACES = tuple(item for item in _CONTAMINATION_SURFACES if item != "policy")
def verify_contamination_manifest(
    manifest: Mapping[str, Any], *, policy_source_digest: str,
    non_policy_source_digests: Mapping[str, str],
) -> None:
    _schema(manifest, "contaminationManifest")
    if type(non_policy_source_digests) is not dict or set(non_policy_source_digests) != set(_NON_POLICY_SURFACES):
        _fail("contamination coordinates are not the exact nine non-policy surfaces")
    if any(type(value) is not str for value in non_policy_source_digests.values()):
        _fail("contamination source coordinate is not a digest")
    coverage = manifest["coverage"]
    if tuple(row["surface"] for row in coverage) != _CONTAMINATION_SURFACES:
        _fail("contamination coverage is not the exact ten-surface inventory")
    expected = {"policy": policy_source_digest, **non_policy_source_digests}
    if any(row["source_digest"] != expected[row["surface"]] for row in coverage):
        _fail("contamination source digest coordinate differs")
    if manifest["manifest_digest"] != object_digest(
        "contamination_manifest", dict(manifest), "manifest_digest"
    ):
        _fail("contamination manifest digest differs")
def verify_candidate_support(
    candidate: Mapping[str, Any], *, policy_bytes: bytes, provenance_bytes: bytes,
    inventory_bytes: bytes, contamination_manifest: Mapping[str, Any],
    contamination_source_digests: Mapping[str, str],
    local_git_root: os.PathLike[str] | str,
) -> CandidateSupport:
    _schema(candidate, "candidate")
    if any(type(raw) is not bytes for raw in (policy_bytes, provenance_bytes, inventory_bytes)):
        _fail("policy, provenance, and inventory inputs must be bytes")
    try:
        inventory = strict_json_loads(inventory_bytes, max_bytes=_MAX_FILE)
    except ValueError as exc:
        raise AdoptedAuthorityError("invalid ontology inventory bytes") from exc
    _schema(inventory, "ontologyInventory")
    if candidate["owner"]["owner_repository_id"] != OWNER_REPOSITORY:
        _fail("candidate owner differs")
    if dict(candidate["ontology_inventory"]) != dict(inventory):
        _fail("supplied inventory differs from nested inventory")
    for field in ("owner", "owner_git_commit", "owner_git_tree", "ontology_snapshot_digest"):
        candidate_field = field if field != "owner" else "owner"
        inventory_field = field
        if candidate[candidate_field] != inventory[inventory_field]:
            _fail("candidate and inventory coordinates differ")
    if inventory["inventory_digest"] != object_digest(
        "ontology_inventory", dict(inventory), "inventory_digest"
    ) or candidate["ontology_inventory_digest"] != inventory["inventory_digest"]:
        _fail("ontology inventory digest differs")
    inventory_ids = inventory["ontology_ids"]
    if inventory_ids != _sorted_strings(inventory_ids):
        _fail("ontology inventory is not UTF-8 sorted")
    selectable = candidate["selectable_ontology_ids"]
    if selectable != _sorted_strings(selectable) or not set(selectable) <= set(inventory_ids):
        _fail("selectable IDs lack exact inventory authority")
    try:
        policy = parse_policy_bytes(policy_bytes)
        provenance = parse_provenance_bytes(provenance_bytes)
    except RouteProtocolError as exc:
        raise AdoptedAuthorityError("invalid Decision 102 policy/provenance bytes") from exc
    failures = validate_v0_invariants(policy, "routingPolicy", provenance=provenance)
    failures += validate_v0_invariants(provenance, "provenanceManifest", policy=policy)
    if failures:
        _fail("Decision 102 policy/provenance invariants differ")
    if policy["authority"]["owner_repo"] != OWNER_REPOSITORY or provenance["policy_owner_repo"] != OWNER_REPOSITORY:
        _fail("Decision 102 policy owner differs")
    if any(record["source_owner_repo"] != OWNER_REPOSITORY for record in provenance["records"]):
        _fail("Decision 102 provenance source owner differs")
    if candidate["routing_policy_digest"] != policy["routing_policy_digest"] or candidate["provenance_manifest_digest"] != provenance["provenance_manifest_digest"]:
        _fail("candidate Decision 102 digest join differs")
    concepts = _sorted_strings([item["ont_id"] for item in policy["concepts"]])
    joints = [_sorted_strings(item["ont_ids"]) for item in policy["joint_routes"]]
    joints.sort(key=jcs_bytes)
    if len(concepts) != len(set(concepts)) or any(len(row) != len(set(row)) for row in joints):
        _fail("Decision 102 ontology projection is not a set")
    supported = set(selectable) & set(inventory_ids)
    if any(item not in supported for item in concepts) or any(item not in supported for row in joints for item in row):
        _fail("policy ID lacks candidate and inventory membership")
    binding = candidate["policy_semantic_binding"]
    receipt = binding["binding_receipt"]
    source_owners = [OWNER_REPOSITORY]
    expected_receipt = {
        "schema": "semantic-routing-policy-binding-receipt.v1",
        "extractor_algorithm": "rocs-adopted-policy-binding-v1",
        "routing_policy_digest": policy["routing_policy_digest"],
        "provenance_manifest_digest": provenance["provenance_manifest_digest"],
        "inventory_digest": inventory["inventory_digest"],
        "policy_owner_repository_id": OWNER_REPOSITORY,
        "provenance_policy_owner_repository_id": OWNER_REPOSITORY,
        "provenance_source_owner_repository_ids": source_owners,
        "policy_concept_ids_digest": domain_digest("policy_concept_ids", concepts),
        "joint_route_sets_digest": domain_digest("joint_route_sets", joints),
    }
    if {key: receipt.get(key) for key in expected_receipt} != expected_receipt:
        _fail("binding receipt projection differs")
    if receipt["receipt_digest"] != object_digest("policy_binding_receipt", receipt, "receipt_digest"):
        _fail("binding receipt digest differs")
    expected_binding = {
        "policy_owner_repository_id": OWNER_REPOSITORY,
        "provenance_owner_repository_id": OWNER_REPOSITORY,
        "inventory_digest": inventory["inventory_digest"],
        "policy_concept_ids": concepts,
        "joint_route_ontology_id_sets": joints,
        "provenance_source_owner_repository_ids": source_owners,
        "binding_receipt": receipt,
        "binding_receipt_digest": receipt["receipt_digest"],
    }
    if {key: binding.get(key) for key in expected_binding} != expected_binding:
        _fail("policy semantic binding projection differs")
    if binding["binding_digest"] != object_digest("policy_semantic_binding", binding, "binding_digest"):
        _fail("policy semantic binding digest differs")
    verify_contamination_manifest(
        contamination_manifest, policy_source_digest=policy["routing_policy_digest"],
        non_policy_source_digests=contamination_source_digests,
    )
    if candidate["contamination_manifest_digest"] != contamination_manifest["manifest_digest"]:
        _fail("candidate contamination manifest digest differs")
    if len(policy_bytes) > _MAX_FILE or len(provenance_bytes) > _MAX_PROVENANCE:
        _fail("candidate policy/provenance exceeds byte limits")
    expected_sources: dict[str, tuple[str, bytes | None, str]] = {}
    commit = candidate["owner_git_commit"]
    def add(path: str, digest: str, raw: bytes | None, category: str) -> None:
        value = (digest, raw, category)
        previous = expected_sources.setdefault(path, value)
        if previous != value:
            _fail("one candidate path is claimed with different coordinates")
    add(candidate["policy_path"], _sha(policy_bytes), policy_bytes, "policy")
    add(candidate["provenance_path"], _sha(provenance_bytes), provenance_bytes, "provenance")
    add(candidate["ontology_inventory_path"], _sha(inventory_bytes), inventory_bytes, "inventory")
    authority = policy["authority"]
    if authority["revision"] != commit or provenance["policy_revision"] != commit:
        _fail("Decision 102 authority revision is not the candidate commit")
    add(authority["path"], authority["source_content_digest"], None, "source")
    for record in provenance["records"]:
        if record["source_revision"] != commit:
            _fail("Decision 102 provenance revision is not the candidate commit")
        add(record["source_path"], record["source_content_digest"], None, "source")
    _git_blobs(local_git_root, commit, candidate["owner_git_tree"], expected_sources)
    if candidate["candidate_digest"] != object_digest("candidate", dict(candidate), "candidate_digest"):
        _fail("candidate digest differs")
    return CandidateSupport(policy, provenance, tuple(concepts), tuple(tuple(row) for row in joints))
