"""Closed event grammar and deterministic schedule consumption."""

from __future__ import annotations

from typing import Any

from python.common import (
    DECIMAL_RE,
    DIGEST_RE,
    HOOKS,
    MAX_INT,
    SPAN_RE,
    canonical_base64,
    require,
)

COMMON_COMPAT: dict[str, set[str]] = {
    "reserve": {"after_reservation"},
    "prepare_return_base64": {"during_prepare"},
    "apply_span": {"after_apply"},
    "assign_base64": {"after_assignment"},
    "readback_base64": {"after_readback"},
    "issue_witness": {"after_witness"},
    "applied_return_digest": {"after_applied"},
    "commit_record": {"after_record_commit"},
    "abort_signal": {hook for hook in HOOKS if hook.startswith(("before_", "during_"))},
    "replace_ack_issuer": {"after_applied"},
    "inject_ack_bytes_base64": {"after_applied"},
    "invoke_nested_prompt": {"during_applied"},
    "reserve_attempt_override": {"before_reservation"},
    "replace_registration_component_id": {"before_reservation"},
    "advance_monotonic_ns": set(HOOKS),
    "reload_generation": set(HOOKS),
    "clone_witness_json": {"before_witness", "after_witness"},
    "consume_witness_twice": {"during_applied"},
}
FIXTURE_COMPAT: dict[str, set[str]] = {
    "prompt_attempt": {"during_applied", "before_record_commit"},
    "continuation_attempt": {"during_applied", "before_record_commit"},
    "completion_attempt": {"during_applied", "before_record_commit"},
    "provider_dispatch_attempt": {"during_applied", "before_record_commit"},
    "model_invocation_attempt": {"during_applied", "before_record_commit"},
    "contributor_callback_attempt": {"during_applied", "before_record_commit"},
    "stale_api_call": {"after_failure"},
    "detached_callback_call": {"during_applied"},
    "provider_dispatch_eligibility": {"after_guard_release"},
    "applied_throw": {"during_applied"},
    "record_commit": {"after_record_commit", "after_failure"},
    "create_registration_b": {"before_reservation"},
    "consume_from_registration_b": {"during_applied"},
    "consume_stale_witness": {"after_failure"},
    "defer_applied": {"during_applied"},
    "settle_applied": {"after_failure"},
    "start_next_attempt": {"after_failure"},
    "assign": {"after_assignment"},
    "readback": {"after_readback"},
    "witness_issued": {"after_witness"},
}
EXACT_VALUES = {
    "abort_signal": {"set"},
    "replace_ack_issuer": {"other-component"},
    "replace_registration_component_id": {"pi-adapter"},
    "invoke_nested_prompt": {"attempt"},
    "clone_witness_json": {"true"},
    "consume_witness_twice": {"true"},
    "stale_api_call": {"rejected"},
    "detached_callback_call": {"rejected"},
    "provider_dispatch_eligibility": {"released"},
    "applied_throw": {"error"},
    "create_registration_b": {"other-component"},
    "consume_from_registration_b": {"rejected"},
    "consume_stale_witness": {"rejected"},
    "defer_applied": {"pending"},
    "settle_applied": {"late"},
    "start_next_attempt": {"allowed"},
    "assign": {"done"},
    "readback": {"verified"},
    "witness_issued": {"after_assign", "after_readback", "generation0"},
}


class Schedule:
    def __init__(self, events: Any, fixture: bool) -> None:
        require(isinstance(events, list) and 1 <= len(events) <= 64, "events must contain 1..64 rows")
        compat = dict(COMMON_COMPAT)
        if fixture:
            compat.update(FIXTURE_COMPAT)
        self.events = events
        self.used: set[int] = set()
        seen: set[tuple[str, str]] = set()
        positions: list[int] = []
        for event in events:
            require(isinstance(event, dict) and set(event) == {"at_hook", "kind", "value"}, "invalid event row")
            hook, kind, value = event["at_hook"], event["kind"], event["value"]
            require(isinstance(hook, str) and isinstance(kind, str) and isinstance(value, str), "event fields must be strings")
            require(kind in compat and hook in compat[kind], f"hook-incompatible or unknown event: {hook}/{kind}")
            require((hook, kind) not in seen, f"duplicate event pair: {hook}/{kind}")
            seen.add((hook, kind))
            positions.append(HOOKS.index(hook))
            self._validate_value(kind, value)
            if fixture:
                self._validate_fixture_combination(hook, kind, value)
        require(positions == sorted(positions), "events are not in hook order")

    @staticmethod
    def _validate_value(kind: str, value: str) -> None:
        if kind in {"reserve", "reserve_attempt_override", "advance_monotonic_ns", "reload_generation"}:
            require(DECIMAL_RE.fullmatch(value) is not None and int(value) <= MAX_INT, f"invalid decimal event value: {kind}")
        elif kind in {"prepare_return_base64", "assign_base64", "readback_base64", "inject_ack_bytes_base64"}:
            canonical_base64(value, kind)
        elif kind == "apply_span":
            match = SPAN_RE.fullmatch(value)
            require(match is not None and all(int(part) <= MAX_INT for part in match.groups()), "invalid apply span")
        elif kind in {"issue_witness", "applied_return_digest", "commit_record"}:
            require(DIGEST_RE.fullmatch(value) is not None, f"invalid digest assertion: {kind}")
        elif kind in EXACT_VALUES:
            require(value in EXACT_VALUES[kind], f"invalid event value: {kind}={value}")
        elif kind == "record_commit":
            require(value in {"done", "forbidden"}, "invalid record_commit value")
        elif kind.endswith("_attempt"):
            allowed = {"blocked", "reentry", "stale"} if kind == "contributor_callback_attempt" else {"blocked", "reentry"}
            require(value in allowed, f"invalid entrypoint event value: {kind}={value}")
        else:
            require(bool(value), f"empty event value: {kind}")

    @staticmethod
    def _validate_fixture_combination(hook: str, kind: str, value: str) -> None:
        entrypoints = {
            "prompt_attempt", "continuation_attempt", "completion_attempt",
            "provider_dispatch_attempt", "model_invocation_attempt", "contributor_callback_attempt",
        }
        if kind in entrypoints:
            expected_hook = "before_record_commit" if value == "blocked" else "during_applied"
            require(hook == expected_hook, f"hook-incompatible fixture event: {hook}/{kind}={value}")
        elif kind == "record_commit":
            expected_hook = "after_record_commit" if value == "done" else "after_failure"
            require(hook == expected_hook, f"hook-incompatible fixture event: {hook}/{kind}={value}")

    def take(self, hook: str) -> list[dict[str, str]]:
        rows = []
        for index, event in enumerate(self.events):
            if event["at_hook"] == hook:
                require(index not in self.used, f"event consumed twice at {hook}")
                self.used.add(index)
                rows.append(event)
        return rows

    def finish(self) -> None:
        require(len(self.used) == len(self.events), "unreachable or unused event")
