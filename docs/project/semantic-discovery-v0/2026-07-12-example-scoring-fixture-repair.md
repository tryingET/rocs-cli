---
summary: "Operator-authorized repair of the semantic-discovery-v0 golden example-token score contradiction found during task 3817."
read_when:
  - "Auditing the semantic-discovery-v0 golden result or task 3817 implementation evidence."
type: "protocol_repair"
status: "accepted_repair"
decision_id: 52
---
# Semantic Discovery v0 — Example-Scoring Fixture Repair

## Defect

Task `3817` found that the accepted golden document contains `ont.examples: [agent]` while the golden request is `agent authority`. The accepted `rocs-lexical-v0` algorithm assigns example-token weight `50` and requires corresponding evidence.

The original golden result incorrectly recorded score `1100` and omitted:

```json
{"field":"example","rule":"token_exact","query_term":"agent"}
```

The deterministic score from the accepted raw document and algorithm is `1150`.

## Authority and resolution

The operator explicitly selected **repair the golden fixture to 1150** on 2026-07-12 after implementation stopped on the contradiction. The algorithm, schema, and invariant meanings remain unchanged.

This repair:

- adds the missing example-token evidence;
- changes the golden candidate score from `1100` to `1150`;
- regenerates the result digest and exact result JCS preimage fixture;
- requires independent Python and TypeScript recomputation before task closure.

It does not authorize production adoption, defaults, or fleet behavior. Decision `53` remains the production membrane.
