---
summary: "Supersedes Decision 80 r23 with r24, closing digest-domain preimage-kind metadata and binding corrected execution authority to Decision 82."
read_when:
  - "Implementing or reviewing semantic Pi delivery v1 r24."
  - "Tracing why Decision 80 r23 cannot authorize generated registry bytes."
system4d:
  container: "Superseding architecture boundary for deterministic r24 registry and packet generation."
  compass: "Preserve all digest algorithms and predecessor history while making domain-row metadata independently executable."
  engine: "Failed r23 generation -> explicit 193-row classification -> five-lane strict convergence -> fresh owner-scoped implementation tasks."
  fog: "A plausible preimage label, accepted predecessor ADR, or passing fixture may be mistaken for current implementation or execution authority."
type: "adr"
status: "accepted"
---
# ADR — Semantic Pi Delivery v1 r24 Preimage-Kind Registry

## Decision

Accept Decision `82` and the exact r24 source set at commit `1d36e5e5a9c7b94ca1a83aa78ae37febd2aedf5d`, tree `d665b562ce6f72b9c14cdcc5fa1966ea3d322a00`, fourteen-file aggregate `8a33c165be0fe026b91ed6ef8826b6d1c830d73543f3a8f46622c468c9b0b2c3`, with controlling synthesis [`semantic-pi-delivery-v1-review-synthesis-r24.md`](../project/semantic-pi-delivery-v1-review-synthesis-r24.md).

R24 supersedes Decision `80` r23 for all future packet, owner-acceptance, implementation, isolated-dogfood, and production-protocol references. Decision 71/r21, failed task `4230`, evidence `5325`, r22, Decision 80 and its accepted r23 ADR, frozen r23 bytes, failed task `4250`, and evidence `5404` remain immutable non-authorizing predecessor history.

The corrected protocol decision ID is `82`. Packet acceptance, owner appointments, AK decision/task/scope references, implementation reevaluation, isolated-dogfood task, production-protocol joins, and the unique canonical-ledger anchor must bind Decision 82 and this accepted ADR.

## Registry correction

The Complete digest registry retains all 193 r23 rows with each first three logical cells byte-identical and adds one explicit `Preimage kind` cell to each row. The closed vocabulary is exactly:

```text
exact_bytes
jcs_object
jcs_preimage
```

The inventory contains exactly 43 `exact_bytes`, 144 `jcs_object` rows comprising 134 named self-digest omissions plus 10 full closed objects, and six `jcs_preimage` projections: execution instance, prompt-run attempt, applied entry, logical realpath identity, filesystem tree, and signed authority statement. It has 191 domains and 193 unique `(domain,object_name)` tuples; `semantic-release.pi-packet-file-bytes.v1` is shared by exactly the three reviewed object names.

Python and Node independently copy the explicit fourth cell, tuple-sort the generated rows, reproduce the exact counts and six projections, and reject missing, unknown, inferred, repaired, or relationally inconsistent metadata. The new classification adds no digest domain, separator, preimage algorithm, artifact edge, signer, owner, or authority relation.

## Preserved architecture

Unicode raw preprocessing, exactly six non-emitting `Cs` sentinel rows, scalar-only outputs, and six independent source-compiler obligations remain unchanged. The 112 mandatory, 115 mandatory-plus-boundary, 25 host, and 127 coverage counts remain unchanged. Seccomp, Wasm, SQL, packet, fixture, process, replay, host-witness, component-issuer, rollback, and default-off contracts otherwise remain as reviewed in r24.

Repository `pi-extensions`, issuer/component `pi-ontology-workflows`, package `@tryinget/pi-ontology-workflows`, preserved identity commit `63d1e9f5c271007b48c45818d1f419a228de1561`, Pi-host post-assignment/readback witnessing, and the absence of any `pi-adapter` alias or owner remain fixed.

## Post-ADR sequence

Do not reopen task `4250` or reuse Decision-80 implementation plans/tasks as r24 authority. After acceptance, materialize fresh Decision-82 continuation plans and owner-scoped tasks in this strict order:

1. ROCS r24 packet, fixtures, independent validators, coverage, and embedding;
2. separately authorized semantic-owner fixture validation and exact packet acceptance;
3. separately reviewed Pi-host owner identity artifact and private content-addressed host API/runtime;
4. `pi-ontology-workflows` component validation and issuance;
5. exact AK scopes, owner evidence, and Decision-82 readiness reevaluation;
6. only then, a separately created and claimed one-shot Decision-82 isolated-dogfood task with current component-owner and host-owner approvals.

## Non-authorizations

This ADR does not itself authorize packet generation, owner signatures or receipts, implementation, task `4127` completion, dogfood, ontology candidate `0d53ce3`, installation/reload, publication, adoption, activation, startup/default/fleet behavior, live acquisition, consumer/canary/recovery/attestation-owner facts, provider/model use, production execution, production delivery, or production rollback.

## Rollback

Before implementation, preserve r21/r22/r23/r24 review and failure history and supersede this ADR through a later reviewed decision if the classification is unsound. During implementation, any reviewed-source, first-three-cell, fourth-cell, count, domain, tuple-order, Python/Node, packet, authority, task/scope, process, replay, or rollback divergence stops before execution authority. No rollback may restore Decision-80 execution binding, reopen task `4250`, alias `pi-adapter`, or manufacture a delivery claim.
