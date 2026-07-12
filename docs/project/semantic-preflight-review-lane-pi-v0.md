---
summary: "Decision:52 strict review lane for Pi prompt trust, runner security, hook lifecycle, cancellation, and operator UX."
read_when:
  - "Reviewing decision:52 attempt 1 Pi findings."
  - "Revising the semantic preflight adapter before ADR."
type: "review_memo"
decision_id: 52
review_outcome: "revise_rfc"
---

# Review Lane — Pi Runtime Security and Lifecycle

## Review identity

- Decision: `52`
- Primary: `semantic-discovery-protocol-v0.md@71a7fdc1bfaaa89e266b123fd9ca5a02fca2144e`
- Companion: `semantic-preflight-adapter-v0.md@f4941909fc2a74128648155b23e078cde0a2c0b2`
- Host baseline: installed Pi `0.80.6`
- Procedure: Prompt Vault `review-rfc-multi`

## Verdict

```text
review_outcome = revise_rfc
```

The core trust direction is sound, but host and lifecycle contracts remain materially underspecified.

## Lens 1 — Prompt and runner trust

### Strengths

- Arbitrary ontology prose is excluded from automatic system-role injection.
- Repository shell wrappers are rejected as automatic runners.
- Byte identity is not confused with semantic certification.

### Must-fixes

1. Close development-runner TOCTOU and executable trust. Use an absolute no-shell descriptor and immutable execution bytes or immediate complete pre-execution reverification. Drift disables the runner.
2. Downgrade markers to framing/deduplication only. Pi provides no authenticated prompt-fragment provenance; later handlers and provider hooks may replace or forge the block.
3. Define the co-resident extension and project-prompt threat boundary explicitly.

## Lens 2 — Hook scope, cancellation, and process closure

### Must-fixes

1. Rename “turn-local” to **prompt-run scoped** unless steering, retries, queued continuation, and follow-up recomputation are explicitly designed. `before_agent_start` runs once for the accepted top-level prompt and its system prompt persists through the agent run.
2. Resolve preflight cancellation before ADR. Pi does not currently prove Escape cancellation before `agent.prompt()` starts. Either add a host capability or define timeout-only preflight with a strict latency ceiling.
3. Specify process-tree cancellation across supported operating systems: merged signals, process-group creation, TERM-to-KILL escalation, reaping, shutdown bounds, and stale completion rejection.
4. Freeze distinct streaming caps for query, stdout, stderr, combined output, decoded JSON, rendered block, UI/error text, and pack output. Define UTF-8 and excess behavior.

### Architecture-shaping question

Is v0 allowed to delay prompt execution with timeout-only cancellation, or is a host-level cancellable preflight signal required before adoption?

## Lens 3 — Consent, headless behavior, and compatibility

### Must-fixes

1. A slash command alone is not operator consent. Require `ctx.mode === "tui"` plus fresh bounded TUI confirmation. RPC, prompts, tools, repository state, and other extensions cannot enable development mode.
2. Define operator-visible TUI and machine-visible RPC/JSON/print reporting for unavailable, timeout, incompatible, and exhausted states. A hidden system prompt is not operator readback.
3. Bound supported Pi host versions or negotiate required capabilities. The package's wildcard peer dependency cannot support a behavior contract tied to observed 0.80.6 internals.

### Material improvement required by strict mode

Define a versioned, advisory coexistence event with `pi-society-startup-context`, including absent/earlier/later/reload behavior. Do not use prompt markers as authority.

## Cross-cutting contradictions

- The RFC promises marker/handler-order safety that the host cannot authenticate.
- “Turn-local” conflicts with prompt-run persistence.
- Escape/abort acceptance is promised without a demonstrated pre-agent cancellation signal.
- Interactive consent is claimed although RPC can present UI capability and invoke commands.

## Evidence limits

No host spike, hostile-extension permutation, RPC injection test, process-tree test, timeout test, or reload/fork/resume canary has run. No production runner trust root exists.

## Legal recommendation

Revise the companion RFC and aligned primary requirements, then rerun review. ADR progression is premature.
