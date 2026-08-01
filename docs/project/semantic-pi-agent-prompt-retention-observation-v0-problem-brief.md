---
summary: "Problem brief for correlating semantic-preflight preparation with Pi agent-state prompt readback."
read_when:
  - "Reviewing Decision 98 agent-prompt observation."
type: "problem_brief"
status: "proposed"
decision_id: 98
---
# Problem brief — Pi agent-prompt observation v0

## Problem

Decision 89 proves only that `pi-ontology-workflows` prepared an exact-append `{systemPrompt}` return and assigned one immutable record immediately before its source-level return. It does not prove callback settlement, host assignment, final agent-state bytes, provider payload, or model use. The installed instance also exposes no readback.

Current Pi awaits the `before_agent_start` chain, assigns the resulting prompt, and later emits `agent_start`; however, independent review of host source found that asynchronous prompt preflights may overlap before Pi marks a run active. Existing events carry no shared prompt-run identity. A single package slot therefore cannot safely correlate an arbitrary `agent_start` with the preparation that produced it.

Whole-prompt digest mismatch is also weaker than “replacement”: a later extension may append bytes while retaining the entire prepared prompt. The truthful observation is exact whole-prompt match or mismatch, not contribution survival.

## Desired outcome

For one explicitly enabled TUI development grant, one bounded package-local slot should answer:

> For the same host-correlated prompt run, did Pi's agent-state system prompt at the post-assignment observation seam exactly match the whole prompt prepared by this package?

This requires a minimal Pi-host correlation/readback contract. The answer remains local diagnostic evidence and never proves provider serialization, transmission, provider receipt, model input/influence, authenticity, semantic correctness, publication, activation, or production use.

## Success condition

1. Pi supplies an opaque per-run correlation token across `before_agent_start` and a post-assignment observation event, with an exact capability guarantee.
2. The package retains at most the latest token internally and no token in public diagnostics.
3. The package reports `prepared`, `agent_prompt_exact_match`, or `agent_prompt_mismatch` through deterministic sanitized readback.
4. Overlapping prompt runs cannot create false correlation; nonmatching tokens are ignored.
5. Live-lineage package, host, install, rollback, deterministic harness, TUI canary, and B0 retrieval evidence pass their separate gates.

## Non-goals

- no second `before_agent_start` handler;
- no queue, history, persistence, timestamps, allocator, session entry, or durable run identity;
- no prompt text or prompt-derived digest/length in operator output;
- no provider-payload or transport witness;
- no automatic default, headless enablement, fleet rollout, or unauthorised provider/model use;
- no security or lifecycle decision based on co-resident extension honesty.
