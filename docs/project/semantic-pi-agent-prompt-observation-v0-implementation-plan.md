---
summary: "Post-ADR owner plan for Decision 98 host correlation, package observation, and isolated dogfood."
read_when:
  - "Implementing Decision 98 after ADR acceptance."
type: "implementation_plan"
status: "proposed"
decision_id: 98
---
# Implementation plan — correlated Pi agent-prompt observation v0

## Authority and re-pinning

Governing ADR: `docs/adr/2026-08-01-correlated-pi-agent-prompt-observation-v0.md`; frozen RFC r2 is normative.

Observed refs are discovery evidence, not mutation bases. Every owner task resolves current `origin/main`, records commit/tree/version, and starts from a clean isolated worktree. Package work preserves the then-current package version and manifests; it does not restore the historical `0.2.0` tree. If owner files drift, rederive and re-review.

## H−1 — current-line host-capability substrate

Owner: `/home/tryinget/ai-society/softwareco/contrib/pi-mono`.

Current owner main lacks the local immutable host-capability substrate required by semantic preflight. Create a separate task from current `origin/main` and rederive only that substrate using local commit `b4bbbc080` as evidence. Do not use stale `5be4473cc` as the implementation base and exclude unrelated successor `0e773d7b0` host-owned model completion.

H−1 includes current-line context plumbing, restricted project-trust contexts, stale-context guards, shortcut/print/RPC shutdown behavior, immutable capability identifiers, docs, exports, and tests required by the accepted substrate. It has its own independent review and revert plan. H0 rollback preserves H−1; H−1 reverts independently to its recorded owner-main parent.

## H0 — correlated agent-prompt-ready event

Start from accepted H−1. Add:

- capability identifier `prompt.agent-state.observation.v1`;
- opaque unique `promptRunToken` allocation before each prompt execution's pre-start chain;
- token on each freshly constructed `BeforeAgentStartEvent` snapshot;
- `AgentPromptReadyEvent` with matching token and assigned `systemPrompt`;
- `agent_prompt_ready` registration/dispatch/exports/docs;
- awaited order:

```text
allocate token
-> await complete before_agent_start chain(token)
-> assign agent.state.systemPrompt
-> await agent_prompt_ready(token, assigned prompt)
-> preflightResult(true)
-> _runAgentPrompt()
```

Token semantics are limited to concurrently alive executions in one host process/runtime generation. The host does not automatically copy tokens to host-owned session messages/entries, provider payloads, logs, or errors. Extensions can observe the token and remain responsible for their own behavior.

Compatibility freezing is exact: each `before_agent_start` handler receives a fresh event envelope and immutable primitive token/system-prompt snapshots; existing `systemPromptOptions` nested mutability remains unchanged. `agent_prompt_ready` is a shallow-frozen envelope containing only immutable strings. Mutation of one handler's local event cannot change the host token or values supplied to another handler. Add explicit mutation tests.

Expected touched surfaces include bounded host-capability plumbing plus coding-agent extension types/runner/session, exports, docs, changelog, and new focused tests. Do not grow already over-budget tests; add focused files. Record owner-scoped brownfield exceptions for unavoidable edits to over-budget host files.

Validation commands from current owner policy:

- focused Vitest files from `packages/coding-agent`;
- root `npm run check`;
- root `./test.sh`;
- `git diff --check` and exact clean-worktree verification.

H0 completion requires exact commit/tree, current-line ancestry, full gates, two independent reviews, and an explicit `git revert <H0>` rehearsal/plan that returns to accepted H−1 without resetting branches.

## P0 — package implementation on current live lineage

Owner: `softwareco/owned/pi-extensions`, package `pi-ontology-workflows`.

After H0 acceptance, start from then-current `origin/main`. Reapply only the accepted Decision-89 observation commits/behavior where absent; do not replace the current package tree. Preserve current package version, manifest, lockfile, entrypoint, release metadata, semantic-release-delivery surfaces, request-epoch fencing, TUI behavior, and runner hardening.

Allowed source:

- new `src/semantic/agent-prompt-observation-state.ts`;
- `src/semantic/handler-observation.ts`;
- bounded wiring in `src/semantic/preflight-runtime.ts` without exceeding 500 LOC;
- new focused state/record/registration/lifecycle test files rather than growing a near-budget lifecycle file.

Use a narrow structural event type inside these RFC-authorized sources; manifests/lockfiles remain unchanged. Runtime use fails closed unless the H0 capability identifier is present.

Implement the exact one-slot transitions, private token behavior, exact whole-prompt match/mismatch record, literal readback/precedence, stale validation, and clearing rules. Tests must prove the token is absent from all public record keys/errors/readback and that changing only the token leaves public record bytes and `record_digest` unchanged.

P0 completion requires focused tests, hard touched-file budget check, quality/full package gate, preserved current manifest/lock/version, exact scope, two reviews, and explicit `git revert <P0>` gates. P0 rollback returns to its recorded current-line parent without resetting owner branches.

## R1a — deterministic no-install cross-repo integration

Owner surface: a new focused test under the H0 Pi worktree, for example `packages/coding-agent/test/decision98-agent-prompt-integration.test.ts`, executed by a fresh R1a AK task.

The test accepts exact P0 extension entrypoint/package root through a required environment path, verifies its Git commit/package tree before load, and loads it through Pi's real extension loader/additional-path mechanism—not by copying source or changing settings. It runs against exact H0 using the coding-agent suite harness and faux provider with fixed provider/model/API, timestamps, output chunks, token size, and no `Date.now()`/`Math.random()` dependence.

Exercise unsupported old host, disabled/enabled-none/prepared, exact match/mismatch, reversed overlap, nonmatching/repeated events, reset/disable/replacement, literal private command outputs, and ready-before-provider ordering. No external network/model and no install.

## R1b — isolated live TUI canary

Use source-local candidates; do not mutate the normal Pi executable or user/project settings.

Prepare dependencies with lock-frozen `npm ci` in clean H0 and P0 worktrees under the workstation heavy-job wrapper when required. Record Node/npm versions, lock hashes, install commands/results, candidate commits/trees, and post-install cleanliness; then protect candidates from mutation.

Build H0 and launch exactly:

```text
PI_CODING_AGENT_DIR=<private managed scratch profile>
node <H0>/packages/coding-agent/dist/cli.js \
  -e <absolute P0 package root> \
  --no-tools \
  <explicit pinned provider/model arguments>
```

The R1b task records the final argv/environment allowlist, executable/build artifact hashes, package root, and isolated profile path. It inventories normal global/project settings and proves they remain byte-identical but does not install into them. Temporary `-e` loading is verified through fixed protocol output plus command/tool `sourceInfo` obtained by a no-provider RPC/SDK provenance probe against the same candidate before the TUI call.

Authorize exactly one provider request, not one agent task. Disable tools; instrument provider-request starts and abort/rollback before request two, retry, compaction continuation, follow-up, or tool call. R1b performs no pack follow-up; pack behavior belongs to R1a.

Live states: default-off/disabled, enable one confirmed grant, enabled-none, one semantic prompt, terminal exact-match or mismatch, disable/reset. Prepared remains harness-only. Any mismatch is recorded, forward work stops, and rollback executes before a separate investigation task.

Rollback terminates the candidate process, verifies normal settings/executable were unchanged, proves no candidate process remains, and preserves only sanitized hashes/receipts. Owned isolated profile/build scratch may be removed only after process liveness and evidence preservation are proved.

## B0 — ROCS-owned semantic relevance dogfood

ROCS owns both execution and analysis. Before execution, a reviewed immutable B0 preregistration records dataset digest, at least 40 balanced strata, dual annotation/adjudication, exact runtime/semantic coordinates, metrics/floors, exclusions, cold/warm latency treatment, and timeout censoring. No DSPx/Oracle authority is implied; later handoff requires a separate task.

Measure recall@k, false matches, ambiguity/no-match correctness, deterministic replay, rendered size, timeout/unavailable rate, and p50/p95 latency against 750 ms. Stop before B1 if floors fail.

## KES and completion

After H−1/H0/P0/R1a/R1b/rollback/B0 acceptance, create a KES-owner task. It records accepted learning identities for divergent-lineage preflight, event-correlation necessity, isolated canary practice, and B0 result, with independent review. Decision 98 completion cites reviews for every stage plus the accepted KES artifact/knowledge ID.

B1/B2, publication, defaults, production, and fleet rollout remain new decisions/tasks.
