---
summary: "ROCS protocol exact-byte review of semantic Pi delivery v1 RFC r19."
read_when: ["Tracing Decision 71 r19 review findings."]
type: "review_lane"
status: "complete"
review_outcome: "revise_rfc"
---
# ROCS protocol lane — r19

Reviewed commit `7ef473aec81ecc8e955d8324918f31b71dd0b3dd`, tree `96eb6037f71a5666c7b25dd19e03acc493bb279c`, aggregate `13776689613245f8ce7320a775e493fd1807f2240d53cbdab09984906733e8f7`. Dispatch `dispatch-1784981883478` read all eleven files, independently reproduced all hashes and byte lengths, and performed no mutation.

## Findings

Blockers:

1. Closed-schema derivation remains underdetermined for authority-bearing identity fields. For example, `issuer` in `pi.host-attestation-statement.v1` is required to name the root but has no exact scalar/object serialization; similar issuer clauses rely on prose identities rather than one closed JSON production.
2. The exhaustive packet inventory has no path, bytes, or derivation rule for the packet-pinned SQLite schema SQL required by durable/replay stores. The integration-ledger SQL also lacks a complete digest-domain/edge closure, so independent implementations cannot reproduce the CAS and permanent Decision-71 uniqueness invariants.
3. Registry bootstrap excludes `semantic-release.pi-resolver-artifact-set.v1` and its self-digest domain from the pre-registry built-ins even though resolvers must decode/authenticate that artifact set to locate the registry.
4. The seccomp policy returns `ERRNO|EPERM`, which does not itself enforce the claimed fail-stop abort after a denied call. Its native-syscall default is `ALLOW` without a pinned kernel syscall ABI, so executable-mapping prevention across eligible kernels is not exhaustive.

Material improvements:

- Pin the accepted-v0 commit/tree/aggregate or equivalent literal authority anchor in reviewed machine inputs instead of inferring acceptance from the current directory.
- Clarify and close whether fixture seeds/mutation bytes and Python embedding bytes are canonically derived from reviewed bytes or become deterministic only after accepting one implementation-authored artifact.

Architecture-shaping open questions:

- What exact serialized issuer identity applies to every signed authority object?
- Where do exact durable-store and integration-ledger SQL bytes live, and how are packet paths, domains, hashes, and inventory counts derived?
- Is seccomp intended as fail-stop OS enforcement or as an EPERM signal trusted by the exact host binary, and what pins the syscall ABI?

The v0 subtree was empirically unchanged, seccomp BPF bytes reproduced, and the JCS/digest, Wasm, Unicode, replay, and authority-separation contracts otherwise showed substantial closure. These passing checks do not resolve the blockers.

## Outcome and legal next move

`revise_rfc`. Close all blocker, material, and architecture-shaping questions in reviewed source bytes, freeze a new commit and aggregate, then rerun all five lanes.

This lane grants no ADR drafting, implementation, dogfood, publication, adoption, activation, production, or live authority.
