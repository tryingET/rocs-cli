---
summary: "Supersedes Decision 71 r21 with r23, closing pinned Unicode source parsing and binding corrected execution authority to Decision 80."
read_when:
  - "Implementing or reviewing semantic Pi delivery v1 r23."
  - "Tracing why Decision 71 r21 cannot authorize corrected packet bytes."
system4d:
  container: "Superseding architecture boundary for deterministic r23 packet generation and Decision-80 authority."
  compass: "Preserve r21 history while making pinned Unicode parsing executable and corrected authority non-transferable."
  engine: "Failed r21 implementation -> r22 review failure -> r23 strict convergence -> new owner-scoped implementation tasks."
  fog: "A corrected parser, accepted predecessor ADR, or passing fixture may be mistaken for current implementation or execution authority."
type: "adr"
status: "accepted"
---
# ADR — Semantic Pi Delivery v1 r23 Unicode Source and Authority

## Decision

Accept Decision `80` and the exact r23 source set at commit `b8619957d0d8c68b2f31f1c20e417ce12d901783`, tree `96a4be6f895969b9355d4b916a5d957de73694bd`, fourteen-file aggregate `e88c4d8470361aa2d96314f050c85ecaedc952dc5cae3a4c84154eb08fef0516`, with controlling synthesis [`semantic-pi-delivery-v1-review-synthesis-r23.md`](../project/semantic-pi-delivery-v1-review-synthesis-r23.md).

R23 supersedes Decision `71` r21 for all future corrected packet, owner-acceptance, implementation, isolated-dogfood, and production references. Decision 71, its ADR, frozen r21 bytes, failed task `4230`, AK evidence `5325`, r22 bytes, and r22 failed review remain immutable predecessor history and cannot authorize r23 bytes.

The corrected protocol decision ID is `80`. Packet acceptance, host-attestation appointments, AK decision/task/scope references, implementation reevaluation, integration request/envelope, isolated-dogfood task, production protocol joins, and the unique canonical-ledger anchor must bind Decision 80 and this accepted ADR.

## Unicode correction

The generator verifies exact raw input identity before parsing, rejects CR, and splits only on LF. For CaseFolding and CompositionExclusions it discards the first ASCII `#` and suffix bytes before decoding, then requires retained syntax bytes to be ASCII. UnicodeData receives no comment stripping and must be ASCII.

Exactly six pinned UnicodeData General_Category `Cs` source/name tuples—`D800`, `DB7F`, `DB80`, `DBFF`, `DC00`, and `DFFF`—are accepted only as non-emitting range metadata with CCC `0` and empty decomposition. Every mapping, decomposition, exclusion, table entry, composition pair, identifier, JSON string, and normalized output remains scalar-only.

Python and Node must independently execute the six source-compiler conformance obligations and regenerate exact tables without shared parser, input builder, expected helper, digest helper, or ambient Unicode implementation. These obligations do not change the 112 mandatory, 3 boundary, 25 host, or 127 coverage counts.

## Preserved architecture

Every other accepted identity, host witness, component issuer, packet, schema, registry, digest, SQL, seccomp, Wasm, process, replay, owner-separation, rollback, and default-off contract remains as reviewed in r23. Repository `pi-extensions`, component/protocol issuer `pi-ontology-workflows`, package `@tryinget/pi-ontology-workflows`, and the absence of any `pi-adapter` alias or owner remain fixed.

Host witnessing still claims only post-assignment/readback prompt-chain insertion, not provider transmission, model invocation, influence, correctness, adoption, or production use.

## Post-ADR sequence

Do not reopen failed task `4230` or reuse Decision-71 implementation plans as r23 execution authority. After acceptance, materialize new Decision-80 tasks in this strict order:

1. ROCS r23 packet, fixtures, independent validators, coverage, and embedding;
2. semantic-owner fixture validation and exact packet acceptance;
3. separately reviewed Pi-host owner identity artifact and content-addressed private host API/runtime;
4. `pi-ontology-workflows` component validation and issuance;
5. exact AK scope materialization, implementation evidence, and Decision-80 post-ADR readiness reevaluation;
6. only then, a separately created/claimed one-shot Decision-80 isolated dogfood task with current component-owner and host-owner approvals.

## Non-authorizations

This ADR does not itself authorize packet generation, owner signatures or receipts, implementation, task `4127` completion, dogfood, ontology candidate `0d53ce3`, installation/reload, publication, adoption, activation, startup/default/fleet behavior, live acquisition, consumer/canary/recovery/attestation-owner facts, production execution, production delivery, or production rollback.

## Rollback

Before implementation, retain r21/r22/r23 review history and supersede this ADR through a later reviewed decision if the correction is unsound. During implementation, any source identity, parser, scalar, Python/Node, packet, authority, task/scope, process, replay, or rollback divergence stops before execution authority. No rollback may restore r21 execution binding, `pi-adapter`, v0 successor acceptance, or a false delivery claim.
