---
summary: "Proposed bounded state machine for observing semantic-preflight retention in Pi agent state."
read_when:
  - "Designing, reviewing, or implementing Decision 98."
type: "rfc"
status: "proposed"
decision_id: 98
protocol_revision: "pi-ontology-workflows-agent-prompt-retention-v0-r1"
---
# RFC — Pi agent-prompt retention observation v0

## Decision request

Authorize a default-off, package-local successor to Decision 89 that observes whether the exact semantic-preflight prompt prepared by `pi-ontology-workflows` matches Pi's agent-state system prompt when `agent_start` fires.

The architecture adds one `agent_start` handler to the existing package runtime and evolves the single replaceable observation slot into a bounded state machine. It does not add a Pi-host API or a second `before_agent_start` handler.

## Identity and baseline

- repository: `pi-extensions`;
- component: `pi-ontology-workflows`;
- package: `@tryinget/pi-ontology-workflows`;
- live-lineage Decision-89 candidate: `96f3b699b77b941522e0cada76672276919e2d6e`;
- package tree: `396630b4cf329d2e1a2a03fa9e4cb219381e89eb`;
- predecessor protocol: `pi-ontology-workflows-handler-observation-v0-r4`;
- proposed protocol: `pi-ontology-workflows-agent-prompt-retention-v0-r1`.

Implementation must re-pin the then-current owner default line and preserve package version/release behavior unless an independently authorized release task changes it.

## State machine

One closure-owned slot exists per extension runtime:

```text
empty
  └─ exact append prepared ─► prepared
prepared
  ├─ agent_start + exact length/digest match ─► retained
  ├─ agent_start + mismatch                  ─► replaced
  └─ invalidation/new attempt/failure        ─► empty
retained | replaced
  ├─ next enabled before_agent_start         ─► empty or prepared
  └─ lifecycle/grant invalidation            ─► empty
```

The slot contains one immutable fixed-shape record. There is no collection, attempt ID, timestamp, allocator, queue, history, persistence, timer, session entry, database row, file, or cross-process lineage.

### Prepared transition

The existing Decision-89 exact-append path remains unchanged through its final pre-return assignment. On success the slot stores a `prepared` record containing only:

- fixed identity and protocol fields;
- predecessor record digest;
- prepared prompt byte length and digest;
- outcome `prepared`;
- claim scope `extension_local_pre_return_only`;
- all host/provider/model fields false.

No prompt text is retained in the record. Existing generation, request-epoch, grant-object, cwd, compatibility, and slot-ownership checks govern whether a completion may assign or clear it.

### Retained/replaced transition

The same runtime registers one `agent_start` handler. If and only if the slot is `prepared` and still belongs to the current extension generation and development grant, it:

1. reads `ctx.getSystemPrompt()` once;
2. validates Unicode scalar input and computes the same domain-separated UTF-8 byte length/digest used for prepared output;
3. compares exact length and digest;
4. replaces the slot atomically with an immutable `retained` or `replaced` record.

`retained` means the observed Pi agent-state bytes at this `agent_start` matched the prepared output. `replaced` means they did not. Both outcomes prove that Pi progressed to the `agent_start` hook after the package prepared its return; neither proves provider serialization or transmission.

A repeated `agent_start` for retry/compaction while the slot is already terminal does not rewrite the observation. The next top-level `before_agent_start` clears/replaces it. Package tests must bind this behavior to current Pi lifecycle semantics rather than infer a universal turn identifier.

## Record contract

Use a closed immutable union with shared identity fields and phase-specific fields.

Prepared phase:

```text
schema
protocol_revision
repository_id
component_id
package_name
phase=prepared
predecessor_record_digest
prepared_prompt_byte_length
prepared_prompt_digest
observation_outcome=package_handler_return_prepared
claim_scope=extension_local_pre_return_only
callback_settlement_observed=false
pi_agent_state_observed=false
pi_agent_state_retention_observed=false
provider_payload_observed=false
provider_transmission_observed=false
model_input_observed=false
record_digest
```

Terminal phase adds/replaces only the closed observation fields:

```text
phase=terminal
predecessor_record_digest
prepared_prompt_byte_length
prepared_prompt_digest
observed_agent_prompt_byte_length
observed_agent_prompt_digest
observation_outcome=agent_prompt_retained|agent_prompt_replaced
claim_scope=pi_agent_state_at_agent_start_only
callback_settlement_observed=true
pi_agent_state_observed=true
pi_agent_state_retention_observed=true|false
provider_payload_observed=false
provider_transmission_observed=false
model_input_observed=false
record_digest
```

The record digest uses JCS and a new fixed domain. Digests authenticate only local bytes against accidental mutation; they are not signatures or public provenance.

## Operator readback

Extend the existing `/ontology-preflight` command with:

```text
/ontology-preflight observation
```

It reports only:

- package/protocol identity;
- phase and outcome;
- predecessor, prepared, observed, and record digest prefixes or full digests according to existing compact diagnostic conventions;
- prepared/observed byte lengths;
- explicit negative provider/model claims.

It never prints prompt text, ontology prose, paths, environment, session IDs, provider/model identity, or secrets. If disabled or empty it reports `observation: none`. Readback is diagnostic and non-authoritative.

## Lifecycle and concurrency

Clear the slot on:

- `session_start` and `session_shutdown` reset;
- explicit disable or observed stale/expired grant;
- successful grant replacement before assigning the new grant;
- non-TUI mode drift;
- stale generation/request/grant/cwd/compatibility completion;
- append-producer rejection;
- malformed producer result;
- non-append formatting replacement;
- record construction/digest failure;
- beginning the next eligible `before_agent_start` attempt.

Preserve Decision-89 ownership semantics:

- a stale old attempt cannot erase a newer-grant or newer-request slot;
- distinct newer requests are request-epoch fenced;
- same-key coalesced discovery with separate append completions remains last-completion-wins;
- one assignment replaces the slot atomically; JavaScript execution introduces no partial record.

## Claims and non-claims

A terminal record may claim only:

> At one `agent_start` callback in this extension runtime, `ctx.getSystemPrompt()` produced bytes whose exact length/digest matched or did not match the package's prepared prompt fields.

It does not claim:

- ordering or honesty of co-resident extensions;
- final provider-specific serialization;
- absence of later `context` or `before_provider_request` rewrites;
- network write, provider receipt, model invocation/input/influence;
- semantic relevance or correctness;
- authenticity, adoption, publication, activation, production, or fleet status.

A host-independent universally final payload witness would require a different host/provider architecture. Model benefit requires separate empirical evaluation.

## Implementation boundary

Expected package files:

- `src/semantic/handler-observation.ts` — evolve closed record/digest helpers;
- `src/semantic/preflight-runtime.ts` — bounded state transitions, `agent_start`, and command readback;
- focused record, lifecycle, source-order, and extension registration tests.

The extension entrypoint should remain unchanged because the runtime's existing `register(pi)` owns both hooks and the command. No `pi-mono`, settings, package manifest, lockfile, release metadata, semantic-release-delivery substrate, or other package changes belong to the implementation candidate.

## Validation

Required deterministic cases include:

1. Decision-89 exact-append and digest vectors remain unchanged;
2. prepared state remains pre-return-only;
3. matching `agent_start` produces retained;
4. mismatching `agent_start` produces replaced;
5. observed prompt Unicode/length/digest vectors;
6. no prompt contents in record or command output;
7. agent start without prepared state is a no-op;
8. repeated agent start does not rewrite terminal state;
9. next prompt and every lifecycle/grant invalidation clear/replace correctly;
10. stale old attempt cannot erase newer observation;
11. distinct request-epoch and same-key completion-order semantics;
12. exactly one `before_agent_start` and one `agent_start` registration;
13. prepared assignment remains final before return;
14. provider/model fields remain false;
15. existing semantic-preflight, legacy hint, semantic-release-delivery, package, and release gates pass.

## Rollout

### R0 — package implementation

Source/tests only on the live owner lineage. No installation.

### R1 — development dogfood

A separate task records current settings/source/commit/tree/version and rollback, replaces the old package source so exactly one instance is configured, starts or reloads Pi, verifies the new protocol through command readback, enables one fresh TUI development grant, exercises retained and disable/reset paths, and restores the prior source if any gate fails.

R1 may authorize one pinned provider/model canary only when its task says so explicitly. A no-model host harness is preferred for engineering proof; provider/model behavior remains empirical evidence rather than architecture proof.

### R2 — empirical evaluation

B0 semantic relevance precedes B1/B2 model-mediated evaluation. Publication, defaults, provider/model claims, production, and fleet rollout require separate owner decisions/tasks.

## Rollback

- R0: revert the implementation commit.
- R1: disable, restore the exact prior sole package source, reload/start a fresh Pi generation, verify prior package identity and ordinary ontology commands, and retain sanitized before/candidate/restored receipts.
- No rollback deletes unrelated caches, worktrees, sessions, or repository state.
