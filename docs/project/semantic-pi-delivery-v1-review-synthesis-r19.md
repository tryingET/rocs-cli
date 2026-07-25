---
summary: "Controlling strict-convergence synthesis for semantic Pi delivery v1 r19."
read_when: ["Tracing Decision 71 r19 outcome and legal next move."]
type: "review_synthesis"
status: "complete"
review_outcome: "revise_rfc"
---
# Decision 71 r19 — controlling synthesis

All five required exact-byte lanes completed on commit `7ef473aec81ecc8e955d8324918f31b71dd0b3dd`, tree `96eb6037f71a5666c7b25dd19e03acc493bb279c`, aggregate `13776689613245f8ce7320a775e493fd1807f2240d53cbdab09984906733e8f7`.

Component, semantic-owner, and governance/security/operations lanes returned `ready_for_adr`. Pi host and ROCS protocol lanes returned `revise_rfc`. Strict convergence does not average or outvote blockers. The controlling outcome is `revise_rfc`.

## Mandatory revision set

1. Define directional FD7 and FD8 credential/ancillary matrices. Authenticate finalizer requests and broker/writer responses with their actual kernel sender identities; do not require response credentials to equal the finalizer or require no ancillary item when receiver `SO_PASSCRED` supplies one.
2. Add `statement_digest`, signing key, algorithm, signature, and exact purpose closure to `pi.production-recovery-pidfd-transfer.v1`, or remove the false broker-signed claim and replace it with an equally explicit authenticated mechanism.
3. Assign exact normal and failure-path `waitid`/reap ownership and ordering for controller and finalizer, so pidfd signaling cannot be mistaken for process absence or zombie reaping.
4. Close exact JSON serialization for every authority-bearing identity/issuer field, including host-attestation and replay-writer objects; prose identity is not a schema production.
5. Add exact packet paths, byte derivation, digest domains, registry edges, and inventory accounting for durable-store and integration-ledger SQLite schema SQL, including permanent Decision-71 uniqueness constraints.
6. Include `semantic-release.pi-resolver-artifact-set.v1` and its self-digest domain in the lawful pre-registry bootstrap or provide another non-circular exact bootstrap.
7. Reconcile seccomp semantics: either encode fail-stop enforcement or explicitly bind EPERM handling to the reviewed host binary, and pin an eligible syscall ABI instead of allowing unknown native syscalls under an unbounded kernel surface.
8. Pin the accepted-v0 authority anchor in reviewed machine inputs rather than inferring acceptance from the current directory.
9. Close whether fixture seeds/mutation bytes and Python embedding bytes are canonically derived from reviewed bytes or become accepted deterministic artifacts only after an explicit owner-reviewed selection.
10. Expand frozen host fixtures and the coverage inventory for bidirectional FD7/FD8 credentials, pidfd-transfer authentication, exited-but-unreaped controller/finalizer states, and the separate seccomp self-test obligation.

## Outcome and legal next move

`revise_rfc`.

The next legal move is a new RFC revision that closes the complete mandatory set, followed by a new immutable freeze, five exact-byte lane reviews, and controlling synthesis. ADR drafting and every implementation, dogfood, publication, adoption, activation, production, recovery, and live action remain unauthorized.

Task `4127`, ontology candidate `0d53ce3`, production defaults, and live acquisition remain deferred.
