---
summary: "Decision 85 owner-repo fan-out from deterministic protocol substrate through bounded insertion-evidence production rollout."
read_when:
  - "Routing or sequencing Decision 85 owner tasks."
  - "Checking Decision 85 cross-repo dependencies and authority boundaries."
type: "cross_repo_fanout"
status: "accepted_plan"
---
# Cross-Repo Fan-Out — Decision 85

## Governing artifacts

- Decision: `85`, accepted with ADR recorded.
- Operator all-phases authorization: AK evidence `5583`.
- ADR: `docs/adr/2026-07-26-semantic-pi-insertion-evidence-v1.md`.
- Implementation plan: `semantic-pi-insertion-evidence-v1-implementation-plan.md`.
- Validation/rollout/rollback: `semantic-pi-insertion-evidence-v1-validation-rollout-rollback.md`.
- Normative RFC and frozen vectors: `semantic-pi-insertion-evidence-v1-rfc.md`, `semantic-pi-insertion-evidence-v1-vectors.json`.

All tasks are fresh, owner-scoped, and linked as `post_adr_execution`. No predecessor or downstream task is reopened/reused.

## Owner slices

| Slice | AK task | Owner repo/package | Depends on | Owner result |
|---|---:|---|---|---|
| R1b protocol substrate | `4342` | `core/rocs-cli` | correction planning `4341` | six-schema bundle, two independent validators, CI bridge, Node pin |
| H1 complete host capability | `4343` | `softwareco/contrib/pi-mono` / `packages/coding-agent` | R1b | closed ABI/status, provenance, state/lifecycle, terminal insertion, guard matrix, record |
| C1 component integration | `4344` | `softwareco/owned/pi-extensions` / `packages/pi-ontology-workflows` | R1b, H1 | contribution/acknowledgement, bounded enable/disable commands, default-off |
| D1 development runtime | `4345` | `softwareco/infra/workstation` runtime-operation/receipt paths | R1b, H1, C1 | isolated install/reload, development canary, disable/version rollback receipt |
| V1 integration coordinator | `4346` | `core/rocs-cli` evidence/coordination paths | D1 | validator rerun and immutable integration receipt; no runtime mutation |
| PH1 host release | `4347` | `softwareco/contrib/pi-mono` / host release paths | V1 | signed compatible host coordinate and insertion-only release evidence |
| PC1 component release | `4348` | `softwareco/owned/pi-extensions` / component release paths | V1 | signed compatible component coordinate and insertion-only release evidence |
| PR1 production runtime | `4349` | `softwareco/infra/workstation` runtime-operation/receipt paths | PH1, PC1 | bounded production canary/wave, status enforcement, runtime rollback receipt |
| PO1 production evidence | `4350` | `core/rocs-cli` evidence/coordination paths | PR1 | receipt verification and canonical AK evidence; no runtime mutation |

D1/PR1 own local install, reload, activation, observation, and rollback because `softwareco/infra/workstation` owns workstation runtime lifecycle. V1/PO1 only verify immutable receipts and record evidence. PH1/PC1 are separate release-owner tasks. Steward/editorial publication is not absorbed into engineering; if desired under evidence `5583`, it receives a separate publication-owner task.

## Dependency graph

```text
correction 4341 -> R1b -> H1 -> C1 -> D1 runtime -> V1 evidence
                                                /         \
                                               v           v
                                           PH1 host     PC1 component
                                            release       release
                                               \           /
                                                v         v
                                                 PR1 runtime
                                                      |
                                                      v
                                                 PO1 evidence
```

Dependencies enforce contract-first implementation. No owner task starts merely because its predecessor exists; every linked task must first be explicitly reevaluated and Decision 85 must be exactly `unblocked`.

## Post-unblock correction membrane

Task `4331` failed clean on evidence `5590` because the accepted plan required repository-wide Ruff despite 1,266 unchanged out-of-scope baseline violations. Tasks `4332`–`4339` remain blocked downstream and are not reopened or reused. Fresh correction task `4341` and successor graph `4342`–`4350` preserve all protocol and owner boundaries.

Before R1b or later implementation:

1. review and commit the scoped-Ruff correction;
2. attach the corrected three artifacts as current Decision-85 continuation artifacts;
3. complete and reevaluate task `4341`;
4. explicitly reevaluate every fresh link `4342`–`4350` `still_valid` while Decision 85 remains `unblocked`;
5. require the passport to show no pending reevaluations or missing artifacts.

Any successor implementation before step 5 is unauthorized.

## Candidate-worktree policy

- Never mutate dirty shared `pi-mono` or `pi-extensions` checkouts.
- Spawn isolated candidate worktrees at explicit owner-selected base refs.
- Never silently include/discard shared-checkout bytes; overlap is a stop condition requiring owner reconciliation/new base.
- Candidate branches do not merge, publish, install, activate, or claim promotion automatically.
- Each task stages/commits only its scoped paths and records exact base/head.

## Handoff contracts

### R1b -> H1/C1

Reviewed source paths, exact hashes, Node/Python contract, and two independent validator commands. Consumers import no generated expected values and never use case IDs/expected objects as behavior.

### H1 -> C1

Exact package/API/capability version, fixed registration method/callback/controller signatures, five-second deadline, generation lifecycle, disable/reload behavior, witness scalars, Schema-3 return contract, and focused faux-provider command. The complete public API and state machine land atomically.

### C1 -> D1

Exact host/component candidate artifacts, default-off/time-bound grant commands, privacy-safe status contract, accepted tests, and disable/reload/version rollback coordinates. No semantic correctness/adoption authority.

### D1 -> V1

Workstation-owned replayable runtime receipt binding R1b/H1/C1 artifacts, development canary, privacy-safe status, zero pre-record dispatch, source invariance, and rollback.

### V1 -> PH1/PC1

Verified integration receipt and independent validator rerun. Release owners independently accept their package evidence.

### PH1/PC1 -> PR1

Signed compatible coordinates, release checks, exact provenance, prior-version rollback coordinates, and insertion-only release wording.

### PR1 -> PO1

Workstation-owned receipt with exact grants, attempt/size/time limits, privacy-safe status samples, host `rollbackRequired` handling, production canary/wave outcomes, and rollback proof.

## Production membrane

AK evidence `5583` authorizes production and package publication, but PR1 remains gated by V1 plus both release owners and exact G5/G6 bounds. Production enables only the fixed host/component/capability pair through host-enforced time/attempt/size grants and privacy-safe status/rollback signals. PO1 verifies; it never deploys. Records never become public authentication or semantic-delivery proof.

Durable recovery, SQL state, cross-process proof, generic resolver/registry, provider-native payload proof, fleet-default enablement, or broader semantic-delivery claims stop PR1 and require a new decision. Expansion beyond the named 5-process/24-hour/500-attempt wave requires a fresh owner-reviewed rollout artifact.

## Remaining pre-implementation gates

Strict convergence completed with three `accept_plan` lanes and zero blockers/material findings. The failed original graph `4331`–`4339` is immutable non-reusable history. Fresh tasks `4342`–`4350` and their dependency edges are materialized.

1. Commit and attach the corrected continuation artifacts.
2. Close/reevaluate `4341`, reevaluate `4342`–`4350`, and confirm no pending passport gates.
3. Select isolated candidate base refs without touching shared dirty bytes.
