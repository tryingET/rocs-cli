---
summary: "Post-ADR owner plan for Decision 98 host correlation, package observation, and dogfood."
read_when:
  - "Implementing Decision 98 after ADR acceptance."
type: "implementation_plan"
status: "proposed"
decision_id: 98
---
# Implementation plan — correlated Pi agent-prompt observation v0

## Authority

Governing ADR: `docs/adr/2026-08-01-correlated-pi-agent-prompt-observation-v0.md`. Frozen RFC r2 remains normative.

This plan sequences separate owner tasks. Acceptance of the plan does not itself mutate Pi, packages, settings, runtime, provider/model, or empirical authority.

## Baselines to re-pin

Observed planning baselines:

- Pi owner: `/home/tryinget/ai-society/softwareco/contrib/pi-mono` `origin/main` `4488ad55c18f07ae89a489096c90de8667b3adfb`, coding-agent `0.83.0`;
- local host-capability predecessor: `5be4473cc` on a branch 1 ahead/1222 behind owner main; it is evidence to rederive, never the H0 base;
- package owner live-lineage candidate: branch commit `96f3b699b77b941522e0cada76672276919e2d6e`, package tree `396630b4cf329d2e1a2a03fa9e4cb219381e89eb`, version `0.2.0`.

Every task rechecks current owner default and uses a clean isolated worktree. If relevant owner files changed, rebase/rederive and re-review; never install a stale/divergent checkout by branch name alone.

## H0 — Pi host capability and correlation event

Owner: `softwareco/contrib/pi-mono`.

Create one bounded task from current `origin/main`. Re-derive the existing immutable host-capability substrate from local commit `5be4473cc` only where current owner main lacks it, then add:

- capability `prompt.agent-state.observation.v1`;
- opaque unique `promptRunToken` creation before each `before_agent_start` chain;
- token on `BeforeAgentStartEvent`;
- frozen `AgentPromptReadyEvent` carrying matching token and assigned `systemPrompt`;
- `agent_prompt_ready` extension registration/dispatch;
- awaited dispatch after assignment and before `_runAgentPrompt()`;
- exports, documentation, and deterministic tests.

Expected owner surfaces are bounded around:

- coding-agent host-capability/context plumbing required by the current line;
- `packages/coding-agent/src/core/extensions/types.ts`;
- `packages/coding-agent/src/core/extensions/runner.ts`;
- `packages/coding-agent/src/core/agent-session.ts`;
- extension type/index exports;
- `packages/coding-agent/docs/extensions.md`;
- focused host-capability, runner, session-order, overlap, and compatibility tests.

Token generation must be dependency-free, process-local, collision-safe for concurrently alive executions, and opaque. No token is persisted to session JSONL or provider payload. Existing extensions receive the additive field/event without behavior change.

H0 completion requires one exact owner commit, current-line ancestry, focused/full owner gates, docs checks, and two independent reviews.

## P0 — package state and deterministic readback

Owner: `softwareco/owned/pi-extensions`, package `pi-ontology-workflows`.

Begin only after H0 acceptance. Re-pin current `origin/main`, then reapply/merge the accepted Decision-89 live-lineage package tree if not yet present. Preserve version `0.2.0`, manifests, lockfiles, entrypoint, release metadata, semantic-release-delivery files/tests, request-epoch fencing, TUI behavior, and runner hardening.

Allowed implementation surfaces:

- new `src/semantic/agent-prompt-observation-state.ts`;
- `src/semantic/handler-observation.ts`;
- bounded wiring in `src/semantic/preflight-runtime.ts` without increasing its 500-LOC budget;
- focused state/record/lifecycle/source-registration tests.

Use a local structural event type inside those source surfaces because the protected package dependency/lock remains pre-H0. Runtime behavior must require the immutable H0 capability token and otherwise report `unsupported-host` without changing ordinary semantic-preflight behavior.

Implement exactly the r2 one-slot transitions, private token handling, exact whole-prompt match/mismatch record, deterministic command outputs/precedence, stale validation, clearing paths, and non-disclosure constraints.

P0 completion requires focused tests, package quality/full gate, preserved manifests/lock/package version, exact filescope, source-size gate, and two independent reviews.

## R1a — deterministic no-install integration dogfood

Owners: Pi host and package owners; evidence attached through one AK task.

Use an isolated SDK/runner test harness with exact H0 and P0 commits and a deterministic faux provider. Do not edit user/project settings or install a package.

Exercise:

- unsupported old host;
- disabled and enabled-none states;
- prepared state under a controlled scheduling barrier;
- exact match and mismatch;
- overlapping prompt runs with reversed completion/event order;
- nonmatching and repeated ready events;
- reset/disable/session replacement;
- command privacy and literal outputs;
- event-before-provider ordering.

Record exact host/package commits, trees, test harness commit, commands, outputs, and negative external-model/network facts.

## R1b — live TUI canary

Owner: runtime operator, under a fresh task explicitly authorizing one pinned provider/model call.

Before mutation:

- identify the active `PI_CODING_AGENT_DIR` and all global/project settings in scope;
- save exact settings bytes, mode, owner, and SHA-256 under managed `TMPDIR`;
- record all configured package source strings, resolved realpaths, commits, package trees, versions, and command/tool provenance;
- record the exact prior Pi host executable/version/commit and restoration command;
- preserve the prior package source and candidate worktree immutably;
- preauthorize rollback independent of candidate loading.

Replace rather than append the old ontology package source. Prove exactly one configured and loaded package and one unsuffixed ontology command/tool source. Start a fresh Pi generation using H0 and P0 candidates.

Live sequence:

1. verify `unsupported-host` is absent and protocol r2 responds while default-off;
2. verify `disabled`, then enable one fresh TUI development grant;
3. verify `enabled outcome=none`;
4. send one bounded semantic task using the pinned provider/model;
5. after settlement read `terminal exact_match|mismatch` and retain the truthful result;
6. run one ordinary exact-ID pack follow-up if the candidate set calls for it;
7. disable and verify disabled/reset;
8. execute rollback even after success unless a separately authorized retention decision says otherwise.

Prepared is not a live readback gate. R1b proves engineering integration only, not semantic benefit.

## B0 — semantic relevance dogfood

Owner: ROCS semantic owner; DSPx/Oracle analyzes without provider/model use.

Use at least 40 balanced dual-annotated prompts and fixed semantic/runtime coordinates. Measure recall@k, false matches, ambiguity/no-match correctness, deterministic replay, block size, timeout/unavailable rate, and latency against the 750 ms budget. Stop before B1 if preregistered floors fail.

## Completion boundary

Decision 98 implementation is complete only when H0, P0, R1a, R1b, rollback, and B0 each have exact owner evidence and independent review. B1/B2, publication, defaults, production, and fleet rollout remain new work.
