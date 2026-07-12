---
summary: "Decision:53 problem brief for governed semantic release, adoption, use, and rollback identity."
read_when:
  - "Reviewing decision:53 or its semantic supply-chain boundary."
type: "problem_brief"
status: "review_pending"
---
# Problem Brief — Semantic Release and Consumer Adoption v0

## Trigger

Decision `52` proved deterministic development discovery and a default-off Pi preflight path, but production use still has no owner-approved immutable fact joining authored meaning to a consumer's desired, adopted, used, and rollback-capable generation.

## Current failure modes

- mutable `dist/`, wrappers, CI, tool versions, and manifest versions can be mistaken for semantic adoption;
- ROCS executable trust can be conflated with semantic release identity;
- AK can drift into storing ontology bytes rather than intent and evidence references;
- consumers can claim desired state without materialization proof;
- use evidence can overclaim model correctness or treat session logs as authority;
- rollback can be declared without a tested predecessor or no-prior fallback;
- one canary can be misread as authorization for search, preflight, startup, or fleet defaults.

## Decision boundary

Decision `53` must determine whether to accept the target architecture in [`semantic-release-capsule-and-consumer-adoption-protocol-v0.md`](semantic-release-capsule-and-consumer-adoption-protocol-v0.md):

```text
authored -> released -> desired -> adopted -> used -> rollback
```

The review must preserve separate owner facts for semantic approval, deterministic packaging/verification, consumer intent, runtime trust, prompt delivery, and empirical analysis.

## P0 questions

1. What exact byte-level schemas and digest omission rules make capsule, intent, adoption, and use receipts replayable?
2. What local trust root makes an owner-approved capsule digest authoritative without signatures?
3. How are namespace/version uniqueness, predecessor lineage, and concurrent publication made atomic?
4. Which compatibility changes are breaking, and who approves policy versus computes classification?
5. How does a consumer prove desired state and adoption without repository-local self-authentication?
6. How are runtime rollback and semantic rollback independently rehearsed and evidenced?
7. Which separate decisions gate explicit search, automatic preflight, startup orientation, and fleet defaults?

## Non-authorization

Review work authorizes no capsule publication, ontology mutation, adopted runtime, consumer default, mandatory enforcement, fleet rollout, or `core.AgentExperience` change.
