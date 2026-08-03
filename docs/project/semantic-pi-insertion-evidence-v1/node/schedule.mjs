/** Closed event grammar and deterministic schedule consumption. */

import {
  DECIMAL_RE,
  DIGEST_RE,
  HOOKS,
  MAX_INT,
  SPAN_RE,
  canonicalBase64,
  requireCondition,
  same,
} from "./common.mjs";

const COMMON_COMPAT = {
  reserve: ["after_reservation"], prepare_return_base64: ["during_prepare"], apply_span: ["after_apply"],
  assign_base64: ["after_assignment"], readback_base64: ["after_readback"], issue_witness: ["after_witness"],
  applied_return_digest: ["after_applied"], commit_record: ["after_record_commit"],
  abort_signal: HOOKS.filter((hook) => hook.startsWith("before_") || hook.startsWith("during_")),
  replace_ack_issuer: ["after_applied"], inject_ack_bytes_base64: ["after_applied"],
  invoke_nested_prompt: ["during_applied"], reserve_attempt_override: ["before_reservation"],
  replace_registration_component_id: ["before_reservation"], advance_monotonic_ns: HOOKS,
  reload_generation: HOOKS, clone_witness_json: ["before_witness", "after_witness"], consume_witness_twice: ["during_applied"],
};
const FIXTURE_COMPAT = {
  prompt_attempt: ["during_applied", "before_record_commit"], continuation_attempt: ["during_applied", "before_record_commit"],
  completion_attempt: ["during_applied", "before_record_commit"], provider_dispatch_attempt: ["during_applied", "before_record_commit"],
  model_invocation_attempt: ["during_applied", "before_record_commit"], contributor_callback_attempt: ["during_applied", "before_record_commit"],
  stale_api_call: ["after_failure"], detached_callback_call: ["during_applied"], provider_dispatch_eligibility: ["after_guard_release"],
  applied_throw: ["during_applied"], record_commit: ["after_record_commit", "after_failure"], create_registration_b: ["before_reservation"],
  consume_from_registration_b: ["during_applied"], consume_stale_witness: ["after_failure"], defer_applied: ["during_applied"],
  settle_applied: ["after_failure"], start_next_attempt: ["after_failure"], assign: ["after_assignment"], readback: ["after_readback"], witness_issued: ["after_witness"],
};
const EXACT_VALUES = {
  abort_signal: ["set"], replace_ack_issuer: ["other-component"], replace_registration_component_id: ["pi-adapter"],
  invoke_nested_prompt: ["attempt"], clone_witness_json: ["true"], consume_witness_twice: ["true"],
  stale_api_call: ["rejected"], detached_callback_call: ["rejected"], provider_dispatch_eligibility: ["released"], applied_throw: ["error"],
  create_registration_b: ["other-component"], consume_from_registration_b: ["rejected"], consume_stale_witness: ["rejected"],
  defer_applied: ["pending"], settle_applied: ["late"], start_next_attempt: ["allowed"], assign: ["done"], readback: ["verified"],
  witness_issued: ["after_assign", "after_readback", "generation0"],
};
class Schedule {
  constructor(events, fixture) {
    requireCondition(Array.isArray(events) && events.length >= 1 && events.length <= 64, "events must contain 1..64 rows");
    const compatibility = { ...COMMON_COMPAT, ...(fixture ? FIXTURE_COMPAT : {}) };
    this.events = events; this.used = new Set();
    const seen = new Set(); const positions = [];
    events.forEach((event) => {
      requireCondition(event !== null && typeof event === "object" && same(Object.keys(event).sort(), ["at_hook", "kind", "value"]), "invalid event row");
      const { at_hook: hook, kind, value } = event;
      requireCondition(typeof hook === "string" && typeof kind === "string" && typeof value === "string", "event fields must be strings");
      requireCondition(Object.hasOwn(compatibility, kind) && compatibility[kind].includes(hook), `hook-incompatible or unknown event: ${hook}/${kind}`);
      requireCondition(!seen.has(`${hook}\0${kind}`), `duplicate event pair: ${hook}/${kind}`);
      seen.add(`${hook}\0${kind}`); positions.push(HOOKS.indexOf(hook)); Schedule.validateValue(kind, value);
      if (fixture) Schedule.validateFixtureCombination(hook, kind, value);
    });
    requireCondition(positions.every((value, index) => index === 0 || positions[index - 1] <= value), "events are not in hook order");
  }
  static validateValue(kind, value) {
    if (["reserve", "reserve_attempt_override", "advance_monotonic_ns", "reload_generation"].includes(kind)) {
      requireCondition(DECIMAL_RE.test(value) && BigInt(value) <= BigInt(MAX_INT), `invalid decimal event value: ${kind}`);
    } else if (["prepare_return_base64", "assign_base64", "readback_base64", "inject_ack_bytes_base64"].includes(kind)) canonicalBase64(value, kind);
    else if (kind === "apply_span") {
      const match = SPAN_RE.exec(value); requireCondition(match !== null && match.slice(1).every((part) => BigInt(part) <= BigInt(MAX_INT)), "invalid apply span");
    } else if (["issue_witness", "applied_return_digest", "commit_record"].includes(kind)) requireCondition(DIGEST_RE.test(value), `invalid digest assertion: ${kind}`);
    else if (Object.hasOwn(EXACT_VALUES, kind)) requireCondition(EXACT_VALUES[kind].includes(value), `invalid event value: ${kind}=${value}`);
    else if (kind === "record_commit") requireCondition(["done", "forbidden"].includes(value), "invalid record_commit value");
    else if (kind.endsWith("_attempt")) {
      const allowed = kind === "contributor_callback_attempt" ? ["blocked", "reentry", "stale"] : ["blocked", "reentry"];
      requireCondition(allowed.includes(value), `invalid entrypoint event value: ${kind}=${value}`);
    } else requireCondition(value.length > 0, `empty event value: ${kind}`);
  }
  static validateFixtureCombination(hook, kind, value) {
    const entrypoints = ["prompt_attempt", "continuation_attempt", "completion_attempt", "provider_dispatch_attempt", "model_invocation_attempt", "contributor_callback_attempt"];
    if (entrypoints.includes(kind)) {
      const expectedHook = value === "blocked" ? "before_record_commit" : "during_applied";
      requireCondition(hook === expectedHook, `hook-incompatible fixture event: ${hook}/${kind}=${value}`);
    } else if (kind === "record_commit") {
      const expectedHook = value === "done" ? "after_record_commit" : "after_failure";
      requireCondition(hook === expectedHook, `hook-incompatible fixture event: ${hook}/${kind}=${value}`);
    }
  }
  take(hook) {
    const rows = [];
    this.events.forEach((event, index) => {
      if (event.at_hook === hook) { requireCondition(!this.used.has(index), `event consumed twice at ${hook}`); this.used.add(index); rows.push(event); }
    });
    return rows;
  }
  finish() { requireCondition(this.used.size === this.events.length, "unreachable or unused event"); }
}

export { Schedule };
