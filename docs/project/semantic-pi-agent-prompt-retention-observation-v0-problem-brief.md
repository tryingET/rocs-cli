---
summary: "Problem brief for observing whether semantic-preflight bytes survive into Pi's agent-state system prompt."
read_when:
  - "Reviewing Decision 98 agent-prompt retention observation."
type: "problem_brief"
status: "proposed"
decision_id: 98
---
# Problem brief — Pi agent-prompt retention observation v0

## Problem

Decision 89 implemented a truthful but deliberately weak package-local observation: `pi-ontology-workflows` can prove that it prepared an exact-append `{systemPrompt}` return and assigned one immutable record immediately before its source-level return statement. That record cannot prove that the callback settled, Pi completed the handler chain, Pi assigned the final agent-state prompt, or the contribution survived later handlers.

The implementation also exposed no installed-instance readback. Package tests passed, but an operator could not distinguish a loaded Decision-89 build from an older package generation or inspect the last observation after a turn.

Current Pi already supplies a narrower useful boundary without a host change. It awaits the complete `before_agent_start` chain, assigns the resulting prompt to agent state, and then emits `agent_start`. At `agent_start`, `ctx.getSystemPrompt()` reports the current Pi agent-state system prompt. A package can compare its prepared prompt digest with that observed value while retaining no prompt text.

## Desired outcome

For one explicitly enabled TUI development grant, one bounded package-local slot should answer:

> Did the exact prompt bytes prepared by this package match Pi's agent-state system prompt when `agent_start` fired for the corresponding prompt run?

The answer must remain local diagnostic evidence. It must not claim final provider payload, network transmission, provider receipt, model input, causal influence, authenticity, publication, activation, or production use.

## Non-goals

- no `pi-mono` source or API change;
- no second `before_agent_start` handler;
- no module-global state, queue, history, persistence, session log, or durable credential;
- no prompt contents in diagnostics;
- no provider-specific payload parser or transport witness;
- no automatic default, headless enablement, fleet rollout, or provider/model authorization;
- no public authenticity or security decision based on co-resident extension ordering.

## Success condition

A default-off package implementation on the live package lineage:

1. records Decision-89 preparation as `prepared`;
2. observes `agent_start` and compares exact UTF-8 byte length/digest with `ctx.getSystemPrompt()`;
3. replaces the slot with `retained` or `replaced` evidence;
4. exposes sanitized protocol/outcome/digests through `/ontology-preflight observation`;
5. clears/replaces state on the existing lifecycle/grant boundaries;
6. passes package and live TUI dogfood with recorded rollback; and
7. makes no claim above Pi agent state at the `agent_start` hook.
