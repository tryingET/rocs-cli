---
summary: "Normative receipt, witness, attestation, authorization, ledger, and replay contracts for semantic Pi delivery v1 r16."
read_when:
  - "Reviewing the exact semantic Pi delivery v1 RFC r16 contract."
system4d:
  container: "Normative annex to Decision 71 semantic Pi delivery v1."
  compass: "Keep exact executable contracts reviewable without an oversized monolith."
  engine: "Closed schemas and invariants -> independent validators -> owner-gated execution."
  fog: "Reading only the core RFC can omit mandatory annex constraints."
type: "rfc_annex"
status: "in_review"
rfc_revision: "semantic-pi-delivery-v1-r16"
---

# Authority contracts — semantic Pi delivery v1 r16

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

Host issuer is fixed and outcome is `rejected_already_redeemed`. After first redemption in integration mode, the host invokes the same private redemption primitive a second time with the same opaque brand, subject kind, and digest; that primitive must observe the redeemed tuple and return this rejection without issuing redemption. The host persists the probe through FD5 and controller verifies its acknowledgement. A constructed object without this observed transition is invalid.

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
replay_probe_bytes_digest, replay_probe_commit_ack_digest, stdout_digest, stderr_digest, exit_code, provider_request_dispatched,
model_invocation_started, filesystem_before_digest, filesystem_after_digest,
process_teardown_complete, controller_transcript_digest
```

It is integration-only: authorization/acknowledgement/replay fields are non-null, provider dispatch and model invocation are false, and teardown is true. Those booleans become irreversibly true at entry to any provider transport or local/remote inference adapter, before side effects. Prompt assignment/readback/witnessing is neither. Any true value forbids proof.

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

Every signed schema computes `statement_digest` with domain `semantic-release.signed-statement.v1` over JCS of the entire object omitting exactly `statement_digest`, `signature`, and that schema's self-digest field; `signing_key_id` and `signature_algorithm` remain in the preimage. Ed25519 signs the decoded 32 digest bytes, not ASCII. Public keys are exactly 32 bytes and signatures 64 bytes under canonical unpadded base64url; noncanonical encoding rejects. `semantic-release.authority-control-resolution.v1` is exactly `{schema,authority_kind,authority_role,authority_repository,trust_basis_kind,trust_basis_digest,accepted_authority_artifact_revision,accepted_authority_artifact_digest,control_principal_ids,controlled_repository_ids,keys,revocation_head_digest,currentness_cas_digest,action_epoch,verification_outcome,authority_control_resolution_digest}`; keys are sorted `{key_id,algorithm,public_key_base64url,purposes}`, with purposes drawn only from `integration_approval|integration_cancellation|ledger_write|store_pin|store_receipt|host_attestation_owner_appointment|host_attestation_statement`. Existing semantic/component/host/AK authorities use `v0_authority_proof`; an attestation owner uses a semantic-owner appointment. A resolution cannot establish its own trust basis.

Authenticated stores use `semantic-release.authority-store-acquisition-pin.v1` exactly `{schema,authority_kind,authority_role,authority_repository,accepted_authority_artifact_digest,store_id,canonical_store_locator,pin_revision,statement_digest,signing_key_id,signature_algorithm,signature,authority_store_acquisition_pin_digest}` and read receipt exactly `{schema,authority_kind,authority_role,authority_repository,accepted_authority_artifact_digest,store_id,canonical_store_locator,authority_store_acquisition_pin_digest,store_revision,store_head_digest,subject_kind,subject_digest,subject_revision,subject_status,read_at_utc,action_epoch,revocation_head_digest,currentness_cas_digest,statement_digest,signing_key_id,signature_algorithm,signature,authority_store_read_receipt_digest}`. Current control keys with `store_pin`/`store_receipt` purpose sign them. Caller paths, copied stores, unsigned evidence, stale head/revocation/CAS/artifact, or mismatched subject reject.

`pi.host-attestation-owner-appointment.v1` is exactly `{schema,appointment_id,appointment_revision,decision_id,semantic_owner_role,semantic_owner_repository,semantic_owner_artifact_digest,appointed_owner_role,appointed_owner_repository,appointed_owner_initial_artifact_digest,host_attestation_trust_root_digest,independence_policy,valid_not_before_utc,valid_not_after_utc,statement_digest,signing_key_id,signature_algorithm,signature,host_attestation_owner_appointment_digest}`. Decision is `71`, role `pi-host-attestation-owner`, policy `decision71-disjoint-control-v1`, and the unique semantic owner signs with appointment purpose through its authenticated store. `pi.host-attestation-trust-root.v1` is exactly `{schema,root_id,root_revision,owner_role,owner_repository,verification_key_id,signature_algorithm,public_key_base64url,valid_not_before_utc,valid_not_after_utc,host_attestation_trust_root_digest}`.

The appointed root signs `pi.host-attestation-statement.v1` exactly `{schema,issuer,host_attestation_owner_appointment_digest,host_attestation_trust_root_digest,host_integration_release_provenance_digest,host_runtime_manifest_digest,runtime_load_observation_digests,execution_instance_digest,boot_nonce,session_instance_nonce,prompt_run_attempt_digest,host_application_witness_digest,host_witness_redemption_digest,delivery_execution_transcript_digest,delivery_transcript_commit_ack_digest,issued_at_utc,statement_digest,signing_key_id,signature_algorithm,signature,host_attestation_statement_digest}`. `pi.host-attestation-resolution.v1` is exactly `{schema,host_attestation_owner_appointment_digest,appointment_acquisition_pin_digest,appointment_read_receipt_digest,semantic_owner_control_resolution_digest,host_attestation_owner_control_resolution_digest,host_owner_control_resolution_digest,component_owner_control_resolution_digest,controller_owner_control_resolution_digest,host_attestation_trust_root_digest,root_acquisition_pin_digest,root_read_receipt_digest,host_attestation_statement_digest,statement_acquisition_pin_digest,statement_read_receipt_digest,semantic_owner_revocation_head_digest,attestation_owner_revocation_head_digest,action_epoch,currentness_cas_digest,appointment_outcome,independence_outcome,revocation_outcome,verification_outcome,host_attestation_resolution_digest}`; all outcomes are `valid`.

Independence requires empty intersections of control-principal IDs, controlled repository IDs, and public keys between attestation owner and the union of semantic/component/host/controller/finalizer/issuer control closures; unknown closure rejects. Appointed repository differs from Pi extension, Pi host, and semantic-owner repositories. Self-appointment, host/component/controller trust basis, key/control overlap, expiry equality, revocation, or supersession yields `self_certification` or `trust_revoked`. No owner/root instance is provisioned here.

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
-> for integration, invoke the same redemption primitive again, durably persist the observed rejection, terminate/reap, then durably persist the controller transcript
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

A separately reviewed Pi-host owner artifact must accept this identity before implementation. The controller remains internal and adds no public command or product surface. `canonical_ledger_identity` is exactly `{store_id:"pi-host-integration-authorization-v1",canonical_store_locator:"sqlite+local://pi-host-owner/semantic-integration-authorization-ledger-v1"}`. Before controller launch the finalizer creates `SOCK_SEQPACKET|SOCK_CLOEXEC`, retains one endpoint, installs its peer as controller FD6, and before any send enables `SO_PASSCRED` on both receiving endpoints. Every FD6 message/body/response carries exactly one kernel-supplied `SCM_CREDENTIALS`, no sender control message or other ancillary item, and PID/starttime equal to the pinned finalizer/controller process. `pi.integration-finalizer-message.v1` is exactly `{schema,sequence,action,process_start_nonce,authorization_envelope_digest,record_digest,store_head_digest,controller_transcript_digest,controller_transcript_bytes_digest,controller_transcript_byte_length,controller_transcript_commit_ack_digest,terminal_mode,pre_witness_authority_resolution_digest,execution_instance_digest,execution_generation,boot_nonce,session_instance_nonce,attempt_ordinal,prompt_run_attempt_digest,attempt_reservation_digest,process_identities,message_digest}`; actions/sequence are `supervise_request/0`, `supervise_committed/1`, `reserve_request/2`, `reserved_committed/3`, `authorize_request/4`, `authorized_committed/5`, `terminal_request/6`, `terminal_committed/7`, with sorted `{role,pid,starttime}` rows. Supervise/reserve/authorize requests have null result record/head until their finalizer CAS. Reserve request carries the host proposal tuple/digest and response carries the durable reserved record/head. Authorize request carries the fresh pre-witness resolution and references that reserved head; response carries the authorized record/head. Terminal request has `terminal_mode=consume|fail`. Consume sends this JCS frame followed by one raw transcript frame with declared length/digest and null commit acknowledgement; finalizer verifies/persists it and response carries the acknowledgement. Fail requires transcript/digest/length/ack null and no body. Partial/extra/truncated or mode-mismatched body fails. Finalizer responses carry exact resulting record/head. Wrong credentials, nonce, envelope, order, nullability, or extra message fails. Controller/host remain paused until supervised response. EOF kills exact child identities; neither side treats FD6 as authority.

Construction is acyclic and uses these exhaustive objects.

`semantic-pi-integration-authorization-request.v1` is exactly `{schema,authorization_id,decision_id,operation_mode,subject_kind,rocs_packet_manifest_digest,rocs_generation_receipt_digest,execution_generation,expected_attempt_ordinal,input_prompt_digest,filesystem_before_digest,disposable_roots,component_commit,component_release_provenance_digest,package_artifact_identity,loaded_component_manifest_digest,host_commit,host_runtime_manifest_digest,controller_identity,controller_commit,controller_executable_digest,host_integration_release_provenance_digest,finalizer_identity,finalizer_commit,finalizer_executable_digest,process_start_nonce,not_before_utc,not_after_utc,max_monotonic_duration_ns,max_witness_issuances,max_redemptions,max_replay_probes,live_acquisition_implemented,production_authorized,authorization_request_digest}`. Decision is `71`, mode `host_integration_only`, subject `host_integration_acknowledgement`, generation and expected ordinal are `0`, cardinalities are `1`, and booleans are false. Input and filesystem digests resolve exact bytes/state; disposable roots equal the manifest's disposable roots and are no-follow-realpath-disjoint from sealed/runtime/production/authority/ledger roots. Every observed generation, artifact, controller/finalizer, nonce, input, filesystem, and subject must equal the request.

`semantic-pi-integration-owner-approval.v1` is exactly `{schema,issuer,owner_repository,owner_artifact_revision,accepted_owner_artifact_digest,authorization_request_digest,approval_scope,valid_not_before_utc,valid_not_after_utc,statement_digest,signing_key_id,signature_algorithm,signature,owner_approval_digest}` with scope `host_integration_only`. Exactly one current component-owner and one current host-owner approval is signed with `integration_approval` purpose and resolved through subject-specific authenticated pins/read receipts. The component approval's accepted artifact is the exact component-release provenance; the host approval's accepted artifact is the exact host-integration release provenance, and every request field joins those artifacts. `semantic-pi-integration-authorization-envelope.v1` is exactly `{schema,authorization_request_digest,component_owner_approval_digest,component_owner_approval_read_receipt_digest,host_owner_approval_digest,host_owner_approval_read_receipt_digest,ak_decision_reference_digest,ak_decision_read_receipt_digest,issued_at_utc,authorization_envelope_digest}`. AK evidence resolves Decision 71 accepted/current. Approvals are stored before envelope construction; nothing refers forward.

After claim and a fresh pre-witness checkpoint, `pi.host-integration-authorization-binding.v1` is exactly `{schema,operation_mode,subject_kind,authorization_request_digest,authorization_envelope_digest,authorization_claim_record_digest,authorization_current_record_digest,claim_authority_resolution_digest,pre_witness_authority_resolution_digest,process_start_nonce,execution_instance_digest,execution_generation,boot_nonce,session_instance_nonce,attempt_ordinal,prompt_run_attempt_digest,attempt_reservation_digest,expected_attempt_ordinal,rocs_generation_receipt_digest,input_prompt_digest,filesystem_before_digest,host_integration_authorization_binding_digest}`. Before extension initialization the controller sends one additional authenticated FD3 frame `pi.host-integration-authorization-transport.v1` exactly `{schema,action,process_start_nonce,authorization_envelope,authorization_binding,authorization_transport_digest}`, action `install_host_integration_authorization`. Missing/repeated/reordered/stale/wrong-mode/wrong-nonce transport aborts. Host exposes the deeply immutable nested objects—not ledger handles, paths, signing material, or mutation methods—to only the selected registrar's prepare/applied contexts. Production sends no frame.

`semantic-release.pi-integration-action-authority-resolution.v1` is exactly `{schema,phase,terminal_mode,authorization_request_digest,authorization_envelope_digest,process_start_nonce,authorization_claim_record_digest,authorization_current_record_digest,controller_transcript_digest,controller_transcript_commit_ack_digest,canonical_ledger_store_head_digest,canonical_ledger_acquisition_pin_digest,canonical_ledger_read_receipt_digest,component_owner_control_resolution_digest,component_owner_acquisition_pin_digest,component_owner_approval_read_receipt_digest,host_owner_control_resolution_digest,host_owner_acquisition_pin_digest,host_owner_approval_read_receipt_digest,ak_control_resolution_digest,ak_acquisition_pin_digest,ak_decision_read_receipt_digest,checkpoint_started_monotonic_ns,checkpoint_completed_monotonic_ns,checked_at_utc,action_epoch,verification_outcome,integration_action_authority_resolution_digest}`. Phase is `claim|pre_witness|terminal`; `terminal_mode` is null except terminal `consume|fail`; only `current` authorizes action. At `claim`, claim/current-record/transcript fields are null and the head names the unique available pre-state, so the resolution can be embedded in the later claimed record without a cycle. At `pre_witness`, claim/current reserved records are non-null and transcript is null; the immediate CAS creates the `authorized` record before transport. At `terminal`, claim/current records are non-null. Consume requires transcript and commit-ack after replay, teardown, filesystem recheck, and durable persistence. Fail requires both null, runs immediately after the triggering abort plus exact child kill/reap and available filesystem cleanup evidence, and permits only failed CAS; it never requires or manufactures replay/transcript. Every phase performs fresh canonical reads; validity is half-open. Claim completes immediately before CAS; pre-witness runs while host is paused immediately before authorization transport/extension init; each terminal mode completes immediately before its corresponding CAS. Revocation, expiry equality, stale head/pin/CAS/key/artifact, Decision drift, realtime rollback relative to `CLOCK_BOOTTIME`, or epoch regression fails. Non-current terminal may append only failed; unavailable writer authority leaves a nonterminal claim for the pinned finalizer and never restores available.

The canonical append-only SQLite ledger is outside disposable/sealed/production roots and resolves only through a current host-owner pin/read receipt. A record is exactly `{schema,store_id,canonical_store_locator,store_revision,prior_store_head_digest,authorization_envelope_digest,sequence,prior_record_digest,state,process_start_nonce,host_runtime_manifest_digest,writer_identity,writer_executable_digest,writer_authority_resolution_digest,claim_authority_resolution_digest,pre_witness_authority_resolution_digest,terminal_authority_resolution_digest,claimed_at_utc,claim_boot_id,monotonic_clock_id,monotonic_deadline_ns,execution_instance_digest,execution_generation,boot_nonce,session_instance_nonce,attempt_ordinal,prompt_run_attempt_digest,attempt_reservation_digest,supervised_process_identities,cancellation_digest,cancellation_read_receipt_digest,abandonment_observation_digest,terminal_reason,controller_transcript_digest,authorization_ledger_record_digest}`. Clock is `CLOCK_BOOTTIME`; process rows are sorted `{role,pid,starttime}`. Legal transitions only are `available->claimed`, `available->cancelled`, `claimed->supervised|failed`, `supervised->reserved|failed`, `reserved->authorized|failed`, and `authorized->consumed|failed`; terminal states never reopen. Structural/writer fields, process nonce, and request-equal host runtime manifest digest are non-null in every state; prior-record is null only for available. Exact state table: available has all three action resolutions and claim metadata null, process array empty, cancellation/abandonment/reason/transcript null; claimed adds claim resolution plus claim time/boot/clock/deadline, process empty, all later fields null; supervised carries claimed fields and a nonempty process array, with reservation/pre/terminal/cancellation/abandonment/reason/transcript null; reserved adds the non-null execution/session/attempt tuple and reservation digest with pre/terminal/cancellation/abandonment/reason/transcript null; authorized inherits reservation and adds non-null pre-witness resolution, terminal/cancellation/abandonment/reason/transcript null; reservation tuple fields are null in available, claimed, and supervised; consumed has all three resolutions, inherited metadata/processes, null cancellation/abandonment, reason `completed`, and non-null transcript; failed inherits every reached phase field, has terminal resolution except when unavailable during authenticated abandonment, null cancellation, abandonment non-null exactly for abandonment/reboot/deadline recovery, non-null reason, and transcript non-null exactly when already durable; cancelled has action/claim/process/abandonment/transcript fields null, reason non-null, and cancellation/read fields non-null except conclusive expiry/revocation uses null cancellation plus current writer resolution. Failed reason is `authority_revoked|authorization_expired|checkpoint_stale|controller_failure|host_failure|teardown_failure|deadline_expired|abandoned_claim|host_reboot`; cancelled reason is `owner_cancelled|decision_revoked|authorization_expired` with authenticated cancellation or conclusive current revocation/expiry.

After each record, `semantic-pi-integration-ledger-store-head.v1` is exactly `{schema,store_id,canonical_store_locator,store_revision,record_digest,prior_store_head_digest,ledger_store_head_digest}`. The first available record for an authorization has per-authorization sequence `0`, null prior-record digest, non-null current global prior-store head (or null only for empty-store genesis), and global store revision prior+1; it is appended only after the envelope and both current owner receipts exist. Every exact record key not required by its state is JSON null. `semantic-pi-integration-cancellation.v1` is exactly `{schema,issuer,authorization_envelope_digest,cancellation_reason,issued_at_utc,statement_digest,signing_key_id,signature_algorithm,signature,integration_cancellation_digest}` and uses a current cancellation-purpose key/read receipt. Abandonment process rows are `{role,pid,starttime}`, observed rows add `status:exact_process_alive|pid_absent|starttime_mismatch`, and termination rows add `action:none|pidfd_sigkill,outcome:not_required|signaled_and_absent`. Every append uses `BEGIN IMMEDIATE`, exact prior-head/record/revision CAS, increments sequence/revision, fsyncs record/store/directory, and is reread through the current pin/receipt. Copied, restored, alternate, concurrent, or stale stores reject. Only the request-pinned finalizer executable with fresh host-owner writer authority appends; controller never writes the ledger. It claims before launch, records/fsyncs supervised PID/starttime identities while children are paused, then releases them. Parent death or authority-channel EOF kills children.

`semantic-release.pi-integration-abandonment-observation.v1` is exactly `{schema,authorization_envelope_digest,authorization_claim_record_digest,authorization_current_record_digest,canonical_ledger_store_head_digest,observed_boot_id,observed_at_utc,observed_monotonic_ns,finalizer_identity,finalizer_executable_digest,finalizer_authority_resolution_digest,abandonment_reason,claimed_process_identities,observed_process_identities,termination_actions,all_claimed_processes_absent,all_supervised_processes_terminated,integration_abandonment_observation_digest}`. Recovery requires exact latest claimed/supervised/reserved/authorized chain and one of changed boot, deadline equality/expiry, or absent/different-starttime finalizer/controller. It pidfd-kills only exact live identities, waits, and proves all absent; then only `claimed|supervised|reserved|authorized -> failed`, preserving any authorized pre-witness and reserved tuple fields. Unverifiable/surviving identity or stale authority/head forbids append. Cancellation is only from available and requires a current component/host/Decision authority signature/read receipt or conclusive current expiry/revocation. Recovery never creates acknowledgement, redemption, transcript, proof, cancellation from a claim, or availability.

## Closed integration proof

`semantic-pi-host-integration-proof.v1` exact keys:

```text
schema, issuer, claim_scope, authorization_request_digest,
authorization_envelope_digest, authorization_claim_record_digest,
authorization_terminal_record_digest, claim_authority_resolution_digest,
pre_witness_authority_resolution_digest, terminal_authority_resolution_digest,
terminal_ledger_store_head_digest, canonical_ledger_acquisition_pin_digest,
canonical_ledger_read_receipt_digest, host_runtime_manifest_digest,
loaded_component_manifest_digest, prompt_run_attempt_digest,
host_application_witness_digest, integration_acknowledgement_digest,
host_witness_redemption_digest, replay_probe_digest,
controller_transcript_digest, controller_transcript_commit_ack_digest,
provider_request_dispatched,
publication_authorized, adoption_authorized, activation_authorized,
provider_or_model_use_observed, influence_observed,
production_authorized, integration_proof_digest
```

Issuer equals closed `controller_identity`, claim is `host_integration_only`, and all booleans are false. Provider/model use is derived as transcript dispatch OR model-invocation and prompt application alone is not use. Construction is witness -> acknowledgement -> redemption -> observed replay rejection -> durable transcript -> fresh terminal resolution -> consumed record/head -> current terminal read receipt -> proof. The receipt must name the consumed record/revision/head as current; any failed/cancelled/nonterminal/copied/stale chain rejects. ROCS delivery validation and AK delivery linkage reject this schema. AK may record it only as implementation-validation evidence.
