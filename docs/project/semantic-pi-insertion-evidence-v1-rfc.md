---
summary: "Decision 85 compact protocol for host-observed semantic prompt-chain insertion evidence."
read_when:
  - "Reviewing or implementing semantic Pi insertion evidence v1."
type: "rfc"
status: "in_review"
rfc_revision: "semantic-pi-insertion-evidence-v1-r1"
---
# RFC — Semantic Pi insertion evidence v1

## Decision requested

Accept a compact successor direction that replaces the unimplementable semantic Pi delivery super-protocol with default-off, same-process evidence that the Pi host inserted and read back one exact `pi-ontology-workflows` contribution.

Decision 85 is prospective only. Before an accepted ADR, this RFC grants no packet, implementation, installation, reload, dogfood, provider/model, publication, activation, live-acquisition, or production authority.

## Fixed identity

```json
{"repository_id":"pi-extensions","component_id":"pi-ontology-workflows","package_name":"@tryinget/pi-ontology-workflows","protocol_issuer":{"kind":"pi_extension_component","id":"pi-ontology-workflows"},"host_package":"@earendil-works/pi-coding-agent"}
```

No `pi-adapter` owner, repository, package, component, issuer, alias, fallback, or edge exists.

The accepted identity commit `63d1e9f5c271007b48c45818d1f419a228de1561` is governance provenance only. It is not a runtime source-commit pin or a substitute for a future component release artifact.

## Claim boundary

An accepted insertion record proves only:

1. the named component returned exact contribution bytes for one host attempt;
2. the host assigned a prompt chain with that contribution at the recorded handler index;
3. the host read back byte-identical prompt-chain bytes;
4. the host issued one private witness after readback;
5. the same registered contributor acknowledged that witness once;
6. the host finalized the record before provider/model dispatch became eligible.

It does **not** prove provider transmission, model invocation, model input, influence, correctness, meaning, semantic release, publication, adoption, activation, consumer consent, production delivery, or later use.

## JSON and digest profile

Every persisted object is strict UTF-8 JSON with no BOM, duplicate keys, trailing bytes, floats, exponents, unsafe integers, lone surrogates, noncharacters, or non-NFC strings. Objects have exactly their listed keys and `additionalProperties=false`. Integers are `0..9007199254740991`. Digests are lowercase `sha256:` plus 64 hexadecimal characters.

JCS means RFC 8785 over this restricted profile. For domain `D`, digest is:

```text
sha256(UTF8(D) || 0x00 || JCS(object with only its named self-digest field omitted))
```

Raw prompt/contribution bytes use:

```text
sha256(UTF8(domain) || 0x00 || uint64_be(byte_length) || bytes)
```

Input, contribution, assigned-chain, and readback values are immutable snapshots of UTF-8 NFC string bytes. The host encodes a JavaScript string with fatal UTF-8 after rejecting lone surrogates/noncharacters; offsets and lengths count bytes, not code points or UTF-16 units. Input may be empty. Contribution is 1..16,777,216 bytes and assigned chain is at most 33,554,432 bytes. The apply operation produces exactly the input bytes with the contribution inserted once and adds, removes, or rewrites no other byte, so valid input/contribution bounds close the combined size. After insertion and before assignment, the complete assigned bytes must decode to one NFC string under the same profile; otherwise stage `apply` returns `malformed_input`. The host copies contribution bytes synchronously when `prepare` settles, before any subsequent callback or await, and lengths in every object equal the retained byte arrays.

Domains are closed:

| Object/value | Domain | Self field |
|---|---|---|
| request | `semantic-pi-insertion.request.v1` | `request_digest` |
| host application witness | `pi.prompt-chain-application-witness.v1` | `witness_digest` |
| component acknowledgement | `semantic-pi-insertion.acknowledgement.v1` | `acknowledgement_digest` |
| host insertion record | `pi.prompt-chain-insertion-record.v1` | `insertion_record_digest` |
| error | `semantic-pi-insertion.error.v1` | `error_digest` |
| input prompt bytes | `semantic-pi-insertion.input-prompt-bytes.v1` | exact bytes |
| contribution bytes | `semantic-pi-insertion.contribution-bytes.v1` | exact bytes |
| assigned/readback prompt-chain bytes | `pi.prompt-chain-bytes.v1` | exact bytes |

No registry, edge catalog, resolver artifact set, or target-first discovery exists.

## Schema 1 — request

`semantic-pi-insertion-request.v1` is exactly:

```text
schema
protocol_revision
repository_id
component_id
package_name
execution_generation
attempt_id
handler_registration_index
input_prompt_byte_length
input_prompt_digest
contribution_byte_length
contribution_digest
request_digest
```

Productions:

- `schema="semantic-pi-insertion-request.v1"`;
- `protocol_revision="semantic-pi-insertion-evidence-v1-r1"`;
- fixed identity equals this RFC;
- generation, attempt, index, and lengths are integers; input length is `0..16777216` and contribution length is `1..16777216`;
- input and contribution lengths equal the retained immutable byte arrays and their digests use the raw-byte domains above;
- `request_digest` uses `semantic-pi-insertion.request.v1`.

The host constructs this request from registered contributor output; caller-supplied identity is forbidden.

## Schema 2 — host application witness

`pi.prompt-chain-application-witness.v1` is exactly:

```text
schema
host_package
protocol_revision
request_digest
execution_generation
attempt_id
handler_registration_index
assigned_prompt_chain_byte_length
assigned_prompt_chain_digest
readback_prompt_chain_byte_length
readback_prompt_chain_digest
contribution_start_byte_offset
contribution_end_byte_offset
observation_phase
provider_request_dispatched_at_observation
model_invocation_started_at_observation
witness_digest
```

Productions:

- `schema="pi.prompt-chain-application-witness.v1"`;
- host package and revision are fixed;
- IDs/index equal the request;
- assigned/readback lengths and digests use `pi.prompt-chain-bytes.v1` and are byte-identical;
- offsets are integers with `start < end <= assigned length` and `end-start=contribution_byte_length` from Schema 1;
- the prompt-chain apply operation returns the exact inserted byte span as part of its host-private result; the witness copies that span directly and never discovers it by searching assigned bytes;
- the assigned byte slice `[start,end)` equals retained contribution bytes; pre-existing or repeated identical byte sequences elsewhere are irrelevant;
- `observation_phase="post_assignment_readback_pre_dispatch"`;
- both booleans are exactly `false`;
- `witness_digest` uses `pi.prompt-chain-application-witness.v1`.

The live witness is not this JSON object alone. Registration atomically creates one immutable host-private record `{execution_generation,repository_id,component_id,package_name,handler_registration_index,capability_nonce,prepare_callback,applied_callback}` from the host loader's accepted registration, never callback input; callback and record identities are compared by object identity. Each host invocation creates a private call-frame record `{registration_identity,execution_generation,attempt_id,handler_registration_index,invocation_nonce,state}` with state `active|revoked`, installs it in one host-owned async-context slot before callback entry, and revokes/removes it in `finally`. Every host capability entrypoint validates the exact active frame before any effect. An externally detached call, inherited async callback after revocation, replaced callback, stale API, or other registration lacks the matching active frame. The exposed frozen witness has only read-only scalar properties `request_digest,witness_digest,execution_generation,attempt_id,handler_registration_index` and is branded in a private WeakMap to that exact registration and attempt. Stale ExtensionAPI instances and detached/replaced/delegated callbacks do not match. Serialization, cloning, reconstruction, or digest knowledge does not reproduce the brand.

The host-private gateway `beginAcknowledgement(witness,call_frame)` validates the witness brand plus exact registration/generation/attempt/index and performs the sole `issued -> acknowledging` transition. The host installs that registration's call frame, invokes the gateway once, then calls exactly `await applied_callback.call(undefined,Object.freeze({witness}))`. The gateway is not exposed to component code; fixture consumption events invoke this host gateway directly. The return is one in-memory plain JSON object matching Schema 3, not bytes or a string; the host copies it, rejects prototypes/accessors/symbols/cycles, strict-validates exact keys/types, and recomputes JCS/digest. Successful validation transitions the brand `acknowledging -> consumed`; throw, rejection, timeout, abort, reload, or mismatch transitions it to terminal `invalid`. A second transition from any non-`issued` state is `witness_reused`. Internal component delegation is not observable and is not claimed; the claim is only that the exact registered callback returned the validated object under the active host frame.

## Schema 3 — component acknowledgement

`semantic-pi-insertion-acknowledgement.v1` is exactly:

```text
schema
issuer
request_digest
witness_digest
execution_generation
attempt_id
handler_registration_index
acknowledgement_outcome
claim_scope
acknowledgement_digest
```

Productions:

- `schema="semantic-pi-insertion-acknowledgement.v1"`;
- issuer is exactly `{kind:"pi_extension_component",id:"pi-ontology-workflows"}`;
- request/witness and attempt tuple equal the consumed private witness;
- `acknowledgement_outcome="observed_inserted"`;
- `claim_scope="prompt_chain_insertion_only"`;
- self digest uses `semantic-pi-insertion.acknowledgement.v1`.

The acknowledgement is not semantic or production authority. It only confirms that the same contributor received the live witness.

## Schema 4 — host insertion record

`pi.prompt-chain-insertion-record.v1` is exactly:

```text
schema
host_package
protocol_revision
request_digest
witness_digest
acknowledgement_digest
execution_generation
attempt_id
handler_registration_index
insertion_outcome
claim_scope
provider_request_dispatched_at_record
model_invocation_started_at_record
record_phase
insertion_record_digest
```

Productions:

- fixed schema/host/revision;
- all digests and tuple fields equal Schemas 1–3;
- `insertion_outcome="observed_inserted"`;
- `claim_scope="prompt_chain_insertion_only"`;
- both booleans are exactly `false`;
- `record_phase="acknowledged_pre_dispatch"`;
- self digest uses `pi.prompt-chain-insertion-record.v1`.

The host atomically commits the immutable in-memory record and the attempt state before dispatch eligibility. That in-memory commit is the protocol linearization point. Optional later persistence serializes the same record as unauthenticated audit data; persistence is outside the guard, and persistence failure neither authorizes nor invalidates the already observed insertion. Record creation does not assert that dispatch later occurs.

## Schema 5 — error

`semantic-pi-insertion-error.v1` is exactly:

```text
schema
protocol_revision
execution_generation
attempt_id_or_null
stage
error_code
details
error_digest
```

- `schema="semantic-pi-insertion-error.v1"` and revision is fixed;
- `execution_generation` is an integer; attempt is null before reservation and an integer afterward;
- stage is `registration|prepare|apply|assignment|readback|witness|acknowledgement|record|dispatch_guard`;
- error is `malformed_input|identity_mismatch|stale_generation|attempt_reuse|contribution_not_inserted|readback_mismatch|witness_forged|witness_reused|acknowledgement_mismatch|reentry_attempt|aborted|deadline_exceeded|internal_failure`;
- `details` is an array of `0..64` exact `{key,value}` rows, sorted/unique by unsigned UTF-8 `(key,value)`; each key/value is an NFC string of 1..256 UTF-8 bytes;
- validation precedence is `malformed_input -> identity_mismatch -> stale_generation -> attempt_reuse -> contribution_not_inserted -> readback_mismatch -> witness_forged -> witness_reused -> acknowledgement_mismatch -> reentry_attempt -> aborted -> deadline_exceeded -> internal_failure`; the earliest established class is emitted;
- strict-decode/type/key/digest-shape failures use stage of the object being processed and `malformed_input` with empty details;
- self digest uses `semantic-pi-insertion.error.v1`.

Errors are local diagnostics and never insertion evidence.

## Host state machine and sequence

Short host-mutex sections linearize state transitions only; the mutex is never held while awaiting contributor code. A separate active-attempt token prevents a second prompt attempt and a pre-dispatch guard blocks prompt/provider/model/completion entrypoints. Reload, abort, and deadline observers may acquire the mutex between callback settlements and invalidate the active token. Already-running provider/model work from an older completed attempt is outside this attempt's claim. The host acquires the active token and pre-dispatch guard before calling any contributor callback and holds them through terminal failure or record commit.

Generation starts at `0`. The next attempt ID starts at `0`; reservation atomically returns current then increments. Reserving when current is `9007199254740991` fails `attempt_reuse` without wrap. States are exactly `reserved -> preparing -> prepared -> applying -> assigned -> readback_verified -> witnessed -> acknowledging -> record_committed -> dispatch_eligible`; every failure transitions once to terminal `failed`, permanently dispatch-ineligible.

The attempt receives integer `deadline_monotonic_ns` from the host's monotonic clock. Expiry is `now >= deadline`. A mandatory host timer is armed for the deadline and takes a short mutex section at expiry; abort and reload observers do likewise immediately. Before and after each callback/await and before assignment, witness issuance, acknowledgement validation, and record commit, a short mutex section checks in exact order: generation still current, abort not signaled, deadline not expired. The first failing predicate emits respectively `stale_generation`, `aborted`, or `deadline_exceeded`. Terminalization revokes the call frame/active token and releases the pre-dispatch guard, allowing later attempts. Late callback settlement is discarded; every retained host capability checks the revoked frame before effect, so late code cannot reenter, dispatch, complete, or mutate host protocol state. Ambient component side effects outside host capabilities are not claimed or controlled.

Sequence:

1. Under the mutex, verify immutable registration/current generation, reserve attempt ID, acquire guard, enter `reserved`.
2. Enter `preparing`; invoke exact registered `prepare_callback` with immutable input, real abort signal, and deadline; synchronously snapshot its nonempty NFC UTF-8 result; enter `prepared`.
3. Construct Schema 1 from host-derived identity and retained bytes.
4. Enter `applying`; apply the contribution. The chain builder returns `{assigned_bytes,start_byte_offset,end_byte_offset}` from the insertion operation itself.
5. Atomically assign those bytes to host state and enter `assigned`.
6. Read back the same state, compare byte-identically, verify the operation-returned span, enter `readback_verified`.
7. Create Schema 2/private witness and enter `witnessed`.
8. Transition brand to `acknowledging`, enter attempt `acknowledging`, and invoke exact registered `applied_callback({witness})` once.
9. Strict-decode/validate Schema 3, transition brand to `consumed`.
10. Under one short mutex section and final guard check, construct and commit Schema 4, enter `record_committed`, then `dispatch_eligible`; release the active token and pre-dispatch guard.

The closed entrypoint matrix covers `prompt|continuation|completion|provider_dispatch|model_invocation|contributor_callback`. With guard active plus matching active contributor frame, every class is reentry: record `reentry_attempt`, poison the outer attempt to `failed`, and perform no nested operation. With guard active and no frame, every class is synchronously refused without poisoning as exact host-control result `{kind:"dispatch_blocked",entrypoint,execution_generation,attempt_id}`. With a foreign active frame (different registration/generation/attempt) while another attempt is guarded, every class returns `{kind:"stale_invocation",entrypoint,execution_generation,attempt_id}` and poisons the guarded outer attempt to `failed`. With any revoked frame, every class returns the same `stale_invocation` object without effect on a current attempt. With guard absent and no frame, ordinary host policy applies. Guard absent plus an active frame is `internal_failure`. These control results are not persisted schemas or Schema-5 evidence; classification uses private frame/guard state only. Reload takes a short mutex section, increments generation, invalidates every nonterminal registration/witness, and makes any late result `stale_generation`. If generation is already `9007199254740991`, reload invalidates active state and makes the host protocol-ineligible with `internal_failure` rather than wrapping. Reload execution remains separately unauthorized; only its invalidation semantics are defined here.

## Replay and lifecycle

Handler index is the host's total registration order and is immutable for the registration generation. One `(generation,attempt)` can have at most one request, witness, acknowledgement, and committed record in the host's non-evicting process sets. Duplicate record commit is `attempt_reuse`. Each brand can be issued/consumed/committed once. Persisted records are optional audit data only and have no public issuance authentication. No database, recovery actor, cross-process replay service, or production restart semantics are defined.

## Closed conformance set

Schema 6, `semantic-pi-insertion-vector-set.v1`, is exactly `{schema,protocol_revision,cases,host_fixtures,accepted_object_aggregate_sha256}`. A case is exact `{id,input_bytes_base64,contribution_bytes_base64,initial_generation,initial_next_attempt_id,handler_registration_index,deadline_monotonic_ns,events,expected}`. IDs match `^[a-z][a-z0-9-]*$`; byte fields are canonical standard padded base64; integers use the global range; events have `1..64` rows. Events are sparse hooks over a canonical baseline: unless overridden, registration uses fixed identity, monotonic time starts at `0`, prepare settles with `contribution_bytes_base64`, apply inserts those bytes at the end and returns that span, assignment/readback use the resulting bytes, the exact registered applied callback settles with the correct acknowledgement, and record commit succeeds. Events are ordered exact `{at_hook,kind,value}` rows. Hooks are `before_reservation|after_reservation|during_prepare|after_prepare|before_apply|after_apply|after_assignment|after_readback|before_witness|after_witness|during_applied|after_applied|before_record_commit|after_record_commit|after_guard_release|after_failure`; each is encountered at the named operation boundary, not inferred from state. Multiple rows at one hook execute in listed order. Every event must be consumed exactly once; an unreachable, unused, hook-incompatible, or duplicate `(at_hook,kind)` row fails the vector harness. Expected is exactly `{accepted,error_or_null,request_or_null,witness_or_null,acknowledgement_or_null,record_or_null}`. Accepted requires all four objects and null error; rejected requires all four objects null plus one complete Schema-5 error. `accepted_object_aggregate_sha256` is ordinary lowercase SHA-256 over the concatenation, in accepted case-ID order, of JCS request, witness, acknowledgement, and record bytes with no separators. A host fixture is exact `{id,baseline_case_id,events,expected_terminal_state,expected_provider_operations_before_record,expected_model_operations_before_record,expected_control_results}`. `expected_control_results` is an ordered array of exact matrix result objects and is empty when no control entrypoint is invoked. `baseline_case_id="valid-single-insertion"` supplies its complete registration, generation, attempt, deadline, input, contribution, and canonical successful operations before fixture hooks are applied.

Event semantics and compatible hooks are closed: `reserve` at `after_reservation` asserts the canonical decimal ID; `prepare_return_base64` at `during_prepare` supplies callback settlement bytes; `apply_span` at `after_apply` overrides canonical `start:end` operation offsets and relocates insertion to that start; `assign_base64` at `after_assignment` asserts assigned bytes; `readback_base64` at `after_readback` overrides readback bytes; `issue_witness` at `after_witness`, `applied_return_digest` at `after_applied`, and `commit_record` at `after_record_commit` assert implementation-produced digests; `abort_signal=set` at any `before_*|during_*` hook signals abort; `replace_ack_issuer` and `inject_ack_bytes_base64` at `after_applied` mutate/supply acknowledgement; `invoke_nested_prompt=attempt` at `during_applied` calls the guarded prompt entrypoint; `reserve_attempt_override` and `replace_registration_component_id` at `before_reservation` alter only their named reservation/host-loader registration input; `advance_monotonic_ns` at any hook sets harness time; `reload_generation` at any hook sets the exact next generation through reload; `clone_witness_json=true` at `before_witness|after_witness` supplies an unbranded clone to `beginAcknowledgement`; and `consume_witness_twice=true` at `during_applied` invokes `beginAcknowledgement` twice. `inject_ack_bytes_base64` is decoder-only conformance: it supplies exact persisted/test-boundary bytes to the strict Schema-3 decoder; the live callback ABI remains an in-memory object. No other case event kind/value grammar exists. Assertions never supply values to the implementation.

Host fixture events use the same `{at_hook,kind,value}` rules and these control kinds: `prompt_attempt=blocked|reentry`, `continuation_attempt=blocked|reentry`, `completion_attempt=blocked|reentry`, `provider_dispatch_attempt=blocked|reentry`, `model_invocation_attempt=blocked|reentry`, `contributor_callback_attempt=blocked|reentry|stale`, `stale_api_call=rejected`, `detached_callback_call=rejected`, `provider_dispatch_eligibility=released`, `applied_throw=error`, `record_commit=done`, terminal assertion `record_commit=forbidden` at `after_failure`, `create_registration_b=other-component`, `consume_from_registration_b=rejected`, `consume_stale_witness=rejected`, `reload_generation` as above, deferred callback controls `defer_applied=pending`, `settle_applied=late`, `start_next_attempt=allowed`, and order assertions `assign=done`, `readback=verified`, `witness_issued=after_assign|after_readback|generation0`. No fixture control value is an implementation-supplied digest. Successful terminal state is `dispatch_eligible`; failed is `failed`.
`semantic-pi-insertion-evidence-v1-vectors.json` is an opaque normative machine source containing exact ID-sorted cases and fixtures, base64 bytes, event schedules, complete expected objects, JCS-derived digests, and the accepted-object aggregate SHA-256. Implementations may not derive behavior from case IDs or expected fields: Python and Node independently execute events and compare actual results afterward. The file contains sixteen cases—three accepted, twelve ordinary protocol failures, one malformed-JSON failure—and thirteen host fixtures.

## Implementation boundary

A future post-ADR plan may create fresh ROCS, Pi-host, and component tasks. A schema means one named top-level protocol object; inline rows are not schemas. It may generate only the six schemas above plus at most one simple packaging-manifest schema. It may not import any predecessor delivery packet, resolver, production/recovery object, SQL schema, seccomp/Wasm contract, or downstream task identity.

Candidate implementation, installation, reload, dogfood, provider/model execution, publication, activation, live acquisition, and production require separate authorization. This RFC supplies none.
