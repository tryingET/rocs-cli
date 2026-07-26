---
summary: "Validation, default-off rollout, stop conditions, and rollback contract for Decision 71 semantic Pi delivery v1."
read_when:
  - "Validating Decision 71 packet, component, host, or isolated-dogfood work."
  - "Checking whether a Decision 71 gate may lawfully advance."
system4d:
  container: "Evidence and rollback membrane for the accepted r21 implementation program."
  compass: "Fail closed on byte, owner, currentness, replay, process, or authority drift."
  engine: "Baseline -> deterministic packet -> owner acceptance -> host-owner artifact/API -> component proof -> exact scope/readiness -> optional one-shot dogfood."
  fog: "A passing fixture, AK unblocking, or isolated run may be overclaimed as delivery or production."
type: "validation_rollout_rollback"
status: "accepted_plan"
---
# Validation / Rollout / Rollback — Semantic Pi Delivery v1

## Scope and authority

This plan validates and stages [`semantic-pi-delivery-v1-implementation-plan.md`](semantic-pi-delivery-v1-implementation-plan.md) under accepted Decision 71 and its [ADR](../adr/2026-07-25-semantic-pi-delivery-v1-identity-and-host-witness.md).

It permits default-off implementation validation only after AK releases the linked tasks. It does not authorize packet-owner signatures, dogfood, publication, activation, ontology mutation, live acquisition, provider/model use, consumer/canary facts, production, or production rollback.

## Baseline record

Before each owner task records evidence, capture without modifying concurrent work:

- Decision 71 state, ADR, exact r21 identity, attached plans, linked task IDs/scopes/contracts, dependencies, and reevaluation status;
- target repository commit, branch/worktree identity, clean/dirty state, and isolated-worktree base;
- the frozen fourteen-file manifest and aggregate `3d8c5c4d50e7fbe1fb1eab6701b407477db405545075fd3fa41cfbf5234d4e2c`;
- accepted Pi identity commit `63d1e9f5c271007b48c45818d1f419a228de1561`;
- preserved Decision-53 v0 tree and accepted v0 authority anchors;
- tool/runtime versions, lockfile digests, environment, network posture, and filesystem/process roots;
- `live_acquisition_implemented=false`, production authorization false, and unchanged default-off behavior.

The dirty shared `pi-extensions` and `softwareco/contrib/pi-mono` checkouts are preservation baselines, not implementation surfaces.

## Validation gates

### V0 — AK release and plan integrity

- Both continuation plans exist, pass strict docs validation, and are attached to Decision 71.
- Tasks `4230`, `4231`, and `4232` are owner-scoped, guarded, linked as `post_adr_execution`, and explicitly reevaluated.
- Task `4234` is linked separately as `decision_support` for the required Pi-host owner identity artifact and is not treated as implementation evidence.
- Completed task `4119` is reevaluated as historical completed architecture work rather than reopened execution.
- Decision 71 advances to `unblocked` only when the AK passport reports complete continuation artifacts and no pending post-ADR linked-task reevaluation.
- Separate pending Pi-owner task `4127` stays outside this implementation program. Its deferral release records the operator's explicit post-ADR identity-integration request only; V0 neither links nor completes it.

Outcome: owner implementation tasks become claimable. No protocol execution envelope or dogfood authority exists.

### V1 — Reviewed-source and packet integrity

- Recompute every frozen source SHA-256, byte length, commit/tree identity, and fourteen-file aggregate.
- Preserve `docs/project/semantic-release-v0/**` byte-for-byte and verify its accepted anchors.
- Run packet write/check from the exact generator entrypoint with no fixture input.
- Verify packet inventory equality, safe paths, resource caps, packet aggregate/self digest, registry/schema/domain/edge closure, SQL bindings, Wasm source copies, seccomp policy/vector output, Unicode 15 tables, and exact embedding.
- Verify seccomp BPF is 223 instructions, 1,784 bytes, SHA-256 `88851d9d4098409b2394e38b7db69c63dcd737f330e1bfe72d79bed19382afc0`, and accepted packet-domain digest.
- Parse every JSON/schema offline with no remote resolution.

Reject any post-review semantic choice, missing/extra file, drifted source, packet self-listing, unknown schema/domain/edge, copied body, or unsupported bootstrap.

### V2 — Fixture and independent-validator convergence

- Finalize the packet before generating fixtures.
- Generate/check exactly five local fixture files and no additional generated fixture inventory.
- Replay 112 mandatory adversarial cases plus 3 boundary cases.
- Verify 127 coverage rows: 99 mandatory rejection obligations, 3 boundary obligations, and 25 host-owned acceptance obligations.
- Independently run Python and Node implementations over all 115 ROCS cases.
- Prove the generator imports neither validator and the validators share no parser, digest helper, derivation builder, or validator code.
- Run two fresh-checkout write sequences and every check mode; compare all generated bytes and hashes.
- Make the sequence unavoidable in `./scripts/ci/full.sh`.

Any byte, derivation, precedence, expected-outcome, or coverage disagreement blocks packet acceptance.

### V3 — Semantic-owner validation and packet acceptance

- Resolve the current semantic protocol owner through accepted Decision-53 authority.
- Verify exact finalized packet/fixture identities and independent convergence.
- Issue fixture-validation only with purpose `fixture_validation` through the owner surface.
- Publish it and obtain a current acquisition pin/read receipt.
- Issue packet acceptance only with purpose `packet_acceptance` after all required v0/r21/fixture joins.
- Publish it and obtain current owner control, acquisition pin, and read receipt.

No repository file, fixture, callback, test flag, self-digest, agent assertion, or AK note substitutes for these owner facts. Missing key/store/currentness capability is a recorded blocker, not permission to fabricate synthetic acceptance.

### V4 — Separately reviewed Pi-host owner identity acceptance

- Complete decision-support task `4234` only after V3.
- Verify the host-owner artifact accepts the exact r21 repository/component identity, canonical ledger identity/application/user version/packet-pinned SQL digest, and content-addressed private API.
- Run a separate Pi-host owner review against the frozen r21 authority and runtime contracts.
- Reject any public command, flag, product surface, component-issued host witness, signing-key provisioning, dogfood, provider/model, or production authority.

The accepted owner artifact is a prerequisite for host implementation; it is not implementation evidence or an execution envelope.

### V5 — Pi host application and process boundary

- Start only after V4 and consume the exact V3-accepted packet.
- Verify the private capability cannot be serialized, supplied by an extension, replaced by environment/repository input, or reused across generation/attempt identity.
- Prove witness issuance occurs only after exact final prompt-chain assignment and host readback.
- Inject failure before and after assignment, readback, persistence, redemption, broker exchange, pidfd transfer, closeout, reap, and teardown boundaries.
- Execute all 25 exact host-owned fixture cases.
- Independently compile/evaluate seccomp policy and execute restricted Wasm grammar/ABI/resource tests.
- Prove duplicate attempts suppress, all reached child processes are terminalized/reaped, terminal history is immutable, and no pre-witness failure emits witness or success authority.
- Run focused tests and the owner coding-agent acceptance gate on the isolated current-base worktree.

The witness says prompt-chain insertion only. Provider transmission, model invocation, influence, correctness, adoption, and production use remain unproven.

### V6 — Pi component separation

- Start only after V5 and consume the same exact V3-accepted packet.
- Verify repository/component/package identity and accepted identity-commit closure.
- Reject `pi-adapter`, v0 delivery receipts, `isolatedDogfood`, alias/fallback/extraction, stale packet acceptance, and non-host-witness constructor authority.
- Prove component receipts cannot manufacture or infer the Pi host witness.
- Prove a host witness is validated before a delivered component receipt and remains bound to exact artifact/generation/attempt identity.
- Prove callback return, persisted JSON, fixture, path, or self-digest alone cannot become delivery authority.
- Run package tests and the monorepo package-quality gate from the isolated worktree.

No install, reload, publication, startup, provider/model action, or default change belongs to this gate.

### V7 — Exact AK scope subjects, cross-owner evidence, and readiness

- Freeze actual file inventories, then use the owning AK surfaces to narrow tasks `4230`, `4231`, and `4232` from their implementation-time glob scopes to sorted unique exact NFC repo-relative allowed/required path rows with no `*?[]{}!` or other glob semantics.
- Verify every required path is byte-identically present in allowed paths and that each exact scope matches the completed task's repository and literal implementation role.
- Materialize distinct `semantic-release.ak-decision-scope.v1` subjects and current `ak_decision_scope` read receipts for `rocs_protocol_implementation`, `pi_component_implementation`, and `pi_host_implementation`.
- Preserve the original broader scopes as immutable authorization history, but never insert those globs into protocol task/scope subjects.
- Verify tasks `4230`, `4231`, and `4232` completed with exact commits and independent reviews.
- Resolve implementation task references, task receipts, scope subjects, and scope receipts in literal role order `rocs_protocol_implementation,pi_component_implementation,pi_host_implementation`.
- Verify component and host packet bytes, registry/schema identities, owner acceptance, and current reads are equal.
- Resolve every Decision-71 dependency, evidence reference, owner control, pin, and read receipt at its required epoch.
- Rehearse owner-specific rollback and verify dirty shared checkouts remain untouched.
- Produce the protocol `post_adr_reevaluation` only after all accepted inputs exist.

A successful result means only that a separate one-shot isolated dogfood task may be proposed.

### V8 — Separately authorized one-shot isolated dogfood

Before one attempt:

- create and claim a new Decision-71 dogfood task;
- bind one current component-owner approval and one current host-owner approval;
- bind exact V3 packet acceptance and V7 reevaluation/evidence;
- bind the three exact implementation task/scope subjects and current receipts in required literal role order;
- reserve one unique attempt under durable canonical history;
- use disposable isolated runtime roots and fixed closed inputs;
- predeclare teardown and rollback.

During and after the attempt:

- prove `integration_only` or a lawful terminal failure/cancellation;
- prove duplicate-attempt suppression and no attempt/generation reuse;
- terminalize all claims and processes;
- preserve receipts, transcripts, ledger/store heads, and replay history;
- remove only verified disposable runtime bytes.

The run cannot validate delivery or production and cannot imply provider/model use.

## Default-off rollout

### R0 — Decision release

Attach the two plans, reevaluate linked tasks, and advance Decision 71 to `unblocked`. This releases implementation tasks only.

### R1 — ROCS generation and validation

Complete task `4230`, freeze exact packet/fixture/embedding commits and digests, run independent review, and record evidence. Do not begin owner implementation from an unaccepted packet.

### R2 — Semantic-owner acceptance

Perform V3 through the lawful owner store. If unavailable, hold at a verified unaccepted packet.

### R3 — Pi-host owner artifact and host implementation

Complete task `4234` and its independent owner review, then complete task `4232` in the isolated current-base host worktree. Do not begin component v1 implementation first.

### R4 — Pi component implementation

Complete task `4231` in its separate clean identity-lineage worktree only after the host API boundary passes R3. Separate pending task `4127` remains outside this rollout and cannot absorb protocol/host implementation authority.

### R5 — Exact-scope readiness hold

Perform V7, including exact AK scope narrowing/materialization and current scope receipts. Keep all package activation, startup, defaults, publication, ontology activation, live acquisition, and production behavior unchanged.

### R6 — Optional one-shot dogfood

Only after separate task creation/claim and current dual-owner approvals, run V8 once. Return to default-off hold after closeout.

No later rollout stage follows automatically.

## Stop conditions

Stop before the next gate and preserve current history if any of these occurs:

- frozen commit/tree/aggregate, reviewed source, v0 anchor, packet, schema, registry, domain, edge, SQL, Unicode, Wasm, seccomp, fixture, coverage, or embedding drift;
- Python/Node disagreement or shared validator implementation;
- fixture input influencing packet bytes or regeneration after owner signatures;
- absent, synthetic, stale, revoked, superseded, unpinned, cross-owner, or self-issued authority;
- dirty owner checkout mutation or loss of concurrent operator changes;
- component/host/loaded-artifact/generation/attempt/issuer substitution;
- witness before assignment/readback, witness reuse, failed durable write, replay gap, duplicate attempt, ambiguous PID, unsigned/incorrect pidfd transfer, unreaped child, or teardown failure;
- provider/model/adoption/influence/production overclaim;
- new public flag/default, startup, install/reload, publication, activation, fleet, live-acquisition, or ontology-activation behavior;
- fabricated consumer, canary, recovery-owner, attestation-owner, signing-key, store, or read-receipt fact;
- unresolved AK decision/task/scope/dependency/evidence/currentness reference;
- unexpected network, shell, ambient environment, mutable sibling checkout, or unmanaged filesystem influence.

## Rollback

### Planning and AK release

- Do not delete Decision 71, its ADR, review history, tasks, reevaluations, or transition receipts.
- If the plans are defective, supersede or revise them through a new bounded task and return the decision/task posture to a truthful blocked state.

### ROCS implementation

- Revert only task-`4230` implementation commits.
- Remove only generated v1 packet/fixture/embedding bytes whose paths and owners are verified.
- Preserve frozen r21 sources and all Decision-53 v0 bytes.
- Re-run the pre-change ROCS gate and verify no managed ontology or production state changed.

### Semantic-owner acceptance

- Never rewrite or delete immutable validation/acceptance history.
- If generated bytes change, mark prior acceptance non-current through the owner surface and return to V1; do not edit signed objects in place.
- Preserve owner-store heads, pins, read receipts, and revocation/supersession evidence.

### Pi component implementation

- Revert only task-`4231` component commits in its isolated worktree.
- Preserve the accepted identity decision/commit, v0 history, packet references, and failed-attempt evidence.
- Verify no live installation or default changed.

### Pi host implementation

- Revert only task-`4232` host commits in its isolated worktree.
- Preserve packet/host fixture evidence and immutable execution/replay history.
- Verify no provider surface, installed runtime, or live Pi session was changed.

### One-shot isolated dogfood

- Stop new reservation/redemption first.
- Terminalize every outstanding claim and process.
- Preserve all receipts, transcripts, ledger/store heads, replay records, closeout/reap observations, and failed-attempt history.
- Reject generation/attempt reuse permanently.
- Remove only verified disposable dogfood runtime bytes.
- Keep default-off production behavior unchanged.

### Architecture escape hatch

If accepted owner boundaries or runtime constraints are not implementable without changing r21 semantics, stop. Create a new reviewed decision and superseding ADR. Never widen the packet, alias `pi-adapter`, weaken witness ordering, or invent owner facts in place.

## Required completion evidence

Each completed owner task records:

- exact task/scope/dependency IDs and repository/worktree/commit identity;
- exact files and before/after status preserving unrelated work;
- commands, versions, inputs, outputs, and exit outcomes;
- generated packet/fixture/embedding or consumed accepted-packet digests;
- independent review reference and owner-specific evidence;
- filesystem, process, environment, and network-effect evidence;
- rollback rehearsal or proof that no live state could change;
- deferred facts and the next legal gate.

Evidence must distinguish observed implementation behavior from owner authorization. A passing proxy is never reported as completed delivery, dogfood, publication, activation, ontology adoption, or production behavior.
