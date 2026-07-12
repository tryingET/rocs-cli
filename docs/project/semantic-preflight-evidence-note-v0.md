---
summary: "Current-code, host-contract, and adversarial evidence supporting the deterministic semantic discovery and Pi preflight decision."
read_when:
  - "Reviewing evidence behind the semantic discovery/preflight RFCs."
  - "Checking whether the proposal addresses current implementation facts rather than session intuition."
type: "evidence"
status: "proposed"
---

# Evidence Note — Semantic Discovery and Pi Preflight v0

## Evidence basis

This note supports the [problem brief](semantic-preflight-problem-brief-v0.md) and [primary RFC](semantic-discovery-protocol-v0.md).

The architecture was derived from targeted inspection of both owner repositories, installed Pi host documentation/runtime types, current package tests, and two independent adversarial review passes.

Session JSONL reconstruction was not needed: the compacted session context plus repository and host sources contained the necessary claims, and every material architecture claim below was checked against an owner file or executable validation surface.

## ROCS current-state evidence

- `src/rocs_cli/pack.py::build_pack` provides deterministic exact-ID graph expansion with depth, relation, document, and byte limits. It does not discover IDs from task language.
- `src/rocs_cli/repo_view.py::load_repo_view` is the shared resolved-layer/document loading seam.
- `src/rocs_cli/id_index.py::build_id_index` emits IDs, kinds, labels, layers, and logical paths, but no task-language ranking contract or complete corpus identity.
- `src/rocs_cli/index_cache.py` is a parsed-document cache and may write cache state.
- `src/rocs_cli/intelligence.py` binds selected context inputs for proposal workflows; that capsule is not a Semantic Release Capsule.
- `src/rocs_cli/contracts.py` schema 3 declares closed operation effects and authority artifacts but does not negotiate request/result/algorithm schema versions.
- `tests/test_wave1_contracts.py` enforces parser/contract closure.

## Pi package current-state evidence

- `extensions/ontology-workflows.ts` registers two `session_start` handlers and one `before_agent_start` handler.
- Startup status inspection can execute ROCS summary and validation with long process timeouts.
- `isOntologyRelevantPrompt` uses a keyword regex and injects a static workflow hint rather than task-sensitive semantic candidates.
- `src/core/inspect.ts` search calls `rocs.build`, reads generated resolve/index artifacts and every indexed document, then ranks them through `scoreDoc` in TypeScript.
- `src/adapters/rocs-cli.ts` currently resolves package-root wrappers, a non-frozen core fallback, and bare ambient `rocs`; it inherits the process environment.
- `src/ports/rocs-port.ts` has summary/validate/build/pack but no discovery protocol or abort signal.
- The package has no prompt-result cache, in-flight coalescing, generation token, subprocess cancellation, or stale-completion guard.
- `extensions/ontology-workflows.ts` is already above the default readability budget, so new state/formatting logic belongs under `src/`.

## Pi host-contract evidence

Installed Pi documentation and runtime types establish:

- `session_start` occurs before resource discovery and carries startup/reload/new/resume/fork reasons;
- `before_agent_start` receives the expanded prompt and chained system prompt;
- returned `systemPrompt` replaces the current prompt, so append behavior must return the complete chained string;
- returned custom messages persist and can accumulate, making them unsuitable for turn-local automatic preflight;
- multiple handlers run sequentially and later handlers may replace earlier prompt changes;
- there is no documented handler priority or mandatory preflight gate;
- extension exceptions are reported but do not provide fail-closed enforcement.

These claims still require the implementation-phase host capability spike because observed installed behavior is not equivalent to a durable compatibility guarantee.

## Adversarial findings incorporated

The design was revised to address:

1. system-prompt privilege escalation from arbitrary ontology prose;
2. automatic execution of hostile repository launchers;
3. conflated invocation/applicability/retrieval state;
4. incomplete identity when only selected candidates are digested;
5. undeclared cache effects;
6. missing protocol-version negotiation;
7. underspecified Unicode/tokenization/tie-break behavior;
8. unbounded Pi hook latency and process-tree cancellation;
9. circular/stale cross-turn cache identity;
10. marker spoofing and handler-order dependence;
11. advisory ambiguity that cannot enforce user resolution;
12. corpus-loading resource exhaustion;
13. inherited environment and implicit `.env` drift;
14. duplicate Pi/ROCS ranking authorities;
15. multi-intent prompts mistaken for single-winner ambiguity;
16. conflation of intelligence capsules with release capsules;
17. default rollout before adoption authority.

A final document review additionally corrected:

- caller request versus resolved effective request identity;
- development opt-in scope and reset behavior;
- release-runtime trust-root deferral;
- exact-ID pack ownership;
- reject-versus-truncate limit semantics;
- hostile filesystem snapshot cases;
- the requirement for a Pi host capability spike.

## Validation already performed

- ROCS strict documentation validation passed.
- Pi package structure validation passed.
- Pi package test suite passed: 32 tests.
- Pi packaging/release checks completed; the existing-version registry guard was expected and handled by the package script.
- Cross-repo links and `git diff --check` passed.
- ROCS `uv.lock` remained at SHA-256 `2faf5bc9a99011b4eeb7c99f3464ee6bdd6f720173c954a4264f246cdb5272f9`.

## Evidence limitations

- No ROCS discovery implementation or live Pi preflight exists yet.
- The production Semantic Release Capsule and consumer adoption protocol remains undecided.
- No production runner trust root exists.
- No latency or agent-outcome evidence exists yet.
- Existing Pi package test coverage does not exercise the proposed lifecycle behavior.

These limitations block implementation claims, not pre-ADR review of the target boundary.
