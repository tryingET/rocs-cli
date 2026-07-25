---
summary: "Accepts semantic Pi delivery v1 with pi-ontology-workflows component issuance, Pi-host post-application witnessing, closed replay and lineage evidence, and separately gated implementation and dogfood."
read_when:
  - "Implementing Decision 71 semantic Pi delivery v1."
  - "Reviewing Pi delivery identity, host witness, isolated integration, or production evidence."
  - "Planning post-ADR ROCS, Pi component, or Pi host implementation tasks."
system4d:
  container: "Accepted architecture boundary for semantic Pi delivery v1."
  compass: "Preserve component identity, host-observed application, and independent production authority."
  engine: "Frozen r21 review -> ADR acceptance -> owner-scoped implementation -> separate one-shot dogfood and production gates."
  fog: "An ADR, fixture, witness digest, or dogfood run may be mistaken for implementation or production authority."
type: "adr"
status: "accepted"
---
# ADR — Semantic Pi Delivery v1 Identity and Host Witness

## Decision

Accept the target architecture from AK decision `71` and the exact reviewed r21 source set:

1. The public product identity is repository `pi-extensions`, component and protocol issuer `pi-ontology-workflows`, and package `@tryinget/pi-ontology-workflows`. No `pi-adapter` repository, component, alias, conversion, fallback, or owner exists.
2. Repository owner, component issuer, Pi host issuer, loaded artifact, execution instance, execution generation, prompt-run attempt, controller, finalizer, launch broker, recovery actor, and attestation owner remain distinct identities and authority roles.
3. A delivered `semantic-pi-delivery-receipt.v1` requires a Pi-host-issued post-application witness created only after exact prompt-chain assignment and host readback. It claims prompt-chain insertion only—not provider transmission, model invocation, adoption, influence, correctness, or production use.
4. Witness issuance, durable persistence, one-use redemption, delivery transcript, process lineage closeout/reap evidence, replay history, and host attestation are separate typed artifacts. A self-digest, fixture, callback return, file path, or test flag is not issuance or delivery authority.
5. The isolated integration path proves only `integration_only` implementation evidence. It requires separately current Decision-71/task scope, completed owner implementations, packet acceptance, reevaluation, Pi component and host approvals, one-shot authorization, durable history, duplicate-attempt suppression, and clean teardown. It cannot validate delivery or production.
6. Production remains a later independent protocol gate requiring a production decision/task, consumer consent, one named canary, disjoint recovery and attestation owners, live-acquisition authority, current reevaluation/evidence, one production reservation, clean teardown, terminal authority resolution, and host attestation.
7. ROCS owns deterministic schemas, registry, packet, independent Python/Node validators, fixture derivation/coverage, and embedding. Generated artifacts may add no semantics absent from the reviewed source bytes.
8. Exact reviewed SQLite schemas, x86-64 seccomp policy/compiler, restricted Wasm grammar/validator, accepted-v0 anchors, digest domains, owner receipts, process credentials, executable gates, pidfd transfer, and parent reap order are normative implementation contracts.
9. Accepted Decision-53 v0 artifacts remain immutable history. Successor entrypoints reject v0 delivery receipts, `isolatedDogfood`, and non-host-witness constructor authority.
10. No delivery flag or default surface is added; default behavior remains unchanged and off. `live_acquisition_implemented=false` and production authorization false remain mandatory.

## Accepted review identity

- RFC revision: `semantic-pi-delivery-v1-r21`
- Frozen commit: `b14620b9433534a351bb0ce4710ad3073e37b64f`
- Frozen tree: `92303cbb46503e2eaa4af07094da535db6be6ef5`
- Fourteen-file review aggregate: `3d8c5c4d50e7fbe1fb1eab6701b407477db405545075fd3fa41cfbf5234d4e2c`
- Controlling synthesis: `docs/project/semantic-pi-delivery-v1-review-synthesis-r21.md`
- Lane outcome: all five required lanes `ready_for_adr`

## Accepted normative artifacts

Primary and machine sources:

- `docs/project/semantic-pi-delivery-v1-rfc.md`
- `docs/project/semantic-pi-delivery-v1-runtime-contracts.md`
- `docs/project/semantic-pi-delivery-v1-authority-contracts.md`
- `docs/project/semantic-pi-delivery-v1-validation-contracts.md`
- `docs/project/semantic-pi-delivery-v1-machine-contract.md`
- `docs/project/semantic-pi-delivery-v1-seccomp-policy.json`
- `docs/project/semantic-pi-delivery-v1-wasm-grammar.json`
- `docs/project/semantic-pi-delivery-v1-wasm-validation-algorithm.md`
- `docs/project/semantic-pi-delivery-v1-durable-store.sql`
- `docs/project/semantic-pi-delivery-v1-integration-ledger.sql`
- `docs/project/semantic-pi-delivery-v1-production-replay.sql`

Reviewed supporting/governance sources in the fourteen-file identity:

- `docs/project/semantic-pi-delivery-v1-problem-brief.md`
- `docs/project/semantic-pi-delivery-v1-evidence-note.md`
- `docs/project/semantic-pi-delivery-v1-review-set-plan.md`

Controlling review evidence, produced after the frozen source commit:

- `docs/project/semantic-pi-delivery-v1-review-memo-r21.md`
- `docs/project/semantic-pi-delivery-v1-review-synthesis-r21.md`

The memo and synthesis establish acceptance readiness; they are not normative generator inputs and are not members of the fourteen-file aggregate.

## Authority split

| Concern | Owner |
|---|---|
| Semantic meaning, v0 authority, packet acceptance, attestation-owner appointment | semantic owner |
| Deterministic protocol generation and validation | ROCS |
| Component repository identity, release, and owner approval | Pi component owner |
| Delivered receipt and integration-ack issuance | `pi-ontology-workflows` component issuer |
| Host release, control, and launch-broker operation | Pi host owner |
| Application witness, redemption, replay observation, suppression/failure observation | fixed Pi-host issuer |
| Executable launch receipts and broker lineage observations | Pi host launch broker |
| Integration proof and ordinary finalizer terminal evidence | fixed finalizer issuer |
| Canonical decisions, tasks, scopes, reevaluation, evidence lineage | Agent Kernel |
| Production consent and named canary | future consumer/canary owners |
| Production teardown and replay recovery | future disjoint recovery owner |
| Production host attestation | future control-disjoint attestation owner |
| Empirical outcome analysis | DSPx/Oracle |

Joining facts does not transfer issuance authority.

## Consequences

### Positive

- Delivery identity and host-observed application are no longer conflated.
- Coherent identity substitution, forged witness JSON, attempt replay, copied stores, stale authority, pid reuse, unreaped-process claims, and purpose confusion fail closed.
- Isolated validation can prove implementation readiness without claiming provider/model use or production delivery.
- Production authority remains independently reviewable and cannot emerge from passing fixtures or one dogfood run.

### Costs

- Implementation spans separate ROCS, Pi component, and Pi host owner surfaces.
- Exact schemas, registries, SQL, Unicode, Wasm, seccomp, fixtures, process barriers, signed receipts, and crash-safe histories require substantial deterministic implementation and cross-owner evidence.
- No future consumer, canary, recovery, acquisition, or attestation-owner instance, key, or live-acquisition fact is provisioned by this ADR.

## Post-ADR implementation obligations

Before any execution, Decision `71` must carry separately scoped implementation tasks for ROCS protocol generation/validation, Pi component integration, and Pi host runtime behavior. The lawful order is: ROCS generates and independently validates the exact packet, fixtures, coverage, and embedding; the semantic owner issues packet acceptance; Pi component and Pi host implementations consume that accepted packet under their own tasks and produce verified evidence; then AK performs the post-ADR reevaluation. Only that reevaluation may establish readiness for a separately authorized isolated dogfood task.

The first implementation must preserve:

- exact r21 reviewed-source identity and no post-review semantics;
- independent Python and Node validators and deterministic write/check convergence;
- exact SQL schemas, seccomp compiler vectors, restricted Wasm validation, and frozen coverage obligations;
- private host capability, assignment/readback ordering, durable one-use witness/redemption, replay, and lineage closure;
- default-off, no publication/startup/fleet behavior, no live acquisition, and no production authorization;
- owner-specific rollback and immutable v0/r21 histories.

## Deferred gates

This ADR does **not** authorize:

- implementation or generation before owner-scoped task authority;
- isolated dogfood without a separately claimed one-shot Decision-71 task and one current component-owner plus one current host-owner approval;
- publication, activation, adoption, startup, defaults, or fleet rollout;
- consumer consent, canary identity, live acquisition, signing/key provisioning, recovery-owner or attestation-owner instances;
- production execution or production delivery;
- ontology mutation or activation of candidate `0d53ce3`;
- completion of blocked task `4127`.

## Rejected alternatives

- `pi-adapter` extraction, alias, fallback, or independent owner;
- component-issued host witness or host-issued component receipt;
- callback return, fixture, path, self-digest, or persisted JSON as delivery authority;
- provider transmission, model invocation, adoption, influence, or correctness claims from prompt insertion;
- pidfd signal or `/proc` absence as process reap proof;
- copied/restored/alternate SQLite stores or mutable terminal history;
- one decision or one successful dogfood run authorizing production;
- generated schemas, fixtures, or embeddings selecting new semantics.

## Rollback and supersession

Before implementation, rollback is semantic: supersede this ADR and retain current v0 behavior and default-off posture.

During implementation, any identity, currentness, determinism, schema, seccomp, Wasm, process, durable-store, replay, fixture-convergence, or rollback failure stops before execution authority and preserves immutable reviewed history.

After separately authorized isolated dogfood, rollback terminalizes every outstanding claim, preserves all receipts, transcripts, ledger/store heads, and replay history, rejects generation or attempt reuse, and removes only disposable dogfood runtime bytes. Default-off production behavior remains unchanged. Production rollback is not authorized here and requires the later production decision, owner facts, recovery protocol, and evidence.

This ADR can be widened only by a later accepted decision and superseding ADR.
