---
summary: "Accepts host-correlated exact-match observation of semantic-preflight bytes in Pi agent state."
read_when:
  - "Implementing or reviewing Decision 98."
type: "adr"
status: "accepted"
decision_id: 98
---
# ADR — Correlated Pi agent-prompt observation v0

## Status

Accepted for Decision 98 after strict three-lane convergence on RFC revision `pi-ontology-workflows-agent-prompt-observation-v0-r2`.

Frozen review identity:

- commit `427d8c62bb110812e9946c609c59e1ab14313b95`;
- aggregate `7ef2e79c2e42ae333e9be90623423363985df9814173e601027ff73df57ab4b0`;
- controlling synthesis `docs/project/semantic-pi-agent-prompt-retention-observation-v0-review-synthesis-r1.md`;
- final lane verdicts `ready_for_adr`: `dispatch-1785563958202`, `dispatch-1785563958203`, and `dispatch-1785563958203-1`.

The frozen r2 RFC is normative in full. This ADR summarizes rather than weakens its token uniqueness, event freezing, readback precedence, lifecycle clearing, owner re-pinning, protected surfaces, rollout, and rollback requirements.

## Context

Decision 89 proves exact package-local pre-return preparation but cannot correlate that preparation with Pi's assigned agent-state prompt. A package-only `agent_start` observer is unsafe because asynchronous preflights may overlap before Pi marks a run active, and existing events expose no shared run identity. Whole-prompt mismatch also cannot establish that a semantic contribution was removed.

## Decision

Adopt one minimal host correlation/readback contract and one bounded package observer.

### Host contract

Pi adds capability `prompt.agent-state.observation.v1`. Before each prompt execution's pre-start chain, the host creates one opaque process-local `promptRunToken`. Tokens are unique among concurrently alive executions, unstable across process/session replacement, and identical only across that execution's `before_agent_start` and new `agent_prompt_ready` events.

`agent_prompt_ready` fires after the complete pre-start chain and assignment to Pi agent state, before the corresponding provider turn. Its frozen event carries the matching token and exact assigned `systemPrompt`. The host freezes the extended `before_agent_start` event values as well. The seam attests no provider invocation or transmission.

### Package contract

`pi-ontology-workflows` keeps one latest closure-local state:

```text
empty -> prepared(token) -> terminal(exact_match|mismatch)
```

A newer preparation replaces the slot; nonmatching ready tokens are ignored. Tokens are never exposed, digested into public records, logged, or persisted. There is no queue, history, timestamp, allocator, database, file, or session entry.

Terminal `exact_match` means the entire agent-state prompt at the correlated host seam equals the package-prepared whole prompt by exact UTF-8 byte length and domain-separated digest. `mismatch` means only that the whole prompts differ; contribution survival remains unknown.

The existing TUI command gains deterministic `/ontology-preflight observation` readback for unsupported-host, disabled, enabled-none, prepared, exact-match, and mismatch states. The literal outputs and precedence in frozen RFC r2 are mandatory: unsupported-host precedes disabled; otherwise the runtime validates current generation/grant/cwd/compatibility, clears stale state, and selects prepared, terminal, or enabled-none. Readback is TUI-only and non-persistent. Output includes fixed protocol/outcome/negative-claim text only—no prompt-derived digest, length, token, prompt text, path, session, provider, or model identity.

Reset, shutdown, disable, stale/expired grant, successful grant replacement, mode drift, invalid generation/request/grant/cwd/compatibility, producer/validation failure, non-append output, and unsupported-host detection clear the slot as specified by r2. Nonmatching or repeated ready events never rewrite a terminal observation.

### Implementation ownership

- Pi owner: capability, event, correlation, ordering, docs/types/tests.
- `pi-extensions` owner: extracted package state/record/readback and package tests.
- runtime operator: exact settings replacement, start/reload, live canary, and restoration.
- ROCS semantic owner: B0 retrieval evaluation.
- DSPx/Oracle: B1/B2 empirical evaluation.
- AK: task/decision/evidence lineage only.

Host, package, deterministic integration, live TUI canary, and empirical work use separate tasks and evidence.

Each task re-pins its owner's then-current default line before mutation. H0 lands first. P0 preserves package manifests and lockfiles and uses a narrowly reviewed structural compatibility type inside the RFC-authorized source surfaces to describe `agent_prompt_ready`; it may not pretend the pinned pre-H0 peer type already contains that event. Runtime use still fails closed unless the immutable H0 capability token is present. Publishing or rebinding a Pi dependency is outside Decision 98.

## Consequences

- A small Pi-host change is required; existing capability tokens are insufficient.
- The observation becomes meaningfully correlated without retaining multiple runs.
- Omission is allowed when the latest slot is replaced; misattribution is not.
- `preflight-runtime.ts` does not grow beyond its readability budget; state logic is extracted.
- Decision 89 remains valid predecessor evidence and is not retroactively widened.
- No provider/model, semantic-benefit, default, publication, production, or fleet claim follows.

## Rollout

1. H0 host capability on the current Pi-owner line, with frozen-event, concurrent-token, assignment-order, pre-provider, lifecycle, and compatibility tests.
2. P0 package implementation on the current live package line, preserving manifests, lockfiles, entrypoint, release behavior, and semantic-delivery surfaces; the structural event type stays inside the RFC-authorized state/runtime source.
3. R1a no-install deterministic host/package integration harness loading exact candidates with a faux provider and no external model use.
4. R1b separately authorized TUI canary with exactly one pinned provider/model call. It proves exact host/package identity, one configured and loaded package across global/project scopes, unsuffixed command provenance, default-off and terminal/reset states, and exact settings rollback. Prepared is harness-only because live TUI exposes no scheduling boundary for it.
5. B0 retrieval relevance before B1/B2 behavioral evaluation.

R1b is engineering dogfood, not a benefit study.

## Rollback

Host and package commits revert independently. Runtime rollback disables the grant, restores exact prior settings bytes/mode/order/source, creates a fresh Pi generation, verifies the prior sole package and unsuffixed command/tool provenance, proves no candidate protocol or handler remains loaded, and leaves unrelated caches, worktrees, sessions, and repositories untouched.

## Non-authorization

This ADR does not implement code, install or reload Pi, enable a grant, call a provider/model, run dogfood, publish, activate defaults, or authorize production/fleet use. Post-ADR implementation and validation/rollout/rollback plans must be accepted through AK before owner tasks begin.
