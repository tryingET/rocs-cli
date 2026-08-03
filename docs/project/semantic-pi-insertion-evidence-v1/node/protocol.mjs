/** Independent insertion-attempt state machine. */

import {
  ConformanceError,
  DIGEST_RE,
  DOMAINS,
  MAX_INT,
  ProtocolFailure,
  REVISION,
  SCHEMA_NAMES,
  SPAN_RE,
  StrictJSONError,
  canonicalBase64,
  objectDigest,
  rawDigest,
  requireCondition,
  same,
  snapshotText,
  strictJSONLoads,
} from "./common.mjs";
import { Schedule } from "./schedule.mjs";

function makeRequest(generation, attempt, index, inputRaw, contribution) {
  const value = { schema: SCHEMA_NAMES[0], protocol_revision: REVISION, repository_id: "pi-extensions", component_id: "pi-ontology-workflows", package_name: "@tryinget/pi-ontology-workflows", execution_generation: generation, attempt_id: attempt, handler_registration_index: index, input_prompt_byte_length: inputRaw.length, input_prompt_digest: rawDigest(DOMAINS[5], inputRaw), contribution_byte_length: contribution.length, contribution_digest: rawDigest(DOMAINS[6], contribution) };
  value.request_digest = objectDigest(DOMAINS[0], value, "request_digest"); return value;
}
function makeWitness(request, assigned, readback, start, end) {
  const value = { schema: SCHEMA_NAMES[1], host_package: "@earendil-works/pi-coding-agent", protocol_revision: REVISION, request_digest: request.request_digest, execution_generation: request.execution_generation, attempt_id: request.attempt_id, handler_registration_index: request.handler_registration_index, assigned_prompt_chain_byte_length: assigned.length, assigned_prompt_chain_digest: rawDigest(DOMAINS[7], assigned), readback_prompt_chain_byte_length: readback.length, readback_prompt_chain_digest: rawDigest(DOMAINS[7], readback), contribution_start_byte_offset: start, contribution_end_byte_offset: end, observation_phase: "post_assignment_readback_pre_dispatch", provider_request_dispatched_at_observation: false, model_invocation_started_at_observation: false };
  value.witness_digest = objectDigest(DOMAINS[1], value, "witness_digest"); return value;
}
function makeAcknowledgement(request, witness) {
  const value = { schema: SCHEMA_NAMES[2], issuer: { kind: "pi_extension_component", id: "pi-ontology-workflows" }, request_digest: request.request_digest, witness_digest: witness.witness_digest, execution_generation: request.execution_generation, attempt_id: request.attempt_id, handler_registration_index: request.handler_registration_index, acknowledgement_outcome: "observed_inserted", claim_scope: "prompt_chain_insertion_only" };
  value.acknowledgement_digest = objectDigest(DOMAINS[2], value, "acknowledgement_digest"); return value;
}
function makeRecord(request, witness, acknowledgement) {
  const value = { schema: SCHEMA_NAMES[3], host_package: "@earendil-works/pi-coding-agent", protocol_revision: REVISION, request_digest: request.request_digest, witness_digest: witness.witness_digest, acknowledgement_digest: acknowledgement.acknowledgement_digest, execution_generation: request.execution_generation, attempt_id: request.attempt_id, handler_registration_index: request.handler_registration_index, insertion_outcome: "observed_inserted", claim_scope: "prompt_chain_insertion_only", provider_request_dispatched_at_record: false, model_invocation_started_at_record: false, record_phase: "acknowledged_pre_dispatch" };
  value.insertion_record_digest = objectDigest(DOMAINS[3], value, "insertion_record_digest"); return value;
}
function makeError(generation, attempt, stage, code) {
  const value = { schema: SCHEMA_NAMES[4], protocol_revision: REVISION, execution_generation: generation, attempt_id_or_null: attempt, stage, error_code: code, details: [] };
  value.error_digest = objectDigest(DOMAINS[4], value, "error_digest"); return value;
}

function runAttempt(spec, fixture) {
  const schedule = new Schedule(spec.events, fixture);
  const generation = spec.initial_generation; let nextAttempt = spec.initial_next_attempt_id;
  const index = spec.handler_registration_index; const deadline = spec.deadline_monotonic_ns;
  requireCondition([generation, nextAttempt, index, deadline].every((value) => Number.isSafeInteger(value) && value >= 0), "invalid attempt integer");
  const inputRaw = canonicalBase64(spec.input_bytes_base64, "input_bytes_base64");
  const defaultContribution = canonicalBase64(spec.contribution_bytes_base64, "contribution_bytes_base64");
  let currentGeneration = generation; let now = 0; let aborted = false;
  let registrationComponent = "pi-ontology-workflows"; let reservationOverride = null; let attempt = null;
  let request = null; let witness = null; let acknowledgement = null; let record = null;
  let state = "reserved"; let guardActive = false; let frameActive = false;
  const providerBeforeRecord = 0; const modelBeforeRecord = 0; const controls = [];
  let cloned = false; let reused = false; let poisoned = false; let deferred = false; let threw = false; let registrationB = false;
  let assignedDone = false; let readbackDone = false; let witnessDone = false;

  function generic(event) {
    if (event.kind === "advance_monotonic_ns") now = Number(event.value);
    else if (event.kind === "reload_generation") { requireCondition(Number(event.value) > currentGeneration, "reload_generation must advance generation"); currentGeneration = Number(event.value); }
    else if (event.kind === "abort_signal") aborted = true;
    else return false;
    return true;
  }
  function predicate(stage, before = []) {
    if (currentGeneration !== generation) throw new ProtocolFailure(stage, "stale_generation");
    for (const [established, code] of before) if (established) throw new ProtocolFailure(code === "reentry_attempt" ? "dispatch_guard" : "witness", code);
    if (aborted) throw new ProtocolFailure(stage, "aborted");
    if (now >= deadline) throw new ProtocolFailure(stage, "deadline_exceeded");
  }
  function addControl(kind, entrypointName) {
    requireCondition(attempt !== null, "control result before reservation");
    controls.push({ kind, entrypoint: entrypointName, execution_generation: generation, attempt_id: attempt });
  }
  function entrypoint(event) {
    const mapping = { prompt_attempt: "prompt", continuation_attempt: "continuation", completion_attempt: "completion", provider_dispatch_attempt: "provider_dispatch", model_invocation_attempt: "model_invocation", contributor_callback_attempt: "contributor_callback" };
    if (!Object.hasOwn(mapping, event.kind)) return false;
    if (event.value === "blocked") { requireCondition(guardActive, "blocked classification without guard"); addControl("dispatch_blocked", mapping[event.kind]); }
    else if (event.value === "reentry") { requireCondition(guardActive && frameActive, "reentry classification without matching frame"); poisoned = true; }
    else { addControl("stale_invocation", mapping[event.kind]); poisoned = guardActive; }
    return true;
  }

  let failure = null;
  try {
    for (const event of schedule.take("before_reservation")) {
      if (generic(event)) continue;
      if (event.kind === "reserve_attempt_override") reservationOverride = Number(event.value);
      else if (event.kind === "replace_registration_component_id") registrationComponent = event.value;
      else if (event.kind === "create_registration_b") registrationB = true;
    }
    if (registrationComponent !== "pi-ontology-workflows") throw new ProtocolFailure("registration", "identity_mismatch");
    if (currentGeneration !== generation) throw new ProtocolFailure("registration", "stale_generation");
    if (aborted) throw new ProtocolFailure("registration", "aborted");
    if (now >= deadline) throw new ProtocolFailure("registration", "deadline_exceeded");
    const candidate = reservationOverride === null ? nextAttempt : reservationOverride;
    if (nextAttempt === MAX_INT || candidate !== nextAttempt) throw new ProtocolFailure("registration", "attempt_reuse");
    attempt = candidate; nextAttempt += 1; guardActive = true; state = "reserved";
    for (const event of schedule.take("after_reservation")) { if (generic(event)) continue; requireCondition(event.kind === "reserve" && event.value === String(attempt), "reservation assertion failed"); }

    predicate("prepare"); state = "preparing"; frameActive = true; let contribution = defaultContribution;
    for (const event of schedule.take("during_prepare")) { if (generic(event)) continue; if (event.kind === "prepare_return_base64") contribution = canonicalBase64(event.value, "prepare_return_base64"); }
    predicate("prepare");
    if (!snapshotText(inputRaw, 0, 16_777_216) || !snapshotText(contribution, 1, 16_777_216)) throw new ProtocolFailure("prepare", "malformed_input");
    frameActive = false; state = "prepared"; request = makeRequest(generation, attempt, index, inputRaw, contribution);
    for (const event of schedule.take("after_prepare")) requireCondition(generic(event), "unsupported after_prepare event");
    for (const event of schedule.take("before_apply")) requireCondition(generic(event), "unsupported before_apply event");
    predicate("apply"); state = "applying"; let start = inputRaw.length; let end = inputRaw.length + contribution.length;
    for (const event of schedule.take("after_apply")) {
      if (generic(event)) continue;
      const match = SPAN_RE.exec(event.value); requireCondition(event.kind === "apply_span" && match !== null, "invalid apply event");
      start = Number(match[1]); end = Number(match[2]);
    }
    const assigned = start <= inputRaw.length ? Buffer.concat([inputRaw.subarray(0, start), contribution, inputRaw.subarray(start)]) : Buffer.concat([inputRaw, contribution]);
    if (!snapshotText(assigned, 1, 33_554_432)) throw new ProtocolFailure("apply", "malformed_input");
    const inserted = start < end && end <= assigned.length && end - start === contribution.length && assigned.subarray(start, end).equals(contribution);
    if (!inserted) throw new ProtocolFailure("apply", "contribution_not_inserted");
    predicate("assignment"); assignedDone = true; state = "assigned";
    for (const event of schedule.take("after_assignment")) {
      if (generic(event)) continue;
      if (event.kind === "assign_base64") requireCondition(canonicalBase64(event.value, "assign_base64").equals(assigned), "assignment assertion failed");
      else if (event.kind === "assign") requireCondition(event.value === "done" && assignedDone, "assignment order assertion failed");
    }
    let readback = assigned;
    for (const event of schedule.take("after_readback")) {
      if (generic(event)) continue;
      if (event.kind === "readback_base64") readback = canonicalBase64(event.value, "readback_base64");
      else if (event.kind === "readback") requireCondition(event.value === "verified" && assignedDone, "readback order assertion failed");
    }
    if (!snapshotText(readback, 1, 33_554_432)) throw new ProtocolFailure("readback", "malformed_input");
    predicate("readback"); if (!readback.equals(assigned)) throw new ProtocolFailure("readback", "readback_mismatch");
    readbackDone = true; state = "readback_verified";
    for (const event of schedule.take("before_witness")) { if (generic(event)) continue; if (event.kind === "clone_witness_json") cloned = true; }
    predicate("witness"); witness = makeWitness(request, assigned, readback, start, end); witnessDone = true; state = "witnessed";
    for (const event of schedule.take("after_witness")) {
      if (generic(event)) continue;
      if (event.kind === "issue_witness") requireCondition(event.value === witness.witness_digest, "witness digest assertion failed");
      else if (event.kind === "clone_witness_json") cloned = true;
      else if (event.kind === "witness_issued") {
        const facts = { after_assign: assignedDone, after_readback: readbackDone, generation0: generation === 0 };
        requireCondition(facts[event.value] && witnessDone, "witness order assertion failed");
      }
    }
    predicate("acknowledgement");
    if (cloned) throw new ProtocolFailure("witness", "witness_forged");

    state = "acknowledging"; frameActive = true;
    for (const event of schedule.take("during_applied")) {
      if (generic(event) || entrypoint(event)) continue;
      if (event.kind === "consume_witness_twice") reused = true;
      else if (event.kind === "invoke_nested_prompt") poisoned = true;
      else if (event.kind === "detached_callback_call") addControl("dispatch_blocked", "contributor_callback");
      else if (event.kind === "consume_from_registration_b") { requireCondition(registrationB, "registration B was not created"); addControl("stale_invocation", "contributor_callback"); poisoned = true; }
      else if (event.kind === "defer_applied") deferred = true;
      else if (event.kind === "applied_throw") threw = true;
    }
    predicate("acknowledgement", [[reused, "witness_reused"], [poisoned, "reentry_attempt"]]);
    if (threw) throw new ProtocolFailure("acknowledgement", "internal_failure");
    if (deferred) throw new ConformanceError("deferred callback remained pending without terminal observer");
    acknowledgement = makeAcknowledgement(request, witness); let malformedAck = false;
    for (const event of schedule.take("after_applied")) {
      if (generic(event)) continue;
      if (event.kind === "replace_ack_issuer") acknowledgement.issuer = { kind: "pi_extension_component", id: event.value };
      else if (event.kind === "inject_ack_bytes_base64") {
        try {
          const candidateAck = strictJSONLoads(canonicalBase64(event.value, event.kind), event.kind);
          if (candidateAck === null || typeof candidateAck !== "object" || Array.isArray(candidateAck)) throw new StrictJSONError("acknowledgement is not an object");
          acknowledgement = candidateAck;
        } catch (error) { if (!(error instanceof ConformanceError)) throw error; malformedAck = true; }
      } else if (event.kind === "applied_return_digest") requireCondition(acknowledgement.acknowledgement_digest === event.value, "acknowledgement digest assertion failed");
    }
    if (malformedAck) throw new ProtocolFailure("acknowledgement", "malformed_input");
    predicate("acknowledgement");
    const ackKeys = ["schema", "issuer", "request_digest", "witness_digest", "execution_generation", "attempt_id", "handler_registration_index", "acknowledgement_outcome", "claim_scope", "acknowledgement_digest"];
    const issuer = acknowledgement.issuer;
    const shapeOK = same(Object.keys(acknowledgement).sort(), [...ackKeys].sort())
      && issuer !== null && typeof issuer === "object" && !Array.isArray(issuer) && same(Object.keys(issuer).sort(), ["id", "kind"])
      && ["schema", "request_digest", "witness_digest", "acknowledgement_outcome", "claim_scope", "acknowledgement_digest"].every((key) => typeof acknowledgement[key] === "string")
      && ["execution_generation", "attempt_id", "handler_registration_index"].every((key) => Number.isSafeInteger(acknowledgement[key]))
      && Object.values(issuer).every((value) => typeof value === "string") && DIGEST_RE.test(acknowledgement.acknowledgement_digest);
    if (!shapeOK) throw new ProtocolFailure("acknowledgement", "malformed_input");
    if (!same(acknowledgement, makeAcknowledgement(request, witness))) throw new ProtocolFailure("acknowledgement", "acknowledgement_mismatch");
    frameActive = false;

    for (const event of schedule.take("before_record_commit")) { if (generic(event) || entrypoint(event)) continue; }
    predicate("record", [[false, "witness_reused"], [poisoned, "reentry_attempt"]]);
    record = makeRecord(request, witness, acknowledgement); state = "record_committed";
    for (const event of schedule.take("after_record_commit")) {
      if (generic(event)) continue;
      if (event.kind === "commit_record") requireCondition(event.value === record.insertion_record_digest, "record digest assertion failed");
      else if (event.kind === "record_commit") requireCondition(event.value === "done" && record !== null, "record commit assertion failed");
    }
    guardActive = false; state = "dispatch_eligible";
    for (const event of schedule.take("after_guard_release")) {
      if (generic(event)) continue;
      requireCondition(event.kind === "provider_dispatch_eligibility" && event.value === "released", "guard release assertion failed");
    }
    schedule.finish();
  } catch (error) {
    if (!(error instanceof ProtocolFailure)) throw error;
    failure = error; frameActive = false; guardActive = false; state = "failed";
    for (const event of schedule.take("after_failure")) {
      if (generic(event)) continue;
      if (event.kind === "settle_applied") requireCondition(event.value === "late" && deferred, "late settlement assertion failed");
      else if (event.kind === "start_next_attempt") requireCondition(event.value === "allowed" && attempt !== null && nextAttempt < MAX_INT, "next attempt was not released");
      else if (event.kind === "record_commit") requireCondition(event.value === "forbidden" && record === null, "record committed after failure");
      else if (["consume_stale_witness", "stale_api_call"].includes(event.kind)) { requireCondition(witnessDone && event.value === "rejected", "stale witness/API assertion failed"); addControl("stale_invocation", "contributor_callback"); }
    }
    schedule.finish();
  }
  const metadata = { terminal_state: state, provider_operations_before_record: providerBeforeRecord, model_operations_before_record: modelBeforeRecord, control_results: controls };
  const actual = failure === null
    ? { accepted: true, error_or_null: null, request_or_null: request, witness_or_null: witness, acknowledgement_or_null: acknowledgement, record_or_null: record }
    : { accepted: false, error_or_null: makeError(generation, attempt, failure.stage, failure.code), request_or_null: null, witness_or_null: null, acknowledgement_or_null: null, record_or_null: null };
  if (failure === null) requireCondition([request, witness, acknowledgement, record].every((value) => value !== null), "incomplete accepted execution");
  return [actual, metadata];
}

export { runAttempt };
