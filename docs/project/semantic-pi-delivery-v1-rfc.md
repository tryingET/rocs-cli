---
summary: "Converged RFC for pi-ontology-workflows delivery identity, host-resolved application evidence, and a non-authoritative isolated integration proof."
read_when:
  - "Reviewing the Decision 53 successor protocol or Pi host delivery witness."
system4d:
  container: "Cross-repo successor RFC for ROCS, pi-ontology-workflows, and Pi host."
  compass: "Make identity, host observation, owner authorization, and delivery authority independently executable."
  engine: "Content-addressed artifacts -> host application witness -> typed redemption -> owner-current delivery validation or isolated integration proof."
  fog: "Digest cycles, forgeable transcripts, replayed authorization, or fixture authority can create a coherent false claim."
type: "rfc"
status: "in_review"
rfc_revision: "semantic-pi-delivery-v1-r11"
---

# RFC — Semantic Pi delivery receipt v1

## Decision requested

Accept a successor to the Pi-delivery seam of Decision 53 that:

1. preserves v0 history;
2. uses the accepted `pi-extensions` / `pi-ontology-workflows` identity;
3. defines a closed v1 delivery receipt plus host witness, redemption, and attestation-resolution contracts;
4. keeps actual `delivered` validation blocked until the complete unchanged Decision 53 authority graph and a new independently owned host-attestation fact are current;
5. permits one separately authorized, non-authoritative real-host integration proof that cannot validate as semantic delivery.

No code is authorized before a successor ADR and post-ADR execution membrane.

## Inputs

- problem brief and evidence note in this review set;
- immutable r1 and r2 review/synthesis artifacts;
- Decision 53 v0 ADR and packet;
- Pi-owner identity artifact at commit `63d1e9f5c271007b48c45818d1f419a228de1561`;
- AK task `4108`, evidence `5030` and `5031`.

## Goals and non-goals

Goals are exact multi-axis identity, post-application host observation, replay resistance, deterministic independent validation, v0 preservation, default-off behavior, and one supervised integration proof.

Non-goals are provider transmission, model use/influence, semantic publication, consumer adoption/activation, recovery policy, a production consumer/canary, live acquisition, defaults/startup/fleet behavior, or protection after compromise of the exact reviewed host/component/controller artifacts.

## Trust statement

Pi extensions execute in the host process. A public JSON digest is integrity, not issuance authentication. V1 claims:

- live runtime anti-confusion from a host-private opaque witness brand and host-owned one-use redemption map;
- deterministic consistency of persisted witness/redemption/transcript bytes;
- controller-observed execution only when AK evidence binds the exact command/process/output.

V1 does **not** claim that a self-digested persisted transcript alone proves execution. Production `delivered` additionally requires a current `pi.host-attestation-resolution.v1` from an independently pinned host-attestation owner. No such owner/root exists today; no production receipt can validate until separately established. The resolver shape is fixed here so later provisioning cannot change v1 semantics.

## Fixed identities

```json
{
  "governance_owner_role": "pi-owner",
  "repository_identity": {
    "repository_id": "pi-extensions",
    "canonical_source_locator": "git+https://github.com/tryingET/pi-extensions.git",
    "workspace_projection": "local://softwareco/owned/pi-extensions",
    "identity_revision": 1
  },
  "component_identity": {
    "component_id": "pi-ontology-workflows",
    "repository_path": "packages/pi-ontology-workflows",
    "identity_revision": 1
  },
  "protocol_issuer": {
    "kind": "pi_extension_component",
    "id": "pi-ontology-workflows",
    "role": "semantic_pi_delivery_attestor"
  }
}
```

`pi-owner` is governance only. Repository, component, package, host, loaded snapshot, execution instance, and attempt are separate. Any `pi-adapter` value in v1 is `issuer_scope_violation`; no alias or conversion exists.

## Acyclic artifact model

### Package tree

`pi.package-tree-manifest.v1` has exactly:

```text
schema
package_name
package_version
source_commit
npm_pack_tarball_digest
files
package_tree_manifest_digest
```

`files` is the complete safely extracted tarball inventory of `{path,mode,byte_length,content_digest}`, UTF-8 path sorted and unique. The manifest does not embed its own identity elsewhere. `package_artifact_identity` is exactly:

```text
package_name
package_version
npm_pack_tarball_digest
package_tree_manifest_digest
```

### Dependency tree

Every runtime dependency is a separate `pi.package-tree-manifest.v1`. Dependency rows in the loaded manifest are exactly `{package_name,package_version,package_tree_manifest_digest}`. The full transitive dependency closure is present once, UTF-8 sorted by `(package_name, package_version, digest)`, with no cycles or undeclared imports.

### Loaded component

`pi.loaded-extension-component-manifest.v1` has exactly:

```text
schema
repository_identity
component_identity
package_artifact_identity
entry_logical_path
entry_content_digest
dependency_manifests
loaded_component_manifest_digest
```

It references but does not contain the package-tree body, preventing digest recursion. Resolver equality binds package identity to the resolved package-tree manifest and tarball.

### Host runtime

`pi.host-runtime-manifest.v1` has exactly:

```text
schema
host_package
host_version
extension_api_version
runtime_kind
standalone_host_executable_digest
standalone_runtime_closure_digest
embedded_builtin_module_allowlist
loader_configuration_digest
argv_contract_digest
host_runtime_manifest_digest
```

`runtime_kind=bun_standalone_binary`. `pi.standalone-host-runtime-closure.v1` is exactly `{schema,standalone_host_executable_digest,elf_interpreter,shared_libraries,expected_load_segments,runtime_data_tree,closure_probe_tool_digest,namespace_tool_digest,mount_contract_digest,staged_root_logical_id,standalone_runtime_closure_digest}`. Interpreter is null or `{logical_path,content_digest}`; shared libraries are UTF-8-SONAME-sorted unique `{soname,logical_path,content_digest}`; interpreter/library content uses `pi.host-runtime-library-bytes.v1`; runtime data tree is `pi.host-runtime-data-tree-manifest.v1`; the probe tool uses `pi.controller-executable-bytes.v1`. `pi.host-runtime-data-tree-manifest.v1` is exactly `{schema,entries,runtime_data_tree_manifest_digest}` with UTF-8 `(path,kind)`-sorted `{path,kind,mode,byte_length,content_digest}` rows; directories have null length/digest and files use `pi.host-runtime-data-file-bytes.v1`.

Witness-capable mode is restricted to the binary produced by the reviewed `build:binary` path whose independently run ELF/interpreter/shared-library probe exactly equals the closure. A non-ELF binary requires null interpreter and empty libraries. Unlisted runtime loading fails. Source/Jiti host startup, npm Node entrypoints, inline factories, mutable paths, and host dynamic loading outside the executable/closure are ineligible. Exact artifact hashes, not build reproducibility, are pinned. Extension loading remains manifest-confined; dynamic/computed extension imports are forbidden.

`pi.native-loader-mount-contract.v1` is exactly `{schema,staged_root_logical_id,executable_path,interpreter_path,library_paths,runtime_data_root,bwrap_argv,network_unshared,ambient_root_visible}`. Constants are executable `/host/pi`, runtime data `/host/runtime-data`, `network_unshared=true`, and `ambient_root_visible=false`; paths are absolute inside the staged root. The namespace launcher is a reviewed statically linked helper implementing the required user/mount/pid/network namespace, bind operations, and inherited barrier socket directly; its ELF has no `PT_INTERP` and no `DT_NEEDED`, verified by the pinned probe before execution. Dynamic `bwrap` is ineligible. The content-addressed helper applies the exact `bwrap_argv`-equivalent contract: unshare all namespaces, read-only bind only the staged root as `/`, create fresh `/proc` and minimal `/dev`, and expose no host filesystem.

Before launch, the controller parses ELF `PT_INTERP` and dependency resolution using the pinned probe and requires exact closure equality. The launcher creates a private inherited `SOCK_SEQPACKET` socketpair whose controller endpoint identity is bound by `{process_start_nonce,device,inode}`; no descriptor number is authority. Host core starts in `witness_bootstrap_paused`, before extension discovery/import, sends a closed `pi.runtime-barrier-message.v1` `ready` message, and blocks. The controller verifies nonce/channel, records the `pre_extension_load` maps observation, then sends the matching `continue`. Before redemption, host sends/blocks on the same sequence for `pre_redemption`. Each message is exactly `{schema,phase,sequence,process_start_nonce,prompt_run_attempt_digest,action,barrier_message_digest}`; first attempt digest is null, second non-null; sequence is 1 then 2. Timeout, EOF, extra/reordered message, wrong nonce/channel, or failed map read kills/reaps the host and yields no witness/redemption.

`pi.runtime-load-observation.v1` is exactly `{schema,phase,process_start_nonce,mappings,runtime_load_observation_digest}`. Mappings are UTF-8 sorted/unique by `(device,inode,file_offset,mapped_length,permissions,logical_path)` and exactly `{device,inode,file_offset,mapped_length,permissions,logical_path,content_digest}`; permissions match `^[r-][w-][x-][ps]$`. The closure's `expected_load_segments` uses the same tuple minus device/inode and is derived from ELF program headers. Observations must equal expected file/offset/length/permission segments modulo device/inode, forbid writable+executable segments, require executable mappings for host/interpreter/libraries, and reject every unlisted file-backed executable mapping. Runtime-data root placement and every sidecar lookup are bound to `/host/runtime-data` in the mount contract. Non-Linux or unavailable namespace/maps enforcement is ineligible, not a weaker posture.

The controller stages snapshots read-only. The host verifies all bytes before load, immediately before prompt execution, before redemption, and during final prompt readback. Any path/inode/mode/content drift aborts before redemption and provider dispatch.

## Normative JSON profile

Input is bounded strict UTF-8 JSON with no BOM/trailing data and duplicate-key rejection before object construction. Legal number tokens are only `0|[1-9][0-9]*`, range `0..9007199254740991`; booleans are never integers. Reject negative/decimal/exponent/NaN/Infinity, lone surrogates, Unicode noncharacters, and non-NFC strings. Depth is at most 64.

Canonical bytes are RFC 8785 JCS under that integer-only I-JSON profile. Object keys sort by UTF-16 code units; arrays retain normative order. Equality is type-exact.

JSON object digests are:

```text
sha256(ASCII(domain) || 0x00 || JCS(object without exactly its top-level self-digest field))
```

Raw byte digests are:

```text
sha256(ASCII(domain) || 0x00 || exact_bytes)
```

Every digest is `sha256:` plus 64 lowercase hex characters.

## Complete digest registry

| Object/value | Domain | Omitted field/preimage |
|---|---|---|
| delivery receipt | `semantic-release.pi-delivery.v1` | `pi_delivery_receipt_digest` |
| delivery error | `semantic-release.pi-delivery-error.v1` | `error_digest` |
| host prompt-application error | `pi.host-prompt-application-error.v1` | `host_error_digest` |
| package tarball bytes | `pi.package-tarball-bytes.v1` | exact bytes |
| package/source file bytes | `pi.package-file-bytes.v1` | exact bytes |
| package tree | `pi.package-tree-manifest.v1` | `package_tree_manifest_digest` |
| loaded component | `pi.loaded-extension-component-manifest.v1` | `loaded_component_manifest_digest` |
| standalone host executable bytes | `pi.standalone-host-executable-bytes.v1` | exact bytes |
| host runtime-data file bytes | `pi.host-runtime-data-file-bytes.v1` | exact bytes |
| host runtime-data tree | `pi.host-runtime-data-tree-manifest.v1` | `runtime_data_tree_manifest_digest` |
| standalone runtime closure | `pi.standalone-host-runtime-closure.v1` | `standalone_runtime_closure_digest` |
| native loader mount contract | `pi.native-loader-mount-contract.v1` | full closed object |
| runtime load observation | `pi.runtime-load-observation.v1` | `runtime_load_observation_digest` |
| runtime barrier message | `pi.runtime-barrier-message.v1` | `barrier_message_digest` |
| namespace tool bytes | `pi.namespace-tool-bytes.v1` | exact bytes |
| runtime interpreter/library bytes | `pi.host-runtime-library-bytes.v1` | exact bytes |
| host file bytes | `pi.host-file-bytes.v1` | exact bytes |
| loader configuration | `pi.loader-configuration.v1` | full closed object |
| argv contract | `pi.argv-contract.v1` | full closed object |
| host runtime | `pi.host-runtime-manifest.v1` | `host_runtime_manifest_digest` |
| execution instance | `pi.execution-instance.v1` | full closed preimage below |
| prompt-run attempt | `pi.prompt-run-attempt.v1` | full closed preimage below |
| prompt input bytes | `pi.prompt-input.v1` | exact UTF-8 bytes |
| prompt returned bytes | `pi.prompt-returned.v1` | exact UTF-8 bytes |
| final prompt bytes | `pi.prompt-final-chain.v1` | exact UTF-8 bytes |
| applied entry | `pi.prompt-applied-entry.v1` | closed `{handler_registration_index, returned_prompt_digest}` |
| witness | `pi.prompt-system-application-witness.v1` | `host_application_witness_digest` |
| integration acknowledgement | `pi.host-integration-acknowledgement.v1` | `integration_acknowledgement_digest` |
| redemption | `pi.prompt-system-witness-redemption.v1` | `host_witness_redemption_digest` |
| replay probe | `pi.prompt-system-witness-replay-probe.v1` | `replay_probe_digest` |
| integration controller transcript | `pi.host-integration-controller-transcript.v1` | `controller_transcript_digest` |
| delivery execution transcript | `pi.host-delivery-execution-transcript.v1` | `delivery_execution_transcript_digest` |
| host attestation | `pi.host-attestation-resolution.v1` | `host_attestation_resolution_digest` |
| authorization request | `semantic-release.pi-integration-authorization-request.v1` | `authorization_request_digest` |
| owner approval | `semantic-release.pi-integration-owner-approval.v1` | `owner_approval_digest` |
| authorization envelope | `semantic-release.pi-integration-authorization-envelope.v1` | `authorization_envelope_digest` |
| ledger record | `semantic-release.pi-integration-authorization-ledger-record.v1` | `authorization_ledger_record_digest` |
| integration proof | `semantic-release.pi-host-integration-proof.v1` | `integration_proof_digest` |
| packet aggregate rows | `semantic-release.pi-delivery-packet-aggregate.v1` | exact row bytes |
| packet manifest | `semantic-release.pi-delivery-packet-manifest.v1` | `packet_manifest_digest` |
| controller executable bytes | `pi.controller-executable-bytes.v1` | exact bytes |
| process environment contract | `pi.process-environment-contract.v1` | full closed object |
| filesystem manifest | `pi.filesystem-manifest.v1` | full closed object |
| TypeScript config bytes | `pi.tsconfig-bytes.v1` | exact bytes |
| logical realpath identity | `pi.logical-realpath-identity.v1` | closed `{logical_id,normalized_device_id,normalized_inode_id}` |
| filesystem tree | `pi.filesystem-tree-manifest.v1` | closed sorted tree rows |
| witness lexical bytes | `pi.witness-json-bytes.v1` | exact JCS bytes |
| acknowledgement lexical bytes | `pi.acknowledgement-json-bytes.v1` | exact JCS bytes |
| redemption lexical bytes | `pi.redemption-json-bytes.v1` | exact JCS bytes |
| replay-probe lexical bytes | `pi.replay-probe-json-bytes.v1` | exact JCS bytes |
| delivery-receipt lexical bytes | `pi.delivery-receipt-json-bytes.v1` | exact JCS bytes |
| filesystem file bytes | `pi.filesystem-file-bytes.v1` | exact bytes |
| stdout bytes | `pi.process-stdout-bytes.v1` | exact bytes |
| stderr bytes | `pi.process-stderr-bytes.v1` | exact bytes |
| pre-redemption journal | `pi.prompt-system-pre-redemption-journal.v1` | `pre_redemption_journal_digest` |
| ledger store head | `semantic-release.pi-integration-ledger-store-head.v1` | `ledger_store_head_digest` |
| ledger record bytes | `semantic-release.pi-integration-ledger-record-bytes.v1` | exact JCS bytes |

`loaded_entry_digest` is exactly the resolved package-tree entry's `content_digest` under `pi.package-file-bytes.v1`; no second entry-digest algorithm exists. Store-head, transcript-byte, configuration, and nested digest fields must use the corresponding row above. Unknown domains reject.

## Closed configuration preimages

`pi.loader-configuration.v1` is exactly `{schema,loader_kind,loader_version,tsconfig_digest,import_map,allowed_root_manifest_digests,node_builtin_allowlist,dynamic_import_policy,module_cache_mode,outside_imports_forbidden,native_addons_forbidden}`. `loader_kind=jiti`; `tsconfig_digest` is `pi.tsconfig-bytes.v1`; import-map rows are `{specifier,target_logical_path,target_manifest_digest}`, UTF-8 specifier sorted/unique; each target digest resolves a package-tree manifest. Allowed roots and Node built-ins are sorted/unique. Built-ins are bound to `embedded_builtin_module_allowlist` in the standalone host manifest; only literal specifiers in that allow-list are legal. Dynamic/computed import or require is `forbidden`; cache mode is `per_execution_generation`; `outside_imports_forbidden=true`; `native_addons_forbidden=true` for v1.

`pi.process-environment-contract.v1` is exactly `{schema,inherit_environment,entries,unset_keys,locale,timezone,network_mode}`. Inheritance is false. The only permitted entry keys are exactly the used subset of `HOME,LANG,LC_ALL,PATH,PI_CODING_AGENT_DIR,TMPDIR,TZ`, UTF-8-key-sorted unique `{key,value}` rows; every omitted key is present in the sorted/unique `unset_keys`, and the sets partition that closed allow-list. Locale is `C.UTF-8`, timezone `UTC`, and network mode `forbidden`.

`pi.argv-contract.v1` is exactly `{schema,standalone_host_executable_digest,argv,cwd_logical_id,process_environment_contract_digest,shell}`. `argv` preserves order, `shell=false`, and cwd resolves inside the staged host snapshot.

`pi.filesystem-tree-manifest.v1` is exactly `{schema,root_logical_id,entries}` where entries are UTF-8 sorted by `(path,kind)` and exactly `{path,kind,mode,byte_length,content_digest}`. Kinds are `directory|file`; directories have null length/digest; files use `pi.filesystem-file-bytes.v1`. `pi.filesystem-manifest.v1` is exactly `{schema,roots,process_ids,network_connections}`. Roots are UTF-8-logical-id-sorted unique `{logical_id,realpath_digest,tree_manifest_digest,mutability}` rows; mutability is `read_only|disposable_write|canonical_ledger`. Process IDs are sorted safe integers. Network connections is empty. Real paths never enter a preimage directly.

## Execution and attempt identity

`execution_instance_digest` preimage is exactly:

```text
{host_runtime_manifest_digest, boot_nonce, extension_api_version}
```

`boot_nonce` is 32 random bytes encoded as 64 lowercase hex characters and appears in the controller transcript and host attestation.

`prompt_run_attempt_digest` preimage is exactly:

```text
{execution_instance_digest, execution_generation, attempt_ordinal,
 session_instance_nonce}
```

Session nonce has the same 32-byte encoding and appears in witness/transcript/attestation. Generation and ordinal are safe integers, start at `0`, increment before use, and fail closed permanently at maximum rather than wrap.

`handler_registration_index` is zero-based in one total registration order shared by ordinary `before_agent_start` handlers and prompt-system contributors. Order is extension load order, then registration call order within each extension. The contributor must be the last registration in that total order; any later ordinary handler or contributor makes witnessing ineligible regardless of whether it returns only a message. The host adds one paired API: `pi.registerPromptSystemContributor({prepare,applied})`. `prepare(prepareContext)` receives read-only host/runtime/component/attempt identity plus signal/deadline and no mutating host methods. It returns exactly one discriminated result:

- `{kind:terminal_receipt,receipt}` where receipt is only the complete suppressed or failed v1 branch. Host validates it, records it in the prompt result, keeps the input prompt unchanged, issues no witness, and never calls `applied`.
- `{kind:contribution,systemPrompt,application_witness_request}` where the request is `{repository_identity,component_identity,rocs_generation_receipt_digest}` and `systemPrompt` differs bytewise from input.

Thus suppressed/failed transport is pre-witness and their mandatory host/attempt fields come from `prepareContext`. A contributor may return a failed receipt for an error it observed. If `prepare` throws, times out, is aborted without returning, or returns malformed data, the host aborts this direct prompt before provider dispatch and emits only a host-local diagnostic; it does not continue as current ordinary-handler error handling does and cannot forge a component-issued receipt. The host validates the request after return; attempt identity remains non-retroactive because it excludes generation digest. The contributor must be the sole requester and final effective handler; any later handler/change aborts before assignment.

After assignment/readback, the host enters a host-wide prompt-application critical section and invokes the same registration's personalized `applied({witness},restrictedContext)` callback exactly once. `restrictedContext` contains only read-only host identity, `AbortSignal`, and deadline; it exposes no model, session, UI, message, prompt, command, or provider method. The host guard also rejects recursive `prompt`, `continue`, `_runAgentPrompt`, `sendUserMessage`, `sendCustomMessage({triggerTurn:true})`, host-owned model completion, or provider dispatch attempted through retained closures until redemption and transcript persistence finish. Any attempt aborts.

The callback resolves within 500 ms and returns exactly `{subject_kind,subject}` where kind is `semantic_delivered_receipt|host_integration_acknowledgement`; the first subject is a complete `semantic-pi-delivery-receipt.v1` delivered branch with `delivery_outcome=delivered`, the second the closed acknowledgement. Suppressed/failed receipts are produced only before witness request/issuance and never enter journal, redemption, transcript, or attestation. Timeout, throw, stale context, wrong brand/index, missing subject, or reentry aborts. No broadcast/unrelated extension receives the witness.

## Closed delivery receipt union

Every branch has `additionalProperties=false` and the common exact keys:

```text
schema
governance_owner_role
issuer
repository_identity
component_identity
package_artifact_identity
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
```

Host capabilities are exactly UTF-8 sorted/unique and include `prompt.system.application-witness.v1`. Consumer/scope are copied only from the resolved generation receipt and imply no owner existence, naming, consent, adoption, or activation.

- **Delivered** adds exactly `delivered_effective_execution_digest` and `applied_prompt_chain_entry_digest`; outcome is `delivered`, claim is `delivered_to_pi_prompt_chain_only`, witness digest is non-null, and execution/application fields equal the resolved generation and witness.
- **Suppressed** adds exactly `suppression_reason`; outcome is `suppressed`, claim is `delivery_suppressed_only`, witness digest is null, and reason is `cancelled|stale_result|policy|duplicate_attempt`. It contains no delivered/error field.
- **Failed** adds exactly `error_digest`; outcome is `failed`, claim is `delivery_failed_only`, witness digest is null. It contains no delivered/suppression field. Deadline equality fails.

A host without the v1 capability or host identity emits no v1 receipt; the component exposes only a local non-protocol diagnostic. Thus all receipt branches can truthfully carry the mandatory host identity fields.

`semantic-pi-delivery-error.v1` is component-owned and exactly `{schema,stage,code,related_artifact_digest,details,error_digest}`. Stage is the constant `prepare`; code is `component_failure|dependency_unavailable|generation_stale|policy_failure`; related digest is nullable; details are UTF-8-key-sorted unique `{key,value}` rows. A failed receipt's `error_digest` resolves exactly this object. Host-observed timeout, abort-without-return, malformed result, stale context, apply/redeem/postcondition failure use separate host-local `pi.host-prompt-application-error.v1={schema,stage,code,related_artifact_digest,details,host_error_digest}` under domain `pi.host-prompt-application-error.v1`; they never appear in a component receipt.

## Closed host objects

### Application witness

Exact keys:

```text
schema, issuer, host_runtime_manifest_digest, repository_identity,
component_identity, package_artifact_identity, loaded_component_manifest_digest,
loaded_entry_digest, execution_instance_digest, boot_nonce,
execution_generation, prompt_run_attempt_digest, attempt_ordinal,
session_instance_nonce, handler_registration_index,
rocs_generation_receipt_digest, input_prompt_digest,
returned_prompt_digest, final_prompt_chain_digest,
applied_prompt_chain_entry_digest, application_outcome,
application_target, observation_phase, host_application_witness_digest
```

Constants: issuer `{kind:pi_host,id:@earendil-works/pi-coding-agent}`, outcome `applied`, target `agent.state.systemPrompt`, phase `post_application`.

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
schema, issuer, claim_scope, authorization_envelope_digest,
host_application_witness_digest, prompt_run_attempt_digest,
integration_acknowledgement_digest
```

Issuer is the component identity; claim is `host_integration_acknowledgement_only`. It is not a delivery receipt.

### Replay probe

Exact keys:

```text
schema, issuer, host_application_witness_digest,
host_witness_redemption_digest, repeated_subject_kind,
repeated_subject_digest, probe_outcome, replay_probe_digest
```

Host issuer is fixed and outcome is `rejected_already_redeemed`. No second redemption exists.

### Integration controller transcript

`pi.host-integration-controller-transcript.v1` has exactly:

```text
schema, controller_executable_digest, host_runtime_manifest_digest,
runtime_load_observation_digests, component_package_tree_manifest_digest, dependency_manifest_digests,
process_environment_contract_digest, argv_contract_digest, process_start_nonce,
boot_nonce, session_instance_nonce, authorization_envelope_digest,
authorization_claim_record_digest, witness_bytes_digest,
acknowledgement_bytes_digest, redemption_bytes_digest,
replay_probe_bytes_digest, stdout_digest, stderr_digest, exit_code,
provider_request_dispatched, filesystem_before_digest,
filesystem_after_digest, process_teardown_complete,
controller_transcript_digest
```

It is integration-only: authorization/acknowledgement/replay fields are non-null, `provider_request_dispatched=false`, and teardown is true.

`pi.host-delivery-execution-transcript.v1` is a separate production shape with exactly:

```text
schema, host_runtime_manifest_digest, runtime_load_observation_digests,
loaded_component_manifest_digest, execution_instance_digest, boot_nonce, session_instance_nonce,
prompt_run_attempt_digest, rocs_generation_receipt_digest,
host_application_witness_digest, delivery_receipt_bytes_digest,
pre_redemption_journal_digest, host_witness_redemption_digest,
final_prompt_chain_digest, final_readback_digest,
filesystem_manifest_digest, provider_dispatch_posture,
delivery_execution_transcript_digest
```

It contains no integration authorization, acknowledgement, replay-probe, exit, or teardown fields. In both transcript schemas, `runtime_load_observation_digests` is an exact two-item array ordered `[pre_extension_load,pre_redemption]`; both observations share the process nonce and independently resolve all mapping bytes/permissions. `provider_dispatch_posture` is the constant `not_dispatched_at_record`; the transcript is persisted before any dispatch. Later dispatch is outside the transcript and delivery claim. One transcript exists per prompt-run attempt, regardless of later provider retries/continuations. Both transcript types prove deterministic consistency only unless resolved by owner evidence.

### Host attestation resolution

Exact keys:

```text
schema, issuer, owner_repository, attestation_root_id,
attestation_root_revision, attestation_root_digest,
revocation_head_digest, host_runtime_manifest_digest,
runtime_load_observation_digests, execution_instance_digest, boot_nonce, session_instance_nonce,
prompt_run_attempt_digest, host_application_witness_digest,
host_witness_redemption_digest, delivery_execution_transcript_digest,
action_epoch, currentness_cas_digest, verification_outcome,
host_attestation_resolution_digest
```

Issuer kind is `independent_host_attestation_verifier`; outcome is `valid`. The v1 resolver requires owner-specific acquisition pin, owner-store read receipt, trust root/current revocation, action-time epoch, and exact joins. No root is provisioned by this RFC.

## Host event and replay machine

Order:

```text
allocate attempt
-> chain before_agent_start while recording per-handler input/return
-> if prepare returned terminal receipt, validate/record it with unchanged prompt and skip the remaining witness machine
-> otherwise assign final prompt
-> readback/hash
-> issue opaque personalized witness
-> receive semantic delivery receipt or integration acknowledgement
-> validate candidate shape/digest
-> reverify staged artifacts
-> final readback/hash agent.state.systemPrompt
-> persist and fsync a pre-redemption journal bound to those final checks
-> atomically redeem once
-> persist the delivery execution transcript for a semantic delivery receipt
-> if exact host postconditions persist, optionally construct/dispatch this run's provider request
-> for integration mode, run the replay probe, terminate/reap the host, then persist the integration controller transcript
```

Any acknowledgement, validation, snapshot, final-readback, pre-redemption persistence, redemption, or delivery-transcript persistence failure aborts before provider dispatch and restores the pre-contribution prompt. Integration mode never dispatches and treats replay, teardown, or integration-transcript persistence failure as terminal proof failure. No redemption is issued before every artifact and prompt postcondition succeeds. A redemption without its matching persisted integration or delivery transcript is unresolved; delivered validation additionally requires host attestation. Provider dispatch depends only on the host's already completed application/snapshot/readback postconditions, never on later offline attestation. Integration proof sets `provider_request_dispatched=false` and terminates after replay probe.

`pi.prompt-system-pre-redemption-journal.v1` has exactly `{schema,execution_instance_digest,prompt_run_attempt_digest,host_application_witness_digest,subject_kind,subject_digest,loaded_component_manifest_digest,final_prompt_chain_digest,final_readback_digest,filesystem_manifest_digest,state,pre_redemption_journal_digest}`. `final_readback_digest` uses `pi.prompt-final-chain.v1` over the exact UTF-8 readback bytes and must equal `final_prompt_chain_digest`. State is `verified_pending_redemption`. It is written and fsynced before redemption. Recovery never manufactures redemption: a journal without a redemption is terminal failed; a redemption without the exact journal plus transcript is unresolved and cannot validate delivery.

State is `allocated -> chained -> applied -> witness_issued -> redeemed`, with failure terminal. Every await rechecks instance/generation/attempt. Reload/new/resume/fork/replacement/shutdown invalidates nonterminal state. Redeemed/invalidated tuples remain in a non-evicting set capped at 4096 for the generation; reaching cap fails closed and requires a new generation. Restart changes execution instance. Production durable replay requires the attestation owner and remains unprovisioned.

## Acyclic isolated authorization and canonical one-shot ledger

The integration controller is a bounded internal component of the real Pi host owner surface, not a new repository product:

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

A separately reviewed Pi-host owner artifact must accept this identity before implementation. The controller remains internal and adds no public command or product surface.

Construction order uses these exhaustive closed schemas:

1. `semantic-pi-integration-authorization-request.v1` is exactly `{schema,authorization_id,decision_id,rocs_packet_manifest_digest,component_commit,package_artifact_identity,loaded_component_manifest_digest,host_commit,host_runtime_manifest_digest,controller_commit,controller_executable_digest,process_start_nonce,not_before_utc,not_after_utc,max_monotonic_duration_ns,disposable_roots,max_witness_issuances,max_redemptions,max_replay_probes,live_acquisition_implemented,production_authorized,authorization_request_digest}`. Cardinalities are `1`; booleans false; roots are sorted, unique, realpath-disjoint from production/runtime/canonical-ledger roots.
2. Each `semantic-pi-integration-owner-approval.v1` is exactly `{schema,issuer,owner_repository,owner_artifact_revision,accepted_owner_artifact_digest,owner_store_id,owner_store_revision,owner_store_head_digest,revocation_head_digest,authorization_request_digest,valid_not_before_utc,valid_not_after_utc,owner_approval_digest}`. Issuers are exactly component owner and host owner, one each, with current accepted unsuperseded artifacts and store receipts.
3. `semantic-pi-integration-authorization-envelope.v1` is exactly `{schema,authorization_request_digest,component_owner_approval_digest,host_owner_approval_digest,ak_decision_reference_digest,issued_at_utc,authorization_envelope_digest}`. The AK reference resolves Decision 71 as accepted, unsuperseded, unrevoked, and current. No object refers forward, so no digest cycle exists.

The canonical append-only SQLite ledger outside disposable/production/runtime roots is the one-shot source. Its location is resolved only through a host-owner acquisition pin and current owner-store read receipt; caller paths and copied databases are never authority.

A ledger record is exactly `{schema,store_id,canonical_store_locator,store_revision,prior_store_head_digest,authorization_envelope_digest,sequence,prior_record_digest,state,process_start_nonce,controller_identity,controller_executable_digest,claimed_at_utc,monotonic_deadline_ns,terminal_reason,controller_transcript_digest,authorization_ledger_record_digest}`. It never contains its resulting head. Per-state rules are: `available` has null claim/time/deadline/reason/transcript; `claimed` has non-null nonce/controller/time/deadline and null reason/transcript; `consumed` has non-null transcript and reason `completed`; `failed` has non-empty terminal reason and nullable transcript. Sequence and store revision increment by one.

`semantic-pi-integration-ledger-store-head.v1` is exactly `{schema,store_id,canonical_store_locator,store_revision,record_digest,prior_store_head_digest,ledger_store_head_digest}`. It is constructed only after the record digest, so there is no recursion. Claim uses `BEGIN IMMEDIATE`, exact current owner-store head/revision, expected prior record/state, unique authorization digest, same-filesystem durable CAS, and fsync before process launch. The resulting head is re-read through the host-owner store receipt. Concurrent/duplicate claim, alternate store, stale/restored head, or copied database fails. Crash after claim becomes terminal `failed`; recovery never restores available. Terminal current head is externally anchored by the host-owner acquisition pin/receipt. UTC is checked once; realtime rollback relative to monotonic progression fails. The private inherited handle derives from the claimed canonical record and is not authority itself.

## Closed integration proof

`semantic-pi-host-integration-proof.v1` exact keys:

```text
schema, issuer, claim_scope, authorization_envelope_digest,
authorization_claim_record_digest, authorization_terminal_record_digest,
host_runtime_manifest_digest, loaded_component_manifest_digest,
prompt_run_attempt_digest, host_application_witness_digest,
integration_acknowledgement_digest, host_witness_redemption_digest,
replay_probe_digest, controller_transcript_digest,
provider_request_dispatched, publication_authorized,
adoption_authorized, activation_authorized, use_observed,
influence_observed, production_authorized, integration_proof_digest
```

Issuer is the controller, claim `host_integration_only`; all booleans are false. Construction is witness -> acknowledgement -> redemption -> replay probe -> transcript -> terminal ledger record -> proof. ROCS delivery validation and AK delivery linkage reject this schema. AK may record it only as implementation-validation evidence.

## Delivery authority overlay

V0 artifacts and runtime remain unchanged. V1 adds `ak_optional_pi_v1`, a generated rule whose role/edge set is mechanically derived from v0 `ak_optional_pi` by replacing only the Pi receipt role with v1 receipt + witness + redemption + host-attestation roles. The generator proves every other role, category, owner, repository, acquisition contract, edge, parameter, error precedence, and currentness predicate is byte-equal to v0.

The exact v1 resolver context is `{v0_authority_verifier_input,v0_authority_proof_bundle,resolved_generation,v1_receipt_or_null,loaded_component_manifest,host_runtime_manifest,runtime_load_observation_or_null,witness_or_null,pre_redemption_journal_or_null,redemption_or_null,delivery_execution_transcript_or_null,host_attestation_resolution_or_null,canonical_task_states}` with every nullable role explicitly present. Null receipt requires all v1 evidence roles null and yields generation-only linkage; non-null delivered requires every evidence role non-null. Suppressed/failed require witness/journal/redemption/transcript/attestation null.

Validation sequence:

1. strict decode/schema and all recursive/derived digests;
2. v0 universal authority preflight plus generation/activation rule over the complete unchanged graph;
3. v1 package/host/attempt/witness/journal/redemption/delivery-transcript preflight;
4. host-attestation owner pin/read/trust/currentness validation;
5. exact overlay role/edge closure and delivered relation;
6. `ak_optional_pi_v1`, identical to v0 AK linkage except the resolved v1 evidence roles.

Complete precedence is `malformed_input -> unsupported_protocol -> resource_exhausted -> deadline_exceeded -> digest_mismatch -> issuer_scope_violation -> self_certification -> trust_reference_stale|trust_revoked -> activation_not_current -> authorization_or_replay_failure -> delivery_relation_failure`. If deadline equality is already observed at a guard, `deadline_exceeded` wins over later resource detection; otherwise earlier decode/schema/resource failures retain order. V0 historical commands accept v0; successor entrypoints reject v0. Schema-checked v0 objects never substitute for the v0 authority verifier.

## Packet and deterministic implementation limits

Preserve `docs/project/semantic-release-v0/**` byte-for-byte. `docs/project/semantic-pi-delivery-v1/` contains only `packet-manifest.json` plus every file listed by it, including schemas, invariants, registries, generator, independent validators, vectors, and fixtures. Any unlisted/missing regular file rejects. Manifest excludes itself and lists UTF-8-sorted `{path,byte_length,sha256}` rows; aggregate row bytes are `path<TAB>byte_length<TAB>sha256<LF>` under the registered aggregate domain. Manifest self-digest omits only its self field.

Limits and the single monotonic deadline start before the first packet/archive/executable/ledger read and end only after process reap, filesystem recheck, transcript/ledger terminal persistence, and receipt/proof validation. They include packet files, compressed/extracted archives, standalone host/controller executable bytes, stdout/stderr, disposable outputs, pre-redemption journals, and all ledger reads/growth:

- 16 MiB per JSON file, 64 MiB packet aggregate, 32 packet files;
- 64 MiB compressed tarballs cumulative;
- 512 MiB extracted component + all dependencies + host cumulative;
- 4096 total extracted files, 128 dependencies, 4096-byte logical paths;
- JSON depth 64, arrays at most 100,000 unless lower field cap;
- one 60,000 ms monotonic deadline; equality expires;
- retained-byte accounting once per object; no reopen;
- stable no-follow regular-file reads, descriptor/path identity/metadata checks;
- NFC root-local POSIX paths; no traversal, backslash, network form, symlink, hard link, special file, normalization/casefold collision;
- extraction ratio at most 32:1 per archive and cumulatively;
- standalone host + runtime-data + controller executable/manifests at most 128 MiB cumulative;
- stdout and stderr at most 1 MiB each; disposable output at most 64 MiB;
- pre-redemption journal at most 1 MiB; canonical ledger at most 64 MiB and 100,000 records, with the current operation accounting every read/new byte.

Error codes and precedence are generated and independently tested. Resource failure is `resource_exhausted` unless deadline equality/expiry occurred first, which is `deadline_exceeded`; earlier malformed/digest/issuer failures retain precedence.

The generator imports neither validator. Python and Node validators share no code/parser/digest helper. Raw vectors cover every JSON/digest rule and boundary.

Existing v0 embedding remains. The sole v1 embedding source is `docs/project/semantic-pi-delivery-v1/protocol.schema.json`, draft 2020-12, `$id=https://ai-society.local/rocs/semantic-pi-delivery-v1/protocol.schema.json`, whose top-level `oneOf` inventory is UTF-8 schema-name sorted and closed by the packet registry. Target is `src/rocs_cli/semantic_pi_delivery_v1_schema.py`. The generated template contains imports, `SCHEMA_SHA256`, `SCHEMA_BYTE_LENGTH`, one `_SCHEMA_B64` tuple, and `schema_bytes()` integrity checks. Standard base64 is split into 76-character non-final lines and one final line of 1..76 characters, with LF endings and exactly one trailing LF. `python docs/project/semantic-pi-delivery-v1/generate.py --write-embedding|--check-embedding` owns generation; two fresh-checkout runs must match exactly.

## Public surface and cross-repo sequence

V1 adds no user-facing tool, command, prompt, flag, default, startup hook, or general package export. Reconcile the package vision, foundation, stable-core ADR, and accepted identity artifact before code.

After ADR:

1. ROCS packet/validators/overlay/embedding;
2. Pi host ADR and content-addressed host API implementation;
3. component v1 validation, v0 rejection, and constructor-authority removal;
4. owner request/approvals/envelope and one-shot ledger task;
5. supervised real Pi integration proof plus rejected replay probe;
6. no delivered receipt until later owner facts and host-attestation root are provisioned and reviewed.

## Stop and rollback matrix

Stop before provider/live mutation on owner/AK currentness drift, duplicate claim, clock rollback, root overlap after realpath, artifact/version skew, post-witness prompt drift, persistence failure, resource/deadline failure, surviving process, or teardown mismatch.

Rollback is owner-specific:

- ROCS: revert v1-only modules/packet entrypoint; preserve v0 history and keep successor delivery disabled.
- Pi host: remove witness event only after component v1 path is disabled; preserve receipts/transcripts.
- component: disable v1 integration path without re-enabling v0 receipt acceptance or constructor authority.
- ledger: never delete history; mark outstanding claim failed and reject reuse.

No rollback restores `pi-adapter`, v0 successor acceptance, test flags, or a false delivered claim.

## Live boundary

This decision may authorize implementation and one isolated host-integration D2E after post-ADR tasks and joint one-shot authorization. It does not authorize a v1 `delivered` receipt, production semantic-release D2E, publication, adoption, activation, or recovery. Those require the missing consumer/consent/canary/recovery facts, live acquisition, and an independently owned host-attestation root/current receipt.

## Open questions

None. Missing production owner/root instances are explicit future gate facts, not protocol-shape questions.

## Requested review outcome

Run a fresh exact-byte five-lane review. Only complete synthesis with zero material findings and `ready_for_adr` permits ADR drafting.
