from __future__ import annotations

import json
import os
import unittest
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from rocs_cli import semantic_router as router_module
from rocs_cli.discovery import DiscoveryError, development_tool_identity, discover
from rocs_cli.semantic_protocol import (
    ProtocolError,
    document_digest,
    jcs_bytes,
    object_digest as discovery_digest,
)
from rocs_cli.semantic_router import ROUTE_ALGORITHM, route
from rocs_cli.semantic_router_invariants import validate_bundle, validate_invariants
from rocs_cli.semantic_router_protocol import (
    SAFE_ERROR_MESSAGES,
    RouteProtocolError,
    derived_discovery_request,
    object_digest,
    route_tokens,
    shape_usage,
)
from rocs_cli.semantic_snapshot import CapturedCorpus, DiscoveryDocument

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "docs" / "project" / "semantic-router-v0" / "golden-fixtures.json"
DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64


def _clause(clause_id: str, *groups: tuple[str, list[tuple[str, str]]]) -> dict:
    return {
        "clause_id": clause_id,
        "all_of": [
            {
                "group_id": group_id,
                "any_of": [
                    {"kind": kind, "value": value} for kind, value in alternatives
                ],
            }
            for group_id, alternatives in groups
        ],
    }


def _all_clauses(policy: dict):
    for key in ("admit_any", "exclude_any"):
        yield from policy["domain"][key]
    for concept in policy["concepts"]:
        for key in ("support_any", "exclude_any"):
            yield from concept[key]
    for joint in policy["joint_routes"]:
        for key in ("support_any", "exclude_any"):
            yield from joint[key]


def _canonicalize_policy(policy: dict) -> None:
    policy["concepts"].sort(key=lambda item: item["ont_id"].encode())
    policy["joint_routes"].sort(key=lambda item: item["joint_route_id"].encode())
    for joint in policy["joint_routes"]:
        joint["ont_ids"].sort(key=str.encode)
    owners = [policy["domain"], *policy["concepts"], *policy["joint_routes"]]
    for owner in owners:
        positive = "admit_any" if "admit_any" in owner else "support_any"
        for key in (positive, "exclude_any"):
            owner[key].sort(key=lambda item: item["clause_id"].encode())
            for clause in owner[key]:
                clause["all_of"].sort(key=lambda item: item["group_id"].encode())
                for group in clause["all_of"]:
                    group["any_of"].sort(
                        key=lambda item: (
                            0 if item["kind"] == "token" else 1,
                            item["value"].encode(),
                        )
                    )


def _sync(policy: dict, provenance: dict, request: dict) -> None:
    """Rebuild exact synthetic provenance after a test policy mutation."""
    _canonicalize_policy(policy)
    authority = policy["authority"]
    provenance.update(
        {
            "policy_id": policy["policy_id"],
            "policy_owner_repo": authority["owner_repo"],
            "policy_revision": authority["revision"],
            "policy_path": authority["path"],
            "policy_source_content_digest": authority["source_content_digest"],
        }
    )
    records = []
    for clause in _all_clauses(policy):
        for group in clause["all_of"]:
            for alternative in group["any_of"]:
                records.append(
                    {
                        "clause_id": clause["clause_id"],
                        "group_id": group["group_id"],
                        "kind": alternative["kind"],
                        "value": alternative["value"],
                        "source_owner_repo": authority["owner_repo"],
                        "source_revision": authority["revision"],
                        "source_path": "synthetic/source.txt",
                        "source_content_digest": DIGEST_A,
                        "author": "synthetic-s2-author",
                        "created_at": "2026-08-01T00:00:00Z",
                        "review_ref": "synthetic-s2-review",
                        "b0_exposure": "confirmed",
                        "development_case_ids": ["SYNTHETIC_S2"],
                        "contamination_scan_receipt": DIGEST_B,
                    }
                )
    records.sort(
        key=lambda item: (
            item["clause_id"].encode(),
            item["group_id"].encode(),
            0 if item["kind"] == "token" else 1,
            item["value"].encode(),
        )
    )
    provenance["records"] = records
    provenance["provenance_manifest_digest"] = object_digest(
        "provenance_manifest", provenance
    )
    policy["provenance_manifest_digest"] = provenance[
        "provenance_manifest_digest"
    ]
    policy["routing_policy_digest"] = object_digest("routing_policy", policy)
    request["expected_provenance_manifest_digest"] = provenance[
        "provenance_manifest_digest"
    ]
    request["expected_routing_policy_digest"] = policy["routing_policy_digest"]


def _fresh() -> tuple[dict, dict, dict]:
    valid = json.loads(GOLDEN.read_text("utf-8"))["valid"]
    request = deepcopy(valid["request"])
    policy = deepcopy(valid["policy"])
    provenance = deepcopy(valid["provenance"])
    _sync(policy, provenance, request)
    return request, policy, provenance


def _document(
    ont_id: str,
    *,
    labels: tuple[str, ...] = ("fabricated",),
    synonyms: tuple[str, ...] = (),
    description: str = "conspicuously synthetic document",
    examples: tuple[str, ...] = (),
) -> DiscoveryDocument:
    raw = f"synthetic document for {ont_id}\n".encode()
    return DiscoveryDocument(
        ont_id=ont_id,
        kind="concept",
        layer="synthetic",
        layer_order=0,
        logical_path=f"reference/concepts/{ont_id}.md",
        raw=raw,
        document_digest=document_digest(raw),
        labels=labels,
        synonyms=synonyms,
        description=description,
        relations=(),
        examples=examples,
        anti_examples=(),
    )


def _corpus(*extra: DiscoveryDocument) -> CapturedCorpus:
    documents = (
        _document("synthetic.Alpha"),
        _document("synthetic.Beta"),
        *extra,
    )
    entries = [
        {
            "logical_path": document.logical_path,
            "layer": "synthetic",
            "layer_order": 0,
            "kind": "concept",
            "raw_byte_length": len(document.raw),
            "document_digest": document.document_digest,
        }
        for document in documents
    ]
    entries.sort(key=lambda item: (item["logical_path"].encode(), item["kind"]))
    snapshot = {
        "schema": "semantic-corpus-snapshot.v0",
        "profile": "review",
        "roots": [
            {
                "root_id": "synthetic",
                "layer": "synthetic",
                "layer_order": 0,
                "kind": "path",
            }
        ],
        "resolved_refs": [],
        "entries": entries,
    }
    snapshot["corpus_snapshot_digest"] = discovery_digest(
        "corpus_snapshot", snapshot
    )
    return CapturedCorpus(jcs_bytes(snapshot), tuple(documents))


def _identity() -> dict:
    return development_tool_identity(manifest_digest=DIGEST_A)


def _execute(
    request: dict, policy: dict, provenance: dict, corpus: CapturedCorpus | None = None
):
    return route(
        corpus or _corpus(),
        request,
        policy,
        provenance,
        tool_identity=_identity(),
    )


def _assert_kind(
    testcase: unittest.TestCase,
    kind: str,
    request: dict,
    policy: dict,
    provenance: dict,
    corpus: CapturedCorpus | None = None,
) -> RouteProtocolError:
    with testcase.assertRaises(RouteProtocolError) as caught:
        _execute(request, policy, provenance, corpus)
    testcase.assertEqual(caught.exception.kind, kind)
    testcase.assertEqual(str(caught.exception), SAFE_ERROR_MESSAGES[kind])
    testcase.assertIsNone(caught.exception.__cause__)
    testcase.assertIsNone(caught.exception.__context__)
    return caught.exception


def _rich_policy(
    *, joint_positive: bool = True, joint_exclusion: bool = False
) -> tuple[dict, dict, dict]:
    request, policy, provenance = _fresh()
    request["query"] = "synthetic alpha bridge synthetic beta block"
    policy["concepts"].append(
        {
            "ont_id": "synthetic.Gamma",
            "support_any": [
                _clause("c.gamma", ("g.gamma", [("token", "gamma")]))
            ],
            "exclude_any": [
                _clause("c.gamma-x", ("g.gamma-x", [("token", "block")]))
            ],
        }
    )
    exact = policy["joint_routes"][0]
    exact["support_any"] = [
        _clause(
            "j.both",
            (
                "g.joint",
                [
                    (
                        "phrase",
                        "alpha bridge synthetic beta"
                        if joint_positive
                        else "unseen fabricated phrase",
                    )
                ],
            ),
        )
    ]
    exact["exclude_any"] = (
        [_clause("j.exclusion", ("g.joint-x", [("token", "block")]))]
        if joint_exclusion
        else []
    )
    policy["joint_routes"].append(
        {
            "joint_route_id": "j.alpha-gamma",
            "ont_ids": ["synthetic.Alpha", "synthetic.Gamma"],
            "support_any": [
                _clause("j.nonexact", ("g.nonexact", [("token", "block")]))
            ],
            "exclude_any": [
                _clause("j.nonexact-x", ("g.nonexact-x", [("token", "block")]))
            ],
        }
    )
    _sync(policy, provenance, request)
    return request, policy, provenance


class SemanticRouterStateAndEvidenceTests(unittest.TestCase):
    def test_every_admission_and_routing_state_reason_row(self) -> None:
        expected = {
            "no_policy_domain_support": (
                "abstained",
                "no_policy_domain_support",
                "not_evaluated",
                "admission_abstained",
            ),
            "explicit_domain_exclusion": (
                "abstained",
                "explicit_domain_exclusion",
                "not_evaluated",
                "admission_abstained",
            ),
            "domain_support_exclusion_conflict": (
                "abstained",
                "domain_support_exclusion_conflict",
                "not_evaluated",
                "admission_abstained",
            ),
            "no_concept_support": (
                "admitted",
                "domain_support",
                "abstained",
                "no_concept_support",
            ),
            "single_supported_concept": (
                "admitted",
                "domain_support",
                "single",
                "single_supported_concept",
            ),
            "concept_support_exclusion_conflict": (
                "admitted",
                "domain_support",
                "abstained",
                "concept_support_exclusion_conflict",
            ),
            "no_joint_route": (
                "admitted",
                "domain_support",
                "ambiguous",
                "multiple_supported_without_joint_route",
            ),
            "joint_positive_absent": (
                "admitted",
                "domain_support",
                "ambiguous",
                "multiple_supported_without_joint_route",
            ),
            "joint_route_exclusion": (
                "admitted",
                "domain_support",
                "abstained",
                "joint_route_exclusion",
            ),
            "explicit_joint_route": (
                "admitted",
                "domain_support",
                "multi",
                "explicit_joint_route",
            ),
        }
        for case, states in expected.items():
            request, policy, provenance = _fresh()
            if case == "no_policy_domain_support":
                request["query"] = "quartz"
            elif case == "explicit_domain_exclusion":
                policy["domain"]["admit_any"] = [
                    _clause("d.other", ("g.other", [("token", "quartz")]))
                ]
                policy["domain"]["exclude_any"] = [
                    _clause("d.exclude", ("g.exclude", [("token", "synthetic")]))
                ]
            elif case == "domain_support_exclusion_conflict":
                policy["domain"]["exclude_any"] = [
                    _clause("d.exclude", ("g.exclude", [("token", "synthetic")]))
                ]
            elif case == "no_concept_support":
                request["query"] = "synthetic quartz"
            elif case == "single_supported_concept":
                request["query"] = "synthetic alpha"
            elif case == "concept_support_exclusion_conflict":
                policy["concepts"][0]["exclude_any"] = [
                    _clause("c.alpha-x", ("g.alpha-x", [("token", "alpha")]))
                ]
            elif case == "no_joint_route":
                policy["joint_routes"] = []
            elif case == "joint_positive_absent":
                policy["joint_routes"][0]["support_any"] = [
                    _clause(
                        "j.unseen",
                        ("g.joint", [("phrase", "unseen fabricated phrase")]),
                    )
                ]
            elif case == "joint_route_exclusion":
                policy["joint_routes"][0]["exclude_any"] = [
                    _clause(
                        "j.exclusion", ("g.joint-x", [("token", "bridge")])
                    )
                ]
            _sync(policy, provenance, request)
            result = _execute(request, policy, provenance).result
            actual = (
                result["admission"]["state"],
                result["admission"]["reason"],
                result["routing"]["state"],
                result["routing"]["reason"],
            )
            with self.subTest(case=case):
                self.assertEqual(actual, states)
                if states[0] == "abstained":
                    self.assertEqual(result["routing"]["selected_ont_ids"], [])
                    self.assertTrue(
                        all(item["scope"] == "domain" for item in result["evidence"])
                    )

    def test_exact_evidence_schedule_joint_truth_table_and_witnesses(self) -> None:
        truth_table = {
            (False, False): ("ambiguous", []),
            (False, True): ("ambiguous", ["exclusion"]),
            (True, False): ("multi", ["support"]),
            (True, True): ("abstained", ["support", "exclusion"]),
        }
        for (positive, exclusion), (state, joint_polarities) in truth_table.items():
            request, policy, provenance = _rich_policy(
                joint_positive=positive, joint_exclusion=exclusion
            )
            result = _execute(
                request,
                policy,
                provenance,
                _corpus(_document("synthetic.Gamma")),
            ).result
            evidence = result["evidence"]
            with self.subTest(positive=positive, exclusion=exclusion):
                self.assertEqual(result["routing"]["state"], state)
                self.assertEqual(
                    [
                        (item["scope"], item["ont_id"], item["clause_id"])
                        for item in evidence[:4]
                    ],
                    [
                        ("domain", None, "d.support"),
                        ("concept", "synthetic.Alpha", "c.alpha"),
                        ("concept", "synthetic.Beta", "c.beta"),
                        ("concept", "synthetic.Gamma", "c.gamma-x"),
                    ],
                )
                joint = [item for item in evidence if item["scope"] == "joint_route"]
                self.assertEqual(
                    [item["polarity"] for item in joint], joint_polarities
                )
                self.assertTrue(
                    all(item["joint_route_id"] == "j.alpha-beta" for item in joint)
                )
                self.assertFalse(
                    any(item["clause_id"].startswith("j.nonexact") for item in evidence)
                )
                tokens = route_tokens(request["query"])
                for item in evidence:
                    for witness in item["witnesses"]:
                        self.assertEqual(
                            tokens[witness["start_token"] : witness["end_token"]],
                            route_tokens(witness["value"]),
                        )
                gamma = next(item for item in evidence if item["clause_id"] == "c.gamma-x")
                self.assertEqual(gamma["polarity"], "exclusion")
                self.assertNotIn("synthetic.Gamma", result["routing"]["supported_ont_ids"])
                self.assertNotIn("synthetic.Gamma", result["routing"]["conflicted_ont_ids"])

                for mutation in ("omitted", "extra", "mis_scoped", "bad_witness"):
                    changed = deepcopy(result)
                    if mutation == "omitted":
                        changed["evidence"].pop(0)
                    elif mutation == "extra":
                        changed["evidence"].append(deepcopy(changed["evidence"][0]))
                    elif mutation == "mis_scoped":
                        changed["evidence"][0]["scope"] = "concept"
                        changed["evidence"][0]["ont_id"] = "synthetic.Alpha"
                    else:
                        changed["evidence"][0]["witnesses"][0]["start_token"] += 1
                    changed["result_digest"] = object_digest("result", changed)
                    failures = validate_invariants(
                        changed,
                        request=request,
                        policy=policy,
                        provenance=provenance,
                    )
                    self.assertTrue(failures, mutation)


class SemanticRouterBudgetTests(unittest.TestCase):
    def _budget_fixture(self):
        request, policy, provenance = _rich_policy(
            joint_positive=True, joint_exclusion=True
        )
        policy["domain"]["admit_any"][0]["all_of"] = [
            {
                "group_id": "g.domain",
                "any_of": [
                    {"kind": "token", "value": "fabricated"},
                    {"kind": "token", "value": "synthetic"},
                ],
            },
            {
                "group_id": "g.domain-second",
                "any_of": [{"kind": "token", "value": "alpha"}],
            },
        ]
        _sync(policy, provenance, request)
        corpus = _corpus(_document("synthetic.Gamma"))
        clauses = list(_all_clauses(policy))
        alternatives = [
            alternative
            for clause in clauses
            for group in clause["all_of"]
            for alternative in group["any_of"]
        ]
        limits = request["route_limits"]
        limits.update(
            {
                "policy_bytes": len(jcs_bytes(policy)),
                "provenance_bytes": len(jcs_bytes(provenance)),
                "concepts": len(policy["concepts"]),
                "clauses": len(clauses),
                "groups_per_clause": max(len(item["all_of"]) for item in clauses),
                "alternatives_per_group": max(
                    len(group["any_of"])
                    for clause in clauses
                    for group in clause["all_of"]
                ),
                "total_alternatives": len(alternatives),
                "normalized_alternative_bytes": sum(
                    len(item["value"].encode()) for item in alternatives
                ),
                "joint_routes": len(policy["joint_routes"]),
                "matching_work": len(route_tokens(request["query"]))
                * sum(len(route_tokens(item["value"])) for item in alternatives),
                "parser_depth": max(
                    shape_usage(policy)[0], shape_usage(provenance)[0]
                ),
                "collection_items": max(
                    shape_usage(policy)[1], shape_usage(provenance)[1]
                ),
            }
        )
        first = _execute(request, policy, provenance, corpus)
        limits["evidence_entries"] = len(first.result["evidence"])
        limits["witnesses"] = sum(
            len(item["witnesses"]) for item in first.result["evidence"]
        )

        # Find exact fixed points because each byte limit is itself nested in output.
        for _ in range(4):
            current = _execute(request, policy, provenance, corpus)
            size = len(jcs_bytes(current.result["discovery_result"]))
            if request["discovery_limits"]["result_bytes"] == size:
                break
            request["discovery_limits"]["result_bytes"] = size
        for _ in range(4):
            current = _execute(request, policy, provenance, corpus)
            size = len(jcs_bytes(current.result))
            if limits["result_bytes"] == size:
                break
            limits["result_bytes"] = size
        execution = _execute(request, policy, provenance, corpus)
        self.assertEqual(
            len(jcs_bytes(execution.result["discovery_result"])),
            request["discovery_limits"]["result_bytes"],
        )
        self.assertEqual(len(jcs_bytes(execution.result)), limits["result_bytes"])
        return request, policy, provenance, corpus

    def test_all_cumulative_budgets_exact_simultaneously_and_each_exhausts_alone(self) -> None:
        request, policy, provenance, corpus = self._budget_fixture()
        dimensions = (
            ("route_limits", "policy_bytes"),
            ("route_limits", "provenance_bytes"),
            ("route_limits", "concepts"),
            ("route_limits", "clauses"),
            ("route_limits", "groups_per_clause"),
            ("route_limits", "alternatives_per_group"),
            ("route_limits", "total_alternatives"),
            ("route_limits", "normalized_alternative_bytes"),
            ("route_limits", "joint_routes"),
            ("route_limits", "matching_work"),
            ("route_limits", "evidence_entries"),
            ("route_limits", "witnesses"),
            ("route_limits", "collection_items"),
            ("route_limits", "parser_depth"),
            ("discovery_limits", "result_bytes"),
            ("route_limits", "result_bytes"),
        )
        for owner, key in dimensions:
            changed = deepcopy(request)
            self.assertGreater(changed[owner][key], 1, (owner, key))
            changed[owner][key] -= 1
            with self.subTest(owner=owner, key=key):
                _assert_kind(
                    self,
                    "resource_exhausted",
                    changed,
                    policy,
                    provenance,
                    corpus,
                )

        simultaneous = deepcopy(request)
        for owner, key in dimensions:
            simultaneous[owner][key] -= 1
        _assert_kind(
            self,
            "resource_exhausted",
            simultaneous,
            policy,
            provenance,
            corpus,
        )


class SemanticRouterLineageAndDiscoveryTests(unittest.TestCase):
    def test_every_nested_lineage_equality_and_complete_unchanged_result(self) -> None:
        request, policy, provenance = _fresh()
        corpus = _corpus()
        identity = _identity()
        derived = derived_discovery_request(request)
        unchanged = discover(corpus, derived, tool_identity=identity)
        execution = route(
            corpus, request, policy, provenance, tool_identity=identity
        )
        nested = execution.result["discovery_result"]
        self.assertEqual(jcs_bytes(nested), jcs_bytes(unchanged.result))
        self.assertEqual(
            nested["caller_request_digest"],
            discovery_digest("caller_request", derived),
        )
        self.assertEqual(
            nested["corpus_snapshot_digest"],
            execution.result["corpus_snapshot_digest"],
        )
        self.assertEqual(nested["tool_identity"], execution.result["tool_identity"])
        self.assertEqual(
            nested["effective_execution_digest"],
            execution.effective_execution[
                "nested_discovery_effective_execution_digest"
            ],
        )
        self.assertEqual(nested["algorithm"], unchanged.effective_execution["algorithm"])
        self.assertEqual(nested["effective_limits"], request["discovery_limits"])
        self.assertEqual(
            nested["result_digest"], discovery_digest("result", nested)
        )

        effective = execution.effective_execution
        for key, expected in {
            "caller_request_digest": object_digest("caller_request", request),
            "corpus_snapshot_digest": nested["corpus_snapshot_digest"],
            "routing_policy_digest": policy["routing_policy_digest"],
            "provenance_manifest_digest": provenance[
                "provenance_manifest_digest"
            ],
            "tool_identity": identity,
            "algorithm": ROUTE_ALGORITHM,
            "discovery_limits": request["discovery_limits"],
            "route_limits": request["route_limits"],
            "nested_discovery_effective_execution_digest": unchanged.effective_execution[
                "effective_execution_digest"
            ],
        }.items():
            self.assertEqual(effective[key], expected, key)
        self.assertEqual(
            effective["effective_execution_digest"],
            object_digest("effective_execution", effective),
        )
        for key in (
            "caller_request_digest",
            "corpus_snapshot_digest",
            "routing_policy_digest",
            "provenance_manifest_digest",
            "tool_identity",
            "algorithm",
            "effective_execution_digest",
        ):
            self.assertEqual(execution.result[key], effective[key], key)
        self.assertEqual(
            execution.result["result_digest"],
            object_digest("result", execution.result),
        )
        corpus_kinds = {item.ont_id: item.kind for item in corpus.documents}
        self.assertEqual(
            validate_bundle(
                request=request,
                policy=policy,
                provenance=provenance,
                effective_execution=effective,
                result=execution.result,
                discovery_effective_execution=unchanged.effective_execution,
                corpus_kinds=corpus_kinds,
            ),
            [],
        )

    def test_discovery_call_count_is_exactly_one_and_not_recursive(self) -> None:
        request, policy, provenance = _fresh()
        corpus = _corpus()
        identity = _identity()
        real_discover = router_module.discover
        real_evaluate = router_module.evaluate_policy
        calls = []
        evaluation_calls = 0
        active = 0
        maximum_active = 0

        def observed(*args, **kwargs):
            nonlocal active, maximum_active
            active += 1
            maximum_active = max(maximum_active, active)
            calls.append((args, kwargs))
            try:
                return real_discover(*args, **kwargs)
            finally:
                active -= 1

        def observed_evaluation(*args, **kwargs):
            nonlocal evaluation_calls
            evaluation_calls += 1
            return real_evaluate(*args, **kwargs)

        with (
            patch.object(router_module, "discover", side_effect=observed),
            patch.object(
                router_module, "evaluate_policy", side_effect=observed_evaluation
            ),
        ):
            execution = route(
                corpus, request, policy, provenance, tool_identity=identity
            )
        self.assertEqual(len(calls), 1)
        self.assertEqual(evaluation_calls, 1)
        self.assertEqual(maximum_active, 1)
        self.assertIs(calls[0][0][0], corpus)
        self.assertEqual(calls[0][0][1], derived_discovery_request(request))
        self.assertEqual(calls[0][1], {"tool_identity": identity})
        unchanged = real_discover(
            corpus, derived_discovery_request(request), tool_identity=identity
        )
        self.assertEqual(
            execution.result["discovery_result"], unchanged.result
        )

    def test_lexical_scores_and_top_candidate_never_select(self) -> None:
        request, policy, provenance = _fresh()
        request["query"] = "synthetic alpha"
        _sync(policy, provenance, request)
        decoy = _document(
            "synthetic.Decoy",
            labels=("synthetic alpha",),
            synonyms=("synthetic alpha",),
            description="synthetic alpha",
            examples=("synthetic alpha",),
        )
        result = _execute(request, policy, provenance, _corpus(decoy)).result
        candidates = result["discovery_result"]["candidates"]
        self.assertEqual(candidates[0]["ont_id"], "synthetic.Decoy")
        self.assertGreater(
            candidates[0]["score"],
            next(item["score"] for item in candidates if item["ont_id"] == "synthetic.Alpha"),
        )
        self.assertEqual(result["routing"]["state"], "single")
        self.assertEqual(
            result["routing"]["selected_ont_ids"], ["synthetic.Alpha"]
        )
        self.assertNotIn(
            "synthetic.Decoy", result["routing"]["supported_ont_ids"]
        )


class SemanticRouterErrorAndDeterminismTests(unittest.TestCase):
    def test_corpus_documents_snapshot_and_discovery_budgets_are_bound(self) -> None:
        request, policy, provenance = _fresh()
        base = _corpus()
        ghost = _document("synthetic.Ghost")
        forged = CapturedCorpus(base.snapshot_bytes, base.documents + (ghost,))
        _assert_kind(self, "invalid_ontology", request, policy, provenance, forged)
        changed = replace(base.documents[0], raw=b"x" * len(base.documents[0].raw))
        stale_digest = CapturedCorpus(base.snapshot_bytes, (changed, *base.documents[1:]))
        _assert_kind(self, "invalid_ontology", request, policy, provenance, stale_digest)
        for key, value in (("corpus_files", 1), ("corpus_bytes", 1), ("file_bytes", 1)):
            with self.subTest(key=key):
                limited = deepcopy(request); limited["discovery_limits"][key] = value
                _assert_kind(self, "resource_exhausted", limited, policy, provenance, base)
        limited = deepcopy(request)
        limited["route_limits"]["policy_bytes"] = len(jcs_bytes(policy)) - 1
        malformed = CapturedCorpus(b"{", ())
        _assert_kind(self, "resource_exhausted", limited, policy, provenance, malformed)
        structural = deepcopy(request); structural["route_limits"]["clauses"] = 1
        _assert_kind(self, "resource_exhausted", structural, policy, provenance, malformed)

    def test_real_unsupported_identity_and_schema_incompatibility_mappings(self) -> None:
        request, policy, provenance = _fresh()
        unsupported = deepcopy(request)
        unsupported["identity_selector"] = {"kind": "future_selector"}
        _assert_kind(self, "unsupported_identity", unsupported, policy, provenance, _corpus())
        identity = _identity(); identity["kind"] = "adopted_runtime"
        identity["digest"] = discovery_digest("tool_identity", identity)
        with self.assertRaises(RouteProtocolError) as caught:
            route(_corpus(), request, policy, provenance, tool_identity=identity)
        self.assertEqual(caught.exception.kind, "unsupported_identity")
        identity = _identity(); identity["python_version"] = "3.11.9"
        identity["digest"] = discovery_digest("tool_identity", identity)
        with self.assertRaises(RouteProtocolError) as caught:
            route(_corpus(), request, policy, provenance, tool_identity=identity)
        self.assertEqual(caught.exception.kind, "incompatible")
        with patch.object(router_module.unicodedata, "unidata_version", "14.0.0"):
            _assert_kind(self, "incompatible", request, policy, provenance, _corpus())
        with patch.object(router_module, "validate_invariants", side_effect=RouteProtocolError("incompatible")):
            _assert_kind(self, "incompatible", request, policy, provenance, _corpus())
        with patch.object(router_module, "validate_discovery_definition", side_effect=ProtocolError("schema incompatible")):
            _assert_kind(self, "incompatible", request, policy, provenance, _corpus())

    def test_safe_operational_errors_are_distinct_from_abstention_and_leak_nothing(self) -> None:
        request, policy, provenance = _fresh()
        request["query"] = "SECRET_QUERY synthetic alpha"
        policy["authority"]["path"] = "synthetic/SECRET_PATH.json"
        policy["authority"]["review_ref"] = "SECRET_POLICY_CONTENT"
        _sync(policy, provenance, request)
        secrets = (
            "SECRET_QUERY",
            "SECRET_PATH",
            "SECRET_POLICY_CONTENT",
            "SECRET_EXCEPTION",
            "SECRET_ENVIRONMENT",
        )
        with patch.dict(os.environ, {"SYNTHETIC_SECRET": "SECRET_ENVIRONMENT"}):
            for kind in (
                "invalid_request",
                "invalid_ontology",
                "resource_exhausted",
                "snapshot_changed",
                "unsupported_identity",
                "incompatible",
                "internal",
            ):
                with self.subTest(kind=kind), patch.object(
                    router_module,
                    "discover",
                    side_effect=DiscoveryError(kind, "SECRET_EXCEPTION"),
                ):
                    error = _assert_kind(
                        self, kind, request, policy, provenance, _corpus()
                    )
                    self.assertTrue(
                        all(secret not in str(error) for secret in secrets)
                    )

            with patch.object(
                router_module,
                "discover",
                side_effect=OSError("SECRET_EXCEPTION SECRET_PATH"),
            ):
                error = _assert_kind(
                    self, "internal", request, policy, provenance, _corpus()
                )
                self.assertTrue(all(secret not in str(error) for secret in secrets))

        invalid_policy = deepcopy(policy)
        invalid_policy["authority"]["path"] = "/SECRET_PATH/policy.json"
        invalid_policy["routing_policy_digest"] = object_digest(
            "routing_policy", invalid_policy
        )
        error = _assert_kind(
            self, "invalid_policy", request, invalid_policy, provenance, _corpus()
        )
        self.assertNotIn("SECRET_PATH", str(error))

    def test_malformed_corpus_is_an_operational_error_not_abstention(self) -> None:
        request, policy, provenance = _fresh()
        malformed = CapturedCorpus(b'{"SECRET_PATH":"SECRET_POLICY_CONTENT"}', ())
        error = _assert_kind(
            self, "invalid_ontology", request, policy, provenance, malformed
        )
        self.assertEqual(str(error), SAFE_ERROR_MESSAGES["invalid_ontology"])

    def test_repeat_canonical_bytes_are_exact_and_inputs_are_unchanged(self) -> None:
        request, policy, provenance = _fresh()
        corpus = _corpus()
        before = deepcopy((request, policy, provenance))
        outputs = []
        for environment in (
            {"LANG": "C", "ROCS_INDEX_CACHE": "1"},
            {"LANG": "synthetic_INVALID", "HOME": "/synthetic/elsewhere"},
        ):
            with patch.dict(os.environ, environment, clear=False):
                for _ in range(3):
                    execution = _execute(request, policy, provenance, corpus)
                    outputs.append(
                        (
                            jcs_bytes(execution.effective_execution),
                            execution.canonical_result_bytes,
                        )
                    )
        self.assertTrue(all(item == outputs[0] for item in outputs))
        self.assertEqual((request, policy, provenance), before)
        self.assertEqual(
            outputs[0][1],
            jcs_bytes(_execute(request, policy, provenance, corpus).result),
        )


if __name__ == "__main__":
    unittest.main()
