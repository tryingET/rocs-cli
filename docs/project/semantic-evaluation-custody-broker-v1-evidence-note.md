---
summary: "Negative evidence and decomposition basis for Decision 104."
read_when:
  - "Reviewing why Decision 104 rejects a cross-owner global state machine."
type: "evidence"
status: "proposed"
decision_id: 104
---
# Evidence note — Decision 104 decomposition

## Preserved rejected evidence

- Decision 103 R2 commit `70d3645e724c93ea407bc11f4e672df7a6ae2289`, tree `79a4a141098f93c65b25c4bb5393b24b4148ab53`, passed 347 tests but failed independent security/falsification review. Tests did not establish architecture acceptance.
- AK evidence `6236`–`6238` and failed task `4553` preserve that rejection. Decision 98 B0 and rejected R2 may not be reused, rerun, relabeled, tuned, or revived.
- Commit `e43eb045179ba95638e690a9574fdc80fd26de7f` preserves the rejected Decision 104 mega-packet: eight files, 7,212 inserted lines, and 271,025 bytes. Its `state-machine.json` alone was 194,652 bytes.
- The latest strict preflight still found illegal acknowledgement transitions, non-constructible branch-dependent gate semantics, and incomplete digest domains. No unanimous acceptance or controlling synthesis exists.

## Operational evidence

Prompt Vault contains active `many-of-the-greats` version 3 as a `cognitive / one_shot / structured` template visible to `core`. It was retrieved from a physically company-scoped Prompt Vault cwd and applied in [`semantic-evaluation-custody-broker-v1-greats-adjudication.md`](semantic-evaluation-custody-broker-v1-greats-adjudication.md).

The normal Pi Vault tool surface correctly failed closed in this `/data/...` session because `PI_COMPANY` is unset and the physical cwd is not company-scoped. That visibility failure did not cause the architecture rejection and was not bypassed by weakening company inference.

## Accepted inference

The global-machine approach was structurally wrong, not merely unfinished. It attempted to make ROCS specify DSPx-private enforcement mechanics and Decision 53 integration details. Each counterexample expanded the graph while reducing ownership clarity.

The appropriate correction is owner-local executable machines joined by immutable evidence contracts:

- DSPx owns only runtime effects and execution evidence it truly mediates;
- ROCS owns semantic and deterministic evaluation truth;
- Decision 53 continues to own publication/currentness;
- Decision 104 owns only the cross-owner boundary and invariants.

## Nonclaims

This evidence does not prove that DSPx currently implements a custody broker, that the successor interfaces are constructible, or that publication compatibility exists. Those are questions for separate owner decisions. No ADR or implementation authority follows from this note.
