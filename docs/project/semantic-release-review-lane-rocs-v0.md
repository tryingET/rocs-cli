---
summary: "Decision:53 lane B review of ROCS schemas, determinism, receipts, materialization, and rollback."
read_when:
  - "Revising or synthesizing decision:53 review."
type: "review_memo"
status: "complete"
review_outcome: "revise_rfc"
---
# Decision 53 Review — Lane B: ROCS Protocol and Receipts

## Outcome

`revise_rfc`

The architecture is viable, but field-list prose is not a deterministic protocol.

## P0 findings

1. **No normative machine contract.** Add closed Draft 2020-12 schemas, cross-field invariants, golden/differential fixtures, precedence, duplicate-free UTF-8 I-JSON, safe integer ranges, unknown-field rejection, exact ordering, and byte limits for capsule, coordinate, approval, compatibility, intent, build/materialization, adoption, use/delivery, rollback, manifests, and errors.
2. **Digest contracts are undefined.** Define explicit domains and one omitted self-digest per object; retain nested digests. Separate raw blob, source manifest, payload, capsule, owner approval, build receipt, intent, materialization/adoption, delivery/use, and rollback identities. Audit timestamps belong in a separately bound audit envelope.
3. **Complete materialization is unprovable.** Define NFC POSIX logical paths, kinds, byte lengths, raw-byte digests, significant modes, UTF-8 ordering, path uniqueness, normalization collision rejection, complete-tree equality, and rejection of unlisted files, links, special files, traversal, and duplicate archive entries.
4. **Tool and semantic identities can be conflated.** Keep ROCS tool identity out of capsule identity. Add a build receipt binding source manifest, compilation contract, tool identity, output manifests, and final capsule digest.
5. **Adoption can self-certify.** Verification must require external semantic-owner approval/trust pin, consumer-owner intent approval, exact intent, full capsule/blobs, independent runtime pin, expected/actual complete manifests, repository identity, compatibility policy/report, prior receipt, rollback target, and fixed verifier contract/limits.
6. **Publication/adoption transaction semantics are absent.** Require private staging, complete verification, fsync, atomic activation, durable receipt commit marker, locking, crash journal/recovery, idempotent same-digest replay, conflict failure, and no mutation where atomic activation is unavailable.
7. **Use receipts are not replayable.** Split ROCS generation facts from Pi delivery and AK evidence linkage; bind exact request/result/effective-execution, candidate IDs, packs, prompt-run identity, issuer, and claim scope. Do not claim interpretation or material influence.
8. **Rollback has no executable protocol.** Add closed semantic, runtime, no-prior, and partial-failure rollback requests/receipts with preconditions, independently trusted recovery path, append-only history, and deterministic failure taxonomy.
9. **Resource and failure behavior is open.** Define caps, deadlines, no-network/offline behavior, trust-root absence, incompatible/unknown policy, snapshot drift, publication conflict, recovery-needed, rollback-unavailable, and malformed input mappings.

## Required artifact family

Create `docs/project/semantic-release-v0/` containing schemas, `invariants.md`, golden fixtures, differential fixtures, and machine-readable examples before a fresh review claims ADR readiness.
