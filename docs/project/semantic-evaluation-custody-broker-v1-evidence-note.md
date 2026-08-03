---
summary: "Evidence and uncertainty record for Decision 104's proposed separation of policy proof, custody enforcement, and evaluation state."
read_when:
  - "Reviewing the factual basis or supersession boundary for Decision 104."
type: "evidence"
status: "proposed"
decision_id: 104
---
# Evidence note — semantic evaluation custody broker v1

## Frozen observations

| Evidence | Observation | What it does not prove |
|---|---|---|
| Accepted Decision 103 r14 ADR at `404486c6f20f252848c03df3890f1e75fc8216ba` | r14 accepted a large synthetic protocol and kept P2–P7 live effects blocked. | That its synthetic R2 implementation is secure or constructible. |
| Accepted R1 base `7fd9922756948208291cc1b247d68376df7d0996`, tree `209e325816662c4bd92397fc38204cca053fbbed` | Exact schema/digest/signature substrate existed before R2. | Runtime enforcement or R2 acceptance. |
| Rejected R2 commit `70d3645e724c93ea407bc11f4e672df7a6ae2289`, tree `79a4a141098f93c65b25c4bb5393b24b4148ab53` | Focused verification and full CI passed; AK evidence `6236` records 347 passing tests. | Architecture or security acceptance. |
| Independent reviews `dispatch-1785707588597` and `dispatch-1785707588598`; AK evidence `6237` | Reviewers found forgeable support authority, incomplete subject/pin/contamination/lifecycle joins, incomplete P7 graph coverage, unsound Git ceilings, hostile-input escapes, order-dependent failure classification, mutable fixture oracles, and incomplete Node independence. | That every possible defect was found. |
| AK evidence `6238` and failed tasks `4553`/`4563` | The rejected candidate is immutable evidence and may not be promoted or patched as accepted R2. | Authority to redesign the accepted protocol. |
| Transcendent run `transcendent-1785707223089` | The orchestrated loop failed in `diagnose` at zero seconds and did not review code. | The internal exception or a specific causal role for a prior abort. |
| Transcendent run `transcendent-1785719268490`; run record `~/.pi/agent/state/pi-society-orchestrator/loop-runs/transcendent-1785719268490.run.json` | A fresh governed retry failed before dispatch at zero seconds because the Pi session had neither `PI_COMPANY` nor a company-scoped physical `ctx.cwd`; Prompt Vault therefore correctly rejected `first-principles` preparation. The current worktree's Git common directory is under `ai-society/core`, but company inference intentionally uses explicit environment or exact cwd segments, not Git metadata. | That the older run had the same cause, that fail-closed visibility should be weakened, or that the architecture packet was reviewed by the failed loop. |
| Displayed aborted operation | It performed Prompt Vault retrieval/posture checks and read-only Git/AK inspection; no `loop_execute` call was shown. | Whether an older aborted controller left child processes or orchestration residue. |
| Decision 53 accepted semantic-release ADR | Existing append-only owner publication/currentness machinery already separates semantic identity, publication, adoption, and use. | Live acquisition or publication authority; those gates remain blocked. |
| Rejected Decision 104 packet aggregate `2a0508e83cec0bc86dd3af66d053b0f6b9efe76c80c8b70ed733af543fcd12ef`, manifest `76d1bcef372666657fc7c1697e666005cda8d75bd0e029285d54115554f093c4`; reviews `dispatch-1785721030840`–`843` | All lanes rejected: expected-generation/replay was prose-only; signed membership folding was contradictory; local descriptor binding and external booleans were underclosed; verdict authority was subject-selected; spawn/read crash effects were not exactly-once; renewable head proof had no canonical seal transition; trace snapshots were quadratic. | That the subsequent atomic allocation+record, closed transaction/evidence contracts, containment/spool protocols, and delta trace are accepted. |

## Accepted inference

The older zero-second run `transcendent-1785707223089` remains an orchestration/agent-dispatch failure whose exact internal exception is unknown. The later run `transcendent-1785719268490` has a known, pre-dispatch cause: fail-closed Prompt Vault company resolution. The supported operational correction is to launch Pi with `PI_COMPANY=core` or from a physically company-scoped cwd; weakening visibility checks or inferring authority from a Git remote/common-dir path is not justified by this evidence.

Aborting a controller can plausibly leave already-spawned children alive and contribute to stale claims or late messages. That is a coordination-risk hypothesis, not the proven direct cause of either run.

The architecture failure is independent of that operational failure: the tests, fixtures, prose, schema, Python, and Node implementations lacked one executable source of truth, while signed declarations represented facts that only a runtime broker could enforce.

The rejected `2a0508…` packet established another design correction: a renewable current-head proof is appropriate as read-time evidence but not as an immutable initial-state selector. The successor draft therefore creates the unique sealed record atomically with allocation, keeps later memberships external to that record, roots all operations in one transaction envelope/protocol, and models spawn containment, protected-read spooling, approval/fixation, and verdict-register commit explicitly. This is a proposal derived from rejection, not acceptance.

## Supersession boundary

Decision 104 proposes a successor architecture. Until it receives strict convergence and an accepted superseding ADR:

- Decision 103 remains historical accepted authority;
- no Decision 104 implementation is authorized;
- `70d3645` remains rejected evidence only;
- Decision 103 R0/R1 mechanics may be reused only after the successor plan explicitly identifies which pure policy/digest primitives remain semantically unchanged;
- no live Decision 53 gate is activated.

## Falsifiable claims for review

Review should reject this proposal if any is false:

1. every broker-enforced fact has a concrete state transition and linearization point;
2. every receipt is downstream of the committed action it describes;
3. the canonical transition contract can enumerate every legal and illegal branch without prose-only exceptions;
4. semantic policy bytes contain no execution, custody, publication/currentness, or consumer semantics;
5. evaluation verdict fixation cannot occur before broker-observed cleanup reaches `closed`;
6. publication/currentness can reference the verdict without duplicating Decision 53's history/CAS model;
7. the design remains useful with all live effects disabled during synthetic conformance work.
