---
summary: "Normative runtime, artifact, registrar, and receipt preimage contracts for semantic Pi delivery v1 r16."
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

# Runtime contracts — semantic Pi delivery v1 r16

## Host runtime

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

`pi.native-loader-mount-contract.v1` is exactly `{schema,staged_root_logical_id,executable_path,interpreter_path,library_paths,runtime_data_root,component_root,dependency_roots,durable_channel_fd,bwrap_argv,network_unshared,ambient_root_visible}`. Constants are executable `/host/pi`, runtime data root `/host/runtime-data`, component root `/extensions/component`, durable channel FD `5`, `network_unshared=true`, and `ambient_root_visible=false`. Dependency roots are digest-sorted unique `{package_tree_manifest_digest,root_path}` rows at `/extensions/dependencies/<64 digest hex>`. `interpreter_path` is null exactly when the closure interpreter is null and otherwise equals its `logical_path`; `library_paths` is the UTF-8-sorted unique array exactly equal to the closure `shared_libraries[].logical_path` values. Every non-null path is NFC, absolute inside the staged root, and the executable, interpreter, library, and runtime-data paths are pairwise distinct; no executable/interpreter/library path is equal to or a descendant of the runtime-data root. The namespace launcher is a reviewed statically linked helper implementing the required user/mount/pid/network namespace, bind operations, and inherited barrier socket directly; its ELF has no `PT_INTERP` and no `DT_NEEDED`, verified by the pinned probe before execution. Dynamic `bwrap` is ineligible. Because the static helper implements setup directly, `bwrap_argv` is exactly the empty JSON array; any value rejects. The content-addressed helper applies the exact `bwrap_argv`-equivalent contract: unshare all namespaces, construct the sealed private staging filesystem below as `/`, create fresh `/proc` and minimal `/dev`, and expose no host filesystem or source bind.

Before launch, the controller parses ELF `PT_INTERP` and dependency resolution using the pinned probe and requires exact closure equality. Before request construction, the request-pinned finalizer generates a unique 32-byte CSPRNG `process_start_nonce`; the controller only receives it from the claimed authorization and requires equality. The nonce is encoded as exactly 64 lowercase hex characters and bound once across authorization request/envelope, available/claim/terminal ledger records, supervisor bootstrap, host barriers, observations, and transcript. It creates three `socketpair(AF_UNIX,SOCK_SEQPACKET|SOCK_CLOEXEC)` channels: barrier, supervisor, and durable persistence. Before any send it enables `SO_PASSCRED` only on the controller's receiving FD3 and FD5 endpoints, retains exactly one local endpoint of each of the three channels, and forks the static launcher supervisor. Parent and child close every opposite/duplicate endpoint immediately after FD installation; no process retains both ends of any channel. In the child it installs the barrier endpoint as FD3, supervisor endpoint as FD4, and durable endpoint as FD5 (conditional `dup3` or `fcntl(F_SETFD,0)` when already equal), closes opposite/extra descriptors, and execs the supervisor. After fork, the controller sends exactly one JCS packet `{schema:"pi.namespace-supervisor-bootstrap.v1",action:"bootstrap_supervisor",process_start_nonce}` with no ancillary data on its retained supervisor endpoint whose child peer is FD4. The execed supervisor receives exactly that packet before any `clone3`, rejects EOF, extra bytes/messages/descriptors, wrong schema/action/nonce shape, or timeout, and retains the received nonce only in memory. It then creates the mapping gate, invokes `clone3` atomically with the exact namespace flags plus `CLONE_PIDFD`, receives the host pidfd/PID, writes and verifies UID/GID maps, releases the gate, closes its FD3/FD5 copies, and waits for the child to confirm identity setup, sealed staging, and host exec readiness. Only then the supervisor responds on FD4 with exactly one JCS packet `{schema:"pi.namespace-supervisor-host-spawned.v1",action:"host_spawned",process_start_nonce,parent_namespace_pid}` carrying exactly the clone-returned pidfd via `SCM_RIGHTS`, then closes FD4; missing/extra descriptor/message or a nonce unequal to the controller bootstrap fails. The supervisor waits and reaps the host. The controller never calls `pidfd_open`; it verifies the received pidfd is initially unsignaled and that later host-message `SCM_CREDENTIALS` PID equals the clone3 parent-namespace PID. The launcher preserves only stdin/stdout/stderr/FD3/FD5 through namespace setup and host exec; the supervisor retains no FD5 endpoint. Controller endpoint identity is bound by `{process_start_nonce,device,inode}`; descriptor number is transport, not authority. Immediately after fork the controller also queues sequence-0 host `bootstrap` containing the same nonce on its retained barrier endpoint whose launcher/host peer is FD3. Launcher and host inherit FD3; host core reads/authenticates bootstrap before initializing extension paths, enters `witness_bootstrap_paused`, sends `ready`, and blocks. Every received host message must carry `SCM_CREDENTIALS`; the first ready supplies the host PID in the controller's namespace. The controller binds pidfd identity to nonce/channel/PID, checks pidfd unsignaled before and after every observation, opens `/proc/<PID>` once with `O_PATH|O_DIRECTORY|O_NOFOLLOW`, reads `stat` starttime and maps through `openat`, and requires stable starttime/credential PID. Host exit, pidfd signal, PID/path replacement, starttime drift, or credential drift fails; the held proc directory and pidfd prevent selecting a replacement process. The controller verifies nonce/channel, records the `pre_extension_load` maps observation, then sends the matching `continue`. Before redemption, host sends/blocks on the same sequence for `pre_redemption`. Each host-barrier message is exactly `{schema,phase,sequence,process_start_nonce,prompt_run_attempt_digest,action,runtime_load_observation_digest,barrier_message_digest}`. Phase is `bootstrap|pre_extension_load|pre_redemption`; action is `bootstrap|ready|continue`; ready/bootstrap have null observation and continue has non-null observation. Production messages are: `(bootstrap,0,bootstrap,null,null)`, `(pre_extension_load,1,ready,null,null)`, `(pre_extension_load,2,continue,null,non-null observation)`, `(pre_redemption,3,ready,non-null attempt,null)`, `(pre_redemption,4,continue,same attempt,non-null observation)`. Integration inserts three non-barrier frames after ready sequence 1 and before continue sequence 2. First the paused host tentatively allocates its sole tuple and sends `pi.integration-attempt-reservation.v1` exactly `{schema,action,process_start_nonce,host_runtime_manifest_digest,execution_instance_digest,execution_generation,boot_nonce,session_instance_nonce,attempt_ordinal,prompt_run_attempt_digest,reservation_digest}`, action `propose_integration_attempt`; controller receives exactly one kernel credential matching host PID/starttime. Controller validates the preimage and obtains the finalizer's durable reserved record/head, then sends `pi.integration-attempt-reservation-commit.v1` exactly `{schema,action,process_start_nonce,reservation_digest,reserved_record_digest,reserved_store_head_digest,reservation_commit_digest}`, action `commit_integration_attempt`, with no ancillary item. Host verifies the exact tuple/head join and only then irreversibly consumes the ordinal; lost response leaves a canonical reservation and terminates the process. Controller next completes pre-witness resolution/finalizer authorized CAS, then sends the authorization-transport frame. For that controller-to-host frame sender supplies no ancillary item; host authenticates only the unique inherited endpoint, nonce, digest, authorized-record join, and exact sequence because ancestor PID credentials are not visible across `CLONE_NEWPID`. Only after all three frames does controller send continue sequence 2. Missing, extra, differently placed, or production-mode reservation/transport fails. The host copies both controller-supplied observation digests into the later transcript; controller retains and validates the corresponding observation objects. Timeout, EOF, extra/reordered message, wrong nonce/channel, or failed map read kills/reaps the host and yields no witness/redemption.

`pi.runtime-load-observation.v1` is exactly `{schema,phase,process_start_nonce,mappings,runtime_load_observation_digest}`. Mappings are UTF-8 sorted/unique by `(device,inode,file_offset,mapped_length,permissions,logical_path)` and exactly `{device,inode,file_offset,mapped_length,permissions,logical_path,content_digest}`; permissions match `^[r-][w-][x-][ps]$`. The closure's `expected_load_segments` rows are unique and exactly `{logical_path,file_offset,mapped_length,maximum_permissions,executable_required,content_digest}` where `maximum_permissions` matches `^[r-][w-][x-]$`, sorted by `(logical_path,file_offset,mapped_length,maximum_permissions)`. Eligibility requires runtime page size exactly 4096. The probe ignores `PT_LOAD` with `p_filesz=0`; for remaining segments it aligns `p_offset` down and `p_offset+p_filesz` up to 4096, then splits all overlapping aligned intervals at every boundary and deterministically ORs PF_R/PF_W/PF_X across covering segments, rejecting any resulting W+X interval. It emits disjoint intervals and marks executable-required iff X. Virtual addresses/ASLR are deliberately excluded because validation concerns file-offset coverage. `/proc/maps` parsing decodes kernel octal path escapes and rejects ` (deleted)`. After NFC normalization, an executable mapping path must equal `executable_path`, an interpreter mapping path must equal the non-null `interpreter_path`, a library mapping path must exactly equal one `library_paths` member, and a runtime-data mapping path must be a strict descendant of `runtime_data_root` separated by `/`; equality to the runtime-data root, lexical prefix without a path-component boundary, any other path, and any multi-class match reject. There is no implicit library-root or arbitrary longest-prefix rule. Device is canonical lowercase hex `major:minor` with no leading zero except the single digit `0`; inode as a canonical decimal safe integer, file offset from lowercase hexadecimal into a safe integer, and mapped length as decoded-hex `end-start`; rows serialize those numeric values as JSON integers; anonymous/bracket mappings are excluded, while every file-backed mapping is included. Before launch the controller obtains a post-seal no-follow `stat` through the staged-root descriptor for the executable, non-null interpreter, every library, and every runtime-data file and retains the exact device/inode tuple. Every observed executable/interpreter/library mapping must equal its resolved staged file's retained device/inode and closure content digest before segment comparison. Observed ELF segments may remove write for RELRO but may not add permissions beyond maximum, may not be writable+executable, must be geometrically contained in one expected segment, and executable-required coverage must be complete using observed rows that carry `x`. File-backed runtime-data rows are separately allowed only under the component-boundary descendant rule for `/host/runtime-data`, must have observed device/inode equal the resolved staged file's retained post-seal tuple, file offset and mapped length within its manifest byte length, resolve exact tree content, and not carry `x`; they need not match PT_LOAD segments. Every other file-backed row rejects. Content digest uses the registered runtime library, executable, or runtime-data domain according to resolved logical path. Runtime-data root placement and every sidecar lookup are bound to `/host/runtime-data` in the mount contract. Non-Linux or unavailable namespace/maps enforcement is ineligible, not a weaker posture.

`pi.sealed-staging-manifest.v1` is exactly `{schema,staged_root_logical_id,host_runtime_manifest_digest,loaded_component_manifest_digest,dependency_manifest_digests,entries,filesystem_kind,mount_attributes,old_root_detached,write_capable_descriptor_count,sealed_staging_manifest_digest}`. Entries are logical-path-sorted unique `{logical_path,source_kind,source_manifest_digest,source_path,kind,mode,byte_length,content_digest,device,inode}`. `filesystem_kind=private_tmpfs_copy`, attributes are exactly `["nodev","nosuid","readonly"]`, old root is detached, and writable descriptor count is zero. Inside the private child mount namespace, verified bytes are copied into a fresh tmpfs with no source bind/overlay/FUSE/backing-image alias, rehashed, no-follow stat-bound, all writable descriptors/mappings closed, remounted read-only, pivoted to root, old root detached, and mount/write capabilities dropped before host exec. Any unlisted file, writable alias, retained write capability, tuple drift, or source inode reuse is ineligible. The host reverifies sealed tuples before load, prompt execution, redemption, and final readback.

`pi.namespace-identity-bootstrap.v1` is exactly `{schema,process_start_nonce,parent_namespace_pid,namespace_flags,outer_euid,outer_egid,outer_supplementary_gids,setgroups_text,uid_map_text,gid_map_text,child_uid,child_euid,child_suid,child_fsuid,child_gid,child_egid,child_sgid,child_fsgid,child_supplementary_gids,no_new_privs,capability_sets_empty,namespace_identity_bootstrap_digest}`. Flags are the sorted exact set `CLONE_NEWCGROUP,CLONE_NEWIPC,CLONE_NEWNET,CLONE_NEWNS,CLONE_NEWPID,CLONE_NEWUSER,CLONE_NEWUTS,CLONE_PIDFD`. A `pipe2(O_CLOEXEC)` gate blocks the child before any lookup/mount/init. The supervisor writes and reads back `setgroups="deny\n"`, `uid_map="0 <outer_euid> 1\n"`, and `gid_map="0 <outer_egid> 1\n"`, then releases exactly byte `0x01`; child IDs are all zero, supplementary IDs are zero-valued with unchanged cardinality, `PR_SET_NO_NEW_PRIVS=1`, and every capability set is empty before host exec. Controller independently verifies those proc values. EOF, extra byte, unsupported ID, or drift fails.

Every host-to-controller FD5 request/raw frame requires exactly one kernel-supplied `SCM_CREDENTIALS`, no other ancillary item, and host PID/starttime equality. Every controller-to-host acknowledgement has no ancillary item and is authenticated by the unique inherited endpoint plus request digest, nonce, sequence, and prior acknowledgement. FD5 is bound by `pi.host-durable-channel-binding.v1` exactly `{schema,process_start_nonce,controller_endpoint_device,controller_endpoint_inode,host_endpoint_device,host_endpoint_inode,controller_parent_namespace_pid,host_parent_namespace_pid,transport,credential_policy,durable_store_id,durable_channel_binding_digest}`, with transport `unix_seqpacket_fd5`, exact `SCM_CREDENTIALS` PID policy, and store `pi-host-durable-artifact-store-v1`. A commit is one `pi.host-durable-commit-request.v1` `{schema,durable_channel_binding_digest,channel_sequence,attempt_commit_ordinal,process_start_nonce,execution_instance_digest,execution_generation,prompt_run_attempt_digest,artifact_kind,artifact_digest,artifact_bytes_digest,artifact_byte_length,durable_commit_request_digest}`, then one exact raw-JCS artifact frame. Artifact kind is exactly `application_witness|integration_acknowledgement|delivery_receipt|pre_redemption_journal|witness_redemption|delivery_execution_transcript|replay_probe`; each raw frame uses its registered lexical-byte domain. The controller parses witness/subject bytes to obtain and cross-check boot/session/attempt identity and every transcript digest; no separate unauthenticated value channel exists. The controller validates identity/length/digests, performs no-replace write plus file/log/parent-directory fsync, then returns `pi.host-durable-commit-acknowledgement.v1` exactly `{schema,issuer,durable_channel_binding_digest,durable_store_id,channel_sequence,attempt_commit_ordinal,commit_request_digest,artifact_kind,artifact_digest,artifact_bytes_digest,recovery_identity,prior_commit_ack_digest,fsync_scope,persistence_outcome,durable_commit_ack_digest}`. Issuer is exactly `{kind:"pi_host_durable_sink",id:"pi-host-durable-artifact-store-v1"}`; recovery identity is exactly `{process_start_nonce,execution_instance_digest,execution_generation,prompt_run_attempt_digest,artifact_kind}`; fsync scope is `artifact_log_and_parent_directory`; outcome is `durable`. Sequence and per-attempt ordinal both start zero and increment. Production order is witness `0`, delivery receipt `1`, journal `2`, redemption `3`, delivery transcript `4`; integration order is witness `0`, acknowledgement `1`, journal `2`, redemption `3`, replay probe `4`. Controller transcript is persisted separately by the pinned finalizer before terminal CAS. Duplicate recovery identity, stale prior ack, copied store, ancillary descriptor, truncation, extra frame, or pre-fsync acknowledgement fails. Delivery attestation resolves the separate transcript commit acknowledgement; integration transcript is durable before terminal ledger CAS. `pi.controller-transcript-commit-ack.v1` is exactly `{schema,issuer,finalizer_identity,controller_transcript_digest,controller_transcript_bytes_digest,controller_transcript_byte_length,durable_store_id,fsync_scope,persistence_outcome,prior_store_commit_digest,controller_transcript_commit_ack_digest}`. Issuer and `finalizer_identity` both equal the fixed finalizer identity; store is `pi-host-durable-artifact-store-v1`; fsync scope is `artifact_log_and_parent_directory`; outcome is `durable`; prior store commit equals this attempt's replay-probe durable acknowledgement, never null. The acknowledgement is the immediate successor of that commit in the same append-only store. On FD6 terminal request the finalizer validates exact bytes/digest/identity, performs no-replace file/log/directory fsync, returns this ack in terminal resolution, then may CAS the ledger; ack before fsync or alternate store rejects.

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
| finalizer executable bytes | `pi.finalizer-executable-bytes.v1` | exact bytes |
| finalizer message | `pi.integration-finalizer-message.v1` | `message_digest` |
| integration attempt reservation | `pi.integration-attempt-reservation.v1` | `reservation_digest` |
| integration attempt reservation commit | `pi.integration-attempt-reservation-commit.v1` | `reservation_commit_digest` |
| controller transcript commit ack | `pi.controller-transcript-commit-ack.v1` | `controller_transcript_commit_ack_digest` |
| integration cancellation | `semantic-pi-integration-cancellation.v1` | `integration_cancellation_digest` |
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
| pre-redemption-journal lexical bytes | `pi.pre-redemption-journal-json-bytes.v1` | exact JCS bytes |
| delivery-transcript lexical bytes | `pi.delivery-transcript-json-bytes.v1` | exact JCS bytes |
| controller-transcript lexical bytes | `pi.controller-transcript-json-bytes.v1` | exact JCS bytes |
| filesystem file bytes | `pi.filesystem-file-bytes.v1` | exact bytes |
| stdout bytes | `pi.process-stdout-bytes.v1` | exact bytes |
| stderr bytes | `pi.process-stderr-bytes.v1` | exact bytes |
| pre-redemption journal | `pi.prompt-system-pre-redemption-journal.v1` | `pre_redemption_journal_digest` |
| ledger store head | `semantic-release.pi-integration-ledger-store-head.v1` | `ledger_store_head_digest` |
| ledger record bytes | `semantic-release.pi-integration-ledger-record-bytes.v1` | exact JCS bytes |
| component release provenance | `pi.component-release-provenance.v1` | `component_release_provenance_digest` |
| host integration release provenance | `pi.host-integration-release-provenance.v1` | `host_integration_release_provenance_digest` |
| signed authority statement | `semantic-release.signed-statement.v1` | JCS substantive fields |
| import closure | `pi.module-import-closure-manifest.v1` | `module_import_closure_manifest_digest` |
| sealed staging | `pi.sealed-staging-manifest.v1` | `sealed_staging_manifest_digest` |
| namespace identity bootstrap | `pi.namespace-identity-bootstrap.v1` | `namespace_identity_bootstrap_digest` |
| durable channel binding | `pi.host-durable-channel-binding.v1` | `durable_channel_binding_digest` |
| durable commit request | `pi.host-durable-commit-request.v1` | `durable_commit_request_digest` |
| durable commit acknowledgement | `pi.host-durable-commit-acknowledgement.v1` | `durable_commit_ack_digest` |
| registrar binding | `pi.prompt-system-registrar-binding.v1` | `registrar_binding_digest` |
| authority control resolution | `semantic-release.authority-control-resolution.v1` | `authority_control_resolution_digest` |
| authority acquisition pin | `semantic-release.authority-store-acquisition-pin.v1` | `authority_store_acquisition_pin_digest` |
| authority read receipt | `semantic-release.authority-store-read-receipt.v1` | `authority_store_read_receipt_digest` |
| attestation appointment | `pi.host-attestation-owner-appointment.v1` | `host_attestation_owner_appointment_digest` |
| attestation root | `pi.host-attestation-trust-root.v1` | `host_attestation_trust_root_digest` |
| attestation statement | `pi.host-attestation-statement.v1` | `host_attestation_statement_digest` |
| authorization binding | `pi.host-integration-authorization-binding.v1` | `host_integration_authorization_binding_digest` |
| authorization transport | `pi.host-integration-authorization-transport.v1` | `authorization_transport_digest` |
| action authority resolution | `semantic-release.pi-integration-action-authority-resolution.v1` | `integration_action_authority_resolution_digest` |
| abandonment observation | `semantic-release.pi-integration-abandonment-observation.v1` | `integration_abandonment_observation_digest` |
| integration replay history | `semantic-release.pi-integration-replay-history.v1` | `integration_replay_history_digest` |
| integration reference evidence set | `semantic-release.pi-integration-reference-evidence-set.v1` | `integration_reference_evidence_set_digest` |
| v0 baseline aggregate rows | `semantic-release.v0-authority-baseline-aggregate.v1` | exact row bytes |
| v0 baseline manifest | `semantic-release.v0-authority-baseline-manifest.v1` | `v0_baseline_manifest_digest` |

`loaded_entry_digest` is exactly the resolved package-tree entry's `content_digest` under `pi.package-file-bytes.v1`; no second entry-digest algorithm exists. Store-head, transcript-byte, configuration, and nested digest fields must use the corresponding row above. Unknown domains reject.

## Closed configuration preimages

`pi.loader-configuration.v1` is exactly `{schema,loader_kind,loader_version,typescript_version,typescript_package_tree_manifest_digest,jiti_package_tree_manifest_digest,resolution_algorithm,tsconfig_digest,import_map,allowed_root_manifest_digests,node_builtin_allowlist,dynamic_import_policy,module_cache_mode,outside_imports_forbidden,native_addons_forbidden}`. `loader_kind=jiti`, `resolution_algorithm=pi.static-ts-jiti-resolution.v1`, and exact TypeScript/Jiti versions and package trees are component-provenance pinned; Jiti fallback is forbidden. Import-map rows are exact-specifier-sorted unique `{specifier,target_logical_path,target_manifest_digest}`; prefix/package fallback rejects. Built-ins are sorted/unique literal `node:` specifiers equal to the standalone allowlist. Cache mode is `per_execution_generation`; outside imports and native addons are forbidden.

`pi.module-import-closure-manifest.v1` is exactly `{schema,algorithm,entry,modules,module_edges,builtin_edges,module_import_closure_manifest_digest}`. Entry/module rows are `{package_tree_manifest_digest,logical_path,content_digest,media_type}`; module edges are `{from_package_tree_manifest_digest,from_logical_path,source_ordinal,syntax_kind,specifier,to_package_tree_manifest_digest,to_logical_path,to_content_digest}`; builtin edges omit target fields. Modules sort by `(manifest,path,digest)` and edges by `(from_manifest,from_path,source_ordinal,syntax_kind,specifier)`. The pinned TypeScript parser accepts strict UTF-8 `.ts,.tsx,.mts,.cts,.js,.jsx,.mjs,.cjs` and strict JSON; any parse diagnostic rejects. Only static `ImportDeclaration`, `ExportDeclaration` with source, literal `require`, and import-equals external references are legal; dynamic import, computed/nonliteral require, glob/context/plugin resolution, native addon, and runtime fallback reject. Ordinals follow AST source position from zero. Relative resolution checks exact path then the fixed extension order above then `/index` plus that order, requiring one match. Import-map lookup is exact only. Every non-builtin bare specifier must have one exact full-specifier import-map row naming its dependency manifest and target path; package-name, exports, main/module, subpath, prefix, extension, and Jiti fallback resolution are forbidden. Built-ins require literal `node:` allowlisting. Every edge stays in its sealed root, every resolved file digest equals its package row, graph traversal is deterministic depth-first in edge order, cycles reject, and every listed dependency is reachable exactly once. Independent validators recompute this closure rather than trust it.

`pi.process-environment-contract.v1` is exactly `{schema,inherit_environment,entries,unset_keys,locale,timezone,network_mode}`. Inheritance is false. The only permitted entry keys are exactly the used subset of `HOME,LANG,LC_ALL,PATH,PI_CODING_AGENT_DIR,TMPDIR,TZ`, UTF-8-key-sorted unique `{key,value}` rows; every omitted key is present in the sorted/unique `unset_keys`, and the sets partition that closed allow-list. Locale is `C.UTF-8`, timezone `UTC`, and network mode `forbidden`.

`pi.argv-contract.v1` is exactly `{schema,standalone_host_executable_digest,argv,cwd_logical_id,process_environment_contract_digest,shell}`. `argv` preserves order, `shell=false`, and cwd resolves inside the staged host snapshot.

`pi.filesystem-tree-manifest.v1` is exactly `{schema,root_logical_id,entries}` where entries are UTF-8 sorted by `(path,kind)` and exactly `{path,kind,mode,byte_length,content_digest}`. Kinds are `directory|file`; directories have null length/digest; files use `pi.filesystem-file-bytes.v1`. `pi.filesystem-manifest.v1` is exactly `{schema,roots,process_ids,network_connections}`. Roots are UTF-8-logical-id-sorted unique `{logical_id,realpath_digest,tree_manifest_digest,mutability}` rows; mutability is `read_only|disposable_write|canonical_ledger`. Process IDs are sorted safe integers. Network connections is empty. Real paths never enter a preimage directly.

## Execution and attempt identity

`execution_instance_digest` preimage is exactly:

```text
{host_runtime_manifest_digest, boot_nonce, extension_api_version}
```

Every nonce is an independent 32-byte Linux `getrandom(...,0)` draw, encoded as 64 lowercase hexadecimal characters; only `EINTR`/partial completion retries are legal. Seeds, inherited PRNG state, timestamps, UUIDs, derived hashes, insecure flags, and `/dev` fallback reject. `process_start_nonce` is drawn by the request-pinned finalizer once before authorization request construction and is unique across the canonical ledger's non-pruned history; collision terminates construction without reuse. `boot_nonce` is drawn after authenticated bootstrap and before extension initialization, is constant for one host process, differs from the process nonce, and appears in transcript/attestation. Attestation-owner evidence rejects reuse of `(host_runtime_manifest_digest,boot_nonce)`.

`prompt_run_attempt_digest` preimage is exactly:

```text
{execution_instance_digest, execution_generation, attempt_ordinal,
 session_instance_nonce}
```

Session nonce is drawn once per session, differs from process/boot nonces, remains in a non-evicting process set, and appears in witness/transcript/attestation; accepted evidence rejects reuse with the execution instance. `execution_generation` initializes to `0`; reload invalidates nonterminal work and atomically increments before new attempts. The attempt counter is scoped by instance/generation/session, initializes to `0`, reserves current then increments, so first use is `0`; every suppressed, failed, aborted, and witnessed attempt consumes an ordinal. Reuse or reserving the maximum rejects.

`handler_registration_index` is zero-based in one total registration order shared by ordinary handlers and contributors: extension load order then registration call order. The contributor is last; any later registration/change makes witnessing ineligible. `pi.prompt-system-registrar-binding.v1` is exactly `{schema,host_runtime_manifest_digest,execution_instance_digest,execution_generation,extension_api_instance_nonce,repository_identity,component_identity,package_identity,package_artifact_identity,component_release_provenance_digest,loaded_component_manifest_digest,entry_logical_path,loaded_entry_digest,sealed_staging_manifest_digest,namespace_identity_bootstrap_digest,handler_registration_index,registrar_binding_digest}`. The host draws the API nonce and creates a fresh ExtensionAPI plus private WeakMap capability for the exact sealed loader tuple. `registerPromptSystemContributor({prepare,applied})` is a closure over it and accepts no identity. Detached/stale/delegated-wrong-generation APIs reject; the host derives every binding field and registration index.

`prepare(prepareContext)` receives a deeply immutable host-derived identity/attempt/registrar plus authenticated resolved-generation projection (generation receipt digest, consumer repository, v0 canary scope), signal/deadline, and—only in integration mode—the closed authorization binding; no mutating methods. It returns exactly:

- `{kind:"terminal_status",status}` where status is `{delivery_outcome:"suppressed",suppression_reason}` or `{delivery_outcome:"failed",error}`. The host constructs a non-authoritative terminal observation, keeps input unchanged, issues no witness, and never calls `applied`.
- `{kind:"contribution",systemPrompt,application_witness_request}` where request is host-validated `{rocs_generation_receipt_digest,subject_kind,authorization_envelope_digest}` and prompt differs bytewise from input. Production requires delivered subject/null authorization; integration requires acknowledgement subject/exact binding.

Prepare throw/timeout/abort/malformed output aborts before provider/model use and emits only local diagnostic. The sole final contributor rule and registrar binding prevent another extension from self-asserting component identity.

After assignment/readback, the host enters a host-wide prompt-application critical section and invokes the same binding's personalized `applied({witness},restrictedContext)` exactly once. Witness/context are defensive immutable snapshots; context contains only host-derived identity, authorization binding when applicable, `AbortSignal`, and deadline, with no model, session, UI, message, prompt, command, or provider method. The host guard also rejects recursive `prompt`, `continue`, `_runAgentPrompt`, `sendUserMessage`, `sendCustomMessage({triggerTurn:true})`, host-owned model completion, or provider dispatch attempted through retained closures until redemption and transcript persistence finish. Any attempt aborts.

The callback resolves within 500 ms and returns exactly `{subject_kind,subject}`. Production permits only a complete delivered receipt; integration permits only the closed acknowledgement and rejects delivered/suppressed/failed before journal or redemption. Terminal observations occur only before witness request and never enter journal, redemption, transcript, attestation, or delivery authority. Timeout, throw, stale context, wrong brand/index, missing subject, or reentry aborts. No broadcast/unrelated extension receives the witness.
