---
summary: "Prospective Decision 89 contract for package-local observation of a prompt-chain handler result without host insertion claims."
read_when:
  - "Reviewing or implementing extension-local prompt-chain handler observation v0."
type: "rfc"
status: "in_review"
rfc_revision: "pi-ontology-workflows-handler-observation-v0-r2"
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
5. the outer handler constructed `{systemPrompt: output}` and atomically replaced the immutable observation-state snapshot with one containing both the new record and its allocator transition; that single commit is the final package operation before the source-level return statement.

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
9. Build an immutable next observation-state snapshot containing the record and allocator transition, then commit it with one synchronous state-reference assignment.
10. Immediately return the already-constructed value, with no intervening package code.

No `Promise.all`, detached observer, event bus, later lifecycle hook, substring search, inferred offset, host callback, or persistence participates in acceptance.

Producer failure, malformed output, a non-append transformation, or observation-record failure creates no positive record. When a valid pre-existing handler result has already been prepared, any observation-only validation or record failure is caught and returns that exact prepared result. Producer failure follows the already reviewed semantic-preflight behavior outside this observation claim.

## Local generation, grant, and attempt

- One package runtime object starts `local_generation=0`, `next_observation_id=0`, `observation_id_exhausted=false`, and an empty record set. These are observation-local values, not the Pi host's generation identity.
- Before handling a later prompt, each `session_start` for startup/reload/new/resume/fork and each `session_shutdown` clears records and advances `local_generation`. These events do not claim that the host created a new extension instance.
- Explicit disable clears records and advances generation synchronously. Successful grant enablement or replacement clears records, advances generation, and resets `next_observation_id=0` before the new grant becomes observation-eligible. Expiry or other grant invalidity clears and advances when the package next synchronously evaluates grant validity; no wall-clock timer or immediate idle-time erasure is claimed.
- If an actual extension reload creates a new runtime object, its namespace starts again at zero. No value is globally unique, and records from different runtime objects or generations are never compared as one lineage.
- `local_generation` and `observation_id` are integers in `0..9007199254740991`. An advance at maximum clears records and permanently disables further observation in that runtime object rather than incrementing.
- Within every new generation, `next_observation_id` starts at `0`. After producer settlement, one no-`await` critical section rechecks current generation/grant and uses the current ID to build, without mutation, an immutable next observation-state snapshot containing the candidate record plus `next_observation_id=id+1`; allocation of `9007199254740991` instead carries `observation_id_exhausted=true` without an increment. One state-reference assignment atomically commits both record and allocator transition. Any failure before that assignment leaves the current state and ID unchanged. A later attempt in an exhausted generation may still complete the pre-existing producer behavior but creates no record.
- Concurrent callbacks may run or coalesce the existing producer work. Their accepted records linearize only in the synchronous post-settlement critical section and therefore receive distinct IDs. A reused, non-current, or already-committed ID rejects without a positive record.
- Records are non-evicting only within the current observation generation, are cleared on the invalidations above, and disappear with the runtime object.
- No database, recovery actor, cross-process replay, or public ledger exists.

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
local_generation
observation_id
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
- `protocol_revision="pi-ontology-workflows-handler-observation-v0-r2"`;
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

Observation recording remains disabled by default and reuses the package's existing bounded TUI-only development grant: `/ontology-preflight enable-development`, fresh UI confirmation, immutable closed host compatibility, current generation/cwd binding, and expiry. It adds no second activation source. Explicit disable synchronously disables observation and clears records. Expiry or other invalidity does so when the package next evaluates grant validity; successful grant replacement clears the prior observation generation before eligibility. Each preserves the package's already reviewed disabled-mode behavior. Repository files, prompt text, model output, and environment variables cannot silently enable it. Production activation requires a separate post-ADR task and evidence.

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
| `replacement-transform` | existing owner frame causes non-append output | exact existing result forwards, no record |
| `observer-throw` | record construction fails after a valid result is prepared | exact prepared result forwards, no record, ID unchanged |
| `duplicate-id` | forced current-generation ID reuse | rejected, no second record |
| `concurrent-ids` | two callbacks settle producer work before either commits | synchronous commits receive distinct increasing IDs |
| `id-maximum` | allocate `9007199254740991`, then attempt again | maximum accepted once; later existing result may forward with no record |
| `generation-maximum` | invalidate generation `9007199254740991` | records clear; runtime observation permanently disabled |
| `grant-replacement` | enable a new grant in the same session lifecycle | prior records clear; generation advances; ID resets to `0` |
| `idle-expiry` | grant expires with no package action | no timer claim; records clear on next validity evaluation before observation |
| `disabled` | observation gate disabled | existing handler behavior unchanged; no observation record |
| `sequential-order` | delayed producer and observer probes | producer settles before observer; one record-plus-allocator state assignment is the final operation before the source-level return statement |
| `return-resolution-harness` | package harness invokes and awaits handler | resolved value equals prepared return; runtime record still claims no return-statement execution or settlement |
| `lifecycle-same-instance` | repeated reload/new/resume/fork events on one runtime | generation advances, ID resets, and prior records clear without re-instantiation claim |
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

## Non-authorization

This RFC is prospective. Strict review and an accepted ADR are necessary but not sufficient for implementation. This decision authorizes no code, test, installation, reload, dogfood, provider/model use, publication, activation, live acquisition, or production mutation; implementation requires a fresh owner-scoped package task, and every later runtime or release action requires its own owner authority.
