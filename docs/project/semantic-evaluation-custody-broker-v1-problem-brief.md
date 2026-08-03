---
summary: "Compact problem statement for Decision 104's owner-boundary review."
read_when:
  - "Reviewing whether Decision 104 should proceed to ADR."
type: "problem-brief"
status: "proposed"
decision_id: 104
---
# Problem brief — owner-bounded semantic evaluation

## Problem

Decision 103's rejected R2 implementation demonstrated that passing tests and signed proof objects do not establish runtime enforcement. A later Decision 104 draft tried to repair this with one 271 KB cross-owner state machine. It remained non-constructible and reproduced state that belongs separately to DSPx, ROCS, and Decision 53.

The architecture needs one small answer before any owner designs implementation details: where does authority begin and end?

## Decision question

Should semantic evaluation use:

- immutable semantic-policy meaning owned by the semantic owner;
- DSPx-owned execution episodes and evidence only for effects DSPx truly mediates;
- ROCS-owned deterministic semantic evaluation;
- existing Decision 53 publication/currentness authority;
- owner-local executable machines joined by immutable evidence contracts rather than one global transition graph?

## Why now

Without this boundary decision, another R2 attempt would either trust caller-authored enforcement claims or make ROCS specify another owner's private runtime. Both paths are already rejected by evidence.

## Acceptance test

Decision 104 is ready for ADR only if independent review agrees that:

1. the authority partition is truthful and non-overlapping;
2. signatures cannot substitute for enforced effects;
3. owner-local machines plus interface conformance can preserve safety without a global machine;
4. Decision 53 remains the sole publication/currentness authority;
5. Decisions 105–107 are the right bounded successors;
6. no implementation or live effect follows from accepting the boundary.

Any unresolved authority overlap, circular evidence flow, hidden publication path, or implementation claim is a blocker.

## Non-goals

This review must not design broker internals, ROCS schemas, publication records, implementation plans, code, fixtures, deployment, dogfood, or production activation. Those belong to later owner decisions and tasks.

## Evidence

- rejected Decision 103 R2: `70d3645e724c93ea407bc11f4e672df7a6ae2289`;
- preserved rejected Decision 104 mega-packet: `e43eb045179ba95638e690a9574fdc80fd26de7f`;
- compact boundary decomposition: `6aec9a808b05fdecb10d2c742ccda853a820fc3a`;
- controlling adjudication: `semantic-evaluation-custody-broker-v1-greats-adjudication.md`.
