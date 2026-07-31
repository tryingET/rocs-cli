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

Inside the package's registered `before_agent_start` callback:

1. the outer package handler receives the host-supplied current chained `systemPrompt`;
2. an inner package producer constructs one canonical contribution and exact appended output;
3. the outer package handler observes that producer result, records hashes and lengths from immutable local snapshots, and returns the same output object to its caller.

This proves only package-local producer resolution and forwarding at the extension callback boundary.

It does not prove that the host accepted the return value, assigned/read it back, preserved it after later handlers, serialized it into a provider payload, transmitted it, invoked a model with it, influenced a model, authenticated it publicly, or used it in production.

## Ownership

- Architecture/history: Decision 89 in `core/rocs-cli`.
- Implementation: `softwareco/owned/pi-extensions/packages/pi-ontology-workflows` only.
- Existing host capability `prompt.system.chain.v1`: compatibility gate only, never evidence.
- No `pi-mono` implementation task or host API change.

## Required outcome

A reviewed, executable package-local contract with explicit non-claims, sequential test harness semantics, deterministic local records, and default-off activation. Decision 85 and all failed/rejected tasks remain immutable history and are not reused.
