---
summary: "Staged owner-scoped implementation plan for Decision 85 semantic Pi insertion evidence v1."
read_when:
  - "Implementing Decision 85 after ADR acceptance."
  - "Creating or reviewing Decision 85 execution tasks."
type: "implementation_plan"
status: "accepted_plan"
---
# Implementation Plan — Semantic Pi insertion evidence v1

## Authority and boundary

- AK decision: `85`, accepted with ADR recorded.
- ADR: `docs/adr/2026-07-26-semantic-pi-insertion-evidence-v1.md`.
- Normative sources: `docs/project/semantic-pi-insertion-evidence-v1-rfc.md` and `docs/project/semantic-pi-insertion-evidence-v1-vectors.json`.
- Frozen review aggregate: `272c892af593ff10ddb056b1914f20372308fe8a47ca28b3ca04ca8e27882991`.
- Vector SHA-256: `e23437e075f49c36e7487deeec2ab8126cd8fb14c0dbf07bf48d17e466525ed4`.
- Accepted-object aggregate: `e1a715cd868bdd9807eecb798b29ac02342697cc2afd9ac8eb7d9b6296b97a7e`.
- Operator authorization: AK evidence `5583`, explicitly covering implementation, installation, reload, development dogfood, provider/model use, publication, activation, live acquisition, and production.

Authorization permits the staged owner work below. It does not waive owner boundaries, AK task gating, dependency order, stop conditions, review, rollback proof, or the insertion-only claim boundary.

The only claim is same-process host observation that one exact `@tryinget/pi-ontology-workflows` contribution was prepared, inserted, assigned, read back, privately acknowledged, and recorded before dispatch eligibility. Provider transmission, model invocation/input/influence, semantic correctness, adoption, consumer consent, and public authentication remain outside the claim.

All mutation occurs in isolated candidate worktrees. Dirty shared `pi-mono` and `pi-extensions` checkouts remain read-only and are never cleaned or overwritten.

## Closed implementation decisions

### Terminal insertion algorithm

1. Run all ordinary `before_agent_start` handlers first under existing chain semantics and no Decision-85 guard.
2. Resolve the final ordinary-handler input by definedness, not truthiness.
3. If no enabled Decision-85 contributor exists, assign normally and stop.
4. Reserve the attempt, acquire the active token/guard, and invoke only the exact structured contributor callbacks.
5. The component returns the complete contribution bytes, including any desired `\n\n` separator. The host adds, removes, or rewrites no byte.
6. Append the contribution once at the terminal byte offset of the final ordinary-handler input. The apply result is exactly `{assigned_bytes,start=input_byte_length,end=start+contribution_byte_length}`.
7. No ordinary chain handler runs after apply. Assign exactly those bytes, synchronously read them back without callback/await, and verify byte equality plus the operation-derived span.
8. Issue the private witness, invoke the exact applied callback, validate its acknowledgement, and commit the record before the outer `agent.prompt(messages)` call can run.

This ordering satisfies the RFC's exact `input + contribution` apply rule and eliminates search, later-handler drift, and separator inference. A factory call queues the structured contributor but does not allocate its index immediately. After every extension factory and ordinary prompt-chain registration completes, loader finalization atomically assigns the structured contributor a terminal `handler_registration_index`. Runtime prompt-chain registration is closed after finalization. The recorded total registration order therefore agrees with terminal execution.

### Public host ABI and activation

| Surface | Exact contract |
|---|---|
| Host capability | immutable token `prompt.system.insertion-evidence.v1` |
| Registration | `pi.registerPromptChainInsertionContributor({prepare, applied})` |
| Prepare invocation | `prepare.call(undefined, Object.freeze({inputPrompt,executionGeneration,attemptId,handlerRegistrationIndex,signal,deadlineMonotonicNs}))` |
| Prepare result | NFC JavaScript string whose exact fatal-UTF-8 bytes are the complete contribution |
| Applied invocation | exactly `applied.call(undefined, Object.freeze({witness}))` |
| Applied result | one in-memory plain object matching Schema 3 |
| Registration result | frozen host controller `{enableForCurrentGeneration,disable,getStatus}`; initially disabled |
| Development action | component command `/ontology-preflight enable-insertion-development`; TUI confirmation; current-generation grant, maximum 10 minutes |
| Production action | component command `/ontology-preflight enable-insertion-production canary|wave`; TUI confirmation; current-generation grant |
| Disable action | `/ontology-preflight disable-insertion`; synchronous controller disable and active-attempt abort |
| Observation | `ctx.getPromptChainInsertionEvidenceStatus()` and controller `getStatus()` return the same frozen privacy-safe status |
| Host attempt deadline | five seconds from reservation using the host monotonic clock; exact vector deadlines remain harness-controlled |

`enableForCurrentGeneration` accepts only frozen `{profile:"development"|"production_canary"|"production_wave",expiresAtMonotonicNs,maxAttempts,maxContributionByteLength}`. Fixed maxima are respectively: 10 minutes/32 attempts/16 MiB; 30 minutes/10 attempts/256 KiB; and 24 hours/500 attempts/256 KiB. The process state owns monotonic `nextGrantId`, starting at `0` without wrap. Successful enable atomically allocates it and returns frozen `{enabled:true,grantId,executionGeneration,profile,expiresAtMonotonicNs,maxAttempts,maxContributionByteLength}`.

Enable is allowed only when no grant and no protocol attempt is active. It throws `TypeError` before effect for invalid/range-exceeding input, `GrantActiveError` when a grant/attempt is active, and `StaleExtensionContextError` for a revoked controller. After disable, expiry, exhaustion, or reload revocation, a fresh grant may be enabled with a higher ID. `disable()` is synchronous/idempotent and returns frozen `{changed,grantIdOrNull,executionGeneration}`. `getStatus()` is read-only.

Each grant owns fresh attempt/accepted/error/control/duration/size counters and an immutable private binding from every reserved attempt ID to that grant ID. Process-lifetime totals and records remain separate and never enter grant threshold calculations. Status reports both process totals and current/last grant snapshot, including exact grant ID/generation/profile/limits. Reload preserves process totals, increments generation, revokes the grant, and requires explicit re-enable.

The host arms a monotonic expiry timer. Expiry or explicit disable during an active attempt synchronously sets its host abort signal; predicate order terminalizes Schema-5 `aborted`, revokes frame/witness, and releases token/guard. Expiry or max-attempt exhaustion while idle disables future protocol reservation and ordinary prompt assignment continues without an attempt. A prepared contribution above the grant limit but within the RFC 16-MiB limit is rejected before apply: the host sets abort and emits stage `prepare`, error `aborted`, details exactly `[{"key":"grant_id","value":"<decimal>"},{"key":"reason","value":"contribution_byte_limit_exceeded"}]`, marks rollback required, and disables the grant. RFC-global malformed/oversize input still follows RFC precedence.

Privacy-safe status contains no input/contribution bytes. It contains process totals plus current/last grant counters, contribution maximum, latest Schema-4 record, exact control objects, and integer-nanosecond samples for host bookkeeping and callback-to-record duration. Percentiles use nearest-rank over accepted attempts in that grant: sort ascending and select zero-based index `ceil(p*n)-1`. Operational error rate is `(all Schema-5 failures except private-cause operator_abort) / (accepted + all Schema-5 failures)` for that grant; it is evaluated only once the denominator reaches 100. Canary thresholds evaluate every completion; wave thresholds evaluate every completion and use only the current grant. Any invariant, limit, or configured threshold breach atomically sets that grant's `rollbackRequired=true` and disables future attempts. Runtime owners consume the grant-bound status to trigger disable/reload/version rollback. There is no environment, repository, model, prompt, or durable default-on switch.

Before extension-factory execution, `DefaultResourceLoader` resolves and freezes package provenance and passes it into `createExtension`. Only provenance exactly bound to repository `pi-extensions`, package `@tryinget/pi-ontology-workflows`, component `pi-ontology-workflows` receives this registration surface. Callbacks cannot submit identity. One active registration is allowed per fixed identity per generation; after revocation on new/resume/fork, loader finalization may replace it in the same generation with a new higher terminal index. A duplicate active or unauthorized registration fails synchronously at stage `registration` with `identity_mismatch` and attempt `null`. `handler_registration_index` comes from one process-local monotonic counter covering ordinary prompt-chain handlers and finalized structured contributors.

The capability token, controller, and public exports land in the same host task as the complete state machine; no incomplete API is advertised.

### Process-local state and lifecycle

`PromptChainInsertionProtocolState` is owned by `AgentSessionRuntime`, passed into each replacement `AgentSession`, and retained until process/runtime disposal. The production `createAgentSessionRuntime()` path always injects it. Low-level direct `createAgentSession()` callers advertise no insertion-evidence capability unless they explicitly inject a process-state owner; tests may inject one. Session-local fallback state is forbidden.

| Lifecycle | Required action |
|---|---|
| startup | generation `0`, next attempt `0`, registration counter `0`, empty non-evicting attempt/record sets |
| reload | at the first executable line, before `session_shutdown` or any await: increment generation, revoke registrations/frames/witnesses/controllers, abort the active attempt, cancel its timer; overflow makes protocol permanently ineligible |
| new/resume/fork | before shutdown callback/await: revoke old registrations/frames/witnesses/controllers but preserve generation, next attempt, registration counter, and committed sets; rebuilt extensions receive new indices |
| abort/deadline | same short transition path terminalizes once, revokes frame, releases token/guard, and discards late settlement |
| shutdown/runtime dispose | synchronously mark closing and terminalize/revoke before callbacks; no later reservation; in-memory records disappear only with process owner disposal |

No cross-process continuity, recovery actor, database, or durable authority is introduced.

### Six-entrypoint guard map

A single synchronous `checkEntrypoint(kind)` classifies from host guard state plus the active async-context frame before any effect.

| RFC entrypoint | Host seam |
|---|---|
| `prompt` | first line of `AgentSession.prompt()` plus a guarded private helper replacing direct internal `agent.prompt()` bypasses |
| `continuation` | one `continueWithProtocolGuard()` wrapper replacing all direct `agent.continue()` call sites |
| `completion` | `AgentSession.compact()`, branch summarization entry, and an injected wrapper around all coding-agent `completeSimple()` calls |
| `model_invocation` | first operation of coding-agent `sdk.ts` `streamFn`, before auth or payload construction |
| `provider_dispatch` | immediately before `streamSimple(...)` in `sdk.ts` |
| `contributor_callback` | host private callback runner; ordinary handlers finish before guard acquisition; only exact prepare/applied callbacks are sanctioned |

Every ExtensionAPI/context closure carries its immutable registration identity. Guard-aware classification runs at the front door of `createExtensionAPI()` and `ExtensionRunner.createContext()` methods before existing `runtime.assertActive()`/`runner.assertActive()` checks. A detached or revoked caller therefore produces the required private `stale_invocation` result rather than a generic stale-context error.

The classifier creates and freezes the exact `dispatch_blocked` or `stale_invocation` object and appends it to the process-local status/control sink. Existing `Promise<void>` APIs keep their signatures and reject before effect with an internal `HostControlRefusal` carrying that object. Fire-and-forget adapters preserve the private exact result rather than rewriting it. Matching-frame reentry records `reentry_attempt`, poisons the outer attempt, and performs no nested operation. Impossible guard-absent/active-frame state terminalizes `internal_failure`.

## Execution sequence

### R1 — ROCS schema and independent conformance substrate

Owner: `core/rocs-cli`.

Add only the six-schema Draft 2020-12 bundle, independent stdlib Python and Node validators, one unittest bridge, and an unconditional exact Node `26.1.0` validator pin in `scripts/tool_versions.json`. Inline shapes remain `$defs`; no seventh packaging schema is used.

Each validator independently parses frozen source bytes, implements strict JSON/NFC/JCS, eight digest domains, raw-byte hashing, event execution, and the host fixture state machine. Neither imports the other, generated output, ROCS runtime code, expected values, case-ID behavior, or predecessor machinery.

Gate: both independently reproduce 16 cases, 13 host fixtures, 3 accepted cases, all exact hashes, and zero unused events; full ROCS CI passes.

### H1 — Complete Pi host insertion-evidence capability

Owner: `softwareco/contrib/pi-mono`, package `packages/coding-agent`. Depends on R1.

Add a small `src/core/extensions/prompt-chain-insertion-evidence.ts` module and integrate the closed ABI, loader provenance, process state, terminal insertion algorithm, strict validation, private frame/witness gateway, all guard seams, assignment/readback, reload invalidation, and in-memory record linearization. Fix the current empty-string assignment discrepancy. Keep provider-native payloads, TUI implementation, session JSONL, databases, recovery, and generic `packages/agent` outside this slice.

The host harness executes vector schedules without using case IDs or expected fields to choose behavior; expected objects are read only after actual execution.

Gate: faux-provider tests prove all 16 cases and 13 host fixtures, exact control results, zero provider/model operations before commit, identity/brand/replay closure, lifecycle/overflow behavior, late-settlement rejection, and ordinary host policy after release/rollback. Additional tests cover grant re-enable/active rejection, grant-ID/counter/status binding, expiry/disable during idle and active attempts, attempt exhaustion, exact over-contribution error, nearest-rank percentiles, error-rate denominator/exclusion, atomic `rollbackRequired`, auto-disable, and privacy-safe status shape.

### C1 — Component contribution and exact acknowledgement

Owner: `softwareco/owned/pi-extensions`, package `packages/pi-ontology-workflows`. Depends on R1 and H1.

Register through the closed host ABI. Reuse canonical semantic-preflight rendering but return the complete separator-plus-rendering contribution. Return Schema 3 only from the exact applied callback after private-witness tuple validation. Extend the existing `/ontology-preflight` command with the exact enable/disable actions above; no environment or repository gate exists. Bind pending state to generation/attempt and invalidate on disable/reload/shutdown/abort.

Component tests do not implement the host fixture state machine and do not use vector case IDs/expected fields as behavior. They independently validate Schema 3/digests and component-owned callback/lifecycle cases. Do not restore or repurpose staged Decision-53 files or change unrelated defaults.

Gate: exactly-once acknowledgement, stale/foreign/clone rejection, callback throw/timeout, grant expiry, reload, disabled behavior, and package gates pass.

### D1 — Workstation development runtime proof

Owner: `softwareco/infra/workstation`, runtime-operation/receipt paths only. Depends on R1, H1, and C1.

The workstation repo owns the named local runtime lifecycle. Before mutation it runs repo-owned status/admission surfaces (`python3 scripts/phasee/lane-op.py status current-posture`, `python3 scripts/phasee/lane-op.py status raw-backends`, and applicable service health), records a plan-only install/reload diff, and stops if baseline health or coexistence is degraded. After explicit apply admission, a disposable HOME/config/cache receives exact candidate artifacts; D1 runs the host 16/13 harness plus real-component subset, reloads one named development process, exercises one TUI attempt, reads privacy-safe status, then disables/reloads and restores prior coordinates. It never mutates host/component source or baseline services.

Gate: workstation-owned runtime receipt with exact commands, artifacts, before/after source hashes, metrics/status, zero pre-record operations, and rollback proof.

### V1 — Integration evidence coordinator

Owner: `core/rocs-cli`, evidence/coordination paths only. Depends on D1.

Verify the immutable R1/H1/C1/D1 receipts, rerun both standalone validators, and bind exact commits/artifacts/results into one replayable integration receipt. V1 performs no install, reload, activation, deployment, or source mutation.

Gate: receipt consistency, independent result agreement, filesystem invariance, and accepted D1 rollback.

### PH1 / PC1 — Owner package release and publication

Owners: Pi host release owner in `pi-mono` and component release owner in `pi-extensions`, as separate tasks. Depend on V1.

Each owner runs supply-chain/release gates, publishes only its signed compatible package coordinate, and records exact provenance. Package publication wording is insertion-only. Steward/editorial publication is a separately routed publication-owner task.

### PR1 — Workstation production runtime rollout

Owner: `softwareco/infra/workstation`, runtime-operation/receipt paths only. Depends on PH1 and PC1.

Before mutation, run workstation status/admission surfaces, preserve baseline service health, and record a plan-only deployment/rollback diff. Stop if baseline/coexistence is degraded. After apply admission, deploy exact compatible releases default-off, enforce G5/G6 through grant-bound time/attempt/size limits and status metrics, execute named canary/wave operations, and perform disable/reload/version rollback on any `rollbackRequired` flag or trigger. Never mutate host/component source or baseline services.

### PO1 — Production evidence coordinator

Owner: `core/rocs-cli`, evidence/coordination paths only. Depends on PR1.

Verify release and PR1 receipts, threshold calculations, status observations, and rollback proof; attach canonical AK evidence. PO1 performs no deployment, activation, reload, or source mutation.

## Task decomposition rule

Create fresh owner-scoped AK tasks for R1, H1, C1, D1, V1, PH1, PC1, PR1, and PO1. Link all to Decision 85 as `post_adr_execution`. Before implementation, attach all continuation artifacts, explicitly reevaluate every linked task, require passport `ready_for_unblocked=true`, and advance Decision 85 to exactly `unblocked`. Never reopen/reuse tasks `4230`, `4250`, `4278`, `4298`, or their downstream tasks.
