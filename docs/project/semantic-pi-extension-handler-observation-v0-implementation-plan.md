---
summary: "Owner-scoped implementation plan for Decision 89 package-local handler observation v0 r4."
read_when:
  - "Planning or implementing Decision 89 in pi-ontology-workflows."
type: "implementation_plan"
status: "proposed"
decision_id: 89
---
# Implementation plan — extension-local handler observation v0 r4

## Authority and baseline

Governing artifacts:

- ADR: `docs/adr/2026-07-31-semantic-pi-extension-handler-observation-v0.md`;
- frozen RFC commit: `53e565b078ccc5bd2dff518a776704993e0b8212`;
- frozen four-file aggregate: `5bb5070d08f79e380e2b0a9762ed783e73f30c9e93d99187944bee10578c664a`;
- controlling synthesis: `docs/project/semantic-pi-extension-handler-observation-v0-review-synthesis-r4.md`.

Observed owner baseline is `softwareco/owned/pi-extensions` commit `f445c5b437456cab789b75b19d12e9290a846358`, package subtree `38b7ffb6194c1619e34f819c258f07f064533656` at `packages/pi-ontology-workflows`. The subtree is byte-identical to the earlier reviewed `a340f9a1` baseline and tracked-clean; unrelated root-level untracked paths are not implementation inputs. The owner task must bind the then-current commit and reverify this subtree identity before mutation.

This plan authorizes no code by itself. A fresh owner-scoped `pi-extensions` task must bind the exact files and baseline before implementation.

## Implementation decision

Implement a small observer inside the existing semantic-preflight runtime, not a new host surface and not a second Pi handler.

The observer is not a new lifecycle state machine. It reuses the existing preflight generation/grant/cwd/compatibility checks and adds only one replaceable in-memory slot:

```ts
let latestObservationRecord: HandlerObservationRecord | undefined;
```

There is no observation generation, attempt ID, allocator, queue, history, persistence, timer, or cross-process lineage.

## File-level design

Owner repository: `softwareco/owned/pi-extensions`.

### New pure contract module

Create `packages/pi-ontology-workflows/src/semantic/handler-observation.ts` with:

- fixed identity and protocol-revision constants;
- the exact closed `HandlerObservationRecord` TypeScript shape;
- lone-surrogate rejection;
- exact UTF-8 length/offset calculation;
- raw digest construction `sha256(UTF8(domain) || 0x00 || uint64_be(byte_length) || bytes)` under exact domains `pi-ontology-workflows.handler-input.v0`, `pi-ontology-workflows.handler-contribution.v0`, and `pi-ontology-workflows.handler-output.v0`;
- record digest construction `sha256(UTF8("pi-ontology-workflows.handler-observation-record.v0") || 0x00 || RFC8785_JCS(record without record_digest))`, with no length field;
- reuse of the package's existing integer-only `jcsBytes` implementation rather than a new dependency; inferior insertion-order JSON is prohibited;
- mutation-free `buildHandlerObservationRecord({input, contribution, output})`;
- deep freezing of the accepted record;
- rejection of empty contribution or any `output !== input + contribution` by both JavaScript string and UTF-8 byte equality.

The module owns no slot, lifecycle, command, host context, or persistence.

### Existing producer integration

Add package-private dependency types:

```ts
type PromptAppendProducer = (
  input: string,
  block: string,
) => Promise<{ contribution: string; output: string }>;

type ObservationBuilder = typeof buildHandlerObservationRecord;
```

Extend `SemanticPreflightRuntimeDeps` with optional `promptAppendProducer` and `observationBuilder` injection used only by tests. The production producer is called exactly once per enabled handler invocation, defines `contribution = "\n\n" + block`, computes `output = appendSemanticPreflightBlock(input, block)`, and resolves `{contribution, output}`. “Producer failure” means this extracted append producer rejects; ROCS discovery failure remains existing behavior that resolves an `unavailable` envelope and may still yield a valid append record.

Change `packages/pi-ontology-workflows/src/semantic/preflight-runtime.ts` only inside the existing registered `before_agent_start` path:

1. keep the current gate and host compatibility checks;
2. await the existing discovery/preflight result and render the current canonical block;
3. call and await the injected-or-default append producer exactly once;
4. on injected append-producer rejection, clear the slot and rethrow the same error; the package harness observes a rejected handler promise and no return object, while Pi-host continuation behavior remains outside the package claim;
5. after producer settlement, recheck generation/grant/cwd/compatibility; stale completion clears the slot and follows current visible-unavailable/no-modification behavior;
6. perform existing binding/status/notification updates;
7. construct the plain return object once;
8. invoke the injected-or-default mutation-free record builder;
9. on non-append or builder failure, assign `undefined` and return the exact prepared value;
10. on success, assign the record to the single slot as the final package operation before the source-level return statement;
11. return the already-constructed value.

The test injections are constructor dependencies, not public Pi or production activation surfaces. They must not select behavior from case IDs or expected outputs.

A complete existing owner/version frame causes the current formatter to replace/deduplicate rather than exact-append. That output still forwards under existing behavior, while the observation slot clears and no positive record exists.

Add one package-local instance read seam `latestObservation(): HandlerObservationRecord | undefined` on the returned `SemanticPreflightRuntime` solely for same-instance unit/integration tests. The installed extension keeps its runtime instance function-local, so this seam is not an installed-runtime readback mechanism. Do not expose module-global state, a Pi tool, command, event, database, file, public credential, or host callback.

### Lifecycle clearing

Clear the slot through exact existing package paths:

- `reset()` used by `session_start` and `session_shutdown`;
- `disable()` used by explicit disable, stale status-command evaluation, stale `before_agent_start`, stale `inspectAccess()`, and stale `isCurrent()` evaluation;
- successful grant enablement or replacement immediately before assigning the new eligible `state.grant`;
- stale completion after append-producer settlement;
- append-producer rejection, validation/record-construction failure, and non-append transformation.

Disabled legacy hints remain behaviorally unchanged and create no record.

## Exact schema

Implement exactly the r4 record fields in RFC order:

```text
schema
protocol_revision
repository_id
component_id
package_name
input_prompt_byte_length
input_prompt_digest
contribution_byte_length
contribution_digest
prepared_return_prompt_byte_length
prepared_return_prompt_digest
contribution_start_byte_offset
contribution_end_byte_offset
observation_outcome
claim_scope
host_acceptance_observed
host_assignment_observed
provider_transmission_observed
model_input_observed
callback_settlement_observed
record_digest
```

No extra timestamp, session ID, host identity, attempt ID, signature, provider field, model field, or production marker is permitted.

Focused tests must include independently precomputed known-answer vectors for all three raw domains and the record domain, JCS lexicographic UTF-16 key ordering/escaping, omission of `record_digest`, exact lowercase digest syntax, and attempted mutation of the deep-frozen accepted record.

## Owner-task file contract

The fresh `pi-extensions` task is bounded to exactly:

- `packages/pi-ontology-workflows/src/semantic/handler-observation.ts`;
- `packages/pi-ontology-workflows/src/semantic/preflight-runtime.ts`;
- `packages/pi-ontology-workflows/tests/handler-observation.test.ts`;
- `packages/pi-ontology-workflows/tests/semantic-preflight-lifecycle.test.ts`;
- `packages/pi-ontology-workflows/tests/handler-observation-source-order.test.ts`.

Final tracked changes to `package.json`, lockfiles, dependency manifests, extension entrypoint, Pi-host repositories, and all other packages are forbidden unless a new reviewed task expands scope. Existing `jcsBytes`, Node crypto, TypeScript compiler test dependency, and current test harness are sufficient.

Because the owner-declared `npm run check` executes reversible `prepack`/`postpack` hooks, the task may allow validation-only transient access to `packages/pi-ontology-workflows/package.json` and `packages/pi-ontology-workflows/.package.json.prepack.backup`. The backup must be absent before and after; `package.json` must be restored byte-for-byte by a preauthorized trap even on gate failure/interruption. Neither path may appear in the final commit. `package-lock.json` remains read-only.

The exact focused command is:

```bash
node --import tsx --test \
  tests/handler-observation.test.ts \
  tests/semantic-preflight-lifecycle.test.ts \
  tests/handler-observation-source-order.test.ts
```

The source-order test must parse `preflight-runtime.ts` with the existing TypeScript compiler dependency and assert the successful slot assignment is the final statement immediately preceding the registered callback's return. Runtime probes prove producer-before-builder order; they cannot prove absence of code after assignment.

## AK continuation sequence

1. independently approve and commit these two planning artifacts in `core/rocs-cli`, then mark their metadata `accepted` in a reviewed commit;
2. attach them to Decision 89 as `implementation_plan` and `validation_rollout_rollback`;
3. complete planning task `4399` with validation/review evidence;
4. advance Decision 89 from `adr_recorded` to `tasks_reevaluation_pending`;
5. reevaluate linked planning task `4399` as `still_valid`, verify the passport has no missing execution artifact or pending reevaluation, then advance to `unblocked`;
6. create and claim the fresh file-bounded `pi-extensions` owner task;
7. implementation begins only after that task and baseline are visible.

Until step 1 acceptance, these plan files remain `proposed`. No package mutation is authorized before step 7.

## Implementation slices

1. **Pure record builder and focused tests** — no extension integration.
2. **Existing-handler integration** — single slot and exact final assignment.
3. **Lifecycle/concurrency/source-order tests** — existing harness plus the package-private injected producer/builder and TypeScript AST assertion.
4. **Package validation** — focused tests, quality gate, full package check.
5. **Independent component review** — claim and behavior preservation.

No install, reload, dogfood, publication, activation, provider/model use, or production action belongs to this implementation task.

## Completion boundary

The implementation task may complete only with:

- one owner commit in `pi-extensions`;
- exact r4 conformance coverage;
- package validation evidence;
- independent review with zero blockers/material findings;
- tracked package files clean after commit.

Completion does not authorize Pi installation or runtime use. Any development install/reload proof requires a separate owner task after implementation acceptance.
