---
summary: "Normative receipt, witness, attestation, authorization, ledger, and replay contracts for semantic Pi delivery v1 r18."
read_when:
  - "Reviewing the exact semantic Pi delivery v1 RFC r18 contract."
system4d:
  container: "Normative annex to Decision 71 semantic Pi delivery v1."
  compass: "Keep exact executable contracts reviewable without an oversized monolith."
  engine: "Closed schemas and invariants -> independent validators -> owner-gated execution."
  fog: "Reading only the core RFC can omit mandatory annex constraints."
type: "rfc_annex"
status: "in_review"
rfc_revision: "semantic-pi-delivery-v1-r18"
---

# Authority contracts — semantic Pi delivery v1 r18

## Closed delivery receipt union

Every branch has `additionalProperties=false` and the common exact keys:

```text
schema
governance_owner_role
issuer
repository_identity
component_identity
package_identity
package_artifact_identity
component_release_provenance_digest
registrar_binding_digest
host_runtime_manifest_digest
host_capabilities
loaded_component_manifest_digest
loaded_entry_digest
execution_instance_digest
execution_generation
prompt_run_attempt_digest
handler_registration_index
rocs_generation_receipt_digest
consumer_repository
v0_canary_scope
delivery_outcome
claim_scope
host_application_witness_digest
pi_delivery_receipt_digest
issuance_authentication
```

Host capabilities are exactly UTF-8 sorted/unique and include `prompt.system.application-witness.v1`. Consumer/scope are copied only from the resolved generation receipt and imply no owner existence, naming, consent, adoption, or activation.

- **Delivered** adds exactly `delivered_effective_execution_digest` and `applied_prompt_chain_entry_digest`; issuer is the fixed component issuer, issuance authentication is `independent_host_attestation_required`, outcome is `delivered`, claim is `delivered_to_pi_prompt_chain_only`, witness is non-null, and every package/provenance/registrar/execution/application field equals resolved host evidence. `delivered_effective_execution_digest` is not a new digest algorithm: it equals the authenticated resolved generation receipt's existing effective-execution digest byte-for-byte.
- **Suppressed** adds exactly `reported_protocol_issuer` and `suppression_reason`; issuer is the fixed Pi host, reported issuer is the component, issuance authentication is `none_non_authoritative_host_observation`, outcome is `suppressed`, claim is `non_authoritative_suppression_observation_only`, witness is null, and reason is `cancelled|stale_result|policy|duplicate_attempt`.
- **Failed** adds exactly `reported_protocol_issuer` and `error_digest`; the same host/non-authoritative issuance rules apply, outcome is `failed`, claim is `non_authoritative_failure_observation_only`, and witness is null. Deadline equality fails.

Terminal observations prove only JSON integrity, cannot satisfy the Pi receipt role or `ak_optional_pi_v1`, and create no component-issuance or delivery edge. Using them as authority is `delivery_relation_failure`; claiming component issuance is `issuer_scope_violation`. A host without v1 capability/identity emits no v1 object.

`semantic-pi-delivery-error.v1` is component-reported but host-packaged as a non-authoritative observation and exactly `{schema,stage,code,related_artifact_digest,details,error_digest}`. Stage is the constant `prepare`; code is `component_failure|dependency_unavailable|generation_stale|policy_failure`; related digest is nullable; details are UTF-8-key-sorted unique `{key,value}` rows. A failed receipt's `error_digest` resolves exactly this object. Host/controller failures produce no protocol object. They abort before provider dispatch and may write bounded human diagnostics to stderr. In integration mode, exact stderr bytes are opaque operational output subject to the byte limit and `pi.process-stderr-bytes.v1` digest recorded in the controller transcript; their text is never parsed and supplies no receipt, packet, authority, conformance, or success fact. Stderr presence or content never determines success or failure. Failure of any required postcondition unconditionally forbids a valid integration transcript and integration proof; the failed run may retain stderr only as local diagnostic evidence.

## Closed host objects

### Application witness

Exact keys:

```text
schema, issuer, host_runtime_manifest_digest, repository_identity,
component_identity, package_identity, package_artifact_identity,
component_release_provenance_digest, loaded_component_manifest_digest,
loaded_entry_digest, sealed_staging_manifest_digest,
namespace_identity_bootstrap_digest, registrar_binding_digest,
execution_instance_digest, boot_nonce, execution_generation,
prompt_run_attempt_digest, attempt_ordinal, session_instance_nonce,
handler_registration_index, rocs_generation_receipt_digest,
input_prompt_digest, returned_prompt_digest, final_prompt_chain_digest,
applied_prompt_chain_entry_digest, application_outcome,
application_target, observation_phase, host_application_witness_digest
```

Constants: issuer `{kind:pi_host,id:@earendil-works/pi-coding-agent}`, outcome `applied`, target `agent.state.systemPrompt`, phase `post_application`. Input digest hashes exact bytes entering this contributor; returned digest hashes its returned `systemPrompt`; because it is the final effective contributor, returned bytes equal assigned/read-back final bytes; final digest hashes those bytes; applied-entry digest hashes exactly `{handler_registration_index,returned_prompt_digest}`. Every identity/staging/registrar field is host-derived and equal to the resolved binding before the immutable witness crosses into extension code.

### Redemption

Exact keys:

```text
schema, issuer, host_runtime_manifest_digest, execution_instance_digest,
execution_generation, prompt_run_attempt_digest, handler_registration_index,
host_application_witness_digest, subject_kind, subject_digest,
redemption_outcome, redemption_sequence, host_witness_redemption_digest
```

`subject_kind` is `semantic_delivered_receipt|host_integration_acknowledgement`; subject digest is respectively the delivered branch's `pi_delivery_receipt_digest` or `integration_acknowledgement_digest` from the resolved closed object. Outcome is `redeemed`, sequence `1`.

### Integration acknowledgement

Exact keys:

```text
schema, issuer, claim_scope, operation_mode, subject_kind,
authorization_request_digest, authorization_envelope_digest,
execution_generation, rocs_generation_receipt_digest,
input_prompt_digest, filesystem_before_digest,
host_application_witness_digest, prompt_run_attempt_digest,
integration_acknowledgement_digest
```

Issuer is the fixed component identity; claim is `host_integration_acknowledgement_only`, mode `host_integration_only`, and subject `host_integration_acknowledgement`. Every authorization/generation/input/filesystem field equals the host-installed binding. It is not a delivery receipt.

### Replay probe

Exact keys:

```text
schema, issuer, host_application_witness_digest,
host_witness_redemption_digest, repeated_subject_kind,
repeated_subject_digest, probe_outcome, replay_probe_digest
```

Host issuer is fixed and outcome is `rejected_already_redeemed`. `pi.integration-second-attempt-suppression.v1` is exactly `{schema,issuer,authorization_envelope_digest,prompt_run_attempt_digest,duplicate_invocation_ordinal,suppression_reason,host_application_witness_digest,provider_request_dispatched,model_invocation_started,second_attempt_suppression_digest}`. Issuer is fixed host, duplicate invocation ordinal is `1`, reason is `witness_already_redeemed`, witness digest is null, and booleans are false. After replay probe, host invokes the same registrar `prepare` a second time with the already-redeemed first-attempt context marked duplicate invocation `1`; the host guard requires terminal suppressed status before contributor code can allocate a new attempt and forbids contribution/witness/applied. This is an observed second invocation, not allocation of attempt ordinal 1: no second prompt-run attempt digest exists, no replay-history binding is created, and the only allocated attempt remains the ledger-reserved ordinal 0. Any other result fails proof. After first redemption in integration mode, the host invokes the same private redemption primitive a second time with the same opaque brand, subject kind, and digest; that primitive must observe the redeemed tuple and return this rejection without issuing redemption. The host persists both probe and suppression through FD5 and controller verifies their acknowledgements. Constructed objects without these transitions are invalid.

### Integration controller transcript

`pi.host-integration-controller-transcript.v1` has exactly:

```text
schema, controller_identity, controller_executable_digest,
host_runtime_manifest_digest, loaded_component_manifest_digest,
component_release_provenance_digest, registrar_binding_digest,
sealed_staging_manifest_digest, namespace_identity_bootstrap_digest,
runtime_load_observation_digests, dependency_manifest_digests,
process_environment_contract_digest, argv_contract_digest, process_start_nonce,
execution_instance_digest, execution_generation, boot_nonce, session_instance_nonce,
attempt_ordinal, prompt_run_attempt_digest, attempt_reservation_digest,
authorization_request_digest,
authorization_envelope_digest, authorization_claim_record_digest,
host_integration_authorization_binding_digest, authorization_transport_digest,
claim_authority_resolution_digest, pre_witness_authority_resolution_digest,
witness_bytes_digest, witness_commit_ack_digest,
acknowledgement_bytes_digest, acknowledgement_commit_ack_digest,
redemption_bytes_digest, pre_redemption_journal_digest,
pre_redemption_commit_ack_digest, redemption_commit_ack_digest,
replay_probe_bytes_digest, replay_probe_commit_ack_digest,
second_attempt_suppression_digest, second_attempt_suppression_commit_ack_digest,
stdout_digest, stderr_digest, exit_code, provider_request_dispatched,
model_invocation_started, filesystem_before_digest, filesystem_after_digest,
host_processes_teardown_complete, controller_exit_pending, controller_transcript_digest
```

It is integration-only: authorization/acknowledgement/replay fields are non-null, provider dispatch and model invocation are false, host-process teardown is true and controller-exit-pending is true; the transcript never claims final controller absence. Those booleans become irreversibly true at entry to any provider transport or local/remote inference adapter, before side effects. Prompt assignment/readback/witnessing is neither. Any true value forbids proof.

`pi.host-delivery-execution-transcript.v1` is a separate production shape with exactly:

```text
schema, host_runtime_manifest_digest, host_integration_release_provenance_digest,
controller_identity, controller_executable_digest, finalizer_identity,
finalizer_executable_digest, runtime_load_observation_digests,
loaded_component_manifest_digest, execution_instance_digest, boot_nonce, session_instance_nonce,
prompt_run_attempt_digest, rocs_generation_receipt_digest,
host_application_witness_digest, delivery_receipt_bytes_digest,
pre_redemption_journal_digest, host_witness_redemption_digest,
final_prompt_chain_digest, final_readback_digest,
filesystem_manifest_digest, durable_channel_binding_digest,
witness_commit_ack_digest, delivery_receipt_commit_ack_digest,
pre_redemption_commit_ack_digest, redemption_commit_ack_digest,
provider_dispatch_posture, delivery_execution_transcript_digest
```

It contains no integration authorization, acknowledgement, replay-probe, exit, or teardown fields. In both transcript schemas, `runtime_load_observation_digests` is an exact two-item array ordered `[pre_extension_load,pre_redemption]`; both observations share the process nonce and independently resolve all mapping bytes/permissions. `provider_dispatch_posture` is `not_dispatched`; witness-capable mode terminates without provider/model entry. Any later provider execution requires a separate non-witness run and cannot inherit this attempt's receipt as use evidence. One transcript exists per prompt-run attempt. Both transcript types prove deterministic consistency only unless resolved by owner evidence.

### Host attestation resolution

Every signed schema computes `statement_digest` with domain `semantic-release.signed-statement.v1` over JCS of the entire object omitting exactly `statement_digest`, `signature`, and that schema's self-digest field; `signing_key_id` and `signature_algorithm` remain in the preimage. Ed25519 signs the decoded 32 digest bytes, not ASCII. Public keys are exactly 32 bytes and signatures 64 bytes under canonical unpadded base64url; noncanonical encoding rejects. `semantic-release.authority-control-resolution.v1` is exactly `{schema,authority_kind,authority_role,authority_repository,trust_basis_kind,trust_basis_digest,accepted_authority_artifact_revision,accepted_authority_artifact_digest,control_principal_ids,controlled_repository_ids,keys,revocation_head_digest,currentness_cas_digest,action_epoch,verification_outcome,statement_digest,signing_key_id,signature_algorithm,signature,authority_control_resolution_digest}`; control-principal and controlled-repository IDs are NFC strings sorted/unique by unsigned UTF-8 bytes; keys are sorted/unique by UTF-8 `key_id` and exactly `{key_id,algorithm,public_key_base64url,purposes}`, with one algorithm/decoded public key per key ID and purposes UTF-8-sorted/unique drawn only from `authority_control|packet_acceptance|integration_approval|integration_cancellation|ledger_write|store_pin|store_receipt|host_attestation_owner_appointment|host_attestation_statement`. Existing semantic/component/host/AK authorities use `v0_authority_proof`; an attestation owner uses a semantic-owner appointment. Each resolution is signed with `authority_control` purpose by a key authenticated by that external trust basis; the accepted authority artifact defines the complete control-principal/repository/key closure. A resolution cannot establish its own trust basis. Duplicate/ambiguous closure is `malformed_input`; independence intersections compare exact NFC IDs and decoded public-key bytes, and any authenticated overlap is `self_certification`.

Authenticated stores use `semantic-release.authority-store-acquisition-pin.v1` exactly `{schema,authority_kind,authority_role,authority_repository,accepted_authority_artifact_digest,store_id,canonical_store_locator,pin_revision,statement_digest,signing_key_id,signature_algorithm,signature,authority_store_acquisition_pin_digest}` and read receipt exactly `{schema,authority_kind,authority_role,authority_repository,accepted_authority_artifact_digest,store_id,canonical_store_locator,authority_store_acquisition_pin_digest,store_revision,store_head_digest,subject_kind,subject_digest,subject_revision,subject_status,read_at_utc,action_epoch,revocation_head_digest,currentness_cas_digest,statement_digest,signing_key_id,signature_algorithm,signature,authority_store_read_receipt_digest}`. Current control keys with `store_pin`/`store_receipt` purpose sign them. Caller paths, copied stores, unsigned evidence, stale head/revocation/CAS/artifact, or mismatched subject reject. Every `*_utc` value is exactly 30 ASCII bytes `YYYY-MM-DDTHH:MM:SS.NNNNNNNNNZ`, proleptic Gregorian year `0001..9999`, zero-padded, valid calendar date, second `00..59`, no leap second/offset, and exact nanosecond precision. Comparison converts fields with the proleptic-Gregorian algorithm to arbitrary-precision integer nanoseconds from `0001-01-01`; Python uses arbitrary integers and Node uses `BigInt`. For every post-claim checkpoint, `current_utc=checked_at_utc` sampled at completion and `current_boottime=checkpoint_completed_monotonic_ns`; `utc_delta=current_utc-claimed_at_utc` and `boottime_delta=current_boottime-claim_started_ns` must be nonnegative and `utc_delta+1000000000>=boottime_delta`; otherwise realtime rollback rejects. `*_boot_id` is parsed only from a stable no-follow read of exact 37 bytes at `/proc/sys/kernel/random/boot_id`: 36 lowercase hexadecimal UUID characters in `8-4-4-4-12` form plus LF. Finalizer reads before claim and every checkpoint/observation, rechecks descriptor/path bytes, and records the 36-character value; caller-provided boot IDs reject.

`pi.host-attestation-owner-appointment.v1` is exactly `{schema,appointment_id,appointment_revision,decision_id,semantic_owner_role,semantic_owner_repository,semantic_owner_artifact_digest,appointed_owner_role,appointed_owner_repository,appointed_owner_initial_artifact_digest,appointed_owner_control_artifact_digest,host_attestation_trust_root_digest,independence_policy,valid_not_before_utc,valid_not_after_utc,statement_digest,signing_key_id,signature_algorithm,signature,host_attestation_owner_appointment_digest}`. Decision is `71`, role `pi-host-attestation-owner`, policy `decision71-disjoint-control-v1`, and the unique semantic owner signs with appointment purpose through its authenticated store. `pi.host-attestation-trust-root.v1` is exactly `{schema,root_id,root_revision,owner_role,owner_repository,verification_key_id,signature_algorithm,public_key_base64url,valid_not_before_utc,valid_not_after_utc,host_attestation_trust_root_digest}`.

The appointed root signs `pi.host-attestation-statement.v1` exactly `{schema,issuer,host_attestation_owner_appointment_digest,host_attestation_trust_root_digest,host_integration_release_provenance_digest,host_runtime_manifest_digest,runtime_load_observation_digests,execution_instance_digest,boot_nonce,session_instance_nonce,prompt_run_attempt_digest,host_application_witness_digest,host_witness_redemption_digest,delivery_execution_transcript_digest,delivery_transcript_commit_ack_digest,issued_at_utc,statement_digest,signing_key_id,signature_algorithm,signature,host_attestation_statement_digest}`. `pi.host-attestation-resolution.v1` is exactly `{schema,host_attestation_owner_appointment_digest,appointment_acquisition_pin_digest,appointment_read_receipt_digest,semantic_owner_control_resolution_digest,host_attestation_owner_control_resolution_digest,host_owner_control_resolution_digest,component_owner_control_resolution_digest,controller_owner_control_resolution_digest,finalizer_owner_control_resolution_digest,protocol_issuer_owner_control_resolution_digest,host_issuer_owner_control_resolution_digest,host_attestation_trust_root_digest,root_acquisition_pin_digest,root_read_receipt_digest,host_attestation_statement_digest,statement_acquisition_pin_digest,statement_read_receipt_digest,semantic_owner_revocation_head_digest,attestation_owner_revocation_head_digest,action_epoch,currentness_cas_digest,appointment_outcome,independence_outcome,revocation_outcome,verification_outcome,host_attestation_resolution_digest}`; all outcomes are `valid`.

Independence requires empty intersections of control-principal IDs, controlled repository IDs, and public keys between attestation owner and the union of semantic/component/host/controller/finalizer/issuer control closures; unknown closure rejects. Appointed repository differs from Pi extension, Pi host, and semantic-owner repositories. Self-appointment, host/component/controller trust basis, or key/control overlap yields `self_certification`; authenticated revocation yields `trust_revoked`; expiry equality, absence, or supersession yields `trust_reference_stale`. No owner/root instance is provisioned here. The appointment's `appointed_owner_control_artifact_digest` equals the attestation-owner control resolution's accepted artifact; finalizer/protocol-issuer/host-issuer control resolutions are supplied as distinct signed bodies even when their authority roles resolve to the same host/component owner.

## Host event and replay machine

Order:

```text
allocate attempt
-> chain before_agent_start while recording per-handler input/return
-> if prepare returned terminal status, host-package the non-authoritative observation with unchanged prompt and stop
-> otherwise assign final prompt
-> readback/hash
-> issue opaque personalized witness and durably commit its exact bytes through FD5
-> receive semantic delivery receipt or integration acknowledgement and durably commit its exact bytes through FD5
-> validate candidate shape/digest and both commit acknowledgements
-> reverify staged artifacts
-> final readback/hash agent.state.systemPrompt
-> persist the pre-redemption journal through FD5 and receive its durable acknowledgement
-> atomically redeem once and durably persist redemption through FD5
-> for delivery, durably persist the delivery transcript; terminate without provider/model entry
-> for integration, invoke the same redemption primitive again, durably persist the observed rejection, run/durably persist the authorized second-attempt suppression, terminate/reap host and supervisor, then persist the controller transcript
```

Any authorization, acknowledgement, validation, snapshot, final-readback, FD5 persistence/acknowledgement, redemption, replay, teardown, or transcript failure aborts and restores the pre-contribution prompt where possible. Witness-capable mode never enters provider transport or model invocation. No redemption precedes all artifact/prompt/journal postconditions; redemption without exact durable journal/transcript evidence is unresolved. Delivered validation additionally requires signed host attestation. Integration proof requires both use booleans false and terminates after replay/teardown/transcript.

`pi.prompt-system-pre-redemption-journal.v1` has exactly `{schema,execution_instance_digest,prompt_run_attempt_digest,host_application_witness_digest,subject_kind,subject_digest,loaded_component_manifest_digest,registrar_binding_digest,sealed_staging_manifest_digest,final_prompt_chain_digest,final_readback_digest,filesystem_manifest_digest,durable_channel_binding_digest,state,pre_redemption_journal_digest}`. `final_readback_digest` uses `pi.prompt-final-chain.v1` over the exact UTF-8 readback bytes and must equal `final_prompt_chain_digest`. State is `verified_pending_redemption`. It is written and fsynced before redemption. Recovery never manufactures redemption: a journal without a redemption is terminal failed; a redemption without the exact journal plus transcript is unresolved and cannot validate delivery.

State is `allocated -> chained -> applied -> witness_issued -> redeemed`, with failure terminal. Every await rechecks instance/generation/attempt. Reload/new/resume/fork/replacement/shutdown invalidates nonterminal state. Redeemed/invalidated tuples remain in a non-evicting set capped at 4096 for the generation; reaching cap fails closed and requires a new generation. Restart changes execution instance. Production durable replay requires the attestation owner and remains unprovisioned.

## Acyclic isolated authorization and canonical one-shot ledger

The integration controller is a bounded internal component of the real Pi host owner surface, not a new repository product:

The following JSON block is explanatory owner-surface topology only, not an identity preimage. Exact `controller_identity` and `canonical_ledger_identity` are the separate closed core objects.

```json
{
  "governance_owner_role": "pi-host-owner",
  "repository": {
    "repository_id": "pi-mono",
    "canonical_source_locator": "git+https://github.com/tryingET/pi-mono.git",
    "identity_revision": 1
  },
  "component": {
    "component_id": "pi-coding-agent-host-integration-controller",
    "repository_path": "packages/coding-agent",
    "identity_revision": 1
  },
  "canonical_ledger": {
    "store_id": "pi-host-integration-authorization-v1",
    "canonical_store_locator": "sqlite+local://pi-host-owner/semantic-integration-authorization-ledger-v1"
  }
}
```

A separately reviewed Pi-host owner artifact must accept this identity before implementation. The controller remains internal and adds no public command or product surface. `canonical_ledger_identity` is exactly `{store_id:"pi-host-integration-authorization-v1",canonical_store_locator:"sqlite+local://pi-host-owner/semantic-integration-authorization-ledger-v1"}`. Before controller launch finalizer creates `SOCK_SEQPACKET|SOCK_CLOEXEC`, installs controller FD6, and enables `SO_PASSCRED` on both receivers. Ordinary frames have exactly one kernel credential matching pinned PID/starttime and no ancillary item. `pi.integration-controller-bootstrap.v1` is exactly `{schema,authorization_request_digest,authorization_envelope_digest,authorization_claim_record_digest,authorization_claim_store_head_digest,source_bundle_digest,source_bundle_file_byte_length,source_bundle_file_digest,process_start_nonce,controller_bootstrap_digest}`. Finalizer sends one fixed-size `initialize/0` bootstrap carrying exactly one sealed source-bundle memfd; the variable source-bundle object is read from that descriptor. Controller rejects `MSG_CTRUNC|MSG_TRUNC`, validates seals/size/object/file/payload/entry digests, claim/current head, and nonce, replies `initialized/1`, and only then may create FD3/4/5 or launch. No FD6 message transports the post-run resolver artifact set; that set is constructed only as an out-of-band validation input after terminal evidence exists.

`pi.integration-finalizer-message.v1` is exactly `{schema,sequence,action,process_start_nonce,authorization_envelope_digest,checked_record_digest,checked_store_head_digest,result_record_digest,result_store_head_digest,checked_durable_store_head_digest,result_durable_store_head_digest,controller_bootstrap_digest,controller_transcript_digest,controller_transcript_bytes_digest,controller_transcript_byte_length,controller_transcript_commit_ack_digest,terminal_mode,pre_witness_authority_resolution_digest,execution_instance_digest,execution_generation,boot_nonce,session_instance_nonce,attempt_ordinal,prompt_run_attempt_digest,attempt_reservation_digest,result_bodies,process_identities,message_digest}`. Result-body rows are ordered `{kind,digest,byte_length}` and followed by exact JCS frames. Actions/sequences are `initialize/0,initialized/1,supervise_request/2,supervise_committed/3,reserve_request/4,reserved_committed/5,authorize_request/6,authorized_committed|authorize_failed/7,terminal_prepare/8,exit_authorized|terminal_failed/9`. State-changing requests carry checked ledger record/head and null ledger result; terminal prepare additionally carries the exact durable head returned by second-attempt suppression and null durable result. Responses echo checked fields and carry resulting fields. Reserve request carries the proposal tuple. Authorize request checks reserved head; finalizer performs fresh v0-rooted resolution. Current result appends authorized and returns resolution/record/head bodies; non-current `revoked|expired|stale` appends failed with resolution/terminal-observation/record/head bodies and action `authorize_failed`, after which controller kills/reaps host and exits without authorization transport. During `supervise_request/2`, and only then, the controller supplies exact pidfds for host and supervisor via `SCM_RIGHTS` in the same order as process identities; finalizer rejects truncation/count/identity drift, duplicates them with `F_DUPFD_CLOEXEC`, and retains them together with its controller pidfd until terminalization. Every other message rejects ancillary descriptors.

For successful terminal prepare, controller supplies a transcript with `host_processes_teardown_complete=true` and `controller_exit_pending=true`, exact transcript bytes, and the final host-written durable head. Finalizer acquires the durable-store writer lock by exact head CAS, persists the transcript with its own commit request, and replies `exit_authorized` with transcript acknowledgement and resulting durable head. Controller closes FD6 and exits. Finalizer polls all retained pidfds. `pi.integration-teardown-observation.v1` is exactly `{schema,process_start_nonce,claimed_process_identities,initial_process_statuses,termination_actions,all_host_processes_absent,controller_process_absent,teardown_outcome,observed_at_utc,observed_boot_id,observed_boottime_ns,teardown_observation_digest}`; initial rows are ordered `{role,pid,starttime,status}` with status `already_absent|still_alive`, termination rows use `none|pidfd_sigkill` and `not_required|signaled_and_absent`, and outcome is `clean|enforced`. Clean means all were initially absent; enforced means at least one survivor was pidfd-killed and then proved absent. Clean plus fresh terminal currentness appends consumed. Enforced produces signed teardown-failure evidence and appends failed while preserving the already durable transcript/ack/head. If any exact process cannot be made and observed absent, finalizer appends nothing, closes the durable-store lock and every retained descriptor, exits, and only then may later authenticated abandonment recovery own that nonterminal state. Earlier fail mode may omit transcript only before transcript persistence and appends failed through the exact terminal-failure path. Partial/extra/mode-mismatched body, EOF before authorized exit, credential drift, or durable-head drift fails closed; no checked/result field is overloaded.

Construction is acyclic and uses these exhaustive objects.

`semantic-pi-integration-authorization-request.v1` is exactly `{schema,authorization_id,decision_id,operation_mode,subject_kind,rocs_packet_manifest_digest,packet_acceptance_digest,source_bundle_digest,rocs_generation_receipt_digest,execution_generation,expected_attempt_ordinal,duplicate_invocation_ordinal,max_prompt_attempt_allocations,max_prepare_invocations,input_prompt_digest,filesystem_before_digest,disposable_roots,component_commit,component_release_provenance_digest,package_artifact_identity,loaded_component_manifest_digest,host_commit,host_runtime_manifest_digest,controller_identity,controller_commit,controller_executable_digest,host_integration_release_provenance_digest,finalizer_identity,finalizer_commit,finalizer_executable_digest,process_start_nonce,not_before_utc,not_after_utc,max_monotonic_duration_ns,max_witness_issuances,max_redemptions,max_replay_probes,live_acquisition_implemented,production_authorized,authorization_request_digest}`. Decision is `71`, mode `host_integration_only`, subject `host_integration_acknowledgement`, generation/expected attempt ordinal are `0`, duplicate invocation ordinal is `1`, maximum attempt allocations is `1`, maximum prepare invocations is `2`, witness/redemption/replay cardinalities are `1`, and booleans are false. Input and filesystem digests resolve exact bytes/state; disposable roots equal the manifest's disposable roots and are no-follow-realpath-disjoint from sealed/runtime/production/authority/ledger roots. Every observed generation/source bundle, controller/finalizer, nonce, input, filesystem, and subject must equal the request. The later post-run resolver artifact-set digest is deliberately absent from all authorized pre-execution objects, preventing a forward-reference cycle. `max_monotonic_duration_ns` is an integer `1..60000000000`. Immediately before the first authority/ledger/artifact read, finalizer samples `CLOCK_BOOTTIME` once as safe integer `claim_started_ns<=9007139254740991` and UTC as `claimed_at_utc`; this value equals the claim resolution's checkpoint start. `monotonic_deadline_ns=claim_started_ns+max_monotonic_duration_ns` and `global_deadline_ns=claim_started_ns+60000000000`, both checked safe integers. Every action uses the earlier deadline and expires at equality. Same-boot recovery uses this equation; changed boot uses `host_reboot` and never compares old boottime.

`semantic-pi-integration-owner-approval.v1` is exactly `{schema,issuer,owner_repository,owner_artifact_revision,accepted_owner_artifact_digest,authorization_request_digest,approval_scope,valid_not_before_utc,valid_not_after_utc,statement_digest,signing_key_id,signature_algorithm,signature,owner_approval_digest}` with scope `host_integration_only`. Exactly one current component-owner and one current host-owner approval is signed with `integration_approval` purpose and resolved through subject-specific authenticated pins/read receipts. The component approval's accepted artifact is the exact component-release provenance; the host approval's accepted artifact is the exact host-integration release provenance, and every request field joins those artifacts. `semantic-pi-integration-authorization-envelope.v1` is exactly `{schema,authorization_request_digest,component_owner_approval_digest,component_owner_approval_read_receipt_digest,host_owner_approval_digest,host_owner_approval_read_receipt_digest,ak_decision_reference_digest,ak_decision_read_receipt_digest,packet_acceptance_digest,packet_acceptance_read_receipt_digest,issued_at_utc,authorization_envelope_digest}`. AK evidence resolves Decision 71 accepted/current. `semantic-release.ak-decision-reference.v1` is exactly `{schema,decision_id,scope,state,review_outcome,adr_ref,unsuperseded,unrevoked,accepted_at_utc,ak_decision_reference_digest}` with decision `71`, cross-repo scope, state `accepted`, outcome `ready_for_adr`, non-null accepted successor ADR, and true booleans; its digest is the read-receipt subject. Approvals are stored before envelope construction; nothing refers forward.

After claim and a fresh pre-witness checkpoint, `pi.host-integration-authorization-binding.v1` is exactly `{schema,operation_mode,subject_kind,authorization_request_digest,authorization_envelope_digest,authorization_claim_record_digest,authorization_current_record_digest,claim_authority_resolution_digest,pre_witness_authority_resolution_digest,process_start_nonce,execution_instance_digest,execution_generation,boot_nonce,session_instance_nonce,attempt_ordinal,prompt_run_attempt_digest,attempt_reservation_digest,expected_attempt_ordinal,rocs_generation_receipt_digest,input_prompt_digest,filesystem_before_digest,host_integration_authorization_binding_digest}`. Before extension initialization the controller sends one additional authenticated FD3 frame `pi.host-integration-authorization-transport.v1` exactly `{schema,action,process_start_nonce,authorization_envelope_digest,authorization_binding_digest,envelope_byte_length,binding_byte_length,authorization_transport_digest}` followed by the two exact JCS body frames. Bodies are transport payloads resolved by digest, never embedded object fields or duplicate resolver roles, action `install_host_integration_authorization`. Missing/repeated/reordered/stale/wrong-mode/wrong-nonce transport aborts. Host exposes the deeply immutable nested objects—not ledger handles, paths, signing material, or mutation methods—to only the selected registrar's prepare/applied contexts. Production sends no frame.

`semantic-release.pi-integration-action-authority-resolution.v1` is exactly `{schema,phase,terminal_mode,authorization_request_digest,authorization_envelope_digest,process_start_nonce,authorization_claim_record_digest,authorization_current_record_digest,controller_transcript_digest,controller_transcript_commit_ack_digest,teardown_observation_digest,durable_store_head_digest,durable_store_acquisition_pin_digest,durable_store_read_receipt_digest,canonical_ledger_store_head_digest,canonical_ledger_acquisition_pin_digest,canonical_ledger_read_receipt_digest,component_owner_control_resolution_digest,component_owner_acquisition_pin_digest,component_owner_approval_read_receipt_digest,host_owner_control_resolution_digest,host_owner_acquisition_pin_digest,host_owner_approval_read_receipt_digest,ak_control_resolution_digest,ak_acquisition_pin_digest,ak_decision_read_receipt_digest,packet_acceptance_owner_control_resolution_digest,packet_acceptance_acquisition_pin_digest,packet_acceptance_read_receipt_digest,checked_boot_id,checkpoint_started_monotonic_ns,checkpoint_completed_monotonic_ns,checked_at_utc,action_epoch,verification_outcome,integration_action_authority_resolution_digest}`. Phase is `claim|pre_witness|terminal`; `terminal_mode` is null except terminal `consume|fail`; verification outcome is exactly `current|revoked|expired|stale`, and only current authorizes continuation. At `claim`, claim/current-record/transcript fields are null and the head names the unique available pre-state, so the resolution can be embedded in the later claimed record without a cycle. A non-current claim performs no claim CAS: revoked/expired available authorization is cancelled with exact evidence, while stale leaves it unavailable and unmodified. At `pre_witness`, claim/current reserved records are non-null and transcript is null; the immediate CAS creates the `authorized` record before transport. A non-current pre-witness result maps `revoked->authority_revoked`, `expired->authorization_expired|deadline_expired` by precedence, and `stale->checkpoint_stale`; finalizer atomically appends failed and returns `authorize_failed` bodies, so no reserved chain is stranded. At `terminal`, claim/current records are non-null. Consume requires transcript/commit-ack plus finalizer-issued clean teardown observation after replay, host teardown, filesystem recheck, controller exit, and durable persistence. `durable_store_read_receipt_digest` is null in claim, pre-witness, and terminal action resolutions because the terminal-sealed receipt is issued only after the ledger CAS; those resolutions instead bind the exact durable head and acquisition pin. The later proof supplies the final receipt. Fail before transcript persistence requires transcript/commit-ack/teardown null. Fail after transcript persistence for enforced teardown requires the exact non-null transcript, commit acknowledgement, durable head, enforced teardown observation, and teardown-failure evidence; it preserves rather than manufactures them. Both fail branches permit only failed CAS and never manufacture replay/redemption evidence. Every phase performs fresh canonical reads; validity is half-open. Except authenticated reboot abandonment, `checked_boot_id=claim_boot_id` and `claim_started_ns<=checkpoint_started_monotonic_ns<=checkpoint_completed_monotonic_ns`; current checkpoints complete before both deadlines, while deadline-failure observation requires completion at/after the applicable deadline. Terminal observation boot/time equals the terminal checkpoint or abandonment observation. Reboot uses a different boot ID and never compares boottime values across boots. Claim completes immediately before CAS; pre-witness runs while host is paused immediately before authorization transport/extension init; each terminal mode completes immediately before its corresponding CAS. Revocation, expiry equality, stale head/pin/CAS/key/artifact, Decision drift, realtime rollback relative to `CLOCK_BOOTTIME`, or epoch regression fails. Non-current terminal may append only failed; unavailable writer authority leaves a nonterminal claim for the pinned finalizer and never restores available.

The canonical append-only SQLite ledger is outside disposable/sealed/production roots and resolves only through a current host-owner pin/read receipt. A record is exactly `{schema,store_id,canonical_store_locator,store_revision,prior_store_head_digest,decision_id,authorization_envelope_digest,sequence,prior_record_digest,state,process_start_nonce,host_runtime_manifest_digest,writer_identity,writer_executable_digest,writer_authority_resolution_digest,claim_authority_resolution_digest,pre_witness_authority_resolution_digest,terminal_authority_resolution_digest,claimed_at_utc,claim_boot_id,monotonic_clock_id,claim_started_ns,monotonic_deadline_ns,global_deadline_ns,execution_instance_digest,execution_generation,boot_nonce,session_instance_nonce,attempt_ordinal,prompt_run_attempt_digest,attempt_reservation_digest,finalizer_process_identity,controller_process_identity,supervised_process_identities,cancellation_digest,cancellation_read_receipt_digest,abandonment_observation_digest,teardown_observation_digest,terminal_observation_digest,terminal_reason,controller_transcript_digest,authorization_ledger_record_digest}`. Clock is `CLOCK_BOOTTIME`; process rows are sorted `{role,pid,starttime}`. Legal transitions only are `available->claimed`, `available->cancelled`, `claimed->supervised|failed`, `supervised->reserved|failed`, `reserved->authorized|failed`, and `authorized->consumed|failed`; terminal states never reopen. Structural/writer fields, process nonce, and request-equal host runtime manifest digest are non-null in every state; prior-record is null only for available. Exact state table: available has all three action resolutions, claim metadata, both process identities, and process array null/empty, with cancellation/abandonment/reason/transcript null; claimed adds claim resolution plus claim time/boot/clock/deadline and the exact finalizer `{role,pid,starttime}`, while controller identity is null and supervised process array empty; supervised carries claimed fields, adds the exact controller identity and nonempty host/supervisor process array, with reservation/pre/terminal/cancellation/abandonment/reason/transcript null; reserved adds the non-null execution/session/attempt tuple and reservation digest with pre/terminal/cancellation/abandonment/reason/transcript null; authorized inherits reservation and adds non-null pre-witness resolution, terminal/cancellation/abandonment/reason/transcript null; reservation tuple fields are null in available, claimed, and supervised; teardown observation is null in every nonterminal/cancelled state; consumed has all three resolutions, inherited metadata/processes, null cancellation/abandonment/terminal-observation, non-null teardown observation, reason `completed`, and non-null transcript; failed inherits every reached phase field, has terminal resolution except when unavailable during authenticated abandonment, null cancellation, abandonment non-null exactly for abandonment/reboot/deadline recovery, terminal observation non-null for every failed record, non-null reason, and transcript non-null exactly when already durable; cancelled has action/claim/process/abandonment/transcript fields null, reason and terminal observation non-null, and cancellation/read fields always non-null. Failed reason is `authority_revoked|authorization_expired|checkpoint_stale|controller_failure|host_failure|teardown_failure|deadline_expired|abandoned_claim|host_reboot`; cancelled reason is `owner_cancelled|decision_revoked|packet_acceptance_revoked|authorization_expired` with authenticated cancellation or conclusive current revocation/expiry.

After each record, `semantic-pi-integration-ledger-store-head.v1` is exactly `{schema,store_id,canonical_store_locator,store_revision,record_digest,prior_store_head_digest,ledger_store_head_digest}`. The first available record for an authorization has per-authorization sequence `0`, null prior-record digest, non-null current global prior-store head (or null only for empty-store genesis), and global store revision prior+1; it is appended only after the envelope and both current owner receipts exist. The ledger enforces a permanent partial unique index on `decision_id WHERE sequence=0`; Decision 71 may have exactly one authorization chain anchor, and every successor retains the anchor's decision/envelope and exact prior-record lineage across complete non-pruned history, regardless of cancelled/failed/consumed outcome. A second request/envelope/available record for Decision 71 is `authorization_or_replay_failure`. Every exact record key not required by its state is JSON null. `pi.integration-operational-failure-evidence.v1` is exactly `{schema,issuer,process_start_nonce,stage,code,observed_at_utc,observed_boottime_ns,process_identities,details,operational_failure_evidence_digest}`; issuer is fixed finalizer, stage is `controller|host|teardown`, code is nonempty NFC, process rows are exact/sorted, details are sorted `{key,value}`. `semantic-release.pi-integration-terminal-observation.v1` is exactly `{schema,issuer,authorization_envelope_digest,observed_at_utc,observed_boot_id,observed_boottime_ns,action_epoch,terminal_reason,component_owner_evidence_digest,host_owner_evidence_digest,ak_decision_evidence_digest,packet_acceptance_evidence_digest,owner_cancellation_evidence_digest,operational_failure_evidence_digest,abandonment_observation_digest,statement_digest,signing_key_id,signature_algorithm,signature,terminal_observation_digest}` and is signed by the fixed finalizer with current `ledger_write` authority. Reason table: `authority_revoked` requires one or more exact revoked component/host/AK/packet-acceptance evidence bodies; `checkpoint_stale` requires one or more exact stale component/host/AK/packet-acceptance bodies; `authorization_expired|deadline_expired` require all evidence digests null and satisfy the UTC/boottime equations; `controller_failure|host_failure|teardown_failure` require only matching operational evidence; `abandoned_claim|host_reboot` require only abandonment evidence; `owner_cancelled` requires component/host owner-cancellation evidence; `decision_revoked` requires AK cancellation plus revocation evidence; `packet_acceptance_revoked` requires packet-owner cancellation plus packet revocation evidence. All unrequired evidence fields are null. If UTC authorization expiry and monotonic/global deadline expiry are both established at one observation, terminal reason is `deadline_expired`; otherwise the established single reason applies. For an available-state `authorization_expired` cancellation, claim timing remains null; observation validates only `observed_at_utc>=request.not_after_utc`, and its observed boot/boottime are recorded but not compared to a nonexistent claim. Post-claim deadline/expiry uses the checkpoint equations; terminal observation UTC/boot/boottime equals `checked_at_utc`, `checked_boot_id`, and `checkpoint_completed_monotonic_ns` of the terminal resolution. `semantic-release.pi-owner-cancellation-evidence.v1` is exactly `{schema,issuer,authority_role,authorization_request_digest,authorization_envelope_digest,cancellation_reason,issued_at_utc,statement_digest,signing_key_id,signature_algorithm,signature,owner_cancellation_evidence_digest}`. Reason is `owner_cancelled|decision_revoked|packet_acceptance_revoked`; component/host/packet-acceptance owner or AK authority signs with `integration_cancellation` purpose, publishes it, and supplies its authenticated read receipt before cancellation. `semantic-pi-integration-cancellation.v1` is exactly `{schema,issuer,authorization_envelope_digest,terminal_observation_digest,owner_cancellation_evidence_digest,owner_cancellation_read_receipt_digest,cancellation_reason,issued_at_utc,statement_digest,signing_key_id,signature_algorithm,signature,integration_cancellation_digest}` and uses a current cancellation-purpose key/read receipt; automatic expiry/revocation cancellation is signed by the pinned finalizer under current host-owner authority and never omits either cancellation or receipt. Cancellation reason equals terminal-observation/ledger reason: `owner_cancelled` requires the component/host owner-cancellation object/read receipt, `decision_revoked` requires the AK cancellation object/read receipt plus AK revocation evidence, `packet_acceptance_revoked` requires the packet-owner cancellation object/read receipt plus packet revocation evidence, and `authorization_expired` has both owner-cancellation fields null and uses the clock-only observation. Failed record reason equals its observation and every referenced evidence body is present in the resolver/reference set. Abandonment process rows are `{role,pid,starttime}`, observed rows add `status:exact_process_alive|pid_absent|starttime_mismatch`, and termination rows add `action:none|pidfd_sigkill,outcome:not_required|signaled_and_absent`. Every append uses `BEGIN IMMEDIATE`, exact prior-head/record/revision CAS, increments sequence/revision, fsyncs record/store/directory, and is reread through the current pin/receipt. Copied, restored, alternate, concurrent, or stale stores reject. Only the request-pinned finalizer executable with fresh host-owner writer authority appends; controller never writes the ledger. It claims before launch and records/fsyncs its own PID/starttime in claimed. It records/fsyncs controller PID/starttime plus host/supervisor PID/starttime identities in supervised while every child is paused, then releases them. Parent death or authority-channel EOF kills children. Ledger SQLite is fixed to application id `0x50494c31`, user version `1`, journal mode `DELETE`, `synchronous=FULL`, `locking_mode=EXCLUSIVE`, foreign keys on, trusted schema off, secure delete on; exact schema SQL bytes are packet-pinned. Records and heads are immutable JCS BLOBs with unique global revision, `(decision_id,sequence)`, record digest, and partial unique Decision-71 anchor constraints. Each transition uses `BEGIN IMMEDIATE`, verifies current externally anchored head and allowed state, inserts record/head, commits, then fsyncs DB and parent directory before releasing a process barrier. On open SQLite rollback recovery completes first, followed by integrity check, schema/application/version checks, and full head/record chain validation. Uncommitted rows disappear; committed incomplete/mismatched state is terminal corruption. No WAL, copied DB, alternate path, restore, or retry-to-available is legal.

`semantic-release.pi-integration-abandonment-observation.v1` is exactly `{schema,authorization_envelope_digest,authorization_claim_record_digest,authorization_current_record_digest,canonical_ledger_store_head_digest,observed_boot_id,observed_at_utc,observed_monotonic_ns,finalizer_identity,finalizer_executable_digest,finalizer_authority_resolution_digest,abandonment_reason,claimed_process_identities,observed_process_identities,termination_actions,all_claimed_processes_absent,all_supervised_processes_terminated,integration_abandonment_observation_digest}`. Recovery requires exact latest claimed/supervised/reserved/authorized chain, the record-carried finalizer identity and—after supervised—the record-carried controller identity, and one of changed boot, deadline equality/expiry, or absent/different-starttime finalizer/controller. On the same boot only, it opens `/proc/<pid>` no-follow, verifies recorded starttime before and after `pidfd_open`, rejects replacement races, then pidfd-kills only exact live identities, waits, and proves all absent; changed boot treats prior identities as absent and never opens old pidfds; then only `claimed|supervised|reserved|authorized -> failed`, preserving any authorized pre-witness and reserved tuple fields. Unverifiable/surviving identity or stale authority/head forbids append. Cancellation is only from available and requires a current component/host/packet-acceptance/Decision authority signature/read receipt or a terminal observation proving current expiry/revocation; every path emits the signed cancellation plus read receipt. Recovery never creates acknowledgement, redemption, transcript, cancellation from a claim, or availability. It cannot issue proof from a nonterminal, failed, or cancelled chain; after a consumed chain exists, the request-pinned finalizer may deterministically issue or reissue the byte-identical proof from current receipt-anchored evidence without ledger mutation.

## Closed integration proof

`semantic-pi-host-integration-proof.v1` exact keys:

```text
schema, issuer, claim_scope, authorization_request_digest,
authorization_envelope_digest, authorization_claim_record_digest,
authorization_terminal_record_digest, claim_authority_resolution_digest,
pre_witness_authority_resolution_digest, terminal_authority_resolution_digest,
terminal_ledger_store_head_digest, durable_store_head_digest,
host_runtime_manifest_digest,
loaded_component_manifest_digest, prompt_run_attempt_digest,
host_application_witness_digest, integration_acknowledgement_digest,
host_witness_redemption_digest, replay_probe_digest,
second_attempt_suppression_digest, teardown_observation_digest,
controller_transcript_digest, controller_transcript_commit_ack_digest,
provider_request_dispatched,
publication_authorized, adoption_authorized, activation_authorized,
provider_or_model_use_observed, influence_observed,
production_authorized, integration_proof_digest
```

Issuer equals closed `finalizer_identity`, claim is `host_integration_only`, and all booleans are false. The proof has no timestamp or issuance nonce, so its JCS bytes are a deterministic function of the consumed evidence and idempotent reissuance is byte-identical. Provider/model use is derived as transcript dispatch OR model-invocation and prompt application alone is not use. Construction is witness -> acknowledgement -> redemption -> observed replay rejection -> observed/durable duplicate-invocation suppression -> clean host teardown -> finalizer-durable controller transcript -> controller exit -> clean teardown observation -> fresh terminal resolution -> consumed record/head -> current durable-store and ledger read receipts -> proof. Validation supplies current receipts outside the proof. The ledger receipt names the consumed record as subject and the complete history links its terminal head to the receipt's current global head; the durable-store receipt names the immutable terminal-sealed transcript head. Any failed/cancelled/nonterminal/copied/stale chain rejects. ROCS delivery validation and AK delivery linkage reject this schema. AK may record it only as implementation-validation evidence.
