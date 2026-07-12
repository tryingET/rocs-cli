---
summary: "Controlling decision:52 operator-authorized fifth review synthesis; RFC remains non-ADR-ready."
read_when: ["Checking decision:52 latest legal review closure."]
type: "review_synthesis"
decision_id: 52
review_outcome: "revise_rfc"
---
# Fifth Review Synthesis — Semantic Discovery Formal Schemas

## Inputs

- primary `semantic-discovery-protocol-v0.md@c8b2cc2`
- companion `semantic-preflight-adapter-v0.md@27481b03`
- operator authorization `@c8b2cc2`
- fifth review plan `@fa504a7`
- Python/ROCS producer lane `scoutpeer-mrhjxgt9-e0bf8f6b`
- TypeScript/Pi verifier lane `scoutpeer-mrhjxgtj-0f6f6682`
- corroborating fork review `forkpeer-mrhk7xjj-bcdb0622`

The earlier execution-blocked note recorded the state before late peer completions arrived. These peer outputs supersede that operational blocker but do not improve the substantive outcome.

## Controlling result

All three independent reports return `revise_rfc`. They agree that prose-level schema tightening still leaves divergent valid implementations.

```text
review_outcome = revise_rfc
ADR_legal_now = no
next_legal_move = operator_escalation_after_authorized_fifth_review_failed
```

## Required next architecture move

Do not perform another prose-only patch/review loop. The next viable proposal must introduce:

1. machine-readable JSON Schemas for request, result, error, capabilities, corpus snapshot, tool identity, and pack;
2. explicit canonical digest-omitted pseudotypes;
3. golden valid/invalid and Python↔TypeScript differential fixtures;
4. closed cross-field invariants and rejection paths.

That is a material RFC shape change beyond the authorized schema-only fifth loop. It requires a new operator decision: authorize a machine-readable schema appendix/revision and a fresh review, accept the ambiguity as ADR constraints, or defer decision:52.

No ADR, task, implementation, default change, or rollout is authorized.
