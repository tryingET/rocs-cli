---
summary: "Decision 104 post-ADR continuation plan: no implementation; delegate owner mechanics to Decisions 105-107."
read_when:
  - "Planning work after the Decision 104 boundary ADR."
type: "implementation_plan"
status: "accepted"
decision_id: 104
---
# Decision 104 continuation plan

## Plan type

This is a **no-implementation boundary plan**. Decision 104 has no source-code phase. Its deliverable is the accepted authority partition in `docs/adr/2026-08-03-owner-bounded-semantic-evaluation.md`.

The plan exists to prevent the boundary ADR from becoming accidental authority for a new global broker or evaluation graph.

## Sequence

### 1. Decision 105 — DSPx owner decision

DSPx must decide, in its own repository and review process:

- which semantic-evaluation effects it can actually mediate;
- whether those effects fit its execution-episode runtime;
- its owner-local state machine, crash/replay behavior, and receipt semantics;
- which claimed custody mechanisms are unsupported and must be removed.

Decision 104 contributes only invariants. It supplies no DSPx schema or implementation task.

### 2. Decision 106 — ROCS owner decision

ROCS must decide:

- accepted evaluation inputs and canonicalization;
- deterministic evaluation/derivation semantics under semantic-owner-defined meaning;
- failure classification and generated conformance vectors;
- rejection of evidence not grounded in an accepted producer contract.

Decision 106 may proceed independently of Decision 105 at the contract-design level, but no end-to-end implementation may assume either decision before both are accepted.

### 3. Decision 107 — Decision 53 compatibility

Decision 107 starts substantive compatibility work only after Decisions 105 and 106 identify accepted output contracts. It may define a non-authoritative verdict reference to Decision 53, or conclude that no compatible adapter exists.

It cannot redefine, activate, or duplicate publication/currentness.

## Task rules

- Every successor uses an owner-repository decision-support task before ADR.
- Source implementation tasks are created only after that owner's accepted ADR.
- One task cannot mutate DSPx and ROCS implementation surfaces together.
- Interface conformance consumes accepted owner contracts; it does not create a third global oracle.
- Decision 98 B0 and rejected Decision 103 R2 remain permanently excluded.

## Existing task disposition

Task `4566` was an erroneous pre-ADR `post_adr_execution` link and produced no implementation. It must be reevaluated as `superseded`. Tasks `4567`, `4578`, `4585`, `4586`, `4587`, and `4590` are design/review/recording lineage only.

## Completion

Decision 104 is complete when:

- its ADR and this no-implementation continuation contract are recorded;
- the companion validation/rollout/rollback artifact is recorded;
- linked tasks are reevaluated;
- Decisions 105–107 remain separate and review-gated.

Completion does not mean any successor, implementation, integration, or live effect exists.
