---
summary: "Owner-scoped Decision 53 execution fan-out with explicit dirty-worktree, absent-owner, and live-operation gates."
read_when:
  - "Routing Decision 53 implementation work across owner repositories."
  - "Checking which semantic-release tasks may execute or remain deferred."
type: "cross_repo_fanout"
status: "active"
---
# Cross-Repo Fan-Out — Decision 53

## Governing chain

- Decision: `53`
- ADR: [`../adr/2026-07-13-semantic-release-and-single-canary-adoption.md`](../adr/2026-07-13-semantic-release-and-single-canary-adoption.md)
- Implementation: [`semantic-release-implementation-plan.md`](semantic-release-implementation-plan.md)
- Validation/rollout/rollback: [`semantic-release-validation-rollout-rollback.md`](semantic-release-validation-rollout-rollback.md)

This is an execution decomposition, not an authority issuer. AK owns task state. Each repository owner retains its facts and mutation authority.

## First executable wave

| Key | Owner repository | Scope | Dependency | Initial posture |
|---|---|---|---|---|
| `d53-rocs-protocol-runtime` | `core/rocs-cli` | I1 closed protocol runtime and independent conformance | — | executable after AK unblocking |
| `d53-rocs-transactions` | `core/rocs-cli` | I2 append-only/CAS transactions, bounded effects, crash proofs | ROCS protocol runtime | dependency-blocked |
| `d53-semantic-owner-sandbox` | `core/ontology-kernel` | I3 owner-only sandbox records and acquisition fixtures | ROCS protocol runtime | defer until dirty worktree is reconciled |
| `d53-ak-lineage` | `softwareco/owned/agent-kernel` | I4 DB-only exact task/decision/evidence lineage; no repository files | ROCS protocol runtime | executable as AK-only work; dirty repo files are off-limits |
| `d53-pi-delivery` | `softwareco/owned/pi-extensions` | I5 default-off Pi validation and delivery attestations | ROCS protocol runtime | defer until owner supplies clean worktree |
| `d53-owner-identity-gate` | `core/rocs-cli` | I6 resolve exact consumer, Pi adapter, and independent recovery-controller identities without substitution | semantic-owner, AK, and Pi slices | coordination only; cannot issue owner facts |

All materialized tasks must be linked to Decision 53 as `post_adr_execution`, carry explicit repo-relative scope and guardrails, and be reevaluated before unblocking.

## Execution graph

```text
d53-rocs-protocol-runtime
  ├─> d53-rocs-transactions
  ├─> d53-semantic-owner-sandbox
  ├─> d53-ak-lineage
  └─> d53-pi-delivery
          \       |       /
           d53-owner-identity-gate
```

A dependency arrow grants sequencing only. It does not let the upstream owner issue downstream facts.

## Owner boundaries

### Semantic owner

`core/ontology-kernel` owns meaning, namespace lifecycle, compatibility, trust, release approval, publication, withdrawal, and revocation. Its current dirty worktree is preserved. No Decision 53 task may overwrite or absorb those changes. Publication requires a later clean immutable source and explicit owner approval.

### ROCS

`core/rocs-cli` owns deterministic compilation, verification, projection, materialization, bounded receipts/errors, and protocol validation. ROCS cannot approve meaning, issue consumer consent, or become a recovery-policy owner.

### Agent Kernel

Agent Kernel owns canonical task, decision, dependency, stop-fact, and evidence lineage. The first-wave task has no file-mutation scope because the runtime already provides the authority surface and its repository is dirty. AK cannot store ontology bytes or issue semantic-owner/consumer-owner facts.

### Pi

`softwareco/owned/pi-extensions/packages/pi-ontology-workflows` is the existing delivery implementation surface. The monorepo is dirty and diverged; implementation waits for an owner-approved clean worktree. Pi reports delivery/suppression/failure only and cannot claim adoption or influence.

### Consumer owner

The accepted identity is exactly `softwareco/pi-canary-consumer` revision `3`, but no matching repository currently exists. No task is materialized against a substitute. Consumer intent, acceptance, activation, deactivation, and rollback remain blocked until the exact repository/owner exists and consents.

### Recovery controller

The accepted architecture requires an independently pinned recovery controller outside replaceable semantic/runtime roots. No concrete owner repository currently exists. The identity-gate task may collect an owner decision but cannot silently assign the role to ROCS, AK, Pi, the semantic owner, or the consumer.

## Later task creation gates

Only after I6 establishes exact owners may AK create:

1. an owner-scoped live-acquisition implementation task per issuing owner;
2. a recovery-controller implementation/rehearsal task in its concrete repository;
3. the exact revision-3 consumer preparation task;
4. a semantic publication operation task after semantic-owner approval;
5. a one-named-canary operation task after consumer consent;
6. a final evidence, rollback rehearsal, and KES closeout task.

Those tasks require fresh scopes, dependencies, evidence contracts, and explicit reevaluation. They are not implied by this first wave.

## First-wave done contracts

Every first-wave task must prove:

- exact accepted protocol/ADR references;
- deterministic local validation and independent review;
- no owner-boundary transfer;
- no live publication, materialization, activation, delivery, or rollback claim;
- `live_acquisition_implemented=false`;
- preservation of concurrent dirty work and current baseline digests;
- rollback or non-mutation proof;
- explicit legal next action and deferred facts.

## Non-authorizations

This fan-out does not:

- create the absent consumer or recovery-controller repository;
- name a canary or infer consumer/semantic-owner consent;
- provision signing keys or live acquisition capabilities;
- publish a semantic release;
- activate, default, start up, mandate, or fleet-roll any behavior;
- mutate ontology meaning;
- turn fixtures, task completion, CI, package versions, or mutable `dist/` into adoption authority.
