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

The accepted ADR and frozen RFC r2 are normative. Every owner task resolves current `origin/main`, records commit/tree/version, and starts from a clean isolated worktree. Observed refs are evidence only. Package work preserves the then-current package version/manifests and reapplies only accepted Decision-89 behavior when absent.

## H−1 — current-line host-capability substrate

Owner: `/home/tryinget/ai-society/softwareco/contrib/pi-mono`.

Create a separate task from current owner main. Rederive the substrate using local `b4bbbc080` as evidence; do not use stale `5be4473cc` as base and exclude unrelated `0e773d7b0` model-completion work.

H−1 implements the exact existing capability set:

```text
prompt.system.chain.v1
session.lifecycle.reason.v1
ui.mode.v1
ui.confirm.timeout.v1
session.shutdown.v1
```

It includes current-line context plumbing, restricted project-trust contexts, stale-context guards, shortcut/print/RPC shutdown behavior, confirm countdown semantics, immutable capability identifiers, exports, `docs/extensions.md`, `CHANGELOG.md`, and new focused tests `test/host-capabilities.test.ts` and `test/host-capabilities-lifecycle.test.ts`. Do not expand the over-budget runner test.

New files must satisfy code `<=500 LOC/51200 bytes` and tests `<=1000 LOC/81920 bytes` through the same `wc -l`/`wc -c` hard checks used by P0. For unavoidable touched brownfield files—currently `src/modes/interactive/interactive-mode.ts`, `src/core/extensions/runner.ts`, `src/core/extensions/types.ts`, and any existing over-budget test—record exact before/after LOC/bytes and an owner-scoped no-unrelated-growth exception; prefer new focused tests.

Exact validation:

```bash
cd <H-1>/packages/coding-agent
node ../../node_modules/vitest/dist/cli.js --run test/host-capabilities.test.ts test/host-capabilities-lifecycle.test.ts
cd <H-1>
npm run check
./test.sh
git diff --check <parent>..<candidate>
git status --short
```

H−1 has two reviews and disposable `git revert <H−1>` validation whose resulting tree equals the recorded parent before named gates run.

## H0 — correlated agent-prompt-ready event

Start from accepted H−1. Add `prompt.agent-state.observation.v1`, unique opaque per-execution `promptRunToken`, token snapshots on pre-start events, and new `agent_prompt_ready` after assignment.

Exact order:

```text
allocate token
-> await complete before_agent_start chain(token)
-> assign agent.state.systemPrompt
-> await agent_prompt_ready(token, assigned prompt)
-> preflightResult(true)
-> _runAgentPrompt()
```

Token uniqueness is limited to concurrently alive executions within one host process/runtime generation. The host does not automatically copy it to host-owned session/provider/log/error surfaces; extensions remain responsible for what they observe.

Compatibility semantics:

- every `before_agent_start` outer envelope is shallow-frozen;
- primitive token and prompt snapshots cannot be reassigned;
- nested `systemPromptOptions` retains existing shared mutability and may remain visible across handlers;
- `agent_prompt_ready` is a shallow-frozen envelope containing only immutable strings;
- isolation claims apply only to outer primitive snapshots, not nested options.

H0 touches bounded capability/event/type/runner/session/exports/docs/changelog surfaces and new focused tests. Apply the same numeric new-file budget checks and exact before/after no-unrelated-growth exceptions to unavoidable brownfield files; do not grow over-budget tests.

Exact command form:

```bash
cd <H0>/packages/coding-agent
node ../../node_modules/vitest/dist/cli.js --run test/agent-prompt-ready.test.ts test/host-capabilities.test.ts
cd <H0>
npm run check
./test.sh
git diff --check <H-1>..<H0>
git status --short
```

Two reviews and disposable `git revert <H0>` validation must produce the accepted H−1 tree and pass the same gates.

## P0 — package implementation on current live lineage

After H0 acceptance, start from then-current `pi-extensions/origin/main`. Reapply only accepted Decision-89 commits/behavior when absent. Preserve current version, manifest, lock, entrypoint, release metadata, semantic-delivery surfaces, request epochs, TUI behavior, and runner hardening.

Allowed source/tests:

- new `src/semantic/agent-prompt-observation-state.ts`;
- `src/semantic/handler-observation.ts`;
- bounded `src/semantic/preflight-runtime.ts` wiring;
- new `tests/agent-prompt-observation-state.test.ts`, `tests/agent-prompt-observation-registration.test.ts`, and other new focused files;
- zero line growth in the existing near-budget Decision-89 lifecycle test.

Use a structural event type inside RFC-authorized sources; manifests/lock remain unchanged. Unsupported hosts preserve ordinary semantic-preflight behavior and report unsupported observation.

Malformed events are exact:

- missing/non-string/nonmatching token: ignore without reading prompt;
- matching token with missing/non-string/invalid-Unicode prompt: clear slot, emit no record, and produce no token/prompt-bearing error or log;
- malformed/repeated event after terminal: no rewrite.

Token privacy tests prove absence from public record keys/digest inputs/errors/readback/log/session/evidence and token-only invariance of public bytes/record digest.

Hard budget command records each touched path and enforces code `<=500 LOC && <=51200 bytes`, tests `<=1000 LOC && <=81920 bytes` using `wc -l` and `wc -c`; no warn-only gate substitutes. Run focused tests, quality/full/package/release/AST/diff/clean gates, two reviews, and disposable `git revert <P0>` validation.

## R1a — exact deterministic no-install integration

Owner: Pi H0 repository. Create one R1a commit whose parent is exact accepted H0 and whose only delta is:

```text
packages/coding-agent/test/decision98-agent-prompt-integration.test.ts
```

Required environment:

```text
DECISION98_P0_PACKAGE_ROOT
DECISION98_P0_COMMIT
DECISION98_P0_PACKAGE_TREE
```

The test verifies Git identity, resolves `<root>/extensions/ontology-workflows.ts`, and loads it through `DefaultResourceLoader` using `additionalExtensionPaths` with ordinary discovery disabled. Use `createAgentSession` and the suite faux provider with fixed provider/model/API, timestamps, chunks, and token sizes.

Exact command:

```bash
cd <R1a>/packages/coding-agent
DECISION98_P0_PACKAGE_ROOT=<abs> \
DECISION98_P0_COMMIT=<commit> \
DECISION98_P0_PACKAGE_TREE=<tree> \
node ../../node_modules/vitest/dist/cli.js --run test/decision98-agent-prompt-integration.test.ts
```

Exercise disabled/enabled-none/prepared, match/mismatch, reversed overlap, malformed/nonmatching/repeated events, reset, literal output, and ready-before-provider. The unsupported-host case is explicitly package compatibility evidence: the same test directly invokes the loaded package registration/handler with a capability-absent synthetic context; it is not described as an end-to-end H0 host run. No settings/install/network/real model. Review the one-file delta and preserve exact R1a commit.

## R1b — isolated live TUI deterministic-provider canary

Use source-local H0/P0 candidates; never mutate normal Pi executable or user/project settings. Prepare dependencies with `npm ci --ignore-scripts` under the heavy-job wrapper, record Node/npm/lock/output, then run the explicit offline owner build (`npm run build`) and hash `dist/cli.js` plus required artifacts.

Create one reviewed R1b source commit whose parent is exact R1a and whose only delta is the canary extension at:

```text
packages/coding-agent/examples/extensions/decision98-canary-provider.ts
```

It registers pinned local provider/model `decision98-canary/deterministic-noop-v1`, performs no network or credential access, allows exactly one stream invocation, fails before a second invocation, emits fixed output/timestamps/chunks, and provides a TUI provenance command that reports same-process `pi.getCommands()` sourceInfo, candidate extension realpaths, request count, and absence of other ontology sources without leaking settings or prompts.

Launch from a pinned cwd with no project resources:

```text
PI_CODING_AGENT_DIR=<private managed profile>
node <H0>/packages/coding-agent/dist/cli.js \
  --no-extensions --no-approve --no-tools \
  -e <absolute P0 package root> \
  -e <absolute reviewed canary-provider.ts> \
  --provider decision98-canary --model deterministic-noop-v1
```

The private profile explicitly sets retry disabled, provider max retries zero, compaction disabled, and contains no queued messages. `--no-extensions` disables discovered sources but preserves explicit `-e` candidates. Same-process provenance must show one unsuffixed ontology command/source before the request.

Live states: default-off/disabled, one confirmed grant, enabled-none, one semantic prompt, terminal match/mismatch, disable/reset. Prepared is R1a-only. No tools/pack/retry/follow-up/second request. Any mismatch or stop condition triggers immediate rollback and separate investigation.

Rollback terminates the process, proves normal settings/executable unchanged and no candidate process remains, preserves sanitized receipts, and removes only owned private scratch after liveness checks.

## B0 — ROCS-owned semantic relevance

Before execution, commit/review an immutable preregistration for at least 40 dual-annotated prompts balanced across named strata, with dataset/gold digest, adjudication, exact coordinates, numerical floors, exclusions, cold/warm latency policy, and timeout censoring. ROCS owns execution and analysis. No DSPx authority or provider/model use.

## Rollback dependency and completion

When all source stages exist, revert the Pi lineage in descendant order: R1b canary source, then R1a harness, then H0, then H−1. P0 is in a separate repository and may revert independently, but must be removed before any integration/runtime verification that assumes it. H0 is never reverted while R1a/R1b descendants remain. Each disposable revert tree must equal its recorded parent and pass named gates; never reset owner lines.

After H−1/H0/P0/R1a/R1b/rollback/B0 acceptance, create a KES-owner task and require reviewed accepted artifact/knowledge ID. Decision-98 closure cites reviews for every stage and KES. B1/B2/publication/defaults/production/fleet remain new work.
