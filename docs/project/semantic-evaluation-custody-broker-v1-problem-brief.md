---
summary: "Problem brief for separating semantic policy proof from custody/execution enforcement and deriving evaluation evidence from one canonical state machine."
read_when:
  - "Reviewing Decision 104 or any successor to Decision 103."
type: "problem_brief"
status: "proposed"
decision_id: 104
---
# Problem brief — semantic evaluation custody broker v1

## Decision question

Should Decision 103's combined proof graph be replaced by three bounded systems with different owners and failure semantics?

1. an immutable semantic-policy coordinate;
2. a custody/execution broker that enforces reservation, access, process, and cleanup behavior;
3. one canonical evaluation state machine from which schemas, validators, fixtures, and negative vectors are derived.

## Observed problem

Decision 103 r14 deliberately combines semantic-owner approval, source custody, process authorization, protected access, execution lifecycle, verdict, publication, and currentness in one protocol. Its synthetic R2 candidate at `70d3645e724c93ea407bc11f4e672df7a6ae2289` passed 347 tests but independent security and falsification reviews rejected it. Passing tests therefore demonstrated agreement with selected fixtures, not that the architecture enforced its claims.

The repeated failure pattern was:

```text
counterexample
→ another signed object, digest, equality join, or branch
→ a larger cross-product
→ representation drift
→ another counterexample
```

A signature establishes that an issuer signed bytes. It does not establish that a process started once, a store transition was linearizable, a lease was revoked, a handle was closed, another history cannot exist, or the declared actor performed a runtime operation. Those facts require an enforcing mechanism and observations rooted in that mechanism.

## Root causes

1. **Proof/enforcement confusion.** Declarative signed assertions were used as substitutes for runtime custody and execution controls.
2. **Scope collapse.** Several systems with different owners, clocks, consistency models, and failure modes were serialized as one nested graph.
3. **No executable semantic center.** Prose, schema unions, topology schedules, Python, Node, and fixtures independently represented the same behavior.
4. **Review became the design compiler.** Review found counterexamples after serialization instead of falsifying a small generative model before implementation.
5. **Operational amplification.** Larger review rounds exhausted reviewer/orchestrator capacity and obscured task/worktree ownership while green tests created false confidence.

## Required outcome

A stranger should be able to answer, without tracing a nested proof graph:

- which component owns each fact;
- which facts are immutable claims and which are enforced state;
- which transition is legal next;
- whether a process may start;
- whether protected access remains live;
- whether cleanup is complete;
- whether a verdict may be fixed;
- whether an independently published semantic release is current.

The target state is intentionally boring:

```text
sealed
→ reserved
→ authorized
→ started | not_started
→ closed
→ verdict_fixed
```

All interrupted and failed paths pass through `closed`. Publication/currentness reuse Decision 53's semantic-release authority machinery rather than entering the evaluation state machine.

## Non-goals

- no real policy, D/U/O, custody, broker, process, publication, or consumer effect;
- no Decision 98 B0 reuse, rerun, tuning, or relabeling;
- no Pi/provider/model, prompt projection, automatic preflight, default, or fleet behavior;
- no claim that a JSON receipt enforces runtime behavior;
- no implementation before strict review, a superseding ADR, and separately scoped owner tasks.

## Success criteria

- one closed machine-readable transition contract is normative;
- every legal and illegal transition vector is mechanically enumerable;
- allocation and the unique immutable initial record share one transaction; mutable current-head evidence never selects immutable initial state;
- every operation, spawn/read external effect, approval/fixation check, and verdict-register append has a closed protocol and crash disposition;
- canonical trace growth is delta-linear rather than copied-state quadratic;
- policy, broker, evaluation, and publication authority are disjoint;
- signed receipts describe broker-observed committed actions but never substitute for broker state;
- crash, retry, replay, fork, stale lease, double-start, retained-handle, and incomplete-cleanup paths fail closed;
- each implementation surface can remain small enough to explain and review independently;
- the replacement removes more concepts and duplicated authority machinery than it adds.
