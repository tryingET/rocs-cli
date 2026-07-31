---
summary: "Prospective Decision 89 contract for package-local observation of a prompt-chain handler result without host insertion claims."
read_when:
  - "Reviewing or implementing extension-local prompt-chain handler observation v0."
type: "rfc"
status: "in_review"
rfc_revision: "pi-ontology-workflows-handler-observation-v0-r3"
---
# RFC — Extension-local prompt-chain handler observation v0

## Decision requested

Accept a package-local successor to the stopped Decision-85 host direction. The successor proves only that `pi-ontology-workflows` observed an inner producer resolve an exact append candidate and constructed the exact value referenced by the callback's next source-level return statement.

## Fixed identity

```json
{"repository_id":"pi-extensions","component_id":"pi-ontology-workflows","package_name":"@tryinget/pi-ontology-workflows","record_schema":"pi-ontology-workflows.prompt-chain-handler-observation.v0"}
```

No `pi-adapter` alias or host-owned witness identity exists.

## Claim boundary

An accepted local record means only:

1. the package outer handler received one `before_agent_start` `event.systemPrompt` string;
2. the package inner producer resolved one contribution and one output string;
3. output was exactly input followed by contribution, with no other byte change;
4. the package outer handler observed immutable snapshots of those three strings;
5. the outer handler constructed `{systemPrompt: output}` and atomically replaced its single package-local diagnostic slot with the new immutable record; that assignment is the final package operation before the source-level return statement.

The record does **not** prove that execution reached or crossed the return statement, that the callback returned to its caller, or that its promise settled. A package-local conformance harness may independently invoke and await the handler to prove ordinary return behavior, but that test result is not encoded into an individual runtime record.

It also does **not** prove:

- host acceptance, assignment, readback, or final-chain retention;
- ordering or behavior of later handlers;
- dispatch exclusion or provider payload contents;
- provider transmission or model invocation/input/influence;
- stale-host isolation, public issuance, authenticity, adoption, consent, semantic correctness, publication, activation, live acquisition, or production use.

The host capability token `prompt.system.chain.v1` is only one member of the package's existing closed compatibility prerequisite. It indicates that the callback receives chained input; neither that token nor the compatibility object is evidence.

## Current-component integration

Decision 89 wraps the existing development semantic-preflight path inside its current single registered `before_agent_start` handler. It does not add a second Pi handler and does not observe another handler through host ordering.

The package extracts a pure inner producer from the enabled semantic-preflight branch. For one validated envelope, its canonical contribution is exactly two LF code points followed by the canonical structural block. The producer returns `{contribution,output}` from immutable input. The observation path accepts only when `output === input + contribution` exactly. Existing complete owner/version framing may still be removed or replaced by the package's pre-existing transformation, but that non-append result is forwarded under existing behavior with no Decision-89 record.

When the Decision-89 observation gate is disabled, the existing handler remains behaviorally unchanged: legacy hints and enabled semantic-preflight behavior stay outside the observation claim. “Disabled” means no observation-specific record or behavior, not that the package's pre-existing handler must return no modification.

## Package-local sequence

The registered handler is one outer package function. For an exact-append observation it executes sequentially:

1. Verify the package-local observation gate and the existing closed host-compatibility prerequisite.
2. Snapshot `event.systemPrompt` as a well-formed JavaScript Unicode string.
3. Call the pure inner producer exactly once.
4. Await producer settlement.
5. Validate the producer result as exact `{contribution,output}` strings.
6. Verify `contribution` is nonempty and `output === input + contribution` by JavaScript string equality and UTF-8 byte equality.
7. Snapshot UTF-8 bytes after rejecting lone surrogates; no Unicode normalization is performed.
8. Construct the exact plain-data return value `{systemPrompt: output}`.
9. Replace the single package-local diagnostic slot with the immutable record using one synchronous state-reference assignment.
10. Immediately return the already-constructed value, with no intervening package code.

No `Promise.all`, detached observer, event bus, later lifecycle hook, substring search, inferred offset, host callback, or persistence participates in acceptance.

Producer failure, malformed output, a non-append transformation, or observation-record failure creates no positive record. Each such completed observation attempt clears the diagnostic slot. When a valid pre-existing handler result has already been prepared, observation-only validation or record failure is caught, the slot is cleared with one assignment, and the exact prepared result returns. Producer failure otherwise follows the already reviewed semantic-preflight behavior.

## Bounded diagnostic state and grant lifecycle

- One package runtime object owns exactly one `latest_observation_record` slot, initially empty. There is no observation generation, attempt ID, collection, queue, history, ordering identity, uniqueness claim, or cross-record lineage.
- The slot exists only to expose the latest completed exact-append observation to package-local development diagnostics and conformance tests. A later completed attempt replaces or clears it; replacement is intentional and is not retention evidence.
- `session_start` for startup/reload/new/resume/fork, `session_shutdown`, explicit disable, and successful grant enablement or replacement clear the slot. These events reuse the existing package runtime lifecycle and do not claim host re-instantiation.
- Expiry or other grant invalidity clears the slot when the package next synchronously evaluates grant validity; no wall-clock timer or immediate idle-time erasure is claimed.
- After producer settlement, the outer handler first rechecks the existing generation/grant/cwd/compatibility boundary. If it is non-current, one assignment clears the slot and the handler follows the existing stale-completion path: visible unavailability and no prompt modification. This invalidation transition is not an observation-construction failure.
- After a successful current-boundary recheck, record construction is mutation-free. Success assigns the immutable record to the slot once as the final package operation before return. Construction or validation failure assigns `undefined` once, then returns the exact prepared existing result. No `await` occurs between the recheck and assignment.
- Concurrent callbacks may run or coalesce existing producer work. Their post-settlement slot assignments linearize under JavaScript run-to-completion; the last completed assignment wins. No record order, completeness, or durability is claimed.
- The single fixed-size record disappears with the runtime object. No database, recovery actor, cross-process replay, public ledger, or unbounded retention exists.

## Encoding and digests

Strings must contain no lone UTF-16 surrogates. UTF-8 bytes preserve the exact scalar sequence; NFC is neither required nor implied.

Raw string digest:

```text
sha256(UTF8(domain) || 0x00 || uint64_be(byte_length) || bytes)
```

Domains are exact:

- `pi-ontology-workflows.handler-input.v0`
- `pi-ontology-workflows.handler-contribution.v0`
- `pi-ontology-workflows.handler-output.v0`
- `pi-ontology-workflows.handler-observation-record.v0`

The record digest is SHA-256 over domain, NUL, and RFC-8785 JCS of the record with `record_digest` omitted. Integers are safe nonnegative JavaScript integers. Digests are lowercase `sha256:` plus 64 lowercase hexadecimal characters.

## Record schema

`pi-ontology-workflows.prompt-chain-handler-observation.v0` has exactly:

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

Productions:

- `schema="pi-ontology-workflows.prompt-chain-handler-observation.v0"`;
- `protocol_revision="pi-ontology-workflows-handler-observation-v0-r3"`;
- repository/component/package identity equals the fixed identity above;
- lengths and offsets count UTF-8 bytes;
- `contribution_start_byte_offset=input_prompt_byte_length`;
- `contribution_end_byte_offset=prepared_return_prompt_byte_length`;
- `prepared_return_prompt_byte_length=input_prompt_byte_length+contribution_byte_length`;
- input, contribution, and prepared-return prompt digests use the exact input, contribution, and output domains above respectively;
- `observation_outcome="package_handler_return_prepared"`;
- `claim_scope="extension_local_pre_return_only"`;
- all five observation booleans are exactly `false`;
- no additional key exists.

The record is a package-local diagnostic object. It is not signed, host-issued, publicly authenticated, or governance authority.

## Default-off gate

Observation recording remains disabled by default and reuses the package's existing bounded TUI-only development grant: `/ontology-preflight enable-development`, fresh UI confirmation, immutable closed host compatibility, current generation/cwd binding, and expiry. It adds no second activation source. Explicit disable synchronously disables observation and clears the slot. Expiry or other invalidity does so when the package next evaluates grant validity; successful grant replacement clears the slot before eligibility. Each preserves the package's already reviewed disabled-mode behavior. Repository files, prompt text, model output, and environment variables cannot silently enable it. Production activation requires a separate post-ADR task and evidence.

## Executable conformance matrix

A package implementation must independently test at least these exact behaviors:

| ID | Input/contribution | Expected |
|---|---|---|
| `ascii-append` | ASCII input and contribution | accepted exact append |
| `empty-input` | empty input, nonempty contribution | accepted offset `0` |
| `unicode-preserve` | decomposed and composed scalar sequences | accepted without normalization |
| `repeated-bytes` | contribution bytes already occur in input | accepted using operation boundary, not search |
| `empty-contribution` | empty contribution | rejected, no record |
| `wrong-output` | output differs from `input+contribution` | rejected, no record |
| `lone-surrogate-input` | malformed JS string | rejected, no record |
| `producer-throw` | producer throws/rejects | rejected, no record |
| `replacement-transform` | existing owner frame causes non-append output | exact existing result forwards; slot clears |
| `observer-throw` | record construction fails after a valid result is prepared | exact prepared result forwards; slot clears |
| `grant-replacement` | enable a new grant in the same session lifecycle | prior slot clears before new eligibility |
| `idle-expiry` | grant expires with no package action | no timer claim; slot clears on next validity evaluation before observation |
| `disabled` | observation gate disabled | existing handler behavior unchanged; slot empty |
| `sequential-order` | delayed producer and observer probes | producer settles before observer; successful slot assignment is the final package operation before the source-level return statement |
| `concurrent-latest` | two callbacks settle and complete in either order | assignments do not interleave; last completed assignment alone occupies the slot |
| `return-resolution-harness` | package harness invokes and awaits handler | resolved value equals prepared return; runtime record still claims no return-statement execution or settlement |
| `lifecycle-same-instance` | repeated reload/new/resume/fork events on one runtime | slot clears without re-instantiation claim |
| `later-handler-removal` | separate simulated later handler removes output | local record remains local only and must not be interpreted as final-chain evidence |

Tests compare actual independently computed outputs after execution. Case IDs and expected rows may not select implementation behavior. The lifecycle harness must execute producer and observer sequentially, never with `Promise.all`. Concurrent behavior may be tested separately, but it cannot supply ordering evidence for an accepted record.

## Ownership and rollout

After an accepted ADR, implementation is still unauthorized until a fresh owner-scoped package task exists:

1. `core/rocs-cli` owns only immutable architecture history and reviewed claim wording.
2. Under that fresh task, `pi-ontology-workflows` owns producer, outer observer, local record, gate, tests, and rollback.
3. `pi-mono` owns no implementation change.
4. A package-local development proof under the fresh task must precede any separately authorized install/reload task.
5. Publication or production work requires separate owner tasks and may state only the extension-local claim.

## Supersession

Decision 89 supersedes Decision 85 as the active implementation direction if accepted. It does not rewrite or invalidate Decision 85's accepted ADR, R1b substrate, failed/rejected tasks, evidence, or frozen artifacts. Tasks `4331`, `4343`, and their downstream graphs are never reopened or reused.

Acceptance is not operational supersession by prose alone. Before Decision 89 can become unblocked or create a package implementation task, the decision owner must use the AK decision membrane to record Decision 85's successor disposition and reevaluate its stopped executable graph. Decision-85 links for failed roots `4331` and `4343` plus their pending executable graphs `4332` through `4339` and `4344` through `4350` must have reevaluation status `cancelled` with notes naming Decision 89 as the successor; task rows and historical artifacts remain intact. The controller must verify the Decision-85 passport no longer presents an unblocked executable direction and exposes no still-valid pending host/component/runtime/release continuation from the stopped graph.

## Non-authorization

This RFC is prospective. Strict review and an accepted ADR are necessary but not sufficient for implementation. This decision authorizes no code, test, installation, reload, dogfood, provider/model use, publication, activation, live acquisition, or production mutation; implementation requires a fresh owner-scoped package task, and every later runtime or release action requires its own owner authority.
