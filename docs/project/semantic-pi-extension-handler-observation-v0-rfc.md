---
summary: "Prospective Decision 89 contract for package-local observation of a prompt-chain handler result without host insertion claims."
read_when:
  - "Reviewing or implementing extension-local prompt-chain handler observation v0."
type: "rfc"
status: "in_review"
rfc_revision: "pi-ontology-workflows-handler-observation-v0-r1"
---
# RFC — Extension-local prompt-chain handler observation v0

## Decision requested

Accept a package-local successor to the stopped Decision-85 host direction. The successor proves only that `pi-ontology-workflows` observed an inner producer resolve an exact transformed prompt string and that its outer registered callback returned the same value.

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
5. the outer handler returned `{systemPrompt: output}` from its own callback frame.

It does **not** prove:

- host acceptance, assignment, readback, or final-chain retention;
- ordering or behavior of later handlers;
- dispatch exclusion or provider payload contents;
- provider transmission or model invocation/input/influence;
- stale-host isolation, public issuance, authenticity, adoption, consent, semantic correctness, publication, activation, live acquisition, or production use.

The host capability token `prompt.system.chain.v1` is only a compatibility prerequisite indicating that the callback receives chained input. It is not evidence.

## Package-local sequence

The registered handler is one outer package function. It executes sequentially:

1. Verify package-local feature gate and exact host compatibility token.
2. Snapshot `event.systemPrompt` as a well-formed JavaScript Unicode string.
3. Call the inner producer exactly once.
4. Await producer settlement.
5. Validate the producer result as exact `{contribution,output}` strings.
6. Verify `contribution` is nonempty and `output === input + contribution` by JavaScript string equality and UTF-8 byte equality.
7. Snapshot UTF-8 bytes after rejecting lone surrogates; no Unicode normalization is performed.
8. Construct and commit one immutable in-memory local record.
9. Return exactly `{systemPrompt: output}`.

No `Promise.all`, detached observer, event bus, later lifecycle hook, substring search, inferred offset, host callback, or persistence participates in acceptance.

If any step fails, no accepted record exists and the handler throws or returns no modification according to the package's explicit default-off failure policy. Failure never creates positive evidence.

## Local generation and attempt

- Each extension instance starts `local_generation=0` and `next_observation_id=0`.
- Reload/new/resume/fork creates a new extension instance and therefore a new local generation namespace; no cross-instance continuity is claimed.
- Within one instance, observation IDs increment without reuse and fail closed before unsafe-integer overflow.
- Records are non-evicting only for that extension instance and disappear at shutdown.
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
returned_prompt_byte_length
returned_prompt_digest
contribution_start_byte_offset
contribution_end_byte_offset
observation_outcome
claim_scope
host_acceptance_observed
host_assignment_observed
provider_transmission_observed
model_input_observed
record_digest
```

Productions:

- fixed schema/identity/revision;
- lengths and offsets count UTF-8 bytes;
- `contribution_start_byte_offset=input_prompt_byte_length`;
- `contribution_end_byte_offset=returned_prompt_byte_length`;
- `returned_prompt_byte_length=input_prompt_byte_length+contribution_byte_length`;
- raw digests use the exact domains above;
- `observation_outcome="package_handler_result_forwarded"`;
- `claim_scope="extension_local_handler_resolution_only"`;
- all four observation booleans are exactly `false`;
- no additional key exists.

The record is a package-local diagnostic object. It is not signed, host-issued, publicly authenticated, or governance authority.

## Default-off gate

Implementation remains disabled by default. A future package plan must define one explicit, bounded TUI-only development gate and rollback-to-disabled behavior. Repository files, prompt text, model output, and environment variables cannot silently enable it. Production activation requires a separate post-ADR task and evidence.

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
| `observer-throw` | record construction fails | rejected, callback does not return modified chain |
| `duplicate-id` | forced observation reuse | rejected, no second record |
| `disabled` | gate disabled | no producer call, no record, no modification |
| `sequential-order` | delayed producer and observer probes | producer settles before observer; observer commits before callback return |
| `later-handler-removal` | separate simulated later handler removes output | local record remains local only and must not be interpreted as final-chain evidence |

Tests compare actual independently computed outputs after execution. Case IDs and expected rows may not select implementation behavior. The lifecycle harness must execute producer and observer sequentially, never with `Promise.all`.

## Ownership and rollout

After an accepted ADR:

1. `core/rocs-cli` owns only immutable architecture history and reviewed claim wording.
2. `pi-ontology-workflows` owns producer, outer observer, local record, gate, tests, and rollback.
3. `pi-mono` owns no implementation change.
4. A package-local development proof must precede any install/reload task.
5. Publication or production work requires separate owner tasks and may state only the extension-local claim.

## Supersession

Decision 89 supersedes Decision 85 as the active implementation direction if accepted. It does not rewrite or invalidate Decision 85's accepted ADR, R1b substrate, failed/rejected tasks, evidence, or frozen artifacts. Tasks `4331`, `4343`, and their downstream graphs are never reopened or reused.

## Non-authorization

This RFC is prospective. It authorizes no code, test, installation, reload, dogfood, provider/model use, publication, activation, live acquisition, or production mutation before strict review and an accepted ADR.
