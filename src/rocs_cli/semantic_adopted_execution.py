"""Pure custody/execution projection checks for Decision 103 P1 S2.

The input is an inert synthetic projection: this module neither obtains authority nor
opens protected data, launches a process, signs, or mutates anything.
"""
from __future__ import annotations

from typing import Any, Mapping

from rocs_cli.semantic_adopted_protocol import jcs_bytes

ERROR_KINDS = (
    "projection_invalid",
    "principal_separation",
    "b0_coverage",
    "history_boundary",
    "reservation_process",
    "custody_order",
    "attempt_verdict_branch",
    "retry_rerun_forbidden",
    "closure_required",
)

_ROLES = (
    "semantic_owner", "policy_author", "development_author", "acceptance_author",
    "operational_author", "annotator", "annotator", "adjudicator", "custodian",
    "independent_reviewer", "evaluator_operator", "implementer",
)
_KEYS = frozenset({
    "principals", "b0_covered_principals", "b0_assessor_principal", "history",
    "reservation_count", "process_invocations", "attempt_state", "passes", "outcome",
    "timeline", "retry_count", "rerun_count", "closed",
})
_TIMELINE_KEYS = frozenset({"proof", "channel", "launch", "handoff", "receipt", "closure"})
# proof, channel, launch, handoff, receipt, process count, pass kinds, state, outcome
_BRANCHES = (
    ((False, False, False, False, False), 0, (), "not_started", "indeterminate"),
    ((True, False, False, False, False), 0, (), "not_started", "indeterminate"),
    ((True, True, True, False, False), 0, (), "not_started", "indeterminate"),
    ((True, True, True, False, False), 1, (), "interrupted", "indeterminate"),
    ((True, True, True, True, False), 1, (), "interrupted", "indeterminate"),
    ((True, True, True, True, True), 1, (), "interrupted", "indeterminate"),
    ((True, True, True, True, True), 1, ("primary",), "interrupted", "indeterminate"),
    ((True, True, True, True, True), 1, ("primary", "immediate_repeat"), "completed", "pass"),
)


def _integer(value: Any) -> bool:
    return type(value) is int


def _shape_valid(value: Any) -> bool:
    if type(value) is not dict or frozenset(value) != _KEYS:
        return False
    principals = value["principals"]
    history, timeline = value["history"], value["timeline"]
    if type(principals) is not list or any(
        type(item) is not dict or frozenset(item) != {"role", "principal_id"}
        or type(item["role"]) is not str or type(item["principal_id"]) is not str
        for item in principals
    ):
        return False
    if type(value["b0_covered_principals"]) is not list or any(
        type(item) is not str for item in value["b0_covered_principals"]
    ) or type(value["b0_assessor_principal"]) is not str:
        return False
    if type(history) is not dict or frozenset(history) != {"base", "activated", "terminal"} or any(
        not _integer(history[key]) for key in history
    ):
        return False
    if type(timeline) is not dict or frozenset(timeline) != _TIMELINE_KEYS or any(
        item is not None and not _integer(item) for item in timeline.values()
    ):
        return False
    if any(not _integer(value[key]) for key in (
        "reservation_count", "process_invocations", "retry_count", "rerun_count"
    )):
        return False
    return (
        type(value["attempt_state"]) is str and type(value["passes"]) is list
        and all(type(item) is str for item in value["passes"])
        and type(value["outcome"]) is str and type(value["closed"]) is bool
    )


def verify_execution_projection(projection: Mapping[str, Any]) -> tuple[str, ...]:
    """Return ordered, closed, non-sensitive error kinds for an inert projection."""
    if not _shape_valid(projection):
        return ("projection_invalid",)
    errors: list[str] = []
    principals = projection["principals"]
    principal_ids = [item["principal_id"] for item in principals]
    if (
        len(principals) != 12 or tuple(item["role"] for item in principals) != _ROLES
        or any(not item for item in principal_ids) or len(set(principal_ids)) != 12
    ):
        errors.append("principal_separation")
    covered = projection["b0_covered_principals"]
    assessor = projection["b0_assessor_principal"]
    if (
        len(covered) != 10 or len(set(covered)) != 10 or assessor in covered
        or assessor not in principal_ids or any(item not in principal_ids for item in covered)
    ):
        errors.append("b0_coverage")
    history = projection["history"]
    if not (
        12 <= history["base"] <= 254
        and history["activated"] == history["base"] + 1 <= 255
        and history["terminal"] == history["activated"] + 1 <= 256
    ):
        errors.append("history_boundary")
    if projection["reservation_count"] != 1 or projection["process_invocations"] not in (0, 1):
        errors.append("reservation_process")
    timeline = projection["timeline"]
    present = tuple(timeline[key] is not None for key in ("proof", "channel", "launch", "handoff", "receipt"))
    ordered = [timeline[key] for key in ("proof", "channel", "launch", "handoff", "receipt", "closure") if timeline[key] is not None]
    if any(item < 0 for item in ordered) or len(ordered) != len(set(ordered)) or ordered != sorted(ordered):
        errors.append("custody_order")
    actual = (
        present, projection["process_invocations"], tuple(projection["passes"]),
        projection["attempt_state"], projection["outcome"],
    )
    if actual not in _BRANCHES:
        errors.append("attempt_verdict_branch")
    if projection["retry_count"] != 0 or projection["rerun_count"] != 0:
        errors.append("retry_rerun_forbidden")
    if not projection["closed"] or timeline["closure"] is None:
        errors.append("closure_required")
    return tuple(errors)


def execution_verification_result(projection: Mapping[str, Any]) -> dict[str, Any]:
    """Produce the language-neutral result envelope used by differential tests."""
    errors = verify_execution_projection(projection)
    return {"ok": not errors, "error_kinds": list(errors)}


def execution_verification_bytes(projection: Mapping[str, Any]) -> bytes:
    """Return canonical bytes, without a terminal newline."""
    return jcs_bytes(execution_verification_result(projection))
