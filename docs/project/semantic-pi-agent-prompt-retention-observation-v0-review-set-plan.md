---
summary: "Strict-convergence review plan for Decision 98."
read_when:
  - "Running Decision 98 architecture review."
type: "review_set_plan"
status: "proposed"
decision_id: 98
---
# Review-set plan — Pi agent-prompt retention observation v0

## Frozen review target

Review the problem brief, evidence note, RFC, and this plan at one exact commit and aggregate digest. All lanes inspect identical bytes.

## Required lanes

### Pi component and host-seam lane

Verify:

- current Pi event ordering and `getSystemPrompt()` semantics;
- correlation of Decision-89 preparation with `agent_start`;
- no second `before_agent_start` handler and no host change;
- state transitions, lifecycle clearing, retries, replacement, and concurrency;
- implementability on the live `pi-ontology-workflows` lineage.

### Governance, security, and claim lane

Verify:

- no provider/model/transmission/authenticity overclaim;
- digest equality is not treated as provenance;
- default-off TUI grant and bounded readback;
- no prompt text, path, secret, session content, or durable state leaks;
- installation, provider/model use, publication, and production remain separately gated.

### Product-value and debt lane

Verify:

- the observation answers an operator-useful question;
- one slot and one additional lifecycle hook are proportionate;
- no IDs, allocator, queue, history, persistence, or public evidence API;
- B0/B1/B2 evaluation remains distinct from engineering observability;
- rollback and deletion remain straightforward.

## Verdicts

Each lane returns exactly one:

- `ready_for_adr`;
- `revise_rfc`;
- `reject_direction`.

Any blocker or unresolved material finding prevents ADR opening. A controlling synthesis cites all lane outputs and the exact frozen aggregate.

## Review integrity

- read-only review;
- no implementation, install, reload, dogfood, provider/model call, publication, or AK lifecycle movement by reviewers;
- review reports are evidence inputs, not authority until attached through AK;
- later implementation must use a fresh package-owner task and then a separate runtime/dogfood task.
