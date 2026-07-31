---
summary: "Problem brief for replacing rejected host insertion evidence with a narrow extension-local handler-resolution observation."
read_when:
  - "Reviewing Decision 89 or the retirement of Decision 85 host implementation."
type: "problem_brief"
status: "proposed"
---
# Problem brief — extension-local prompt-chain handler observation v0

## Trigger

Decision 85 accepted a host-owned insertion-evidence architecture. Its R1b schema/vector substrate completed under task `4342`, but host task `4343` stopped without a commit after independent review found unresolved dispatch, provenance, stale-context, rollback, and no-oracle failures. AK evidence `5665` records the rejected candidate. The shared `pi-mono` checkout remained unchanged.

The operator then chose to stop the Pi-host direction and redesign around what `pi-ontology-workflows` can actually observe without host changes.

## Smallest truthful observation

Inside the package's existing registered `before_agent_start` callback:

1. the outer package handler receives the host-supplied current chained `systemPrompt`;
2. a pure inner producer constructs the current semantic-preflight contribution and output;
3. only an exact append candidate is eligible for observation; pre-existing replacement/deduplication behavior may continue without a record;
4. the outer package handler records hashes and lengths from immutable local snapshots, constructs the exact return object, and replaces one bounded package-local diagnostic slot with the immutable record as its final package operation before the source-level return statement.

This proves only package-local producer resolution and return-value preparation. The runtime record does not prove execution reached or crossed the return statement, callback return, or promise settlement to its caller.

A package-local harness may separately invoke and await the handler to verify ordinary return behavior. Neither that harness nor the runtime record proves that the host accepted the value, assigned/read it back, preserved it after later handlers, serialized it into a provider payload, transmitted it, invoked a model with it, influenced a model, authenticated it publicly, or used it in production.

## Ownership

- Architecture/history: Decision 89 in `core/rocs-cli`.
- Implementation: `softwareco/owned/pi-extensions/packages/pi-ontology-workflows` only.
- Existing host capability `prompt.system.chain.v1`: compatibility gate only, never evidence.
- No `pi-mono` implementation task or host API change.
- Existing disabled-mode hints, enabled preflight framing replacement, and same-runtime session lifecycle remain package behavior outside any positive observation claim.

## Required outcome

A reviewed, executable package-local contract with explicit non-claims, sequential test harness semantics, one deterministic bounded diagnostic slot, default-off activation, and a representable AK `superseded` transition for retiring Decision 85. Review and an accepted ADR remain non-executing; implementation requires a fresh owner-scoped package task. Decision 85 and all failed/rejected tasks remain immutable history and are not reused.
