---
summary: "Proposed correlated exact-match observation for semantic-preflight bytes in Pi agent state."
read_when:
  - "Designing, reviewing, or implementing Decision 98."
type: "rfc"
status: "proposed"
decision_id: 98
protocol_revision: "pi-ontology-workflows-agent-prompt-observation-v0-r2"
---
# RFC — Correlated Pi agent-prompt observation v0

## Decision request

Authorize the smallest truthful successor to Decision 89 that can correlate package preparation with Pi's assigned agent-state prompt despite overlapping preflights.

The design requires one minimal Pi-host capability/event contract and one bounded package slot. It does not observe provider payloads, transmission, model input, or semantic benefit.

## Identity and baseline

- architecture owner: `core/rocs-cli`;
- host owner: Pi coding-agent runtime;
- package owner: `pi-extensions` / `pi-ontology-workflows` / `@tryinget/pi-ontology-workflows`;
- live-lineage package candidate: `96f3b699b77b941522e0cada76672276919e2d6e`;
- package tree: `396630b4cf329d2e1a2a03fa9e4cb219381e89eb`;
- predecessor: `pi-ontology-workflows-handler-observation-v0-r4`;
- proposed revision: `pi-ontology-workflows-agent-prompt-observation-v0-r2`.

Every owner task re-pins its then-current default line. Package release/version behavior cannot change incidentally.

## Why a host contract is required

Current Pi source happens to await the handler chain, assign the prompt, and then emit `agent_start`, but it can overlap asynchronous prompt preflights before marking a run active. Current events have no shared run identity, and `prompt.system.chain.v1` does not bind assignment/readback ordering.

A package-only `agent_start` observer could therefore consume another run's single-slot preparation. Narrowing the wording would not fix the false correlation. Decision 98 instead adds an explicit owner-controlled seam.

## Host capability and event

Add immutable capability token:

```text
prompt.agent-state.observation.v1
```

Its exact guarantee:

1. Pi creates one opaque process-local `promptRunToken` before invoking `before_agent_start` for a prompt execution.
2. `BeforeAgentStartEvent` carries that token.
3. After the complete handler chain resolves and Pi assigns the resulting system prompt to agent state, Pi emits:

```ts
interface AgentPromptReadyEvent {
  type: "agent_prompt_ready";
  promptRunToken: string;
  systemPrompt: string;
}
```

4. The token equals the token from that execution's `before_agent_start` event.
5. `event.systemPrompt` is the exact assigned Pi agent-state prompt at this seam.
6. The event fires before the corresponding provider turn begins. It may fire even when later provider preparation fails; it does not attest provider invocation.
7. Tokens are unique among prompt executions concurrently alive in one host process. They are not stable across process/session replacement, are not credentials, and establish no external authority.

The host freezes event values and token strings. Extension API type, documentation, capability tests, overlap tests, assignment-order tests, and lifecycle tests land together. Hosts without the token visibly disable Decision-98 observation while preserving existing semantic-preflight behavior.

No provider payload, headers, model, or transport fields are added.

## Package state

Extract package logic into a small `agent-prompt-observation-state.ts`; do not grow the 500-LOC preflight runtime.

One closure-owned state exists:

```text
empty
  └─ exact append prepared(token A) ─► prepared(A)
prepared(A)
  ├─ newer preparation(token B)     ─► prepared(B)
  ├─ ready(token A) + exact match   ─► terminal(exact_match)
  ├─ ready(token A) + mismatch      ─► terminal(mismatch)
  ├─ ready(non-A)                   ─► unchanged
  └─ invalidation/failure           ─► empty
terminal
  ├─ newer preparation(token B)     ─► prepared(B)
  ├─ ready(nonmatching/repeated)     ─► unchanged
  └─ invalidation                    ─► empty
```

The token is held only as a private correlation field while the slot exists. It is omitted from every public record, command output, log, error, digest, test snapshot intended as evidence, and durable artifact. There is no collection, queue, history, timestamp, allocator, persistence, or session entry.

Latest-preparation-wins is deliberate: when overlapping attempts replace the slot, a later ready event for the older token is ignored. This may omit an observation, but cannot misattribute one.

## Exact-match semantics

Decision-89 preparation remains unchanged. The prepared state stores the predecessor record plus the private token.

On a matching `agent_prompt_ready` event, the package validates Unicode scalar input and computes the same domain-separated UTF-8 byte length/digest over `event.systemPrompt`. It emits one immutable terminal record:

- `agent_prompt_exact_match` when whole-prompt byte length and digest equal the prepared fields;
- `agent_prompt_mismatch` otherwise.

Mismatch does **not** mean the semantic contribution was removed. It means only that the whole assigned prompt was not byte-identical; later handlers may have appended, removed, or rewritten bytes.

## Closed record

Shared fields:

```text
schema
protocol_revision
repository_id
component_id
package_name
phase
predecessor_record_digest
prepared_prompt_byte_length
prepared_prompt_digest
observation_outcome
claim_scope
callback_chain_completion_observed
pi_agent_state_observed
whole_prompt_exact_match_observed
provider_payload_observed=false
provider_transmission_observed=false
model_input_observed=false
record_digest
```

Prepared values:

```text
phase=prepared
observation_outcome=package_handler_return_prepared
claim_scope=extension_local_pre_return_only
callback_chain_completion_observed=false
pi_agent_state_observed=false
whole_prompt_exact_match_observed=false
```

Terminal values:

```text
phase=terminal
observation_outcome=agent_prompt_exact_match|agent_prompt_mismatch
claim_scope=pi_agent_state_at_agent_prompt_ready_only
callback_chain_completion_observed=true
pi_agent_state_observed=true
whole_prompt_exact_match_observed=true|false
```

The record digest uses JCS and a fixed new domain. It is a local integrity check, not a signature, public receipt, or provenance credential.

## Deterministic operator readback

Extend the existing command:

```text
/ontology-preflight observation
```

Exact output states are:

```text
semantic-preflight-observation protocol=pi-ontology-workflows-agent-prompt-observation-v0-r2 state=disabled
semantic-preflight-observation protocol=pi-ontology-workflows-agent-prompt-observation-v0-r2 state=enabled outcome=none
semantic-preflight-observation protocol=pi-ontology-workflows-agent-prompt-observation-v0-r2 state=prepared claim=pre-return-only
semantic-preflight-observation protocol=pi-ontology-workflows-agent-prompt-observation-v0-r2 state=terminal outcome=exact_match claim=pi-agent-state-only provider=false model=false
semantic-preflight-observation protocol=pi-ontology-workflows-agent-prompt-observation-v0-r2 state=terminal outcome=mismatch claim=pi-agent-state-only contribution_survival=unknown provider=false model=false
semantic-preflight-observation protocol=pi-ontology-workflows-agent-prompt-observation-v0-r2 state=unsupported-host
```

State precedence is exact: `unsupported-host` wins whenever the capability token is absent; otherwise `disabled` wins without a current grant; with a current grant the state is `prepared`, terminal, or `enabled outcome=none` in that order. Before readback the runtime evaluates current generation/grant/cwd/compatibility and clears stale state. Output contains no prompt-derived digest, byte length, run token, prompt text, ontology prose, path, environment, session/provider/model identity, or secret. The command uses TUI notification only and never appends a session entry or log.

The fixed protocol string proves only which command implementation responded. R1 separately inspects loaded resource provenance and duplicate commands across global/project settings.

## Lifecycle and concurrency

Clear on reset, shutdown, disable, stale/expired grant, successful grant replacement, mode drift, generation/request/grant/cwd/compatibility invalidation, producer rejection/malformed result, non-append output, builder failure, and explicit unsupported-host detection.

Preserve live request-epoch semantics and Decision-89 slot ownership. Same-key completion order may replace the latest preparation. Nonmatching ready tokens never clear or rewrite the slot. Repeated matching ready events after terminal state are no-ops.

## Claims and non-claims

A terminal record proves only:

> For one host-correlated prompt execution, the whole Pi agent-state system prompt exposed at `agent_prompt_ready` exactly matched or did not exactly match the package-prepared whole prompt.

It does not prove contribution survival under mismatch, final provider serialization, later `context`/payload rewrites, network transmission, provider receipt, model invocation/input/influence, semantic relevance, authenticity, adoption, activation, publication, production, or fleet status.

## Owner implementation sequence

### H0 — Pi host capability

Separate Pi-owner task changes only required host event types, runner/session dispatch, capabilities, docs, and tests. Use deterministic faux-provider/session harnesses; no external model/provider is needed. Gate on overlapping prompt correlation, unique tokens, assignment-before-event, event-before-provider, session replacement, and old-extension compatibility.

### P0 — package implementation

After H0 acceptance, a fresh package task starts from the live owner line and may change:

- new `src/semantic/agent-prompt-observation-state.ts`;
- `src/semantic/handler-observation.ts`;
- bounded wiring in `src/semantic/preflight-runtime.ts`;
- focused state/record/lifecycle/source-registration tests.

The extension entrypoint, manifests, lockfiles, release metadata, semantic-release-delivery substrate, and other packages remain unchanged.

### R1a — deterministic integration dogfood

Install neither global nor project package. Use a host SDK/runner harness with deterministic faux provider to load exact host and package candidates, exercise overlap, exact match/mismatch, unsupported host, and command output. This is engineering evidence only.

### R1b — live TUI canary

A separate runtime task explicitly authorizes one pinned provider/model call. It records all global/project package settings and source realpaths; preserves exact settings bytes/order/mode; replaces the old source so exactly one package instance is configured and one unsuffixed command/tool provenance resolves to the candidate; starts/reloads Pi; verifies unsupported-host when applicable, disabled, enabled-none, terminal, and disable/reset states; and exercises rollback. The transient `prepared` state is required only in deterministic R1a harness tests because live Pi provides no operator scheduling boundary before `agent_prompt_ready`.

Rollback restores the exact settings snapshot, source order, prior sole package, and fresh runtime generation; proves no candidate command/handler remains loaded; and never deletes unrelated cache, worktree, session, or repository state.

### B0/B1/B2

- B0: adjudicated deterministic retrieval relevance/latency/cost, no model.
- B1: preregistered randomized correct/disabled/sham mediation pilot on one pinned runtime.
- B2: powered held-out benefit study with practical margin and safety/cost limits.

R1b is not B1/B2. Publication, defaults, production, and fleet rollout remain separate decisions.

## Validation gates

Host: capability/token uniqueness, overlap, assignment ordering, frozen event, pre-provider ordering, replacement lifecycle, docs/types/tests.

Package: all Decision-89 vectors; prepared/terminal exact match/mismatch; private-token non-disclosure; nonmatching/repeated event behavior; latest-preparation-wins; all clearing paths; deterministic six-state command output; exactly one `before_agent_start` and one `agent_prompt_ready`; file-budget compliance; existing semantic-preflight, legacy-hint, semantic-release-delivery, package, and release gates.

Runtime: exact loaded host/package identities, no duplicate source/command, default-off, one authorized grant, one pinned canary, immediate disable, exact restoration, and sanitized evidence.

## Rollback

- H0/P0: revert owner commits independently.
- R1: disable, restore exact settings bytes and prior sole source, create a fresh Pi generation, verify prior command/tool provenance and absence of candidate protocol.
- No rollback infers model effects or deletes unrelated state.
