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

## Context

Decision 89 proves exact package-local pre-return preparation but cannot correlate that preparation with Pi's assigned agent-state prompt. A package-only `agent_start` observer is unsafe because asynchronous preflights may overlap before Pi marks a run active, and existing events expose no shared run identity. Whole-prompt mismatch also cannot establish that a semantic contribution was removed.

## Decision

Adopt one minimal host correlation/readback contract and one bounded package observer.

### Host contract

Pi adds capability `prompt.agent-state.observation.v1` and an immutable process-local `promptRunToken` shared between `before_agent_start` and new `agent_prompt_ready`.

`agent_prompt_ready` fires after the complete pre-start chain and assignment to Pi agent state, before the corresponding provider turn. It carries the token and exact assigned `systemPrompt`. It attests no provider invocation or transmission.

### Package contract

`pi-ontology-workflows` keeps one latest closure-local state:

```text
empty -> prepared(token) -> terminal(exact_match|mismatch)
```

A newer preparation replaces the slot; nonmatching ready tokens are ignored. Tokens are never exposed, digested into public records, logged, or persisted. There is no queue, history, timestamp, allocator, database, file, or session entry.

Terminal `exact_match` means the entire agent-state prompt at the correlated host seam equals the package-prepared whole prompt by exact UTF-8 byte length and domain-separated digest. `mismatch` means only that the whole prompts differ; contribution survival remains unknown.

The existing TUI command gains deterministic `/ontology-preflight observation` readback for unsupported-host, disabled, enabled-none, prepared, exact-match, and mismatch states. Output includes fixed protocol/outcome/negative-claim text only—no prompt-derived digest, length, token, prompt text, path, session, provider, or model identity.

### Implementation ownership

- Pi owner: capability, event, correlation, ordering, docs/types/tests.
- `pi-extensions` owner: extracted package state/record/readback and package tests.
- runtime operator: exact settings replacement, start/reload, live canary, and restoration.
- ROCS semantic owner: B0 retrieval evaluation.
- DSPx/Oracle: B1/B2 empirical evaluation.
- AK: task/decision/evidence lineage only.

Host, package, deterministic integration, live TUI canary, and empirical work use separate tasks and evidence.

## Consequences

- A small Pi-host change is required; existing capability tokens are insufficient.
- The observation becomes meaningfully correlated without retaining multiple runs.
- Omission is allowed when the latest slot is replaced; misattribution is not.
- `preflight-runtime.ts` does not grow beyond its readability budget; state logic is extracted.
- Decision 89 remains valid predecessor evidence and is not retroactively widened.
- No provider/model, semantic-benefit, default, publication, production, or fleet claim follows.

## Rollout

1. H0 host capability with deterministic faux-provider tests.
2. P0 package implementation on the live lineage.
3. R1a deterministic host/package integration harness without external model use.
4. R1b separately authorized TUI canary with exactly one pinned provider/model call and exact settings rollback.
5. B0 retrieval relevance before B1/B2 behavioral evaluation.

R1b is engineering dogfood, not a benefit study.

## Rollback

Host and package commits revert independently. Runtime rollback disables the grant, restores exact prior settings bytes/order/source, creates a fresh Pi generation, verifies prior sole package provenance and absence of the candidate protocol, and leaves unrelated caches, worktrees, sessions, and repositories untouched.

## Non-authorization

This ADR does not implement code, install or reload Pi, enable a grant, call a provider/model, run dogfood, publish, activate defaults, or authorize production/fleet use. Post-ADR implementation and validation/rollout/rollback plans must be accepted through AK before owner tasks begin.
