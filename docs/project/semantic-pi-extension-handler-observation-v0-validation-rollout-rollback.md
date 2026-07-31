---
summary: "Validation, rollout, and rollback contract for Decision 89 package-local handler observation v0 r4."
read_when:
  - "Validating or sequencing Decision 89 implementation and later runtime proof."
type: "validation_rollout_rollback"
status: "proposed"
decision_id: 89
---
# Validation, rollout, and rollback — extension-local handler observation v0 r4

## Validation authority

This contract follows the accepted Decision-89 ADR and implementation plan. It authorizes package validation only under a fresh owner-scoped `pi-extensions` implementation task. It does not authorize installation, reload, dogfood, publication, activation, provider/model use, or production behavior.

## Required conformance

The owner task must implement independent, behavior-driven cases for:

1. ASCII exact append;
2. empty input with nonempty contribution and offset zero;
3. composed/decomposed Unicode preservation without normalization;
4. contribution bytes repeated earlier in input, proving operation boundary rather than search;
5. empty contribution rejection and empty slot;
6. wrong output rejection and empty slot;
7. lone-surrogate rejection and empty slot;
8. injected append-producer rejection clears the slot and rejects the package handler promise with the same error and no return object, distinct from discovery failure that resolves an `unavailable` envelope;
9. existing-frame replacement forwarding with empty slot;
10. record-construction failure forwarding the exact prepared result with empty slot;
11. grant replacement clearing before new eligibility;
12. idle expiry retaining no timer claim and clearing on next validity evaluation;
13. disabled observation preserving existing handler behavior with empty slot;
14. producer settlement before record construction and slot assignment as the final operation before return;
15. concurrent completions using non-interleaving assignments with last completion in the slot;
16. package harness resolution equal to the prepared return while the record still claims no settlement;
17. reload/new/resume/fork on one runtime clearing the slot without a re-instantiation claim;
18. simulated later-handler removal leaving only the local pre-return claim.
19. independently precomputed known-answer vectors for input/contribution/output raw digests and the record digest;
20. JCS lexicographic UTF-16 key ordering, escaping, and `record_digest` omission;
21. attempted mutation of the deep-frozen record and its exact key set;
22. TypeScript AST proof that successful slot assignment is the final statement before the registered callback return.

Case IDs and expected rows may not drive implementation behavior. `Promise.all` may exercise concurrent completion but cannot supply sequential-order evidence.

## Required commands

From `packages/pi-ontology-workflows` at the owner candidate commit, run in order:

```bash
node --import tsx --test \
  tests/handler-observation.test.ts \
  tests/semantic-preflight-lifecycle.test.ts \
  tests/handler-observation-source-order.test.ts
npm run quality:pre-commit
npm run check
```

`npm run check` includes quick release/package validation, registry access, and mutable `prepack`/`postpack` lifecycle hooks. The implementation task must explicitly allow validation-only transient mutation of `package.json` and `.package.json.prepack.backup` while forbidding them from the final commit. Before the gate, require the backup absent and copy exact `package.json` bytes to an owned file under managed `TMPDIR`. Install a shell `trap` that restores those bytes and removes only the newly created backup on success, failure, signal, or shell exit; then run the gate. `package-lock.json` stays read-only. Afterward require both manifests at their pre-run hashes, the backup absent, and the canonical candidate diff limited to authorized source/tests. Registry failure, unrestored bytes, leftover backup, or cleanup uncertainty fails validation; never delete a pre-existing backup.

Validation evidence must include:

- exact candidate commit and package subtree;
- focused test names/counts;
- `npm run check` result;
- pre/post manifest hashes and absence of `.package.json.prepack.backup`;
- whether registry/package lifecycle steps ran and their exact outcome;
- known-answer digest/JCS/deep-freeze and AST source-order results;
- `git diff --check`;
- independent review dispatch/reference;
- confirmation that no `pi-mono` path changed;
- confirmation that no install/reload/runtime command ran.

## Adversarial checks

Review must attempt to falsify:

- a positive record after non-append replacement;
- stale slot survival across disable, grant replacement, session lifecycle, or observed expiry;
- mutation between successful slot assignment and source-level return, checked structurally through the TypeScript AST rather than a post-assignment runtime probe;
- unbounded collection/history growth;
- callback-settlement or host-final-chain wording;
- compatibility token treated as evidence;
- normalization, substring search, inferred offset, or case-ID-driven behavior;
- extra schema keys, timestamps, host/session IDs, signatures, or persistence;
- observer failure suppressing or altering a valid pre-existing handler result.

Any blocker or unresolved material finding fails implementation acceptance.

## Rollout stages

### R0 — package implementation only

- default-off;
- source/tests only;
- no Pi installation or reload;
- no operator-facing publication claim.

### R1 — separately authorized development install proof

Only after R0 acceptance may a fresh task authorize:

- local package install from the exact owner commit;
- Pi reload;
- one TUI-only, freshly confirmed development grant;
- ordinary existing extension behavior and immediate disable verification.

R1 does not claim installed-instance diagnostic readback: the runtime object is function-local, and the unit-test seam cannot observe the installed instance. Any installed-instance read mechanism requires separate architecture review; module-global state is prohibited.

R1 remains local development evidence. It proves no host acceptance/readback, final-chain retention, provider/model use, authenticity, or production behavior.

### R2 — optional later publication/production decision

Publication, activation, live acquisition, provider/model use, or production rollout requires a new owner decision/task. Decision 89 and R0/R1 evidence are insufficient.

## Rollback

### R0 rollback

Revert the owner implementation commit. Existing semantic-preflight behavior remains unchanged because observation is additive and default-off.

### R1 rollback

Before installation, the R1 task must record the current installed package source/specification, exact prior package commit or version, Pi package configuration, and the CLI command needed to restore it. Rollback authority is preauthorized in that same task and cannot depend on the candidate extension loading successfully.

1. if available, run `/ontology-preflight disable`; absence of the command does not block rollback;
2. use the recorded Pi CLI restoration command to reinstall the prior package source/specification;
3. reload Pi only under that rollback authority;
4. verify existing ontology commands and disabled legacy hints;
5. verify the candidate slot cannot be reached because the prior package is active;
6. record sanitized prior/candidate/restored identities and evidence.

No rollback step may delete unrelated cache/repository state, mutate `pi-mono`, or claim provider/model effects.

## Stop conditions
## Planning-to-execution gate

These files remain `proposed` until independently approved and committed with `status: accepted`. The controller then attaches both artifacts, completes task `4399`, advances Decision 89 to `tasks_reevaluation_pending`, reevaluates `4399` as `still_valid`, verifies post-ADR execution tracking, and only then advances to `unblocked`. The fresh owner implementation task is created afterward; no package mutation occurs earlier.


Stop and return to architecture review if implementation requires:

- a Pi-host API or host callback;
- a second host-ordered handler;
- durable history, database, queue, observation IDs, or cross-process lineage;
- acceptance of non-append output as exact append;
- callback settlement, host final-chain, provider/model, authenticity, or production claims;
- behavior changes to disabled legacy hints or existing framing replacement.
